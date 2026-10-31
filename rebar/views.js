// views.js - builds the HTML for each panel as strings. No DOM access; app.js puts them on the page.
// Anything the user typed goes through esc(). Inputs carry data-b="<where it is stored>" (see app.js).
import { BARS } from './rebar-math.js';
import { letter, cutLetter, closingSide, fmt0, fmt1, fmt2, ft, CLOSED_FT } from './calc.js';

export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

let fieldCounter = 0;
const fid = () => `f${++fieldCounter}`;

export const BAD = {
  ft: `Can't read that. Try 27'-10 1/2" or 27-10.5`,
  sft: `Can't read that. Try 4'-6" or -4.5 (a minus means the other side of the start corner)`,
  in: 'Type inches, like 12 or 16',
  num: 'Type a number, like 0.56',
  int: 'Type a whole number, like 14',
};

const tip = (text) => `<details class="tip"><summary aria-label="What does this mean?">?</summary><span class="tip-body">${esc(text)}</span></details>`;

function field({ label, tipText, b, value, check, placeholder = '', mode = 'text', cls = '', unit = '', rerender = false }) {
  const id = fid();
  return `<div class="field ${cls}"><div class="lbl"><label for="${id}">${label}</label>${tipText ? tip(tipText) : ''}</div>
  <div class="inwrap"><input id="${id}" type="text" inputmode="${mode}" autocomplete="off" autocapitalize="off" spellcheck="false" data-b="${b}"${check ? ` data-check="${check}"` : ''}${rerender ? ' data-rerender' : ''} value="${esc(value)}" placeholder="${esc(placeholder)}" aria-describedby="${id}e">${unit ? `<span class="unit">${unit}</span>` : ''}</div>
  <p class="err" id="${id}e" aria-live="polite"></p></div>`;
}

function select({ label, tipText, b, value, options, cls = '', rerender = false }) {
  const id = fid();
  return `<div class="field ${cls}"><div class="lbl"><label for="${id}">${label}</label>${tipText ? tip(tipText) : ''}</div>
  <div class="inwrap"><select id="${id}" data-b="${b}"${rerender ? ' data-rerender' : ''}>${options.map(([v, t]) => `<option value="${esc(v)}"${String(v) === String(value) ? ' selected' : ''}>${esc(t)}</option>`).join('')}</select></div></div>`;
}

const seg = (label, act, items, current, extra = '') => `<div class="seg" role="radiogroup" aria-label="${esc(label)}">${items.map(([v, t]) =>
  `<button type="button" role="radio" aria-checked="${String(v) === String(current)}" data-act="${act}" data-v="${esc(v)}"${extra}>${t}</button>`).join('')}</div>`;

// ---------------------------------------------------------------- landing
export function heroHtml() {
  return `<div class="hero-inner">
  <h1>Count the rebar in any slab shape</h1>
  <p class="lead">Draw the slab, take the old foundations off, and get pounds with every step of the math showing. It all stays on this device.</p>
  <div class="choices">
    <button type="button" class="choice" data-act="startPhoto"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 11a2 2 0 0 1 2-2h3l2-3h10l2 3h3a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><circle cx="16" cy="17" r="5"/></svg><span class="choice-t">Start from a photo</span><span class="choice-d">Snap the slab or pick a picture, then tap its corners.</span></button>
    <button type="button" class="choice" data-act="startType"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 26V8h10v6h6v6h6v6z"/><path d="M5 12h3M5 16h3M5 20h3M5 24h3"/></svg><span class="choice-t">Type the sides</span><span class="choice-d">Walk the edges: right 60', up 20', left 30', and so on.</span></button>
  </div>
  <p class="small-links"><button type="button" class="linkish" data-act="example">Load an example</button><span aria-hidden="true">&middot;</span><button type="button" class="linkish" data-act="openFile">Open a saved job file</button></p>
</div>`;
}

