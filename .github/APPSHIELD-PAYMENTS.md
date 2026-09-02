# AppShield pilot payment runbook

This runbook covers the five-slot, $99 AppShield founding pilot. It intentionally uses a scope-first sale: approve the app and review scope before sending the payment link.

## Stripe objects

- Product: `AppShield — Single-store human preflight pilot`
- Description: `One app, one store, one submitted build, one primary locale and standard user role, up to 12 agreed flows, a source-linked report, one clarification round, and one focused recheck.`
- Price: one-time `99.00 USD`
- Quantity: fixed at `1`
- Payment Link completed-session limit: `5`
- Live Payment Link: `https://buy.stripe.com/14A3cndzr207e2s9vNfAc00`
- Payment Link ID: `plink_1UAy6s0tqwapy3DIBBkAM62E`
- Adjustable quantity: off
- Promotion codes: off for the founding pilot
- Customer email: required
- Customer name: required
- Billing address: automatic / only as required by the selected payment method
- Custom fields:
  1. `App name` — required text
  2. `Target store` — required dropdown: `Apple App Store`, `Google Play`
  3. `Approved scope ID` — required text copied from the acceptance email
- Terms acceptance: required, linking to `https://revolutionarydesigns.io/appshield/service-terms.html`
- Privacy policy: `https://revolutionarydesigns.io/appshield/privacy.html`
- After-payment redirect: `https://revolutionarydesigns.io/appshield/payment-complete.html`
- Paid intake summary: `https://revolutionarydesigns.io/appshield/client-intake.html`

## Payment methods

Use Stripe Dynamic payment methods instead of hard-coding method types.

The live link currently exposes eligible dynamic methods including:

- Cards
- Apple Pay
- Google Pay
- Link
- Link Instant Bank Payments
- Cash App Pay
- Klarna
- Affirm
- Amazon Pay

Leave ACH Direct Debit off for the pilot. ACH can take several business days and takes precedence over Link Instant Bank Payments when both are eligible. Do not start review work from a redirect when an asynchronous payment method is pending.

Stripe-processed PayPal is not currently available to a US-based Stripe business through Payment Links. Do not add a separate PayPal rail for the five-slot pilot; it would split receipts, refunds, and availability tracking.

## Account settings

- Public support URL, privacy URL, and service-terms URL are configured.
- Checkout displays the legal links and requires affirmative terms acceptance.
- Add AppShield branding and the shield mark.
- Enable customer emails for successful payments and refunds.
- Confirm the public statement descriptor.
- Confirm the bank payout account and two-factor authentication.
- Keep secret keys and webhook secrets out of this static repository.
- Do not enable Stripe Tax or choose a product tax code until the business's registrations and service tax treatment are confirmed. If tax will be added, update public copy to `$99 plus applicable tax` before activating the link.

## Sale and fulfillment sequence

1. Customer submits the public review request. No credentials or app files are accepted at this stage.
2. Confirm fit, availability, exact store/build/locale/role/flow scope, and a unique approved scope ID.
3. Send the active Stripe Payment Link in the acceptance email.
4. Confirm successful payment in Stripe. A success-page visit alone is not proof of payment.
5. Customer completes the non-sensitive paid intake summary. Do not accept files or credentials through that public form.
6. Send the restricted intake-folder and disposable-credential handoff instructions.
7. Check intake completeness and email `Intake complete`. The 24–48 clock-hour delivery window begins only then.
8. Deliver the report and record the clarification/recheck deadline.
9. Delete active working copies under the published retention policy and ask the client to revoke access.

For every accepted pilot, maintain a simple service ledger with the request date, approved scope ID, acceptance and payment deadlines, payment confirmation, `Intake complete`, `Review started`, report delivery, recheck deadline, recheck completion, and working-copy deletion due date. Record completion of each deletion and access-revocation reminder.

## Refund handling

- Full refund if AppShield declines an already-paid scope or does not begin the accepted review.
- After work begins, apply the refund terms shown in the accepted service terms and preserve the written scope record.
- Refund only through the original Stripe payment, never through a different rail.
- Keep the Stripe receipt, refund record, scope acceptance, and customer correspondence together.

## Service ladder (added 2026-09-02; all seven Payment Links created live 2026-09-02)

The five-slot $99 founding pilot above stays as its own Stripe object and its own Payment Link. It does not change when the standard/dual-store price takes over after the founding slots end or Oct 31 2026, whichever comes first (see AppShield build spec §Products). Each row below is a separate Stripe Product with its own Price and its own Payment Link. Scope-first still applies: no link goes out until Jacob confirms scope by email and sends it.

Shared settings across every row in this ladder unless a row says otherwise:

