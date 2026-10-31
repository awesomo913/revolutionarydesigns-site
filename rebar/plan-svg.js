// plan-svg.js - draws the flat 2D plan as an SVG string: thin outline, lettered sides with dimension
// lines and end ticks, hatched cutouts (C1, C2...), red dashed closure gap. No DOM; colours come from
// CSS classes in app.css so light/dark both work.
import { flatten, isCcw, ringBounds } from './rebar-math.js';
import { cutLetter, ft, CLOSED_FT } from './calc.js';

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const r1 = (n) => Math.round(n * 10) / 10;
let svgCounter = 0;

// ---------------------------------------------------------------- models
function sideList(path, sidesInfo, labelOf, textOf) {
  return sidesInfo.map((s, i) => ({ label: labelOf(i), p: path[i], q: path[i + 1], bulge: s.status.bulge, text: textOf(s, i), est: !!s.row.est }));
}

// Real drawing: outline + cutouts from computeArea() output.
export function planFromCalc(res, { showBars = false } = {}) {
  const o = res.outline;
  const shapes = [];
  const n = res.sides.length;
  shapes.push({
    kind: 'outline', ring: flatten(o.region), ccw: isCcw(o.region.pts),
    sides: sideList(o.path, res.sides, (i) => res.sides[i].letter, (s) => ft(s.status.len)),
  });
  res.cutouts.forEach((c, k) => {
    if (!c.region) return;
    const sh = { kind: 'cutout', ring: flatten(c.region), tag: `C${k + 1}`, dimText: c.dimText || '', sides: [] };
    if (c.walk && c.stats) {
      sh.ccw = isCcw(c.region.pts);
      sh.sides = c.walk.path.slice(0, -1).map((p, i) => ({
        label: cutLetter(k, i), p, q: c.walk.path[i + 1], bulge: c.stats[i].bulge, text: ft(c.stats[i].len), est: false, small: true,
      }));
    }
    shapes.push(sh);
  });
  const gap = o.closureGap > CLOSED_FT ? { a: o.path[n], b: o.path[0], text: ft(o.closureGap) } : null;
  const bars = showBars && res.layout ? [...res.layout.x.pieces, ...res.layout.y.pieces] : null;
  return { shapes, gap, bars, aria: `Plan of ${res.name}: ${n} sides` };
}

// Provisional drawing from the photo corners while lengths are still missing.
export function planFromSketch(area, res) {
  const pts = area.sketch;
  const curveOf = (row, a, b) => (row.curve === 'none' ? 0 : (row.curve === 'out' ? 1 : -1) * 0.12 * Math.hypot(b.x - a.x, b.y - a.y));
  const mk = (rows, sk, stats, labelOf) => {
    const n = sk.length;
    const bulges = rows.map((r, i) => curveOf(r, sk[i], sk[(i + 1) % n]));
    const region = { pts: sk, bulges };
    return {
      region,
      sides: rows.map((r, i) => ({
        label: labelOf(i), p: sk[i], q: sk[(i + 1) % n], bulge: bulges[i], est: !!r.est,
        text: stats[i] && Number.isFinite(stats[i].len) ? ft(stats[i].len) : '?', unknown: !(stats[i] && Number.isFinite(stats[i].len)), small: false,
      })),
    };
  };
  const outlineStats = res.sides.map((s) => s.status);
  const o = mk(area.steps, pts, outlineStats, (i) => res.sides[i].letter);
  const shapes = [{ kind: 'outline', ring: flatten(o.region), ccw: isCcw(pts), sides: o.sides }];
  area.cutouts.forEach((c, k) => {
    if (c.kind !== 'traced' || !c.sketch || c.sketch.length !== c.steps.length) return;
    const stats = res.cutouts[k].stats || [];
    const m = mk(c.steps, c.sketch, stats, (i) => cutLetter(k, i));
    m.sides.forEach((s) => { s.small = true; });
    shapes.push({ kind: 'cutout', ring: flatten(m.region), ccw: isCcw(c.sketch), tag: `C${k + 1}`, dimText: '', sides: m.sides });
  });
  return { shapes, gap: null, bars: null, sketch: true, aria: 'Rough sketch from the photo, not to scale' };
}

