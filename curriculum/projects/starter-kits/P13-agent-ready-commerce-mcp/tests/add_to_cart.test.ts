// Tests for the §7 control (add_to_cart.ts): the reviewed behaviour of the brief's sketch, plus curveballs 4 and 5.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { addToCart, checkout, type Mandate } from "../add_to_cart.ts";
import { MemoryStore } from "../baseline.ts";

const PRICES: Record<string, Record<string, number>> = {  // minor units; SS-GONE-0001 is out of stock
  "SS-BRD-LEHENGA": { INR: 2200000, GBP: 23000 }, "SS-BRD-BLOUSE": { INR: 800000 }, "SS-BRD-DUPATTA": { INR: 1200000 } };
const KEY = "test-receipt-key";
const inr = (max: number, over: Partial<Mandate> = {}): Mandate =>
  ({ id: "md-1", maxCartMinor: max, currency: "INR", expiresAt: Date.now() + 60_000, ...over });

function setup(mandate: Mandate | null = inr(2_500_000), scopes = ["cart:write"]) {
  const store = new MemoryStore((sku, cur) => PRICES[sku]?.[cur] ?? null);
  const cart = store.createCart("u1");
  const ctx = store.ctx("u1", scopes, mandate, KEY);
  const add = (sku: string, key: string, extra: Record<string, unknown> = {}, onCart = cart) =>
    addToCart({ cartId: onCart, sku, quantity: 1, idempotencyKey: key, ...extra }, ctx);
  return { store, cart, ctx, add };
}
const code = (r: { structuredContent: Record<string, unknown> }) => r.structuredContent.error;
const lines = (s: MemoryStore) => [...s.carts.values()].flatMap((c) => c.lines).length;

test("valid add: price from the server catalogue in the mandate currency, signed receipt", async () => {
  const { store, ctx, cart } = setup(inr(100_000, { currency: "GBP" }));
  const r = await addToCart({ cartId: cart, sku: "SS-BRD-LEHENGA", quantity: 2, idempotencyKey: "k-0000000000000001" }, ctx);
  assert.equal(r.isError, undefined);
  const { signature, ...body } = r.structuredContent;
  assert.equal(body.unitPriceMinor, 23000);
  assert.equal(body.cartTotalMinor, 46000);
  assert.equal(signature, createHmac("sha256", KEY).update(JSON.stringify(body)).digest("base64url"));
  assert.equal(lines(store), 1);
});

test("strict input: price, currency and unknown fields are rejected, with the path in the message", async () => {
  const { add, store } = setup();
  for (const extra of [{ price: 1 }, { currency: "USD" }, { unitPriceMinor: 0 }]) {
    const r = await add("SS-BRD-BLOUSE", "k-0000000000000002", extra);
    assert.equal(code(r), "INVALID_INPUT");
    assert.match(r.content[0].text, new RegExp(`${Object.keys(extra)[0]}: unrecognized key`));
  }
  assert.equal(code(await add("SS-BRD-BLOUSE", "k-0000000000000002", { quantity: 6 })), "INVALID_INPUT");
  assert.equal(code(await add("ss-lower", "k-0000000000000002")), "INVALID_INPUT");
  assert.equal(code(await add("SS-BRD-BLOUSE", "short-key")), "INVALID_INPUT");
  assert.equal(lines(store), 0);
});

test("curveball 4: tutorial-era calls with a session id and no cartId are refused", async () => {
  const { ctx, store } = setup();
  const legacy = { sessionId: "sess-1-a1b2c3d4", sku: "SS-BRD-BLOUSE", quantity: 1, idempotencyKey: "k-0000000000000003" };
  const r = await addToCart(legacy, ctx);
  assert.equal(code(r), "INVALID_INPUT");
  assert.match(r.content[0].text, /sessionId: unrecognized key; cartId: expected/);
  assert.equal(lines(store), 0);
});

test("scope, mandate and cart ownership fail closed", async () => {
  assert.equal(code(await setup(inr(9e9), ["orders:read"]).add("SS-BRD-BLOUSE", "k-0000000000000004")), "INSUFFICIENT_SCOPE");
  assert.equal(code(await setup(null).add("SS-BRD-BLOUSE", "k-0000000000000004")), "NO_VALID_MANDATE");
  const now = Date.now(), { store, cart, add } = setup();
  const expired = { ...store.ctx("u1", ["cart:write"], inr(9e9, { expiresAt: now }), KEY), now: () => now };
  const r = await addToCart({ cartId: cart, sku: "SS-BRD-BLOUSE", quantity: 1, idempotencyKey: "k-0000000000000005" }, expired);
  assert.equal(code(r), "NO_VALID_MANDATE");  // expiresAt == now is already expired
  assert.equal(code(await add("SS-BRD-BLOUSE", "k-0000000000000006", {}, store.createCart("u2"))), "CART_NOT_FOUND");
  assert.equal(code(await add("SS-GONE-0001", "k-0000000000000007")), "NOT_AVAILABLE");
});

