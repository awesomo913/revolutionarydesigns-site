// rebar-math.js - pure math for the rebar takeoff page. No DOM, no dependencies.
//
// Units: feet unless a name ends in "In" (inches). Weights are lb.
// Region = { pts:[{x,y}...], bulges:[h per edge] }  (edge i runs pts[i] -> pts[i+1], the last edge closes)
//        | { circle:{ cx, cy, d } }
// A bulge h is the arc rise (sagitta): + curves OUTWARD from the shape, - curves INWARD,
// whichever way the outline was walked. Arcs become polylines (>= 64 segments) for clipping and
// bar sweeps; areas use the exact arc formulas.

const EPS = 1e-9;
const SEG_MIN = 64;        // minimum polyline segments per arc
const CIRCLE_SEGS = 256;   // polyline segments for a full circle

// ---------------------------------------------------------------- bar table
// ASTM A615 nominal sizes. wplf = lb per foot, dia = inches, area = sq in.
const bar = (dia, wplf, area) => Object.freeze({ dia, wplf, area });
export const BARS = Object.freeze({
  '#3': bar(0.375, 0.376, 0.11),
  '#4': bar(0.5, 0.668, 0.2),
  '#5': bar(0.625, 1.043, 0.31),
  '#6': bar(0.75, 1.502, 0.44),
  '#7': bar(0.875, 2.044, 0.6),
  '#8': bar(1.0, 2.67, 0.79),
  '#9': bar(1.128, 3.4, 1.0),
  '#10': bar(1.27, 4.303, 1.27),
  '#11': bar(1.41, 5.313, 1.56),
  '#14': bar(1.693, 7.65, 2.25),
  '#18': bar(2.257, 13.6, 4.0),
});

// Default lap in inches (lead's call, 2026-10-30): #3, #4 and #5 = 60"; #6 and larger = 96 bar
// diameters rounded up to the inch (#6 = 72", #7 = 84", #8 = 96", ...). Every value is editable.
const SHORT_LAP_SIZES = ['#3', '#4', '#5'];
export function defaultLapIn(size, bars = BARS) {
  if (SHORT_LAP_SIZES.includes(size)) return 60;
  const b = bars[size];
  if (!b) throw new Error(`Unknown bar size ${size}`);
  return Math.ceil(96 * b.dia - EPS);
}

function barOf(size, bars) {
  const b = bars && bars[size];
  if (!b) throw new Error(`Unknown bar size ${size}`);
  return b;
}

// ---------------------------------------------------------------- feet-inches text
function normText(input) {
  return String(input)
    .trim()
    .toLowerCase()
    .replace(/[′’‘]/g, "'")
    .replace(/[″”“]/g, '"')
    .replace(/''/g, '"')
    .replace(/(\d),(?=\d{3}(?!\d))/g, '$1')
    .replace(/\s*(?:feet|foot|ft)\b\.?/g, "'")
    .replace(/\s*(?:inches|inch|in)\b\.?/g, '"')
    .replace(/\s+/g, ' ')
    .trim();
}

// inches part: "10", "3.5", "10 1/2", "10-1/2", "1/2"
function parseInchPart(t) {
  t = t.trim();
  let m = /^(\d+(?:\.\d+)?)$/.exec(t);
  if (m) return Number(m[1]);
  m = /^(\d+)\s*[\s-]\s*(\d+)\/(\d+)$/.exec(t);
  if (m && Number(m[3]) > 0 && Number(m[2]) < Number(m[3])) return Number(m[1]) + Number(m[2]) / Number(m[3]);
  m = /^(\d+)\/(\d+)$/.exec(t);
  if (m && Number(m[2]) > 0) return Number(m[1]) / Number(m[2]);
  return NaN;
}

