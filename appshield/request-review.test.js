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
  service: "verification",
  store: "Google Play",
  build: "Yes — APK or Android test track",
  flows: "6–9",
  locale: "English (United States)",
  role: "standard signed-in user",
  "target-date": "2026-09-15",
  rejection: "No",
  rejection_text: "Your app was rejected for guideline 5.1.1 data collection.",
  notes: "Account and purchase flows"
};

const SERVICE_VALUES = ["preflight", "verification", "launch", "rejection", "agency"];

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
const window = { location: { href: "", search: "?service=verification" } };
// Steerable stub for the server capture call. `fetchMode` decides whether the
// endpoint accepts, rejects, or is unreachable, so both branches are covered.
let fetchMode = "ok";
const fetchCalls = [];
function fetch(url, init) {
  fetchCalls.push({ url, body: JSON.parse(init.body) });
  if (fetchMode === "network") return Promise.reject(new Error("offline"));
  if (fetchMode === "reject") {
    return Promise.resolve({ ok: false, json: () => Promise.resolve({ error: "Nope." }) });
  }
  return Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true, received: true }) });
}
const document = { getElementById(id) { return elements.get(id); } };

vm.runInNewContext(controller, { document, navigator, window, String, Promise, Error, encodeURIComponent, RegExp, decodeURIComponent, Object, fetch, JSON });

// --- service select markup: the five options must exist with these exact values ---
const optionValues = [...html.matchAll(/<option value="([a-z]+)">/g)]
  .map((m) => m[1])
  .filter((v) => SERVICE_VALUES.includes(v));
assert.deepEqual(optionValues, SERVICE_VALUES, "service select must offer exactly the five service options, in order");

// --- ?service= preselect: run the controller in a fully isolated sandbox for each case.
// (Reusing the shared `elements`/`listeners` here would let a later run's addEventListener
// calls clobber the submit handler the main flow test below depends on.)
function isolatedElement(id) {
  return {
    id, value: values[id] || "", hidden: id === "request-fallback", style: {},
    addEventListener() {}, reportValidity() { return true; }, focus() {}, select() {}
  };
}
function runWithQuery(search) {
  const localElements = new Map([
    "request-form", "form-message", "copy-request", "request-fallback", "request-copy",
    ...Object.keys(values)
  ].map((id) => [id, isolatedElement(id)]));
  const localDocument = { getElementById(id) { return localElements.get(id); } };
  const localWindow = { location: { href: "", search } };
  const localNavigator = { clipboard: { writeText: () => Promise.resolve() } };
  vm.runInNewContext(controller, {
    document: localDocument, navigator: localNavigator, window: localWindow,
    String, Promise, Error, encodeURIComponent, RegExp, decodeURIComponent, Object, fetch, JSON
  });
  return localElements.get("service").value;
}

assert.equal(runWithQuery("?service=agency"), "agency", "?service=agency must preselect the agency option");
assert.equal(runWithQuery("?service=not-a-real-service"), "preflight", "an invalid ?service= must fall back to preflight");
assert.equal(runWithQuery(""), "preflight", "no ?service= must default to preflight");

async function settle() {
  await Promise.resolve();
  await new Promise((resolve) => setImmediate(resolve));
}

(async function run() {
  let prevented = false;
  listeners["request-form:submit"]({ preventDefault() { prevented = true; } });
  await settle();

  assert.equal(prevented, true, "form submission must be intercepted");
  assert.equal(elements.get("service").value, "verification", "?service=verification must have preselected the service select before submit");

  // The request must reach AppShield's own endpoint, not depend on a mail client.
  assert.equal(fetchCalls.length, 1, "submitting must POST the request to the capture endpoint");
  assert.match(fetchCalls[0].url, /\/request$/, "capture endpoint must be the /request route");
  assert.equal(fetchCalls[0].body.kind, "review_request");
  assert.equal(fetchCalls[0].body.email, "casey@example.com", "sender email must be sent as a field, not only inside the text");
  assert.equal(fetchCalls[0].body.service, "verification");
  assert.equal(fetchCalls[0].body.source, "request-review");
  assert.match(fetchCalls[0].body.message, /Sender email: casey@example\.com/);
  assert.match(fetchCalls[0].body.message, /Service requested: Verification & Account Concierge \(\$129\)/, "composed summary must contain the selected service's name");
  assert.match(fetchCalls[0].body.message, /Rejection or warning text: Your app was rejected for guideline 5\.1\.1 data collection\./, "composed summary must contain the pasted rejection text");
  assert.match(fetchCalls[0].body.message, /Notes: Account and purchase flows/);
  assert.match(elements.get("form-message").textContent, /received/i, "a successful capture must tell the visitor it arrived");
  assert.equal(window.location.href, "", "a successful capture must NOT hijack the page into a mailto");
  assert.match(writes[0], /AppShield review request/, "a copy is still placed on the clipboard as a convenience");

  // Server refuses: the visitor must not be left with a silently lost request.
  fetchMode = "reject";
  window.location.href = "";
  listeners["request-form:submit"]({ preventDefault() {} });
  await settle();
  assert.match(window.location.href, /^mailto:awesomo913@gmail\.com\?subject=/, "a refused capture must fall back to the mailto handoff");
  assert.doesNotMatch(window.location.href, /(?:[?&]|&amp;)body=/i);
  assert.doesNotMatch(window.location.href, /casey%40example\.com/i);

  // Endpoint unreachable: same guarantee.
  fetchMode = "network";
  window.location.href = "";
  elements.get("form-message").textContent = "";
  listeners["request-form:submit"]({ preventDefault() {} });
  await settle();
  assert.match(elements.get("form-message").textContent, /network problem/i, "an unreachable endpoint must say so plainly");
  assert.match(window.location.href, /^mailto:awesomo913@gmail\.com\?subject=/, "an unreachable capture must fall back to the mailto handoff");
  fetchMode = "ok";

  navigator.clipboard.writeText = () => Promise.reject(new Error("blocked"));
  listeners["copy-request:click"]();
  await settle();

  assert.equal(elements.get("request-fallback").hidden, false, "blocked clipboard must reveal fallback");
  assert.match(elements.get("request-copy").value, /AppShield review request/);
  assert.match(elements.get("form-message").textContent, /manual copy/i);
  console.log("ALL REQUEST FLOW TESTS PASS");
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
