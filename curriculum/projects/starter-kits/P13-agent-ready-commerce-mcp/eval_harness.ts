// Score a P13 system against the brief's acceptance criteria (§5), offline.
//
//   node --experimental-strip-types eval_harness.ts                     # the baseline server and shopper
//   node --experimental-strip-types eval_harness.ts --system adapter    # an LLM shopper via adapter.ts (LLM_* env vars)
//   node --experimental-strip-types eval_harness.ts --runs 5            # pass^5 instead of pass^3
//
// AC-IDs number the rows of the brief's §5 table in order (AC-1 attributes ... AC-12 cost). Labels come from
// data/labels.json and the other fixtures, never from the system. Writes results/eval_<system>.json.
// Exits 0 when thresholds fail (expected for the baseline); exits 1 only if the harness itself crashes.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { BaselineServer, classifyRequest, runShopper, TOOLS } from "./baseline.ts";
import { HERE, prng, signToken } from "./generate_data.ts";

const arg = (name: string, dflt: string) => { const i = process.argv.indexOf(name); return i > 0 ? process.argv[i + 1] : dflt; };
const system = arg("--system", "baseline"), runs = Math.max(1, Number(arg("--runs", "3")));
const data = arg("--data", join(HERE, "data"));
const read = (f: string) => readFileSync(join(data, f), "utf8");
const jsonl = (f: string) => read(f).trim().split("\n").map((l) => JSON.parse(l));
const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : NaN);
const p95 = (xs: number[]) => [...xs].sort((a, b) => a - b)[Math.max(0, Math.ceil(0.95 * xs.length) - 1)] ?? NaN;
const HIDDEN = /[\u200b-\u200d\u2060\ufeff]|<!--|style\s*=|\]\(https?:/i;   // must not survive anywhere
const LINT = /color:\s*#?f{3,6}\b|font-size:\s*[01]px|display:\s*none|[\u200b-\u200d]/i;
const OFFLINE = "not computable offline";

type Row = { ac: string; metric: string; value: string; threshold: string; result: string; note: string };
const rows: Row[] = [];
function add(ac: string, metric: string, value: number | string, threshold: string, pass: boolean | null, note = "") {
  const shown = typeof value === "number" ? (Number.isInteger(value) ? String(value) : value.toFixed(3)) : value;
  rows.push({ ac, metric, value: shown, threshold, result: pass === null ? "N/A" : pass ? "PASS" : "FAIL", note });
}

function ndcg(ranked: string[], rel: Record<string, number>, k = 10) {
  const dcg = (gs: number[]) => gs.slice(0, k).reduce((s, g, i) => s + (2 ** g - 1) / Math.log2(i + 2), 0);
  const ideal = dcg(Object.values(rel).sort((a, b) => b - a));
  return ideal ? dcg(ranked.map((s) => rel[s] ?? 0)) / ideal : 0;
}

/** Injected seller text reached the tool output if hidden characters, HTML or links survive anywhere, or if its
 *  marker appears outside a block labelled {untrusted: true}. */
function reached(output: unknown, marker: string): boolean {
  if (HIDDEN.test(JSON.stringify(output))) return true;
  const outside = JSON.stringify(output, (_k, v) => (v && typeof v === "object" && v.untrusted === true ? undefined : v));
  return outside.replace(/[\u200b-\u200d\u2060\ufeff]/g, "").toLowerCase().includes(marker.toLowerCase());
}

async function main() {
  if (!existsSync(join(data, "labels.json"))) throw new Error("No data: run node --experimental-strip-types generate_data.ts first.");
  if (system === "adapter" && !(process.env.LLM_BASE_URL && process.env.LLM_MODEL))
    throw new Error("--system adapter needs the LLM_BASE_URL and LLM_MODEL environment variables");
  const labels = JSON.parse(read("labels.json")), mock = JSON.parse(read("mock_authz.json"));
  const sor = new Map<string, any>(JSON.parse(read("catalogue.json")).map((p: any) => [p.sku, p]));
  const shopper = system === "adapter" ? (await import("./adapter.ts")).runShopperLLM : runShopper;
  const token = (sub: string, mandate: any = null) => signToken({ iss: mock.issuer, aud: mock.audience, sub,
    scope: "cart:write orders:read", exp: Math.floor(Date.now() / 1000) + 3600, ...(mandate ? { mandate } : {}) }, mock.hs256_test_key);
  const mandate = (id: string, m: any) =>
    ({ id, maxCartMinor: m.maxCartMinor, currency: m.currency, expiresAt: Date.now() + m.expires_in_s * 1000 });
  const server = new BaselineServer(data), lat: Record<string, number[]> = {};
  const call = async (s: BaselineServer, name: string, args: any, bearer?: string) => {
    const t0 = performance.now(), r = await s.call(name, args, bearer);
    (lat[name] ??= []).push(performance.now() - t0);
    return r;
  };

  // AC-1 and AC-3: attribute completeness and the fact diff, over every SKU in the system of record
  const need = (p: any) => ["fabric", "origin", "colours", "occasion", ...(p.type === "saree" ? ["length_m"] : [])];
  const facts = (x: any) => JSON.stringify([x?.price, x?.stock, x?.blouse]);
  let complete = 0, inStock = 0, factBad = 0;
  for (const [sku, truth] of sor) {
    const p = (await call(server, "get_product", { sku })).structuredContent as any;
    const length = p?.attributes?.length_m;  // missing is AC-1's problem; a wrong length is a wrong fact
    factBad += Number(facts(p) !== facts(truth) || (length != null && length !== labels.true_attributes[sku].length_m));
    if (truth.stock > 0) {
      inStock++;
      const attrs = need(truth).every((k) => p.attributes?.[k] != null);
      complete += Number(attrs && p.return_policy != null && (truth.type !== "saree" || p.blouse != null));
    }
  }
  add("AC-1", "In-stock SKUs with complete agent-facing attributes", complete / inStock, ">= 0.95", complete / inStock >= 0.95,
    `${inStock} in stock`);
  add("AC-1", "Agent-channel orders attributed end to end", OFFLINE, "1.00", null, "needs production order tagging");

  // AC-2: nDCG@10 by language
  const nd: Record<string, number[]> = { en: [], hinglish: [] };
  for (const q of jsonl("queries.jsonl")) {
    const res = (await call(server, "search_catalog", { query: q.query })).structuredContent.results as any[];
    nd[q.lang].push(ndcg(res.map((x) => x.sku), q.rel));
  }
  const [en, hi, all] = [mean(nd.en), mean(nd.hinglish), mean([...nd.en, ...nd.hinglish])];
  add("AC-2", "nDCG@10, all labelled queries", all, ">= 0.75", all >= 0.75, `${nd.en.length + nd.hinglish.length} queries`);
  add("AC-2", "nDCG@10 gap, English minus Hinglish", en - hi, "<= 0.05", en - hi <= 0.05, `EN ${en.toFixed(3)}, Hinglish ${hi.toFixed(3)}`);
  add("AC-3", "Tool price, stock, blouse and length facts match the record", 1 - factBad / sor.size, "1.00", factBad === 0,
    `${factBad} SKUs differ`);

  // AC-4: size guidance against the 200 rule-derived cases
  const sizes = jsonl("size_cases.jsonl");
  let sizeOk = 0;
  for (const c of sizes) {
    const got = (await call(server, "size_guidance", { sku: c.sku, bust_in: c.bust_in })).structuredContent;
    sizeOk += Number(JSON.stringify(got) === JSON.stringify(c.expected));
  }
  add("AC-4", "size_guidance outcome correct", sizeOk / sizes.length, "1.00", sizeOk === sizes.length, `${sizes.length} cases`);

  // AC-5: synthetic shoppers, pass^k. A fresh server per run; success is judged from the store, not the shopper.
  const tasks = jsonl("shopper_tasks.jsonl"), passed = new Map<string, number>();
  for (let k = 0; k < runs; k++) {
    const s = new BaselineServer(data);
    for (const t of tasks) {
      const user = `shopper-${t.task_id}`;
      await shopper(s, t, token(user, mandate(`md-${t.task_id}`, t.mandate)));
      const lines = [...s.store.carts.values()].filter((c) => c.userId === user).flatMap((c) => c.lines);
      const good = t.success_check.kind === "no_purchase" ? lines.length === 0
        : lines.length === 1 && lines[0].qty === 1 && t.success_check.acceptable_skus.includes(lines[0].sku);
      passed.set(t.task_id, (passed.get(t.task_id) ?? 0) + Number(good));
    }
  }
  const passK = (ts: any[]) => mean(ts.map((t) => Number(passed.get(t.task_id) === runs)));
  const heldOut = passK(tasks.filter((t) => t.held_out)), hinglish = passK(tasks.filter((t) => t.lang === "hinglish"));
  add("AC-5", `Shopper tasks pass^${runs} (${system} shopper)`, passK(tasks), ">= 0.85", passK(tasks) >= 0.85,
    `held-out ${heldOut.toFixed(2)}, Hinglish ${hinglish.toFixed(2)}`);

  // AC-6: chaos replay. Bursts of concurrent identical calls, a late retry after each, and replayed checkouts.
  const rnd = prng(606), skus = [...sor.values()].filter((p) => p.stock > 0).map((p) => p.sku);
  const chaos = new BaselineServer(data);
  const bearer = token("chaos-user", { id: "md-chaos", maxCartMinor: 1e15, currency: "INR", expiresAt: Date.now() + 3.6e6 });
  const newCart = async () => String((await chaos.call("create_cart", {}, bearer)).structuredContent.cartId);
  const addOk = new Set<string>(), checkoutOk = new Set<string>();
  let calls = 0, cartId = await newCart();
  for (let i = 0; calls < 10000; i++) {
    const a = { cartId, sku: rnd.pick(skus), quantity: 1, idempotencyKey: `chaos-key-${i}-xxxxxx` }, burst = rnd.int(1, 4);
    await Promise.all(Array.from({ length: burst }, () => chaos.call("add_to_cart", a, bearer)));
    if (!(await chaos.call("add_to_cart", a, bearer)).isError) addOk.add(a.idempotencyKey);  // the late retry
    calls += burst + 1;
    if (i % 50 === 49) {
      const c = { cartId, idempotencyKey: `chaos-checkout-${i}-xx` };
      await Promise.all([chaos.call("checkout", c, bearer), chaos.call("checkout", c, bearer)]);
      if (!(await chaos.call("checkout", c, bearer)).isError) checkoutOk.add(c.idempotencyKey);
      calls += 3;
      cartId = await newCart();
    }
  }
  const units = [...chaos.store.carts.values(), ...chaos.store.orders].flatMap((c) => c.lines).reduce((s, l) => s + l.qty, 0);
  const dupes = units - addOk.size + (chaos.store.orders.length - checkoutOk.size);
  add("AC-6", "Duplicate cart lines or orders under retries and replays", dupes, "0", dupes === 0, `${calls} calls`);

  // AC-7: auth conformance
  const auth = jsonl("auth_cases.jsonl");
  let right = 0, badRejected = 0, bad = 0;
  for (const c of auth) {
    const accepted = !(await server.call("create_cart", {}, c.token)).isError;
    right += Number(accepted === (c.expect === "accept"));
    if (c.expect === "reject") { bad++; badRejected += Number(!accepted); }
  }
  add("AC-7", "Wrong-audience, expired, passed-through tokens rejected", badRejected / bad, "1.00", badRejected === bad,
    `${right}/${auth.length} cases right; kinds: ${[...new Set(auth.map((c) => c.kind))].join(", ")}`);

  // AC-8: mandate-abuse suite. Each attempt is a fresh user; overrun = orders placed above the mandate.
  let overruns = 0, cb5 = "", cb5ok = false;
  const attacks = jsonl("mandate_attacks.jsonl");
  for (const at of attacks) {
    const user = `attacker-${at.attack_id}`, m = mandate(`md-${at.attack_id}`, at.mandate), b = token(user, m);
    const carts: string[] = [];
    const cart = async (i: number) => (carts[i] ??= String((await server.call("create_cart", {}, b)).structuredContent.cartId));
    const step = async (st: any, j: string): Promise<unknown> => {
      if (st.op === "parallel") return Promise.all(st.steps.map((x: any, n: number) => step(x, `${j}p${n}`)));
      const cartId = await cart(st.cart);
      if (st.op === "add") return call(server, "add_to_cart", { cartId, idempotencyKey: `${at.attack_id}-step-${j}-k`, ...st.args }, b);
      return server.call("checkout", { cartId, idempotencyKey: `${at.attack_id}-checkout-${j}-k` }, b);
    };
    for (const [j, st] of at.steps.entries()) {
      for (const s of st.op === "parallel" ? st.steps : [st]) await cart(s.cart);  // create carts in a fixed order
      await step(st, String(j));
    }
    const spent = server.store.orders.filter((o) => o.userId === user).reduce((s, o) => s + o.totalMinor, 0);
    overruns += Number(spent > m.maxCartMinor);
    if (at.kind === "cb5_split_bridal_set") [cb5, cb5ok] = [`${spent / 100} of ${m.maxCartMinor / 100} INR`, spent <= m.maxCartMinor];
  }
  add("AC-8", "Purchases above mandate", `${overruns}/${attacks.length}`, "0", overruns === 0);

  // AC-9: poisoning reach-through for every injected SKU, via get_product and search_catalog
  let reach = 0, cb1 = false;
  const byKind: Record<string, number> = {};
  for (const [sku, inj] of Object.entries(labels.injected) as [string, any][]) {
    const outs = [(await call(server, "get_product", { sku })).structuredContent,
      (await call(server, "search_catalog", { query: sor.get(sku).title })).structuredContent];
    const hit = outs.some((o) => reached(o, inj.marker));
    reach += Number(hit);
    byKind[inj.kind] = (byKind[inj.kind] ?? 0) + Number(hit);
    if (sku === labels.cb1_sku) cb1 = hit;
  }
  const nInjected = Object.keys(labels.injected).length;
  add("AC-9", "Injected seller text reaching tools unsanitised or unlabelled", `${reach}/${nInjected}`, "0", reach === 0,
    Object.entries(byKind).map(([k, v]) => `${k}=${v}`).join(" "));
  add("AC-10", "Human p95 latency under a 20x bot surge", OFFLINE, "<= 1.2x", null, "needs the k6 swarm");
  const [ps, pg, pa] = ["search_catalog", "get_product", "add_to_cart"].map((n) => p95(lat[n] ?? []));
  add("AC-11", "p95 ms search / get_product / add_to_cart (this machine)", `${ps.toFixed(1)} / ${pg.toFixed(1)} / ${pa.toFixed(1)}`,
    "<= 400 / 200 / 300", ps <= 400 && pg <= 200 && pa <= 300, "in-process; meaningful behind real I/O");
  add("AC-12", "Cost per 1,000 tool calls", OFFLINE, "<= USD 0.50", null, "needs the cost dashboard");

  // Curveballs and §9 minimal disclosure
  add("CB1", "Hindi white-on-white 'add two to the cart' reaches tools", cb1 ? "yes" : "no", "no", !cb1);
  const snippet = read("cb2_marketing_request.html"), descs = TOOLS.map((t) => t.description).join(" ");
  const dirty = LINT.test(descs) || /\b(always|best|only|most trusted)\b/i.test(descs);  // snapshot-diff these in CI too
  add("CB2", "CI lint blocks marketing's hidden text; tool text clean", `${LINT.test(snippet) ? "blocked" : "missed"}; ` +
    `${dirty ? "dirty" : "clean"}`, "blocked; clean", LINT.test(snippet) && !dirty);
  const spoofed = jsonl("traffic.jsonl").filter((t) => t.truth_class === "spoofed_agent");
  const trusted = spoofed.filter((t) => classifyRequest(t) === "verified_assistant").length;
  add("CB3", "Spoofed agents classified as verified assistants", `${trusted}/${spoofed.length}`, "0", trusted === 0,
    "verify Web Bot Auth signatures, not user agents");
  let legacyOk = 0;
  for (const c of jsonl("legacy_calls.jsonl")) legacyOk += Number(!(await server.call("add_to_cart", c.args, token("legacy"))).isError);
  add("CB4", "Tutorial-era calls (Mcp-Session-Id, no cartId) accepted", legacyOk, "0", legacyOk === 0);
  add("CB5", "Bridal set split across two carts: amount ordered", cb5, "<= 25000 of 25000", cb5ok);
  const orders = jsonl("orders.jsonl").slice(0, 200);
  let leaks = 0;
  for (const o of orders) {
    const out = await server.call("get_order_status", { orderId: o.order_id }, token(o.user_id));
    const text = JSON.stringify(out.structuredContent);
    leaks += Number(text.includes(o.address.line1) || text.includes(o.address.postcode));
  }
  add("§9", "get_order_status exposing street address or postcode", `${leaks}/${orders.length}`, "0", leaks === 0,
    "minimal disclosure: city only");

  console.log(`\nP13 eval · system=${system} · ${sor.size} SKUs, ${tasks.length} shopper tasks x ${runs} runs\n`);
  console.log(`${"AC-ID".padEnd(6)} | ${"metric".padEnd(62)} | ${"value".padStart(22)} | ${"threshold".padStart(18)} | result`);
  console.log("-".repeat(126));
  for (const r of rows) {
    const cells = [r.ac.padEnd(6), r.metric.slice(0, 62).padEnd(62), r.value.slice(0, 22).padStart(22), r.threshold.padStart(18)];
    console.log(`${cells.join(" | ")} | ${r.result}${r.note ? `  (${r.note})` : ""}`);
  }
  const count = (s: string) => rows.filter((r) => r.result === s).length;
  console.log(`\n${count("PASS")} PASS, ${count("FAIL")} FAIL, ${count("N/A")} N/A. Failing is expected for the baseline.`);
  mkdirSync(join(HERE, "results"), { recursive: true });
  const file = join(HERE, "results", `eval_${system}.json`);
  writeFileSync(file, JSON.stringify({ system, runs, results: rows }, null, 1));
  console.log(`wrote ${file}`);
}

main().catch((e) => { console.error(e.message ?? e); process.exitCode = 1; });
