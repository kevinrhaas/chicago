/**
 * T-2612 — the arrival's telemetry (design doc "Field Navigator Mk II", section 05,
 * "Telemetry: semi-real, on purpose").
 *
 * Payload, Link and ETA stay where arrival.js paints them (real bytes, the measured
 * link, the forecast ETA). This module adds the rest of the strip and the deck:
 *
 *   - YEARS TO GO: how far the ticker year still is from the destination, counted
 *     down as the ticker rolls (main.js forwards arrival.js's `onYear`), 0 on landing.
 *   - FOUR LAMPS in place of six. STRUCT and SYNC said nothing a visitor understands,
 *     so the lamps are named for what a visitor will see, each on the real boot phases
 *     of js/boot-phases.js: STREETS (scene + terrain + ground), BUILDINGS, TREES (flora)
 *     and PEOPLE (people + interaction). A lamp blinks while any of its phases runs and
 *     lights when all of them have finished. An optional phase that fails (people) still
 *     counts as finished, because it never holds the arrival; an essential one faults it.
 *   - THE LOG: one line per boot phase, "PLANTING 1904 ELMS…" while it runs and OK when
 *     it ends. The lines are machine lore in mono caps and say so by their voice; the
 *     destination's own lines come from its deck, data/timestream/<year>.json `log`
 *     (tools/check_timestream.py lints them), over a machine default for each phase, so
 *     a line shows from the first phase even before the deck has arrived.
 *
 * Presentation only: every element is aria-hidden on the page, nothing here can stop
 * the boot, and a missing element simply paints nothing.
 */

export const LAMP_GROUPS = [
  ['streets', 'Streets', ['scene', 'terrain', 'ground']],
  ['buildings', 'Buildings', ['buildings']],
  ['trees', 'Trees', ['flora']],
  ['people', 'People', ['people', 'interaction']],
];

/** Each phase's machine line, used until (or unless) the deck names its own. */
export const MACHINE_LINES = {
  scene: 'Syncing time mesh',
  terrain: 'Rolling back the skyline',
  buildings: 'Raising the buildings',
  ground: 'Laying the streets',
  flora: 'Planting the trees',
  people: 'Reading the directory',
  interaction: 'Arming the Navigator',
};

export function yearsToGo(year, targetYear) {
  const y = Math.round(Number(year)), t = Math.round(Number(targetYear));
  return Number.isFinite(y) && Number.isFinite(t) ? Math.max(0, y - t) : null;
}

/** A lamp's state from the phases it stands for: 'fault' when an essential one failed,
 * 'done' when every one has finished (an optional failure counts as finished), 'active'
 * while one of them is running, 'partial' between them (some finished, none running:
 * STREETS after the terrain and before the ground), and null before any has started. */
export function groupState(phases, ids) {
  const members = (phases || []).filter(p => ids.includes(p.id));
  if (!members.length) return null;
  if (members.some(p => p.error && p.essential !== false)) return 'fault';
  const finished = p => p.endedAt != null || (p.error && p.essential === false);
  if (members.every(finished)) return 'done';
  if (members.some(p => p.startedAt != null && !finished(p))) return 'active';
  if (members.some(finished)) return 'partial';
  return null;
}

export function createTelemetry({
  boot,
  lampsEl = null,
  logEl = null,
  yearsEl = null,
  targetYear,
  currentYear = new Date().getFullYear(),
} = {}) {
  if (!boot) throw new Error('createTelemetry requires the boot controller');
  let lines = { ...MACHINE_LINES };
  const rows = logEl ? [...logEl.children] : [];
  const lamps = new Map();
  for (const [group, , ids] of LAMP_GROUPS) {
    const el = lampsEl?.querySelector?.(`[data-group="${group}"]`);
    if (el) lamps.set(group, { el, ids });
  }

  function paintLamps() {
    for (const { el, ids } of lamps.values()) {
      const state = groupState(boot.phases, ids);
      if (state) { if (el.dataset.state !== state) el.dataset.state = state; } else delete el.dataset.state;
    }
  }

  const lineFor = id => lines[id] || MACHINE_LINES[id] || null;
  function shiftIn(id) {
    const text = lineFor(id);
    if (!rows.length || !text) return;
    for (let i = 0; i < rows.length - 1; i++) {
      rows[i].textContent = rows[i + 1].textContent;
      rows[i].className = rows[i + 1].className.replace(/\bfresh\b/, '').trim();
      if (rows[i + 1].dataset.phase) rows[i].dataset.phase = rows[i + 1].dataset.phase; else delete rows[i].dataset.phase;
    }
    const last = rows.at(-1);
    last.textContent = text;
    last.dataset.phase = id;
    last.className = 'run fresh';
  }
  // OK when the phase finished; FAULT when an essential one failed; SKIP when an optional
  // one did (the people directory never holds the arrival, and is not claimed as loaded).
  function settleRow(phase) {
    const row = rows.find(r => r.dataset.phase === phase.id);
    if (row) row.className = !phase.error ? 'ok' : phase.essential === false ? 'skip' : 'fault';
  }

  let year = Number(currentYear);
  function paintYears() {
    const n = yearsToGo(year, targetYear);
    if (yearsEl && n != null && yearsEl.textContent !== String(n)) yearsEl.textContent = String(n);
  }

  boot.on('phasestart', ({ phase } = {}) => { if (phase?.id) shiftIn(phase.id); paintLamps(); });
  boot.on('phaseend', ({ phase } = {}) => { if (phase?.id) settleRow(phase); paintLamps(); });
  boot.on('error', ({ phase } = {}) => { if (phase?.id) settleRow(phase); paintLamps(); });
  paintLamps();
  paintYears();

  return {
    /** The ticker's year, from arrival.js's onYear. */
    year(y) { if (Number(y) <= year || !Number.isFinite(year)) { year = Number(y); paintYears(); } },
    /** The destination's own log lines, from its deck. Rows already showing a phase take
     * the deck's wording for it, so a deck that lands mid-trip reads as one log. */
    setDeck(deck) {
      const log = deck?.log;
      if (!log || typeof log !== 'object') return;
      lines = { ...MACHINE_LINES };
      for (const [id, text] of Object.entries(log)) if (typeof text === 'string' && text.trim()) lines[id] = text.trim();
      for (const row of rows) if (row.dataset.phase && lineFor(row.dataset.phase)) row.textContent = lineFor(row.dataset.phase);
    },
    get state() {
      return {
        years: yearsEl?.textContent ?? null,
        lamps: Object.fromEntries([...lamps].map(([g, { el }]) => [g, el.dataset.state ?? null])),
        log: rows.map(r => ({ text: r.textContent, state: r.className })),
      };
    },
  };
}
