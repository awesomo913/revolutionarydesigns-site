"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(__dirname + "/client-intake.html", "utf8");
const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/gi)];
assert.ok(scripts.length, "intake page must contain its controller script");
const controller = scripts.at(-1)[1];

const listeners = {};
const values = {
  "scope-id": "AS-2026-001",
  "checkout-email": "casey@example.com",
  "app-name": "Quiet Garden",
  store: "Google Play",
  "build-version": "42 (1.8.0)",
  locale: "English (United States)",
  role: "standard signed-in customer",
  "access-method": "APK or Android internal test track",
  flows: "Onboarding\nLogin\nPurchase\nAccount deletion",
  notes: "Previous rejection supplied separately"
};

function element(id) {
  return {
    id,
    value: values[id] || "",
    checked: ["listing-ready", "declarations-ready", "authorized", "safe"].includes(id),
    hidden: id === "intake-fallback",
    addEventListener(type, handler) { listeners[id + ":" + type] = handler; },
    reportValidity() { return true; },
    focus() {},
    select() {}
  };
}

const elements = new Map([
  "intake-form", "form-message", "copy-intake", "intake-fallback", "intake-copy",
  "listing-ready", "declarations-ready", "authorized", "safe", ...Object.keys(values)
].map((id) => [id, element(id)]));

const writes = [];
const navigator = { clipboard: { writeText(text) { writes.push(text); return Promise.resolve(); } } };
const window = { location: { href: "" } };
const document = { getElementById(id) { return elements.get(id); } };

vm.runInNewContext(controller, { document, navigator, window, String, Promise, Error, encodeURIComponent });

async function settle() {
  await Promise.resolve();
  await new Promise((resolve) => setImmediate(resolve));
}

(async function run() {
  let prevented = false;
  listeners["intake-form:submit"]({ preventDefault() { prevented = true; } });
  await settle();

  assert.equal(prevented, true, "intake submission must be intercepted");
  assert.match(writes[0], /Approved scope ID: AS-2026-001/);
  assert.match(writes[0], /Checkout email: casey@example\.com/);
  assert.match(writes[0], /Account deletion/);
  assert.match(window.location.href, /^mailto:awesomo913@gmail\.com\?subject=/);
  assert.doesNotMatch(window.location.href, /(?:[?&]|&amp;)body=/i);
  assert.doesNotMatch(window.location.href, /casey%40example\.com/i);

  navigator.clipboard.writeText = () => Promise.reject(new Error("blocked"));
  listeners["copy-intake:click"]();
  await settle();

  assert.equal(elements.get("intake-fallback").hidden, false, "blocked clipboard must reveal fallback");
  assert.match(elements.get("intake-copy").value, /AppShield paid review intake summary/);
  assert.match(elements.get("form-message").textContent, /manual copy/i);
  console.log("ALL CLIENT INTAKE TESTS PASS");
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
