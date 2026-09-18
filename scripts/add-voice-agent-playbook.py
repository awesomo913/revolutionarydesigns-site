#!/usr/bin/env python3
"""Add the hidden "Voice agent" upsell section to every prospect playbook overlay.

The playbook overlay is PRIVATE - it opens only from the amber triangle in the top-left
corner (#pbk-tri) behind a password prompt, or the ` key, and is never linked. This script
adds two collapsibles to that panel:

  1. per-prospect - why THIS trade would buy a 24/7 phone answerer, the ask, their money
     math, and (the panel being private) the cost and sale price so margin is visible
     mid-pitch;
  2. the whole playbook - the general kit: who to target, the five ways to sell it,
     pricing rules, the one qualifying question, the TCPA red line, and the build path.

Pricing is a single source of truth here (PRICE_* below). Re-running is safe: files that
already carry the section are skipped, so this can be re-run after the price changes only
if --force is passed (which strips every generation of the block first).

Usage:
    python scripts/add-voice-agent-playbook.py [--dry-run] [--force]
"""
from __future__ import annotations

import argparse
import glob
import html
import logging
import os
import re
import sys
import tempfile

log = logging.getLogger("voice-agent-playbook")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEWS = os.path.join(ROOT, "previews", "mk-b82e50b0a4")
DESIGN_PAGES = ("a.html", "b.html", "c.html", "d.html", "e.html", "f.html")

# SAFETY: only these sets get the playbook. `sites/` is deliberately EXCLUDED - those are
# the isolated per-business client send-links (commit 91ec190) and they carry no triangle,
# no playbook and no PRIVATE tag by design. They are the pages handed to the prospect, so
# injecting cost/margin there would hand a client the exact numbers you negotiate against.
# Do not widen this to a glob over previews/*/*/ - that would sweep sites/ in.
LEAD_SETS = ("local", "metro")

# --- pricing (single source of truth) ---------------------------------------
PRICE_SETUP = "$500 setup"
PRICE_MONTHLY = "$199/mo"
PRICE_FULL = f"{PRICE_SETUP} + {PRICE_MONTHLY}"
COST_RANGE = "~$10-35/mo"
MARGIN_RANGE = "~$165-190/mo"
SITE_CARE = "$99"
BUNDLED = "$298/mo"

MARKER = "VA:START"  # idempotency marker (wraps every block this script owns)