// Reads 519'-4", 519' 4", 519-4, 27'-10 1/2", 6'3", 47", 47 in, 12.5, 12.5'. Bare number = feet.
// Returns feet, or NaN when it cannot be read (empty, negative, inches >= 12 beside feet).
export function parseFtIn(input) {
  if (typeof input === 'number') return Number.isFinite(input) && input >= 0 ? input : NaN;
  if (typeof input !== 'string') return NaN;
  const s = normText(input);
  if (!s) return NaN;
  let m = /^(\d+(?:\.\d+)?)\s*'\s*(?:-\s*)?(.*)$/.exec(s);
  if (m) {
    const feet = Number(m[1]);
    const rest = m[2].replace(/"\s*$/, '').trim();
    if (rest === '') return feet;
    if (!/^\d+$/.test(m[1])) return NaN; // 12.5' 3" makes no sense
    const inches = parseInchPart(rest);
    if (!Number.isFinite(inches) || inches >= 12) return NaN;
    return feet + inches / 12;
  }
  m = /^(.*)"$/.exec(s);
  if (m) {
    const inches = parseInchPart(m[1]);
    return Number.isFinite(inches) ? inches / 12 : NaN;
  }
  m = /^(\d+)\s*-\s*(.+)$/.exec(s);
  if (m) {
    const inches = parseInchPart(m[2]);
    return Number.isFinite(inches) && inches < 12 ? Number(m[1]) + inches / 12 : NaN;
  }
  if (/^\d+(?:\.\d+)?$/.test(s)) return Number(s);
  return NaN;
}

// Like parseFtIn but a leading minus is allowed (cutout offsets can sit before the start corner).
export function parseSignedFtIn(input) {
  if (typeof input === 'number') return Number.isFinite(input) ? input : NaN;
  if (typeof input !== 'string') return NaN;
  const s = input.trim().replace(/^[−–]/, '-');
  if (s.startsWith('-')) {
    const v = parseFtIn(s.slice(1));
    return Number.isNaN(v) ? NaN : -v;
  }
  return parseFtIn(s);
}

// Spacing / cover: a bare number is INCHES (16 = 16"); marks or ft/in words are honoured (1'-4").
export function parseInches(input) {
  if (typeof input === 'number') return Number.isFinite(input) && input >= 0 ? input : NaN;
  if (typeof input !== 'string') return NaN;
  const s = normText(input);
  if (!s) return NaN;
  const bare = parseInchPart(s);
  if (Number.isFinite(bare)) return bare;
  const ft = parseFtIn(s);
  return Number.isNaN(ft) ? NaN : ft * 12;
}

// Feet -> feet-inches to the nearest 1/16".
export function formatFtIn(ft) {
  if (!Number.isFinite(ft)) return '';
  const sixteenths = Math.round(Math.abs(ft) * 192 + 1e-7);
  const feet = Math.floor(sixteenths / 192);
  const rem = sixteenths - feet * 192;
  const inch = Math.floor(rem / 16);
  let n = rem - inch * 16;
  let frac = '';
  if (n) {
    let d = 16;
    while (n % 2 === 0) { n /= 2; d /= 2; }
    frac = ` ${n}/${d}`;
  }
  return `${ft < 0 && sixteenths > 0 ? '-' : ''}${feet}'-${inch}${frac}"`;
}

// ---------------------------------------------------------------- weights and laps
// lb per sq ft = weight/ft x 12/spacing (each direction) x mats
export function wpsf(size, spacingIn, mats = 1, spacing2In = spacingIn, bars = BARS) {
  const b = barOf(size, bars);
  if (!(spacingIn > 0) || !(spacing2In > 0)) throw new Error('Spacing must be greater than 0.');
  return b.wplf * 12 * (1 / spacingIn + 1 / spacing2In) * mats;
}

export function rateWeight({ area, size, spacingIn, mats = 1, spacing2In = spacingIn, bars = BARS }) {
  return area * wpsf(size, spacingIn, mats, spacing2In, bars);
}

// Splices in a run: 0 if it fits one stock bar, else each extra bar adds (stock - lap) of reach.
export function lapsExact(run, stock, lap) {
  if (!(stock > 0)) throw new Error('Stock length must be greater than 0.');
  if (!(lap >= 0)) throw new Error('Lap length cannot be negative.');
  if (lap >= stock) throw new Error('Lap length must be shorter than the stock bar length.');
  if (!(run > 0) || run <= stock + EPS) return 0;
  return Math.max(0, Math.ceil((run - stock) / (stock - lap) - EPS));
}

// Simple rule: one lap per full stock length (ceil(run / stock) - 1).
export function lapsSimple(run, stock) {
  if (!(stock > 0)) throw new Error('Stock length must be greater than 0.');
  if (!(run > 0)) return 0;
  return Math.max(0, Math.ceil(run / stock - EPS) - 1);
}

// ---------------------------------------------------------------- arcs
// Arc rise from the chord plus ONE of: arcLength, radius, angleDeg (central angle).
// Returns a positive rise; the caller picks the sign (+ out, - in).
export function sagittaFrom({ chord, arcLength, radius, angleDeg, major = false }) {
  if (!(chord > 0)) throw new Error('The side length must be greater than 0 before a curve can be worked out.');
  if (arcLength !== undefined) {
    if (!(arcLength > 0)) throw new Error('Arc length must be greater than 0.');
    if (arcLength < chord - 1e-9) throw new Error('Arc length cannot be shorter than the straight side.');
    if (arcLength - chord < 1e-9 * chord) return 0;
    const ratio = chord / arcLength; // = sin(u)/u with u = half the central angle
    let lo = 1e-9;
    let hi = Math.PI;
    for (let i = 0; i < 200; i++) {
      const mid = (lo + hi) / 2;
      if (Math.sin(mid) / mid > ratio) lo = mid; else hi = mid;
    }
    return (chord / 2) * Math.tan((lo + hi) / 4);
  }
  if (radius !== undefined) {
    if (!(radius > 0)) throw new Error('Radius must be greater than 0.');
    if (radius < chord / 2 - 1e-9) throw new Error('Radius is too small: it must be at least half the side length.');
    const root = Math.sqrt(Math.max(0, radius * radius - (chord * chord) / 4));
    return major ? radius + root : radius - root;
  }
  if (angleDeg !== undefined) {
    if (!(angleDeg > 0 && angleDeg < 360)) throw new Error('Arc angle must be between 0 and 360 degrees.');
    return (chord / 2) * Math.tan((angleDeg * Math.PI) / 180 / 4);
  }
  throw new Error('Give a rise, radius, arc length or angle for the curve.');
}

// ---------------------------------------------------------------- region geometry
function signedArea(pts) {
  let a = 0;
  for (let i = 0; i < pts.length; i++) {
    const p = pts[i];
    const q = pts[(i + 1) % pts.length];
    a += p.x * q.y - q.x * p.y;
  }
  return a / 2;
}

export function polygonArea(pts) {
  return Math.abs(signedArea(pts));
}

// True when the corners run counter-clockwise (y up).
export const isCcw = (pts) => signedArea(pts) >= 0;

// Geometry of one curved edge (null for a straight one). `ccw` = chord polygon runs counter-clockwise.
function edgeArc(P, Q, bulge, ccw) {
  const dx = Q.x - P.x;
  const dy = Q.y - P.y;
  const c = Math.hypot(dx, dy);
  if (!bulge || c < EPS) return null;
  const o = ccw ? 1 : -1;
  const sg = Math.sign(bulge);
  const h = Math.abs(bulge);
  const toX = (o * dy / c) * sg; // unit vector from chord midpoint toward the arc's middle
  const toY = (-o * dx / c) * sg;
  const mx = (P.x + Q.x) / 2;
  const my = (P.y + Q.y) / 2;
  const r = (c * c / 4 + h * h) / (2 * h);
  const cx = mx + toX * (h - r);
  const cy = my + toY * (h - r);
  const Mx = mx + toX * h;
  const My = my + toY * h;
  const alpha = Math.atan2(c / 2, r - h); // half the central angle
  const cross = (P.x - cx) * (My - cy) - (P.y - cy) * (Mx - cx);
  return {
    c, h, r, alpha, sign: sg, cx, cy, mid: { x: Mx, y: My },
    a0: Math.atan2(P.y - cy, P.x - cx),
    sweep: (cross >= 0 ? 1 : -1) * 2 * alpha,
  };
}

const segmentArea = (arc) => arc.r * arc.r * arc.alpha - (arc.c / 2) * (arc.r - arc.h);

// Per-edge arcs for a pts/bulges region (array parallel to pts; null = straight).
export function regionArcs(region) {
  const { pts, bulges = [] } = region;
  const ccw = signedArea(pts) >= 0;
  return pts.map((p, i) => edgeArc(p, pts[(i + 1) % pts.length], bulges[i] || 0, ccw));
}

export function regionArea(region) {
  if (region.circle) return (Math.PI * region.circle.d * region.circle.d) / 4;
  let total = polygonArea(region.pts);
  for (const arc of regionArcs(region)) if (arc) total += arc.sign * segmentArea(arc);
  return total;
}

// Region -> closed polyline ring (first point not repeated).
export function flatten(region) {
  if (region.circle) {
    const { cx, cy, d } = region.circle;
    const ring = [];
    for (let i = 0; i < CIRCLE_SEGS; i++) {
      const a = (2 * Math.PI * i) / CIRCLE_SEGS;
      ring.push({ x: cx + (d / 2) * Math.cos(a), y: cy + (d / 2) * Math.sin(a) });
    }
    return ring;
  }
  const arcs = regionArcs(region);
  const ring = [];
  region.pts.forEach((p, i) => {
    ring.push({ x: p.x, y: p.y });
    const arc = arcs[i];
    if (!arc) return;
    const n = Math.min(1024, Math.max(SEG_MIN, Math.ceil(Math.abs(arc.sweep) / 0.025)));
    for (let k = 1; k < n; k++) {
      const a = arc.a0 + (arc.sweep * k) / n;
      ring.push({ x: arc.cx + arc.r * Math.cos(a), y: arc.cy + arc.r * Math.sin(a) });
    }
  });
  return ring;
}

export function ringBounds(ring) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const p of ring) {
    if (p.x < minX) minX = p.x;
    if (p.x > maxX) maxX = p.x;
    if (p.y < minY) minY = p.y;
    if (p.y > maxY) maxY = p.y;
  }
  return { minX, minY, maxX, maxY };
}

