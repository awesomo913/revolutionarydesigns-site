# AppShield pilot fulfillment checklist

Use this checklist for every accepted paid pilot. The approved scope ID is the join key across the request, Stripe payment, intake, report, and email thread.

## 1. Approve the scope

- Confirm one app, one store, one submitted build, one locale, one primary role, and no more than 12 agreed flows.
- Confirm a runnable build is available, or label the work as a separately accepted limited materials review.
- Assign a unique scope ID such as `AS-2026-001`.
- Send the acceptance email with the exact scope, excluded items, price, payment deadline, delivery trigger, recheck window, safe-handoff rule, and legal links.
- Record the request and acceptance in the service ledger.

## 2. Match payment

- Open the Stripe payment, not merely the redirect visit.
- Confirm `Payment succeeded` and the expected `$99.00 USD` amount.
- Match customer email, app name, target store, and approved scope ID.
- Confirm the link has not exceeded the five completed sessions.
- Record the Stripe payment reference and paid time in the ledger.
- Send the payment-confirmed email.

## 3. Complete intake

- Match the client intake summary to the same scope ID.
- Send the restricted folder invitation and separate one-time or password-manager credential method.
- Reject and request rotation of any secret sent through ordinary email.
- Check every required material against `review-intake.html`.
- List missing or unusable items in one intake-incomplete email.
- When complete, record the exact intake-complete time and send the `Intake complete` email. This starts the 24–48 clock-hour window.

## 4. Run the review

- Create a working copy of the report template.
- Record the exact build, device, OS, store, locale, role, and agreed flow list before testing.
- Capture evidence only inside the accepted scope.
- For every finding, record observation, supplied claim, current official source when applicable, classification, severity, correction, and recheck condition.
- Mark untested or unprovable areas `Not Evaluated`; never imply certification or guaranteed approval.
- Check account creation/deletion, reviewer access, purchases, restore or management paths, permissions, broken links, placeholder content, listing claims, screenshots, privacy declarations, age rating, SDK/data inventory, and reviewer notes when they are in scope.

## 5. Quality check and deliver

- Verify every policy citation opens and supports the stated claim.
- Remove credentials, secrets, personal data, and unnecessary account identifiers from the report.
- Confirm the final recommendation matches the findings and scope limits.
- Export PDF and retain the Markdown source.
- Send the report-delivery email with clarification and recheck deadlines.
- Record delivery time and deadlines in the ledger.

## 6. Recheck and close

- Accept one focused recheck only for items flagged in the original report and submitted within seven days.
- Record pass, remaining issue, or unable-to-assess for each rechecked item.
- Send the recheck-complete email.
- Delete active working copies within seven days after the recheck window closes.
- Ask the client to revoke TestFlight, internal-test, folder, and disposable-account access.
- Record deletion and access-revocation reminders in the ledger.

## Service ledger fields

`Scope ID | App | Store | Client email | Request received | Scope accepted | Payment deadline | Stripe payment reference | Payment confirmed | Intake summary received | Intake complete | Review started | Report delivered | Clarification deadline | Recheck deadline | Recheck completed | Working-copy deletion due | Working copy deleted | Access-revocation reminder sent | Status | Notes`

Optional scope ID prefix convention for the newer services, so the ledger reads clearly at a glance: `AS-` preflight (unchanged), `AS-V-` verification concierge, `AS-L-` launch package, `AS-R-` rejection audit, `AS-A-` agency desk. This is a labeling convention only; the join-key rule above still applies to every scope ID regardless of prefix.

## 7. Verification concierge delivery checklist

Use this checklist for every accepted Android Developer Verification & Account Concierge engagement ($129 one-time). The same scope ID / ledger discipline from sections 1-6 applies; this section adds the service-specific steps.

- **Decision call agenda** (45 minutes, screen-share):
  1. Confirm which store(s) and which developer account(s) are in scope.
  2. Walk the Full Distribution ($25 one-time fee) vs Limited Distribution (free, capped at 20 devices) decision against the client's actual distribution plan; do not default to one option.
  3. Confirm whether the account is an individual or an organization account, since that changes the verification path.
  4. Confirm the regional deadline that applies (Sept 30 2026 for Brazil, Indonesia, Singapore, Thailand; 2027 for global) and whether the client's account falls under the enterprise/managed-device exemption.
  5. Record the decision and the reasoning in the client's file, not just a verbal agreement.
- **D-U-N-S walkthrough steps** (organization accounts only):
  1. Confirm whether the organization already has a D-U-N-S number; if not, explain the free application (typically up to 28 days) and start it now, before anything else in this engagement, since it is the longest lead time in the whole process.
  2. Confirm the legal business name, address, and other details the client will submit match their existing legal records exactly (mismatches are the most common cause of delay).
  3. Send the client the direct application link and confirm they applied; do not apply on their behalf.
  4. Track the application status at each follow-up until it resolves.
- **Document / prep checklist** (send before the decision call so the call is not spent gathering paperwork):
  - Government-issued ID type the client will use (do not collect the ID itself; confirm only that they have one ready)
  - Organization legal name, registered address, and D-U-N-S number (once issued)
  - Developer account email and the account type currently selected in Play Console
  - Any existing published apps under the account, so the concierge can flag account-type mismatches early
  - Primary contact for the 45-minute call and for async follow-up