# --- per-trade content ------------------------------------------------------
# Each entry: hook, why, math (their side), and two trade-specific objections.
TRADES = {
    "septic": dict(
        hook="Emergency trade - a backed-up line at 9pm does not leave a voicemail.",
        why="Septic and sewer calls are panic calls. Somebody with sewage in the basement "
            "rings the top three listings until a human answers. If that is not {name}, the "
            "job is simply gone - there is no callback, because they already hired someone.",
        ticket="a pump-and-repair call runs a few hundred, a system replacement many thousands",
        months="one emergency call a year",
    ),
    "plumbing": dict(
        hook="Emergency trade - a burst pipe at 9pm does not leave a voicemail.",
        why="Plumbing is the clearest case there is. A leak is happening right now, and the "
            "caller works down the Google list until somebody picks up. Every after-hours "
            "ring {name} misses is a job that went to the next name on the page.",
        ticket="a service call runs a few hundred, a repipe or water heater several thousand",
        months="one service call a month",
    ),
    "hvac": dict(
        hook="Emergency trade - no heat in January, no A/C in July, and nobody waits.",
        why="HVAC demand arrives in spikes on the worst weather days, which is exactly when "
            "the techs are buried and the phone rings hardest. {name} cannot answer while "
            "under a furnace, and a cold house calls the next company in about ninety seconds.",
        ticket="a service call runs a few hundred, a system replacement several thousand",
        months="one service call a month",
    ),
    "electrical": dict(
        hook="Emergency trade - half the house is dark and they are calling right now.",
        why="Electrical calls split between true emergencies and scheduled work, and both "
            "leak the same way: the tech is on a job with hands full. An agent catches the "
            "panic call and books the panel upgrade instead of sending it to voicemail.",
        ticket="a service call runs a couple hundred, a panel upgrade a few thousand",
        months="one service call a month",
    ),
    "roofing": dict(
        hook="Storm trade - after hail your phone rings forty times in two days.",
        why="Roofing money arrives in bursts. After a storm {name} physically cannot answer "
            "every call, and the ones that ring out go to the out-of-town crews who flood in "
            "with call centers. An agent means the surge gets captured instead of lost.",
        ticket="a roof replacement runs many thousands",
        months="one roof for several years",
    ),
    "gutters": dict(
        hook="Overflow trade - the calls arrive all at once after heavy rain.",
        why="Gutter work clusters after storms and in the fall, and it is almost always a "
            "quote request rather than an emergency. Those requests go to whoever replies "
            "first - the agent answers at 8pm and books {name} the estimate.",
        ticket="a gutter job runs one to a few thousand",
        months="one job a year",
    ),
    "siding": dict(
        hook="Storm and quote trade - the estimate goes to whoever answers first.",
        why="Siding is a considered purchase that starts with a phone call for a quote. The "
            "homeowner calls two or three companies in one sitting. Whoever picks up gets "
            "on the calendar first, and first on the calendar usually wins the job.",
        ticket="a siding job runs several thousand",
        months="one job for years",
    ),
    "garage": dict(
        hook="Emergency trade - a door stuck shut means a car trapped in the garage.",
        why="A broken garage door is an urgent, same-day problem and the caller will not wait. "
            "It is also a fast, high-margin repair for {name}. Missing those calls after hours "
            "is losing the easiest work of the week.",
        ticket="a repair runs a couple hundred, a new door over a thousand",
        months="one door a year",
    ),
    "paving": dict(
        hook="Seasonal quote trade - the whole year's work is booked in a few months.",
        why="Paving and sealcoating sell in a short season, and every call is a quote request. "
            "{name} is on a driveway all day with equipment running - nobody hears the phone. "
            "Those quote calls go to the competitor who answered.",
        ticket="a driveway runs a few thousand",
        months="one driveway a year",
    ),
    "concrete": dict(
        hook="Quote trade - crews run loud equipment and the phone loses.",
        why="Concrete, masonry and retaining-wall work is all estimate-driven, and the crew "
            "cannot hear a phone over a mixer or a saw. Every missed ring is a homeowner who "
            "wanted a number and got silence from {name}.",
        ticket="a patio or wall runs several thousand",
        months="one job a year",
    ),
    "fencing": dict(
        hook="Quote trade - homeowners call three fencers in one afternoon.",
        why="Fencing buyers shop. They call a short list back-to-back and book the first one "
            "who answers and sounds organized. An agent that picks up and captures the yard "
            "size and fence type puts {name} first in that line every time.",
        ticket="a fence runs a few thousand",
        months="one fence a year",
    ),
    "polebarn": dict(
        hook="High-ticket trade - one building pays for this many times over.",
        why="Post-frame buildings are the biggest ticket on this list and the buying process "
            "starts with a phone call full of questions - sizes, spans, permits. An agent that "
            "captures those details and books the call back is worth a great deal to {name}.",
        ticket="a building runs well into five figures",
        months="one building for many years",
    ),
    "painting": dict(
        hook="Quote trade - painters are up a ladder when the phone rings.",
        why="Painting is sold on estimates, and {name} is physically unable to answer while "
            "cutting in a ceiling. The homeowner who wanted a quote calls the next painter. "
            "An agent takes the room count and books the walkthrough.",
        ticket="an interior or exterior job runs a couple thousand up",
        months="one job a year",
    ),
    "landscaping": dict(
        hook="Quote and recurring trade - mowers drown out every call.",
        why="Landscaping and excavation both run loud equipment all day, and a good share of "
            "calls are recurring maintenance - the kind that pays {name} every month for years. "
            "Losing one of those to voicemail costs far more than the single job.",
        ticket="a project runs a few thousand, and maintenance repeats monthly",
        months="one maintenance account",
    ),
    "flooring": dict(
        hook="Showroom trade - the after-hours question never gets asked twice.",
        why="Flooring buyers call with narrow questions - do you carry this, what does it run "
            "per square foot, when could you measure. Those calls come in the evening after "
            "work, when {name} is closed. An agent answers and books the measure.",
        ticket="a flooring job runs a few thousand",
        months="one job a year",
    ),
    "glass": dict(
        hook="Mixed emergency trade - a broken window is a same-day problem.",
        why="Glass splits between urgent board-ups and scheduled replacement, and the urgent "
            "half will not wait on a callback. An agent lets {name} capture the emergency at "
            "10pm and quote the window replacement in the morning.",
        ticket="a repair runs a few hundred, a full replacement into the thousands",
        months="one job a month",
    ),
    "insulation": dict(
        hook="Quote trade - driven by energy bills and rebate season.",
        why="Insulation calls spike when bills land and when rebates are announced, and they "
            "are all quote requests. The homeowner calls two contractors. The one who answers "
            "gets the attic. An agent makes that {name}.",
        ticket="an insulation job runs a couple thousand up",
        months="one job a year",
    ),
    "handyman": dict(
        hook="Volume trade - lots of small calls, and every one is lost the same way.",
        why="Handyman work is high-volume and low-ceremony: people call with a list and hire "
            "whoever calls back first. {name} is on a job all day, so most of those calls die "
            "in voicemail. An agent turns them into a booked schedule.",
        ticket="a typical job runs a few hundred to a couple thousand",
        months="one small job a month",
    ),
    "gc": dict(
        hook="Quote trade - the biggest jobs start with an unanswered phone call.",
        why="General contracting leads arrive as open-ended calls - remodels, additions, "
            "repairs - and they need a human to capture scope. {name} is on site all day. "
            "An agent takes the details and books the walkthrough instead of losing the lead.",
        ticket="a remodel runs many thousands",
        months="one job for a year or more",
    ),
}