// Sides done so far when the outline is not finished yet (no fill, no area).
export function planFromPartial(res) {
  const pts = [{ x: 0, y: 0 }];
  const sides = [];
  for (let i = 0; i < res.sides.length; i++) {
    const st = res.sides[i].status;
    if (!st.complete) break;
    const p = pts[pts.length - 1];
    const rad = (st.dirDeg * Math.PI) / 180;
    const c = { 0: [1, 0], 90: [0, 1], 180: [-1, 0], 270: [0, -1] }[st.dirDeg];
    const q = { x: p.x + st.len * (c ? c[0] : Math.cos(rad)), y: p.y + st.len * (c ? c[1] : Math.sin(rad)) };
    pts.push(q);
    sides.push({ label: res.sides[i].letter, p, q, bulge: 0, text: ft(st.len), est: !!res.sides[i].row.est });
  }
  if (!sides.length) return null;
  return { shapes: [{ kind: 'outline', open: true, ring: pts, ccw: true, sides }], gap: null, bars: null, partial: true, aria: 'Sides entered so far' };
}

// ---------------------------------------------------------------- drawing
export function emptyPlan(message) {
  return `<svg class="plan" viewBox="0 0 600 220" role="img" aria-label="${esc(message)}"><text class="pl-empty" x="300" y="112" text-anchor="middle">${esc(message)}</text></svg>`;
}

const GLYPH_W = 0.56; // average glyph width / font size for tabular figures
const rad = (d) => (d * Math.PI) / 180;

// Geometry of one side's dimension line, its letter circle and its default label slot (screen space).
function sideGeom(side, sh, X, Y, s, narrow) {
  const { p, q } = side;
  const dx = q.x - p.x;
  const dy = q.y - p.y;
  const c = Math.hypot(dx, dy);
  if (c < 1e-9) return null;
  const o = sh.ccw === false ? -1 : 1;
  const nx = (o * dy) / c; // outward unit normal, screen space (screen y is flipped)
  const ny = (o * dx) / c;
  const bulge = side.bulge || 0;
  const small = !!side.small;
  const midX = X((p.x + q.x) / 2 + ((o * dy) / c) * bulge);
  const midY = Y((p.y + q.y) / 2 + ((-o * dx) / c) * bulge);
  const off = (small ? 16 : narrow ? 20 : 26) + Math.max(0, bulge) * s; // same offset for every side
  const P = { x: X(p.x), y: Y(p.y) };
  const Q = { x: X(q.x), y: Y(q.y) };
  const A = { x: P.x + nx * off, y: P.y + ny * off };
  const B = { x: Q.x + nx * off, y: Q.y + ny * off };
  const len = Math.hypot(B.x - A.x, B.y - A.y) || 1;
  let ang = (Math.atan2(B.y - A.y, B.x - A.x) * 180) / Math.PI;
  if (ang > 90) ang -= 180;
  if (ang < -90) ang += 180;
  const text = small ? `${side.label} ${side.text}` : `${side.label} ${side.text}${side.est ? ' (est.)' : ''}`;
  return {
    side, small, P, Q, A, B, nx, ny, tx: (B.x - A.x) / len, ty: (B.y - A.y) / len, len, ang, text, short: `${side.text}${side.est ? ' (est.)' : ''}`, midX, midY,
    badgeR: small ? 8 : 11, fs0: small ? 10.5 : narrow ? 11.5 : 12.5,
  };
}

function textBox(cx, cy, w, h, angDeg) {
  const a = rad(angDeg);
  const hx = (w / 2) * Math.abs(Math.cos(a)) + (h / 2) * Math.abs(Math.sin(a));
  const hy = (w / 2) * Math.abs(Math.sin(a)) + (h / 2) * Math.abs(Math.cos(a));
  return { x0: cx - hx, y0: cy - hy, x1: cx + hx, y1: cy + hy };
}
const boxesHit = (a, b) => a.x0 < b.x1 + 2 && b.x0 < a.x1 + 2 && a.y0 < b.y1 + 2 && b.y0 < a.y1 + 2;
function circleHitsBox(c, b) {
  const nx = Math.max(b.x0, Math.min(c.x, b.x1));
  const ny = Math.max(b.y0, Math.min(c.y, b.y1));
  return Math.hypot(nx - c.x, ny - c.y) < c.r + 2;
}

