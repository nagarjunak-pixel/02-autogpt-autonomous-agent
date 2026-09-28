"""The brief's §7 control for P03: field validation, confidence routing and seeded-error injection.

Kept from the reviewed sketch (each point has a test in tests/test_review_router.py):
- No deny path. REJECT means "re-scan or re-key this extraction", never a claim decision, and claim_status()
  has no approve, deny or close state, so text inside a document ("approve this claim") has nothing to act on.
- A field with any validation error never auto-accepts, however confident the extractor is.
- Thresholds are per field type and apply to *calibrated* probabilities (fit THRESH from your calibration curves).
- Seeds come only from auto-accepted, independently verified SEEDABLE fields with at least two digits.
- A seed is a new Field that renders exactly like a normal item, and its value never reaches the claim record.
Added: shape (schema) checks before any date or amount comparison, handwritten fields always reviewed, the motor
cross-document checks, FCU fraud signals (flags only), claim_status() and commit().
"""
import random
import re
from dataclasses import dataclass, field

AUTO, REVIEW, REJECT = "auto_accept", "needs_review", "reject_extraction"  # REJECT = re-scan/re-key, never a denial
STATUSES = ("prefilled_for_adjuster", "needs_review", "documents_requested")  # no approve, deny or close state
CRITICAL = {"policy_no", "total_billed", "admission_date", "discharge_date", "vehicle_reg_no"}
SEEDABLE = {"total_billed", "invoice_no", "vehicle_reg_no"}  # fields where a one-digit slip is plausible
THRESH = {"critical": 0.98, "standard": 0.90, "floor": 0.40}  # from calibration curves, per field type
ISO = r"20[0-9]{2}-[01][0-9]-[0-3][0-9]"
AMT = r"₹?[0-9][0-9,]*(\.[0-9]{1,2})?"
REG = r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}"
SCHEMA = {  # shape only: constrained decoding can guarantee shape, never truth (ADR 3). ASCII digits only.
    "policy_no": r"KGI-[HM]-[0-9]{7}", "invoice_no": r"[A-Z]{2,4}-[0-9]{4,6}", "patient_name": r"\S.{1,60}",
    "total_billed": AMT, "claimed_amount": AMT, "admission_date": ISO, "discharge_date": ISO, "loss_date": ISO,
    "fir_date": ISO, "fir_no": r"[0-9]{3,4}/20[0-9]{2}", "vehicle_reg_no": REG, "fir_reg_no": REG}
CONFLICTS = {"policy_mismatch", "total_not_sum_of_line_items", "discharge_before_admission", "duplicate_bill",
             "fir_after_claim_date", "reg_mismatch_rc_fir", "exif_before_policy_start"}


@dataclass
class Field:
    name: str
    value: str
    confidence: float                    # calibrated probability, not the model's self-report
    evidence: tuple | None               # (doc_id, page, bbox); None = not grounded on any page
    verified: bool = False               # matched an authoritative source (policy system, FHIR bundle)
    handwritten: bool = False            # added: handwritten fields are always reviewed (brief §5)
    errors: list = field(default_factory=list)
    seeded_true_value: str | None = None


def amount(s: str) -> float:
    return float(s.replace(",", "").replace("₹", "").strip())   # "₹48,500" -> 48500.0


def valid_shape(f: Field) -> bool:
    return f.name not in SCHEMA or re.fullmatch(SCHEMA[f.name], f.value or "") is not None