GENERIC_OBJECTIONS = [
    ("&quot;I answer my own phone.&quot;",
     "Not at 8pm on a Saturday you don&#x27;t - and that&#x27;s when half of these calls come in. "
     "This only picks up what you were already missing."),
    ("&quot;Won&#x27;t it sound like a robot?&quot;",
     "Let them hear it. Call the demo on the spot and hand them the phone - that&#x27;s the whole close."),
    ("&quot;What if it says something wrong?&quot;",
     "It only knows what we put in it - your services, your area, your hours. It books and takes "
     "messages; it never quotes a job."),
    ("&quot;I&#x27;ll just get an answering service.&quot;",
     "Those charge per call and read from a card. This one knows your trade and your town, and it "
     "texts you the lead before they&#x27;ve hung up."),
]

GUARDRAILS = [
    "Sell this <b>after</b> the site is signed - never instead of it. The site is the product; "
    "this is the add-on.",
    "It <b>answers, qualifies and books</b>. It does not diagnose, price a job, or promise a "
    "tech by a certain hour. Say that out loud.",
    "Minutes are metered on your side - don&#x27;t promise &quot;unlimited.&quot; Heavy months "
    "get a conversation, not a surprise invoice.",
    "Don&#x27;t claim it replaces an office person. It covers the hours nobody is there.",
    "If they want calls <b>recorded</b>, check your state&#x27;s consent rules first - they vary "
    "and it is their liability as much as yours.",
]