// Finds a slot for one dimension label that touches no letter circle, tag or earlier label:
// slide along the line (a label may overhang the line ends by a quarter of its width), lift a row
// further out, drop the font a point or two, and as a last resort drop the "C " prefix (the letter
// circle on the side already names it).
function placeText(g, obstacles, placed) {
  const sizes = [g.fs0, g.fs0 - 1, g.fs0 - 2].map((f) => Math.max(9.5, f)).filter((f, i, arr) => arr.indexOf(f) === i);
  const variants = [{ text: g.text, extra: 0 }, { text: g.short, extra: 0.25 }];
  let best = null;
  for (const variant of variants) {
    for (const fs of sizes) {
      const w = variant.text.length * fs * GLYPH_W + 6;
      const h = fs + 4;
      const strict = w <= g.len - 12;
      const loose = w * 0.75 <= g.len - 12;
      const lo = loose ? w / 4 + 6 : g.len / 2;
      const hi = loose ? g.len - w / 4 - 6 : g.len / 2;
      const us = loose ? [0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8, 0.1, 0.9] : [0.5];
      for (const lift of [fs * 0.85, fs * 0.85 + h]) {
        for (const u of us) {
          const along = Math.min(Math.max(g.len * u, lo), hi);
          const cx = g.A.x + g.tx * along + g.nx * lift;
          const cy = g.A.y + g.ty * along + g.ny * lift;
          const box = textBox(cx, cy, w, h, g.ang);
          let hits = 0;
          for (const ob of obstacles) if (ob.c ? circleHitsBox(ob.c, box) : boxesHit(ob.b, box)) hits++;
          for (const pb of placed) if (boxesHit(pb, box)) hits++;
          const cand = { cx, cy, fs, box, text: variant.text, hits: hits + (strict ? 0 : 0.4) + variant.extra };
          if (cand.hits === 0) return cand;
          if (!best || cand.hits < best.hits) best = cand;
        }
      }
    }
  }
  return best;
}

// Greedy placement depends on who goes first, so try several orders and keep the one with the fewest overlaps.
function placeAll(geoms, obstacles) {
  const byLen = [...geoms].sort((a, b) => b.len - a.len);
  const orders = [byLen, [...byLen].reverse()];
  let seed = 7;
  const rnd = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
  for (let i = 0; i < 24 && geoms.length > 2; i++) {
    const o = [...geoms];
    for (let k = o.length - 1; k > 0; k--) { const j = Math.floor(rnd() * (k + 1)); [o[k], o[j]] = [o[j], o[k]]; }
    orders.push(o);
  }
  let best = null;
  for (const order of orders) {
    const placed = [];
    const spots = new Map();
    let cost = 0;
    for (const g of order) {
      const spot = placeText(g, obstacles, placed);
      spots.set(g, spot);
      placed.push(spot.box);
      cost += spot.hits * 10 + (spot.fs < g.fs0 ? 1 : 0) + (spot.text === g.text ? 0 : 1);
    }
    if (!best || cost < best.cost) best = { cost, spots };
    if (cost === 0) break;
  }
  return best.spots;
}

function sideSvg(g, spot) {
  const { A, B, P, Q, nx, ny, tx, ty, side, small } = g;
  const ext = (E, F) => `M${r1(E.x + nx * 5)} ${r1(E.y + ny * 5)}L${r1(F.x + nx * 6)} ${r1(F.y + ny * 6)}`;
  const tick = (E) => `M${r1(E.x - tx * 4 - nx * 4)} ${r1(E.y - ty * 4 - ny * 4)}L${r1(E.x + tx * 4 + nx * 4)} ${r1(E.y + ty * 4 + ny * 4)}`;
  const cls = `pl-dimtext${side.unknown ? ' unk' : ''}${side.est ? ' est' : ''}${small ? ' small' : ''}`;
  return `<g class="pl-dim"><path class="pl-ext" d="${ext(P, A)}${ext(Q, B)}"/>`
    + `<path class="pl-dimline" d="M${r1(A.x)} ${r1(A.y)}L${r1(B.x)} ${r1(B.y)}${tick(A)}${tick(B)}"/>`
    + `<text class="${cls}" style="font-size:${r1(spot.fs)}px" transform="translate(${r1(spot.cx)} ${r1(spot.cy)}) rotate(${r1(g.ang)})" text-anchor="middle" dominant-baseline="central">${esc(spot.text)}</text></g>`
    + `<g class="pl-badge${small ? ' small' : ''}"><circle cx="${g.midX}" cy="${g.midY}" r="${g.badgeR}"/><text x="${g.midX}" y="${g.midY}" text-anchor="middle" dominant-baseline="central">${esc(side.label)}</text></g>`;
}

