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

## Official Stripe references

- Payment Links: https://docs.stripe.com/payment-links
- Payment Link customization and completed-session limits: https://docs.stripe.com/payment-links/customize
- Dynamic payment methods: https://docs.stripe.com/payments/payment-methods/dynamic-payment-methods
- Post-payment redirects: https://docs.stripe.com/payment-links/post-payment
- Fulfillment and asynchronous methods: https://docs.stripe.com/checkout/fulfillment?payment-ui=stripe-hosted
- Receipts: https://docs.stripe.com/receipts
- Refunds: https://docs.stripe.com/refunds
- Key security: https://docs.stripe.com/keys-best-practices
