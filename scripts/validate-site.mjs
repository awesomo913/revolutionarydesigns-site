import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const ignoredDirectories = new Set([".git", "node_modules"]);
const errors = [];

function walk(directory) {
  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue;
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...walk(absolute));
    else if (entry.isFile() && entry.name.endsWith(".html")) files.push(absolute);
  }
  return files;
}

function attributes(html, name) {
  const values = [];
  const pattern = new RegExp(`\\s${name}\\s*=\\s*["']([^"']*)["']`, "gi");
  for (const match of html.matchAll(pattern)) values.push(match[1]);
  return values;
}

function targetFor(url) {
  let target = path.join(root, decodeURIComponent(url.pathname).replace(/^\/+/, ""));
  if (url.pathname.endsWith("/") || (fs.existsSync(target) && fs.statSync(target).isDirectory())) {
    target = path.join(target, "index.html");
  }
  return target;
}

const htmlFiles = walk(root);
const idCache = new Map();

for (const file of htmlFiles) {
  const html = fs.readFileSync(file, "utf8");
  const relative = path.relative(root, file).replaceAll(path.sep, "/");
  const ids = attributes(html, "id");
  idCache.set(path.resolve(file), new Set(ids));

  const duplicates = ids.filter((id, index) => ids.indexOf(id) !== index);
  for (const id of new Set(duplicates)) errors.push(`${relative}: duplicate id #${id}`);

  for (const match of html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/gi)) {
    const scriptAttributes = match[1];
    const scriptBody = match[2];
    if (/type=["']application\/ld\+json["']/i.test(scriptAttributes)) {
      try {
        JSON.parse(scriptBody);
      } catch (error) {
        errors.push(`${relative}: invalid JSON-LD (${error.message})`);
      }
    } else if (!/\ssrc\s*=/i.test(scriptAttributes) && scriptBody.trim()) {
      try {
        new Function(scriptBody);
      } catch (error) {
        errors.push(`${relative}: invalid inline JavaScript (${error.message})`);
      }
    }
  }

  if ((relative === "index.html" || relative.startsWith("appshield/")) &&
      /fonts\.googleapis\.com[^"']*&(?:family|display)=/i.test(html)) {
    errors.push(`${relative}: Google Fonts URL contains an unescaped ampersand`);
  }
}

for (const file of htmlFiles) {
  const html = fs.readFileSync(file, "utf8");
  const relative = path.relative(root, file).replaceAll(path.sep, "/");
  const base = new URL(relative, "https://revolutionarydesigns.io/");

  for (const href of attributes(html, "href")) {
    if (!href || /^(?:mailto|tel|javascript|data):/i.test(href)) continue;

    let url;
    try {
      url = new URL(href, base);
    } catch {
      errors.push(`${relative}: invalid href ${href}`);
      continue;
    }

    if (url.origin !== "https://revolutionarydesigns.io") continue;
    const target = targetFor(url);
    if (!fs.existsSync(target)) {
      errors.push(`${relative}: missing local target ${href}`);
      continue;
    }

    if (url.hash) {
      const fragment = decodeURIComponent(url.hash.slice(1));
      if (!fragment) continue;
      const resolved = path.resolve(target);
      let targetIds = idCache.get(resolved);
      if (!targetIds) {
        targetIds = new Set(attributes(fs.readFileSync(resolved, "utf8"), "id"));
        idCache.set(resolved, targetIds);
      }
      if (!targetIds.has(fragment)) errors.push(`${relative}: missing anchor ${href}`);
    }
  }
}

const checkerFile = path.join(root, "appshield", "index.html");
const checkerHtml = fs.readFileSync(checkerFile, "utf8");
const requiredCheckerIds = [
  "drop", "filepick", "folderpick", "browse-files-btn", "browse-folder-btn",
  "drop-tab", "paste-toggle", "pastebox", "paste-actions", "paste-run",
  "results", "emailband", "emailform", "email", "consent", "email-msg",
  "footer-email-link"
];

for (const id of requiredCheckerIds) {
  const count = attributes(checkerHtml, "id").filter((value) => value === id).length;
  if (count !== 1) errors.push(`appshield/index.html: expected one #${id}, found ${count}`);
}

const engineIndex = checkerHtml.indexOf('<script src="checker.js"></script>');
const initializerIndex = checkerHtml.indexOf("(function(){", engineIndex);
if (engineIndex < 0 || initializerIndex < engineIndex) {
  errors.push("appshield/index.html: checker.js must load before the inline initializer");
}

if (!checkerHtml.includes('class="checker-zone ph-no-capture" id="checker"')) {
  errors.push("appshield/index.html: checker and signup area must opt out of PostHog autocapture");
}

const requestFile = path.join(root, "appshield", "request-review.html");
const requestHtml = fs.readFileSync(requestFile, "utf8");
const requiredRequestIds = [
  "request-form", "copy-request", "request-fallback", "request-copy", "form-message"
];

for (const id of requiredRequestIds) {
  const count = attributes(requestHtml, "id").filter((value) => value === id).length;
  if (count !== 1) errors.push(`appshield/request-review.html: expected one #${id}, found ${count}`);
}

if (/mailto:[^"']*[?&](?:amp;)?body=/i.test(requestHtml)) {
  errors.push("appshield/request-review.html: keep request text out of mailto URLs; use the copy fallback");
}

const requestForm = requestHtml.match(/<form\b[^>]*id=["']request-form["'][^>]*>([\s\S]*?)<\/form>/i);
if (!requestForm || /\sname\s*=/i.test(requestForm[1])) {
  errors.push("appshield/request-review.html: request controls must not have name attributes that can leak through native GET submission");
}

const intakeFile = path.join(root, "appshield", "client-intake.html");
const intakeHtml = fs.readFileSync(intakeFile, "utf8");
const requiredIntakeIds = [
  "intake-form", "scope-id", "checkout-email", "app-name", "store",
  "build-version", "locale", "role", "access-method", "flows", "notes",
  "authorized", "safe", "copy-intake", "intake-fallback", "intake-copy", "form-message"
];

for (const id of requiredIntakeIds) {
  const count = attributes(intakeHtml, "id").filter((value) => value === id).length;
  if (count !== 1) errors.push(`appshield/client-intake.html: expected one #${id}, found ${count}`);
}

if (!/name=["']robots["'][^>]*content=["'][^"']*noindex/i.test(intakeHtml)) {
  errors.push("appshield/client-intake.html: paid intake page must remain noindex");
}

if (/mailto:[^"']*[?&](?:amp;)?body=/i.test(intakeHtml)) {
  errors.push("appshield/client-intake.html: keep intake data out of mailto URLs; use the copy fallback");
}

const intakeForm = intakeHtml.match(/<form\b[^>]*id=["']intake-form["'][^>]*>([\s\S]*?)<\/form>/i);
if (!intakeForm || /\sname\s*=/i.test(intakeForm[1])) {
  errors.push("appshield/client-intake.html: intake controls must not have name attributes that can leak through native GET submission");
}

const paymentReturnHtml = fs.readFileSync(path.join(root, "appshield", "payment-complete.html"), "utf8");
if (!/name=["']robots["'][^>]*content=["'][^"']*noindex/i.test(paymentReturnHtml)) {
  errors.push("appshield/payment-complete.html: payment return page must remain noindex");
}

if (errors.length) {
  console.error(`Site validation failed with ${errors.length} error(s):`);
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log(`Site validation passed: ${htmlFiles.length} HTML files, local links, anchors, IDs, and JSON-LD.`);
