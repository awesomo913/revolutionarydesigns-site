// store.js - autosave to this browser, save/open job files, CSV download. Every failure comes back as a
// plain-English message (the caller shows it) and is also logged to the console.
import { sanitizeJob } from './calc.js';

const KEY = 'rebarTakeoff.job.v1';
const MAX_FILE_BYTES = 5 * 1024 * 1024;

export const PAUSED_MESSAGE =
  'Autosave is paused so the job saved in this browser is not written over. Save a job file or start a new job to turn it back on.';

export const NO_STORAGE_MESSAGE =
  'This browser is not letting the page save on your device (a private window or blocked site data can do that). Use "Save job file" to keep your work.';

export function loadAutosave() {
  let text;
  try {
    text = window.localStorage.getItem(KEY);
  } catch (e) {
    console.error('autosave read blocked', e);
    return { job: null, available: false, error: NO_STORAGE_MESSAGE };
  }
  if (text == null) return { job: null, available: true, error: null };
  try {
    return { job: sanitizeJob(JSON.parse(text)), available: true, error: null };
  } catch (e) {
    console.error('autosave unreadable', e);
    let kept = true;
    try { window.localStorage.setItem(`${KEY}.damaged`, text); } catch (e2) { kept = false; console.error('could not keep the damaged copy', e2); }
    return {
      job: null, available: true, pauseAutosave: !kept,
      error: kept
        ? `The autosaved job could not be read (${e.message}). Starting with a blank job; the damaged copy is still kept in this browser.`
        : `The autosaved job could not be read (${e.message}), and a backup copy of it could not be saved. ${PAUSED_MESSAGE}`,
    };
  }
}

export function saveAutosave(job) {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(job));
    return { ok: true, error: null };
  } catch (e) {
    console.error('autosave write failed', e);
    const full = e && (e.name === 'QuotaExceededError' || e.code === 22);
    return { ok: false, error: full ? 'This browser has no room left to autosave. Use "Save job file".' : NO_STORAGE_MESSAGE };
  }
}

export const safeFileName = (name, ext) => `${(String(name || '').trim().replace(/[^\w\- ]+/g, '').replace(/\s+/g, '-').slice(0, 60) || 'rebar-takeoff')}.${ext}`;

export function downloadText(filename, text, mime) {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

export function readJobFile(file) {
  return new Promise((resolve, reject) => {
    if (file.size > MAX_FILE_BYTES) { reject(new Error('That file is too big to be a job file.')); return; }
    const reader = new FileReader();
    reader.onerror = () => { console.error('file read failed', reader.error); reject(new Error('The file could not be read.')); };
    reader.onload = () => {
      try {
        resolve(sanitizeJob(JSON.parse(String(reader.result))));
      } catch (e) {
        console.error('job file rejected', e);
        reject(new Error(e instanceof SyntaxError ? 'That file is not a job file (it is not valid JSON).' : e.message));
      }
    };
    reader.readAsText(file);
  });
}
