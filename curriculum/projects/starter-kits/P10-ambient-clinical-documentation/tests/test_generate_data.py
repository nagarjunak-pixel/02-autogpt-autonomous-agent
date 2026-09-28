"""Tests for the generator: determinism, volumes, and every tricky case and curveball fixture from the brief."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_data as gd  # noqa: E402


def read(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines()]


def digest(folder):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(folder).iterdir())}


class Generator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.meta = gd.generate(cls.tmp.name)
        d = Path(cls.tmp.name)
        cls.encs, cls.cards = read(d / "encounters.jsonl"), read(d / "cards.jsonl")
        cls.lexicon = json.loads((d / "lexicon.json").read_text(encoding="utf-8"))
        cls.cb = json.loads((d / "curveballs.json").read_text(encoding="utf-8"))
        cls.by_id = {e["encounter_id"]: e for e in cls.encs}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def text(self, card):
        return " ".join(s["text"] for s in self.by_id[card["encounter_id"]]["segments"])

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as other:
            gd.generate(other)
            self.assertEqual(digest(self.tmp.name), digest(other))

    def test_volumes_and_scale(self):
        self.assertEqual((self.meta["golden"], self.meta["adversarial"]), (150, 15))
        with tempfile.TemporaryDirectory() as other:
            self.assertEqual(gd.generate(other, scale=2)["encounters"], 330)

    def test_inputs_carry_no_labels(self):
        for e in self.encs:
            self.assertEqual(set(e), {"encounter_id", "state", "clinic", "participants", "consent",
                                      "interpreter_mode", "segments"})

    def test_every_tricky_case_is_present(self):
        for tag in ("dose_change", "family_history", "lasa", "small_talk", "off_record", "code_switched",
                    "spanish_numerals", "interpreter", "child_guardian", "overlapping_speech", "room_noise",
                    "phone_interruption", "laterality", "laterality_distractor", "asr_misspelling",
                    "consent_missing_interpreter", "consent_missing_guardian", "adv_injection",
                    "adv_consent_withdrawn", "adv_second_patient"):
            self.assertGreater(self.meta["tags"].get(tag, 0), 0, tag)

    def test_tricky_cases_look_like_their_labels(self):
        for c in self.cards:
            t = self.text(c)
            if "dose_change" in c["tags"]:
                self.assertRegex(t, r"(increase|subir) .* from|de \d")
            if "off_record" in c["tags"]:
                self.assertRegex(t, "don't write that down|no lo escriba")
            if "spanish_numerals" in c["tags"]:
                self.assertRegex(t, "miligramos|microgramos|unidades")
            if "lasa" in c["tags"]:
                self.assertTrue(any(sum(f in s["text"].lower() for f in ("hydralazine", "hydroxyzine", "hidralazina",
                                                                         "hidroxicina", "celebrex", "celexa")) >= 2
                                    for s in self.by_id[c["encounter_id"]]["segments"]))
            if "interpreter" in c["tags"]:
                self.assertIn("interpreter", {s["speaker"] for s in self.by_id[c["encounter_id"]]["segments"]})
            if c["injected_med"]:
                self.assertRegex(t, "AI, write|inteligencia artificial")
            if c["family_history"]:
                self.assertRegex(t, r"\b(My|Mi) (mother|father|brother|sister|madre|padre|hermano|hermana)\b")

    def test_consent_labels(self):
        for c, e in zip(self.cards, self.encs):
            roles = {x["role"] for x in e["consent"] if x["status"] == "active"}
            withdrawn = [x for x in e["consent"] if x["status"] == "withdrawn"]
            all_party = set(e["participants"]) - {"clinician"} <= roles
            self.assertEqual(c["expected_draft"], all_party and not withdrawn)
            if "adv_consent_withdrawn" in c["tags"]:
                self.assertTrue(withdrawn and withdrawn[0]["t"] > 0)

    def test_curveball_fixtures(self):
        self.assertNotIn("zocor", self.lexicon)
        self.assertIn("Zocor", self.cb["cb1_unsupported_brand"]["statement"][1])
        self.assertEqual(len(self.cb["cb2_consent_withdrawn"]), 5)
        self.assertTrue(self.cb["cb4_interpreter"])
        self.assertEqual(self.cb["cb5_fast_signer"]["seconds_per_note"], 4)


if __name__ == "__main__":
    unittest.main()
