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

## Scope accepted and payment requested — service ladder variants (added 2026-09-02)

Use the same structure as the founding-pilot "Scope accepted and payment requested" template above. Swap the price, the payment link, and the bracketed scope details for the service actually sold. Every variant keeps: no payment until scope is agreed, the exact scope list, the delivery-trigger sentence, and the payment link with the "enter your scope ID" instruction.

### Preflight — standard ($149) or dual-store ($249)

**Subject:** `AppShield scope accepted — [scope ID] — payment by [date]`

Hi [name],

I can accept your AppShield preflight under scope `[scope ID]`:

- App: [app]
- Store(s): [store or both stores]
- Build: [build or build-ready condition]
- Locale: [locale]
- Primary role: [role]
- Agreed flows: [flows]
- Excluded: [exclusions]

The one-time price is $[149 for one store / 249 for both stores]. The 24-48 hour delivery window begins only after Stripe confirms payment and I email `Intake complete` for a complete, usable intake.

Pay securely: [payment link]

Enter `[scope ID]` in the approved scope ID field. Review the service terms and privacy notice linked at checkout. Do not send files or credentials yet.

### Verification concierge ($129)

**Subject:** `AppShield verification concierge accepted — [scope ID] — payment by [date]`

Hi [name],

I can accept your Android Developer Verification & Account Concierge engagement under scope `[scope ID]`:

- Store/account: [store and developer account email]
- Account type under review: [Full Distribution / Limited Distribution / undecided, to be confirmed on the call]
- Individual or organization account: [type]
- Call time: [date/time]
- Excluded: [exclusions, for example we do not log in as you and do not hold your ID or credentials]

The one-time price is $129 and includes the 45-minute decision call, the D-U-N-S walkthrough if you are an organization, a document/prep checklist, written next-steps, and follow-up until Google confirms or 30 days, whichever comes first.

Pay securely: [payment link]

Enter `[scope ID]` in the approved scope ID field. We never log in as you, never hold your ID or credentials, and never create or verify accounts on your behalf. Review the service terms and privacy notice linked at checkout.

### Launch package ($149)

**Subject:** `AppShield launch package accepted — [scope ID] — payment by [date]`

Hi [name],

I can accept your Launch Package (Preflight + Closed Testing) under scope `[scope ID]`:

- App: [app]
- Store: [store]
- Build: [build or build-ready condition]
- Locale: [locale]
- Primary role: [role]
- Agreed flows: [flows]
- Closed-testing cohort: coordinated through our developer community exchange, real developers and real devices only, tracked daily for 14 days; you test back for others in the exchange
- Excluded: [exclusions]

The one-time price is $149 and includes the single-store preflight, cohort coordination, and a production-access application review before you apply. Google decides production access; we do not guarantee it.

Pay securely: [payment link]

Enter `[scope ID]` in the approved scope ID field. Review the service terms and privacy notice linked at checkout. Do not send files or credentials yet.

### Rejection & production-access audit ($199)

**Subject:** `AppShield rejection audit accepted — [scope ID] — payment by [date]`

Hi [name],

I can accept your Rejection & Production-Access Audit under scope `[scope ID]`:

- App: [app]
- Store: [store]
- Rejection / denial / enforcement notice date: [date]
- Notice type: [rejection / "more testing required" denial / policy enforcement]
- Excluded: [exclusions]

The one-time price is $199 and includes a full audit against the cited policy, a written appeal-support brief, a resubmission plan, and one follow-up round. This does not include writing an appeal that misstates facts or helps evade enforcement, and there is no outcome guarantee. If your termination is more than 180 days old, appeals are no longer accepted by Google and I will say so before starting paid work.

Pay securely: [payment link]

Enter `[scope ID]` in the approved scope ID field. Review the service terms and privacy notice linked at checkout.

### Agency Release Desk ($399/month)

**Subject:** `AppShield Agency Release Desk accepted — [scope ID] — payment by [date]`

Hi [name],

I can accept your agency onto the Release Desk under scope `[scope ID]`:

- Agency / primary app or portfolio name: [name]
- Apps in scope this month (up to 3 included): [apps]
- Extra preflights beyond 3/month: billed separately at $79 each, scope confirmed the same way as everything else
- 48-hour turnaround starting at `Intake complete` for each preflight
- White-label footer text: [confirm or attach]
- Alert contact for the deadline calendar: [contact]

The subscription is $399/month, cancel anytime. Confirm cancellation with me directly; stopping invoicing alone does not cancel the Stripe subscription.

Subscribe securely: [payment link]

Enter `[scope ID]` in the approved scope ID field. Review the service terms and privacy notice linked at checkout.

## Capacity: dated start (added 2026-09-02)

Use this when the preflight queue is full (more than 3 reviews in flight) and a new buyer needs a later start date instead of the standard 24-48 hour window. Send this before or instead of the standard "Scope accepted" email once you know the delay.

**Subject:** `AppShield scope accepted — [scope ID] — start date [date] (queue is full)`

Hi [name],

I can accept your AppShield engagement under scope `[scope ID]` with the same scope terms as usual:

- App: [app]
- Store: [store]
- Build: [build or build-ready condition]
- Locale: [locale]
- Primary role: [role]
- Agreed flows: [flows]
- Excluded: [exclusions]

I currently have 3 reviews in flight, which is my working limit so each one gets full attention. Your review will start on [dated start], and the standard 24-48 clock-hour delivery window begins from that start date once intake is complete, not from today. If that date does not work for you, let me know and I will not send the payment link until we agree on a start date that does.

If you would rather wait for an open slot instead of a fixed dated start, say so and I will hold this scope without a payment link until one opens.

Pay securely (only after you confirm the dated start works): [payment link]

Enter `[scope ID]` in the approved scope ID field. Review the service terms and privacy notice linked at checkout. Do not send files or credentials yet.

## Closeout and access removal

**Subject:** `AppShield closeout — revoke review access — [scope ID]`

Hi [name],

The review and recheck window for `[scope ID]` are closed. Please revoke the shared folder, TestFlight or internal-test access, and delete or rotate the disposable test account now.

Active working copies are scheduled for deletion by [date]. The final report, scope confirmation, payment record, and ordinary correspondence may be retained as service records under the published terms and privacy notice.
