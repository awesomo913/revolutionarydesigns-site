// Tests for calc.js (the layer between the typed job and the numbers). Made-up numbers only.
// Run: node --test rebar/tests/calc.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  newJob, newArea, newRow, newCutout, newExtra, computeJob, closingSide, rowStatus, sanitizeJob, buildCsv, letter, num,
} from '../calc.js';
import { shapeProblem, walk } from '../rebar-math.js';
import { useBlocker } from '../photo-geom.js';
import * as store from '../store.js';

const near = (a, e, tol = 0.01, msg = '') => assert.ok(Math.abs(a - e) <= tol, `${msg} expected ${e}, got ${a}`);
const row = (dir, lenText, extra = {}) => ({ ...newRow(dir), lenText, ...extra });

function slabJob() {
  const job = newJob();
  const a = job.areas[0];
  a.steps = [row('R', `40'`), row('U', `25'`), row('L', `40'`), row('D', `25'`)];
  a.rebar = { ...a.rebar, size: '#4', spacingText: '12', coverText: '3', houseText: '' };
  return job;
}

test('letters run A..Z, AA, AB', () => {
  assert.equal(letter(0), 'A');
  assert.equal(letter(25), 'Z');
  assert.equal(letter(26), 'AA');
  assert.equal(letter(27), 'AB');
});

test('num reads plain decimals only', () => {
  assert.equal(num('40'), 40);
  assert.equal(num(' 0.56 '), 0.56);
  assert.ok(Number.isNaN(num('')));
  assert.ok(Number.isNaN(num('4x')));
});