# --- the general playbook (identical on every page) -------------------------
KIT = f"""
      <div class="pb-va-hook">You are not selling &quot;AI.&quot; You are selling the calls they
      are already losing.</div>

      <h3 class="pb-h">Who to go after first</h3>
      <ul class="pb-ul">
        <li><b>Tier 1 &mdash; high ticket, high miss rate.</b> Plumbing, septic, HVAC, electrical,
          roofing, garage doors. One missed call is a job worth hundreds to five figures.</li>
        <li><b>Tier 2 &mdash; booking driven.</b> Dental, vet, salons, storage, gyms. Steady volume,
          after-hours booking is the win.</li>
        <li><b>Tier 3 &mdash; your warm lane.</b> Nurseries, garden centres, landscapers. You speak
          the language already.</li>
      </ul>
      <p class="pb-p"><b>The wedge is after-hours.</b> Most shops are closed 5pm&ndash;8am and
      weekends &mdash; over half the week. You are not replacing their office person (scary, gets a
      no). You are covering the hours nobody is there.</p>

      <h3 class="pb-h">Five ways to sell it</h3>
      <ul class="pb-ul">
        <li><b>1. Website upsell &mdash; warmest.</b> Every site you build and every Site Care
          client is already a buyer. Start here before any cold work.</li>
        <li><b>2. Demo first.</b> Build their agent from their own website before you pitch:
          &quot;I built your shop a receptionist &mdash; call it.&quot; Beats any script.</li>
        <li><b>3. After-hours audit.</b> Call their line at 8pm, note what happens. That is the
          pitch. (Check consent law before recording anything.)</li>
        <li><b>4. Content.</b> Film the build. Nobody else in this niche can &mdash; it is your
          moat and it works while you sleep.</li>
        <li><b>5. Local.</b> Chamber, BNI, trade suppliers. These owners buy from people they met.</li>
      </ul>

      <h3 class="pb-h">Pricing rules</h3>
      <ul class="pb-ul">
        <li><b>{PRICE_FULL}.</b> Setup fee plus retainer &mdash; <b>never</b> per-minute to the
          client, or they fixate on the meter and you eat the overage.</li>
        <li>Anchor to one job: &quot;what is your average ticket?&quot; &rarr; &quot;this pays for
          itself if it catches one a month.&quot; Insurance, not expense.</li>
        <li>Cap included minutes with a defined overage so a viral month cannot sink you.</li>
        <li>Your cost {COST_RANGE} &mdash; margin {MARGIN_RANGE}. Stacked with Site Care: {BUNDLED}.</li>
      </ul>

      <h3 class="pb-h">Qualify in one question</h3>
      <p class="pb-script">&quot;What happens when somebody calls you at 7pm?&quot;<br>
      Voicemail &rarr; you have a customer. &quot;My wife answers&quot; &rarr; walk. Skip anyone who
      already answers reliably, and anyone with almost no inbound calls.</p>

      <h3 class="pb-h">The red line &mdash; do not cross</h3>
      <p class="pb-p"><b>No ringless voicemail blasts. No scraped call lists.</b> The FCC ruled in
      Nov 2022 that ringless voicemail is a &quot;call&quot; under the TCPA needing prior express
      consent. B2B is <b>not</b> exempt on cell numbers. Damages are <b>$500 per call</b>, trebled
      to <b>$1,500</b> if willful, uncapped &mdash; 500 drops is a $250k&ndash;750k exposure. The
      guru videos selling this method are affiliate funnels. Inbound and demos only.</p>

      <h3 class="pb-h">How it actually gets built</h3>
      <ul class="pb-ul">
        <li><b>Phase 1 &mdash; web widget, no phone.</b> ElevenLabs agent (customer-service
          template) embedded on their site. No phone number means <b>no TCPA surface at all</b>.</li>
        <li><b>Phase 2 &mdash; the phone.</b> Link a Twilio number once Phase 1 has earned it. This
          is where the real money is, because this is where the loss is.</li>
        <li><b>Phase 3 &mdash; the reel.</b> Film it. Demo asset and funnel in one.</li>
        <li>Knowledge base = their services, area, hours. It books and takes messages; it never
          quotes a job.</li>
      </ul>
"""


def trade_key(name: str, meta: str) -> str:
    """Map a business name + meta line onto a trade bucket. Specific wins over generic."""
    blob = f"{name} {meta}".lower()
    # order matters: a "Roofing" company listed under "General Contractors" is a roofer
    ordered = [
        ("septic", ("septic", "sewer", "waste water")),
        ("roofing", ("roof",)),
        ("hvac", ("heating", "air condition", "refrigerat", "hvac", " air ")),
        ("plumbing", ("plumb",)),
        ("electrical", ("electric",)),
        ("garage", ("garage door",)),
        ("gutters", ("gutter", "downspout")),
        ("siding", ("siding", "sheetmetal", "sheet metal")),
        ("polebarn", ("pole", "post frame", "post-frame")),
        ("paving", ("paving", "asphalt", "sealcoat", "seal coat", "line striping")),
        ("concrete", ("concrete", "masonry", "retaining")),
        ("fencing", ("fenc",)),
        ("painting", ("paint",)),
        ("insulation", ("insulation",)),
        ("flooring", ("floor", "tile", "carpet")),
        ("glass", ("glass", "window")),
        ("landscaping", ("landscap", "lawn", "excavat", "outdoor design")),
        ("handyman", ("handyman", "home repair")),
        ("gc", ("general contract", "contractor", "building suppl", "home solution",
                "remodel", "improvement")),
    ]
    for key, needles in ordered:
        if any(n in blob for n in needles):
            return key
    return "gc"