// ---------------------------------------------------------------- step 1: shape
const DIRS = [['R', '&rarr;', 'right'], ['U', '&uarr;', 'up'], ['L', '&larr;', 'left'], ['D', '&darr;', 'down']];
const CURVE_BY = [['rise', 'Rise (how far it bulges)'], ['radius', 'Radius'], ['arc', 'Arc length']];
const CURVE_TIP = {
  rise: 'The rise is the straight-line distance from the middle of the chord (the straight side) out to the middle of the curve.',
  radius: 'The radius of the circle the curve is part of. It must be at least half the side length.',
  arc: 'The length measured along the curve itself. It is always longer than the straight side.',
};

export function rowHtml(row, i, scope) {
  const key = (f) => (scope.cutId ? `cstep.${scope.cutId}.${row.id}.${f}` : `step.${row.id}.${f}`);
  const cut = scope.cutId ? ` data-cut="${scope.cutId}"` : '';
  const lab = scope.cutId ? cutLetter(scope.cutIndex, i) : letter(i);
  const dirs = DIRS.map(([v, glyph, word]) => `<button type="button" role="radio" class="dirbtn" aria-checked="${row.dir === v}" data-act="dir" data-id="${row.id}"${cut} data-v="${v}" title="${word}">${glyph}<span class="sr"> ${word}</span></button>`).join('')
    + `<button type="button" role="radio" class="dirbtn wide" aria-checked="${row.dir === 'ANG'}" data-act="dir" data-id="${row.id}"${cut} data-v="ANG" title="any angle">&ang;<span class="sr"> angle</span></button>`;
  const angle = row.dir === 'ANG'
    ? `<div class="field ang"><div class="lbl"><label>Angle in degrees</label>${tip('0 is straight right (east), 90 is straight up (north), 180 is left, 270 is down.')}</div><div class="inwrap"><input type="text" inputmode="decimal" autocomplete="off" data-b="${key('angText')}" value="${esc(row.angText)}" placeholder="degrees" aria-label="Angle of side ${lab} in degrees"><span class="unit">deg</span></div><p class="err" data-err="ang:${row.id}" aria-live="polite"></p></div>` : '';
  const curve = row.curve !== 'none'
    ? `<div class="curvebox"><div class="field"><div class="lbl"><label>Measured as</label>${tip(CURVE_TIP[row.curveBy])}</div><div class="inwrap"><select data-b="${key('curveBy')}" data-rerender aria-label="How the curve of side ${lab} is measured">${CURVE_BY.map(([v, t]) => `<option value="${v}"${row.curveBy === v ? ' selected' : ''}>${t}</option>`).join('')}</select></div></div>
      <div class="field"><div class="lbl"><label>${{ rise: 'Rise', radius: 'Radius', arc: 'Arc length' }[row.curveBy]}</label></div><div class="inwrap"><input type="text" inputmode="text" autocomplete="off" data-b="${key('curveText')}" value="${esc(row.curveText)}" placeholder="${{ rise: 'rise', radius: 'radius', arc: 'arc length' }[row.curveBy]}" aria-label="Curve measurement for side ${lab}"></div><p class="err" data-err="curve:${row.id}" aria-live="polite"></p></div></div>` : '';
  return `<li class="row" data-row="${row.id}">
  <span class="badge" aria-hidden="true">${lab}</span>
  <div class="dirs seg" role="radiogroup" aria-label="Direction of side ${lab}">${dirs}</div>
  <div class="field len"><div class="inwrap"><input type="text" inputmode="text" autocomplete="off" autocapitalize="off" spellcheck="false" data-b="${key('lenText')}" data-role="len" data-id="${row.id}"${cut} value="${esc(row.lenText)}" placeholder="length" aria-label="Length of side ${lab}"></div><p class="err" data-err="len:${row.id}" aria-live="polite"></p>${row.est ? '<p class="est-tag">estimated from the photo, check it</p>' : ''}</div>
  <div class="field curvesel"><div class="inwrap"><select data-b="${key('curve')}" data-rerender aria-label="Shape of side ${lab}"><option value="none"${row.curve === 'none' ? ' selected' : ''}>Straight</option><option value="out"${row.curve === 'out' ? ' selected' : ''}>Curves out</option><option value="in"${row.curve === 'in' ? ' selected' : ''}>Curves in</option></select></div></div>
  <button type="button" class="icon" data-act="delRow" data-id="${row.id}"${cut} aria-label="Remove side ${lab}">&times;</button>
  ${angle}${curve}
</li>`;
}

