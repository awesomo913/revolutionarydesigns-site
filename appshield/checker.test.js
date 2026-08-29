/* Node test runner for checker.js — run: node checker.test.js */
const C = require("./checker.js");
const cases = [
  ["groovy old sdk", [{ name: "app/build.gradle", content: "android {\n  defaultConfig {\n    targetSdkVersion 30\n  }\n}" }], r => r.targetSdk.status === "fail" && r.targetSdk.found === 30],
  ["kts new sdk", [{ name: "app/build.gradle.kts", content: "defaultConfig {\n  targetSdk = 36\n}" }], r => r.targetSdk.status === "pass"],
  ["colon form 35", [{ name: "build.gradle", content: "targetSdkVersion: 35" }], r => r.targetSdk.status === "fail"],
  ["manifest legacy", [{ name: "AndroidManifest.xml", content: "<uses-sdk android:targetSdkVersion=\"29\"/>" }], r => r.targetSdk.status === "fail" && r.targetSdk.found === 29],
  ["multi-module worst wins", [{ name: "a/build.gradle", content: "targetSdkVersion 36" }, { name: "b/build.gradle", content: "targetSdkVersion 33" }], r => r.targetSdk.status === "fail" && r.targetSdk.found === 33],
  ["no files", [], r => r.targetSdk.status === "not_found" && r.billing.status === "not_found"],
  ["sdk in java not counted", [{ name: "Main.java", content: "int targetSdkVersion = 21;" }], r => r.targetSdk.status === "not_found"],
  ["billing v6 dep", [{ name: "app/build.gradle", content: "implementation \"com.android.billingclient:billing:6.2.1\"" }], r => r.billing.status === "fail" && r.billing.found === 6],
  ["billing v6 ktx", [{ name: "app/build.gradle", content: "implementation(\"com.android.billingclient:billing-ktx:6.0.1\")" }], r => r.billing.status === "fail"],
  ["billing v8 pass", [{ name: "app/build.gradle", content: "implementation \"com.android.billingclient:billing:8.0.0\"" }], r => r.billing.status === "pass"],
  ["billing v9 pass", [{ name: "app/build.gradle", content: "implementation \"com.android.billingclient:billing-ktx:9.0.0\"" }], r => r.billing.status === "pass" && r.billing.found === 9],
  ["billing 7.1.1 fail (lookahead bug regression)", [{ name: "build.gradle", content: "com.android.billingclient:billing:7.1.1" }], r => r.billing.status === "fail" && r.billing.found === 7],
  ["catalog var", [{ name: "gradle/libs.versions.toml", content: "[versions]\nbilling = \"7.0.0\"" }], r => r.billing.status === "fail" && r.billing.found === 7],
  ["gradle ext var", [{ name: "build.gradle", content: "billingVersion = \"6.1.0\"" }], r => r.billing.status === "fail"],
  ["catalog v9 pass", [{ name: "gradle/libs.versions.toml", content: "billing = \"9.0.0\"" }], r => r.billing.status === "pass"],
  ["altpay warn", [{ name: "Pay.kt", content: "fun goPremium() { stripe.checkout(\"premium_upgrade\") }" }], r => r.altPay.status === "warn"],
  ["altpay clear on physical goods", [{ name: "Pay.kt", content: "stripe.checkout(shippingAddress)" }], r => r.altPay.status === "clear"],
  ["mixed real project", [
    { name: "app/build.gradle", content: "android{ defaultConfig{ targetSdkVersion 34 } }\ndependencies{ implementation \"com.android.billingclient:billing:6.2.1\" }" },
    { name: "AndroidManifest.xml", content: "<manifest/>" },
  ], r => r.targetSdk.status === "fail" && r.targetSdk.found === 34 && r.billing.status === "fail"],
];
let bad = 0;
for (const [name, files, check] of cases) {
  const r = C.analyze(files);
  if (!check(r)) { bad++; console.log("FAIL", name, JSON.stringify(r).slice(0, 300)); }
  else console.log("pass", name);
}
console.log(bad === 0 ? "ALL " + cases.length + " PASS" : "FAILURES: " + bad);
process.exit(bad ? 1 : 0);
