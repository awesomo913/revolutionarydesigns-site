export function phoneRender(screen='home',side='b',alt='Dayform proposed app screen'){return `<span class="phone-render phone-render-${side}"><img src="/assets/dayform-${screen}-ab.webp" alt="${alt}" width="1536" height="1024" loading="lazy" decoding="async"></span>`}
export function routeScreen(){return phoneRender('home','b','Dayform proposed home: reading focus, weekly rhythm, and meaningful habit progress.')}
export function listingA(){return `<div class="dayform-listing"><span class="dayform-store-label">STORE PREVIEW / FICTIONAL APP</span><strong>dayform</strong><h4>Small habits.<br>More intentional days.</h4><p>A habit tracker for your daily rhythm.</p>${phoneRender('home','a','Dayform as submitted: generic dashboard and obstructed Add habit button.')}<small>Example listing artwork · compare with the actual build</small></div>`}
export const reviewCases=[
  {
    "id": "screenshots",
    "number": "01",
    "label": "App experience",
    "title": "From a template to a reason to come back.",
    "aTitle": "Decoration competes with the task.",
    "bTitle": "One clear next step. A distinct identity.",
    "a": "<a class=\"phone-inspect\" href=\"/assets/dayform-home-ab.webp\" target=\"_blank\" rel=\"noopener\" aria-label=\"Enlarge App experience A and B phones\"><span class=\"phone-render phone-render-a\"><img src=\"/assets/dayform-home-ab.webp\" alt=\"Generic purple Dayform dashboard with emoji counters and an Android mascot over Add habit.\" width=\"1536\" height=\"1024\" loading=\"lazy\" decoding=\"async\"></span><span class=\"phone-enlarge\">Inspect both screens ↗</span></a>",
    "b": "<a class=\"phone-inspect\" href=\"/assets/dayform-home-ab.webp\" target=\"_blank\" rel=\"noopener\" aria-label=\"Enlarge App experience A and B phones\"><span class=\"phone-render phone-render-b\"><img src=\"/assets/dayform-home-ab.webp\" alt=\"Refined ivory and evergreen Dayform with a reading focus action, weekly rhythm, habit progress, and clear navigation.\" width=\"1536\" height=\"1024\" loading=\"lazy\" decoding=\"async\"></span><span class=\"phone-enlarge\">Inspect both screens ↗</span></a>",
    "aSummary": "Emoji stat cards all shout at once. The Android mascot sits over Add habit, putting decoration in the way of a useful action.",
    "bSummary": "An editorial identity, a focused reading session, meaningful progress, and controls with room to work. The same idea, made deliberate.",
    "impact": "A habit tracker should help someone take their next small step. This direction makes that purpose visible immediately.",
    "work": "In a real review, open Today on the supplied build, try Add habit, check the bottom controls at the agreed screen sizes, then trace the primary task. Separate reproducible obstruction from subjective design advice.",
    "observation": "This fictional Dayform screen gives four decorative counters equal emphasis and places an Android mascot over Add habit. The proposed screen prioritizes a reading session and separates the navigation from content.",
    "route": "Today → Add habit → return to Today → inspect bottom navigation and the next habit action.",
    "evidence": [
      "E-01 · generated A home screen: competing counters",
      "E-02 · generated A home screen: mascot overlaps Add habit",
      "E-03 · proposed B home screen: focus action, useful progress, clear navigation"
    ],
    "fixes": [
      "Remove the mascot from the controls and reserve system-navigation space.",
      "Prioritize one meaningful next action; make habit progress and scheduling explicit.",
      "Use a consistent type hierarchy, restrained palette, and coherent icons; verify the revised flow in the build."
    ],
    "checks": [
      "Add habit and navigation remain visible and tappable at agreed sizes.",
      "Begin focus opens the intended reading session and progress reflects actual state.",
      "Large text and system navigation do not cover actions; design choices remain identified as recommendations."
    ],
    "owner": "Developer / product designer",
    "limit": "Generated concept screens demonstrate a proposed direction, not a tested app or measured conversion result. A review provides correction guidance; a full redesign or implementation requires its own agreed scope.",
    "basis": "Control visibility and usability are quality concerns. The typography, palette, and icon direction are design recommendations; emojis alone are not a policy violation.",
    "source": "https://developer.android.com/docs/quality-guidelines/core-app-quality",
    "sourceLabel": "Android: Core app quality",
    "screen": "home"
  },
  {
    "id": "deletion",
    "number": "02",
    "label": "Account flow",
    "title": "Turn an account dead end into a clear exit.",
    "aTitle": "Sign out is the last available action.",
    "bTitle": "A clear exit, with room to make a decision.",
    "a": "<a class=\"phone-inspect\" href=\"/assets/dayform-account-ab.webp\" target=\"_blank\" rel=\"noopener\" aria-label=\"Enlarge Account flow A and B phones\"><span class=\"phone-render phone-render-a\"><img src=\"/assets/dayform-account-ab.webp\" alt=\"Generic Dayform account settings ending at Sign out, with Android decoration crowding controls.\" width=\"1536\" height=\"1024\" loading=\"lazy\" decoding=\"async\"></span><span class=\"phone-enlarge\">Inspect both screens ↗</span></a>",
    "b": "<a class=\"phone-inspect\" href=\"/assets/dayform-account-ab.webp\" target=\"_blank\" rel=\"noopener\" aria-label=\"Enlarge Account flow A and B phones\"><span class=\"phone-render phone-render-b\"><img src=\"/assets/dayform-account-ab.webp\" alt=\"Dayform deletion confirmation with affected data, deletion details, request and keep-account actions.\" width=\"1536\" height=\"1024\" loading=\"lazy\" decoding=\"async\"></span><span class=\"phone-enlarge\">Inspect both screens ↗</span></a>",
    "aSummary": "A generic profile ends at Sign out. There is no visible deletion entry, and the mascot crowds the bottom controls.",
    "bSummary": "The proposed confirmation names the affected information, points to deletion details, and separates Request deletion from Keep my account.",
    "impact": "Users can find the request and understand its purpose before acting.",
    "work": "In a real review, follow You → Account and Help & support, attempt to reach a deletion request, and inspect the supplied web deletion resource. Record the exact route and any missing evidence.",
    "observation": "In this fictional scenario, Dayform Account ends at Sign out. Help & support does not supply a deletion path, and the submission deletion URL is blank.",
    "route": "You → Account → Help & support; inspect the supplied deletion URL.",
    "evidence": [
      "E-01 · generated A Account screen: no deletion entry",
      "E-02 · fictional support-path and blank-URL scenario",
      "E-03 · proposed B confirmation: affected data, details, and distinct actions"
    ],
    "fixes": [
      "Add a prominent Delete account entry and a functioning request path.",
      "Explain affected data, actual timing, and applicable retention before confirmation.",
      "Publish the app-named web deletion resource and supply its link for the Google Play submission."
    ],
    "checks": [
      "Request path is reachable using the test account.",
      "Web request resource works without reinstalling the app.",
      "UI wording matches owner-supplied process details; unverified backend erasure stays marked unverified."
    ],
    "owner": "Developer / account-service owner",
    "limit": "B illustrates a proposed confirmation reached from a new Delete account entry. Actual timing, retained records, web access, and backend erasure require implementation evidence; a rendered screen does not establish them.",
    "basis": "For applicable Google Play apps with account creation, both an in-app deletion path and a web request resource are required.",
    "source": "https://support.google.com/googleplay/android-developer/answer/13327111",
    "sourceLabel": "Google Play: Account deletion",
    "screen": "account"
  },
  {
    "id": "privacy",
    "number": "03",
    "label": "Privacy choices",
    "title": "From a privacy slogan to understandable choices.",
    "aTitle": "A blanket promise. Unclear controls.",
    "bTitle": "Specific choices, explained where they matter.",
    "a": "<a class=\"phone-inspect\" href=\"/assets/dayform-privacy-ab.webp\" target=\"_blank\" rel=\"noopener\" aria-label=\"Enlarge Privacy choices A and B phones\"><span class=\"phone-render phone-render-a\"><img src=\"/assets/dayform-privacy-ab.webp\" alt=\"Generic privacy screen promising 100% private with unclear toggles and an obstructed save control.\" width=\"1536\" height=\"1024\" loading=\"lazy\" decoding=\"async\"></span><span class=\"phone-enlarge\">Inspect both screens ↗</span></a>",
    "b": "<a class=\"phone-inspect\" href=\"/assets/dayform-privacy-ab.webp\" target=\"_blank\" rel=\"noopener\" aria-label=\"Enlarge Privacy choices A and B phones\"><span class=\"phone-render phone-render-b\"><img src=\"/assets/dayform-privacy-ab.webp\" alt=\"Refined Dayform privacy screen separating required account data, optional analytics and crash reports, and Save preferences.\" width=\"1536\" height=\"1024\" loading=\"lazy\" decoding=\"async\"></span><span class=\"phone-enlarge\">Inspect both screens ↗</span></a>",
    "aSummary": "“100% private” sits above vague Privacy mode and enabled Smart insights. The screen never explains what those controls change.",
    "bSummary": "Required account data is distinguished from optional analytics and crash reports. Each choice has a purpose, and Save preferences has its own clear space.",
    "impact": "People can understand what is required, what is optional, and where to manage their data. The implementation must support every promise.",
    "work": "In a real review, compare the privacy wording and draft declaration with the SDK inventory and supplied test events. Exercise each toggle, relaunch the app, and request evidence for facts the client cannot establish.",
    "observation": "The fictional A screen claims 100% private while Smart insights is enabled. The scenario pairs a No data collected draft with an illustrative habit_completed event and identifier demo-7f2a sent to analytics.example.",
    "route": "Privacy → inspect choices → compare declaration and SDK inventory → change preference → relaunch → inspect supplied event evidence.",
    "evidence": [
      "E-01 · generated A privacy screen: blanket claim and vague controls",
      "E-02 · fictional declaration and SDK inventory",
      "E-03 · illustrative habit_completed event, demo-7f2a → analytics.example",
      "E-04 · proposed B privacy choices; behavior not yet verified"
    ],
    "fixes": [
      "Replace blanket claims with accurate purposes and a clear distinction between required and optional processing.",
      "Implement preferences that persist and govern actual collection; map SDK behavior, recipient roles, retention, and sharing to evidence.",
      "Align the declaration, policy, and in-app explanation. Keep unresolved data-handling questions open."
    ],
    "checks": [
      "Optional collection stays off before consent and after relaunch when disabled, supported by behavior evidence.",
      "Every revised declaration answer cites evidence, including third-party components.",
      "Owner confirms purposes and handling; backend unknowns remain explicitly unverified."
    ],
    "owner": "Developer / data-handling owner",
    "limit": "B is a proposed interface, not a completed Data safety declaration or privacy audit. OFF toggles and explanatory copy do not prove collection behavior or server-side handling.",
    "basis": "Google Play asks developers to account for data handled by the app and included third-party components.",
    "source": "https://support.google.com/googleplay/android-developer/answer/10787469",
    "sourceLabel": "Google Play: Data safety",
    "screen": "privacy"
  }
];
