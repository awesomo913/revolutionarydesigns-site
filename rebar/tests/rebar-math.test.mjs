// Acceptance tests for rebar-math.js — run: node --test rebar/tests/
// Numbers are made-up examples worked out by hand; no real job data lives in this public repo.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  BARS, parseFtIn, formatFtIn, wpsf, rateWeight, lapsExact, lapsSimple,
  sagittaFrom, walk, regionArea, netArea, barLayout,
} from '../rebar-math.js';

const near = (actual, expected, tol = 0.01, msg = '') =>
  assert.ok(Math.abs(actual - expected) <= tol, `${msg} expected ${expected}, got ${actual}`);

const rect = (x0, y0, x1, y1) => ({
  pts: [{ x: x0, y: y0 }, { x: x1, y: y0 }, { x: x1, y: y1 }, { x: x0, y: y1 }],
  bulges: [0, 0, 0, 0],
});

test('bar table matches ASTM A615 nominal weights', () => {
  const expected = { '#3': 0.376, '#4': 0.668, '#5': 1.043, '#6': 1.502, '#7': 2.044, '#8': 2.670,
    '#9': 3.400, '#10': 4.303, '#11': 5.313, '#14': 7.650, '#18': 13.600 };
  for (const [size, w] of Object.entries(expected)) assert.equal(BARS[size].wplf, w, size);
  assert.equal(BARS['#5'].dia, 0.625);
});

test('parseFtIn reads the ways estimators write lengths', () => {
  near(parseFtIn(`519'-4"`), 519 + 4 / 12, 1e-6);
  near(parseFtIn(`519' 4"`), 519 + 4 / 12, 1e-6);
  near(parseFtIn('519-4'), 519 + 4 / 12, 1e-6);
  near(parseFtIn(`27'-10 1/2"`), 27.875, 1e-6);
  near(parseFtIn(`6'3"`), 6.25, 1e-6);
  near(parseFtIn('47"'), 47 / 12, 1e-6);
  near(parseFtIn('47 in'), 47 / 12, 1e-6);
  near(parseFtIn('12.5'), 12.5, 1e-6);
  near(parseFtIn(`12.5'`), 12.5, 1e-6);
  near(parseFtIn(`0'-6"`), 0.5, 1e-6);
  near(parseFtIn('1/2"'), 1 / 24, 1e-6);
  for (const bad of ['', 'abc', `-5'`, `5'-13"`]) assert.ok(Number.isNaN(parseFtIn(bad)), `bad: ${bad}`);
});

test('formatFtIn writes feet-inches to the nearest 1/16"', () => {
  assert.equal(formatFtIn(519 + 4 / 12), `519'-4"`);
  assert.equal(formatFtIn(27.875), `27'-10 1/2"`);
  assert.equal(formatFtIn(0.5), `0'-6"`);
  assert.equal(formatFtIn(12), `12'-0"`);
  assert.equal(formatFtIn(1 + 1 / 192), `1'-0 1/16"`);
  assert.equal(formatFtIn(11.99999), `12'-0"`);
});

test('wpsf = weight/ft x 12/spacing x 2 directions x mats', () => {
  near(wpsf('#5', 16), 1.5645, 1e-4);
  near(wpsf('#3', 16), 0.564, 1e-4);
  near(wpsf('#5', 12, 2), 4.172, 1e-4);
  near(rateWeight({ area: 7916.523, size: '#5', spacingIn: 16, mats: 1 }), 12385.40, 0.05);
});

test('laps on 40 ft stock: exact and simple rules', () => {
  assert.equal(lapsExact(519 + 4 / 12, 40, 6), 15);
  assert.equal(lapsExact(519 + 4 / 12, 40, 5), 14);
  assert.equal(lapsExact(509 + 10 / 12, 40, 5), 14);
  assert.equal(lapsExact(37, 40, 6), 0);
  assert.equal(lapsExact(40, 40, 6), 0);
  assert.equal(lapsExact(40.1, 40, 6), 1);
  assert.equal(lapsSimple(509 + 10 / 12, 40), 12);
  assert.equal(lapsSimple(80, 40), 1);
  assert.equal(lapsSimple(79.9, 40), 1);
  assert.equal(lapsSimple(40, 40), 0);
  assert.throws(() => lapsExact(100, 40, 40), /lap/i);
});