test('plain slab: gross, rate method, bar-by-bar method', () => {
  const job = slabJob();
  const calc = computeJob(job);
  const a = calc.areas[0];
  near(a.gross, 1000, 1e-6);
  near(a.net, 1000, 1e-6);
  assert.match(a.sections.area[0].math, /40'-0" x 25'-0" = 1,000\.00 sf/);
  near(a.rate.math, 1.336, 1e-9);
  near(a.A.rateLb, 1336, 1e-6);
  // 40 ft x 25 ft, 3" cover: x pieces 39.5 ft (no laps), y pieces 24.5 ft
  assert.equal(a.layout.x.laps, 0);
  near(a.A.lb, 1336, 1e-6);
  near(a.B.lb, a.layout.weight, 1e-9);
  assert.equal(a.chosen, 'A');
  near(calc.total.lb, 1336, 1e-6);
  near(calc.tons, 0.668, 1e-9);
});

test('cutouts: placed rectangle, quick piers, house rate flag, method switch', () => {
  const job = slabJob();
  const a = job.areas[0];
  const rect = { ...newCutout('rect'), name: 'Old pad', xText: `5'`, yText: `5'`, wText: `10'`, lText: `5'` };
  const piers = { ...newCutout('quick'), name: 'Piers', countText: '4', qShape: 'circle', qdText: `2'` };
  a.cutouts = [rect, piers];
  a.rebar.houseText = '1.40';
  const calc = computeJob(job);
  const r = calc.areas[0];
  near(r.net, 1000 - 50 - 4 * Math.PI, 1e-6);
  near(r.A.rateLb, r.net * 1.40, 1e-6);
  assert.ok(r.flags.some((f) => /house rate/i.test(f)), 'house rate mismatch flagged');
  assert.ok(r.sections.B.some((l) => /approximate/.test(l.tag || '')), 'quick cutout is flagged approximate in method B');
  // picking the math rate changes the total, the flag stays
  a.rebar.houseUse = 'math';
  const m = computeJob(job).areas[0];
  near(m.A.rateLb, m.net * 1.336, 1e-6);
  assert.ok(m.flags.some((f) => /house rate/i.test(f)));
  // method B feeds totals when chosen
  a.method = 'B';
  const b = computeJob(job);
  assert.equal(b.areas[0].chosen, 'B');
  near(b.total.lb, b.areas[0].B.lb, 1e-6);
});

test('cutout hanging past the edge is flagged and clipped', () => {
  const job = slabJob();
  job.areas[0].cutouts = [{ ...newCutout('rect'), xText: `35'`, yText: `0'`, wText: `10'`, lText: `5'` }];
  const r = computeJob(job).areas[0];
  near(r.net, 1000 - 25, 1e-6);
  assert.ok(r.flags.some((f) => /past|outside/i.test(f)));
});

test('extra loose bars, waste and job totals by bar size', () => {
  const job = slabJob();
  job.areas[0].extras = [{ ...newExtra(), size: '#4', lenText: `10'`, qtyText: '2' }, { ...newExtra(), size: '#6', lenText: `100'`, qtyText: '1' }];
  job.settings.wasteText = '10';
  const calc = computeJob(job);
  const sizes = Object.fromEntries(calc.rows.map((r) => [r.size, r.lb]));
  near(sizes['#4'], 1336 + 20 * 0.668, 1e-6);
  near(sizes['#6'], 100 * 1.502, 1e-6);
  near(calc.subtotal.lb, 1336 + 13.36 + 150.2, 1e-6);
  near(calc.total.lb, (1336 + 13.36 + 150.2) * 1.1, 1e-6);
});

test('curves: rise, radius and arc length all give the same arc', () => {
  const byRise = rowStatus({ ...row('L', `20'`), curve: 'out', curveBy: 'rise', curveText: `10'` });
  const byRadius = rowStatus({ ...row('L', `20'`), curve: 'out', curveBy: 'radius', curveText: `10'` });
  near(byRise.bulge, 10, 1e-9);
  near(byRadius.bulge, 10, 1e-9);
  const inward = rowStatus({ ...row('L', `20'`), curve: 'in', curveBy: 'rise', curveText: `10'` });
  near(inward.bulge, -10, 1e-9);
  const bad = rowStatus({ ...row('L', `20'`), curve: 'out', curveBy: 'radius', curveText: `5'` });
  assert.ok(bad.errors.curve, 'radius smaller than half the side is an error');
});

test('unreadable length is an inline error, blank is just unfinished', () => {
  assert.ok(rowStatus(row('R', 'abc')).errors.len);
  assert.ok(rowStatus(row('R', '')).blank);
  assert.equal(rowStatus(row('R', `12'-6"`)).complete, true);
});

test('closingSide finds the last side that closes the walk', () => {
  const open = [row('R', `40'`), row('U', `25'`), row('L', `40'`), row('D', `1'`)];
  const c = closingSide(open);
  assert.equal(c.dir, 'D');
  assert.equal(c.lenText, `25'-0"`);
  // 30 right + 40 up leaves a 3-4-5 diagonal back to the start: 50 ft at about 233.13 degrees
  const diagonal = closingSide([row('R', `30'`), row('U', `40'`), row('L', `1'`)]);
  assert.equal(diagonal.dir, 'ANG');
  assert.equal(diagonal.lenText, `50'-0"`);
  near(Number(diagonal.angText), 233.13, 0.01);
});

test('open outline is flagged but still measured; unfinished outline is reported', () => {
  const job = slabJob();
  job.areas[0].steps[3].lenText = `20'`;
  const r = computeJob(job).areas[0];
  assert.ok(r.flags.some((f) => /does not close/i.test(f)));
  job.areas[0].steps[3].lenText = '';
  const u = computeJob(job).areas[0];
  assert.equal(u.outline, null);
  assert.ok(u.messages.some((m) => /needs a length/.test(m)));
});

test('lap longer than stock is flagged, not thrown', () => {
  const job = slabJob();
  job.settings.bars['#4'].lap = '600';
  const r = computeJob(job).areas[0];
  assert.ok(r.flags.some((f) => /stock bar/i.test(f)));
  assert.equal(r.layout, null);
  assert.ok(r.A, 'rate method still works without laps');
});

test('spacing outside 3-24 inches is flagged', () => {
  const job = slabJob();
  job.areas[0].rebar.spacingText = '30';
  assert.ok(computeJob(job).areas[0].flags.some((f) => /3"-24"/.test(f)));
});

test('job file round trip and bad files', () => {
  const job = slabJob();
  const back = sanitizeJob(JSON.parse(JSON.stringify(job)));
  assert.equal(back.areas[0].steps.length, 4);
  assert.throws(() => sanitizeJob({ hello: 1 }), /not a rebar takeoff job/);
  assert.throws(() => sanitizeJob(null), /not a rebar/);
  assert.throws(() => sanitizeJob({ schema: 'rebar-takeoff-job', version: 1 }), /areas/);
});

test('CSV has the math and the totals', () => {
  const job = slabJob();
  job.name = 'Test, job';
  const csv = buildCsv(job, computeJob(job));
  assert.match(csv, /Gross area/);
  assert.match(csv, /"Rebar takeoff: Test, job"/);
  assert.match(csv, /Job totals,Total/);
});

test('lap defaults: #3/#4/#5 = 60 in, #6 and up = 96 bar diameters rounded up', async () => {
  const { defaultLapIn, BARS } = await import('../rebar-math.js');
  const got = Object.fromEntries(Object.keys(BARS).map((s) => [s, defaultLapIn(s)]));
  assert.deepEqual(got, { '#3': 60, '#4': 60, '#5': 60, '#6': 72, '#7': 84, '#8': 96, '#9': 109, '#10': 122, '#11': 136, '#14': 163, '#18': 217 });
  assert.equal(newJob().settings.bars['#4'].lap, '60');
});

test('loose bars are listed as their own pounds so the headline weight can say what it includes', () => {
  const job = slabJob();
  job.areas[0].extras = [{ ...newExtra(), size: '#4', lenText: `10'`, qtyText: '2' }];
  const r = computeJob(job).areas[0];
  near(r.sections.extras.reduce((t, l) => t + l.lb, 0), 13.36, 1e-9);
  near(r.A.lb + 13.36, 1336 + 13.36, 1e-6);
  near(Object.values(r.bySize).reduce((t, v) => t + v.lb, 0), 1336 + 13.36, 1e-6);
});

// ---------------------------------------------------------------- review fixes (made-up numbers only)
const tracedCutout = (rows, sx = '20', sy = '20') => ({ ...newCutout('traced'), name: 'Old pad', steps: rows, sxText: sx, syText: sy });
const angRow = (deg, len) => ({ ...newRow('ANG'), angText: String(deg), lenText: String(len) });

test('a traced cutout whose sides cross (a bow-tie) is flagged and NOT subtracted', () => {
  const job = slabJob();
  job.areas[0].cutouts = [tracedCutout([angRow(45, 14.142136), row('D', '10'), angRow(135, 14.142136)])];
  const r = computeJob(job).areas[0];
  assert.ok(r.cutouts[0].error, 'cutout carries an error');
  assert.equal(r.cutouts[0].region, null, 'no region, so nothing is subtracted');
  assert.ok(r.flags.some((f) => /Old pad .*crosses itself.*not subtracted/i.test(f)), r.flags.join(' | '));
  near(r.net, 1000, 1e-6);
});

test('job totals and the CSV carry each area flags', () => {
  const job = slabJob();
  const second = newArea('Slab B');
  second.steps = [row('R', `10'`), row('U', `10'`), row('L', `10'`), row('D', `10'`)];
  second.cutouts = [{ ...newCutout('rect'), xText: `2'` }]; // half filled
  job.areas.push(second);
  const calc = computeJob(job);
  assert.ok(calc.flags.some((f) => /1 area has flags to check: Slab B/.test(f)), calc.flags.join(' | '));
  const csv = buildCsv(job, calc);
  assert.match(csv, /Slab B,Flag,/);
  assert.match(csv, /Job totals,Check,1 area has flags to check/);
});

test('a lap the user typed is kept exactly as typed (no hidden rewrite of old defaults)', () => {
  const job = JSON.parse(JSON.stringify(newJob()));
  job.settings.bars['#4'].lap = '24';
  assert.equal(sanitizeJob(job).settings.bars['#4'].lap, '24');
});

test('unfinished photo cutout blocks "Use these sides" and names the cutout', () => {
  const done = { kind: 'outline', done: true, pts: [1, 2, 3] };
  assert.equal(useBlocker([done], 0), null);
  assert.match(useBlocker([done, { kind: 'cutout', done: true }, { kind: 'cutout', done: false }], 1), /cutout 3 first/);
  assert.match(useBlocker([{ kind: 'outline', done: false }], 0), /Finish the outline first/);
  assert.match(useBlocker([], 0), /Finish the outline first/);
});

test('failed backup of an unreadable autosave pauses autosave and says so', () => {
  const fake = (failBackup) => {
    const data = { 'rebarTakeoff.job.v1': 'not json {' };
    return { getItem: (k) => (k in data ? data[k] : null), setItem: (k, v) => { if (failBackup && k.endsWith('.damaged')) throw new Error('no room'); data[k] = v; } };
  };
  try {
    globalThis.window = { localStorage: fake(false) };
    const kept = store.loadAutosave();
    assert.equal(kept.job, null);
    assert.ok(!kept.pauseAutosave);
    assert.match(kept.error, /damaged copy is still kept/);
    globalThis.window = { localStorage: fake(true) };
    const lost = store.loadAutosave();
    assert.equal(lost.pauseAutosave, true);
    assert.match(lost.error, /backup copy of it could not be saved/);
    assert.match(lost.error, /paused/i);
  } finally {
    delete globalThis.window;
  }
});

test('tiny spacing skips the bar-by-bar count (flagged) and the page does not freeze', () => {
  const job = slabJob();
  job.areas[0].rebar.spacingText = '0.000001';
  const t0 = Date.now();
  const r = computeJob(job).areas[0];
  assert.ok(Date.now() - t0 < 3000, 'finished quickly');
  assert.equal(r.layout, null);
  assert.equal(r.B, null);
  assert.ok(r.A, 'rate method still shown');
  assert.ok(r.flags.some((f) => /too small to count bar by bar/i.test(f)), r.flags.join(' | '));
});

test('a square walked twice (or a side that doubles back) is flagged; a normal L is not', () => {
  const sq = [['R', 10], ['U', 10], ['L', 10], ['D', 10]];
  const W = (list) => walk(list.map(([dir, len]) => ({ dir, len }))).region;
  assert.equal(shapeProblem(W(sq)), null);
  assert.equal(shapeProblem(W([['R', 100], ['U', 50], ['L', 40], ['D', 30], ['L', 60], ['D', 20]])), null);
  assert.equal(shapeProblem(W([...sq, ...sq])), 'doubles');
  assert.equal(shapeProblem(W([['R', 10], ['U', 10], ['L', 5], ['R', 5], ['L', 5], ['D', 10]])), 'doubles');
  const job = slabJob();
  job.areas[0].steps = [...sq, ...sq].map(([d, l]) => row(d, `${l}'`));
  const r = computeJob(job).areas[0];
  assert.ok(r.flags.some((f) => /runs over itself/.test(f)), r.flags.join(' | '));
});

test('cutout problems are written in plain words', () => {
  const job = slabJob();
  job.areas[0].cutouts = [{ ...newCutout('rect'), wText: `5'`, lText: `5'` }];
  let r = computeJob(job).areas[0];
  assert.ok(r.flags.includes('Cutout 1 needs its position: how far from the start corner, across and up. It is not subtracted until that is fixed.'), r.flags.join(' | '));
  job.areas[0].cutouts = [{ ...newCutout('rect'), xText: `5'`, yText: `5'`, lText: `5'` }];
  r = computeJob(job).areas[0];
  assert.ok(r.flags.some((f) => /^Cutout 1 needs its width\./.test(f)), r.flags.join(' | '));
  job.areas[0].cutouts = [{ ...newCutout('quick'), countText: '4' }];
  r = computeJob(job).areas[0];
  assert.ok(r.flags.some((f) => /^Cutout 1 needs its diameter\./.test(f)), r.flags.join(' | '));
});
