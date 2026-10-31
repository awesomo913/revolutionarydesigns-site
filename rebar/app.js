// app.js - the page itself: state, events, rendering. Math lives in rebar-math.js / calc.js,
// HTML strings in views.js, drawing in plan-svg.js, photo tracing in photo.js.
// Everything stays in this browser; there are no network requests.
import { parseFtIn, parseSignedFtIn, parseInches, formatFtIn } from './rebar-math.js';
import {
  newJob, newArea, newRow, newCutout, newExtra, computeJob, closingSide, buildCsv, exampleJob, isEmptyJob,
  defaultBarsText, num, fmt0, fmt2,
} from './calc.js';
import { estimateFromPhoto } from './photo-geom.js';
import { renderPlan, planFromCalc, planFromSketch, planFromPartial, emptyPlan } from './plan-svg.js';
import * as V from './views.js';
import { createPhotoTool } from './photo.js';
import { loadAutosave, saveAutosave, downloadText, readJobFile, safeFileName, PAUSED_MESSAGE } from './store.js';

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

let job;
let calc = null;
let photoTool = null;
let saveTimer = null;
const ui = {
  step: 'shape', started: false, showBars: false, quickOpen: false, photoOpen: false, pendingFocus: null,
  quick: { rect: { w: '', l: '' }, ell: { w: '', l: '', nw: '', nl: '' } },
  storageOk: true, storageMsg: '', autosavePaused: false,
};
const photoCard = document.createElement('details');
const SMOOTH = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
const NEXT_DIR = { R: 'U', U: 'L', L: 'D', D: 'R', ANG: 'R' };

const activeArea = () => job.areas.find((a) => a.id === job.activeId) || job.areas[0];
const areaCalc = () => calc.areas[job.areas.indexOf(activeArea())];

// ---------------------------------------------------------------- messages
function notify(msg, kind = 'info') {
  const box = $('#notice');
  if (!msg || kind === 'clear') { box.innerHTML = ''; return; }
  if (kind === 'error') console.error('[rebar]', msg);
  box.innerHTML = `<div class="notice ${kind}" role="${kind === 'error' ? 'alert' : 'status'}"><span>${V.esc(msg)}</span><button type="button" class="icon" data-act="dismiss" aria-label="Dismiss this message">&times;</button></div>`;
}

// ---------------------------------------------------------------- bindings (data-b="where it is stored")
function resolve(key) {
  const p = key.split('.');
  const a = activeArea();
  const find = (list, id) => (list || []).find((x) => x.id === id);
  switch (p[0]) {
    case 'job': return [job, p[1]];
    case 'set': return [job.settings, p[1]];
    case 'bar': return [job.settings.bars[p[1]], p[2]];
    case 'area': return [a, p[1]];
    case 'reb': return [a.rebar, p[1]];
    case 'step': return [find(a.steps, p[1]), p[2]];
    case 'cut': return [find(a.cutouts, p[1]), p[2]];
    case 'cstep': { const c = find(a.cutouts, p[1]); return [c && find(c.steps, p[2]), p[3]]; }
    case 'ext': return [find(a.extras, p[1]), p[2]];
    default: return [null, null];
  }
}

function applyBinding(el) {
  const key = el.dataset.b;
  const [obj, prop] = resolve(key);
  if (!obj || !prop) { console.error('binding not found', key); return false; }
  let v = el.type === 'checkbox' ? el.checked : el.value;
  if (key === 'reb.mats') v = Number(v);
  obj[prop] = v;
  if (prop === 'lenText' && obj.est) { obj.est = false; el.closest('.field')?.querySelector('.est-tag')?.remove(); }
  if ((prop === 'sxText' || prop === 'syText') && obj.est) { obj.est = false; el.closest('.cut-card')?.querySelector('.est-tag')?.remove(); }
  return true;
}

