"""Tests for the §7 action gate: the reviewed sketch's behaviour, the kit's additions, and curveballs 1-5."""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from action_gate import (FIELD_OF, Action, ActionGate, Blocked, Kind, classify, idem_key,  # noqa: E402
                         presubmit_diff)
from mock_portal import BASE, V2, V5, VARIANTS  # noqa: E402

P = "https://portal.broker.example/#/declarations"
PLAN = {"hs_code": "84713000", "consignee_name": "Murugan Textiles", "currency": "EUR"}
FILING = {"shipment_id": "DH-RTM-26-000001", "decl_type": "EX", "plan": PLAN}
SUBMIT = Action("click", f"{P}/D1/review", "Submit declaration")
CONFIRM = Action("click", f"{P}/D1/confirm", "Confirm and transmit")


class Approver:
    def __init__(self, answer=True, hook=None):
        self.calls, self.answer, self.hook = 0, answer, hook

    def __call__(self, action, filing):
        self.calls += 1
        if self.hook:
            self.hook()
        return self.answer


class Classify(unittest.TestCase):
    def test_reads(self):
        for t in ("screenshot", "scroll", "wait", "navigate"):
            self.assertIs(classify(Action(t, f"{P}/D1/review")), Kind.READ)

    def test_commit_screen_by_path_and_by_hash_route(self):
        self.assertIs(classify(Action("click", "https://portal.broker.example/declarations/D1/review",
                                      "Submit declaration")), Kind.SUBMIT)
        self.assertIs(classify(SUBMIT), Kind.SUBMIT)
        self.assertIs(classify(CONFIRM), Kind.SUBMIT)

    def test_commit_screen_fails_closed(self):
        self.assertIs(classify(Action("click", f"{P}/D1/review", "Back")), Kind.WRITE)
        self.assertIs(classify(Action("click", f"{P}/D1/review", "CANCEL")), Kind.WRITE)
        for name in ("Back to list", "Cancel and submit", "Verify", ""):  # exact safe list only
            self.assertIs(classify(Action("click", f"{P}/D1/review", name)), Kind.SUBMIT)

    def test_no_keys_or_typing_on_commit_screen(self):
        with self.assertRaises(Blocked):
            classify(Action("key", f"{P}/D1/review", text="Enter"))
        with self.assertRaises(Blocked):
            classify(Action("type", f"{P}/D1/confirm", "Currency", "EUR"))

    def test_unnamed_click_blocked_on_portal_only(self):
        with self.assertRaises(Blocked):
            classify(Action("click", f"{P}/new", ""))
        self.assertIs(classify(Action("click", "https://tms.duinhaven.internal/shipments", "")), Kind.WRITE)

    def test_cb1_submit_like_control_off_the_map_is_drift(self):
        for url, name in ((f"https://portal.broker.example/#/filings/F1/finalise", "Submit filing"),
                          (f"{P}/new", "Submit all pending declarations"), (f"{P}/new", "Transmit now")):
            with self.assertRaisesRegex(Blocked, "UI drift"):
                classify(Action("click", url, name))

    def test_cb1_v5_labels_are_not_on_the_approved_map(self):
        for field, label in {**BASE, **V2}.items():
            self.assertEqual(FIELD_OF[label.casefold()], field)
        for label in V5.values():
            self.assertNotIn(label.casefold(), FIELD_OF)
        self.assertNotRegex(VARIANTS["v5"]["route"], "declarations")


