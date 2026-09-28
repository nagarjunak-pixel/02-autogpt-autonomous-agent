// The brief's §7 control for P13: the add_to_cart tool handler, plus checkout(), which re-checks the mandate.
//
// Kept from the reviewed sketch (each point has a test in tests/add_to_cart.test.ts):
// - strict input: unknown fields such as "price", "currency" or "sessionId" are rejected, never ignored;
// - an explicit cartId handle, never a protocol session (Mcp-Session-Id is gone in MCP 2026-07-28);
// - idempotency keys are scoped to the user and bound to a hash of the request; reuse with other arguments fails;
// - price always comes from the server catalogue, in the mandate's currency, never from the agent;
// - a missing or expired mandate, a foreign cart or an over-limit cart fails closed, and MANDATE_LIMIT_EXCEEDED
//   tells the assistant to go back to the human, not to retry; receipts are HMAC-signed.
// Fixed here, where the sketch left a comment: the idempotency store claims the key atomically *before* any work
// (check-then-write lets concurrent retries through), and the limit is a per-mandate aggregate across open carts and
// orders (curveball 5), re-checked by checkout() inside the store's placeOrder transaction.
// Zod is replaced by a 15-line strict validator so the kit needs no npm install.
import { createHash, createHmac, randomUUID } from "node:crypto";

type Rule = (v: unknown) => string | null;
const str = (re: RegExp, min: number, max: number): Rule => (v) =>
  typeof v === "string" && v.length >= min && v.length <= max && re.test(v) ? null : `expected ${min}-${max} chars matching ${re}`;
const int = (min: number, max: number): Rule => (v) =>
  Number.isInteger(v) && (v as number) >= min && (v as number) <= max ? null : `expected an integer ${min}-${max}`;

/** Like zod's .strict(): every rule must pass and unknown keys are errors. */
export function strictParse<T>(shape: Record<string, Rule>, raw: unknown): { data: T } | { issues: string[] } {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return { issues: ["input: expected an object"] };
  const issues = Object.keys(raw).filter((k) => !(k in shape)).map((k) => `${k}: unrecognized key`);
  for (const [k, rule] of Object.entries(shape)) {
    const msg = rule((raw as Record<string, unknown>)[k]);
    if (msg) issues.push(`${k}: ${msg}`);
  }
  return issues.length ? { issues } : { data: raw as T };
}

const cartId = str(/^cart_[A-Za-z0-9]{12,32}$/, 17, 37);                 // explicit handle, not a protocol session
const idempotencyKey = str(/^[\x21-\x7e]+$/, 16, 64);
export const AddInput = { cartId, sku: str(/^SS-[A-Z0-9-]{4,24}$/, 7, 27), quantity: int(1, 5), idempotencyKey };
export const CheckoutInput = { cartId, idempotencyKey };
type AddArgs = { cartId: string; sku: string; quantity: number; idempotencyKey: string };
type CheckoutArgs = { cartId: string; idempotencyKey: string };

export type Mandate = { id: string; maxCartMinor: number; currency: "INR" | "USD" | "GBP"; expiresAt: number };
export type ToolResult =
  { isError?: boolean; content: { type: "text"; text: string }[]; structuredContent: Record<string, unknown> };
export type Stored = { hash: string; result: ToolResult | null };        // result null = first attempt still running
export type Ctx = {                                                      // built from the validated, audience-bound token
  userId: string; scopes: string[]; mandate: Mandate | null; receiptKey: string; now?: () => number;
  priceOf(sku: string, currency: string): Promise<number | null>;      // server catalogue, minor units; null = not sold
  cartTotal(cartId: string, userId: string): Promise<number | null>;    // null = not this user's cart
  mandateCommitted(mandateId: string, userId: string): Promise<number>; // open carts + placed orders under this mandate
  addLine(cartId: string, sku: string, qty: number, unitMinor: number, mandateId: string): Promise<number>;
  placeOrder(cartId: string, userId: string, mandateId: string, maxMinor: number):     // one transaction
    Promise<{ orderId: string; totalMinor: number } | { error: "LIMIT" | "EMPTY" | "NOT_FOUND" | "OTHER_MANDATE" }>;
  idem: { claim(k: string, hash: string): Promise<Stored | null>;     // atomic insert-if-absent; returns the prior entry
          finish(k: string, r: ToolResult): Promise<void>; release(k: string): Promise<void> };
};

export const fail = (code: string, msg: string): ToolResult =>
  ({ isError: true, content: [{ type: "text", text: `${code}: ${msg}` }], structuredContent: { error: code } });
const sha256 = (s: string) => createHash("sha256").update(s).digest("hex");