def build_section(name: str, meta: str) -> str:
    t = TRADES[trade_key(name, meta)]
    esc = html.escape(name, quote=False)
    why = t["why"].format(name=f"<b>{esc}</b>")

    objections = "".join(
        f"<li><b>{q}</b> &rarr; {a}</li>" for q, a in GENERIC_OBJECTIONS
    )
    guards = "".join(f"<li>{g}</li>" for g in GUARDRAILS)

    return f"""<!--VA:START-->
    <div class="pb-rule"></div>
    <button id="pb-va-btn" class="pb-va-btn" type="button" aria-expanded="false" aria-controls="pb-va">
      <span class="pb-va-btn-t">Voice agent &mdash; the {PRICE_MONTHLY} add-on</span>
      <span class="pb-va-chev" aria-hidden="true">&#9662;</span>
    </button>
    <div id="pb-va" class="pb-va" hidden>
      <div class="pb-va-hook">{t['hook']}</div>

      <h3 class="pb-h">Why {esc} specifically</h3>
      <p class="pb-p">{why}</p>

      <h3 class="pb-h">The ask &mdash; 20 seconds, once they like the site</h3>
      <p class="pb-script">&quot;One more thing. When somebody calls you after hours right now,
      what happens? &hellip; Right. I can put a thing on your line that picks up every time,
      answers the basic stuff, and texts you the name and number before they&#x27;ve hung up.
      Want to hear it? Here &mdash; call this.&quot;</p>

      <h3 class="pb-h">Their math</h3>
      <p class="pb-p">For {esc}, {t['ticket']}. At {PRICE_MONTHLY}, catching
      <b>{t['months']}</b> that would otherwise have gone to voicemail pays for the whole thing.
      That&#x27;s the only number they need to hear.</p>

      <h3 class="pb-h">Your math &mdash; private</h3>
      <div class="pb-facts">
        <div class="pb-row"><span class="pb-k">You charge</span><span class="pb-v"><b class="pb-va-price">{PRICE_FULL}</b></span></div>
        <div class="pb-row"><span class="pb-k">Your cost</span><span class="pb-v">{COST_RANGE} <span class="pb-va-dim">(~$0.08/min + LLM + number)</span></span></div>
        <div class="pb-row"><span class="pb-k">Margin</span><span class="pb-v">{MARGIN_RANGE} recurring</span></div>
        <div class="pb-row"><span class="pb-k">Stacked</span><span class="pb-v">{SITE_CARE} Site Care + {PRICE_MONTHLY} = <b>{BUNDLED}</b></span></div>
        <div class="pb-row"><span class="pb-k">Watch</span><span class="pb-v"><span class="pb-va-dim">Billed on call duration, not compute &mdash; silent callers still cost you.</span></span></div>
      </div>

      <h3 class="pb-h">Objections</h3>
      <ul class="pb-ul">{objections}</ul>

      <h3 class="pb-h">Don&#x27;t oversell</h3>
      <ul class="pb-ul">{guards}</ul>
    </div>

    <button id="pb-vk-btn" class="pb-va-btn" type="button" aria-expanded="false" aria-controls="pb-vk">
      <span class="pb-va-btn-t">Voice agent &mdash; the whole playbook</span>
      <span class="pb-va-chev" aria-hidden="true">&#9662;</span>
    </button>
    <div id="pb-vk" class="pb-va" hidden>{KIT}</div>
<!--VA:END-->
"""


