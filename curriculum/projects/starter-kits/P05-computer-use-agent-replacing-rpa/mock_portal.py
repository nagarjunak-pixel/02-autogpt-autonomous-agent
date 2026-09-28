"""An in-process stand-in for the Tollvane portal (brief §3), so the kit runs with no browser, server or network.

The executor sees an observation dict (URL, visible accessible names, review values, untrusted page text, pop-up
buttons, HTTP status) and returns Actions. Variants:
- v1 baseline;
- v2 redesign: renamed labels, goods fields behind a "Goods" tab, a cookie banner;
- v3: lazy dropdowns (open Currency/Incoterm before typing), goods lines in a frame, a confirmation modal;
- v4: v1, v2 or v3 at random per run (A/B);
- v5: curveball 1's overnight redesign: new routes and labels that are not on the approved screen map.
5% of page loads return 502 (on a submit, half of those after the declaration was lodged) and 3% stall for 20 s.
"""
from action_gate import PORTAL

BASE = {"hs_code": "HS code", "goods_desc": "Goods description", "gross_kg": "Gross mass (kg)",
        "net_kg": "Net mass (kg)", "invoice_value": "Invoice value", "currency": "Currency", "incoterm": "Incoterm",
        "consignor_name": "Consignor name", "consignor_id": "Consignor EORI/IEC", "consignee_name": "Consignee name",
        "consignee_id": "Consignee EORI/IEC", "container_no": "Container number", "customer_ref": "Customer reference"}
V2 = {"hs_code": "Commodity code", "gross_kg": "Gross weight (kg)", "net_kg": "Net weight (kg)",
      "invoice_value": "Declared value", "consignor_name": "Exporter name", "consignor_id": "Exporter EORI/IEC",
      "consignee_name": "Importer name", "consignee_id": "Importer EORI/IEC"}
V5 = {"hs_code": "Tariff number", "invoice_value": "Customs value", "consignee_name": "Receiver",
      "gross_kg": "Weight, gross (kg)"}
GOODS = ("hs_code", "goods_desc", "gross_kg", "net_kg")
DEFAULTS = dict(banner=None, tab=None, confirm=None, lazy=(), route="declarations", review="review")
VARIANTS = {
    "v1": dict(labels=BASE, next="Next", submit="Submit declaration"),
    "v2": dict(labels={**BASE, **V2}, next="Continue", submit="Lodge declaration", banner="Accept all cookies",
               tab="Goods"),
    "v3": dict(labels=BASE, next="Next", submit="Submit declaration", confirm="Confirm and transmit",
               tab="Goods lines", lazy=("currency", "incoterm")),
    "v5": dict(labels={**BASE, **V5}, next="Next", submit="Submit filing", route="filings", review="finalise"),
}


class Registry:
    """The broker's side: every lodged declaration. It survives worker crashes, like the real portal."""

    def __init__(self):
        self.lodged = []

    def lodge(self, record, values):
        ref = f"26NL{len(self.lodged) + 1:06d}DH{sum(map(ord, record['customer_ref'])) % 97:02d}"
        self.lodged.append({"ref": ref, "customer_ref": record["customer_ref"], "record_id": record["record_id"],
                            "shipment_id": record["shipment_id"], "decl_type": record["decl_type"], "values": values})
        return ref

    def search(self, customer_ref):
        return next((d["ref"] for d in self.lodged if d["customer_ref"] == customer_ref), None)

    def get(self, ref):
        return next(d for d in self.lodged if d["ref"] == ref)


class Portal:
    def __init__(self, variant, registry, record, rng, faults=True, stepup=False, popup=None, lure="",
                 force_502_after_lodge=False):
        self.variant = rng.choice(["v1", "v2", "v3"]) if variant == "v4" else variant
        self.v = {**DEFAULTS, **VARIANTS[self.variant]}
        self.registry, self.record, self.rng, self.faults, self.stepup = registry, record, rng, faults, stepup
        self.popup, self.force_502 = list(popup or []), force_502_after_lodge
        self.text = f"Shipment remarks (from customer, untrusted): {record['remarks']}" + (f" {lure}" if lure else "")
        self.field_of = {label: f for f, label in self.v["labels"].items()}
        self.values, self.opened, self.tab_open, self.banner = {}, set(), False, self.v["banner"]
        self.screen, self.did, self.ref, self.elapsed = "form", f"D{rng.randrange(10 ** 6):06d}", None, 0.0

    def url(self):
        path = {"form": "new", "review": f"{self.did}/{self.v['review']}", "confirm": f"{self.did}/confirm",
                "done": f"{self.did}/done"}[self.screen]
        return f"https://{PORTAL}/#/{self.v['route']}/{path}"

    def labels(self):
        if self.screen == "form":
            names = [lab for f, lab in self.v["labels"].items() if f not in GOODS or not self.v["tab"] or self.tab_open]
            return (names + [x for x in (self.v["tab"], self.banner) if x] + [self.v["next"]] + self.popup)
        if self.screen == "review":
            return ["One-time code", "Verify", "Back"] if self.stepup else [self.v["submit"], "Back"]
        return [self.v["confirm"], "Cancel"] if self.screen == "confirm" else []

    def observe(self, status=200):
        shown = self.screen in ("review", "confirm")
        return {"url": self.url(), "labels": self.labels(), "values": dict(self.values) if shown else {},
                "text": self.text if self.screen != "done" else "", "popup": list(self.popup), "status": status,
                "ref": self.ref if self.screen == "done" else None, "elapsed": self.elapsed}

    def act(self, a):
        self.elapsed += 0.5 if a.type == "type" else 1.0
        if a.type not in ("click", "type"):
            return self.observe()
        if a.target not in self.labels():
            return self.observe(404)  # no such element on this screen
        blocker = self.popup or ([self.banner] if self.banner else [])
        if blocker and a.target not in blocker:
            return self.observe(409)  # obscured by a pop-up or the cookie banner
        field = self.field_of.get(a.target)
        if a.type == "type":
            if field in self.v["lazy"] and field not in self.opened:
                return self.observe()  # lazy dropdown not loaded yet: the input is silently lost
            self.values[a.target] = a.text
        elif a.target in self.popup:
            self.popup = []
        elif a.target == self.banner:
            self.banner = None
        elif a.target == self.v["tab"]:
            self.tab_open = True
        elif field in self.v["lazy"]:
            self.opened.add(field)
        elif a.target in ("Back", "Cancel"):
            self.screen = "form"
        elif a.target == self.v["next"]:
            return self._load("review")
        elif a.target == self.v["submit"] and self.screen == "review":
            return self._load("confirm" if self.v["confirm"] else "done", lodge=not self.v["confirm"])
        elif a.target == self.v["confirm"]:
            return self._load("done", lodge=True)
        return self.observe()

    def _load(self, screen, lodge=False):
        self.elapsed += 2.0
        forced = lodge and self.force_502
        self.force_502 = self.force_502 and not forced
        r = 0.0 if forced else (self.rng.random() if self.faults else 1.0)
        if r < 0.05:  # HTTP 502; on a submit, half of them after the declaration was lodged (curveball 5)
            if lodge and (forced or self.rng.random() < 0.5):
                self._lodge()
            return self.observe(502)
        status = "stall" if r < 0.08 else 200
        self.elapsed += 20.0 if status == "stall" else 0.0
        if lodge:
            self._lodge()
        self.screen = screen
        return self.observe(status)

    def _lodge(self):
        values = {self.field_of[label]: v for label, v in self.values.items()}
        self.ref = self.registry.lodge(self.record, values)