- Quantity: fixed at `1`
- Customer email: required
- Customer name: required
- Billing address: automatic / only as required by the selected payment method
- Terms acceptance: required, linking to `https://revolutionarydesigns.io/appshield/service-terms.html`
- Privacy policy: `https://revolutionarydesigns.io/appshield/privacy.html`
- After-payment redirect: `https://revolutionarydesigns.io/appshield/payment-complete.html`
- Paid intake summary: `https://revolutionarydesigns.io/appshield/client-intake.html`
- Custom fields (reuse the existing three from the founding pilot on every link):
  1. `App name` — required text
  2. `Target store` — required dropdown: `Apple App Store`, `Google Play`
  3. `Approved scope ID` — required text copied from the acceptance email
- Tax/receipt settings: do not enable Stripe Tax or choose a product tax code until the business's registrations and service tax treatment are confirmed, same as the founding pilot. If tax is added later, update the public price copy to say "plus applicable tax" before activating any link in this ladder. Enable customer emails for successful payments and refunds on every link, same as the founding pilot.
- Promotion codes: off, same as the founding pilot.
- Completed-session limit: none, unless a row says otherwise. Capacity for these tiers is managed operationally (the capacity note in the acceptance email and the service ledger), not by capping Stripe sessions, because these are not scarce founding slots.

### 1. Preflight — standard

- Product: `AppShield — Single-store human preflight (standard)`
- Description: `One app, one store, one submitted build, one primary locale and standard user role, up to 12 agreed flows, a source-linked report, one clarification round, and one focused recheck.`
- Price: one-time `149.00 USD`
- Statement descriptor suggestion: `APPSHIELD PREFLIGHT`
- Completed-session limit: none (the founding-only 5-session cap stays on the $99 link above; this is the ongoing rate once founding slots are gone)
- Live Payment Link: `https://buy.stripe.com/7sYeV5brjeMT2jKbDVfAc01`
- Payment Link ID: `plink_1UBJd10tqwapy3DIoY2KbJG2`

### 2. Preflight — dual-store

- Product: `AppShield — Dual-store human preflight`
- Description: `One app, both Apple App Store and Google Play, one submitted build per store, one primary locale and standard user role per store, up to 12 agreed flows per store, a source-linked report covering both stores, one clarification round, and one focused recheck per store.`
- Price: one-time `249.00 USD`
- Statement descriptor suggestion: `APPSHIELD DUAL`
- Completed-session limit: none
- Live Payment Link: `https://buy.stripe.com/7sY5kvgLD48faQg0ZhfAc02`
- Payment Link ID: `plink_1UBJgx0tqwapy3DIO5mDzxlj`

### 3. Android Developer Verification & Account Concierge

- Product: `AppShield — Android Developer Verification & Account Concierge`
- Description: `Account-type decision (Full Distribution $25 fee vs free Limited Distribution up to 20 devices), a D-U-N-S walkthrough for organizations, a document and prep checklist, a 45-minute screen-share, written next-steps, and follow-up until Google confirms or 30 days, whichever comes first.`
- Price: one-time `129.00 USD`
- Statement descriptor suggestion: `APPSHIELD VERIFY`
- Completed-session limit: none
- Live Payment Link: `https://buy.stripe.com/6oU4grdzrawDbUk9vNfAc03`
- Payment Link ID: `plink_1UBJkB0tqwapy3DIlZbrdd1N`
- Note: this service never touches credentials or accounts on the client's behalf; see the honesty line in the build spec and repeat it in the acceptance email.

### 4. Launch Package (Preflight + Closed Testing)

- Product: `AppShield — Launch Package (Preflight + Closed Testing)`
- Description: `The single-store preflight plus closed-testing cohort coordination through the developer community exchange (real developers, real devices, 12+ opted in, tracked daily for 14 days, test-back required), plus a production-access application review before the client applies.`
- Price: one-time `149.00 USD`
- Statement descriptor suggestion: `APPSHIELD LAUNCH`
- Completed-session limit: none
- Live Payment Link: `https://buy.stripe.com/7sY3cn9jbbAHe2s4btfAc04`
- Payment Link ID: `plink_1UBJox0tqwapy3DIpN3lZHEW`
- Note: no purchased or fake testers, ever. Google decides production access; this service does not guarantee it.

### 5. Rejection & Production-Access Audit

- Product: `AppShield — Rejection & Production-Access Audit`
- Description: `For a rejected update, a "more testing required" production-access denial, or a policy enforcement action: a full audit against the cited policy, a written appeal-support brief (facts, citations, remediation log), a resubmission plan, and one follow-up round.`
- Price: one-time `199.00 USD`
- Statement descriptor suggestion: `APPSHIELD AUDIT`
- Completed-session limit: none
- Live Payment Link: `https://buy.stripe.com/cNi7sDcvngV13nOgYffAc05`
- Payment Link ID: `plink_1UBJs20tqwapy3DICPruKa7b`
- Note: no appeal that misstates facts, and no help evading enforcement. No outcome guarantee. Appeals must be filed within 180 days of a termination (since Jan 28 2026).

### 6. Agency Release Desk (monthly)

