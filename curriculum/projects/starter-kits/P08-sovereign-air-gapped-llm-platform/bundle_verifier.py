"""Offline model-bundle verifier (brief §7). Runs inside the air-gapped enclave, before promotion to the registry.

    python3 bundle_verifier.py <bundle_dir> <pubkey.raw> <prod_version>   # exit 0 = PROMOTE, 1 = reject

Kept from the reviewed sketch: signature over the exact manifest bytes (checked before anything is parsed);
anti-rollback and anti-replay (version must be newer than production); unsafe paths ("..", absolute, symlinks);
pickle-capable formats refused (case-insensitive); hash and size of every listed file; unlisted files refused; the eval
report must be covered by the signed manifest and bound to THESE weights; per-language eval gates (a Telugu loss
cannot hide in the average); safety-critical failures and a missing licence approver block promotion.

Added for the kit (each fails closed, and each has a test): the Ed25519 check uses the stdlib `ed25519_ref` instead of
`cryptography`; a missing manifest or signature, a missing or malformed eval report and a missing language slice
return errors instead of crashing; `aibom_gaps()` lists missing CERT-In AIBOM elements (not binding by default).
"""
import hashlib
import json
import sys
from pathlib import Path

from ed25519_ref import InvalidSignature, verify

FORBIDDEN = {".pkl", ".pickle", ".pt", ".pth", ".bin"}   # pickle-capable formats; safetensors only
MIN_DELTA = {"overall": 0.0, "te": -1.0, "hi": -1.0, "en": -1.0}  # points vs current production
AIBOM_FIELDS = ("version", "developer", "licence", "dependencies", "data_sources", "metrics", "intended_use",
                "vulnerabilities")   # CERT-In SBOM/AIBOM guidelines v2.0, minimum elements


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def weights_digest(files: list[dict]) -> str:
    """The digest an eval report must name: every weights file's path and hash, sorted."""
    weights = sorted(f"{e['path']}:{e['sha256']}" for e in files if e.get("role") == "weights")
    return hashlib.sha256("\n".join(weights).encode()).hexdigest()


def verify_signature(data: bytes, sig: bytes, pubkey_raw: bytes) -> None:
    """Private key stays in the staging-side HSM; only this public key exists inside the enclave."""
    verify(pubkey_raw, data, sig)  # raises InvalidSignature


def verify_bundle(bundle: Path, pubkey_raw: bytes, prod_version: int) -> list[str]:
    try:
        raw, sig = (bundle / "manifest.json").read_bytes(), (bundle / "manifest.sig").read_bytes()
    except OSError:
        return ["manifest or signature missing: quarantine bundle"]
    try:
        verify_signature(raw, sig, pubkey_raw)
    except InvalidSignature:
        return ["SIGNATURE INVALID: quarantine bundle and open a security incident"]
    m, errors, listed, safe = json.loads(raw), [], set(), set()
    if m["bundle_version"] <= prod_version:                 # anti-rollback / replay
        errors.append(f"version {m['bundle_version']} is not newer than production {prod_version}")
    for e in m["files"]:
        rel, p = Path(e["path"]), bundle / e["path"]
        if p.is_symlink() or not p.resolve().is_relative_to(bundle.resolve()):  # "..", absolute, symlinked dirs
            errors.append(f"unsafe path {rel}")
            continue
        listed.add(p.resolve())
        safe.add(e["path"])
        if p.suffix.lower() in FORBIDDEN:
            errors.append(f"forbidden file format {rel}")
        if not p.is_file() or p.stat().st_size != e["size"] or sha256(p) != e["sha256"]:
            errors.append(f"hash or size mismatch {rel}")
    control = {(bundle / n).resolve() for n in ("manifest.json", "manifest.sig")}
    errors += [f"unlisted file {p.relative_to(bundle)}" for p in sorted(bundle.rglob("*"))
               if p.is_file() and p.resolve() not in listed | control]
    # The eval report must itself be covered by the signed manifest, and must describe THESE weights.
    if m["eval_report"] not in {e["path"] for e in m["files"]}:
        return errors + ["eval report not covered by the signed manifest"]
    if m["eval_report"] not in safe:
        return errors                                        # already reported as unsafe; never read it
    try:
        ev = json.loads((bundle / m["eval_report"]).read_text(encoding="utf-8"))
        weights_ok, deltas = ev["weights_digest"] == weights_digest(m["files"]), ev["delta_vs_prod"]
        safety_failures = ev["safety_critical_failures"]
        if not isinstance(deltas, dict):
            raise TypeError("delta_vs_prod must be an object")
    except (OSError, ValueError, KeyError, TypeError):
        return errors + ["eval report missing or malformed"]
    if not weights_ok:
        errors.append("eval report was produced for different weights")
    for k, floor in MIN_DELTA.items():
        if not isinstance(deltas.get(k), (int, float)):
            errors.append(f"eval gate '{k}': no result for this slice")
        elif deltas[k] < floor:
            errors.append(f"eval gate '{k}': {deltas[k]:+.1f} pts < {floor:+.1f}")
    if safety_failures or not m.get("licence_approved_by"):
        errors.append("safety-critical eval failures or no recorded licence approval")
    return errors


def aibom_gaps(bundle: Path) -> list[str]:
    """Missing AIBOM minimum elements. Curveball 4 (provenance walk) ends here; make it binding if audit asks."""
    try:
        aibom = json.loads((bundle / "aibom.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return list(AIBOM_FIELDS)
    return [k for k in AIBOM_FIELDS if aibom.get(k) in (None, "", [], {})]


if __name__ == "__main__":
    try:
        errs = verify_bundle(Path(sys.argv[1]), Path(sys.argv[2]).read_bytes(), int(sys.argv[3]))
    except Exception as exc:  # noqa: BLE001  any surprise is a rejection, never a promotion
        errs = [f"VERIFIER ERROR ({type(exc).__name__}): {exc}"]
    print("\n".join(errs) or "PROMOTE: all checks passed")
    sys.exit(1 if errs else 0)
