// A deliberately simple, non-LLM baseline for P13: the MCP tool handlers, an in-memory store, token checks,
// a user-agent bot classifier and a rule-based synthetic shopper. No transport: register the handlers with the
// official MCP TypeScript SDK v2 when you build the real server.
//
//   const server = new BaselineServer("data");
//   await server.call("search_catalog", { query: "laal banarasi sari" });
//   await server.call("add_to_cart", { cartId, sku, quantity: 1, idempotencyKey }, bearerToken);
//
// add_to_cart and checkout go through add_to_cart.ts (the brief's §7 control); keep it when you replace this.
// Weaknesses on purpose (each marked GAP): tools serve the stale product feed instead of the system of record;
// seller HTML is only tag-stripped and returned unlabelled; search is keyword overlap with no transliteration;
// size_guidance assumes inches and ignores blouse stitching; tokens are checked for signature and expiry but not
// audience or issuer; bots are classified by user-agent string; get_order_status returns the whole order.
import { createHmac, randomUUID, timingSafeEqual } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { addToCart, checkout, fail, type Ctx, type Mandate, type Stored, type ToolResult } from "./add_to_cart.ts";
import { COLOURS, TYPES } from "./generate_data.ts";

type Line = { sku: string; qty: number; unitMinor: number; mandateId: string };
const S = { type: "string" };
const schema = (properties: Record<string, unknown>, required: string[] = []) =>
  ({ type: "object", additionalProperties: false, properties, required });
const READ = { readOnlyHint: true }, WRITE = { readOnlyHint: false, destructiveHint: false, idempotentHint: true };
export const TOOLS = [  // our own short, literal descriptions: no seller text, no "always choose us" (brief §9)
  { name: "search_catalog", annotations: READ,
    description: "Search Neyyarasi's sarees, lehengas, blouses, kurtas and dupattas. Returns up to 10 products.",
    inputSchema: schema({ query: S, limit: { type: "integer", minimum: 1, maximum: 10 } }, ["query"]) },
  { name: "get_product", annotations: READ,
    description: "Get one product's attributes, prices in minor units, stock and blouse details by SKU.",
    inputSchema: schema({ sku: S }, ["sku"]) },
  { name: "size_guidance", annotations: READ,
    description: "Recommend a size from the shopper's bust measurement in inches, using the seller's size chart.",
    inputSchema: schema({ sku: S, bust_in: { type: "number" } }, ["sku", "bust_in"]) },
  { name: "create_cart", annotations: { readOnlyHint: false, destructiveHint: false },
    description: "Create an empty cart and return its cartId. Requires sign-in.", inputSchema: schema({}) },
  { name: "add_to_cart", annotations: WRITE,
    description: "Add a SKU to a cart within the shopper's approved spending limit. The store sets the price. " +
      "If the limit would be exceeded, stop and ask the shopper.",
    inputSchema: schema({ cartId: S, sku: S, quantity: { type: "integer", minimum: 1, maximum: 5 }, idempotencyKey: S },
      ["cartId", "sku", "quantity", "idempotencyKey"]) },
  { name: "checkout", annotations: WRITE,
    description: "Re-check the spending limit and hand the cart to Neyyarasi's checkout. Returns a link for the shopper to pay.",
    inputSchema: schema({ cartId: S, idempotencyKey: S }, ["cartId", "idempotencyKey"]) },
  { name: "get_order_status", annotations: READ,
    description: "Get the status of one of the signed-in shopper's orders.", inputSchema: schema({ orderId: S }, ["orderId"]) }];

export const ok = (v: Record<string, unknown>): ToolResult =>
  ({ content: [{ type: "text", text: JSON.stringify(v) }], structuredContent: v });
const words = (s: string) => s.toLowerCase().normalize("NFKC").match(/[\p{L}\p{N}]+/gu) ?? [];
const sum = (ls: Line[]) => ls.reduce((s, l) => s + l.qty * l.unitMinor, 0);

export class MemoryStore {  // the in-memory stand-in for Postgres; every method body is synchronous, so each is atomic
  carts = new Map<string, { userId: string; lines: Line[] }>();
  orders: { orderId: string; userId: string; mandateId: string; totalMinor: number; lines: Line[] }[] = [];
  idem = new Map<string, Stored>();
  price: (sku: string, currency: string) => number | null;
  constructor(price: (sku: string, currency: string) => number | null) { this.price = price; }

  createCart(userId: string): string {
    const id = `cart_${randomUUID().replace(/-/g, "").slice(0, 16)}`;
    this.carts.set(id, { userId, lines: [] });
    return id;
  }