export function shapeHtml(area, ui) {
  const q = ui.quick;
  const quick = `<details class="quick"${ui.quickOpen || (!area.steps.length && !ui.photoOpen) ? ' open' : ''}><summary>Quick shapes: rectangle or L</summary>
  <div class="quick-grid">
    <form class="quick-form" data-form="rect"><h4>Rectangle</h4>
      <div class="two">${quickField('rect.w', 'Width', q.rect.w)}${quickField('rect.l', 'Length', q.rect.l)}</div>
      <button type="submit" class="btn">Make the rectangle</button><p class="err" data-qerr="rect" aria-live="polite"></p></form>
    <form class="quick-form" data-form="ell"><h4>L-shape</h4>
      <div class="two">${quickField('ell.w', 'Overall width', q.ell.w)}${quickField('ell.l', 'Overall length', q.ell.l)}${quickField('ell.nw', 'Notch width', q.ell.nw)}${quickField('ell.nl', 'Notch length', q.ell.nl)}</div>
      <p class="hint">The notch is cut from the top-right corner.</p>
      <button type="submit" class="btn">Make the L</button><p class="err" data-qerr="ell" aria-live="polite"></p></form>
  </div></details>`;
  const rows = area.steps.map((r, i) => rowHtml(r, i, {})).join('');
  return `<h2 class="step-title">Walk the edges</h2>
<p class="step-help">Start at any corner. For each side, pick the way you head and type how long it is. The drawing builds as you go.</p>
<div id="photoSlot"></div>
${quick}
<p class="hint format-hint">Type lengths like 27'-10 1/2" or 27-10.5 (feet, then inches). Plain feet like 27.875 also works.</p>
<ol class="rows" aria-label="Sides of the slab">${rows}</ol>
<div class="row-actions"><button type="button" class="btn" data-act="addRow">+ Add a side</button></div>
<div id="closureBox" class="closure" aria-live="polite"></div>
<div id="estimateBox"></div>
<div class="nav-next"><button type="button" class="btn primary" data-act="step" data-v="cuts">Next: Cutouts</button></div>`;
}

function quickField(key, label, value) {
  const id = fid();
  return `<div class="field"><div class="lbl"><label for="${id}">${label}</label></div><div class="inwrap"><input id="${id}" type="text" inputmode="text" autocomplete="off" data-q="${key}" value="${esc(value)}" placeholder="${esc(label.toLowerCase())}"></div></div>`;
}

// the line under the rows that explains whether the outline closes
export function closureHtml(area, res) {
  if (!area.steps.length) return '';
  if (res.outline) {
    const gap = res.outline.closureGap;
    if (gap <= CLOSED_FT) return `<p class="ok">Closed: the last side meets the start corner.</p>`;
    const fix = closingSide(area.steps);
    const last = letter(area.steps.length - 1);
    const tilt = fix && fix.dir === 'ANG' ? `<p class="hint">That would tilt side ${last} a little. If ${last} should run straight, one of the other lengths is probably the one that is off.</p>` : '';
    return `<p class="gapmsg">The last side ends <b>${esc(ft(gap))}</b> from the start corner. Either a length is off, or let the last side fix it.</p>${fix ? `<button type="button" class="btn" data-act="closeIt">Close it for me (set side ${last})</button>${tilt}` : ''}`;
  }
  const fix = area.steps.length >= 3 ? closingSide(area.steps) : null;
  if (fix && !String(area.steps[area.steps.length - 1].lenText).trim()) {
    return `<button type="button" class="btn" data-act="closeIt">Close it for me (set side ${letter(area.steps.length - 1)})</button>`;
  }
  return '';
}

export function estimateHtml(area, res) {
  if (!area.sketch || area.sketch.length !== area.steps.length) return '';
  const typed = res.sides.some((s) => Number.isFinite(s.status.len) && !s.row.est);
  const blank = res.sides.some((s) => s.status.blank || s.row.est);
  if (!blank) return '';
  return `<div class="estimate"><p>${typed ? 'You typed at least one real length, so the others can be estimated from the photo.' : 'Type one side you measured (any one). Then the others can be estimated from the photo.'}</p>
  <button type="button" class="btn"${typed ? '' : ' disabled'} data-act="estimate">Estimate the other sides from the photo</button>
  <p class="hint">Estimates are marked "check". Photos taken at an angle stretch and shrink lengths, so measure the sides that matter.</p></div>`;
}