export const regionBounds = (region) => ringBounds(flatten(region));

export function translate(region, dx, dy) {
  if (region.circle) return { circle: { ...region.circle, cx: region.circle.cx + dx, cy: region.circle.cy + dy } };
  return { pts: region.pts.map((p) => ({ x: p.x + dx, y: p.y + dy })), bulges: [...(region.bulges || [])] };
}

export function rectRegion(x, y, w, l) {
  return {
    pts: [{ x, y }, { x: x + w, y }, { x: x + w, y: y + l }, { x, y: y + l }],
    bulges: [0, 0, 0, 0],
  };
}

export const circleRegion = (cx, cy, d) => ({ circle: { cx, cy, d } });

// True if the outline crosses itself (a figure-8 or a sloppy trace).
export function selfIntersects(region) {
  const ring = region.circle ? [] : flatten(region);
  const n = ring.length;
  if (n < 4) return false;
  const edges = ring.map((a, i) => {
    const b = ring[(i + 1) % n];
    return { i, a, b, minX: Math.min(a.x, b.x), maxX: Math.max(a.x, b.x) };
  });
  edges.sort((p, q) => p.minX - q.minX);
  const orient = (p, q, r) => (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x);
  for (let s = 0; s < n; s++) {
    const e = edges[s];
    for (let t = s + 1; t < n && edges[t].minX <= e.maxX + EPS; t++) {
      const f = edges[t];
      const gap = Math.abs(e.i - f.i);
      if (gap === 1 || gap === n - 1) continue; // neighbours share a corner
      const o1 = orient(e.a, e.b, f.a);
      const o2 = orient(e.a, e.b, f.b);
      const o3 = orient(f.a, f.b, e.a);
      const o4 = orient(f.a, f.b, e.b);
      if (o1 * o2 < -EPS && o3 * o4 < -EPS) return true;
    }
  }
  return false;
}