def validate(fs: dict, policy: dict | None, line_items: list[str], claim_date: str | None = None) -> None:
    for f in fs.values():
        if f.evidence is None:
            f.errors.append("no_evidence_span")
        if not valid_shape(f):
            f.errors.append("schema_invalid")      # never compare or add values that failed the schema
    ok = lambda n: n in fs and "schema_invalid" not in fs[n].errors
    if ok("policy_no") and (policy is None or fs["policy_no"].value != policy["policy_no"]):
        fs["policy_no"].errors.append("policy_mismatch")
    if ok("total_billed") and line_items:
        tb = fs["total_billed"]
        try:
            if abs(sum(map(amount, line_items)) - amount(tb.value)) > 1:   # rupee rounding
                tb.errors.append("total_not_sum_of_line_items")
        except ValueError:
            tb.errors.append("line_items_unreadable")
    if ok("admission_date") and ok("discharge_date") and fs["discharge_date"].value < fs["admission_date"].value:
        fs["discharge_date"].errors.append("discharge_before_admission")   # ISO-8601 strings compare correctly
    if ok("fir_date") and claim_date and fs["fir_date"].value > claim_date:
        fs["fir_date"].errors.append("fir_after_claim_date")
    if ok("vehicle_reg_no") and ok("fir_reg_no") and fs["vehicle_reg_no"].value != fs["fir_reg_no"].value:
        fs["fir_reg_no"].errors.append("reg_mismatch_rc_fir")


def fraud_signals(fs: dict, policy: dict | None, exif_dates: list[str], seen_bills: set, hospital_id=None) -> list:
    """Reasoned flags for the Fraud Control Unit. Flags only: nothing here changes a field, a route or a status."""
    flags = []
    if policy and any(d < policy["start"] for d in exif_dates):
        flags.append("exif_before_policy_start")
    inv = fs.get("invoice_no")
    if inv is not None and valid_shape(inv):
        if (hospital_id, inv.value) in seen_bills:
            flags.append("duplicate_bill")
        seen_bills.add((hospital_id, inv.value))
    return flags


def route(f: Field) -> str:
    if f.errors:
        return REJECT if f.confidence < THRESH["floor"] else REVIEW
    if f.handwritten:
        return REVIEW                                          # added: handwritten is always reviewed
    return AUTO if f.confidence >= THRESH["critical" if f.name in CRITICAL else "standard"] else REVIEW


def claim_status(routes: dict, documents_missing: bool = False) -> str:
    """The only claim-level outcomes. A missing document triggers a request, never a closure (IRDAI 2024)."""
    if documents_missing:
        return "documents_requested"
    return "prefilled_for_adjuster" if all(r == AUTO for r in routes.values()) else "needs_review"


def perturb(value: str, rng: random.Random) -> str:
    """Plausible slip: change one non-leading digit (48,500 -> 43,500)."""
    i = rng.choice([i for i, c in enumerate(value) if c.isdigit()][1:])
    return value[:i] + str((int(value[i]) + rng.randint(1, 9)) % 10) + value[i + 1:]


def build_queue(fs: dict, rng: random.Random, seed_rate: float = 0.03) -> list:
    queue = []
    for f in fs.values():
        if (r := route(f)) == REVIEW:
            queue.append(f)
        elif (r == AUTO and f.verified and f.name in SEEDABLE and rng.random() < seed_rate
              and sum(c.isdigit() for c in f.value) >= 2):  # seed only where ground truth is known
            queue.append(Field(f.name, perturb(f.value, rng), f.confidence, f.evidence,
                               seeded_true_value=f.value))   # renders exactly like a normal item
    return queue


def score(item: Field, reviewer_value: str, seconds: float) -> dict:
    out = {"field": item.name, "seconds": seconds, "seeded": item.seeded_true_value is not None}
    if out["seeded"]:
        out["caught"] = reviewer_value != item.value
        item.value = item.seeded_true_value              # a seeded error never reaches the claim record
    else:
        out["override"] = reviewer_value != item.value
    return out


def commit(fs: dict, reviewed: list) -> dict:
    """Claim record from auto-accepted fields plus reviewer decisions [(item, reviewer_value)].
    Seeded items are skipped, so no seeded value can be persisted; REJECT fields stay empty for re-keying."""
    record = {n: f.value for n, f in fs.items() if route(f) == AUTO}
    for item, value in reviewed:
        if item.seeded_true_value is None:
            record[item.name] = value
    return record
