// photo.js - "Start from a photo": show a picture, tap the slab corners in order, tap cutout corners,
// tap a side's letter to curve it. Produces walk rows with blank lengths (see photo-geom.js).
// The picture never leaves the browser: it is read through an object URL and drawn to a canvas.
import { flatten } from './rebar-math.js';
import { letter, cutLetter } from './calc.js';
import { frameRotation, shapeToRows, useBlocker } from './photo-geom.js';

const TAP_MAX_MOVE = 10;   // px a finger may wander and still be a tap
const HIT_VERTEX = 14;     // px
const HIT_LETTER = 20;     // px
const NOMINAL_BULGE = 0.12;
const COLORS = { outline: '#ff8a45', cutout: '#35b2ff' };

const HTML = `
<div class="photo-pick">
  <label class="btn primary photo-file"><input type="file" accept="image/*" capture="environment" class="sr-file" data-role="cam"><span>Take a photo</span></label>
  <label class="btn photo-file"><input type="file" accept="image/*" class="sr-file" data-role="pick"><span>Choose a picture</span></label>
</div>
<p class="hint">Stand square to the slab if you can. Your picture stays on this device; nothing is uploaded.</p>
<div class="photo-work" hidden>
  <div class="photo-modes" role="radiogroup" aria-label="Snap the sides to">
    <span class="lbl">Snap sides to</span>
    <button type="button" role="radio" data-snap="45" aria-checked="true">45 deg</button>
    <button type="button" role="radio" data-snap="90" aria-checked="false">90 deg only</button>
    <button type="button" role="radio" data-snap="exact" aria-checked="false">Exactly as tapped</button>
  </div>
  <div class="photo-bar">
    <button type="button" class="btn" data-do="undo">Undo last corner</button>
    <button type="button" class="btn" data-do="finish">Finish outline</button>
    <button type="button" class="btn" data-do="cutout">Add a cutout</button>
    <button type="button" class="btn" data-do="clear">Start over</button>
    <span class="zoom"><span class="zoom-cap" aria-hidden="true">Zoom</span>
      <button type="button" data-do="zoomout" aria-label="Zoom out" title="Zoom out"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h10"/></svg></button>
      <button type="button" data-do="zoomin" aria-label="Zoom in" title="Zoom in"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h10M8 3v10"/></svg></button></span>
  </div>
  <p class="photo-status" aria-live="polite"></p>
  <div class="photo-scroll"><canvas class="photo-canvas" aria-label="Your photo. Tap the corners of the slab in order."></canvas></div>
  <div class="photo-use"><button type="button" class="btn primary" data-do="use" disabled>Use these sides</button><span class="hint">Lengths stay blank for you to fill in. Photos taken at an angle distort real lengths.</span></div>
</div>`;

