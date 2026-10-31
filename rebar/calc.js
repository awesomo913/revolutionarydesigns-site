// calc.js - turns the job the page stores into numbers, math lines and yellow flags. No DOM.
// All fields the user types are kept as TEXT in the job; this file reads them (and says what is wrong).
import {
  BARS, defaultLapIn, parseFtIn, parseSignedFtIn, parseInches, formatFtIn, wpsf, sagittaFrom, walk,
  regionArea, regionArcs, polygonArea, netArea, barLayout, translate, rectRegion, circleRegion,
  shapeProblem, dirToDegrees, isCcw,
} from './rebar-math.js';

export const SCHEMA = 'rebar-takeoff-job';
export const VERSION = 1;
export const CLOSURE_FLAG_FT = 0.5 / 12; // flag a closure gap bigger than 1/2"
export const CLOSED_FT = 1 / 192;        // a gap under 1/16" counts as closed (lengths are written to 1/16")
export const HOUSE_RATE_TOLERANCE = 0.02;
export const TON_LB = 2000;

export const uid = () => Math.random().toString(36).slice(2, 9);

// ---------------------------------------------------------------- number formatting
const nf = (digits) => new Intl.NumberFormat('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
const nf0 = nf(0), nf1 = nf(1), nf2 = nf(2), nf3 = nf(3);
export const fmt0 = (n) => nf0.format(n);
export const fmt1 = (n) => nf1.format(n);
export const fmt2 = (n) => nf2.format(n);
export const fmt3 = (n) => nf3.format(n);
export const sf = (n) => `${fmt2(n)} sf`;
export const lb = (n) => `${fmt1(n)} lb`;
export const lf = (n) => `${fmt1(n)} LF`;
export const ft = (n) => formatFtIn(n);

// A plain decimal typed into a number box. Blank or junk -> NaN.
export function num(text) {
  if (typeof text === 'number') return Number.isFinite(text) ? text : NaN;
  const s = String(text ?? '').trim().replace(/,/g, '');
  return /^-?\d+(\.\d+)?$|^-?\.\d+$/.test(s) ? Number(s) : NaN;
}

export function letter(i) {
  let s = '';
  let n = i;
  do { s = String.fromCharCode(65 + (n % 26)) + s; n = Math.floor(n / 26) - 1; } while (n >= 0);
  return s;
}
export const cutLetter = (k, i) => `${k + 1}${letter(i).toLowerCase()}`;

const DIR_WORD = { R: 'right', U: 'up', L: 'left', D: 'down' };
export const barNumber = (size) => Number(String(size).replace('#', ''));
const sortSizes = (a, b) => barNumber(a) - barNumber(b);

// ---------------------------------------------------------------- job shapes
export function defaultBarsText() {
  const out = {};
  for (const [size, b] of Object.entries(BARS)) out[size] = { dia: String(b.dia), wplf: String(b.wplf), lap: String(defaultLapIn(size)) };
  return out;
}

export function defaultSettings() {
  return { stockText: '40', wasteText: '0', bars: defaultBarsText() };
}

export const newRow = (dir = 'R') => ({ id: uid(), dir, angText: '', lenText: '', curve: 'none', curveBy: 'rise', curveText: '', est: false });

export function newCutout(kind = 'rect') {
  return {
    id: uid(), name: '', kind,
    xText: '', yText: '', wText: '', lText: '',
    cxText: '', cyText: '', dText: '',
    sxText: '', syText: '', steps: [], sketch: null, est: false,
    countText: '1', qShape: 'circle', qdText: '', qwText: '', qlText: '',
  };
}

export const newExtra = () => ({ id: uid(), size: '#4', lenText: '', qtyText: '1' });

export function newArea(name = 'Area 1') {
  return {
    id: uid(), name, steps: [], sketch: null, cutouts: [],
    rebar: { size: '#5', spacingText: '12', spacing2On: false, spacing2Text: '', mats: 1, coverText: '3', lapMode: 'exact', houseText: '', houseUse: 'house' },
    extras: [], method: 'A',
  };
}

export function newJob() {
  const area = newArea('Area 1');
  return { schema: SCHEMA, version: VERSION, name: '', settings: defaultSettings(), areas: [area], activeId: area.id };
}

// Checks a job read from a file or from autosave; fills anything missing so old/hand-edited files still open.
// Throws an Error with a plain-English message when the file is not a job at all.
export function sanitizeJob(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw new Error('That file is not a rebar takeoff job (it is not a JSON object).');
  if (raw.schema !== SCHEMA) throw new Error('That file is not a rebar takeoff job file (wrong "schema" marker).');
  if (!Number.isFinite(raw.version) || raw.version > VERSION) throw new Error('That job file was saved by a newer version of this page.');
  if (!Array.isArray(raw.areas)) throw new Error('That job file has no "areas" list.');
  const base = newJob();
  const s = raw.settings && typeof raw.settings === 'object' ? raw.settings : {};
  const settings = { stockText: str(s.stockText, '40'), wasteText: str(s.wasteText, '0'), bars: defaultBarsText() };
  for (const size of Object.keys(settings.bars)) {
    const b = s.bars && s.bars[size];
    if (b && typeof b === 'object') settings.bars[size] = { dia: str(b.dia, settings.bars[size].dia), wplf: str(b.wplf, settings.bars[size].wplf), lap: str(b.lap, settings.bars[size].lap) };
  }
  const areas = raw.areas.filter((a) => a && typeof a === 'object').map((a, i) => sanitizeArea(a, i));
  if (!areas.length) areas.push(base.areas[0]);
  const activeId = areas.some((a) => a.id === raw.activeId) ? raw.activeId : areas[0].id;
  return { schema: SCHEMA, version: VERSION, name: str(raw.name, ''), settings, areas, activeId };
}

const str = (v, d = '') => (typeof v === 'string' ? v : typeof v === 'number' ? String(v) : d);
const pick = (v, allowed, d) => (allowed.includes(v) ? v : d);
const id = (v) => (typeof v === 'string' && /^[A-Za-z0-9_-]{1,40}$/.test(v) ? v : uid());
const sketchOf = (v) => (Array.isArray(v) && v.every((p) => p && Number.isFinite(p.x) && Number.isFinite(p.y)) ? v.map((p) => ({ x: p.x, y: p.y })) : null);

function sanitizeRow(r) {
  const d = newRow();
  return {
    id: id(r.id), dir: pick(r.dir, ['R', 'U', 'L', 'D', 'ANG'], 'R'), angText: str(r.angText), lenText: str(r.lenText),
    curve: pick(r.curve, ['none', 'out', 'in'], 'none'), curveBy: pick(r.curveBy, ['rise', 'radius', 'arc'], 'rise'),
    curveText: str(r.curveText), est: r.est === true && d.est === false,
  };
}

function sanitizeArea(a, i) {
  const d = newArea(`Area ${i + 1}`);
  const rb = a.rebar && typeof a.rebar === 'object' ? a.rebar : {};
  const steps = Array.isArray(a.steps) ? a.steps.filter((r) => r && typeof r === 'object').map(sanitizeRow) : [];
  return {
    id: id(a.id), name: str(a.name, d.name) || d.name, steps, sketch: sketchOf(a.sketch),
    cutouts: Array.isArray(a.cutouts) ? a.cutouts.filter((c) => c && typeof c === 'object').map(sanitizeCutout) : [],
    rebar: {
      size: Object.keys(BARS).includes(rb.size) ? rb.size : d.rebar.size, spacingText: str(rb.spacingText, d.rebar.spacingText),
      spacing2On: rb.spacing2On === true, spacing2Text: str(rb.spacing2Text), mats: rb.mats === 2 ? 2 : 1,
      coverText: str(rb.coverText, d.rebar.coverText), lapMode: pick(rb.lapMode, ['exact', 'simple'], 'exact'),
      houseText: str(rb.houseText), houseUse: pick(rb.houseUse, ['house', 'math'], 'house'),
    },
    extras: Array.isArray(a.extras) ? a.extras.filter((e) => e && typeof e === 'object').map((e) => ({
      id: id(e.id), size: Object.keys(BARS).includes(e.size) ? e.size : '#4', lenText: str(e.lenText), qtyText: str(e.qtyText, '1'),
    })) : [],
    method: a.method === 'B' ? 'B' : 'A',
  };
}

function sanitizeCutout(c) {
  const d = newCutout();
  return {
    id: id(c.id), name: str(c.name), kind: pick(c.kind, ['rect', 'circle', 'traced', 'quick'], 'rect'),
    xText: str(c.xText), yText: str(c.yText), wText: str(c.wText), lText: str(c.lText),
    cxText: str(c.cxText), cyText: str(c.cyText), dText: str(c.dText),
    sxText: str(c.sxText), syText: str(c.syText),
    steps: Array.isArray(c.steps) ? c.steps.filter((r) => r && typeof r === 'object').map(sanitizeRow) : [],
    sketch: sketchOf(c.sketch), est: c.est === true,
    countText: str(c.countText, d.countText), qShape: pick(c.qShape, ['circle', 'rect'], 'circle'),
    qdText: str(c.qdText), qwText: str(c.qwText), qlText: str(c.qlText),
  };
}

// ---------------------------------------------------------------- settings
export function settingsCalc(settings) {
  const problems = [];
  let stockFt = num(settings.stockText);
  if (!(stockFt > 0)) { problems.push('Stock bar length is not a usable number, so 40 ft is being used.'); stockFt = 40; }
  let wastePct = 0;
  if (String(settings.wasteText ?? '').trim() !== '') {
    wastePct = num(settings.wasteText);
    if (!(wastePct >= 0)) { problems.push('Waste % is not a usable number, so 0% is being used.'); wastePct = 0; }
  }
  const table = {};
  const lapIn = {};
  for (const size of Object.keys(BARS)) {
    const src = (settings.bars && settings.bars[size]) || {};
    const dia = num(src.dia);
    const wplf = num(src.wplf);
    const lap = num(src.lap);
    if (!(dia > 0) || !(wplf > 0)) problems.push(`Bar ${size}: diameter or weight per foot is not a usable number, so the standard value is being used.`);
    if (!(lap >= 0)) problems.push(`Bar ${size}: lap length is not a usable number, so the standard lap is being used.`);
    table[size] = { dia: dia > 0 ? dia : BARS[size].dia, wplf: wplf > 0 ? wplf : BARS[size].wplf, area: BARS[size].area };
    lapIn[size] = lap >= 0 ? lap : defaultLapIn(size);
  }
  return { stockFt, wastePct, table, lapIn, problems };
}

// ---------------------------------------------------------------- one side of a walk
const BAD_LEN = `Can't read that. Try 27'-10 1/2" or 27-10.5`;

export function rowStatus(row) {
  const st = { dirDeg: NaN, len: NaN, bulge: 0, errors: {}, blank: false, pending: false, complete: false };
  if (row.dir === 'ANG') {
    const t = String(row.angText ?? '').trim();
    const a = num(t);
    if (!t) st.pending = true;
    else if (Number.isNaN(a)) st.errors.ang = 'Angle must be a number of degrees (0 = east, 90 = north)';
    else st.dirDeg = ((a % 360) + 360) % 360;
  } else {
    st.dirDeg = dirToDegrees(row.dir);
  }
  const t = String(row.lenText ?? '').trim();
  if (!t) st.blank = true;
  else {
    const v = parseFtIn(t);
    if (Number.isNaN(v) || v <= 0) st.errors.len = BAD_LEN;
    else st.len = v;
  }
  if (row.curve && row.curve !== 'none') {
    const ct = String(row.curveText ?? '').trim();
    if (!ct) st.pending = true;
    else {
      const v = parseFtIn(ct);
      const what = { rise: 'rise', radius: 'radius', arc: 'arc length' }[row.curveBy] || 'rise';
      if (Number.isNaN(v) || v <= 0) st.errors.curve = `Can't read that ${what}. Try 4'-6" or 4.5`;
      else if (row.curveBy === 'rise' || !row.curveBy) st.bulge = (row.curve === 'out' ? 1 : -1) * v;
      else if (!Number.isFinite(st.len)) st.pending = true;
      else {
        try {
          const h = sagittaFrom(row.curveBy === 'radius' ? { chord: st.len, radius: v } : { chord: st.len, arcLength: v });
          st.bulge = (row.curve === 'out' ? 1 : -1) * h;
        } catch (e) {
          st.errors.curve = e.message;
        }
      }
    }
  }
  st.complete = !Object.keys(st.errors).length && !st.blank && !st.pending && Number.isFinite(st.dirDeg) && Number.isFinite(st.len);
  return st;
}

// The last side that would make the walk end exactly where it started (the "close it for me" button).
// Needs every other side to be readable. Returns { dir, angText, lenText } or null.
export function closingSide(rows) {
  if (rows.length < 2) return null;
  const stats = rows.slice(0, -1).map(rowStatus);
  if (!stats.every((s) => s.complete)) return null;
  let x = 0;
  let y = 0;
  for (const s of stats) {
    const rad = (s.dirDeg * Math.PI) / 180;
    const c = { 0: [1, 0], 90: [0, 1], 180: [-1, 0], 270: [0, -1] }[s.dirDeg];
    x += s.len * (c ? c[0] : Math.cos(rad));
    y += s.len * (c ? c[1] : Math.sin(rad));
  }
  const len = Math.hypot(x, y);
  if (len < 1e-6) return null;
  const deg = (((Math.atan2(-y, -x) * 180) / Math.PI) % 360 + 360) % 360;
  const cardinal = { 0: 'R', 90: 'U', 180: 'L', 270: 'D' };
  const near = [0, 90, 180, 270, 360].find((c) => Math.abs(deg - c) < 1e-6);
  const key = near === 360 ? 0 : near;
  return key !== undefined ? { dir: cardinal[key], angText: '', lenText: formatFtIn(len) } : { dir: 'ANG', angText: String(Math.round(deg * 1000) / 1000), lenText: formatFtIn(len) };
}

export function dirText(row) {
  return row.dir === 'ANG' ? `${row.angText || '?'} deg` : DIR_WORD[row.dir];
}

// Builds a walk from rows when every row is readable; otherwise says why not.
function walkRows(rows, label) {
  const stats = rows.map(rowStatus);
  const problems = [];
  stats.forEach((s, i) => {
    const who = `${label}${letter(i)}`;
    if (Object.keys(s.errors).length) problems.push(`${who}: ${Object.values(s.errors)[0]}`);
    else if (s.blank) problems.push(`${who} needs a length`);
    else if (s.pending) problems.push(`${who} needs its curve or angle filled in`);
  });
  let result = null;
  if (!problems.length && rows.length >= 2) {
    const hasCurve = stats.some((s) => s.bulge);
    if (rows.length < 3 && !hasCurve) problems.push('A shape needs at least 3 straight sides (or 2 with a curve)');
    else result = walk(stats.map((s) => ({ dir: s.dirDeg, len: s.len, bulge: s.bulge })));
  } else if (!problems.length) {
    problems.push('Add the sides of the shape');
  }
  return { stats, problems, result };
}

// ---------------------------------------------------------------- math text helpers
function rectDims(region) {
  const { pts, bulges } = region;
  if (pts.length !== 4 || (bulges || []).some((b) => b)) return null;
  const xs = pts.map((p) => p.x);
  const ys = pts.map((p) => p.y);
  const w = Math.max(...xs) - Math.min(...xs);
  const l = Math.max(...ys) - Math.min(...ys);
  const axis = pts.every((p, i) => {
    const q = pts[(i + 1) % 4];
    return Math.abs(p.x - q.x) < 1e-9 || Math.abs(p.y - q.y) < 1e-9;
  });
  return axis ? { w, l } : null;
}

function grossMath(region, gross) {
  const r = rectDims(region);
  if (r) return `${ft(r.w)} x ${ft(r.l)} = ${sf(gross)}`;
  const poly = polygonArea(region.pts);
  const curved = gross - poly;
  if (Math.abs(curved) < 1e-9) return `${region.pts.length} corners (corner-to-corner formula) = ${sf(gross)}`;
  return `corners ${sf(poly)} ${curved < 0 ? '-' : '+'} curved sides ${sf(Math.abs(curved))} = ${sf(gross)}`;
}

const line = (label, math, value, extra = {}) => ({ label, math, value, ...extra });

// ---------------------------------------------------------------- one cutout
const POSITION_NEEDED = 'needs its position: how far from the start corner, across and up';

// A typed measurement: { blank } when empty, { bad } when unreadable (or not above 0 unless signed), else { v }.
function readDim(text, signed = false) {
  const t = String(text ?? '').trim();
  if (!t) return { blank: true };
  const v = signed ? parseSignedFtIn(t) : parseFtIn(t);
  return Number.isNaN(v) || (!signed && !(v > 0)) ? { bad: true } : { v };
}

// First thing wrong with a cutout's numbers, in plain words (null when they are all usable).
// pos / dims are lists of [label, readDim result].
function dimProblem(pos, dims) {
  if (pos.some(([, r]) => r.blank)) return POSITION_NEEDED;
  const blank = dims.filter(([, r]) => r.blank).map(([l]) => l);
  if (blank.length) return `needs its ${blank.join(' and ')}`;
  const bad = [...pos, ...dims].filter(([, r]) => r.bad).map(([l]) => l);
  if (bad.length) return `has a ${bad.join(' and ')} that can't be read (try 27'-10 1/2" or 27-10.5)`;
  return null;
}

const CROSSING = {
  crosses: 'has an outline that crosses itself (check the directions of its sides)',
  doubles: 'has an outline that runs over itself (check the directions of its sides)',
};

function cutoutCalc(c, index, label) {
  const name = (c.name || '').trim() || `Cutout ${index + 1}`;
  const out = { id: c.id, name, kind: c.kind, region: null, quick: null, error: null, flag: null, stats: null, letters: [] };
  const fail = (problem) => { if (problem) throw new Error(problem); };
  try {
    if (c.kind === 'rect') {
      const pos = [['across', readDim(c.xText, true)], ['up', readDim(c.yText, true)]];
      const dims = [['width', readDim(c.wText)], ['length', readDim(c.lText)]];
      fail(dimProblem(pos, dims));
      const [x, y, w, l] = [pos[0][1].v, pos[1][1].v, dims[0][1].v, dims[1][1].v];
      out.region = rectRegion(x, y, w, l);
      out.dimText = `${ft(w)} x ${ft(l)}`;
      out.area = w * l;
      out.math = `${ft(w)} x ${ft(l)} = ${sf(w * l)}`;
    } else if (c.kind === 'circle') {
      const pos = [['across', readDim(c.cxText, true)], ['up', readDim(c.cyText, true)]];
      const dims = [['diameter', readDim(c.dText)]];
      fail(dimProblem(pos, dims));
      const [cx, cy, d] = [pos[0][1].v, pos[1][1].v, dims[0][1].v];
      out.region = circleRegion(cx, cy, d);
      out.dimText = `dia ${ft(d)}`;
      out.area = (Math.PI * d * d) / 4;
      out.math = `pi x (${ft(d)} / 2)^2 = ${sf(out.area)}`;
    } else if (c.kind === 'traced') {
      const pos = [['across', readDim(c.sxText, true)], ['up', readDim(c.syText, true)]];
      fail(dimProblem(pos, []));
      const w = walkRows(c.steps, label);
      out.stats = w.stats;
      if (!w.result) throw new Error(`needs all its sides filled in (${w.problems[0]})`);
      const sx = pos[0][1].v;
      const sy = pos[1][1].v;
      const region = translate(w.result.region, sx, sy);
      out.walk = { path: w.result.path.map((p) => ({ x: p.x + sx, y: p.y + sy })), gap: w.result.closureGap };
      const bad = shapeProblem(region);
      if (bad) throw new Error(CROSSING[bad]); // flagged, and NOT subtracted
      out.region = region;
      out.area = regionArea(region);
      out.math = `${c.steps.length} sides = ${sf(out.area)}`;
      if (w.result.closureGap > CLOSURE_FLAG_FT) out.flag = `${name} does not close: it misses its start by ${ft(w.result.closureGap)}.`;
    } else {
      const count = num(c.countText);
      if (!(count >= 1) || !Number.isInteger(count)) throw new Error('needs a count (a whole number, 1 or more)');
      let each;
      let eachMath;
      if (c.qShape === 'rect') {
        const dims = [['width', readDim(c.qwText)], ['length', readDim(c.qlText)]];
        fail(dimProblem([], dims));
        each = dims[0][1].v * dims[1][1].v;
        eachMath = `${ft(dims[0][1].v)} x ${ft(dims[1][1].v)}`;
      } else {
        const dims = [['diameter', readDim(c.qdText)]];
        fail(dimProblem([], dims));
        each = (Math.PI * dims[0][1].v * dims[0][1].v) / 4;
        eachMath = `pi x (${ft(dims[0][1].v)} / 2)^2`;
      }
      out.quick = { count, each, total: count * each };
      out.area = out.quick.total;
      out.math = `${count} x (${eachMath} = ${sf(each)}) = ${sf(out.quick.total)}`;
    }
  } catch (e) {
    out.error = e.message;
  }
  return out;
}

// ---------------------------------------------------------------- one area
function parseRebar(reb, S) {
  const problems = [];
  const size = reb.size;
  const bar = S.table[size];
  if (!bar) problems.push('Pick a bar size');
  const s1 = parseInches(reb.spacingText);
  if (!(s1 > 0)) problems.push('Bar spacing is blank or unreadable (inches, like 12)');
  let s2 = s1;
  if (reb.spacing2On) {
    s2 = parseInches(reb.spacing2Text);
    if (!(s2 > 0)) problems.push('The second-direction spacing is blank or unreadable');
  }
  let cover = 3;
  if (String(reb.coverText ?? '').trim() !== '') {
    cover = parseInches(reb.coverText);
    if (Number.isNaN(cover)) problems.push('Cover is unreadable (inches, like 3)');
  }
  const mats = reb.mats === 2 ? 2 : 1;
  return { problems, size, bar, s1, s2, cover, mats, lapIn: S.lapIn[size], lapFt: (S.lapIn[size] || 0) / 12 };
}

export function computeArea(area, S) {
  const res = {
    id: area.id, name: area.name, messages: [], flags: [], sections: { area: [], A: [], B: [], extras: [] },
    outline: null, rowStatus: {}, sides: [], cutouts: [], gross: null, net: null, bySize: {},
    A: null, B: null, chosen: null, chosenLb: 0, method: area.method, layout: null, rate: null,
  };
  const reb = parseRebar(area.rebar, S);

  // ---- outline
  const rows = area.steps;
  const ow = walkRows(rows, '');
  rows.forEach((r, i) => { res.rowStatus[r.id] = ow.stats[i]; });
  res.sides = rows.map((r, i) => ({ letter: letter(i), row: r, status: ow.stats[i] }));
  if (!rows.length) res.messages.push('Add the outline of this area: walk its edges, or start from a photo.');
  else if (ow.problems.length) res.messages.push(`Outline not finished: ${ow.problems.join('; ')}.`);
  if (ow.result) {
    const w = ow.result;
    res.outline = { region: w.region, closureGap: w.closureGap, closed: w.closed, path: w.path };
    if (w.closureGap > CLOSURE_FLAG_FT) res.flags.push(`The outline does not close: it misses the start corner by ${ft(w.closureGap)}. Check the side lengths, or press "Close it for me".`);
    const bad = shapeProblem(w.region);
    if (bad === 'crosses') res.flags.push('The outline crosses itself, so the area may be wrong. Check the directions of the sides.');
    if (bad === 'doubles') res.flags.push('The outline runs over itself (a side doubles back, or it goes around more than once), so some area may be counted twice. Check the directions of the sides.');
  }
  const estimated = rows.filter((r) => r.est).length + area.cutouts.reduce((t, c) => t + (c.kind === 'traced' ? c.steps.filter((r) => r.est).length + (c.est ? 1 : 0) : 0), 0);
  if (estimated) res.flags.push(`${estimated} side length${estimated === 1 ? ' is' : 's are'} still marked "estimated, check" (worked out from the photo, which can distort lengths). Type the real measurement over them.`);

  // ---- cutouts
  res.cutouts = area.cutouts.map((c, i) => cutoutCalc(c, i, `${i + 1}`));
  area.cutouts.forEach((c, i) => {
    if (c.kind === 'traced') res.cutouts[i].stats = c.steps.map(rowStatus);
  });
  for (const c of res.cutouts) {
    if (c.error) res.flags.push(`${c.name} ${c.error}. It is not subtracted until that is fixed.`);
    if (c.flag) res.flags.push(c.flag);
  }

  // ---- rebar settings problems and flags
  for (const p of reb.problems) res.messages.push(p);
  if (reb.s1 > 0 && (reb.s1 < 3 || reb.s1 > 24)) res.flags.push(`Bar spacing ${reb.s1}" is outside the usual 3"-24" range.`);
  if (reb.s2 > 0 && reb.s2 !== reb.s1 && (reb.s2 < 3 || reb.s2 > 24)) res.flags.push(`Second-direction spacing ${reb.s2}" is outside the usual 3"-24" range.`);
  const lapTooLong = reb.lapFt >= S.stockFt;
  if (lapTooLong) res.flags.push(`The lap for ${reb.size} (${ft(reb.lapFt)}) is as long as, or longer than, a stock bar (${ft(S.stockFt)}). Laps cannot be worked out until that is fixed in Settings (bottom of the page).`);

  const rebarOk = !reb.problems.length;
  const placed = res.cutouts.filter((c) => c.region && !c.quick);
  const quick = res.cutouts.filter((c) => c.quick);
  const quickArea = quick.reduce((t, c) => t + c.quick.total, 0);

  // ---- areas
  let net = null;
  if (res.outline) {
    const gross = regionArea(res.outline.region);
    const na = netArea(res.outline.region, placed.map((c) => ({ ...c.region, name: c.name })));
    for (const w of na.warnings) res.flags.push(w);
    net = Math.max(0, na.net - quickArea);
    if (na.net - quickArea < -1e-6) res.flags.push('The cutouts add up to more than the whole area.');
    res.gross = gross;
    res.net = net;
    res.placedCutTotal = na.cutoutTotal;
    res.quickCutTotal = quickArea;
    const A = res.sections.area;
    A.push(line('Gross area', grossMath(res.outline.region, gross), sf(gross)));
    placed.forEach((c, i) => {
      const r = na.cutouts[i];
      const tag = r.status === 'straddles' ? 'clipped to the outline' : r.status === 'outside' ? 'outside the outline' : null;
      const math = r.status === 'straddles' ? `${c.math}; only ${sf(r.area)} is inside the outline` : r.status === 'outside' ? `${c.math}; outside, so 0` : c.math;
      A.push(line(c.name, math, `- ${sf(r.area)}`, tag ? { tag } : {}));
    });
    if (na.overlapArea > 1e-6) A.push(line('Overlap between cutouts', 'counted twice above, added back once', `+ ${sf(na.overlapArea)}`));
    quick.forEach((c) => A.push(line(c.name, c.math, `- ${sf(c.quick.total)}`, { tag: 'quick, no position' })));
    const cutTotal = na.cutoutTotal + quickArea;
    A.push(line('Net area', `${sf(gross)} - ${sf(cutTotal)} = ${sf(net)}`, sf(net), { strong: true }));
  }

  // ---- rebar methods
  if (res.outline && rebarOk) computeRebar(res, area, S, reb, placed, quick, quickArea, net);
  else if (res.outline && !rebarOk) res.messages.push('Fix the bar settings above to see weights.');

  // ---- extras
  area.extras.forEach((e, i) => {
    const label = `Extra ${i + 1}`;
    const bar = S.table[e.size];
    const len = parseFtIn(e.lenText);
    const qty = num(e.qtyText);
    if (!bar || String(e.lenText).trim() === '' || Number.isNaN(len) || !(len > 0) || !(qty >= 1) || !Number.isInteger(qty)) {
      res.flags.push(`${label} (loose bars) is not complete (needs a size, a readable length and a whole number of bars), so it is not counted yet.`);
      return;
    }
    const total = len * qty;
    const wt = total * bar.wplf;
    res.sections.extras.push(line(`${e.size} loose bars`, `${qty} x ${ft(len)} = ${lf(total)}; ${lf(total)} x ${bar.wplf} lb/ft = ${lb(wt)}`, lb(wt), { size: e.size, lf: total, lb: wt }));
    addSize(res.bySize, e.size, total, wt);
  });
  if (res.chosen) addSize(res.bySize, reb.size, res.chosenLb / reb.bar.wplf, res.chosenLb);
  return res;
}

function addSize(map, size, lfVal, lbVal) {
  const cur = map[size] || { lf: 0, lb: 0 };
  cur.lf += lfVal;
  cur.lb += lbVal;
  map[size] = cur;
}

function computeRebar(res, area, S, reb, placed, quick, quickArea, net) {
  const { size, bar, s1, s2, mats, cover, lapFt } = reb;
  const mathRate = wpsf(size, s1, mats, s2, S.table);
  const sameWay = s1 === s2;
  const rateMath = `${size} @ ${s1}"${sameWay ? ' each way' : ` and ${s2}"`}, ${mats} mat${mats > 1 ? 's' : ''}: ${bar.wplf} lb/ft x (12/${s1} + 12/${s2}) x ${mats} = ${fmt3(mathRate)} lb/sf`;
  const house = num(area.rebar.houseText);
  let used = mathRate;
  let usedName = 'math';
  let houseNote = null;
  if (String(area.rebar.houseText).trim() !== '') {
    if (!(house > 0)) res.flags.push('Your house rate is not a usable number, so the math rate is being used.');
    else {
      const off = (house - mathRate) / mathRate;
      if (Math.abs(off) > HOUSE_RATE_TOLERANCE) {
        res.flags.push(`Your house rate ${fmt3(house)} lb/sf is ${fmt1(Math.abs(off) * 100)}% ${off > 0 ? 'above' : 'below'} the plain math for this layout (${fmt3(mathRate)} lb/sf). Totals use the ${area.rebar.houseUse === 'house' ? 'house' : 'math'} rate you picked.`);
      }
      houseNote = { house, off };
      if (area.rebar.houseUse === 'house') { used = house; usedName = 'house'; }
    }
  }
  res.rate = { math: mathRate, house: houseNote ? houseNote.house : null, used, usedName, mathText: rateMath };

  // laps and bar-by-bar come from the layout
  let layout = null;
  try {
    if (reb.lapFt < S.stockFt || area.rebar.lapMode === 'simple') {
      layout = barLayout(res.outline.region, placed.map((c) => ({ ...c.region, name: c.name })), {
        size, spacingIn: s1, spacing2In: s2, coverIn: cover, stockFt: S.stockFt, lapFt, lapMode: area.rebar.lapMode, mats, bars: S.table,
      });
    }
  } catch (e) {
    if (e && e.code === 'TOO_MANY_LINES') {
      console.warn('barLayout skipped: spacing too small', e.message);
      res.flags.push('Spacing too small to count bar by bar (it would be more than 20,000 bars each way). Method A still shows the weight from the rate, without laps; check the spacing.');
    } else {
      console.error('barLayout failed', e);
      res.flags.push(`The bar-by-bar layout could not be worked out: ${e.message}`);
    }
  }
  res.layout = layout;
  for (const w of layout ? layout.warnings : []) res.flags.push(w);

  // ---- Method A: rate + laps
  const A = { lines: res.sections.A };
  const netTxt = sf(net);
  A.rateLb = net * used;
  A.lines.push(line('Rate', rateMath, `${fmt3(mathRate)} lb/sf`));
  if (houseNote) A.lines.push(line('House rate', `you typed ${fmt3(houseNote.house)} lb/sf (${houseNote.off >= 0 ? '+' : ''}${fmt1(houseNote.off * 100)}% vs math); using the ${usedName} rate`, `${fmt3(used)} lb/sf`, { tag: usedName === 'house' ? 'house rate used' : 'math rate used' }));
  A.lines.push(line('Weight from area', `${netTxt} x ${fmt3(used)} lb/sf = ${lb(A.rateLb)}`, lb(A.rateLb)));
  if (layout) {
    const laps = layout.x.laps + layout.y.laps;
    A.lapLf = (layout.x.lapLf + layout.y.lapLf) * mats;
    A.lapLb = A.lapLf * bar.wplf;
    const lapMath = `${laps} laps x ${ft(lapFt)}${mats > 1 ? ` x ${mats} mats` : ''} = ${lf(A.lapLf)}; ${lf(A.lapLf)} x ${bar.wplf} lb/ft = ${lb(A.lapLb)}`;
    A.lines.push(line(`Laps (${area.rebar.lapMode === 'exact' ? 'exact rule' : 'one per full stock bar'})`, lapMath, lb(A.lapLb)));
  } else {
    A.lapLf = 0;
    A.lapLb = 0;
    A.lines.push(line('Laps', 'not worked out (see the yellow flags)', '-', { tag: 'missing' }));
  }
  A.lb = A.rateLb + A.lapLb;
  A.lines.push(line('Method A total', `${lb(A.rateLb)} + ${lb(A.lapLb)} = ${lb(A.lb)}`, lb(A.lb), { strong: true }));
  res.A = A;

  // ---- Method B: bar by bar
  if (layout) {
    const B = { lines: res.sections.B };
    const mk = (name, d, spacing) => `${name}: ${d.lines} lines at ${spacing}" max, ${d.pieces.length} pieces, ${lf(d.lf)} of bar`;
    B.lines.push(line('Bars running left-right', mk('x', layout.x, s1), lf(layout.x.lf)));
    B.lines.push(line('Bars running up-down', mk('y', layout.y, s2), lf(layout.y.lf)));
    B.lines.push(line('Laps', `${layout.x.laps + layout.y.laps} laps x ${ft(lapFt)} = ${lf(layout.x.lapLf + layout.y.lapLf)}`, lf(layout.x.lapLf + layout.y.lapLf)));
    B.lines.push(line(mats > 1 ? `Per mat x ${mats} mats` : 'Total bar', `(${fmt1(layout.x.lf)} + ${fmt1(layout.y.lf)} + ${fmt1(layout.x.lapLf + layout.y.lapLf)})${mats > 1 ? ` x ${mats}` : ''} = ${lf(layout.totalLf)}; x ${bar.wplf} lb/ft = ${lb(layout.weight)}`, lb(layout.weight)));
    B.quickLb = quickArea * mathRate;
    if (quickArea > 0) B.lines.push(line('Quick cutouts (approximate)', `- ${sf(quickArea)} x ${fmt3(mathRate)} lb/sf = ${lb(B.quickLb)}`, `- ${lb(B.quickLb)}`, { tag: 'approximate' }));
    B.lb = Math.max(0, layout.weight - B.quickLb);
    B.lines.push(line('Method B total', quickArea > 0 ? `${lb(layout.weight)} - ${lb(B.quickLb)} = ${lb(B.lb)}` : lb(B.lb), lb(B.lb), { strong: true, tag: quickArea > 0 ? 'approximate' : undefined }));
    res.B = B;
  }

  const wantB = area.method === 'B';
  if (wantB && res.B) { res.chosen = 'B'; res.chosenLb = res.B.lb; }
  else if (res.A) {
    res.chosen = 'A';
    res.chosenLb = res.A.lb;
    if (wantB) res.flags.push('Method B (bar by bar) is not available right now, so Method A is being used.');
  }
  if (res.A && res.B && Math.abs(res.A.lb - res.B.lb) > 0.05 * Math.max(res.A.lb, 1)) {
    res.notes = [`Method A and Method B differ by ${fmt1(Math.abs(res.A.lb - res.B.lb))} lb (${fmt1((Math.abs(res.A.lb - res.B.lb) / Math.max(res.A.lb, res.B.lb)) * 100)}%). That is normal for odd shapes: the rate method treats the whole net area as covered, while bar by bar stops bars at cover and at cutouts. A house rate that differs from the math moves Method A too.`];
  }
}

// ---------------------------------------------------------------- whole job
export function computeJob(job) {
  const S = settingsCalc(job.settings);
  const areas = job.areas.map((a) => computeArea(a, S));
  const bySize = {};
  for (const a of areas) for (const [size, v] of Object.entries(a.bySize)) addSize(bySize, size, v.lf, v.lb);
  const rows = Object.keys(bySize).sort(sortSizes).map((size) => ({ size, lf: bySize[size].lf, lb: bySize[size].lb }));
  const subLf = rows.reduce((t, r) => t + r.lf, 0);
  const subLb = rows.reduce((t, r) => t + r.lb, 0);
  const k = S.wastePct / 100;
  const flags = [...S.problems];
  const incomplete = areas.filter((a) => !a.chosen && a.messages.length).map((a) => a.name);
  if (incomplete.length) flags.push(`Not counted yet (unfinished): ${incomplete.join(', ')}.`);
  const flagged = areas.filter((a) => a.flags.length).map((a) => a.name);
  if (flagged.length) flags.push(`${flagged.length} area${flagged.length === 1 ? ' has' : 's have'} flags to check: ${flagged.join(', ')}. The pounds below include them as they stand.`);
  return {
    settings: S, areas, rows,
    subtotal: { lf: subLf, lb: subLb },
    waste: { pct: S.wastePct, lf: subLf * k, lb: subLb * k },
    total: { lf: subLf * (1 + k), lb: subLb * (1 + k) },
    tons: (subLb * (1 + k)) / TON_LB,
    flags,
  };
}

// ---------------------------------------------------------------- CSV
const csvCell = (v) => {
  const s = String(v ?? '');
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};

export function buildCsv(job, calc) {
  const rows = [['Area', 'Section', 'Item', 'Math', 'Result', 'Note']];
  calc.areas.forEach((a) => {
    const add = (section, l) => rows.push([a.name, section, l.label, l.math, l.value, l.tag || '']);
    a.sections.area.forEach((l) => add('Area', l));
    a.sections.A.forEach((l) => add(`Method A rate + laps${a.chosen === 'A' ? ' (used)' : ''}`, l));
    a.sections.B.forEach((l) => add(`Method B bar by bar${a.chosen === 'B' ? ' (used)' : ''}`, l));
    a.sections.extras.forEach((l) => add('Extra bars', l));
    a.messages.forEach((m) => rows.push([a.name, 'Not finished', m, '', '', '']));
    a.flags.forEach((f) => rows.push([a.name, 'Flag', f, '', '', '']));
  });
  rows.push([]);
  rows.push(['Job totals', 'Bar size', 'LF', 'Pounds']);
  calc.rows.forEach((r) => rows.push(['Job totals', r.size, r.lf.toFixed(1), r.lb.toFixed(1)]));
  rows.push(['Job totals', 'Subtotal', calc.subtotal.lf.toFixed(1), calc.subtotal.lb.toFixed(1)]);
  rows.push(['Job totals', `Waste ${calc.waste.pct}%`, calc.waste.lf.toFixed(1), calc.waste.lb.toFixed(1)]);
  rows.push(['Job totals', 'Total', calc.total.lf.toFixed(1), calc.total.lb.toFixed(1)]);
  rows.push(['Job totals', 'Tons (2,000 lb)', '', calc.tons.toFixed(3)]);
  calc.flags.forEach((f) => rows.push(['Job totals', 'Check', f, '']));
  return `﻿${[[`Rebar takeoff: ${job.name || 'untitled job'}`], ...rows].map((r) => r.map(csvCell).join(',')).join('\r\n')}\r\n`;
}

export { regionArcs };

// ---------------------------------------------------------------- example job (made-up numbers)
export function exampleJob() {
  const job = newJob();
  job.name = 'Example job';
  const a = job.areas[0];
  a.name = 'L-shaped slab';
  const r = (dir, lenText) => ({ ...newRow(dir), lenText });
  a.steps = [r('R', "60'"), r('U', "20'"), r('L', "30'"), r('U', "20'"), r('L', "30'"), r('D', "40'")];
  a.cutouts = [
    { ...newCutout('rect'), name: 'Old footing', xText: "10'", yText: "6'", wText: "12'", lText: "8'" },
    { ...newCutout('quick'), name: 'Piers', countText: '6', qShape: 'circle', qdText: `2'-6"` },
  ];
  a.rebar = { ...a.rebar, size: '#5', spacingText: '12', mats: 1 };
  a.extras = [{ ...newExtra(), size: '#4', lenText: "60'", qtyText: '2' }];
  return job;
}

export function isEmptyJob(job) {
  return !job.name.trim() && job.areas.length === 1
    && !job.areas[0].steps.length && !job.areas[0].cutouts.length && !job.areas[0].extras.length;
}
