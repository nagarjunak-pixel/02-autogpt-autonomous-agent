"""Tests for turn_manager.py, including the behaviour the brief's critic pass fixed and curveballs 1 and 3."""
import asyncio
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from turn_manager import Budget, TurnManager, latency_gate  # noqa: E402

B = Budget(first_token=60, hard_cap=300)  # ms; scaled down so the suite runs in about a second
FILLER = "<filler>"
TWO = ("Your recharge failed. ", "The money comes back in 48 hours.")


def model(delay_ms, chunks=TWO, error=None, error_after=False):
    async def gen(prompt):
        await asyncio.sleep(delay_ms / 1000)
        if error and not error_after:
            raise error
        for c in chunks:
            yield c
        if error:
            raise error
    return gen


class Speaker:
    def __init__(self, secs=0.0, filler_secs=0.0):
        self.said, self.secs, self.filler_secs = [], secs, filler_secs

    async def __call__(self, text):
        self.said.append(text)
        await asyncio.sleep(self.filler_secs if text == FILLER else self.secs)


def manager(primary, fallback=None, speaker=None):
    return TurnManager(primary, fallback or model(5, ("Fallback answer.",)), speaker or Speaker(), FILLER, B)


class TurnManagerTests(unittest.IsolatedAsyncioTestCase):
    async def test_fast_primary_speaks_each_sentence_without_filler(self):
        speaker = Speaker()
        log = await manager(model(5), speaker=speaker).run("p")
        self.assertEqual(log.spoken, list(TWO))
        self.assertEqual(speaker.said, list(TWO))  # two separate sentences, spoken as each completed
        self.assertFalse(log.filler or log.fallback or log.interrupted)

    async def test_late_first_token_plays_filler_but_never_records_it(self):
        speaker = Speaker()
        log = await manager(model(120), speaker=speaker).run("p")
        self.assertEqual(speaker.said[0], FILLER)
        self.assertTrue(log.filler)
        self.assertFalse(log.fallback)
        self.assertEqual(log.spoken, list(TWO))  # history holds what the caller heard from the model, not the clip

    async def test_after_filler_fallback_waits_only_until_the_hard_cap(self):
        t0 = time.monotonic()
        log = await manager(model(2000)).run("p")
        elapsed = time.monotonic() - t0
        self.assertTrue(log.filler and log.fallback)
        self.assertEqual(log.spoken, ["Fallback answer."])
        self.assertLess(elapsed, 0.37)  # hard cap 0.30 s + fallback; a fresh cap after the filler would be >= 0.36 s

    async def test_provider_error_switches_at_once_without_filler(self):
        t0 = time.monotonic()
        log = await manager(model(0, error=ConnectionError("503"))).run("p")
        self.assertLess(time.monotonic() - t0, 0.05)  # well inside the 60 ms first-token budget
        self.assertTrue(log.fallback)
        self.assertFalse(log.filler)

    async def test_cb3_region_down_both_models_fail_so_caller_goes_to_ivr(self):
        with self.assertRaises(TimeoutError):  # the caller of run() routes to a human or the drilled IVR failover
            down = ConnectionError("region down")
            await manager(model(0, error=down), model(0, error=down)).run("p")
        with self.assertRaises(TimeoutError):
            await manager(model(2000), model(2000)).run("p")

    async def test_barge_in_mid_answer_stops_and_keeps_only_heard_sentences(self):
        speaker = Speaker(secs=0.05)
        tm = manager(model(5, ("First sentence. ", "Second sentence. ", "Third.")), speaker=speaker)
        asyncio.get_running_loop().call_later(0.08, tm.barge_in.set)  # during the second sentence
        log = await tm.run("p")
        self.assertTrue(log.interrupted)
        self.assertEqual(log.spoken, ["First sentence. "])  # the cut sentence is not in the history
        self.assertNotIn("Third.", speaker.said)  # the rest is dropped, never played

    async def test_barge_in_during_filler_neither_falls_back_nor_raises(self):
        tm = manager(model(2000), speaker=Speaker(filler_secs=0.2))
        asyncio.get_running_loop().call_later(0.1, tm.barge_in.set)  # the filler starts at 60 ms
        log = await tm.run("p")
        self.assertTrue(log.filler and log.interrupted)
        self.assertFalse(log.fallback)
        self.assertEqual(log.spoken, [])

    async def test_stale_barge_in_from_the_last_turn_is_cleared(self):
        tm = manager(model(5))
        tm.barge_in.set()
        log = await tm.run("p")
        self.assertFalse(log.interrupted)
        self.assertEqual(log.spoken, list(TWO))

    async def test_devanagari_danda_ends_a_sentence(self):
        speaker = Speaker()
        await manager(model(5, ("आपका रिचार्ज सफल रहा। ", "धन्यवाद।")), speaker=speaker).run("p")
        self.assertEqual(speaker.said, ["आपका रिचार्ज सफल रहा। ", "धन्यवाद।"])

    async def test_stream_dying_mid_answer_ends_the_turn_without_hanging(self):
        log = await asyncio.wait_for(manager(model(5, ("Part one. ", "Part tw"), error=ConnectionError("reset"),
                                                   error_after=True)).run("p"), timeout=1)
        self.assertEqual(log.spoken[0], "Part one. ")
        self.assertFalse(log.fallback)  # the sketch then flushes the fragment it holds ("Part tw"): see README gaps

    async def test_cb1_slower_successor_is_masked_by_filler_but_fails_the_ci_gate(self):
        async def answer_ms(delay):
            speaker, t0 = Speaker(), time.monotonic()
            log = await manager(model(delay), speaker=speaker).run("p")
            return log, (time.monotonic() - t0) * 1000
        pinned, pinned_ms = await answer_ms(30)
        successor, successor_ms = await answer_ms(30 + 100)  # +400 ms at full scale is past the filler budget
        self.assertFalse(pinned.filler)
        self.assertTrue(successor.filler and not successor.fallback)  # the caller hears the clip at 60 ms
        self.assertFalse(latency_gate(pinned_ms, successor_ms))  # but the replay p95 gate blocks the upgrade


class LatencyGateTests(unittest.TestCase):
    def test_gate_allows_under_ten_percent_and_blocks_at_ten(self):
        self.assertTrue(latency_gate(1500, 1640))
        self.assertFalse(latency_gate(1500, 1650))
        self.assertFalse(latency_gate(1500, 1900))  # curveball 1: p95 1.5 s -> 1.9 s


if __name__ == "__main__":
    unittest.main()