// ---------------------------------------------------------------- focus handling across re-renders
function focusKeyOf(el) {
  if (!el || !el.dataset) return null;
  if (el.dataset.b) return `b:${el.dataset.b}`;
  if (el.dataset.q) return `q:${el.dataset.q}`;
  if (el.dataset.act) return `a:${el.dataset.act}|${el.dataset.id || ''}|${el.dataset.cut || ''}|${el.dataset.v || ''}`;
  return null;
}
function findByKey(k) {
  if (!k) return null;
  const kind = k[0];
  const rest = k.slice(2);
  if (kind === 'b') return $$('[data-b]').find((e) => e.dataset.b === rest);
  if (kind === 'q') return $$('[data-q]').find((e) => e.dataset.q === rest);
  return $$('[data-act]').find((e) => focusKeyOf(e) === k);
}

function withFocus(fn) {
  const el = document.activeElement;
  const key = ui.pendingFocus || focusKeyOf(el);
  const caret = !ui.pendingFocus && el && typeof el.selectionStart === 'number' ? [el.selectionStart, el.selectionEnd] : null;
  const wasPending = !!ui.pendingFocus;
  ui.pendingFocus = null;
  fn();
  const target = findByKey(key);
  if (target) {
    target.focus({ preventScroll: !wasPending });
    if (caret && typeof target.setSelectionRange === 'function') { try { target.setSelectionRange(caret[0], caret[1]); } catch (e) { /* not a text field */ } }
    if (wasPending) target.scrollIntoView({ block: 'center', behavior: SMOOTH });
  }
}

// ---------------------------------------------------------------- rendering
const STEP_PANELS = { shape: '#panelShape', cuts: '#panelCuts', rebar: '#panelRebar', results: '#panelResults' };

function renderChrome() {
  const empty = !ui.started && isEmptyJob(job);
  $('#hero').hidden = !empty;
  $('#work').hidden = empty;
  $('#work').dataset.step = ui.step;
  $('#areaChips').innerHTML = job.areas.map((a) =>
    `<button type="button" class="areachip" data-act="selArea" data-id="${a.id}" aria-pressed="${a.id === job.activeId}">${V.esc(a.name || 'Untitled')}</button>`).join('');
  $$('#stepper [data-act="step"]').forEach((b) => {
    const on = b.dataset.v === ui.step;
    b.classList.toggle('on', on);
    if (on) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current');
  });
  for (const [step, sel] of Object.entries(STEP_PANELS)) $(sel).hidden = step !== ui.step;
  const note = $('#saveNote');
  note.textContent = ui.storageMsg;
  note.classList.toggle('warn', !ui.storageOk);
}

function syncInputs() {
  $('#jobName').value = job.name;
  $('#areaName').value = activeArea().name;
}

function renderPanels() {
  withFocus(() => {
    const a = activeArea();
    const res = calc ? areaCalc() : null;
    ui.photoOpen = photoCard.open;
    if (ui.step === 'shape') {
      $('#panelShape').innerHTML = V.shapeHtml(a, ui);
      $('#photoSlot').appendChild(photoCard);
    } else if (ui.step === 'cuts') {
      $('#panelCuts').innerHTML = V.cutoutsHtml(a);
    } else if (ui.step === 'rebar') {
      $('#panelRebar').innerHTML = V.rebarHtml(a, res);
    } else {
      $('#panelResults').innerHTML = V.wrapHtml();
    }
    renderChrome();
  });
}

function renderSettings() {
  $('#settings').innerHTML = V.settingsHtml(job);
}

const CHECKS = {
  ft: (t) => { const v = parseFtIn(t); return Number.isNaN(v) || v <= 0 ? V.BAD.ft : ''; },
  sft: (t) => (Number.isNaN(parseSignedFtIn(t)) ? V.BAD.sft : ''),
  in: (t) => (Number.isNaN(parseInches(t)) ? V.BAD.in : ''),
  num: (t) => (Number.isNaN(num(t)) ? V.BAD.num : ''),
  int: (t) => { const n = num(t); return Number.isInteger(n) && n >= 1 ? '' : V.BAD.int; },
};

