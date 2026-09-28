"""Latency-budget-aware turn manager: the brief's §7 control, kept as the reviewed sketch (library-agnostic).

If the primary model's first token is late it plays a pre-recorded filler. After the hard cap, or at once if the
provider errors, it switches to a faster model. It speaks sentence by sentence, cancels on barge-in and records only
what the caller heard. run() raises TimeoutError when no model answers in time: route the caller to a human or the IVR.
latency_gate() is the §8 CI gate: a model, prompt, ASR or TTS change must not regress replay p95 by 10% or more.
"""
import asyncio
import re
import time
from dataclasses import dataclass, field

SENTENCE_END = re.compile(r"[.!?।]\s*$")  # includes the Devanagari danda
LATE = object()                           # sentinel: no chunk within the time allowed


@dataclass
class Budget:               # ms, measured from the moment the caller's turn is committed
    first_token: int = 450  # primary model should start within this, else play a filler
    hard_cap: int = 1200    # past this, abandon the primary and use the fast fallback


@dataclass
class TurnLog:
    spoken: list = field(default_factory=list)  # only sentences the caller actually heard
    timings: dict = field(default_factory=dict)
    filler: bool = False
    fallback: bool = False
    interrupted: bool = False


async def _pump(agen, q):  # decouple the model stream from our timeouts
    try:
        async for chunk in agen:
            await q.put(chunk)
        await q.put(None)
    except Exception as e:  # a provider error surfaces now, not at the timeout
        await q.put(e)


async def _get(q, timeout):
    try:
        return await asyncio.wait_for(q.get(), timeout)
    except asyncio.TimeoutError:
        return LATE


class TurnManager:
    def __init__(self, primary, fallback, speak, filler_clip, budget=Budget()):
        # primary/fallback: async-generator fns prompt -> text chunks; speak: cancellable TTS + playback
        self.primary, self.fallback, self.speak, self.filler, self.b = primary, fallback, speak, filler_clip, budget
        self.barge_in = asyncio.Event()  # set by the VAD when the caller talks over us

    def _start(self, model, prompt):
        q = asyncio.Queue()
        return q, asyncio.create_task(_pump(model(prompt), q))

    async def run(self, prompt: str) -> TurnLog:  # raises TimeoutError -> caller routes to human/IVR
        log, t0 = TurnLog(), time.monotonic()
        left = lambda: max(0.05, self.b.hard_cap / 1000 - (time.monotonic() - t0))  # noqa: E731
        self.barge_in.clear()
        q, prod = self._start(self.primary, prompt)
        chunk = await _get(q, self.b.first_token / 1000)
        if chunk is LATE:  # slow start: cover the gap with a pre-recorded clip
            log.filler = True
            await self._say(self.filler, log, record=False)
            chunk = LATE if log.interrupted else await _get(q, left())
        if (chunk is LATE or isinstance(chunk, Exception)) and not log.interrupted:
            prod.cancel()  # too slow or failed: switch to the fast model
            log.fallback = True
            q, prod = self._start(self.fallback, prompt)
            chunk = await _get(q, self.b.hard_cap / 1000)
            if chunk is LATE or isinstance(chunk, Exception):
                prod.cancel()
                raise TimeoutError("no model answered in time")
        log.timings["first_token_ms"] = round((time.monotonic() - t0) * 1000)
        buf = ""
        while isinstance(chunk, str) and not log.interrupted:  # None = end, Exception = died mid-answer
            buf += chunk
            if SENTENCE_END.search(buf):  # speak each sentence as soon as it is complete
                await self._say(buf, log)
                buf = ""
            chunk = None if log.interrupted else await q.get()
        if buf and not log.interrupted:
            await self._say(buf, log)
        prod.cancel()
        return log

    async def _say(self, text, log, record=True):
        if self.barge_in.is_set():
            log.interrupted = True
            return
        play, stop = asyncio.create_task(self.speak(text)), asyncio.create_task(self.barge_in.wait())
        done, _ = await asyncio.wait({play, stop}, return_when=asyncio.FIRST_COMPLETED)
        stop.cancel()
        if play not in done:  # stop playback at once; drop the rest
            play.cancel()
            log.interrupted = True
        elif record:  # dialogue history = what was heard, not what was generated
            log.spoken.append(text)


def latency_gate(control_p95_ms: float, candidate_p95_ms: float, max_regression: float = 0.10) -> bool:
    """True if the candidate may ship: replay p95 regresses by less than max_regression (brief §8 CI gates)."""
    return (candidate_p95_ms - control_p95_ms) / control_p95_ms < max_regression
