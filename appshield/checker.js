/* AppShield — Google Play Target API 36 / Billing Library v8 deadline checker.
 *
 * Runs entirely in the browser: files are read locally and never uploaded.
 * The detection logic is ported from AppShield's verified rule registry
 * (GOOGLE-PERM-003, GOOGLE-BILL-002, GOOGLE-BILL-001) — same patterns,
 * verified against Google's official policy pages on 2026-08-28.
 *
 * Honesty contract: "not found" is reported as NOT FOUND, never as a pass.
 */
(function (root) {
  "use strict";

  var REQUIRED_TARGET_SDK = 36;
  var REQUIRED_BILLING_MAJOR = 8;

  // Which files each check reads.
  var GRADLE_FILE = /(^|[\\/])build\.gradle(\.kts)?$/i;
  var MANIFEST_FILE = /(^|[\\/])AndroidManifest\.xml$/i;
  var CATALOG_FILE = /(^|[\\/])libs\.versions\.toml$/i;
  var CODE_FILE = /\.(java|kt|kts|gradle|xml|js|ts|dart|cs|toml|properties)$/i;

  // targetSdk 34 / targetSdkVersion 34 / targetSdk = 34 / targetSdkVersion=34
  var TARGET_SDK_RE = /targetSdk(?:Version)?\s*(?:[:=]\s*|\s+)(\d{1,3})\b/g;
  // Legacy manifests: <uses-sdk android:targetSdkVersion="30" />
  var MANIFEST_SDK_RE = /android:targetSdkVersion\s*=\s*["'](\d{1,3})["']/g;
  // com.android.billingclient:billing:6.2.1 (or billing-ktx)
  var BILLING_DEP_RE = /com\.android\.billingclient:billing(?:-ktx)?:(\d{1,2})\./g;
  // version catalog or gradle ext: billing = "6.0.1" / billingVersion = '7.1.1'
  var BILLING_VAR_RE = /\b(?:billing[-_]?(?:client[-_]?)?version|billing)\s*=\s*["'](\d{1,2})\./gi;
  // Third-party processors near digital-goods words (heads-up only — heuristic).
  var ALT_PAY_RES = [
    /(?:stripe|paypal|braintree)[\s\S]{0,80}?(?:subscribe|premium|unlock|pro\b|upgrade|coin|gem|token)/i,
    /(?:premium|pro\b|unlock)[\s\S]{0,80}?(?:stripe|paypal|braintree)/i,
  ];

  function findAll(re, text) {
    re.lastIndex = 0;
    var out = [], m;
    while ((m = re.exec(text)) !== null) {
      out.push({ value: parseInt(m[1], 10), index: m.index });
      if (m.index === re.lastIndex) re.lastIndex++;
    }
    return out;
  }

  function lineOf(text, index) {
    var upto = text.slice(0, index);
    var line = upto.split("\n").length;
    var start = upto.lastIndexOf("\n") + 1;
    var end = text.indexOf("\n", index);
    return { line: line, text: text.slice(start, end === -1 ? text.length : end).trim().slice(0, 160) };
  }

  // files: [{name, content}] — analyze returns {targetSdk, billing, altPay}
  function analyze(files) {
    var sdkHits = [], billingHits = [], altPayHits = [];
    var sawGradle = false, sawManifest = false;

    files.forEach(function (f) {
      var isGradle = GRADLE_FILE.test(f.name);
      var isManifest = MANIFEST_FILE.test(f.name);
      var isCatalog = CATALOG_FILE.test(f.name);
      if (isGradle) sawGradle = true;
      if (isManifest) sawManifest = true;

      if (isGradle) {
        findAll(TARGET_SDK_RE, f.content).forEach(function (h) {
          var loc = lineOf(f.content, h.index);
          sdkHits.push({ file: f.name, line: loc.line, evidence: loc.text, value: h.value });
        });
      }
      if (isManifest) {
        findAll(MANIFEST_SDK_RE, f.content).forEach(function (h) {
          var loc = lineOf(f.content, h.index);
          sdkHits.push({ file: f.name, line: loc.line, evidence: loc.text, value: h.value });
        });
      }
      if (isGradle || isCatalog) {
        findAll(BILLING_DEP_RE, f.content).forEach(function (h) {
          var loc = lineOf(f.content, h.index);
          billingHits.push({ file: f.name, line: loc.line, evidence: loc.text, major: h.value });
        });
        findAll(BILLING_VAR_RE, f.content).forEach(function (h) {
          var loc = lineOf(f.content, h.index);
          // Skip lines already matched as a full dependency string.
          if (!/com\.android\.billingclient/.test(loc.text)) {
            billingHits.push({ file: f.name, line: loc.line, evidence: loc.text, major: h.value });
          }
        });
      }
      if (CODE_FILE.test(f.name)) {
        ALT_PAY_RES.forEach(function (re) {
          var m = re.exec(f.content);
          if (m) {
            var loc = lineOf(f.content, m.index);
            altPayHits.push({ file: f.name, line: loc.line, evidence: loc.text });
          }
        });
      }
    });

    // ── targetSdk verdict ──
    var targetSdk;
    if (sdkHits.length === 0) {
      targetSdk = {
        status: "not_found",
        detail: sawGradle || sawManifest
          ? "No targetSdk declaration found in the gradle/manifest files provided. If your target SDK comes from a variable, CI config, or a file you didn't include, add that file and re-run."
          : "No build.gradle, build.gradle.kts, or AndroidManifest.xml was provided — nothing to check the target SDK against. This is NOT a pass.",
        hits: [],
      };
    } else {
      var worst = sdkHits.reduce(function (a, b) { return a.value <= b.value ? a : b; });
      targetSdk = {
        status: worst.value >= REQUIRED_TARGET_SDK ? "pass" : "fail",
        found: worst.value,
        required: REQUIRED_TARGET_SDK,
        hits: sdkHits,
      };
    }

    // ── billing verdict ──
    var billing;
    if (billingHits.length === 0) {
      billing = {
        status: "not_found",
        detail: "No Google Play Billing Library dependency detected. If your app sells NO digital goods or subscriptions, that's fine. If it does and billing comes from a module you didn't include, add that build.gradle and re-run.",
        hits: [],
      };
    } else {
      var worstB = billingHits.reduce(function (a, b) { return a.major <= b.major ? a : b; });
      billing = {
        status: worstB.major >= REQUIRED_BILLING_MAJOR ? "pass" : "fail",
        found: worstB.major,
        required: REQUIRED_BILLING_MAJOR,
        hits: billingHits,
      };
    }

    return {
      targetSdk: targetSdk,
      billing: billing,
      altPay: { status: altPayHits.length ? "warn" : "clear", hits: altPayHits },
      filesScanned: files.length,
    };
  }

  var api = { analyze: analyze, REQUIRED_TARGET_SDK: REQUIRED_TARGET_SDK, REQUIRED_BILLING_MAJOR: REQUIRED_BILLING_MAJOR };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.AppShieldCheck = api;
})(typeof self !== "undefined" ? self : this);