function updateErrors(res) {
  const stats = {};
  Object.assign(stats, res.rowStatus);
  const a = activeArea();
  a.cutouts.forEach((c, k) => { if (res.cutouts[k].stats) c.steps.forEach((r, i) => { stats[r.id] = res.cutouts[k].stats[i]; }); });
  for (const el of $$('[data-err]')) {
    const [kind, id] = el.dataset.err.split(':');
    let msg = '';
    if (kind === 'len' || kind === 'ang' || kind === 'curve') msg = (stats[id] && stats[id].errors[kind]) || '';
    else if (kind === 'cut') {
      const k = a.cutouts.findIndex((c) => c.id === id);
      const r = res.cutouts[k];
      msg = r && r.error ? `This cutout ${r.error}. It is not subtracted until then.` : '';
    }
    el.textContent = msg;
    const input = el.closest('.field')?.querySelector('input');
    if (input && kind !== 'cut') input.setAttribute('aria-invalid', msg ? 'true' : 'false');
  }
  for (const input of $$('input[data-check]')) {
    const t = input.value.trim();
    const msg = t ? CHECKS[input.dataset.check](t) : '';
    const err = input.closest('.field')?.querySelector('.err') || input.parentElement.querySelector('.err');
    if (err) err.textContent = msg;
    input.setAttribute('aria-invalid', msg ? 'true' : 'false');
  }
}

const planWidth = () => Math.floor($('#planBox').clientWidth) || 640;

function planHtmlFor(area, res, opts) {
  let model;
  if (res.outline) model = planFromCalc(res, { showBars: opts.showBars });
  else if (area.sketch && area.sketch.length === area.steps.length && area.steps.length >= 3) model = planFromSketch(area, res);
  else model = planFromPartial(res);
  if (!model) return emptyPlan(area.steps.length ? 'Type the first side length to start the drawing.' : 'Your drawing appears here as you add sides.');
  return renderPlan(model, { width: opts.width });
}

function legendHtml(area, res) {
  const items = area.cutouts.map((c, k) => {
    const r = res.cutouts[k];
    const name = V.esc(r.name);
    const note = r.quick ? ' (count only, not drawn)' : r.error ? ' (not finished)' : '';
    return `<li><span class="ctag">C${k + 1}</span> ${name}${note}</li>`;
  }).join('');
  return items ? `<ul class="legend">${items}</ul>` : '';
}

function renderDrawing() {
  const a = activeArea();
  const res = areaCalc();
  $('#planBox').innerHTML = planHtmlFor(a, res, { width: planWidth(), showBars: ui.showBars });
  $('#planLegend').innerHTML = legendHtml(a, res);
  $('#barsToggle').hidden = !res.layout;
}

function renderOutputs() {
  calc = computeJob(job);
  const a = activeArea();
  const res = areaCalc();
  renderDrawing();
  $('#resultsBox').innerHTML = V.resultsHtml(res, a);
  $('#totalsBox').innerHTML = V.totalsHtml(calc);
  $('#totalsBox').hidden = calc.rows.length === 0; // nothing to total yet
  const cb = $('#closureBox');
  if (cb) cb.innerHTML = V.closureHtml(a, res);
  const eb = $('#estimateBox');
  if (eb) eb.innerHTML = V.estimateHtml(a, res);
  const phrase = $('#rebarPhrase');
  if (phrase) {
    const r = a.rebar;
    phrase.textContent = `${r.size} @ ${r.spacing2On && r.spacing2Text ? `${r.spacingText || '?'}" and ${r.spacing2Text}" oc` : `${r.spacingText || '?'}" oc each way`}, ${r.mats} mat${r.mats > 1 ? 's' : ''}`;
  }
  updateErrors(res);
  // stepper marks and the phone summary bar
  const mark = (step, done) => $(`#stepper [data-v="${step}"]`)?.classList.toggle('done', done);
  mark('shape', !!res.outline && res.outline.closureGap < 1 / 24);
  mark('cuts', a.cutouts.length > 0 && res.cutouts.every((c) => !c.error));
  mark('rebar', !!res.chosen);
  mark('results', !!res.chosen);
  const mini = $('#miniBar');
  mini.hidden = !res.outline || ui.step === 'results';
  if (res.outline) {
    const lb = V.areaPounds(res);
    mini.innerHTML = `<span><span class="k">Net</span> <b>${fmt2(res.net)} sf</b></span><span><span class="k">Rebar</span> <b>${fmt0(lb)} lb</b></span><button type="button" class="btn primary" data-act="step" data-v="results">Results</button>`;
  }
  if (photoTool) photoTool.refresh();
}

