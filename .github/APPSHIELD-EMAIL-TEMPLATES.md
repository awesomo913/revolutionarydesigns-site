# AppShield client email templates

Replace bracketed fields and verify every date, scope item, amount, and link before sending.

## Scope accepted and payment requested

**Subject:** `AppShield scope accepted — [scope ID] — payment by [date]`

Hi [name],

I can accept your AppShield founding pilot under scope `[scope ID]`:

- App: [app]
- Store: [store]
- Build: [build or build-ready condition]
- Locale: [locale]
- Primary role: [role]
- Agreed flows: [flows]
- Excluded: [exclusions]

The one-time pilot price is $99. The 24–48 hour delivery window begins only after Stripe confirms payment and I email `Intake complete` for a complete, usable intake.

Pay securely: https://buy.stripe.com/14A3cndzr207e2s9vNfAc00

Enter `[scope ID]` in the approved scope ID field. Review the service terms and privacy notice linked at checkout. Do not send files or credentials yet.

## Payment confirmed

**Subject:** `AppShield payment confirmed — [scope ID] — prepare intake`

Hi [name],

I matched the successful $99 Stripe payment to `[scope ID]` for [app] / [store].

Complete the non-sensitive intake summary: https://revolutionarydesigns.io/appshield/client-intake.html

Do not include credentials, secrets, payment data, customer records, or regulated personal data. After I match the summary, I will send the restricted folder and separate disposable-credential handoff instructions.

## Intake incomplete

**Subject:** `AppShield intake needs items — [scope ID]`

Hi [name],

I received the intake for `[scope ID]`, but the delivery clock has not started. Please provide or correct:

- [missing or unusable item]
- [missing or unusable item]

Use the previously confirmed restricted handoff. Do not email credentials or sensitive files.

## Intake complete

**Subject:** `AppShield intake complete — [scope ID] — report due [date/time]`

Hi [name],

Intake for `[scope ID]` is complete as of [time and time zone]. The 24–48 clock-hour review window starts now. I expect to deliver the report by [deadline].

Accepted scope: [short restatement]. Anything outside that scope will be marked Not Evaluated or handled as a separate scope.

## Report delivered

**Subject:** `AppShield report delivered — [scope ID] — [recommendation]`

Hi [name],

Attached are the PDF report and Markdown copy for `[scope ID]`.

Recommendation: [recommendation]

The written clarification window closes [date/time]. Your one focused recheck covers findings in this report and must be submitted by [date/time]. Reply in this thread with non-sensitive questions. Use the established secure handoff for updated builds or materials.

## Recheck complete

**Subject:** `AppShield recheck complete — [scope ID]`

Hi [name],

The focused recheck for `[scope ID]` is complete.

- [finding]: [Pass / Remaining issue / Unable to assess]
- [finding]: [result]

This closes the included recheck. The report remains a defined-scope readiness review, not an approval guarantee.

## Closeout and access removal

**Subject:** `AppShield closeout — revoke review access — [scope ID]`

Hi [name],

The review and recheck window for `[scope ID]` are closed. Please revoke the shared folder, TestFlight or internal-test access, and delete or rotate the disposable test account now.

Active working copies are scheduled for deletion by [date]. The final report, scope confirmation, payment record, and ordinary correspondence may be retained as service records under the published terms and privacy notice.
