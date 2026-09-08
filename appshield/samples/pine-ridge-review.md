# AppShield / Pine Ridge Trails

FICTIONAL WORKED EXAMPLE. No client results, actual build execution, implemented changes, or successful retests are claimed.

## Scope and recommendation

Illustrated build: 1.8 (42). Three example surfaces: listing, account path, declaration. Policy context: Google Play. Official sources checked September 7, 2026.

Example recommendation: FIX BEFORE SUBMISSION. All corrections await implementation and recheck evidence.

## Finding 01: Make the promise match the product.

### Recorded observation (fictional)
In this fictional build 1.8 (42), Trails opens Sunset Loop. The supplied discovery screenshot cannot be reproduced in that inspected path.

### Work behind the finding
Open the exact build with the supplied account, navigate to Trails, record the reachable screen, and compare it with listing image 02.

### Reproduction path
Sign in → Trails → Sunset Loop; compare with listing image 02.

### Evidence references
- E-01 · supplied listing image 02
- E-02 · build 1.8 (42), Trails screen

### Correction plan
1. Replace image 02 with a capture from the submission build.
2. Describe the saved route, distance, elevation, and difficulty shown.
3. Compare the entire final screenshot sequence with the same build.

### Acceptance checks
- [ ] Image and caption match the current screen.
- [ ] Reviewer access reaches the pictured flow.
- [ ] No discovery claim remains without supporting behavior.

Implementation owner: Developer / listing owner

Recheck status: Awaiting implementation / not rechecked.

### Source and limits
Store listings must accurately represent the app. The visual treatment shown here is a design recommendation.
Google Play: Deceptive behavior: https://support.google.com/googleplay/android-developer/answer/9888077

This illustrates a listing correction. AppShield recommends the changes; the customer implements them. No new app feature or store approval is implied.

## Finding 02: Turn an account dead end into a clear exit.

### Recorded observation (fictional)
The fictional Account screen ends at Sign out. Help & support is generic, and the supplied deletion-link field is blank.

### Work behind the finding
Create or enter the test account, inspect Account, follow Help & support, and record the missing request path and the supplied deletion-link field.

### Reproduction path
Profile → Account → Help & support; inspect supplied deletion URL.

### Evidence references
- E-01 · Account screen
- E-02 · Help & support destination
- E-03 · deletion-link field, blank

### Correction plan
1. Add a prominent Delete account entry and a functioning request path.
2. Explain affected data, actual timing, and applicable retention before confirmation.
3. Publish the app-named web deletion resource and supply its link for the Google Play submission.

### Acceptance checks
- [ ] Request path is reachable using the test account.
- [ ] Web request resource works without reinstalling the app.
- [ ] UI wording matches owner-supplied process details; unverified backend erasure stays marked unverified.

Implementation owner: Developer / account-service owner

Recheck status: Awaiting implementation / not rechecked.

### Source and limits
For applicable Google Play apps with account creation, both an in-app deletion path and a web request resource are required.
Google Play: Account deletion: https://support.google.com/googleplay/android-developer/answer/13327111

The illustrated screens are a proposed interface. A request acknowledgment does not prove backend erasure; that remains outside this review without separate evidence.

## Finding 03: Replace a blanket answer with traceable evidence.

### Recorded observation (fictional)
The fictional draft says No data collected. E-03 shows trail_opened and demo-7f2a sent to analytics.example; the inventory includes an analytics component.

### Work behind the finding
Compare the declaration with the supplied SDK inventory and test event. Record the contradiction, then ask the implementation owner for facts the client evidence cannot establish.

### Reproduction path
Declaration draft → SDK inventory → supplied test event → owner questions.

### Evidence references
- E-01 · declaration draft
- E-02 · SDK inventory
- E-03 · illustrative test event

### Correction plan
1. List the observed identifiers, activity, and included SDK.
2. Obtain evidence for collection purposes, recipient roles, sharing, retention, and optionality.
3. Update declaration and privacy information together; leave unresolved answers explicitly open.

### Acceptance checks
- [ ] Each revised answer cites supporting evidence.
- [ ] The third-party component is included in the assessment.
- [ ] Owner questions are resolved or recorded as not evaluated; no unknown is counted as a pass.

Implementation owner: Developer / data-handling owner

Recheck status: Awaiting implementation / not rechecked.

### Source and limits
Google Play asks developers to account for data handled by the app and included third-party components.
Google Play: Data safety: https://support.google.com/googleplay/android-developer/answer/10787469

The proposed register is not a completed declaration or full privacy audit. Client evidence alone does not establish server-side handling.

## Use in a real engagement
Replace illustrative observations with actual evidence. Record the exact build, test environment, access and routes, source dates, severity rationale, implementation owner, and limitations. No evidence is a reason to mark an item Not Evaluated, never a pass. AppShield recommends corrections; the customer implements them. Store approval is not guaranteed.