// Does the outline run over itself? True when it goes around more than once (a square walked twice)
// or when two of its edges lie on the same line and overlap (a side that doubles straight back).
function doublesBack(ring) {
  const pts = ring.filter((p, i) => {
    const q = ring[(i + 1) % ring.length];
    return Math.hypot(q.x - p.x, q.y - p.y) > 1e-9;
  });
  const n = pts.length;
  if (n < 3) return false;
  let turning = 0;
  for (let i = 0; i < n; i++) {
    const a = pts[i];
    const b = pts[(i + 1) % n];
    const c = pts[(i + 2) % n];
    let d = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(b.y - a.y, b.x - a.x);
    while (d > Math.PI) d -= 2 * Math.PI;
    while (d <= -Math.PI) d += 2 * Math.PI;
    turning += d;
  }
  if (Math.abs(turning) > 3 * Math.PI) return true; // one clean loop turns 2 pi; twice round turns 4 pi
  const edges = pts.map((a, i) => {
    const b = pts[(i + 1) % n];
    return { a, b, len: Math.hypot(b.x - a.x, b.y - a.y), minX: Math.min(a.x, b.x), maxX: Math.max(a.x, b.x) };
  }).sort((p, q) => p.minX - q.minX);
  for (let s = 0; s < n; s++) {
    const e = edges[s];
    const dx = (e.b.x - e.a.x) / e.len;
    const dy = (e.b.y - e.a.y) / e.len;
    for (let t = s + 1; t < n && edges[t].minX <= e.maxX + EPS; t++) {
      const f = edges[t];
      const off1 = Math.abs((f.a.x - e.a.x) * dy - (f.a.y - e.a.y) * dx);
      const off2 = Math.abs((f.b.x - e.a.x) * dy - (f.b.y - e.a.y) * dx);
      if (off1 > 1e-6 || off2 > 1e-6) continue; // not on the same line
      const t1 = (f.a.x - e.a.x) * dx + (f.a.y - e.a.y) * dy;
      const t2 = (f.b.x - e.a.x) * dx + (f.b.y - e.a.y) * dy;
      if (Math.min(e.len, Math.max(t1, t2)) - Math.max(0, Math.min(t1, t2)) > 1e-6) return true;
    }
  }
  return false;
}