_CSS_BODY = """
#pbk .pb-va-btn{display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;
  margin:14px 0 0;padding:12px 14px;border:1px solid #3a3020;border-radius:12px;cursor:pointer;
  background:#1d1913;color:#e9e7e2;font:inherit;font-size:14px;font-weight:600;text-align:left}
#pbk .pb-va-btn:hover{background:#241f16;border-color:#4a3d27}
#pbk .pb-va-btn-t{color:#e0a24a}
#pbk .pb-va-chev{color:#8b9099;font-size:12px;transition:transform .15s ease}
#pbk .pb-va-btn[aria-expanded="true"] .pb-va-chev{transform:rotate(180deg)}
#pbk .pb-va[hidden]{display:none}
#pbk .pb-va{padding:2px 2px 4px}
#pbk .pb-va-hook{margin:14px 0 2px;padding:10px 13px;border-radius:10px;background:#1a1d24;
  border-left:3px solid #e0a24a;color:#f2efe9;font-size:13.5px;font-weight:600}
#pbk .pb-va-price{color:#7fd0a3}
#pbk .pb-va-dim{color:#8b9099;font-size:12px}
"""

# Marker-wrapped. strip_existing() removes these by MARKER, never by matching their text -
# so editing _CSS_BODY/_JS_BODY can never again orphan the old copy and append a duplicate
# (the bug that shipped in the first release and duplicated CSS across all 240 files).
VA_CSS = "\n/*VA:CSS-START*/" + _CSS_BODY + "/*VA:CSS-END*/\n"

# FROZEN SNAPSHOT - do not edit, do not "tidy". This is the exact unmarked CSS the
# pre-marker releases wrote into the files. It exists solely so one --force can still find
# and remove it; once every file carries the markers above it is inert history.
_FROZEN_CSS_V2 = _CSS_BODY

_JS_BODY = """
<script>
(function(){
  // Delegated on purpose. Binding per-button at load time proved fragile - in a
  // static-snapshot renderer the first button's panel was not resolvable yet, so that
  // button silently never got a handler while the second one worked. One document-level
  // listener cannot lose that race, and it keeps working if the panel is ever re-rendered.
  document.addEventListener('click',function(e){
    var t=e.target,b=null;
    while(t&&t!==document){
      if(t.className&&String(t.className).indexOf('pb-va-btn')>-1){b=t;break;}
      t=t.parentNode;
    }
    if(!b)return;
    var p=document.getElementById(b.getAttribute('aria-controls'));
    if(!p)return;
    var open=p.hidden;
    p.hidden=!open;
    b.setAttribute('aria-expanded',open?'true':'false');
  });
})();
</script>
"""


VA_JS = "\n<!--VA:JS-START-->" + _JS_BODY + "<!--VA:JS-END-->\n"

# FROZEN SNAPSHOT - see the CSS note above. Same purpose, same rule: never edit.
_FROZEN_JS_V2 = _JS_BODY

LEGACY_MARKER = 'id="pb-va-btn"'


def strip_existing(text: str) -> str:
    """Remove every block this script has ever injected, so --force re-applies cleanly.

    Two generations exist in the wild: the first release had no comment markers, so a
    --force against it silently appended a SECOND copy (duplicate CSS, a stale third
    button). Both are removed here. The legacy sweep is anchored to the .pb-foot div -
    the panel's last element - so it can only ever eat this script's own region.
    """
    # 1. marker-anchored: survives any future edit to the block's wording
    for pattern in (r"<!--VA:START-->.*?<!--VA:END-->\n?",
                    r"/\*VA:CSS-START\*/.*?/\*VA:CSS-END\*/\n?",
                    r"<!--VA:JS-START-->.*?<!--VA:JS-END-->\n?"):
        text = re.sub(pattern, "", text, flags=re.S)

    # 2. legacy markup sweep, anchored to .pb-foot (the panel's last element) so it can
    #    only ever eat this script's own region
    text = re.sub(
        r'\n    <div class="pb-rule"></div>\n    <button id="pb-va-btn".*?\n    </div>\n'
        r'(?=\s*<div class="pb-foot">)',
        "\n", text, flags=re.S)

    # 3. frozen pre-marker CSS/JS. Content-matched by necessity - these are historical
    #    constants, never edited, so the match cannot drift. New generations are removed
    #    by their markers in step 1, so this is the last time content matching is needed.
    for chunk in (_FROZEN_CSS_V2, _FROZEN_CSS_V2.strip() + "\n",
                  _FROZEN_JS_V2, _FROZEN_JS_V2.strip() + "\n"):
        while chunk and chunk in text:
            text = text.replace(chunk, "")
    return text