export function renderPlan(model, { width = 700 } = {}) {
  const all = [];
  for (const sh of model.shapes) for (const p of sh.ring) all.push(p);
  if (model.gap) all.push(model.gap.a, model.gap.b);
  if (!all.length) return emptyPlan('Your drawing appears here as you add sides.');
  const bb = ringBounds(all);
  const bw = Math.max(bb.maxX - bb.minX, 1e-6);
  const bh = Math.max(bb.maxY - bb.minY, 1e-6);
  const W = Math.max(280, Math.min(Math.round(width), 1100));
  const M = W < 520 ? 58 : 76;
  const maxH = Math.max(300, Math.min(W * 0.85, 640));
  const s = Math.min((W - 2 * M) / bw, (maxH - 2 * M) / bh);
  const offX = (W - bw * s) / 2;
  const H = Math.round(bh * s + 2 * M);
  const X = (x) => r1(offX + (x - bb.minX) * s);
  const Y = (y) => r1(M + (bb.maxY - y) * s);
  const id = `pl${++svgCounter}`;
  const out = [];
  out.push(`<svg class="plan" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(model.aria || 'Plan')}" xmlns="http://www.w3.org/2000/svg">`);
  out.push(`<defs><pattern id="${id}" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" class="pl-hatch"/></pattern></defs>`);

  const geoms = [];
  for (const sh of model.shapes) {
    for (const side of sh.sides) {
      const g = sideGeom(side, sh, X, Y, s, W < 520);
      if (g) geoms.push(g);
    }
  }
  const obstacles = geoms.map((g) => ({ c: { x: g.midX, y: g.midY, r: g.badgeR } }));

  const d = (ring, close) => `M${ring.map((p) => `${X(p.x)} ${Y(p.y)}`).join('L')}${close ? 'Z' : ''}`;
  for (const sh of model.shapes) {
    if (sh.kind === 'outline') out.push(`<path class="${sh.open ? 'pl-open' : 'pl-outline'}" d="${d(sh.ring, !sh.open)}"/>`);
  }
  if (model.bars && model.bars.length) {
    out.push(`<path class="pl-bars" d="${model.bars.map((b) => `M${X(b.x0)} ${Y(b.y0)}L${X(b.x1)} ${Y(b.y1)}`).join('')}"/>`);
  }
  for (const sh of model.shapes) {
    if (sh.kind !== 'cutout') continue;
    out.push(`<path class="pl-cut-fill" fill="url(#${id})" d="${d(sh.ring, true)}"/><path class="pl-cut" d="${d(sh.ring, true)}"/>`);
    const cb = ringBounds(sh.ring);
    const cx = X((cb.minX + cb.maxX) / 2);
    const cy = Y((cb.minY + cb.maxY) / 2);
    const wide = (cb.maxX - cb.minX) * s;
    out.push(`<g class="pl-tag"><rect x="${cx - 14}" y="${cy - 10}" width="28" height="20" rx="4"/><text x="${cx}" y="${cy}" text-anchor="middle" dominant-baseline="central">${esc(sh.tag)}</text></g>`);
    obstacles.push({ b: { x0: cx - 14, y0: cy - 10, x1: cx + 14, y1: cy + 10 } });
    if (sh.dimText && wide > 90) {
      out.push(`<text class="pl-cutdim" x="${cx}" y="${cy + 22}" text-anchor="middle">${esc(sh.dimText)}</text>`);
      const hw = (sh.dimText.length * 11 * GLYPH_W) / 2;
      obstacles.push({ b: { x0: cx - hw, y0: cy + 14, x1: cx + hw, y1: cy + 30 } });
    }
  }
  const origin = model.sketch ? model.shapes[0].ring[0] : { x: 0, y: 0 };
  out.push(`<g class="pl-start"><circle cx="${X(origin.x)}" cy="${Y(origin.y)}" r="4"/></g>`);

  const spots = placeAll(geoms, obstacles);
  for (const g of geoms) out.push(sideSvg(g, spots.get(g)));

  if (model.gap) {
    const a = model.gap.a;
    const b = model.gap.b;
    out.push(`<path class="pl-gap" d="M${X(a.x)} ${Y(a.y)}L${X(b.x)} ${Y(b.y)}"/><circle class="pl-gap-dot" cx="${X(a.x)}" cy="${Y(a.y)}" r="4.5"/>`);
    out.push(`<text class="pl-gap-text" x="${(X(a.x) + X(b.x)) / 2 + 10}" y="${(Y(a.y) + Y(b.y)) / 2 - 8}">gap ${esc(model.gap.text)}</text>`);
  }
  if (model.sketch) out.push(`<text class="pl-note" x="14" y="22">Rough sketch from your photo, not to scale. Type the lengths to draw it true.</text>`);
  else if (model.partial) out.push(`<text class="pl-note" x="14" y="22">Sides so far. Finish the rest to see the whole shape.</text>`);
  out.push('</svg>');
  return out.join('');
}
