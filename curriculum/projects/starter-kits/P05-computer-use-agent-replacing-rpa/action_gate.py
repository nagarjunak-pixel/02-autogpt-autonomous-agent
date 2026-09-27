"""P05 action gate: every executor proposes its actions through this wrapper (brief §7).

Kept from the reviewed sketch:
- the host allow-list runs first, on the parsed hostname, so lookalike domains and `user@host` tricks fail;
- commit screens match on the path or the #route and fail closed: typing and keys are refused there (Enter
  submits), and any control not on the safe list is an irreversible submit;
- an unnamed click on the portal is refused until it is resolved to an accessible name (DOM hit-test);
- a submit-like control on an unmapped screen is escalated as UI drift, so the classifier doubles as a redesign
  detector (curveball 1);
- the idempotency claim (SUBMITTING, no portal ref) is written after approval and before the click, atomically; a
  restart that finds it must reconcile, never retry (curveball 5).
Added for the kit (README, "What the control adds"):
- the §7 design note's data-flow check: a `type` action passes only into a field on the approved screen map and only
  with the planned value, so remarks-borne values never reach the portal (curveball 2) and nobody types an MFA code
  (curveball 3);
- confirmation modals (portal v3): the run holding the claim may move review -> confirm once, under the same approval;
- reconcile(): record the reference a customer-reference search found, or release the claim when the search
  authoritatively finds nothing (the next claim then needs a fresh approval);
- presubmit_diff(): the review screen against the plan. The harness's approver declines on any mismatch.
"""
import hashlib
import re
import sqlite3
import time
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


class Kind(Enum):
    READ = "read"
    WRITE = "reversible_write"
    SUBMIT = "irreversible_submit"


class Blocked(Exception):
    pass


PORTAL = "portal.broker.example"
TMS = "tms.duinhaven.internal"  # the sketch's "tms.northwind.internal", renamed to the brief's client
ALLOWED_HOSTS = {PORTAL, TMS}
COMMIT_SCREEN = re.compile(r"/declarations/[^/#?]+/(review|confirm)\b")  # screen map; path or #route
SAFE_ON_COMMIT = re.compile(r"^(back|cancel|edit|previous)$", re.I)
SUBMIT_LIKE = re.compile(r"\b(submit|lodge|transmit|send to customs|confirm)\b", re.I)
CRITICAL = ("hs_code", "invoice_value", "currency", "gross_kg", "net_kg", "consignor_id", "consignee_id")

# The approved screen map: plan field -> accessible names a human has signed off (portal v1-v4). After a redesign,
# new names are added only once a human signs off the repaired map (curveball 1); until then typing is blocked.
SCREEN_MAP = {
    "hs_code": ("HS code", "Commodity code"),
    "goods_desc": ("Goods description",),
    "gross_kg": ("Gross mass (kg)", "Gross weight (kg)"),
    "net_kg": ("Net mass (kg)", "Net weight (kg)"),
    "invoice_value": ("Invoice value", "Declared value"),
    "currency": ("Currency",),
    "incoterm": ("Incoterm",),
    "consignor_name": ("Consignor name", "Exporter name"),
    "consignor_id": ("Consignor EORI/IEC", "Exporter EORI/IEC"),
    "consignee_name": ("Consignee name", "Importer name"),
    "consignee_id": ("Consignee EORI/IEC", "Importer EORI/IEC"),
    "container_no": ("Container number",),
    "customer_ref": ("Customer reference",),
}
FIELD_OF = {name.casefold(): field for field, names in SCREEN_MAP.items() for name in names}


@dataclass(frozen=True)
class Action:
    type: str  # click | type | key | navigate | scroll | screenshot | wait (| escalate, handled by the workflow)
    url: str  # page URL (TMS screens are mapped to tms.duinhaven.internal/<screen>)
    target: str = ""  # accessible name from the DOM/UIA tree, never from OCR of page text
    text: str = ""


def classify(a: Action) -> Kind:
    if a.type in ("screenshot", "scroll", "wait", "navigate"):
        return Kind.READ
    if COMMIT_SCREEN.search(a.url):  # fail closed on commit screens
        if a.type != "click":
            raise Blocked("keys/typing on a commit screen (Enter submits): escalate")
        return Kind.WRITE if SAFE_ON_COMMIT.match(a.target) else Kind.SUBMIT
    if a.type == "click" and not a.target and urlparse(a.url).hostname == PORTAL:
        raise Blocked("unnamed portal click: resolve the element by DOM hit-test first")
    if a.type == "click" and SUBMIT_LIKE.search(a.target):  # submit-like control on an unmapped screen
        raise Blocked(f"'{a.target}' off a mapped commit screen: possible UI drift, escalate")
    return Kind.WRITE


