/* Revolutionary Designs — website traffic analytics (PostHog).
 *
 * Single source of truth for the tracking config: every page just loads
 * this one file, so the token/settings live in exactly one place.
 *
 * Added 2026-08-23. Project: "Revo" org, Default project (id 457849), US cloud.
 * The phc_ key below is a PUBLIC ingestion key — safe to ship in client HTML.
 *
 * PRIVACY: uses memory-only persistence, so the PostHog identifier is not
 * intentionally persisted to cookies or local storage across page loads.
 * Session replay is OFF. Trade-off: pageviews, referrers, top pages, devices
 * and geo are useful; unique-visitor and session stitching are approximate
 * because each page load looks like a fresh visitor. To switch to persistent
 * identifiers and session replay, change:
 *     persistence: 'localStorage+cookie'
 *     disable_session_recording: false
 * (and add a cookie/consent notice if your audience needs one).
 */
(function () {
  var s = document.createElement('script');
  s.src = 'https://us-assets.i.posthog.com/static/array.js';
  s.async = true;
  s.crossOrigin = 'anonymous';
  s.onload = function () {
    if (!(window.posthog && window.posthog.init)) return;
    window.posthog.init('phc_rEQ2ZQWKNTZTUcB3rCUaNtbiCtWqhrMZiDXVhJU6UzoF', {
      api_host: 'https://us.i.posthog.com',
      ui_host: 'https://us.posthog.com',
      persistence: 'memory',           // cookieless -> no consent banner
      autocapture: true,               // pageviews + clicks, no per-page code
      capture_pageview: true,
      capture_pageleave: true,
      disable_session_recording: true  // replays off by default (privacy)
    });
  };
  s.onerror = function () {
    /* analytics is best-effort: never let a blocked/failed tracker
       affect the page. Silently give up. */
  };
  document.head.appendChild(s);
})();
