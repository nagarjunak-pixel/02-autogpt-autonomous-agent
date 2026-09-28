import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from permission_trim import (MAX_SNAPSHOT_AGE_S, AccessError, AnswerCache, Chunk, Entitlements,  # noqa: E402
                             apply_wall_event, authorize, index_filter, matches_filter)

NOW = 1_000_000.0


def ent(groups=("grp-disputes",), screened=(), version=1, synced_at=NOW, user="U001"):
    return Entitlements(user, frozenset(groups), frozenset(screened), version, synced_at)


def chunk(doc="D1", matter="M-1042", groups=("grp-disputes",), ai=True):
    return Chunk(f"{doc}#p0", doc, matter, frozenset(groups), ai)


class Spy:
    """A fake batched DMS ACL check that records its calls."""
    def __init__(self, allowed=None):
        self.allowed, self.calls = allowed, []

    def __call__(self, user_id, doc_ids):
        self.calls.append((user_id, set(doc_ids)))
        return set(doc_ids) if self.allowed is None else set(self.allowed)


class TestAuthorize(unittest.TestCase):
    def test_deny_wins_over_group_allow(self):
        # the brief's tricky case: a user in a permitted group AND screened by a wall
        self.assertEqual(authorize([chunk()], ent(screened={"M-1042"}), Spy(), NOW), [])

    def test_no_shared_group_is_dropped(self):
        self.assertEqual(authorize([chunk(groups=("grp-ma",))], ent(), Spy(), NOW), [])

    def test_stale_snapshot_fails_closed(self):
        with self.assertRaises(AccessError):
            authorize([chunk()], ent(synced_at=NOW - MAX_SNAPSHOT_AGE_S - 1), Spy(), NOW)
        self.assertEqual(len(authorize([chunk()], ent(synced_at=NOW - MAX_SNAPSHOT_AGE_S), Spy(), NOW)), 1)

    def test_no_live_call_when_nothing_survives(self):
        spy = Spy()
        authorize([chunk(matter="M-1011")], ent(screened={"M-1011"}), spy, NOW)
        self.assertEqual(spy.calls, [])

    def test_one_batched_live_call_and_dms_has_final_say(self):
        spy = Spy(allowed={"D2"})
        kept = authorize([chunk("D1"), chunk("D2"), chunk("D3")], ent(), spy, NOW)
        self.assertEqual([c.doc_id for c in kept], ["D2"])
        self.assertEqual(spy.calls, [("U001", {"D1", "D2", "D3"})])

    def test_ai_opt_out_matter_never_passes(self):
        # curveball 5 (Copilot bake-off) re-runs the ai_permitted suite; brief §9 CW1226324 lesson
        self.assertEqual(authorize([chunk(ai=False)], ent(), Spy(), NOW), [])

    def test_index_filter_is_a_pre_filter_with_the_same_semantics(self):
        e = ent(groups=("grp-ma", "grp-disputes"), screened={"M-1042"})
        flt = index_filter(e)
        self.assertEqual(flt, {"allow_groups_any": ["grp-disputes", "grp-ma"], "matter_id_none_of": ["M-1042"],
                               "ai_permitted": True})
        for c in [chunk(), chunk(matter="M-1011"), chunk(ai=False), chunk(groups=("grp-regulatory",))]:
            self.assertEqual(matches_filter(c, flt), bool(authorize([c], e, Spy(), NOW)), c)


class TestAnswerCache(unittest.TestCase):
    def test_key_carries_user_version_and_corpus_and_normalises_query(self):
        cache, e = AnswerCache(), ent()
        k = cache.key(e, "  What is   the PRICE? ", "c1")
        self.assertEqual(k, cache.key(e, "what is the price?", "c1"))
        self.assertNotEqual(k, cache.key(ent(version=2), "what is the price?", "c1"))
        self.assertNotEqual(k, cache.key(ent(user="U002"), "what is the price?", "c1"))
        self.assertNotEqual(k, cache.key(e, "what is the price?", "c2"))

    def test_hit_is_reauthorised_and_evicted_when_a_cited_doc_is_forbidden(self):
        # curveball 2 as well: once the DMS deletes a document, a cached answer citing it must not be served
        cache, e = AnswerCache(), ent()
        k = cache.key(e, "q", "c1")
        cache.put(k, "answer", [chunk("D1"), chunk("D2")])
        self.assertEqual(cache.get(k, e, Spy(), NOW), "answer")
        self.assertIsNone(cache.get(k, e, Spy(allowed={"D1"}), NOW))
        self.assertIsNone(cache.get(k, e, Spy(), NOW))  # evicted, not just hidden

    def test_cb1_new_wall_hides_cached_answers_before_the_dms_catches_up(self):
        cache, before = AnswerCache(), ent()
        k_old = cache.key(before, "summarise M-1042", "c1")
        cache.put(k_old, "M-1042 summary", [chunk()])
        after = apply_wall_event(before, "M-1042")  # the DMS still allows everything (Spy())
        self.assertNotEqual(after.version, before.version)
        self.assertIsNone(cache.get(cache.key(after, "summarise M-1042", "c1"), after, Spy(), NOW))
        self.assertIsNone(cache.get(k_old, after, Spy(), NOW))  # even a replayed old key is re-authorised
        self.assertEqual(after.synced_at, before.synced_at)

    def test_stale_snapshot_fails_closed_through_the_cache(self):
        cache, e = AnswerCache(), ent(synced_at=NOW - 3600)
        cache.put("k", "answer", [chunk()])
        with self.assertRaises(AccessError):
            cache.get("k", e, Spy(), NOW)


if __name__ == "__main__":
    unittest.main()