test("idempotency: a replay returns the stored result; reusing the key for another request conflicts", async () => {
  const { add, store } = setup();
  const first = await add("SS-BRD-BLOUSE", "k-0000000000000008");
  const again = await add("SS-BRD-BLOUSE", "k-0000000000000008");
  assert.deepEqual(again, first);  // same receipt id, no second line
  assert.equal(lines(store), 1);
  assert.equal(code(await add("SS-BRD-DUPATTA", "k-0000000000000008")), "IDEMPOTENCY_CONFLICT");
});

test("idempotency: concurrent duplicates add one line (atomic claim, not check-then-write)", async () => {
  const { add, store } = setup(inr(9e9));
  const results = await Promise.all(Array.from({ length: 5 }, () => add("SS-BRD-BLOUSE", "k-0000000000000009")));
  assert.equal(results.filter((r) => !r.isError).length, 1);
  assert.ok(results.filter((r) => r.isError).every((r) => code(r) === "IN_PROGRESS"));
  assert.equal(lines(store), 1);
  assert.equal((await add("SS-BRD-BLOUSE", "k-0000000000000009")).isError, undefined);  // the late retry gets the result
});

test("idempotency keys are scoped to the user", async () => {
  const { store, add } = setup();
  await add("SS-BRD-BLOUSE", "k-0000000000000010");
  const other = store.ctx("u2", ["cart:write"], inr(9e9), KEY);
  const args = { cartId: store.createCart("u2"), sku: "SS-BRD-DUPATTA", quantity: 1, idempotencyKey: "k-0000000000000010" };
  const r = await addToCart(args, other);
  assert.equal(r.isError, undefined);
});

test("over the limit: MANDATE_LIMIT_EXCEEDED, nothing added, and the key is free once the user approves more", async () => {
  const { store, cart } = setup();
  const low = store.ctx("u1", ["cart:write"], inr(1_000_000), KEY);
  const args = { cartId: cart, sku: "SS-BRD-DUPATTA", quantity: 1, idempotencyKey: "k-0000000000000011" };
  const r = await addToCart(args, low);
  assert.equal(code(r), "MANDATE_LIMIT_EXCEEDED");
  assert.match(r.content[0].text, /user must approve/);
  assert.equal(lines(store), 0);
  const raised = store.ctx("u1", ["cart:write"], inr(2_000_000, { id: "md-2" }), KEY);
  assert.equal((await addToCart(args, raised)).isError, undefined);
});

test("curveball 5: a bridal set split across two carts is refused at the second cart", async () => {
  const { store, ctx, add, cart } = setup(inr(2_500_000));  // ₹25,000 mandate; set costs ₹42,000
  const cart2 = store.createCart("u1");
  assert.equal((await add("SS-BRD-LEHENGA", "k-0000000000000012")).isError, undefined);           // ₹22,000
  assert.equal(code(await add("SS-BRD-BLOUSE", "k-0000000000000013", {}, cart2)), "MANDATE_LIMIT_EXCEEDED");
  assert.equal((await checkout({ cartId: cart, idempotencyKey: "co-0000000000000001" }, ctx)).isError, undefined);
  assert.equal(code(await add("SS-BRD-BLOUSE", "k-0000000000000014", {}, cart2)), "MANDATE_LIMIT_EXCEEDED");  // orders count too
});

test("curveball 5, concurrent: both soft checks can pass, but checkout re-checks and places one order", async () => {
  const { store, ctx, add, cart } = setup(inr(2_500_000));
  const cart2 = store.createCart("u1");
  const [a, b] = await Promise.all([add("SS-BRD-LEHENGA", "k-0000000000000015"),
    add("SS-BRD-DUPATTA", "k-0000000000000016", {}, cart2)]);
  assert.equal(a.isError, undefined);  // the race lets both into carts: that is why checkout re-checks
  assert.equal(b.isError, undefined);
  const c1 = await checkout({ cartId: cart, idempotencyKey: "co-0000000000000002" }, ctx);
  const c2 = await checkout({ cartId: cart2, idempotencyKey: "co-0000000000000003" }, ctx);
  assert.equal(c1.isError, undefined);
  assert.equal(code(c2), "MANDATE_LIMIT_EXCEEDED");
  assert.equal(store.orders.reduce((s, o) => s + o.totalMinor, 0), 2_200_000);
});

test("checkout is idempotent and refuses empty or foreign carts", async () => {
  const { store, ctx, add, cart } = setup();
  await add("SS-BRD-BLOUSE", "k-0000000000000017");
  const req = { cartId: cart, idempotencyKey: "co-0000000000000004" };
  const [x, y] = [await checkout(req, ctx), await checkout(req, ctx)];
  assert.deepEqual(x, y);
  assert.equal(store.orders.length, 1);
  assert.match(String(x.structuredContent.checkoutUrl), /^https:\/\/www\.neyyarasi\.example\/checkout\//);
  assert.equal(code(await checkout({ cartId: store.createCart("u1"), idempotencyKey: "co-0000000000000005" }, ctx)), "CART_EMPTY");
  const foreign = { cartId: store.createCart("u2"), idempotencyKey: "co-0000000000000006" };
  assert.equal(code(await checkout(foreign, ctx)), "CART_NOT_FOUND");
});