  ctx(userId: string, scopes: string[], mandate: Mandate | null, receiptKey: string): Ctx {
    const own = (cartId: string, u: string) => { const c = this.carts.get(cartId); return c && c.userId === u ? c : null; };
    const placed = (mid: string, u: string) =>
      this.orders.filter((o) => o.mandateId === mid && o.userId === u).reduce((s, o) => s + o.totalMinor, 0);
    const inCarts = (mid: string, u: string) => [...this.carts.values()].filter((c) => c.userId === u)
      .reduce((s, c) => s + sum(c.lines.filter((l) => l.mandateId === mid)), 0);
    return {
      userId, scopes, mandate, receiptKey,
      priceOf: async (sku, cur) => this.price(sku, cur),
      cartTotal: async (cartId, u) => { const c = own(cartId, u); return c ? sum(c.lines) : null; },
      mandateCommitted: async (mid, u) => inCarts(mid, u) + placed(mid, u),
      addLine: async (cartId, sku, qty, unitMinor, mandateId) => {
        const c = this.carts.get(cartId)!;
        c.lines.push({ sku, qty, unitMinor, mandateId });
        return sum(c.lines);
      },
      placeOrder: async (cartId, u, mid, max) => {  // the "same DB transaction": re-check, write, close the cart
        const c = own(cartId, u);
        if (!c) return { error: "NOT_FOUND" };
        if (!c.lines.length) return { error: "EMPTY" };
        if (c.lines.some((l) => l.mandateId !== mid)) return { error: "OTHER_MANDATE" };
        if (placed(mid, u) + sum(c.lines) > max) return { error: "LIMIT" };
        const orderId = `ORD-A-${this.orders.length + 1}`;
        this.orders.push({ orderId, userId: u, mandateId: mid, totalMinor: sum(c.lines), lines: c.lines });
        this.carts.delete(cartId);
        return { orderId, totalMinor: sum(c.lines) };
      },
      idem: {
        claim: async (k, hash) => {  // insert-if-absent with no await in between: atomic
          const prior = this.idem.get(k);
          if (!prior) this.idem.set(k, { hash, result: null });
          return prior ?? null;
        },
        finish: async (k, res) => { this.idem.get(k)!.result = res; },
        release: async (k) => { this.idem.delete(k); } } };
  }
}

export type Claims = { iss: string; aud: string; sub: string; scope: string; exp: number; mandate?: Mandate };
export function validateToken(token: string | undefined, key: string, now = Date.now()): Claims | null {
  const [head, body, sig] = (token ?? "").split(".");
  if (!head || !body || !sig) return null;
  const want = Buffer.from(createHmac("sha256", key).update(`${head}.${body}`).digest("base64url"));
  if (want.length !== Buffer.from(sig).length || !timingSafeEqual(want, Buffer.from(sig))) return null;
  const claims = JSON.parse(Buffer.from(body, "base64url").toString()) as Claims;
  return typeof claims.exp === "number" && claims.exp * 1000 > now ? claims : null;  // GAP: no aud or iss check
}

export function classifyRequest(req: { ua: string; signature_verified: boolean }): string {
  if (/ChatGPT-User|Claude-User|Perplexity-User/.test(req.ua)) return "verified_assistant";  // GAP: trusts the UA string
  if (/GPTBot|ClaudeBot|CCBot/.test(req.ua)) return "declared_crawler";
  return /Mozilla/.test(req.ua) && !/Headless/.test(req.ua) ? "human" : "unverified_automation";
}

export class BaselineServer {
  sor: Map<string, any>; feed: Map<string, any>; charts: Map<string, any>; orders: Map<string, any>;
  mock: any; store: MemoryStore; index: [string, Set<string>][]; df = new Map<string, number>();

  constructor(dataDir: string) {
    const text = (f: string) => readFileSync(join(dataDir, f), "utf8");
    const byKey = (rows: any[], key: string) => new Map<string, any>(rows.map((x) => [x[key], x]));
    this.sor = byKey(JSON.parse(text("catalogue.json")), "sku");
    this.feed = byKey(JSON.parse(text("feed.json")), "sku");  // GAP: the stale feed, not the system of record
    this.charts = byKey(JSON.parse(text("size_charts.json")), "chart_id");
    this.orders = byKey(text("orders.jsonl").trim().split("\n").map((l) => JSON.parse(l)), "order_id");
    this.mock = JSON.parse(text("mock_authz.json"));
    this.store = new MemoryStore((sku, cur) => {  // the cart service does read the system of record
      const p = this.sor.get(sku);
      return p && p.stock > 0 && Number.isInteger(p.price[cur]) ? p.price[cur] : null;
    });
    this.index = [...this.feed.values()].map((p) => [p.sku, new Set(words(`${p.title} ${this.clean(p.description_html)}`))]);
    for (const [, ws] of this.index) for (const w of ws) this.df.set(w, (this.df.get(w) ?? 0) + 1);
  }