function renderAll() {
  renderChrome();
  syncInputs();
  renderSettings();
  calc = computeJob(job);
  renderPanels();
  renderOutputs();
}

// ---------------------------------------------------------------- saving
function saveNow() {
  clearTimeout(saveTimer);
  saveTimer = null;
  if (ui.autosavePaused) {
    ui.storageOk = false;
    ui.storageMsg = PAUSED_MESSAGE;
    const paused = $('#saveNote');
    paused.textContent = ui.storageMsg;
    paused.classList.add('warn');
    return;
  }
  const r = saveAutosave(job);
  ui.storageOk = r.ok;
  ui.storageMsg = r.ok ? `Autosaved on this device at ${new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}. Clearing browser data wipes it, so save a job file for a copy.` : r.error;
  const note = $('#saveNote');
  note.textContent = ui.storageMsg;
  note.classList.toggle('warn', !r.ok);
}
function saveSoon() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(saveNow, 400);
}

// ---------------------------------------------------------------- actions
function seedRows() {
  return ['R', 'U', 'L', 'D'].map((d) => newRow(d));
}

function addRowTo(list) {
  const last = list[list.length - 1];
  const row = newRow(last ? NEXT_DIR[last.dir] : 'R');
  list.push(row);
  return row;
}

function listFor(cutId) {
  const a = activeArea();
  return cutId ? a.cutouts.find((c) => c.id === cutId).steps : a.steps;
}
const lenKey = (row, cutId) => (cutId ? `b:cstep.${cutId}.${row.id}.lenText` : `b:step.${row.id}.lenText`);

function quickShape(which) {
  const q = ui.quick[which];
  const read = (t) => parseFtIn(t);
  const err = (m) => { $(`[data-qerr="${which}"]`).textContent = m; };
  const vals = Object.fromEntries(Object.entries(q).map(([k, t]) => [k, read(t)]));
  if (Object.values(vals).some((v) => Number.isNaN(v) || v <= 0)) { err(`Fill in every box with a length like 40' or 27'-10 1/2".`); return; }
  let steps;
  if (which === 'rect') {
    steps = [['R', vals.w], ['U', vals.l], ['L', vals.w], ['D', vals.l]];
  } else {
    if (vals.nw >= vals.w || vals.nl >= vals.l) { err('The notch has to be smaller than the overall width and length.'); return; }
    steps = [['R', vals.w], ['U', vals.l - vals.nl], ['L', vals.nw], ['U', vals.nl], ['L', vals.w - vals.nw], ['D', vals.l]];
  }
  const a = activeArea();
  if (a.steps.some((r) => r.lenText.trim()) && !window.confirm('Replace the sides you already typed?')) return;
  a.steps = steps.map(([d, v]) => ({ ...newRow(d), lenText: formatFtIn(v) }));
  a.sketch = null;
  ui.quickOpen = false;
  err('');
  saveSoon();
  renderPanels();
  renderOutputs();
}

function usePhoto({ rows, sketch, cutouts }) {
  const a = activeArea();
  const oldCuts = a.cutouts.map((c, k) => [c, k]).filter(([c]) => c.kind === 'traced' && c.sketch);
  const typed = a.steps.filter((r) => r.lenText.trim()).length;
  if (typed || oldCuts.length) {
    const parts = [];
    if (typed) parts.push(`the ${typed} side length${typed === 1 ? '' : 's'} you typed`);
    if (oldCuts.length) parts.push(`the cutouts traced from the earlier photo (${oldCuts.map(([c, k]) => `C${k + 1}${c.name ? ` ${c.name}` : ''}`).join(', ')}) and anything typed into them`);
    if (!window.confirm(`Use the photo's sides? This replaces ${parts.join(' and ')}.`)) return;
  }
  a.steps = rows;
  a.sketch = sketch;
  a.cutouts = a.cutouts.filter((c) => !(c.kind === 'traced' && c.sketch));
  cutouts.forEach((c) => { const cut = newCutout('traced'); cut.steps = c.rows; cut.sketch = c.sketch; a.cutouts.push(cut); });
  ui.pendingFocus = lenKey(rows[0]);
  notify(`Loaded ${rows.length} sides${cutouts.length ? ` and ${cutouts.length} cutout${cutouts.length > 1 ? 's' : ''}` : ''} from the photo. Type each length; the letters match the photo.`, 'info');
  saveSoon();
  renderPanels();
  renderOutputs();
}

