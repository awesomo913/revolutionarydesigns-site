"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(__dirname + "/request-review.html", "utf8");
const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/gi)];
assert.ok(scripts.length, "request page must contain its controller script");
const controller = scripts.at(-1)[1];

const listeners = {};
const values = {
  "app-name": "Quiet Garden",
  name: "Casey Founder",
  email: "casey@example.com",
  store: "Google Play",
  build: "Yes — APK or Android test track",
  flows: "6–9",
  locale: "English (United States)",
  role: "standard signed-in user",
  "target-date": "2026-09-15",
  rejection: "No",
  notes: "Account and purchase flows"
};

function element(id) {
  return {
    id,
    value: values[id] || "",
    hidden: id === "request-fallback",
    style: {},
    addEventListener(type, handler) { listeners[id + ":" + type] = handler; },
    reportValidity() { return true; },
    focus() {},
    select() {}
  };
}

const elements = new Map([
  "request-form", "form-message", "copy-request", "request-fallback", "request-copy",
  ...Object.keys(values)
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
  listeners["request-form:submit"]({ preventDefault() { prevented = true; } });
  await settle();

  assert.equal(prevented, true, "form submission must be intercepted");
  assert.match(writes[0], /Sender email: casey@example\.com/);
  assert.match(writes[0], /Notes: Account and purchase flows/);
  assert.match(window.location.href, /^mailto:awesomo913@gmail\.com\?subject=/);
  assert.doesNotMatch(window.location.href, /(?:[?&]|&amp;)body=/i);
  assert.doesNotMatch(window.location.href, /casey%40example\.com/i);

  navigator.clipboard.writeText = () => Promise.reject(new Error("blocked"));
  listeners["copy-request:click"]();
  await settle();

  assert.equal(elements.get("request-fallback").hidden, false, "blocked clipboard must reveal fallback");
  assert.match(elements.get("request-copy").value, /AppShield pilot request/);
  assert.match(elements.get("form-message").textContent, /manual copy/i);
  console.log("ALL REQUEST FLOW TESTS PASS");
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
