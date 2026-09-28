"""Query-time permission trim and per-user answer cache: the control from brief P01 §7.

Kept from the reviewed sketch (tests/test_permission_trim.py covers each point):
- walls override group allows (deny wins);
- a stale entitlement snapshot fails closed with AccessError;
- no live DMS call when nothing survives the static trim; otherwise ONE batched call, and the DMS has the final say;
- cache keys carry user, entitlement version, corpus version and a normalised query hash;
- every cache hit is re-authorised, and evicted if any cited document is now forbidden.

Additions (all backwards compatible with the sketch):
- Chunk.ai_permitted, and authorize() drops ai_permitted=False chunks as defence in depth
  (the sketch enforced the flag only in the index pre-filter; brief §9 asks for its own tests);
- matches_filter(): reference semantics of index_filter() for an in-memory index;
- apply_wall_event(): a wall event adds a screened matter and bumps the version within seconds;
- AnswerCache.get(..., now=) for simulated clocks, and AnswerCache.entries() for deletion sweeps.
"""
import hashlib
import time
from dataclasses import dataclass, replace
from typing import Callable, Iterable, Optional

MAX_SNAPSHOT_AGE_S = 5 * 60  # backstop, well inside the 15-minute wall SLO


@dataclass(frozen=True)
class Entitlements:
    user_id: str
    groups: frozenset            # IdP + DMS groups, resolved transitively
    screened_matters: frozenset  # matters this user is walled OFF from (walls system)
    version: int                 # changes on ANY change to this user's access
    synced_at: float             # epoch seconds of the last successful sync


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    matter_id: str
    allow_groups: frozenset      # copied from the DMS ACL at index time
    ai_permitted: bool = True    # False for matters whose client guidelines forbid AI use


class AccessError(Exception):
    pass


def index_filter(ent: Entitlements) -> dict:
    """Pushed INTO the hybrid search as a pre-filter (filter-aware ANN, never post-filter only)."""
    return {"allow_groups_any": sorted(ent.groups), "matter_id_none_of": sorted(ent.screened_matters),
            "ai_permitted": True}  # matters of clients that restrict AI are never retrieved


def matches_filter(chunk: Chunk, flt: dict) -> bool:
    """What a search engine must do with index_filter(): apply it BEFORE ranking and top-k."""
    return (bool(chunk.allow_groups & set(flt["allow_groups_any"]))
            and chunk.matter_id not in flt["matter_id_none_of"]
            and chunk.ai_permitted == flt["ai_permitted"])


def authorize(chunks: Iterable[Chunk], ent: Entitlements,
              live_check: Callable[[str, set], set], now: Optional[float] = None) -> list:
    """Query-time trim: walls override allows, the DMS has the final say, fail closed."""
    now = time.time() if now is None else now
    if now - ent.synced_at > MAX_SNAPSHOT_AGE_S:
        raise AccessError("entitlement snapshot too old; failing closed")
    kept = [c for c in chunks
            if c.ai_permitted and c.matter_id not in ent.screened_matters and c.allow_groups & ent.groups]
    if not kept:
        return []
    allowed = live_check(ent.user_id, {c.doc_id for c in kept})  # one batched DMS call
    return [c for c in kept if c.doc_id in allowed]


def apply_wall_event(ent: Entitlements, matter_id: str) -> Entitlements:
    """A wall event is deny-only: screen the matter and change the version at once, before the DMS catches up.
    synced_at is deliberately NOT refreshed: a deny cannot make a stale group snapshot fresh."""
    if matter_id in ent.screened_matters:
        return ent
    return replace(ent, screened_matters=ent.screened_matters | {matter_id}, version=ent.version + 1)


class AnswerCache:
    """Per-user answer cache: key carries the entitlement version; every hit is re-authorised."""

    def __init__(self):
        self._store = {}

    def key(self, ent: Entitlements, query: str, corpus_version: str) -> str:
        q = hashlib.sha256(" ".join(query.lower().split()).encode()).hexdigest()
        return f"{ent.user_id}:{ent.version}:{corpus_version}:{q}"

    def get(self, key: str, ent: Entitlements, live_check, now: Optional[float] = None):
        hit = self._store.get(key)
        if hit is None:
            return None
        answer, cited = hit
        if authorize(cited, ent, live_check, now) != list(cited):  # a cited doc is now forbidden
            self._store.pop(key, None)
            return None
        return answer

    def put(self, key: str, answer, cited_chunks: Iterable[Chunk]) -> None:
        self._store[key] = (answer, tuple(cited_chunks))

    def entries(self) -> list:
        """(key, (answer, cited_chunks)) pairs, for deletion and erasure sweeps."""
        return list(self._store.items())
