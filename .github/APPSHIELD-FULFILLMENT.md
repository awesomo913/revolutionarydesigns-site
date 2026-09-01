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