- Product: `AppShield — Agency Release Desk (monthly)`
- Description: `Up to 3 preflights per month, 48-hour turnaround, white-label report footer, deadline-calendar alerts for the agency's portfolio, and a shared email/Slack channel.`
- Price: recurring `399.00 USD` / month, billing interval `month`
- Statement descriptor suggestion: `APPSHIELD AGENCY`
- Completed-session limit: none (subscription, not a capped one-time link)
- Live Payment Link: `https://buy.stripe.com/14A5kvdzr6gn8I823lfAc06`
- Payment Link ID: `plink_1UBJvR0tqwapy3DIpfxanzEI`
- Custom fields: same three as every other link. Treat `App name` as "primary app / portfolio name" for agency clients with more than one app; capture the rest of the portfolio on the scope call, not in the Stripe field.
- Extra preflight add-on (beyond the included 3/month): separate Product `AppShield — Agency extra preflight`, one-time `79.00 USD`, billed as a manual invoice item or a second one-time Payment Link, not folded into the subscription price. Live Payment Link: `https://buy.stripe.com/bJecMX52V0W3aQgcHZfAc07`, Payment Link ID: `plink_1UBJyT0tqwapy3DIPNEkjXUX` (same three custom fields, terms acceptance, and redirect as the rest of the ladder). Do not create this as a Stripe metered/usage price for the pilot phase; keep it a manual add so scope confirmation happens before every extra preflight, same scope-first rule as everything else.
- Note: scope call first, same as the build spec says. This is a subscription; confirm cancellation terms are stated in the acceptance email and that Jacob can cancel the Stripe subscription directly (not just stop invoicing) if the agency relationship ends.

### Stripe API alternative

Once a restricted Stripe API key exists for this purpose (create it scoped to `products:write`, `prices:write`, `payment_links:write` only, and never commit it to this repo), the six links above can be scripted instead of built by hand in the Dashboard. Example for the standard preflight (repeat with each row's values):

```bash
# 1. Create the product
curl https://api.stripe.com/v1/products \
  -u "<RESTRICTED_KEY>:" \
  -d name="AppShield — Single-store human preflight (standard)" \
  -d description="One app, one store, one submitted build, one primary locale and standard user role, up to 12 agreed flows, a source-linked report, one clarification round, and one focused recheck."

# 2. Create the price (use the product id returned above)
curl https://api.stripe.com/v1/prices \
  -u "<RESTRICTED_KEY>:" \
  -d product="<PRODUCT_ID>" \
  -d unit_amount=14900 \
  -d currency=usd

# For the agency subscription price, add recurring params:
curl https://api.stripe.com/v1/prices \
  -u "<RESTRICTED_KEY>:" \
  -d product="<AGENCY_PRODUCT_ID>" \
  -d unit_amount=39900 \
  -d currency=usd \
  -d "recurring[interval]=month"

# 3. Create the Payment Link (use the price id returned above)
curl https://api.stripe.com/v1/payment_links \
  -u "<RESTRICTED_KEY>:" \
  -d "line_items[0][price]=<PRICE_ID>" \
  -d "line_items[0][quantity]=1" \
  -d "custom_fields[0][key]=app_name" \
  -d "custom_fields[0][label][type]=custom" \
  -d "custom_fields[0][label][custom]=App name" \
  -d "custom_fields[0][type]=text" \
  -d "custom_fields[1][key]=target_store" \
  -d "custom_fields[1][label][type]=custom" \
  -d "custom_fields[1][label][custom]=Target store" \
  -d "custom_fields[1][type]=dropdown" \
  -d "custom_fields[1][dropdown][options][0][label]=Apple App Store" \
  -d "custom_fields[1][dropdown][options][0][value]=apple" \
  -d "custom_fields[1][dropdown][options][1][label]=Google Play" \
  -d "custom_fields[1][dropdown][options][1][value]=google_play" \
  -d "custom_fields[2][key]=approved_scope_id" \
  -d "custom_fields[2][label][type]=custom" \
  -d "custom_fields[2][label][custom]=Approved scope ID" \
  -d "custom_fields[2][type]=text" \
  -d "after_completion[type]=redirect" \
  -d "after_completion[redirect][url]=https://revolutionarydesigns.io/appshield/payment-complete.html"
```

Amounts above are in the smallest currency unit (cents): `14900` = $149.00, `24900` = $249.00, `12900` = $129.00, `19900` = $199.00, `39900` = $399.00/month, `7900` = $79.00. Do not paste a real key into this file or into chat; use an env var or a secret manager reference (see Key security link below), and never widen the key's scope beyond products/prices/payment_links.

## Official Stripe references

- Payment Links: https://docs.stripe.com/payment-links
- Payment Link customization and completed-session limits: https://docs.stripe.com/payment-links/customize
- Dynamic payment methods: https://docs.stripe.com/payments/payment-methods/dynamic-payment-methods
- Post-payment redirects: https://docs.stripe.com/payment-links/post-payment
- Fulfillment and asynchronous methods: https://docs.stripe.com/checkout/fulfillment?payment-ui=stripe-hosted
- Receipts: https://docs.stripe.com/receipts
- Refunds: https://docs.stripe.com/refunds
- Key security: https://docs.stripe.com/keys-best-practices