function estimateSides() {
  const a = activeArea();
  const r = estimateFromPhoto(a);
  if (!r.ok) { notify(r.reason, 'warn'); return; }
  let count = 0;
  r.outline.forEach((t, i) => { if (t) { a.steps[i].lenText = t; a.steps[i].est = true; count++; } });
  r.cutouts.forEach((ec) => {
    const c = a.cutouts.find((x) => x.id === ec.id);
    ec.rows.forEach((t, i) => { if (t) { c.steps[i].lenText = t; c.steps[i].est = true; count++; } });
    if (ec.sxText !== null || ec.syText !== null) {
      if (ec.sxText !== null) c.sxText = ec.sxText;
      if (ec.syText !== null) c.syText = ec.syText;
      c.est = true;
      count++;
    }
  });
  notify(`Estimated ${count} measurement${count === 1 ? '' : 's'} using side ${r.refLetter} as the scale. They are marked "check": a photo taken at an angle distorts lengths.`, 'warn');
  saveSoon();
  renderPanels();
  renderOutputs();
}

const ACTIONS = {
  dismiss: () => notify('', 'clear'),
  startPhoto() {
    ui.started = true;
    ui.step = 'shape';
    photoCard.open = true;
    renderAll();
    photoTool.openPicker(true);
  },
  startType() {
    ui.started = true;
    ui.step = 'shape';
    ui.quickOpen = true;
    const a = activeArea();
    if (!a.steps.length) a.steps.push(newRow('R'));
    ui.pendingFocus = lenKey(a.steps[0]);
    saveSoon();
    renderAll();
  },
  example() {
    job = exampleJob();
    ui.started = true;
    ui.step = 'results';
    saveSoon();
    renderAll();
    notify('Example loaded: an L-shaped slab with an old footing and six piers. Change anything, or start over from the Job file menu.', 'info');
  },
  openFile: () => $('#openInput').click(),
  step(el) {
    ui.step = el.dataset.v;
    renderPanels();
    renderOutputs();
    window.scrollTo({ top: 0, behavior: SMOOTH });
  },
  selArea(el) {
    job.activeId = el.dataset.id;
    saveSoon();
    renderAll();
  },
  addArea() {
    const a = newArea(`Area ${job.areas.length + 1}`);
    job.areas.push(a);
    job.activeId = a.id;
    ui.step = 'shape';
    saveSoon();
    renderAll();
    $('.areaedit').open = true;
    $('#areaName').focus();
    $('#areaName').select();
  },
  delArea() {
    const a = activeArea();
    if (!window.confirm(`Delete "${a.name}" and everything in it?`)) return;
    if (job.areas.length === 1) job.areas[0] = newArea('Area 1');
    else job.areas = job.areas.filter((x) => x.id !== a.id);
    job.activeId = job.areas[0].id;
    saveSoon();
    renderAll();
  },
  addRow(el) {
    const list = listFor(el.dataset.cut);
    const row = addRowTo(list);
    ui.pendingFocus = lenKey(row, el.dataset.cut);
    saveSoon();
    renderPanels();
    renderOutputs();
  },
  delRow(el) {
    const list = listFor(el.dataset.cut);
    const i = list.findIndex((r) => r.id === el.dataset.id);
    if (i >= 0) list.splice(i, 1);
    saveSoon();
    renderPanels();
    renderOutputs();
  },
  dir(el) {
    const row = listFor(el.dataset.cut).find((r) => r.id === el.dataset.id);
    row.dir = el.dataset.v;
    saveSoon();
    renderPanels();
    renderOutputs();
  },
  closeIt() {
    const a = activeArea();
    const fix = closingSide(a.steps);
    if (!fix) return;
    Object.assign(a.steps[a.steps.length - 1], { dir: fix.dir, angText: fix.angText, lenText: fix.lenText, est: false });
    saveSoon();
    renderPanels();
    renderOutputs();
  },
  estimate: estimateSides,
  addCut(el) {
    const c = newCutout(el.dataset.v);
    if (c.kind === 'traced') c.steps = seedRows();
    activeArea().cutouts.push(c);
    ui.pendingFocus = `b:cut.${c.id}.name`;
    saveSoon();
    renderPanels();
    renderOutputs();
  },
  delCut(el) {
    const a = activeArea();
    a.cutouts = a.cutouts.filter((c) => c.id !== el.dataset.id);
    saveSoon();
    renderPanels();
    renderOutputs();
  },
  cutKind(el) {
    const c = activeArea().cutouts.find((x) => x.id === el.dataset.id);
    c.kind = el.dataset.v;
    if (c.kind === 'traced' && !c.steps.length) c.steps = seedRows();
    saveSoon();
    renderPanels();
    renderOutputs();
  },
  addExtra() {
    const e = newExtra();
    activeArea().extras.push(e);
    ui.pendingFocus = `b:ext.${e.id}.lenText`;
    saveSoon();
    renderPanels();
    renderOutputs();
  },
  delExtra(el) {
    const a = activeArea();
    a.extras = a.extras.filter((e) => e.id !== el.dataset.id);
    saveSoon();
    renderPanels();
    renderOutputs();
  },
  mats(el) { activeArea().rebar.mats = Number(el.dataset.v); saveSoon(); renderPanels(); renderOutputs(); },
  houseUse(el) { activeArea().rebar.houseUse = el.dataset.v; saveSoon(); renderPanels(); renderOutputs(); },
  method(el) { activeArea().method = el.dataset.v; saveSoon(); renderOutputs(); },
  resetBars() {
    job.settings.bars = defaultBarsText();
    saveSoon();
    renderSettings();
    renderOutputs();
  },
  saveFile() {
    downloadText(safeFileName(job.name, 'json'), JSON.stringify(job, null, 2), 'application/json');
    ui.autosavePaused = false; // a copy now exists outside the browser, so autosave may resume
    saveSoon();
    notify('Download started. If nothing shows up in your downloads, your browser may have blocked it. Open the file later with Job file > Open a job file.', 'info');
  },
  csv() {
    calc = computeJob(job);
    downloadText(safeFileName(job.name, 'csv'), buildCsv(job, calc), 'text/csv;charset=utf-8');
    notify('Download started. If nothing shows up in your downloads, your browser may have blocked it.', 'info');
  },
  print() { buildPrintSheet(); window.print(); },
  newJob() {
    if (!window.confirm('Start a new blank job? The current one stays saved only if you saved a job file.')) return;
    job = newJob();
    ui.started = false;
    ui.autosavePaused = false;
    ui.step = 'shape';
    saveSoon();
    renderAll();
  },
};

