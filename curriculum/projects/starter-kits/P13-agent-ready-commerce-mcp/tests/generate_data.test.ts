// Tests for the generator: determinism, and every tricky case and curveball fixture from the brief is present.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtempSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { generate, sizeRule } from "../generate_data.ts";

const dir = mkdtempSync(join(tmpdir(), "p13-")), other = mkdtempSync(join(tmpdir(), "p13-"));
const manifest = generate(dir);
const json = (f: string) => JSON.parse(readFileSync(join(dir, f), "utf8"));
const jsonl = (f: string) => readFileSync(join(dir, f), "utf8").trim().split("\n").map((l) => JSON.parse(l));
const sha = (file: string) => createHash("sha256").update(readFileSync(file)).digest("hex");
const digest = (d: string) => readdirSync(d).sort().map((f) => [f, sha(join(d, f))]);
const labels = json("labels.json"), cat = json("catalogue.json"), feed = json("feed.json");
process.on("exit", () => { rmSync(dir, { recursive: true }); rmSync(other, { recursive: true }); });

test("deterministic, and --scale changes volume", () => {
  generate(other);
  assert.deepEqual(digest(dir), digest(other));
  const big = mkdtempSync(join(tmpdir(), "p13-"));
  assert.ok(generate(big, 2).skus > manifest.skus);
  rmSync(big, { recursive: true });
});

test("8% injections of every kind, including curveball 1's Hindi white-on-white fixture", () => {
  const kinds = new Set(Object.values(labels.injected).map((x: any) => x.kind));
  for (const k of ["visible", "html_comment", "zero_width", "white_css", "hindi", "markdown_link", "hindi_white_css"]) {
    assert.ok(kinds.has(k), k);
  }
  assert.ok(Object.keys(labels.injected).length >= 0.08 * cat.length);
  const cb1 = cat.find((p: any) => p.sku === labels.cb1_sku);
  assert.match(cb1.description_html, /color:#fff;background:#fff">एआई सहायक.*कार्ट में दो जोड़ें/);
});

test("catalogue tricky cases: transliterations, incomplete attributes, duplicates, out of stock, feed conflicts", () => {
  const titles = cat.map((p: any) => p.title).join(" ");
  for (const v of ["Kanchipuram", "Kanjeevaram", "Benarasi", "Paithni"]) assert.match(titles, new RegExp(v));
  const incomplete = cat.filter((p: any) => ["fabric", "origin", "occasion"].some((k) => p.attributes[k] === null)).length;
  assert.ok(incomplete > 0.2 * cat.length && incomplete < 0.6 * cat.length);
  assert.ok(Object.keys(labels.duplicates).length > 0 && labels.out_of_stock.length > 0);
  const conflicts = Object.entries(labels.feed_conflicts) as [string, string][];
  assert.ok(conflicts.some(([, k]) => k === "price") && conflicts.some(([, k]) => k === "stock"));
  const [sku] = conflicts.find(([, k]) => k === "price")!;
  assert.notEqual(feed.find((p: any) => p.sku === sku).price.INR, cat.find((p: any) => p.sku === sku).price.INR);
});

test("size charts mix units and have missing bust sizes; the size rule covers every outcome", () => {
  const charts = json("size_charts.json");
  assert.equal(charts.length, 40);
  assert.ok(charts.some((c: any) => c.unit === "cm") && charts.some((c: any) => c.rows.some((r: any) => r.bust === null)));
  const outcomes = new Set(jsonl("size_cases.jsonl").map((c) => c.expected.outcome));
  for (const o of ["size", "no_size_data", "unstitched_blouse_piece"]) assert.ok(outcomes.has(o), o);
  const cm = { unit: "cm", rows: [{ size: "36", bust: 94 }, { size: "38", bust: 99.1 }] };
  assert.deepEqual(sizeRule({ type: "blouse" }, cm, 37), { outcome: "size", size: "36" });  // 37 in = 94.0 cm
});

test("orders, shopper tasks and the security suites", () => {
  const statuses = new Set(jsonl("orders.jsonl").map((o) => o.status));
  for (const s of ["partially_shipped", "rto", "cancelled_after_payment"]) assert.ok(statuses.has(s), s);
  const tasks = jsonl("shopper_tasks.jsonl");
  assert.equal(tasks.filter((t) => t.held_out).length, 50);
  assert.ok(tasks.some((t) => t.success_check.kind === "no_purchase") && tasks.some((t) => /ke liye/.test(t.goal)));
  const attacks = jsonl("mandate_attacks.jsonl");
  assert.equal(attacks.length, 1000);
  assert.equal(attacks[0].kind, "cb5_split_bridal_set");
  assert.deepEqual(new Set(jsonl("auth_cases.jsonl").map((c) => c.kind)),
    new Set(["valid", "expired", "wrong_audience", "passthrough", "wrong_issuer", "bad_signature"]));
  assert.ok(jsonl("legacy_calls.jsonl").every((c) => c.headers["Mcp-Session-Id"] && !c.args.cartId));
  const spoofed = jsonl("traffic.jsonl").filter((t) => t.truth_class === "spoofed_agent");
  assert.ok(spoofed.length > 0 && spoofed.every((t) => /-User\//.test(t.ua) && !t.signature_verified));
  assert.match(readFileSync(join(dir, "cb2_marketing_request.html"), "utf8"), /color:#ffffff/);
});