def check_typed(a: Action, plan: dict) -> None:
    """Plan-bound values: the only text an executor may type is the planned value for a mapped field."""
    field = FIELD_OF.get(a.target.strip().casefold())
    if field is None:
        raise Blocked(f"typing into '{a.target}', which is not on the approved screen map: escalate")
    if field not in plan or plan[field] != a.text:
        raise Blocked(f"typed value for {field} is not the planned value: off-plan, blocked and logged")


def idem_key(filing: dict) -> str:  # one declaration per shipment+type; changes go via amendment
    return hashlib.sha256(f"{filing['shipment_id']}|{filing['decl_type']}".encode()).hexdigest()


def presubmit_diff(shown: dict, plan: dict) -> list:
    """Plan fields whose value on the review screen is different or missing. Empty means the diff is clean."""
    seen = {FIELD_OF.get(label.casefold()): value for label, value in shown.items()}
    return sorted(f for f, v in plan.items() if seen.get(f) != v)


class ActionGate:
    def __init__(self, db, approve):  # db: a path or an open sqlite3 connection; approve(action, filing) -> bool
        self.db = db if isinstance(db, sqlite3.Connection) else sqlite3.connect(db)
        self.approve = approve
        self.db.execute("CREATE TABLE IF NOT EXISTS idem(key TEXT PRIMARY KEY, state TEXT,"
                        " run_id TEXT, ts REAL, portal_ref TEXT, screen TEXT)")

    def state(self, filing: dict):
        row = self.db.execute("SELECT state FROM idem WHERE key=?", (idem_key(filing),)).fetchone()
        return row[0] if row else None

    def check(self, a: Action, filing: dict, run_id: str) -> Kind:
        if urlparse(a.url).hostname not in ALLOWED_HOSTS:
            raise Blocked(f"host not on allow-list: {a.url}")
        kind = classify(a)
        if a.type == "type":
            check_typed(a, filing.get("plan") or {})
        if kind is Kind.SUBMIT:
            self._claim(a, filing, run_id)
        return kind

    def _claim(self, a: Action, filing: dict, run_id: str) -> None:
        key, screen = idem_key(filing), COMMIT_SCREEN.search(a.url).group(1)
        row = self.db.execute("SELECT state, run_id, screen FROM idem WHERE key=?", (key,)).fetchone()
        if row == ("SUBMITTING", run_id, "review") and screen == "confirm":
            with self.db:  # confirmation modal: the claiming run moves review -> confirm once, same approval
                moved = self.db.execute("UPDATE idem SET screen='confirm' WHERE key=? AND run_id=? AND"
                                        " screen='review'", (key, run_id)).rowcount
            if moved == 1:
                return
        if row and row[0] != "RELEASED":  # SUBMITTING without a portal ref = crash window: reconcile, never retry
            raise Blocked(f"idempotency record exists ({row[0]} by run {row[1]}): reconcile")
        if not self.approve(a, filing):
            raise Blocked("approver declined")
        try:
            with self.db:  # PRIMARY KEY (or the RELEASED guard) makes the claim atomic across workers
                if row is None:
                    self.db.execute("INSERT INTO idem VALUES (?,?,?,?,NULL,?)",
                                    (key, "SUBMITTING", run_id, time.time(), screen))
                elif self.db.execute("UPDATE idem SET state='SUBMITTING', run_id=?, ts=?, screen=? WHERE key=?"
                                     " AND state='RELEASED'", (run_id, time.time(), screen, key)).rowcount != 1:
                    raise sqlite3.IntegrityError("claim lost")
        except sqlite3.IntegrityError:
            raise Blocked("another worker claimed this filing") from None

    def record_outcome(self, filing: dict, portal_ref: str) -> None:
        with self.db:
            self.db.execute("UPDATE idem SET state='SUBMITTED', portal_ref=? WHERE key=?",
                            (portal_ref, idem_key(filing)))

    def reconcile(self, filing: dict, portal_ref) -> None:
        """After a crash or timeout, search the portal by the customer reference stamped on every declaration.
        Found: record it. Not found (an authoritative search): release the claim; a new claim needs a new approval."""
        if portal_ref:
            return self.record_outcome(filing, portal_ref)
        with self.db:
            self.db.execute("UPDATE idem SET state='RELEASED', run_id=NULL WHERE key=? AND state='SUBMITTING'",
                            (idem_key(filing),))