function buildPrintSheet() {
  calc = computeJob(job);
  $('#printSheet').innerHTML = V.printHtml(job, calc, (ar, r) => planHtmlFor(ar, r, { width: 640, showBars: false }));
}

// ---------------------------------------------------------------- events
document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-act]');
  if (!el || el.disabled) return;
  const fn = ACTIONS[el.dataset.act];
  if (!fn) { console.error('unknown action', el.dataset.act); return; }
  fn(el);
  const menu = el.closest('details.menu');
  if (menu) menu.removeAttribute('open');
});

document.addEventListener('input', (e) => {
  const el = e.target;
  if (el.tagName === 'SELECT' || el.type === 'checkbox' || el.type === 'file') return;
  if (el.dataset.q) { const [which, k] = el.dataset.q.split('.'); ui.quick[which][k] = el.value; return; }
  if (!el.dataset.b) return;
  if (!applyBinding(el)) return;
  if (el.dataset.b === 'job.name') { saveSoon(); return; }
  if (el.dataset.b === 'area.name') { renderChrome(); }
  saveSoon();
  renderOutputs();
});

document.addEventListener('change', (e) => {
  const el = e.target;
  if (el.id === 'showBars') { ui.showBars = el.checked; renderDrawing(); return; }
  if (el.id === 'openInput') {
    const file = el.files && el.files[0];
    el.value = '';
    if (!file) return;
    readJobFile(file).then((j) => {
      if (!isEmptyJob(job) && !window.confirm(`Open "${file.name}"? It replaces the job on this page${job.name ? ` ("${job.name}")` : ''}. Save a job file first if you want to keep this one.`)) return;
      job = j;
      ui.started = true;
      ui.step = 'shape';
      saveSoon();
      renderAll();
      notify(`Opened "${file.name}".`, 'info');
    }).catch((err) => notify(err.message, 'error'));
    return;
  }
  if (!el.dataset.b || !(el.tagName === 'SELECT' || el.type === 'checkbox')) return;
  if (!applyBinding(el)) return;
  saveSoon();
  if (el.hasAttribute('data-rerender')) renderPanels();
  renderOutputs();
});