def _write_atomic(path: str, text: str) -> None:
    """Write via a temp file in the same directory, then os.replace.

    A plain open(path, "w") truncates immediately: an interruption mid-write (disk full,
    AV lock, killed process) would leave a prospect page empty with no way back. os.replace
    is atomic on the same filesystem, so a reader sees either the old file or the new one.
    """
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".va-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError as exc:
            log.warning("could not remove temp file %s: %s", tmp, exc)
        raise


def patch(path: str, force: bool) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        log.error("read failed %s: %s", path, exc)
        return "read-error"

    if MARKER in text or LEGACY_MARKER in text:
        if not force:
            return "skip"
        text = strip_existing(text)

    name_m = re.search(r'<h2 class="pb-name">(.*?)</h2>', text, re.S)
    meta_m = re.search(r'<div class="pb-meta">(.*?)</div>', text, re.S)
    if not name_m or not meta_m:
        return "no-playbook"

    name = html.unescape(name_m.group(1)).strip()
    meta = html.unescape(meta_m.group(1)).strip()

    foot = '    <div class="pb-foot">'
    if foot not in text:
        return "no-foot"
    text = text.replace(foot, build_section(name, meta) + "\n" + foot, 1)

    # CSS rides inside the existing playbook <style> block, JS just before </body>
    anchor = "#pbk .pb-foot{"
    if anchor not in text:
        return "no-style"
    text = text.replace(anchor, VA_CSS.strip() + "\n" + anchor, 1)

    if "</body>" not in text:
        return "no-body"
    text = text.replace("</body>", VA_JS + "</body>", 1)

    try:
        _write_atomic(path, text)
    except OSError as exc:
        log.error("write failed %s: %s", path, exc)
        return "write-error"
    return "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="strip and re-apply an existing block (use after a price change)")
    args = ap.parse_args()

    if not os.path.isdir(PREVIEWS):
        print(f"previews dir not found: {PREVIEWS}", file=sys.stderr)
        return 2

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    counts: dict[str, int] = {}
    trades: dict[str, int] = {}
    problems: list[tuple[str, str]] = []
    for set_ in LEAD_SETS:
        for d in sorted(glob.glob(os.path.join(PREVIEWS, set_, "*"))):
            if not os.path.isdir(d):
                continue
            first = os.path.join(d, "a.html")
            if os.path.exists(first):
                try:
                    with open(first, encoding="utf-8") as fh:
                        t = fh.read()
                except (OSError, UnicodeDecodeError) as exc:
                    log.warning("trade probe failed %s: %s", first, exc)
                    t = ""
                n = re.search(r'<h2 class="pb-name">(.*?)</h2>', t, re.S)
                m = re.search(r'<div class="pb-meta">(.*?)</div>', t, re.S)
                if n and m:
                    k = trade_key(html.unescape(n.group(1)), html.unescape(m.group(1)))
                    trades[k] = trades.get(k, 0) + 1
            for page in DESIGN_PAGES:
                p = os.path.join(d, page)
                if not os.path.exists(p):
                    continue
                if args.dry_run:
                    res = "would-patch"
                else:
                    res = patch(p, args.force)
                counts[res] = counts.get(res, 0) + 1
                if res not in ("ok", "skip", "would-patch"):
                    problems.append((res, p))

    print("results:", dict(sorted(counts.items())))
    print("trade buckets:", dict(sorted(trades.items(), key=lambda kv: -kv[1])))
    # An aggregate count alone leaves the operator hunting for which files need repair.
    if problems:
        print(f"PROBLEM FILES ({len(problems)}):", file=sys.stderr)
        for res, p in problems:
            print(f"  {res}: {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
