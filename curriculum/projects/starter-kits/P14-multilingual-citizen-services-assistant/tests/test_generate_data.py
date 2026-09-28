"""Tests for generate_data.py: determinism, volumes, and every tricky case and curveball fixture from the brief."""
import hashlib
import hmac
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
        cls.docs, cls.labels = rows(cls.out, "corpus"), {x["doc_id"]: x for x in rows(cls.out, "corpus_labels")}
        cls.queries = rows(cls.out, "queries")
        cls.rules = json.loads((cls.out / "rules.json").read_text(encoding="utf-8"))
        cls.forged = json.loads((cls.out / "forged_docs.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_deterministic(self):
        again = generate_data.main(["--out", str(Path(self.tmp.name) / "b")])
        digest = lambda d: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.iterdir())}  # noqa: E731
        self.assertEqual(digest(self.out), digest(again))

    def test_corpus_schema_and_tricky_documents(self):
        self.assertEqual(len(self.rules), 40)
        self.assertEqual(len(self.docs), 406)
        for key in ("go_no", "date", "scheme_id", "valid_from", "supersedes", "lang", "signed", "source"):
            self.assertIn(key, self.docs[0])
        tags = Counter(t for x in self.labels.values() for t in x["tags"])
        self.assertAlmostEqual(tags["scanned"] / 400, 0.35, delta=0.06)
        self.assertAlmostEqual(tags["legacy_font"] / 400, 0.10, delta=0.04)
        self.assertGreater(tags["income_table"], 0)
        legacy = next(d for d in self.docs if "legacy_font" in self.labels[d["doc_id"]]["tags"])
        self.assertIn("à°", legacy["text"])  # mojibake, not Telugu
        self.assertEqual(len({d["scheme_id"] for d in self.docs if d["lang"] == "ur" and d["source"] == "registry"}), 5)
        self.assertTrue(any(d["supersedes"] for d in self.docs))
        self.assertTrue(any(d["source"] == "vendor_faq" for d in self.docs))

    def test_registry_lists_only_genuine_documents_and_verifies(self):
        reg = json.loads((self.out / "registry.json").read_text(encoding="utf-8"))
        body = json.dumps(reg["manifest"], sort_keys=True, ensure_ascii=False).encode("utf-8")
        self.assertEqual(reg["signature"], hmac.new(generate_data.REGISTRY_DEMO_KEY, body, hashlib.sha256).hexdigest())
        listed = {m["doc_id"]: m["sha256"] for m in reg["manifest"]}
        for d in self.docs:
            self.assertEqual(d["doc_id"] in listed, d["source"] == "registry")
            if d["doc_id"] in listed:
                self.assertEqual(listed[d["doc_id"]], hashlib.sha256(d["text"].encode("utf-8")).hexdigest())

    def test_cb1_forged_circular_and_red_team_folder(self):
        self.assertEqual(len(self.forged), 6)
        self.assertEqual({f["kind"] for f in self.forged}, {"forged_go", "fee_scam", "hidden_instruction"})
        cb1 = [f for f in self.forged if f["curveball"] == "cb1_forged_circular"]
        self.assertTrue(cb1 and all(f["facts"]["income"] > in_force for f in cb1
                                    for in_force in [self.rules["S01"]["versions"][-1]["income_max"]]))
        by_id = {d["doc_id"]: d for d in self.docs}
        self.assertTrue(by_id[cb1[0]["doc_id"]]["signed"])  # it claims a signature; only the registry can say no
        self.assertTrue(any(generate_data.UPI in by_id[f["doc_id"]]["text"] for f in self.forged))
        self.assertTrue(any("color:#ffffff" in by_id[f["doc_id"]]["text"] for f in self.forged))

    def test_golden_slices_and_other_query_sets(self):
        golden = Counter((q["lang"], q["channel"], q["gold"]["answerable"]) for q in self.queries if q["split"] == "golden")
        for lang in generate_data.LANGS:
            self.assertEqual((golden[(lang, "text", True)], golden[(lang, "text", False)]), (150, 50))
        for lang in ("te", "hi", "ur", "en"):
            self.assertEqual((golden[(lang, "voice", True)], golden[(lang, "voice", False)]), (120, 30))
        splits = Counter(q["split"] for q in self.queries)
        self.assertEqual((splits["political"], splits["injection"], splits["forged_probe"], splits["cb2"]), (100, 50, 30, 20))
        self.assertTrue(all(q["gold"]["doc_ids"] for q in self.queries if q["gold"].get("answerable")))

    def test_query_tricky_cases(self):
        tags = Counter(t for q in self.queries for t in q["gold"]["tags"])
        for tag in ("arabic_codepoints", "code_mixed", "misspelling", "dialect", "unanswerable"):
            self.assertGreater(tags[tag], 0, tag)
        arabic = [q["text"] for q in self.queries if "arabic_codepoints" in q["gold"]["tags"]]
        self.assertTrue(all(any(ch in t for ch in "يكه") for t in arabic))
        self.assertFalse(any(ch in d["text"] for d in self.docs for ch in "يكه"))  # documents use Urdu code points
        self.assertIn("naaku", " ".join(q["text"] for q in self.queries if q["lang"] == "te-Latn"))
        self.assertTrue(any("0000 1111 2222" in q["text"] for q in self.queries if q["split"] == "injection"))

    def test_cb2_overnight_rule_change(self):
        s01 = self.rules["S01"]["versions"]
        self.assertEqual((s01[-1]["valid_from"], s01[-1]["age_min"], s01[-2]["age_min"]), ("2026-09-24", 57, 60))
        cb2 = [q for q in self.queries if q["split"] == "cb2"]
        self.assertTrue(all(q["date"] > "2026-09-24" and q["gold"]["fact"] == "57" for q in cb2))
        new_go = {d["doc_id"] for d in self.docs if d["go_no"] == s01[-1]["go_no"]}
        self.assertTrue(all(set(q["gold"]["doc_ids"]) <= new_go | {d["doc_id"] for d in self.docs if d["scheme_id"] == "S01"} for q in cb2))
        self.assertTrue(all(set(q["gold"]["doc_ids"]) & new_go for q in cb2))

    def test_clause_level_amendment_changes_gold_per_clause(self):
        q_income = next(q for q in self.queries if q["split"] == "golden" and q["gold"].get("scheme_id") == "S01" and q["gold"].get("intent") == "income")
        q_age = next(q for q in self.queries if q["split"] == "golden" and q["gold"].get("scheme_id") == "S01" and q["gold"].get("intent") == "age")
        base = {d["doc_id"] for d in self.docs if d["go_no"] == self.rules["S01"]["versions"][0]["go_no"]}
        self.assertFalse(base & set(q_income["gold"]["doc_ids"]))  # income clause superseded in 2025
        self.assertTrue(base & set(q_age["gold"]["doc_ids"]))       # age clause still in force on the query date

    def test_profiles_cover_exclusions_boundaries_and_cb2(self):
        profiles = rows(self.out, "profiles")
        self.assertEqual(len(profiles), 400)
        outcomes = Counter(p["gold"]["outcome"] for p in profiles)
        self.assertGreater(min(outcomes.values()), 80)
        tags = Counter(t for p in profiles for t in p["gold"]["tags"])
        self.assertGreater(tags["exclusion"], 0)
        self.assertGreater(tags["cb2_rule_change"], 0)
        self.assertTrue(any(p["gold"]["minor"] for p in profiles))

    def test_status_fixtures(self):
        apps = rows(self.out, "applications")
        self.assertEqual(len(apps), 5000)
        self.assertTrue(all(a["mobile"].startswith("55") and len(a["mobile"]) == 10 for a in apps))
        self.assertTrue(any(a["minor"] for a in apps) and any(a["shared_phone"] for a in apps))
        red = rows(self.out, "status_redteam")
        self.assertEqual(len(red), 500)
        owner = {a["app_id"]: a["mobile"] for a in apps}
        self.assertTrue(all(r["mobile"][-10:] != owner[r["app_id"]] for r in red))
        scen = rows(self.out, "status_scenarios")
        self.assertEqual((len(scen), sum(s["gold"]["stale"] for s in scen)), (200, 20))


if __name__ == "__main__":
    unittest.main()