// What is wrong with a drawn shape: 'crosses' (edges cross), 'doubles' (runs over itself), or null.
export function shapeProblem(region) {
  if (region.circle) return null;
  if (selfIntersects(region)) return 'crosses';
  return doublesBack(flatten(region)) ? 'doubles' : null;
}

// ---------------------------------------------------------------- walk the edges
const CARDINAL = { 0: [1, 0], 90: [0, 1], 180: [-1, 0], 270: [0, -1] };
const DIR_DEG = { R: 0, U: 90, L: 180, D: 270 };

export function dirToDegrees(dir) {
  if (typeof dir === 'string') {
    const d = DIR_DEG[dir.toUpperCase()];
    if (d === undefined) throw new Error(`Unknown direction "${dir}"`);
    return d;
  }
  if (!Number.isFinite(dir)) throw new Error('Direction must be R, L, U, D or an angle in degrees');
  return dir;
}

// steps: { dir:'R'|'L'|'U'|'D'|degrees (0=east, 90=north), len, bulge? } starting at (0,0).
// An open walk is closed with a straight edge; closureGap is how far the walk missed the start.
export function walk(steps) {
  if (!Array.isArray(steps) || steps.length < 2) throw new Error('A walk needs at least 2 sides.');
  const path = [{ x: 0, y: 0 }];
  steps.forEach((s, i) => {
    if (!Number.isFinite(s.len) || s.len <= 0) throw new Error(`Side ${i + 1}: length must be greater than 0.`);
    const deg = ((dirToDegrees(s.dir) % 360) + 360) % 360;
    const card = CARDINAL[deg];
    const ux = card ? card[0] : Math.cos((deg * Math.PI) / 180);
    const uy = card ? card[1] : Math.sin((deg * Math.PI) / 180);
    const prev = path[path.length - 1];
    path.push({ x: prev.x + ux * s.len, y: prev.y + uy * s.len });
  });
  const end = path[path.length - 1];
  const closureGap = Math.hypot(end.x, end.y);
  const closed = closureGap < 1e-6;
  const pts = closed ? path.slice(0, -1) : path.slice();
  const bulges = steps.map((s) => s.bulge || 0);
  if (!closed) bulges.push(0);
  return { region: { pts, bulges }, closureGap, closed, path };
}