class Gate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "idem.db")
        self.approve = Approver()
        self.gate = ActionGate(self.db, self.approve)

    def tearDown(self):
        self.gate.db.close()
        self.tmp.cleanup()

    def row(self):
        return sqlite3.connect(self.db).execute("SELECT state, run_id, portal_ref FROM idem").fetchone()

    def test_allow_list_rejects_lookalikes(self):
        for url in ("https://portal.broker.example.co/login", "https://portal-broker.example/",
                    "https://portal.broker.example@auth-check.example/verify", "https://portal.broker.example./",
                    "https://xn--portl-broker-8fb.example/", "javascript:alert(1)"):
            with self.assertRaisesRegex(Blocked, "allow-list"):
                self.gate.check(Action("navigate", url), FILING, "r1")
        self.assertIs(self.gate.check(Action("navigate", "https://PORTAL.broker.example/#/x"), FILING, "r1"),
                      Kind.READ)

    def test_cb2_typed_values_are_plan_bound(self):
        ok = Action("type", f"{P}/new", "Consignee name", "Murugan Textiles")
        self.assertIs(self.gate.check(ok, FILING, "r1"), Kind.WRITE)
        self.assertIs(self.gate.check(Action("type", f"{P}/new", "Importer name", "Murugan Textiles"), FILING,
                                      "r1"), Kind.WRITE)  # a v2 name on the approved map
        with self.assertRaisesRegex(Blocked, "off-plan"):
            self.gate.check(Action("type", f"{P}/new", "Consignee name", "Kestrel Trading FZE"), FILING, "r1")
        with self.assertRaisesRegex(Blocked, "screen map"):
            self.gate.check(Action("type", f"{P}/new", "Remarks", "anything"), FILING, "r1")
        with self.assertRaisesRegex(Blocked, "off-plan"):
            self.gate.check(ok, {**FILING, "plan": None}, "r1")

    def test_cb3_no_mfa_code_typed_by_the_executor(self):
        with self.assertRaises(Blocked):
            self.gate.check(Action("type", f"{P}/D1/review", "One-time code", "123456"), FILING, "r1")
        with self.assertRaises(Blocked):
            self.gate.check(Action("type", f"{P}/new", "One-time code", "123456"), FILING, "r1")

    def test_claim_written_before_the_click_after_approval(self):
        self.assertIs(self.gate.check(SUBMIT, FILING, "r1"), Kind.SUBMIT)
        self.assertEqual(self.approve.calls, 1)
        self.assertEqual(self.row(), ("SUBMITTING", "r1", None))
        self.gate.record_outcome(FILING, "26NL000001")
        self.assertEqual(self.row(), ("SUBMITTED", "r1", "26NL000001"))

    def test_declined_approval_leaves_no_claim(self):
        gate = ActionGate(self.db, Approver(answer=False))
        with self.assertRaisesRegex(Blocked, "declined"):
            gate.check(SUBMIT, FILING, "r1")
        self.assertIsNone(self.row())

    def test_cb5_retry_of_a_timed_out_submit_is_blocked_without_reusing_approval(self):
        self.gate.check(SUBMIT, FILING, "r1")
        with self.assertRaisesRegex(Blocked, "reconcile"):
            self.gate.check(SUBMIT, FILING, "r1")  # same run, same screen: the engine's retry
        self.assertEqual(self.approve.calls, 1)
        restarted = ActionGate(self.db, Approver())  # a new worker after a crash: state is in the DB, not memory
        with self.assertRaisesRegex(Blocked, "reconcile"):
            restarted.check(SUBMIT, FILING, "r2")

    def test_race_between_workers_is_atomic(self):
        other = ActionGate(self.db, Approver())
        gate = ActionGate(self.db, Approver(hook=lambda: other.check(SUBMIT, FILING, "w2")))
        with self.assertRaisesRegex(Blocked, "another worker"):
            gate.check(SUBMIT, FILING, "w1")
        self.assertEqual(self.row()[1], "w2")

    def test_confirmation_modal_continues_once_under_the_same_approval(self):
        self.gate.check(SUBMIT, FILING, "r1")
        self.assertIs(self.gate.check(CONFIRM, FILING, "r1"), Kind.SUBMIT)
        self.assertEqual(self.approve.calls, 1)
        with self.assertRaises(Blocked):
            self.gate.check(CONFIRM, FILING, "r1")  # retrying the confirm click
        gate = ActionGate(self.db, Approver())
        gate.reconcile(FILING, None)
        gate.check(SUBMIT, FILING, "r2")
        with self.assertRaises(Blocked):
            gate.check(CONFIRM, FILING, "r3")  # a different run cannot ride on r2's approval

    def test_reconcile_found_records_and_not_found_releases(self):
        self.gate.check(SUBMIT, FILING, "r1")
        self.gate.reconcile(FILING, None)
        self.assertEqual(self.row()[0], "RELEASED")
        self.assertIs(self.gate.check(SUBMIT, FILING, "r2"), Kind.SUBMIT)  # re-claim needs a fresh approval
        self.assertEqual(self.approve.calls, 2)
        self.gate.reconcile(FILING, "26NL000009")
        self.gate.reconcile(FILING, None)  # never releases a submitted filing
        self.assertEqual(self.row(), ("SUBMITTED", "r2", "26NL000009"))

    def test_edi_resend_shares_the_key_and_a_new_declaration_type_does_not(self):
        resend = {"shipment_id": FILING["shipment_id"], "decl_type": "EX", "plan": {"hs_code": "11111111"}}
        self.assertEqual(idem_key(resend), idem_key(FILING))
        self.assertNotEqual(idem_key({**FILING, "decl_type": "IM"}), idem_key(FILING))
        self.gate.check(SUBMIT, FILING, "r1")
        self.gate.record_outcome(FILING, "26NL000001")
        with self.assertRaisesRegex(Blocked, "SUBMITTED"):  # an amendment goes via the broker, never a new filing
            self.gate.check(SUBMIT, resend, "r9")

    def test_cb4_api_lodging_through_the_same_gate_is_idempotent_with_the_ui(self):
        self.gate.check(SUBMIT, FILING, "ui-run")
        api = Action("click", "https://portal.broker.example/api/v1/declarations/DH-RTM-26-000001/confirm",
                     "lodge_declaration")
        with self.assertRaisesRegex(Blocked, "idempotency"):
            self.gate.check(api, FILING, "api-run")

    def test_presubmit_diff(self):
        self.assertEqual(presubmit_diff({"HS code": "84713000", "Importer name": "Murugan Textiles",
                                         "Currency": "EUR"}, PLAN), [])
        self.assertEqual(presubmit_diff({"HS code": "84713000", "Consignee name": "Murugan Textiles"}, PLAN),
                         ["currency"])  # a lazy dropdown that lost its value


if __name__ == "__main__":
    unittest.main()