function signed(text: string, body: Record<string, unknown>, key: string): ToolResult {
  const signature = createHmac("sha256", key).update(JSON.stringify(body)).digest("base64url");
  return { content: [{ type: "text", text }], structuredContent: { ...body, signature } };
}

async function once(ctx: Ctx, key: string, hash: string, run: () => Promise<ToolResult>): Promise<ToolResult> {
  const prior = await ctx.idem.claim(key, hash);
  if (prior) {
    if (prior.hash !== hash) return fail("IDEMPOTENCY_CONFLICT", "key reused for a different request");
    return prior.result ?? fail("IN_PROGRESS", "the first request with this key is still running; retry shortly");
  }
  let result: ToolResult;
  try {
    result = await run();
  } catch (e) {
    await ctx.idem.release(key);
    throw e;
  }
  if (result.isError) await ctx.idem.release(key);   // no side effect happened; the user may fix it and retry
  else await ctx.idem.finish(key, result);
  return result;
}

function liveMandate(ctx: Ctx): Mandate | null {
  const m = ctx.mandate;
  return m && m.expiresAt > (ctx.now ?? Date.now)() ? m : null;
}

export async function addToCart(raw: unknown, ctx: Ctx): Promise<ToolResult> {
  const parsed = strictParse<AddArgs>(AddInput, raw);
  if ("issues" in parsed) return fail("INVALID_INPUT", parsed.issues.join("; "));
  const inp = parsed.data;
  if (!ctx.scopes.includes("cart:write")) return fail("INSUFFICIENT_SCOPE", "cart:write required");
  const hash = sha256(JSON.stringify([inp.cartId, inp.sku, inp.quantity]));
  return once(ctx, `${ctx.userId}:${inp.idempotencyKey}`, hash, async () => {
    const m = liveMandate(ctx);
    if (!m) return fail("NO_VALID_MANDATE", "ask the user to approve a spending limit");
    const unit = await ctx.priceOf(inp.sku, m.currency);
    if (unit === null) return fail("NOT_AVAILABLE", "SKU not sold in this currency or region, or out of stock");
    if ((await ctx.cartTotal(inp.cartId, ctx.userId)) === null) return fail("CART_NOT_FOUND", "unknown cart for this user");
    const projected = (await ctx.mandateCommitted(m.id, ctx.userId)) + unit * inp.quantity;
    if (projected > m.maxCartMinor) {  // soft check across every open cart and order; checkout re-checks atomically
      const why = `mandate total would be ${projected} > ${m.maxCartMinor} ${m.currency}; user must approve`;
      return fail("MANDATE_LIMIT_EXCEEDED", why);
    }
    const total = await ctx.addLine(inp.cartId, inp.sku, inp.quantity, unit, m.id);
    const body = { receiptId: `rcpt_${randomUUID()}`, cartId: inp.cartId, sku: inp.sku, quantity: inp.quantity,
      unitPriceMinor: unit, cartTotalMinor: total, currency: m.currency, mandateId: m.id, issuedAt: new Date().toISOString() };
    return signed(`Added ${inp.quantity} x ${inp.sku}. Cart total ${total} ${m.currency} (minor units).`, body, ctx.receiptKey);
  });
}

export async function checkout(raw: unknown, ctx: Ctx): Promise<ToolResult> {
  const parsed = strictParse<CheckoutArgs>(CheckoutInput, raw);
  if ("issues" in parsed) return fail("INVALID_INPUT", parsed.issues.join("; "));
  const inp = parsed.data;
  if (!ctx.scopes.includes("cart:write")) return fail("INSUFFICIENT_SCOPE", "cart:write required");
  return once(ctx, `${ctx.userId}:checkout:${inp.idempotencyKey}`, sha256(inp.cartId), async () => {
    const m = liveMandate(ctx);
    if (!m) return fail("NO_VALID_MANDATE", "ask the user to approve a spending limit");
    const r = await ctx.placeOrder(inp.cartId, ctx.userId, m.id, m.maxCartMinor);
    if ("error" in r) {
      if (r.error === "LIMIT") return fail("MANDATE_LIMIT_EXCEEDED", "orders under this mandate would exceed it; user must approve");
      return fail({ EMPTY: "CART_EMPTY", NOT_FOUND: "CART_NOT_FOUND", OTHER_MANDATE: "MANDATE_CHANGED" }[r.error], r.error);
    }
    const body = { receiptId: `rcpt_${randomUUID()}`, orderId: r.orderId, totalMinor: r.totalMinor, currency: m.currency,
      mandateId: m.id, checkoutUrl: `https://www.neyyarasi.example/checkout/${r.orderId}`, issuedAt: new Date().toISOString() };
    return signed(`Order ${r.orderId} ready for the shopper to pay at the checkout link.`, body, ctx.receiptKey);
  });
}