// ---------------------------------------------------------------- polygon measuring (vertical slabs)
function crossX(e, f) {
  const rx = e.x2 - e.x1;
  const ry = e.y2 - e.y1;
  const sx = f.x2 - f.x1;
  const sy = f.y2 - f.y1;
  const d = rx * sy - ry * sx;
  if (Math.abs(d) < 1e-14) return null;
  const t = ((f.x1 - e.x1) * sy - (f.y1 - e.y1) * sx) / d;
  const u = ((f.x1 - e.x1) * ry - (f.y1 - e.y1) * rx) / d;
  if (t < -EPS || t > 1 + EPS || u < -EPS || u > 1 + EPS) return null;
  return e.x1 + t * rx;
}

function intervalsAtX(edges, x) {
  const ys = [];
  for (const e of edges) {
    if ((e.x1 <= x && e.x2 > x) || (e.x2 <= x && e.x1 > x)) ys.push(e.y1 + ((x - e.x1) * (e.y2 - e.y1)) / (e.x2 - e.x1));
  }
  ys.sort((a, b) => a - b);
  const out = [];
  for (let i = 0; i + 1 < ys.length; i += 2) out.push([ys[i], ys[i + 1]]);
  return out;
}

const insideIv = (iv, y) => iv.some(([a, b]) => y > a && y < b);

// Area of { points inside the rings whose membership flags satisfy predicate(flags) }.
// Exact for straight-edged rings: between two neighbouring "event" x values the cross-section
// length is linear in x, so (width x length at the middle) is the exact slab area.
function ringsMeasure(rings, predicate) {
  const all = [];
  const scan = rings.map(() => []);
  const xs = [];
  rings.forEach((ring, k) => {
    const n = ring.length;
    for (let i = 0; i < n; i++) {
      const a = ring[i];
      const b = ring[(i + 1) % n];
      xs.push(a.x);
      const e = { k, x1: a.x, y1: a.y, x2: b.x, y2: b.y, minX: Math.min(a.x, b.x), maxX: Math.max(a.x, b.x) };
      all.push(e);
      if (a.x !== b.x) scan[k].push(e);
    }
  });
  all.sort((p, q) => p.minX - q.minX);
  for (let i = 0; i < all.length; i++) {
    const e = all[i];
    for (let j = i + 1; j < all.length && all[j].minX <= e.maxX + EPS; j++) {
      if (all[j].k === e.k) continue; // each ring is assumed not to cross itself
      const x = crossX(e, all[j]);
      if (x !== null) xs.push(x);
    }
  }
  xs.sort((p, q) => p - q);
  let total = 0;
  for (let s = 0; s + 1 < xs.length; s++) {
    const x0 = xs[s];
    const x1 = xs[s + 1];
    if (x1 - x0 <= 1e-12) continue;
    const xm = (x0 + x1) / 2;
    const ivs = scan.map((edges) => intervalsAtX(edges, xm));
    const ys = [];
    for (const iv of ivs) for (const [a, b] of iv) ys.push(a, b);
    ys.sort((p, q) => p - q);
    let len = 0;
    for (let m = 0; m + 1 < ys.length; m++) {
      if (ys[m + 1] - ys[m] <= 1e-12) continue;
      const ym = (ys[m] + ys[m + 1]) / 2;
      if (predicate(ivs.map((iv) => insideIv(iv, ym)))) len += ys[m + 1] - ys[m];
    }
    total += len * (x1 - x0);
  }
  return total;
}

const bboxesOverlap = (a, b) => a.minX < b.maxX && b.minX < a.maxX && a.minY < b.maxY && b.minY < a.maxY;

