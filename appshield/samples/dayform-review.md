# AppShield / Dayform sample review

Fictional scenario and generated concept screens. No real build tested or customer result claimed.

## 01 / App experience: From a template to a reason to come back.

Observation: This fictional Dayform screen gives four decorative counters equal emphasis and places an Android mascot over Add habit. The proposed screen prioritizes a reading session and separates the navigation from content.

Work: In a real review, open Today on the supplied build, try Add habit, check the bottom controls at the agreed screen sizes, then trace the primary task. Separate reproducible obstruction from subjective design advice.

Route: Today → Add habit → return to Today → inspect bottom navigation and the next habit action.

Evidence:
- E-01 · generated A home screen: competing counters
- E-02 · generated A home screen: mascot overlaps Add habit
- E-03 · proposed B home screen: focus action, useful progress, clear navigation

Corrections:
- Remove the mascot from the controls and reserve system-navigation space.
- Prioritize one meaningful next action; make habit progress and scheduling explicit.
- Use a consistent type hierarchy, restrained palette, and coherent icons; verify the revised flow in the build.

Acceptance checks:
- Add habit and navigation remain visible and tappable at agreed sizes.
- Begin focus opens the intended reading session and progress reflects actual state.
- Large text and system navigation do not cover actions; design choices remain identified as recommendations.

Owner: Developer / product designer

Basis: Control visibility and usability are quality concerns. The typography, palette, and icon direction are design recommendations; emojis alone are not a policy violation.

Source: [Android: Core app quality](https://developer.android.com/docs/quality-guidelines/core-app-quality)

Boundary: Generated concept screens demonstrate a proposed direction, not a tested app or measured conversion result. A review provides correction guidance; a full redesign or implementation requires its own agreed scope.

Status: Awaiting implementation / not rechecked.

## 02 / Account flow: Turn an account dead end into a clear exit.

Observation: In this fictional scenario, Dayform Account ends at Sign out. Help & support does not supply a deletion path, and the submission deletion URL is blank.

Work: In a real review, follow You → Account and Help & support, attempt to reach a deletion request, and inspect the supplied web deletion resource. Record the exact route and any missing evidence.

Route: You → Account → Help & support; inspect the supplied deletion URL.

Evidence:
- E-01 · generated A Account screen: no deletion entry
- E-02 · fictional support-path and blank-URL scenario
- E-03 · proposed B confirmation: affected data, details, and distinct actions

Corrections:
- Add a prominent Delete account entry and a functioning request path.
- Explain affected data, actual timing, and applicable retention before confirmation.
- Publish the app-named web deletion resource and supply its link for the Google Play submission.

Acceptance checks:
- Request path is reachable using the test account.
- Web request resource works without reinstalling the app.
- UI wording matches owner-supplied process details; unverified backend erasure stays marked unverified.

Owner: Developer / account-service owner

Basis: For applicable Google Play apps with account creation, both an in-app deletion path and a web request resource are required.

Source: [Google Play: Account deletion](https://support.google.com/googleplay/android-developer/answer/13327111)

Boundary: B illustrates a proposed confirmation reached from a new Delete account entry. Actual timing, retained records, web access, and backend erasure require implementation evidence; a rendered screen does not establish them.

Status: Awaiting implementation / not rechecked.

## 03 / Privacy choices: From a privacy slogan to understandable choices.

Observation: The fictional A screen claims 100% private while Smart insights is enabled. The scenario pairs a No data collected draft with an illustrative habit_completed event and identifier demo-7f2a sent to analytics.example.

Work: In a real review, compare the privacy wording and draft declaration with the SDK inventory and supplied test events. Exercise each toggle, relaunch the app, and request evidence for facts the client cannot establish.

Route: Privacy → inspect choices → compare declaration and SDK inventory → change preference → relaunch → inspect supplied event evidence.

Evidence:
- E-01 · generated A privacy screen: blanket claim and vague controls
- E-02 · fictional declaration and SDK inventory
- E-03 · illustrative habit_completed event, demo-7f2a → analytics.example
- E-04 · proposed B privacy choices; behavior not yet verified

Corrections:
- Replace blanket claims with accurate purposes and a clear distinction between required and optional processing.
- Implement preferences that persist and govern actual collection; map SDK behavior, recipient roles, retention, and sharing to evidence.
- Align the declaration, policy, and in-app explanation. Keep unresolved data-handling questions open.

Acceptance checks:
- Optional collection stays off before consent and after relaunch when disabled, supported by behavior evidence.
- Every revised declaration answer cites evidence, including third-party components.
- Owner confirms purposes and handling; backend unknowns remain explicitly unverified.

Owner: Developer / data-handling owner

Basis: Google Play asks developers to account for data handled by the app and included third-party components.

Source: [Google Play: Data safety](https://support.google.com/googleplay/android-developer/answer/10787469)

Boundary: B is a proposed interface, not a completed Data safety declaration or privacy audit. OFF toggles and explanatory copy do not prove collection behavior or server-side handling.

Status: Awaiting implementation / not rechecked.
