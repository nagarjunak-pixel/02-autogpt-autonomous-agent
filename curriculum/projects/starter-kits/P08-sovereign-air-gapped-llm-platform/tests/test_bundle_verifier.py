"""Tests for the §7 verifier: every reviewed behaviour of the sketch, the kit's fail-closed additions, curveballs 2 and 5."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import ed25519_ref  # noqa: E402
from bundle_verifier import aibom_gaps, sha256, verify_bundle  # noqa: E402
from generate_data import write_bundle  # noqa: E402

KEY = hashlib.sha256(b"test HSM key").digest()
PUB = ed25519_ref.public_key(KEY)
PROD = 7


def relist(b: Path, rel: str):
    """Operator re-hashes a changed file and re-signs: the signature is valid again, so the other gates must catch it."""
    m = json.loads((b / "manifest.json").read_text())
    for e in m["files"]:
        if e["path"] == rel:
            e.update(size=(b / rel).stat().st_size, sha256=sha256(b / rel))
    raw = json.dumps(m).encode()
    (b / "manifest.json").write_bytes(raw)
    (b / "manifest.sig").write_bytes(ed25519_ref.sign(KEY, raw))


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def bundle(self, name="b", version=8, **kw):
        return write_bundle(self.root, name, version, key=KEY, **kw)

    def errors(self, b, prod=PROD):
        return verify_bundle(b, PUB, prod)

    def assertBlocked(self, b, fragment):
        errs = self.errors(b)
        self.assertTrue(any(fragment in e for e in errs), errs)

    def test_good_bundle_promotes(self):
        self.assertEqual(self.errors(self.bundle()), [])

    def test_signature_checked_before_anything_is_parsed(self):
        b = self.bundle()
        (b / "manifest.json").write_bytes((b / "manifest.json").read_bytes().replace(b'"bundle_version": 8', b'"bundle_version": 80'))
        self.assertEqual(self.errors(b), ["SIGNATURE INVALID: quarantine bundle and open a security incident"])
        (b / "manifest.json").write_bytes(b"{not json")          # garbage is rejected by signature, never parsed
        self.assertEqual(len(self.errors(b)), 1)

    def test_wrong_key_and_missing_signature(self):
        b = write_bundle(self.root, "evil", 8, key=hashlib.sha256(b"attacker").digest())
        self.assertBlocked(b, "SIGNATURE INVALID")
        (b / "manifest.sig").unlink()
        self.assertBlocked(b, "manifest or signature missing")

    def test_anti_rollback_and_replay(self):
        self.assertBlocked(self.bundle("old", 6), "not newer than production 7")
        self.assertBlocked(self.bundle("same", 7), "not newer than production 7")
        self.assertEqual(self.errors(self.bundle("new", 8)), [])

    def test_pickle_capable_formats_refused_case_insensitively(self):
        for name, rel in (("pt", "weights/model.pt"), ("bin", "weights/pytorch_model.BIN"), ("pkl", "tokenizer.pkl"),
                          ("pth", "weights/x.Pth")):
            self.assertBlocked(self.bundle(name, extra={rel: b"\x80\x04pickle"}), f"forbidden file format {rel}")

    def test_unsafe_paths(self):
        (self.root / "outside.safetensors").write_bytes(b"outside")

        def listed(path):
            return lambda b, m: m["files"].append({"path": path, "size": 7, "sha256": hashlib.sha256(b"outside").hexdigest(),
                                                  "role": "weights"})
        self.assertBlocked(self.bundle("dots", mutate=listed("../outside.safetensors")), "unsafe path ../outside.safetensors")
        self.assertBlocked(self.bundle("abs", mutate=listed(str(self.root / "outside.safetensors"))), "unsafe path")

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_symlinks_listed_or_not(self):
        def link(b, m):
            os.symlink(self.root / "outside.safetensors", b / "weights" / "x.safetensors")
            m["files"].append({"path": "weights/x.safetensors", "size": 7, "sha256": hashlib.sha256(b"outside").hexdigest(),
                               "role": "weights"})
        (self.root / "outside.safetensors").write_bytes(b"outside")
        self.assertBlocked(self.bundle("listed", mutate=link), "unsafe path weights/x.safetensors")
        b = self.bundle("dropped")
        os.symlink(self.root / "outside.safetensors", b / "weights" / "y.safetensors")
        self.assertBlocked(b, "unlisted file weights/y.safetensors")

    def test_symlinked_eval_report_is_never_read(self):
        (self.root / "evil.json").write_text("{not json")

        def link(b, m):
            (b / "eval" / "report.json").unlink()
            os.symlink(self.root / "evil.json", b / "eval" / "report.json")
        if os.name == "nt":
            self.skipTest("symlinks need privileges on Windows")
        errs = self.errors(self.bundle(mutate=link))
        self.assertIn("unsafe path eval/report.json", errs)
        self.assertNotIn("eval report missing or malformed", errs)

    def test_tampered_missing_and_resized_files(self):
        b = self.bundle()
        (b / "weights/model-00001-of-00002.safetensors").write_bytes(b"tampered")
        (b / "config.json").unlink()
        errs = self.errors(b)
        self.assertIn("hash or size mismatch weights/model-00001-of-00002.safetensors", errs)
        self.assertIn("hash or size mismatch config.json", errs)

    def test_unlisted_file_dropped_in_after_signing(self):
        b = self.bundle()
        (b / "run.py").write_text("import os\n")
        self.assertBlocked(b, "unlisted file run.py")

    def test_eval_report_must_be_signed_and_bound_to_these_weights(self):
        uncovered = self.bundle("u", mutate=lambda b, m: m["files"].remove(next(e for e in m["files"] if e["path"] == "eval/report.json")))
        self.assertBlocked(uncovered, "eval report not covered by the signed manifest")
        self.assertBlocked(self.bundle("stale", stale_report=True), "eval report was produced for different weights")

    def test_language_gates_cannot_be_averaged_away(self):
        self.assertBlocked(self.bundle("te", delta={"overall": 0.9, "te": -6.0, "hi": 0.4, "en": 2.1}), "eval gate 'te': -6.0 pts")
        self.assertEqual(self.errors(self.bundle("edge", delta={"overall": 0.0, "te": -1.0, "hi": -1.0, "en": -1.0})), [])
        self.assertBlocked(self.bundle("avg", delta={"overall": -0.1, "te": 1, "hi": 1, "en": 1}), "eval gate 'overall'")

    def test_missing_slice_or_malformed_report_fails_closed(self):
        self.assertBlocked(self.bundle("noslice", delta={"overall": 1.0, "hi": 0.2, "en": 1.1}), "eval gate 'te': no result")
        b = self.bundle("bad")
        (b / "eval/report.json").write_text("{not json")
        relist(b, "eval/report.json")
        self.assertIn("eval report missing or malformed", self.errors(b))

    def test_safety_failures_block(self):
        self.assertBlocked(self.bundle(safety=1), "safety-critical eval failures")

    def test_curveball_2_unapproved_custom_licence_blocks(self):
        self.assertBlocked(self.bundle(licence="Llama 4 Community Licence + AUP", approver=None), "no recorded licence approval")

    def test_curveball_5_telugu_gain_does_not_excuse_hindi_loss(self):
        self.assertBlocked(self.bundle("r", 9, delta={"overall": 2.0, "te": 8.0, "hi": -2.4, "en": 0.1}), "eval gate 'hi': -2.4 pts")
        self.assertEqual(self.errors(self.bundle("c", 9, delta={"overall": 2.3, "te": 8.0, "hi": 0.2, "en": 0.1})), [])

    def test_reviewed_custom_code_travels_as_listed_files(self):
        self.assertEqual(self.errors(self.bundle(extra={"modeling_custom.py": b"# reviewed\n"})), [])

    def test_aibom_gaps(self):
        self.assertEqual(aibom_gaps(self.bundle("full")), [])
        self.assertEqual(aibom_gaps(self.bundle("gaps", aibom_drop=("licence", "data_sources"))), ["licence", "data_sources"])

    def test_cli_exit_codes(self):
        good, bad = self.bundle("good"), self.bundle("bad", 6)
        (self.root / "pub.raw").write_bytes(PUB)
        run = lambda b: subprocess.run([sys.executable, str(KIT / "bundle_verifier.py"), str(b), str(self.root / "pub.raw"),  # noqa: E731
                                        str(PROD)], capture_output=True, text=True)
        self.assertEqual(run(good).returncode, 0)
        self.assertIn("PROMOTE", run(good).stdout)
        self.assertEqual(run(bad).returncode, 1)
        self.assertEqual(run(self.root / "no-such-bundle").returncode, 1)


class Ed25519Tests(unittest.TestCase):
    def test_rfc8032_vector_1(self):
        sk = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
        self.assertEqual(ed25519_ref.public_key(sk).hex(), "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
        sig = ed25519_ref.sign(sk, b"")
        self.assertEqual(sig.hex(), "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701"
                                    "cf9b46bd25bf5f0595bbe24655141438e7a100b")
        ed25519_ref.verify(ed25519_ref.public_key(sk), b"", sig)
        with self.assertRaises(ed25519_ref.InvalidSignature):
            ed25519_ref.verify(ed25519_ref.public_key(sk), b"x", sig)
        with self.assertRaises(ed25519_ref.InvalidSignature):
            ed25519_ref.verify(ed25519_ref.public_key(sk), b"", sig[:-1] + bytes([sig[-1] ^ 1]))


if __name__ == "__main__":
    unittest.main()