// Gross, each cutout (clipped to the outline), and net. Cutouts may be any simple shape
// (they do not need to be convex). Overlapping cutouts are subtracted once.
export function netArea(outline, cutouts = []) {
  const warnings = [];
  const gross = regionArea(outline);
  const O = flatten(outline);
  const items = cutouts.map((c, i) => {
    const name = c.name || `Cutout ${i + 1}`;
    const ring = flatten(c);
    const fullArea = regionArea(c);
    const flatArea = polygonArea(ring);
    const inter = ringsMeasure([O, ring], (f) => f[0] && f[1]);
    let status;
    let area;
    if (inter <= 1e-9 * Math.max(1, flatArea)) {
      status = 'outside';
      area = 0;
      warnings.push(`${name} lies outside the outline, so it subtracts nothing.`);
    } else if (Math.abs(inter - flatArea) <= 1e-6 * flatArea + 1e-9) {
      status = 'inside';
      area = fullArea;
    } else {
      status = 'straddles';
      area = inter;
      warnings.push(`${name} extends past the outline edge, so only the part inside is subtracted.`);
    }
    return { name, ring, bounds: ringBounds(ring), area, fullArea, clipped: inter, status };
  });

  let overlapArea = 0;
  const live = items.filter((it) => it.status !== 'outside');
  const pairs = [];
  for (let a = 0; a < live.length; a++) {
    for (let b = a + 1; b < live.length; b++) {
      if (!bboxesOverlap(live[a].bounds, live[b].bounds)) continue;
      const ov = ringsMeasure([live[a].ring, live[b].ring], (f) => f[0] && f[1]);
      if (ov > 1e-6) pairs.push([live[a], live[b], ov]);
    }
  }
  if (pairs.length) {
    const union = ringsMeasure([O, ...live.map((it) => it.ring)], (f) => f[0] && f.slice(1).some(Boolean));
    overlapArea = Math.max(0, live.reduce((t, it) => t + it.clipped, 0) - union);
    for (const [p, q, ov] of pairs) {
      warnings.push(`${p.name} and ${q.name} overlap by about ${ov.toFixed(2)} sf; the overlap is only subtracted once.`);
    }
  }
  const cutoutTotal = items.reduce((t, it) => t + it.area, 0) - overlapArea;
  if (cutoutTotal > gross + 1e-6) warnings.push('The cutouts add up to more than the whole area.');
  return {
    gross,
    cutouts: items.map(({ name, area, fullArea, status }) => ({ name, area, fullArea, status })),
    cutoutTotal,
    overlapArea,
    net: Math.max(0, gross - cutoutTotal),
    warnings,
  };
}

// ---------------------------------------------------------------- bar layout
function intervalsOnLine(ring, t) {
  const xs = [];
  const n = ring.length;
  for (let i = 0; i < n; i++) {
    const a = ring[i];
    const b = ring[(i + 1) % n];
    if ((a.y <= t && b.y > t) || (b.y <= t && a.y > t)) xs.push(a.x + ((t - a.y) * (b.x - a.x)) / (b.y - a.y));
  }
  xs.sort((p, q) => p - q);
  const out = [];
  for (let i = 0; i + 1 < xs.length; i += 2) out.push([xs[i], xs[i + 1]]);
  return out;
}

function unionIntervals(list) {
  const sorted = list.filter(([a, b]) => b > a).sort((p, q) => p[0] - q[0]);
  const out = [];
  for (const [a, b] of sorted) {
    const last = out[out.length - 1];
    if (last && a <= last[1]) last[1] = Math.max(last[1], b);
    else out.push([a, b]);
  }
  return out;
}

function subtractIntervals(A, B) {
  const out = [];
  for (const [a0, a1] of A) {
    let cur = a0;
    for (const [b0, b1] of B) {
      if (b1 <= cur) continue;
      if (b0 >= a1) break;
      if (b0 > cur) out.push([cur, b0]);
      cur = Math.max(cur, b1);
      if (cur >= a1) break;
    }
    if (cur < a1) out.push([cur, a1]);
  }
  return out;
}

const transposeRing = (ring) => ring.map((p) => ({ x: p.y, y: p.x }));

