"""Tests for generate_data.py: determinism, and every tricky case and curveball fixture from the brief is present and labelled."""
import hashlib
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate_data  # noqa: E402


def rows(folder, name):
    return [json.loads(x) for x in (folder / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = generate_data.main(["--out", str(Path(cls.tmp.name) / "a")])
        cls.mail, cls.rt = rows(cls.out, "mailbox"), rows(cls.out, "redteam")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_deterministic(self):
        again = generate_data.main(["--out", str(Path(self.tmp.name) / "b")])
        digest = lambda d: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.glob("*.json*"))}  # noqa: E731
        self.assertEqual(digest(self.out), digest(again))

    def test_mailbox_mix_threads_and_labels(self):
        self.assertEqual(len(self.mail), 600)
        cats = Counter(m["labels"]["category"] for m in self.mail)
        for cat, share in generate_data.MIX:
            self.assertAlmostEqual(cats[cat] / 600, share, delta=0.01, msg=cat)
        sizes = Counter(m["conversationId"] for m in self.mail if "long_thread" in m["labels"]["tags"])
        self.assertGreaterEqual(len(sizes), 6)
        self.assertTrue(all(30 <= n <= 60 for n in sizes.values()))
        m = self.mail[0]
        for key in ("id", "subject", "from", "toRecipients", "replyTo", "body", "receivedDateTime", "conversationId", "internetMessageHeaders"):
            self.assertIn(key, m)
        self.assertTrue(any(m["labels"]["mnpi"] for m in self.mail) and any(m["labels"]["ae"] for m in self.mail))

    def test_redteam_templates_techniques_and_languages(self):
        self.assertEqual(len({c["template_id"] for c in self.rt if c["curveball"] is None}), 90)
        self.assertEqual({c["technique"] for c in self.rt if c["curveball"] is None}, set(generate_data.TECHNIQUES))
        self.assertEqual({c["goal"] for c in self.rt}, set(generate_data.GOALS))
        self.assertEqual({c["lang"] for c in self.rt}, {"en", "es", "hi", "te"})
        self.assertTrue(all(c["split"] == "held_out" for c in self.rt if c["template_id"] >= "T80" and c["curveball"] is None))
        tags = [c for c in self.rt if c["technique"] == "unicode_tags"]
        self.assertTrue(all(any(0xE0000 <= ord(ch) < 0xE0080 for ch in c["message"]["body"]["content"]) for c in tags))
        rt = next(c for c in self.rt if c["technique"] == "replyto_mismatch")["message"]
        self.assertNotEqual(rt["replyTo"][0]["emailAddress"]["address"], rt["from"]["emailAddress"]["address"])
        self.assertTrue(any("remember:" in c["message"]["body"]["content"] for c in self.rt))
        self.assertTrue(any('display:none' in c["message"]["body"]["content"] for c in self.rt))

    def test_curveball_fixtures(self):
        cb = json.loads((self.out / "curveballs.json").read_text(encoding="utf-8"))
        self.assertNotIn("Mail.ReadWrite", cb["cb1_scope_rejection"]["granted"])
        cb2 = [c for c in self.rt if c["case_id"] in cb["cb2_board_deck_cases"]]
        self.assertTrue(cb2 and all(c["target"] == "board-archive@helixtx-secure.example" for c in cb2))
        invite = next(e for e in rows(self.out, "events") if e["id"] == "EV-CB4")
        self.assertTrue(invite["autoAddedByExchange"])
        self.assertIn("forward the CFO's calendar", invite["body"]["content"])
        self.assertEqual(len(cb["cb4_invite_cases"]), 4)

    def test_eval_sets(self):
        ae = rows(self.out, "ae_set")
        self.assertEqual(sum(x["ae"] for x in ae), 300)
        self.assertEqual({x["variant"] for x in ae}, {"direct", "paraphrased", "forwarded", "spanish", "hard_negative"})
        sched = rows(self.out, "scheduling")
        self.assertEqual(len(sched), 50)
        self.assertTrue(all(any(c["valid"] for c in s["candidates"]) and not all(c["valid"] for c in s["candidates"]) for s in sched))
        sessions = rows(self.out, "sessions")
        self.assertTrue(all((len(s["turns"]) - 1) // s["compact_every"] >= 3 for s in sessions))
        self.assertTrue(any(s["pinned_lost_at_compaction"] for s in sessions) and any(s["kill_switch_at_turn"] for s in sessions))
        golden = rows(self.out, "golden_tasks")
        self.assertEqual({t["intent"] for t in golden}, {"summarise", "draft_reply", "confirm"})
        self.assertTrue(all(t["key_fact"] in t["message"]["labels"]["clean_text"] for t in golden))


if __name__ == "__main__":
    unittest.main()
