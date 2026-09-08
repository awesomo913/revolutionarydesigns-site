import './scrollcraft.js';
import {initDeskDetails} from './desk-details.js?v=20260907-desk';
import {initEvidence} from './evidence.js?v=20260907-evidence';

const motionQuery = matchMedia('(prefers-reduced-motion: reduce)');
let manualPause = false;
const hero = document.querySelector('.hero');
const desk = document.querySelector('.desk');
const phone = document.querySelector('.phone-plane');
const listing = document.querySelector('.listing-plane');
const paper = document.querySelector('.report-plane');
const forest = document.querySelector('.bamboo-project');
const forestArt = document.querySelector('.forest-art');
const forestBack = document.querySelector('.forest-back');
const foreground = document.querySelector('.bamboo-foreground');
const cactus = document.querySelector('.cactus-visual img');
const motionButton = document.querySelector('.motion-toggle');
let frame = 0, px = 0, py = 0, tx = 0, ty = 0;
const clamp = (x, min, max) => Math.min(max, Math.max(min, x));
const paused = () => manualPause || motionQuery.matches;

try { window.ScrollCraft.mount(document); } catch (error) { console.warn('Optional scroll engine unavailable', error); }

function paint() {
  frame = 0;
  if (document.hidden) return;
  const still = paused();
  px = still ? 0 : px + (tx - px) * .085;
  py = still ? 0 : py + (ty - py) * .085;
  const box = hero.getBoundingClientRect();
  const travel = still ? 0 : clamp(-box.top / Math.max(box.height, 1), 0, 1);
  const small = innerWidth <= 900;
  const scale = small ? .4 : 1;
  desk.style.transform = `translate3d(${px * 3}px,${travel * 20}px,0)`;
  phone.style.transform = `translate3d(${px * 11 * scale}px,${py * 7 * scale - travel * 36}px,0) rotate(${px * .6}deg)`;
  listing.style.transform = `translate3d(${px * 6 * scale}px,${py * 3 * scale - travel * 16}px,0) rotate(${px * .3}deg)`;
  paper.style.transform = `translate3d(${px * 18 * scale}px,${py * 9 * scale + travel * 80}px,0) rotate(${-8 + px * .8 + travel * 8}deg) rotateX(${12 - travel * 12}deg)`;
  hero.classList.toggle('engaged', still || travel > .07 || Math.abs(px) > .12);
  const fb = forest.getBoundingClientRect();
  const fp = still ? 0 : clamp((innerHeight / 2 - fb.top) / (fb.height + innerHeight), -.4, 1);
  forestArt.style.transform = `translate3d(0,${fp * -60}px,0) scale(1.04)`;
  forestBack.style.transform = `translate3d(0,${fp * -22}px,0)`;
  foreground.style.transform = `translate3d(0,${fp * 54}px,0)`;
  const cb = cactus.parentElement.getBoundingClientRect();
  const cp = still ? 0 : clamp((innerHeight - cb.top) / (innerHeight + cb.height), 0, 1);
  cactus.style.transform = `scale(${1.035 + cp * .045}) translateY(${cp * -8}px)`;
  if (!still && (Math.abs(tx - px) > .002 || Math.abs(ty - py) > .002)) requestPaint();
}
function requestPaint() { if (!frame) frame = requestAnimationFrame(paint); }
hero.addEventListener('pointermove', event => { if (event.pointerType !== 'mouse' || paused()) return; const r = hero.getBoundingClientRect(); tx = clamp((event.clientX - r.left) / r.width * 2 - 1, -1, 1); ty = clamp((event.clientY - r.top) / r.height * 2 - 1, -1, 1); requestPaint(); });
hero.addEventListener('pointerleave', () => { tx = 0; ty = 0; requestPaint(); });
addEventListener('scroll', requestPaint, {passive:true});
addEventListener('resize', requestPaint);
document.addEventListener('visibilitychange', requestPaint);
motionQuery.addEventListener('change', updateMotion);
function updateMotion() { const isPaused = paused(); document.documentElement.classList.toggle('motion-paused', isPaused); motionButton.setAttribute('aria-pressed', String(isPaused)); motionButton.textContent = motionQuery.matches ? 'Reduced motion enabled' : isPaused ? 'Resume motion' : 'Pause motion'; motionButton.disabled = motionQuery.matches; requestPaint(); }
motionButton.addEventListener('click', () => { manualPause = !manualPause; updateMotion(); });
updateMotion();

const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('arrived'); observer.unobserve(entry.target); } }), {threshold:.12});
document.querySelectorAll('.arrive').forEach(el => observer.observe(el));
document.documentElement.classList.add('motion-ready');

initEvidence();
initDeskDetails();

const dialog = document.querySelector('.report-dialog');
let dialogOpener;
document.querySelectorAll('[data-report-open]').forEach(button => button.addEventListener('click', () => { dialogOpener = button; dialog.showModal(); document.body.style.overflow = 'hidden'; document.querySelector('.dialog-close').focus(); }));
document.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
dialog.addEventListener('close', () => { document.body.style.overflow = ''; dialogOpener?.focus({preventScroll:true}); });
document.querySelectorAll('.mobile-menu a').forEach(a => a.addEventListener('click', () => document.querySelector('.mobile-menu').open = false));
requestPaint();
