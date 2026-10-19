/**
 * confidence-store.js — the Confidence view's choices, kept for the next page (T-2649,
 * NAV-604; DESIGN §09: "Choices persist in localStorage['chicago4d.confidence'] and carry
 * between destinations").
 *
 * One record at `chicago4d.confidence`:
 *
 *   { on: true,                                   the colouring (the HUD's switch)
 *     hidden: ['reconstructed'],                  the grades taken out of the view
 *     looks: { attested: { mode, opacity, color }, … } }   each grade's look (T-2647/8)
 *
 * Every page of every year boots from the same record (a Jump is a page load on the same
 * origin), so a choice made in 1835 is the view a visitor lands in at 1904: the looks go on
 * the renderer before the first frame (confidence-presets.js restoreLooks), the hidden set
 * with the HUD's other stored settings (hud.js applyHidden), and the colouring as the
 * visitor walks in (hud.js restore).
 *
 * Before T-2649 the HUD wrote '1' or '0' to this same key and T-2647's looks wrote their
 * JSON over it, so whichever was written last won and the colouring did not survive a
 * reload. A write here MERGES into what is kept, so no writer drops another's part — and
 * a later part (T-2650's overlays) is a new field that the others carry untouched.
 *
 * The hidden set is still written to its own key too, `chicago4d.confidence.hidden`, as
 * it always was: a build without this module on the same origin reads it there. It is
 * read back only when the record has no hidden set of its own (a visitor from before).
 *
 * Storage refused, unreadable or full, nothing is kept and nothing breaks: the view
 * opens at NORMAL, the same as a first visit.
 */

export const STORE_KEY = 'chicago4d.confidence';
export const HIDDEN_KEY = 'chicago4d.confidence.hidden';
const LEVELS = ['attested', 'inferred', 'reconstructed'];

const local = () => { try { return globalThis.localStorage ?? null; } catch { return null; } };
const get = (storage, key) => { try { return storage?.getItem(key) ?? null; } catch { return null; } };
const levelsOf = (list) => [...new Set(list.filter((l) => LEVELS.includes(l)))];

/** The record as stored, its parts unchecked: {} when there is none or it cannot be read. */
function readRecord(storage) {
  const raw = get(storage, STORE_KEY);
  if (raw === '1' || raw === '0') return { on: raw === '1' }; // the HUD's switch, before T-2649
  if (!raw) return {};
  try {
    const v = JSON.parse(raw);
    return v && typeof v === 'object' && !Array.isArray(v) ? v : {};
  } catch { return {}; }
}

/**
 * What the visitor chose, each part present only when it was kept and reads as one:
 * `on` (boolean), `hidden` (grade names), `looks` ({ grade: { mode, opacity, color } }).
 * Any other field (a later part of the view) comes back as it was kept.
 */
export function readChoices(storage = local()) {
  const rec = readRecord(storage);
  const out = { ...rec };
  delete out.on; delete out.hidden; delete out.looks;
  if (typeof rec.on === 'boolean') out.on = rec.on;
  if (Array.isArray(rec.hidden)) out.hidden = levelsOf(rec.hidden);
  else {
    try {
      const old = JSON.parse(get(storage, HIDDEN_KEY) ?? 'null');
      if (Array.isArray(old)) out.hidden = levelsOf(old);
    } catch { /* an unreadable old key is no choice */ }
  }
  if (rec.looks && typeof rec.looks === 'object' && !Array.isArray(rec.looks)) out.looks = rec.looks;
  return out;
}

/**
 * Keep part of the choice — `{ on }`, `{ hidden }`, `{ looks }` or several — merged into
 * what is kept, so the other parts are left as they were. Returns whether it was written.
 */
export function keepChoices(part, storage = local()) {
  if (!part || typeof part !== 'object') return false;
  try {
    const next = { ...readRecord(storage), ...part };
    if ('hidden' in part) {
      next.hidden = levelsOf(Array.isArray(part.hidden) ? part.hidden : []);
      storage?.setItem(HIDDEN_KEY, JSON.stringify(next.hidden));
    }
    if (!storage) return false;
    storage.setItem(STORE_KEY, JSON.stringify(next));
    return true;
  } catch { return false; /* private mode, or full: a convenience */ }
}

/** The view is anything but NORMAL: the colouring on, or a grade hidden (the legend shows). */
export const viewIsOn = ({ on, hidden } = {}) => !!on || (Array.isArray(hidden) && hidden.length > 0);