// ---------------------------------------------------------------- step 2: cutouts
const KINDS = [['rect', 'Rectangle'], ['circle', 'Circle'], ['traced', 'Traced shape'], ['quick', 'Count only']];
const POS_TIP = 'Measured from the start corner of the outline (where you began walking). Across is to the right, up is toward the top of the drawing. A minus number goes the other way, for an old foundation that hangs past the edge.';

export function cutoutCard(c, k, area) {
  const b = (f) => `cut.${c.id}.${f}`;
  let body = '';
  if (c.kind === 'rect') {
    body = `<div class="two">${field({ label: 'Across from start', tipText: POS_TIP, b: b('xText'), value: c.xText, check: 'sft', placeholder: 'across' })}${field({ label: 'Up from start', b: b('yText'), value: c.yText, check: 'sft', placeholder: 'up' })}
    ${field({ label: 'Width (across)', b: b('wText'), value: c.wText, check: 'ft', placeholder: 'width' })}${field({ label: 'Length (up)', b: b('lText'), value: c.lText, check: 'ft', placeholder: 'length' })}</div>`;
  } else if (c.kind === 'circle') {
    body = `<div class="two">${field({ label: 'Center across', tipText: POS_TIP, b: b('cxText'), value: c.cxText, check: 'sft', placeholder: 'across' })}${field({ label: 'Center up', b: b('cyText'), value: c.cyText, check: 'sft', placeholder: 'up' })}
    ${field({ label: 'Diameter', b: b('dText'), value: c.dText, check: 'ft', placeholder: 'diameter' })}</div>`;
  } else if (c.kind === 'traced') {
    body = `<div class="two">${field({ label: 'Start across', tipText: `Where this shape starts, measured from the outline's start corner. ${POS_TIP}`, b: b('sxText'), value: c.sxText, check: 'sft', placeholder: 'across' })}${field({ label: 'Start up', b: b('syText'), value: c.syText, check: 'sft', placeholder: 'up' })}</div>
    ${c.est ? '<p class="est-tag">position estimated from the photo, check it</p>' : ''}
    <ol class="rows small" aria-label="Sides of ${esc(c.name || `cutout ${k + 1}`)}">${c.steps.map((r, i) => rowHtml(r, i, { cutId: c.id, cutIndex: k })).join('')}</ol>
    <button type="button" class="btn" data-act="addRow" data-cut="${c.id}">+ Add a side</button>`;
  } else {
    body = `<div class="two">${field({ label: 'How many', b: b('countText'), value: c.countText, check: 'int', mode: 'numeric', placeholder: 'count' })}
    ${select({ label: 'Shape', b: b('qShape'), value: c.qShape, options: [['circle', 'Round (piers)'], ['rect', 'Rectangle']], rerender: true })}
    ${c.qShape === 'rect' ? field({ label: 'Width', b: b('qwText'), value: c.qwText, check: 'ft', placeholder: 'width' }) + field({ label: 'Length', b: b('qlText'), value: c.qlText, check: 'ft', placeholder: 'length' })
      : field({ label: 'Diameter each', b: b('qdText'), value: c.qdText, check: 'ft', placeholder: 'diameter' })}</div>
    <p class="hint">No position needed; they are assumed to sit inside the slab. In the bar-by-bar method their weight comes off by area, so that line is approximate.</p>`;
  }
  return `<article class="cut-card" data-cut="${c.id}">
  <header><span class="ctag">C${k + 1}</span><input class="cutname" type="text" autocomplete="off" data-b="${b('name')}" value="${esc(c.name)}" placeholder="Name (optional), e.g. old footing" aria-label="Name of cutout C${k + 1}">
  <button type="button" class="icon" data-act="delCut" data-id="${c.id}" aria-label="Remove cutout C${k + 1}">&times;</button></header>
  ${seg(`Kind of cutout C${k + 1}`, 'cutKind', KINDS, c.kind, ` data-id="${c.id}"`)}
  ${body}
  <p class="cut-msg" data-err="cut:${c.id}" aria-live="polite"></p>
</article>`;
}

export function cutoutsHtml(area) {
  const cards = area.cutouts.map((c, k) => cutoutCard(c, k, area)).join('');
  return `<h2 class="step-title">Cutouts</h2>
<p class="step-help">Anything that is not new concrete: old foundations, piers, openings. They come off the area, and bars stop short of them. Skip this step if there are none.</p>
<p class="hint format-hint">Type lengths like 27'-10 1/2" or 27-10.5. Positions are measured from the start corner; a minus number goes the other way.</p>
${cards || '<p class="empty">No cutouts yet.</p>'}
<div class="add-cut"><span class="lbl">Add a cutout</span><div class="addrow">
  <button type="button" class="btn" data-act="addCut" data-v="rect">Rectangle</button>
  <button type="button" class="btn" data-act="addCut" data-v="circle">Circle</button>
  <button type="button" class="btn" data-act="addCut" data-v="traced">Traced shape</button>
  <button type="button" class="btn" data-act="addCut" data-v="quick">Piers (count only)</button></div></div>
<div class="nav-next"><button type="button" class="btn" data-act="step" data-v="shape">Back</button><button type="button" class="btn primary" data-act="step" data-v="rebar">Next: Rebar</button></div>`;
}

// ---------------------------------------------------------------- step 3: rebar
const FRACTION = { '#3': '3/8', '#4': '1/2', '#5': '5/8', '#6': '3/4', '#7': '7/8', '#8': '1', '#9': '1-1/8', '#10': '1-1/4', '#11': '1-3/8', '#14': '1-3/4', '#18': '2-1/4' };
export const sizeOptions = () => Object.keys(BARS).map((s) => [s, `${s}  (${FRACTION[s]} in)`]);

export function rebarHtml(area, settingsCalc) {
  const r = area.rebar;
  const b = (f) => `reb.${f}`;
  const spaceTxt = r.spacing2On && r.spacing2Text ? `${r.spacingText || '?'}" and ${r.spacing2Text}" oc` : `${r.spacingText || '?'}" oc each way`;
  const extras = area.extras.map((e) => `<li class="extra" data-extra="${e.id}">
    ${select({ label: 'Size', b: `ext.${e.id}.size`, value: e.size, options: sizeOptions() })}
    ${field({ label: 'Length each', b: `ext.${e.id}.lenText`, value: e.lenText, check: 'ft', placeholder: 'length' })}
    ${field({ label: 'How many', b: `ext.${e.id}.qtyText`, value: e.qtyText, check: 'int', mode: 'numeric', placeholder: 'how many' })}
    <button type="button" class="icon" data-act="delExtra" data-id="${e.id}" aria-label="Remove this bar line">&times;</button></li>`).join('');
  return `<h2 class="step-title">Rebar</h2>
<p class="step-help">Bar size and spacing come from the engineer's drawings. This page only counts and weighs.</p>
<div class="card-lite">
  <div class="two">
    ${select({ label: 'Bar size', b: b('size'), value: r.size, options: sizeOptions() })}
    ${field({ label: 'Bars every (spacing, "oc")', tipText: 'Center to center, in inches. "#5 @ 12 oc" means a #5 bar every 12 inches.', b: b('spacingText'), value: r.spacingText, check: 'in', mode: 'decimal', placeholder: 'inches', unit: 'in' })}
  </div>
  <label class="check"><input type="checkbox" data-b="${b('spacing2On')}" data-rerender${r.spacing2On ? ' checked' : ''}><span>Different spacing the other way</span></label>
  ${r.spacing2On ? field({ label: 'Other direction: bars every', b: b('spacing2Text'), value: r.spacing2Text, check: 'in', mode: 'decimal', placeholder: 'inches', unit: 'in' }) : ''}
  <div class="field"><div class="lbl"><span class="lbl-t">Layers of bars (mats)</span>${tip('A mat is one grid of bars running both ways. Two mats means a second grid on top of the first.')}</div>${seg('Mats', 'mats', [[1, '1 mat'], [2, '2 mats']], r.mats)}</div>
  <p class="phrase" id="rebarPhrase">${esc(r.size)} @ ${esc(spaceTxt)}, ${r.mats} mat${r.mats > 1 ? 's' : ''}</p>
</div>
<details class="adv"><summary>Advanced for this area: cover, lap rule, my own rate</summary>
  <div class="two">
    ${field({ label: 'Concrete cover', tipText: 'Bars stop this far short of every edge and cutout. 3 in is the usual for concrete poured against earth.', b: b('coverText'), value: r.coverText, check: 'in', mode: 'decimal', placeholder: 'inches', unit: 'in' })}
    ${select({ label: 'Lap rule', tipText: 'Exact: a run needs laps only when it is longer than one stock bar. Simple: one lap for every full stock bar length.', b: b('lapMode'), value: r.lapMode, options: [['exact', 'Exact (only past one stock bar)'], ['simple', 'Simple (one per full stock bar)']] })}
  </div>
  <div class="two">
    ${field({ label: 'My own rate (house rate)', tipText: 'Pounds per square foot you normally use. The page compares it with the plain math and flags a difference over 2%.', b: b('houseText'), value: r.houseText, check: 'num', mode: 'decimal', placeholder: 'lb per sf', unit: 'lb/sf' })}
    <div class="field"><div class="lbl"><span class="lbl-t">Use for the total</span></div>${seg('Which rate to use', 'houseUse', [['house', 'My rate'], ['math', 'The math']], r.houseUse)}</div>
  </div>
  <p class="hint">Stock bar length, lap length per bar size and waste are in Settings at the bottom of the page.</p>
</details>
<section class="loose" aria-label="Loose bars">
  <h3>Loose bars</h3><p class="hint">Curb steel, extra bars, anything counted by length instead of by area.</p>
  <ul class="extras">${extras}</ul>
  <button type="button" class="btn" data-act="addExtra">+ Add bars</button>
</section>
<div class="nav-next"><button type="button" class="btn" data-act="step" data-v="cuts">Back</button><button type="button" class="btn primary" data-act="step" data-v="results">See results</button></div>`;
}

// ---------------------------------------------------------------- step 4: wrap up
export function wrapHtml() {
  return `<h2 class="step-title">Results</h2>
<p class="step-help">Your numbers are on the right. Every line shows its math under "Show the math". Keep a copy of the job before you close the page.</p>
<div class="wrap-actions">
  <button type="button" class="btn primary" data-act="saveFile">Save job file</button>
  <button type="button" class="btn" data-act="print">Print or save as PDF</button>
  <button type="button" class="btn" data-act="csv">Download CSV for Excel</button>
  <button type="button" class="btn" data-act="addArea">+ Add another area</button>
</div>
<p class="hint">Autosave keeps the job in this browser only. Clearing your browser data wipes it, so save a job file for anything you want to keep.</p>
<div class="nav-next"><button type="button" class="btn" data-act="step" data-v="rebar">Back</button></div>`;
}

// ---------------------------------------------------------------- results
const sectionTitle = { area: 'Area', A: 'Method A: rate + laps', B: 'Method B: bar by bar', extras: 'Loose bars' };

export function linesHtml(lines) {
  return `<dl class="mathlines">${lines.map((l) => `<div class="ml${l.strong ? ' strong' : ''}"><dt>${esc(l.label)}${l.tag ? ` <span class="pill">${esc(l.tag)}</span>` : ''}</dt><dd class="m">${esc(l.math)}</dd><dd class="v">${esc(l.value)}</dd></div>`).join('')}</dl>`;
}

export function mathSections(res, open = false) {
  const parts = [];
  for (const key of ['area', 'A', 'B', 'extras']) {
    const lines = res.sections[key];
    if (!lines.length) continue;
    const used = (key === 'A' || key === 'B') && res.chosen === key ? ' <span class="pill used">used for totals</span>' : '';
    parts.push(`<h4>${sectionTitle[key]}${used}</h4>${linesHtml(lines)}`);
  }
  if (res.notes) parts.push(`<p class="hint">${esc(res.notes[0])}</p>`);
  void open;
  return parts.join('');
}

export const looseLb = (res) => res.sections.extras.reduce((t, l) => t + (l.lb || 0), 0);
export const areaPounds = (res) => Object.values(res.bySize).reduce((t, v) => t + v.lb, 0);

export function flagChips(flags) {
  if (!flags.length) return '';
  return `<ul class="chips" aria-label="Things to check">${flags.map((f) => `<li class="chip"><span class="chip-i" aria-hidden="true">!</span><span>${esc(f)}</span></li>`).join('')}</ul>`;
}

export function resultsHtml(res, area) {
  const head = `<h2 id="resTitle">${esc(area.name)}</h2>`;
  const todo = res.messages.length ? `<ul class="todo">${res.messages.map((m) => `<li>${esc(m)}</li>`).join('')}</ul>` : '';
  if (!res.outline) {
    const extrasLb = areaPounds(res);
    return `${head}<p class="empty">Add the sides of the shape and the area and weight appear here.</p>${todo}${extrasLb ? `<p class="hint">Loose bars so far: ${fmt0(extrasLb)} lb.</p>` : ''}${flagChips(res.flags)}${res.sections.extras.length ? `<details class="math"><summary>Show the math</summary>${mathSections(res)}</details>` : ''}`;
  }
  const lb = areaPounds(res);
  const A = res.A ? fmt0(res.A.lb) : '-';
  const B = res.B ? fmt0(res.B.lb) : '-';
  const methods = res.A ? `<div class="seg methods" role="radiogroup" aria-label="Which method feeds the totals">
    <button type="button" role="radio" aria-checked="${res.chosen === 'A'}" data-act="method" data-v="A"><span>Rate + laps</span><b>${A} lb</b></button>
    <button type="button" role="radio" aria-checked="${res.chosen === 'B'}" data-act="method" data-v="B"${res.B ? '' : ' disabled'}><span>Bar by bar</span><b>${B} lb</b></button></div>
    <p class="hint">Rate + laps multiplies the net area by pounds per square foot, then adds the laps. Bar by bar counts every bar across the real shape. The one you pick feeds the totals.</p>` : '';
  return `${head}${todo}
<div class="hero-nums">
  <div class="num"><span class="k">Net area</span><span class="v">${fmt2(res.net)}</span><span class="u">sf</span></div>
  <div class="num main"><span class="k">Rebar weight</span><span class="v">${fmt0(lb)}</span><span class="u">lb</span><span class="s">${fmt2(lb / 2000)} tons</span>${looseLb(res) > 0 ? `<span class="s inc">includes ${fmt0(looseLb(res))} lb of loose bars</span>` : ''}</div>
</div>
${methods}${flagChips(res.flags)}
<details class="math"><summary>Show the math</summary>${mathSections(res)}</details>`;
}

export function totalsHtml(calc) {
  const withRows = calc.areas.filter((a) => areaPounds(a) > 0);
  const byArea = calc.areas.length > 1 ? `<ul class="byarea">${calc.areas.map((a) => `<li><span>${esc(a.name)}</span><b>${fmt0(areaPounds(a))} lb</b></li>`).join('')}</ul>` : '';
  const table = calc.rows.length ? `<table class="sizes"><thead><tr><th scope="col">Bar</th><th scope="col" class="n">Length (LF)</th><th scope="col" class="n">Pounds</th></tr></thead><tbody>
    ${calc.rows.map((r) => `<tr><th scope="row">${esc(r.size)}</th><td class="n">${fmt1(r.lf)}</td><td class="n">${fmt1(r.lb)}</td></tr>`).join('')}
    ${calc.waste.pct > 0 ? `<tr class="sub"><th scope="row">Waste ${esc(calc.waste.pct)}%</th><td class="n">${fmt1(calc.waste.lf)}</td><td class="n">${fmt1(calc.waste.lb)}</td></tr>` : ''}
    <tr class="tot"><th scope="row">Total</th><td class="n">${fmt1(calc.total.lf)}</td><td class="n">${fmt1(calc.total.lb)}</td></tr></tbody></table>` : '<p class="empty">Totals appear once an area has a shape and bars.</p>';
  void withRows;
  return `<h2>Whole job</h2>
<div class="hero-nums">
  <div class="num main"><span class="k">Total rebar</span><span class="v">${fmt0(calc.total.lb)}</span><span class="u">lb</span><span class="s">${fmt2(calc.tons)} tons (2,000 lb)</span></div>
</div>
${byArea}${table}${calc.waste.pct > 0 ? '' : '<p class="hint">Waste is set to 0%. Change it in Settings if you add scrap.</p>'}${flagChips(calc.flags)}`;
}

// ---------------------------------------------------------------- settings
export function settingsHtml(job) {
  const s = job.settings;
  const rows = Object.keys(BARS).map((size) => {
    const b = s.bars[size];
    const cell = (f, label, mode) => `<td><input type="text" inputmode="${mode}" autocomplete="off" data-b="bar.${size}.${f}" data-check="num" value="${esc(b[f])}" aria-label="${size} ${label}"><span class="err" data-err="bar:${size}:${f}" aria-live="polite"></span></td>`;
    return `<tr><th scope="row">${size}</th>${cell('dia', 'diameter in inches', 'decimal')}${cell('wplf', 'pounds per foot', 'decimal')}${cell('lap', 'lap length in inches', 'decimal')}</tr>`;
  }).join('');
  return `<summary>Settings: stock bar length, waste, lap lengths</summary>
<div class="settings-body">
  <div class="two">
    ${field({ label: 'Stock bar length', tipText: 'How long the bars are when they arrive. Runs longer than this need laps.', b: 'set.stockText', value: s.stockText, check: 'num', mode: 'decimal', placeholder: 'feet', unit: 'ft' })}
    ${field({ label: 'Waste', tipText: 'Extra added to every total for scrap and cut-offs. Leave at 0 to match a plain takeoff.', b: 'set.wasteText', value: s.wasteText, check: 'num', mode: 'decimal', placeholder: 'percent', unit: '%' })}
  </div>
  <h3>Bar table and lap lengths</h3>
  <p class="hint">Standard A615 sizes. Lap defaults: #3, #4 and #5 are 60 in; #6 and larger are 96 bar diameters rounded up (#6 72 in, #7 84 in, #8 96 in). Change any number.</p>
  <div class="tablewrap"><table class="bartable"><thead><tr><th scope="col">Bar</th><th scope="col">Diameter (in)</th><th scope="col">Weight (lb/ft)</th><th scope="col">Lap (in)</th></tr></thead><tbody>${rows}</tbody></table></div>
  <button type="button" class="btn" data-act="resetBars">Reset to standard values</button>
</div>`;
}

// ---------------------------------------------------------------- print sheet
export function printHtml(job, calc, planFor) {
  const date = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  const areas = calc.areas.map((res, i) => {
    const area = job.areas[i];
    const sides = res.sides.length ? `<p class="sides">Sides: ${res.sides.map((s) => `${s.letter} ${esc(s.row.dir === 'ANG' ? `${s.row.angText} deg` : { R: 'right', U: 'up', L: 'left', D: 'down' }[s.row.dir])} ${esc(s.row.lenText || '?')}${s.row.curve !== 'none' ? ` (curves ${s.row.curve})` : ''}`).join('; ')}</p>` : '';
    return `<section class="p-area"><h2>${esc(area.name)}</h2>${planFor(area, res)}${sides}
      ${res.outline ? `<p class="p-nums">Net area <b>${fmt2(res.net)} sf</b> &middot; Rebar <b>${fmt0(areaPounds(res))} lb</b> (${fmt2(areaPounds(res) / 2000)} tons${looseLb(res) > 0 ? `, includes ${fmt0(looseLb(res))} lb of loose bars` : ''})</p>` : ''}
      ${mathSections(res)}${res.flags.length ? `<h4>Things to check</h4><ul>${res.flags.map((f) => `<li>${esc(f)}</li>`).join('')}</ul>` : ''}</section>`;
  }).join('');
  return `<h1>Rebar takeoff${job.name ? `: ${esc(job.name)}` : ''}</h1><p class="p-date">${esc(date)}</p>${areas}<section class="p-area">${totalsHtml(calc)}</section>`;
}