- **Never-handle-credentials rule:** we never log in as the client, never hold their ID, never hold their credentials, and never create or verify accounts on their behalf. If a client sends a password, ID photo, or login session by email or chat, do not open it beyond confirming it needs to be revoked/rotated; tell them to remove it from the record and rotate/replace it. State this rule again in the acceptance email, not just verbally.
- **30-day follow-up cadence:**
  - Day 0: decision call complete, D-U-N-S application (if applicable) started, document checklist sent.
  - Day 7: check in on D-U-N-S status and any Google-side requests for more information.
  - Day 14: check in again; if D-U-N-S is still pending, remind the client this is expected (up to 28 days) and not a delay on our side.
  - Day 30 or Google confirmation, whichever comes first: close the engagement. If Google has not confirmed by day 30, send a closeout note explaining the engagement's included follow-up window has ended and offer a paid extension rather than open-ended free follow-up.
  - Record every check-in date and outcome in the service ledger under Notes.

## 8. Launch package delivery checklist

Use this checklist for every accepted Launch Package (Preflight + Closed Testing) engagement ($149 one-time). Run the standard preflight steps in sections 1-6 for the review half of the package, then add the following for the closed-testing half.

- **Cohort coordination via the developer community exchange:**
  - Confirm the client understands testers come from the exchange (real developers, real devices) and that the client is expected to test back for other developers' apps in the exchange, not just receive testers.
  - Recruit or confirm at least 12 opted-in testers before closed testing starts; do not start the clock with fewer than 12 opted in.
  - Never use purchased, fake, or bot testers. If the client asks for that, decline and explain why (it violates Google's testing requirements and risks the account).
- **Daily opted-in count tracking for 14 days:**
  - Record the opted-in tester count once per day for the full 14-day closed-testing window in the service ledger Notes field or a linked tracking sheet.
  - Flag to the client immediately (do not wait for the daily check-in) if the count drops below the minimum Google requires for production-access eligibility.
  - Note any tester attrition and whether replacements were recruited from the exchange.
- **Test-back obligations:**
  - Confirm the client is actually testing other developers' apps from the exchange during the same window, since exchange access depends on reciprocity.
  - Record which apps the client tested and roughly when, so there is a record if the exchange or Google asks.
- **Production-access application review:**
  - Before the client applies for production access, review the application against Google's current production-access requirements (support.google.com/googleplay/android-developer/answer/14151465) and the 14-day, 12+ tester history just built.
  - Flag anything likely to trigger a "more testing required" response before the client submits, not after.
  - Do not submit the application on the client's behalf; review and advise only.
  - Set expectations clearly: Google decides production access, this engagement does not guarantee it.

## 9. Rejection audit delivery checklist

Use this checklist for every accepted Rejection & Production-Access Audit engagement ($199 one-time).

- **Evidence intake:**
  - Collect the exact rejection notice, "more testing required" denial, or enforcement notice text and any screenshots Google provided.
  - Collect the submitted build/listing version that was rejected, or confirm it is unavailable and mark the audit as evidence-limited.
  - Confirm the date the rejection or enforcement action was issued, since appeal windows are date-driven (see below).
- **Policy-citation audit against the registry:**
  - Match every claim in Google's rejection/enforcement notice to the specific policy section it cites; do not accept a vague citation without tracing it to the actual current policy text.
  - Record each citation, its current official source URL, and whether the client's build/listing actually violates it, is a false positive, or is a partial/ambiguous match.
  - Where the notice cites a policy that has since been updated or superseded, note the version discrepancy explicitly.
- **Appeal-support brief outline:**
  1. Summary of the enforcement action and the specific policy cited.
  2. Facts as evidenced by the build/listing/account history (cite exactly what was checked).
  3. Point-by-point response to each cited policy violation, using only facts that can be evidenced; never assert something the audit did not actually verify.
  4. Remediation log: what was changed or will be changed, with dates.
  5. Requested outcome, stated plainly (reinstatement, reduced enforcement, clarification).
- **Resubmission plan:** a concrete, dated checklist of what must change in the build/listing/account before resubmission, separate from the appeal brief itself, so the client can act even if the appeal is denied.
- **Refusal criteria for fraud/ban-evasion cases:** decline the engagement (refund if already paid and work has not begun, per the refund rule in the payments runbook) if the intake evidence shows the account was terminated for fraud, ban evasion, or a similar trust-and-safety violation rather than a policy/technical rejection. Do not write an appeal brief that would help evade enforcement or that misstates facts to Google. If declining after payment has already begun, follow the standard refund terms in APPSHIELD-PAYMENTS.md, not an ad hoc arrangement.
- **Appeal window:** confirm the appeal is being filed within 180 days of the termination (rule in effect since Jan 28 2026, source: support.google.com/googleplay/android-developer/answer/16659089). If the client is already past 180 days, say so plainly before starting paid work.

## 10. Agency desk delivery checklist

Use this checklist for every active Agency Release Desk subscription ($399/month).

- **Monthly cadence:**
  - At the start of each billing month, confirm with the agency which up-to-3 apps/preflights are in scope for the month; anything beyond 3 is a separate $79 extra-preflight add-on (see APPSHIELD-PAYMENTS.md), confirmed by scope call first like every other engagement.
  - Track each month's included preflights against the 3/month cap in the service ledger so overage is caught before delivery, not after.
- **48-hour SLA:** the 48-hour turnaround clock starts at `Intake complete`, same trigger as the standard preflight (section 3). Track it the same way; do not silently extend it without telling the client.
- **White-label footer:** confirm the agency's preferred footer text/branding before the first report ships that month, and reuse it for every report in the subscription unless the agency changes it. Keep AppShield's own limits-and-independence language in the report body even when the footer is white-labeled; only the footer changes, not the findings-section disclaimers.
- **Alerts:** send deadline-calendar alerts for the agency's tracked apps/portfolio proactively (do not wait for the agency to ask), and log each alert sent in the ledger Notes field so there is a record of what was flagged and when.
- **Cancellation:** if the agency cancels, confirm the Stripe subscription is actually canceled (not just that invoicing stopped) and record the cancellation date and the last billing period covered in the ledger.