  clean(html: string): string {  // GAP: tag-stripping only; the text of hidden spans, zero-width characters and links remain
    return html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  }

  search(query: string, limit = 10) {  // GAP: IDF-weighted keyword overlap, no transliteration or synonyms
    const q = [...new Set(words(query))], n = this.index.length;
    const scored = this.index.map(([sku, ws]) => ({ sku, score: q.reduce((s, w) => s + (ws.has(w) ? Math.log(n / this.df.get(w)!) : 0), 0) }));
    return scored.filter((x) => x.score > 0).sort((a, b) => b.score - a.score || (a.sku < b.sku ? -1 : 1)).slice(0, limit)
      .map(({ sku }) => { const p = this.feed.get(sku); return { sku, title: p.title, price: p.price, stock: p.stock }; });
  }

  product(sku: string) {
    const p = this.feed.get(sku);
    return p && { sku, type: p.type, title: p.title, attributes: p.attributes, blouse: p.blouse, price: p.price,
      stock: p.stock, size_chart_ref: p.size_chart_ref, return_policy: p.return_policy,
      description: this.clean(p.description_html) };  // GAP: seller text, unlabelled
  }

  sizeGuidance(sku: string, bustIn: number) {  // GAP: assumes inches; ignores blouse stitching and missing rows
    const chart = this.charts.get(this.feed.get(sku)?.size_chart_ref);
    const row = chart?.rows.find((r: any) => (r.bust ?? 0) >= bustIn);
    return row ? { outcome: "size", size: row.size } : { outcome: "no_size_data" };
  }

  async call(name: string, args: any, bearer?: string): Promise<ToolResult> {
    if (name === "search_catalog") return ok({ results: this.search(String(args?.query ?? ""), Math.min(10, args?.limit ?? 10)) });
    if (name === "get_product") { const p = this.product(args?.sku); return p ? ok(p) : fail("NOT_FOUND", "unknown SKU"); }
    if (name === "size_guidance") return ok(this.sizeGuidance(args?.sku, Number(args?.bust_in)));
    const claims = validateToken(bearer, this.mock.hs256_test_key);
    if (!claims) return fail("UNAUTHORIZED", "a valid access token for this server is required");
    const ctx = this.store.ctx(claims.sub, claims.scope.split(" "), claims.mandate ?? null, this.mock.receipt_test_key);
    if (name === "create_cart") return ok({ cartId: this.store.createCart(claims.sub) });
    if (name === "add_to_cart") return addToCart(args, ctx);
    if (name === "checkout") return checkout(args, ctx);
    if (name === "get_order_status") {
      const o = this.orders.get(args?.orderId);
      return o && o.user_id === claims.sub ? ok(o) : fail("NOT_FOUND", "no such order for this user");  // GAP: whole order
    }
    return fail("UNKNOWN_TOOL", name);
  }
}

/** Rule-based synthetic shopper (stands in for mock-assistant): English keywords only, first acceptable hit wins. */
export async function runShopper(server: BaselineServer, task: any, bearer: string): Promise<void> {
  const goal = task.goal.toLowerCase();
  const cap = Number((goal.match(/₹\s?([\d,]+)/)?.[1] ?? "0").replace(/,/g, "")) * 100;
  const colour = Object.keys(COLOURS).find((c) => goal.includes(c)), type = TYPES.find((t) => goal.includes(t));
  const hits = (await server.call("search_catalog", { query: task.goal })).structuredContent.results as any[];
  const cartId = (await server.call("create_cart", {}, bearer)).structuredContent.cartId;
  for (const hit of hits) {
    const p = (await server.call("get_product", { sku: hit.sku })).structuredContent as any;
    const wrongColour = colour && !p.attributes.colours?.includes(colour);
    if (p.stock <= 0 || p.price.INR > cap || (type && p.type !== type) || wrongColour) continue;
    const key = `${task.task_id}-${p.sku}-k`;
    const r = await server.call("add_to_cart", { cartId, sku: p.sku, quantity: 1, idempotencyKey: key }, bearer);
    if (!r.isError || r.structuredContent.error === "MANDATE_LIMIT_EXCEEDED") return;  // done, or go back to the human
  }
}