// Bars running along x in the given rings, stacked from minT to maxT at the given spacing.
function sweep(O, C, minT, maxT, spacing, cover, count) {
  const usable = maxT - minT - 2 * cover;
  const lines = usable < -EPS ? 0 : usable <= EPS ? 1 : Math.ceil(usable / spacing - EPS) + 1;
  const result = { lines, lf: 0, laps: 0, lapLf: 0, pieces: [] };
  if (!lines) return result;
  const step = lines > 1 ? usable / (lines - 1) : 0;
  const first = lines > 1 ? minT + cover : (minT + maxT) / 2;
  for (let i = 0; i < lines; i++) {
    const t = Math.min(maxT - 1e-7, Math.max(minT + 1e-7, first + i * step));
    const open = subtractIntervals(unionIntervals(intervalsOnLine(O, t)), unionIntervals(C.flatMap((ring) => intervalsOnLine(ring, t))));
    for (const [a, b] of open) {
      const len = b - a - 2 * cover;
      if (len <= EPS) continue;
      const laps = count(len);
      result.pieces.push({ t, a: a + cover, b: b - cover, len, laps });
      result.lf += len;
      result.laps += laps;
    }
  }
  return result;
}

// Real bars across the real shape. opts: { size, spacingIn, spacing2In?, coverIn=3, stockFt=40,
// lapFt, lapMode:'exact'|'simple', mats=1, bars=BARS }.
// x = bars running left-right (stacked up the page, spaced by spacingIn);
// y = bars running up-down (spaced by spacing2In, which defaults to spacingIn).
export const MAX_BAR_LINES = 20000; // per direction; beyond this a bar-by-bar count is refused

export function barLayout(outline, cutouts = [], opts = {}) {
  const { size, spacingIn, spacing2In = spacingIn, coverIn = 3, stockFt = 40, lapFt = 0, lapMode = 'exact', mats = 1, bars = BARS } = opts;
  const b = barOf(size, bars);
  if (!(spacingIn > 0) || !(spacing2In > 0)) throw new Error('Spacing must be greater than 0.');
  if (!(coverIn >= 0)) throw new Error('Cover cannot be negative.');
  if (lapMode !== 'exact' && lapMode !== 'simple') throw new Error('lapMode must be "exact" or "simple".');
  if (lapMode === 'exact') lapsExact(0, stockFt, lapFt); // validates stock/lap up front
  const count = lapMode === 'exact' ? (len) => lapsExact(len, stockFt, lapFt) : (len) => lapsSimple(len, stockFt);
  const cover = coverIn / 12;
  const O = flatten(outline);
  const C = cutouts.map(flatten);
  const bb = ringBounds(O);
  const linesFor = (span, spacing) => { const u = span - 2 * cover; return u < -EPS ? 0 : u <= EPS ? 1 : Math.ceil(u / spacing - EPS) + 1; };
  const wanted = Math.max(linesFor(bb.maxY - bb.minY, spacingIn / 12), linesFor(bb.maxX - bb.minX, spacing2In / 12));
  if (wanted > MAX_BAR_LINES) {
    const err = new Error(`That spacing would mean more than ${MAX_BAR_LINES.toLocaleString('en-US')} bars each way.`);
    err.code = 'TOO_MANY_LINES';
    throw err;
  }

  const rawX = sweep(O, C, bb.minY, bb.maxY, spacingIn / 12, cover, count);
  const rawY = sweep(transposeRing(O), C.map(transposeRing), bb.minX, bb.maxX, spacing2In / 12, cover, count);
  const x = {
    ...rawX,
    lapLf: rawX.laps * lapFt,
    pieces: rawX.pieces.map((p) => ({ x0: p.a, y0: p.t, x1: p.b, y1: p.t, len: p.len, laps: p.laps })),
  };
  const y = {
    ...rawY,
    lapLf: rawY.laps * lapFt,
    pieces: rawY.pieces.map((p) => ({ x0: p.t, y0: p.a, x1: p.t, y1: p.b, len: p.len, laps: p.laps })),
  };
  const perMatLf = x.lf + y.lf + x.lapLf + y.lapLf;
  const warnings = [];
  if (!x.lines || !y.lines) warnings.push('The shape is too small for bars with this cover.');
  return { x, y, mats, perMatLf, totalLf: perMatLf * mats, weight: perMatLf * mats * b.wplf, lapFt, stockFt, lapMode, warnings };
}