test('sagittaFrom converts arc length or radius into the arc rise', () => {
  near(sagittaFrom({ chord: 14.1421356, arcLength: 15.7079633 }), 10 * (1 - Math.cos(Math.PI / 4)), 1e-3);
  near(sagittaFrom({ chord: 20, radius: 10 }), 10, 1e-6);
});

test('walk builds a closed outline from direction + length steps', () => {
  const L = walk([
    { dir: 'R', len: 100 }, { dir: 'U', len: 50 }, { dir: 'L', len: 40 },
    { dir: 'D', len: 30 }, { dir: 'L', len: 60 }, { dir: 'D', len: 20 },
  ]);
  near(L.closureGap, 0, 1e-9);
  near(regionArea(L.region), 3200, 1e-6);
  const open = walk([{ dir: 'R', len: 10 }, { dir: 'U', len: 10 }, { dir: 'L', len: 9 }]);
  near(open.closureGap, Math.hypot(1, 10), 1e-6);
  const angled = walk([{ dir: 0, len: 10 }, { dir: 90, len: 10 }, { dir: 180, len: 10 }, { dir: 270, len: 10 }]);
  near(regionArea(angled.region), 100, 1e-6);
});

test('arc edges add (curve out) or remove (curve in) area', () => {
  const out = walk([{ dir: 'R', len: 20 }, { dir: 'U', len: 10 }, { dir: 'L', len: 20, bulge: 10 }, { dir: 'D', len: 10 }]);
  near(regionArea(out.region), 200 + Math.PI * 50, 0.01);
  const inward = walk([{ dir: 'R', len: 20 }, { dir: 'U', len: 10 }, { dir: 'L', len: 20, bulge: -10 }, { dir: 'D', len: 10 }]);
  near(regionArea(inward.region), 200 - Math.PI * 50, 0.01);
  // same shape walked clockwise must give the same area
  const cw = walk([{ dir: 'U', len: 10 }, { dir: 'R', len: 20, bulge: 10 }, { dir: 'D', len: 10 }, { dir: 'L', len: 20 }]);
  near(regionArea(cw.region), 200 + Math.PI * 50, 0.01);
});

test('netArea subtracts cutouts, clipping ones that hang past the edge', () => {
  const slab = rect(0, 0, 100, 50);
  const piers = Array.from({ length: 14 }, (_, i) => ({ circle: { cx: 5 + i * 6, cy: 25, d: 3 } }));
  near(netArea(slab, piers).net, 5000 - 14 * Math.PI * 1.5 ** 2, 0.05);
  const straddle = netArea(slab, [rect(90, 10, 110, 20)]);
  near(straddle.gross, 5000, 1e-6);
  near(straddle.net, 4900, 0.01);
  assert.ok(straddle.warnings.some((w) => /past|outside/i.test(w)));
  const outside = netArea(slab, [rect(200, 0, 210, 10)]);
  near(outside.net, 5000, 1e-6);
  assert.ok(outside.warnings.length > 0);
});

// Bar lines: count = ceil((width - 2 x cover) / spacing) + 1, spread evenly from cover to cover
// (spacing is a maximum). Each piece of bar stops `cover` short of every edge, cutout edges included.
// x = bars running left-right (stacked up the page); y = bars running up-down.
test('barLayout counts real bars across the shape, with cover and laps', () => {
  const opts = { size: '#5', spacingIn: 12, coverIn: 3, stockFt: 40, lapFt: 5, lapMode: 'exact' };
  const plain = barLayout(rect(0, 0, 100, 50), [], opts);
  assert.equal(plain.x.lines, 51);
  assert.equal(plain.y.lines, 101);
  near(plain.x.lf, 5074.5, 1e-6);
  near(plain.y.lf, 4999.5, 1e-6);
  assert.equal(plain.x.laps, 102);
  assert.equal(plain.y.laps, 101);
  near(plain.totalLf, 11089, 1e-6); // bar LF + 203 laps x 5 ft
  near(plain.weight, 11565.827, 0.01);

  const cut = barLayout(rect(0, 0, 100, 50), [rect(40.5, 20.5, 59.5, 29.5)], opts);
  near(cut.x.lf, 4899, 1e-6);
  near(cut.y.lf, 4819, 1e-6);
  assert.equal(cut.x.laps, 84);
  assert.equal(cut.y.laps, 82);
  near(cut.totalLf, 10548, 1e-6);
  near(cut.weight, 11001.564, 0.01);
});