document.addEventListener('submit', (e) => {
  const form = e.target.closest('[data-form]');
  if (!form) return;
  e.preventDefault();
  quickShape(form.dataset.form);
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') $$('details.menu[open]').forEach((m) => m.removeAttribute('open'));
  const el = e.target;
  if (e.key !== 'Enter' || el.dataset.role !== 'len') return;
  e.preventDefault();
  const cutId = el.dataset.cut || null;
  const list = listFor(cutId);
  const i = list.findIndex((r) => r.id === el.dataset.id);
  if (i < 0) return;
  if (i < list.length - 1) { findByKey(lenKey(list[i + 1], cutId))?.focus(); return; }
  ACTIONS.addRow({ dataset: { cut: cutId || '' } });
});

window.addEventListener('beforeprint', buildPrintSheet);
window.addEventListener('beforeunload', () => { if (saveTimer) saveNow(); });
window.addEventListener('error', (e) => {
  if (/ResizeObserver loop/.test(e.message || '')) return; // harmless browser notice, not a fault
  notify(`Something went wrong on the page: ${e.message}. Your job is still saved; reload to continue.`, 'error');
});
window.addEventListener('unhandledrejection', (e) => notify(`Something went wrong: ${e.reason && e.reason.message ? e.reason.message : e.reason}`, 'error'));

if (typeof ResizeObserver === 'function') {
  let lastW = 0;
  new ResizeObserver(() => {
    window.requestAnimationFrame(() => {
      const w = Math.floor($('#planBox').clientWidth);
      if (calc && w && Math.abs(w - lastW) > 8) { lastW = w; renderDrawing(); }
    });
  }).observe($('#planBox'));
}

// ---------------------------------------------------------------- start
function boot() {
  const loaded = loadAutosave();
  job = loaded.job || newJob();
  ui.started = !isEmptyJob(job);
  ui.autosavePaused = !!loaded.pauseAutosave;
  ui.storageOk = loaded.available && !ui.autosavePaused;
  ui.storageMsg = ui.autosavePaused ? PAUSED_MESSAGE : loaded.available ? 'Autosave is on, in this browser only. Clearing browser data wipes it, so save a job file for a copy.' : loaded.error;

  photoCard.className = 'photo-card';
  photoCard.innerHTML = '<summary>Start from a photo</summary><div class="photo-root"></div>';
  photoTool = createPhotoTool($('.photo-root', photoCard), {
    notify,
    getOutlineLengths: () => activeArea().steps.map((r) => r.lenText.trim()),
    cutoutBase: () => activeArea().cutouts.filter((c) => !(c.kind === 'traced' && c.sketch)).length,
    onUse: usePhoto,
  });
  $('#hero').innerHTML = V.heroHtml();
  renderAll();
  if (loaded.error && loaded.available) notify(loaded.error, 'error');
  else if (!loaded.available) notify(loaded.error, 'warn');
}

boot();
