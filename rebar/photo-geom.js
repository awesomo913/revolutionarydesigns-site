// photo-geom.js - pure helpers that turn tapped photo corners into walk rows, and estimate sides from
// one real measurement. No DOM. Photo points are {x,y} with y UP, in "photo units" (image width = 1).
import { formatFtIn } from './rebar-math.js';
import { newRow, rowStatus, letter } from './calc.js';

export const SNAP_MODES = ['45', '90', 'exact'];

const norm360 = (d) => ((d % 360) + 360) % 360;
const angleOf = (a, b) => norm360((Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI);
const dist = (a, b) => Math.hypot(b.x - a.x, b.y - a.y);

export function snapAngle(deg, mode) {
  if (mode === 'exact') return norm360(Math.round(deg * 10) / 10);
  const step = mode === '90' ? 90 : 45;
  return norm360(Math.round(deg / step) * step) % 360;
}

function rotate(pts, about, deg) {
  const r = (deg * Math.PI) / 180;
  const c = Math.cos(r);
  const s = Math.sin(r);
  return pts.map((p) => ({ x: about.x + (p.x - about.x) * c - (p.y - about.y) * s, y: about.y + (p.x - about.x) * s + (p.y - about.y) * c }));
}

// How far to turn a whole photo so that its first outline edge lands exactly on a snapped direction.
export function frameRotation(outlinePts, mode) {
  if (mode === 'exact' || outlinePts.length < 2) return 0;
  const a = angleOf(outlinePts[0], outlinePts[1]);
  return snapAngle(a, mode) - a;
}

// Corner points -> walk rows (lengths left blank). curves[i] = 1 curves out, -1 in, 0 straight.
// Points are first turned by `rotation` degrees about `origin` (the outline's first corner).
export function shapeToRows(pts, curves, mode, rotation = 0, origin = pts[0]) {
  const rotated = rotation ? rotate(pts, origin, rotation) : pts.map((p) => ({ ...p }));
  const rows = rotated.map((p, i) => {
    const q = rotated[(i + 1) % rotated.length];
    const snapped = snapAngle(angleOf(p, q), mode);
    const row = newRow('R');
    const cardinal = { 0: 'R', 90: 'U', 180: 'L', 270: 'D' }[snapped];
    if (cardinal) row.dir = cardinal;
    else { row.dir = 'ANG'; row.angText = String(snapped); }
    const c = curves && curves[i];
    if (c) row.curve = c > 0 ? 'out' : 'in';
    return row;
  });
  return { pts: rotated, rows };
}

// Why "Use these sides" has to wait (null when it can go ahead). `base` = cutouts already in the area.
export function useBlocker(shapes, base = 0) {
  const outline = shapes.find((s) => s.kind === 'outline');
  if (!outline || !outline.done) return 'Finish the outline first: tap its first corner again, or press Finish outline.';
  const cuts = shapes.filter((s) => s.kind === 'cutout');
  const open = cuts.find((s) => !s.done);
  if (open) return `Finish or remove cutout ${base + cuts.indexOf(open) + 1} first: press Finish cutout (it needs at least 3 corners), or press Undo last corner until it is gone.`;
  return null;
}

const roundInch = (ft) => Math.max(1, Math.round(ft * 12)) / 12;

// Works out the sides (and cutout positions) that are still blank, from ONE typed side.
// Returns { ok:false, reason } or { ok:true, ftPerUnit, outline:[lenText|null], cutouts:[{ id, rows:[lenText|null], sxText, syText }] }.
export function estimateFromPhoto(area) {
  const rows = area.steps;
  const sk = area.sketch;
  if (!sk || sk.length !== rows.length || rows.length < 3) return { ok: false, reason: 'There is no photo outline to estimate from. Use "Start from a photo" and press "Use as outline" first.' };
  const stats = rows.map(rowStatus);
  const ref = rows.findIndex((r, i) => !r.est && Number.isFinite(stats[i].len));
  if (ref < 0) return { ok: false, reason: 'Type the real length of at least one side first (one you measured), then ask for the estimate.' };
  const photoLen = (i) => dist(sk[i], sk[(i + 1) % sk.length]);
  if (!(photoLen(ref) > 0)) return { ok: false, reason: 'That side has no length in the photo, so it cannot be used as the scale. Pick another side to type.' };
  const ftPerUnit = stats[ref].len / photoLen(ref);
  const fill = (rws, sketch) => rws.map((r, i) => {
    const st = rowStatus(r);
    if (!(st.blank || r.est)) return null;
    return formatFtIn(roundInch(dist(sketch[i], sketch[(i + 1) % sketch.length]) * ftPerUnit));
  });
  const outline = fill(rows, sk);
  const cutouts = [];
  area.cutouts.forEach((c) => {
    if (c.kind !== 'traced' || !c.sketch || c.sketch.length !== c.steps.length || c.steps.length < 3) return;
    cutouts.push({
      id: c.id,
      rows: fill(c.steps, c.sketch),
      sxText: String(c.sxText).trim() === '' || c.est ? formatFtIn((c.sketch[0].x - sk[0].x) * ftPerUnit) : null,
      syText: String(c.syText).trim() === '' || c.est ? formatFtIn((c.sketch[0].y - sk[0].y) * ftPerUnit) : null,
    });
  });
  return { ok: true, ftPerUnit, refLetter: letter(ref), outline, cutouts };
}

// Offsets can be negative; formatFtIn writes the minus sign in front, which parseSignedFtIn accepts.