export function createPhotoTool(root, api) {
  root.innerHTML = HTML;
  const $ = (s) => root.querySelector(s);
  const work = $('.photo-work');
  const canvas = $('.photo-canvas');
  const ctx = canvas.getContext('2d');
  const scroll = $('.photo-scroll');
  const status = $('.photo-status');
  const st = { img: null, url: null, shapes: [], snap: '45', zoom: 1, cssW: 0, cssH: 0, bg: null, drag: null, down: null };

  // ---- loading
  function loadFile(file) {
    if (!file) return;
    if (!/^image\//.test(file.type) && !/\.(jpe?g|png|webp|gif|bmp|heic|heif)$/i.test(file.name)) {
      api.notify('That file is not a picture. Choose a JPG or PNG photo.', 'error');
      return;
    }
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      if (st.url) URL.revokeObjectURL(st.url);
      st.img = img;
      st.url = url;
      st.shapes = [];
      st.zoom = 1;
      work.hidden = false;
      layout();
      api.notify('', 'clear');
      refresh();
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      console.error('photo failed to decode', file.name, file.type);
      api.notify("That picture could not be opened. Try a JPG or PNG (phone photos in HEIC format may need to be shared as JPG).", 'error');
    };
    img.src = url;
  }
  root.addEventListener('change', (e) => {
    if (e.target.classList.contains('sr-file')) {
      loadFile(e.target.files && e.target.files[0]);
      e.target.value = '';
    }
  });

  // ---- sizing and drawing
  function layout() {
    if (!st.img) return;
    const base = Math.max(260, scroll.clientWidth || 320);
    st.cssW = base * st.zoom;
    st.cssH = st.cssW * (st.img.naturalHeight / st.img.naturalWidth);
    const dpr = Math.min(window.devicePixelRatio || 1, 2, Math.sqrt(16e6 / (st.cssW * st.cssH)));
    canvas.width = Math.round(st.cssW * dpr);
    canvas.height = Math.round(st.cssH * dpr);
    canvas.style.width = `${st.cssW}px`;
    canvas.style.height = `${st.cssH}px`;
    st.dpr = dpr;
    st.bg = document.createElement('canvas');
    st.bg.width = canvas.width;
    st.bg.height = canvas.height;
    st.bg.getContext('2d').drawImage(st.img, 0, 0, canvas.width, canvas.height);
  }

  const px = (p) => ({ x: p.u * st.cssW, y: p.v * st.cssW });
  const unit = (x, y) => ({ u: x / st.cssW, v: y / st.cssW });
  const yUp = (pts) => pts.map((p) => ({ x: p.u, y: -p.v }));

  // outline + bulges for drawing curved sides (same in/out meaning as the walk)
  function shapeRing(sh) {
    const pts = yUp(sh.pts);
    const bulges = pts.map((p, i) => {
      const c = sh.curves[i];
      const q = pts[(i + 1) % pts.length];
      return c ? c * NOMINAL_BULGE * Math.hypot(q.x - p.x, q.y - p.y) : 0;
    });
    return { pts, bulges };
  }

  function sideMid(sh, i) {
    const n = sh.pts.length;
    const a = sh.pts[i];
    const b = sh.pts[(i + 1) % n];
    if (!sh.curves[i] || n < 3) return { x: ((a.u + b.u) / 2) * st.cssW, y: ((a.v + b.v) / 2) * st.cssW };
    const region = shapeRing(sh); // y up
    const p = region.pts[i];
    const q = region.pts[(i + 1) % n];
    const dx = q.x - p.x;
    const dy = q.y - p.y;
    const len = Math.hypot(dx, dy) || 1;
    const o = signed(region.pts) >= 0 ? 1 : -1;
    const h = region.bulges[i];
    return { x: ((p.x + q.x) / 2 + ((o * dy) / len) * h) * st.cssW, y: -((p.y + q.y) / 2 + ((-o * dx) / len) * h) * st.cssW };
  }

  function signed(pts) {
    let a = 0;
    pts.forEach((p, i) => { const q = pts[(i + 1) % pts.length]; a += p.x * q.y - q.x * p.y; });
    return a / 2;
  }

  function draw() {
    if (!st.img) return;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(st.bg, 0, 0);
    ctx.setTransform(st.dpr, 0, 0, st.dpr, 0, 0);
    const lengths = api.getOutlineLengths();
    const base = api.cutoutBase();
    let cutIdx = 0;
    st.shapes.forEach((sh) => {
      const col = COLORS[sh.kind];
      const k = sh.kind === 'cutout' ? base + cutIdx++ : -1;
      const n = sh.pts.length;
      if (n >= 2) {
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        const path = new Path2D();
        if (sh.done && n >= 3) {
          const ring = flatten(shapeRing(sh));
          ring.forEach((p, i) => (i ? path.lineTo(p.x * st.cssW, -p.y * st.cssW) : path.moveTo(p.x * st.cssW, -p.y * st.cssW)));
          path.closePath();
        } else {
          sh.pts.forEach((p, i) => { const q = px(p); if (i) path.lineTo(q.x, q.y); else path.moveTo(q.x, q.y); });
        }
        ctx.strokeStyle = 'rgba(0,0,0,.65)';
        ctx.lineWidth = 6;
        ctx.stroke(path);
        ctx.strokeStyle = col;
        ctx.lineWidth = 3;
        ctx.stroke(path);
        if (sh.done) { ctx.fillStyle = `${col}33`; ctx.fill(path); }
      }
      sh.pts.forEach((p, i) => {
        const q = px(p);
        ctx.beginPath();
        ctx.arc(q.x, q.y, 11, 0, Math.PI * 2);
        ctx.fillStyle = '#1b1612';
        ctx.fill();
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = col;
        ctx.stroke();
        ctx.fillStyle = '#fff';
        ctx.font = '700 12px system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(i + 1), q.x, q.y + 0.5);
      });
      if (sh.done) {
        sh.pts.forEach((_, i) => {
          const m = sideMid(sh, i);
          const label = sh.kind === 'outline' ? letter(i) : cutLetter(k, i);
          const typed = sh.kind === 'outline' && lengths[i] ? ` ${lengths[i]}` : '';
          const text = `${label}${typed}`;
          ctx.font = '700 13px system-ui, sans-serif';
          const w = Math.max(24, ctx.measureText(text).width + 14);
          ctx.fillStyle = 'rgba(255,255,255,.95)';
          ctx.strokeStyle = col;
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.roundRect(m.x - w / 2, m.y - 12, w, 24, 12);
          ctx.fill();
          ctx.stroke();
          ctx.fillStyle = '#1b1612';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(text, m.x, m.y + 0.5);
          if (sh.curves[i]) {
            ctx.font = '600 11px system-ui, sans-serif';
            ctx.fillStyle = '#fff';
            ctx.strokeStyle = 'rgba(0,0,0,.7)';
            ctx.lineWidth = 3;
            const t = sh.curves[i] > 0 ? 'curves out' : 'curves in';
            ctx.strokeText(t, m.x, m.y + 24);
            ctx.fillText(t, m.x, m.y + 24);
          }
        });
      }
    });
  }

  // ---- state helpers
  const activeShape = () => st.shapes.find((s) => !s.done);
  const outline = () => st.shapes.find((s) => s.kind === 'outline');

  function refresh() {
    const act = activeShape();
    const out = outline();
    const setDis = (sel, v) => { $(sel).disabled = v; };
    setDis('[data-do="finish"]', !act || act.pts.length < 3);
    $('[data-do="finish"]').textContent = act && act.kind === 'cutout' ? 'Finish cutout' : 'Finish outline';
    setDis('[data-do="cutout"]', !(out && out.done) || !!act);
    setDis('[data-do="undo"]', !st.shapes.length);
    setDis('[data-do="use"]', !(out && out.done));
    let msg;
    if (!st.img) msg = 'Choose a picture to begin.';
    else if (!out) msg = 'Tap each corner of the slab, going around in order. A finger is fine.';
    else if (act && act.kind === 'outline') msg = `Corner ${act.pts.length} placed. Tap the next one${act.pts.length >= 3 ? ', or tap the first corner again to close the outline' : ''}.`;
    else if (act) msg = `Cutout: tap its corners in order${act.pts.length >= 3 ? ', then Finish cutout' : ''}.`;
    else msg = 'Outline done. Tap a letter to curve that side, add any existing-foundation cutouts, then press Use these sides.';
    status.textContent = msg;
    root.querySelectorAll('[data-snap]').forEach((b) => b.setAttribute('aria-checked', String(b.dataset.snap === st.snap)));
    draw();
  }

  function eventPoint(e) {
    const r = canvas.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }

  function hitVertex(x, y) {
    for (const sh of st.shapes) {
      for (let i = 0; i < sh.pts.length; i++) {
        const q = px(sh.pts[i]);
        if (Math.hypot(q.x - x, q.y - y) <= HIT_VERTEX) return { sh, i };
      }
    }
    return null;
  }

  function hitLetter(x, y) {
    for (const sh of st.shapes) {
      if (!sh.done) continue;
      for (let i = 0; i < sh.pts.length; i++) {
        const m = sideMid(sh, i);
        if (Math.hypot(m.x - x, m.y - y) <= HIT_LETTER) return { sh, i };
      }
    }
    return null;
  }

  function onTap(x, y) {
    const l = hitLetter(x, y);
    if (l) {
      l.sh.curves[l.i] = l.sh.curves[l.i] === 0 ? 1 : l.sh.curves[l.i] === 1 ? -1 : 0;
      refresh();
      return;
    }
    let act = activeShape();
    if (!act && !outline()) {
      act = { kind: 'outline', pts: [], curves: [], done: false };
      st.shapes.push(act);
    }
    if (!act) return;
    if (act.pts.length >= 3) {
      const q = px(act.pts[0]);
      if (Math.hypot(q.x - x, q.y - y) <= HIT_VERTEX + 4) { finish(); return; }
    }
    act.pts.push(unit(x, y));
    act.curves.push(0);
    refresh();
  }

  function finish() {
    const act = activeShape();
    if (act && act.pts.length >= 3) { act.done = true; refresh(); }
  }

  // pointer handling: tap = down+up without moving (so scrolling and pinch-zoom never add corners);
  // mouse/pen can also drag a corner
  canvas.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    const p = eventPoint(e);
    st.down = { ...p, t: Date.now(), type: e.pointerType };
    if (e.pointerType !== 'touch') {
      const v = hitVertex(p.x, p.y);
      if (v) { st.drag = v; canvas.setPointerCapture(e.pointerId); }
    }
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!st.drag) return;
    const p = eventPoint(e);
    st.drag.sh.pts[st.drag.i] = unit(Math.max(0, Math.min(st.cssW, p.x)), Math.max(0, Math.min(st.cssH, p.y)));
    st.drag.moved = true;
    draw();
  });
  canvas.addEventListener('pointerup', (e) => {
    const p = eventPoint(e);
    const d = st.down;
    st.down = null;
    if (st.drag) {
      const moved = st.drag.moved;
      st.drag = null;
      if (moved) { refresh(); return; }
    }
    if (!d) return;
    if (Math.hypot(p.x - d.x, p.y - d.y) <= TAP_MAX_MOVE && Date.now() - d.t < 800) onTap(p.x, p.y);
  });
  canvas.addEventListener('pointercancel', () => { st.down = null; st.drag = null; });

  // ---- buttons
  root.addEventListener('click', (e) => {
    const snap = e.target.closest('[data-snap]');
    if (snap) { st.snap = snap.dataset.snap; refresh(); return; }
    const b = e.target.closest('[data-do]');
    if (!b) return;
    switch (b.dataset.do) {
      case 'undo': {
        const sh = st.shapes[st.shapes.length - 1];
        if (!sh) break;
        sh.done = false;
        sh.pts.pop();
        sh.curves.pop();
        if (!sh.pts.length) st.shapes.pop();
        refresh();
        break;
      }
      case 'clear':
        if (!st.shapes.length || window.confirm('Clear all the corners you tapped?')) { st.shapes = []; refresh(); }
        break;
      case 'finish': finish(); break;
      case 'cutout': st.shapes.push({ kind: 'cutout', pts: [], curves: [], done: false }); refresh(); break;
      case 'zoomin': st.zoom = Math.min(4, st.zoom + 0.5); layout(); refresh(); break;
      case 'zoomout': st.zoom = Math.max(1, st.zoom - 0.5); layout(); refresh(); break;
      case 'use': use(); break;
      default: break;
    }
  });
  if (typeof ResizeObserver === 'function') {
    let last = 0;
    new ResizeObserver(() => {
      window.requestAnimationFrame(() => {
        const w = scroll.clientWidth;
        if (st.img && w && Math.abs(w - last) > 2) { last = w; layout(); refresh(); }
      });
    }).observe(scroll);
  }

  function use() {
    const block = useBlocker(st.shapes, api.cutoutBase());
    if (block) {
      status.textContent = block;
      api.notify(block, 'warn');
      return;
    }
    const out = outline();
    const o = yUp(out.pts);
    const rot = frameRotation(o, st.snap);
    const base = shapeToRows(o, out.curves, st.snap, rot, o[0]);
    const cuts = st.shapes.filter((s) => s.kind === 'cutout' && s.done && s.pts.length >= 3)
      .map((s) => shapeToRows(yUp(s.pts), s.curves, st.snap, rot, o[0]));
    api.onUse({ rows: base.rows, sketch: base.pts, cutouts: cuts.map((c) => ({ rows: c.rows, sketch: c.pts })) });
  }

  return {
    openPicker(camera) { root.querySelector(camera ? '[data-role="cam"]' : '[data-role="pick"]').click(); },
    refresh() { if (st.img) draw(); },
  };
}
