/* Revolutionary Designs — website traffic analytics (PostHog).
 *
 * Single source of truth for the tracking config: every page just loads
 * this one file, so the token/settings live in exactly one place.
 *
 * Added 2026-08-23. Project: "Revo" org, Default project (id 457849), US cloud.
 * The phc_ key below is a PUBLIC ingestion key — safe to ship in client HTML.
 *
 * PRIVACY: runs COOKIELESS (persistence:'memory') so no consent banner is
 * required, and session replay is OFF by default. Trade-off: pageviews,
 * referrers, top pages, devices and geo are accurate; unique-visitor and
 * session stitching are approximate (each page load looks like a fresh
 * visitor). To switch to precise unique visitors + session replay, change:
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
