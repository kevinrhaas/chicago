/**
 * Settings › About › Field log (T-2660): the counts js/field-log.js keeps on this device,
 * one row each, repainted whenever the log changes, and Clear, which empties it.
 *
 * The rows are built from the string table into #s-field-log-rows, so a visitor reads
 * plain words (no event names), and every count cell carries data-field-log="<count>" for
 * the smoke. Painting a closed section costs a dozen text nodes, so it simply always paints.
 */
import { t as str } from './strings/index.js';
import './strings/field-log.js';
import { fieldLog as pageLog, COUNTS } from './field-log.js';

/** "41 s", "2 min 5 s". */
export function duration(s) {
  const n = Math.max(0, Math.round(Number(s) || 0));
  return n < 60 ? str('fieldlog.time.sec', { s: n }) : str('fieldlog.time.min', { m: Math.floor(n / 60), s: n % 60 });
}

/** The rows About shows, in order: [{ key, label, value }]. */
export function fieldLogRows(log) {
  const rows = COUNTS.map((key) => ({ key, label: str(`fieldlog.row.${key}`), value: String(log.counts[key] ?? 0) }));
  const time = log.lastFirstInspectS == null ? str('fieldlog.time.none')
    : str('fieldlog.time.value', { time: duration(log.lastFirstInspectS), quick: log.quick, landed: log.counts.landed });
  rows.splice(2, 0, { key: 'time', label: str('fieldlog.row.time'), value: time });
  return rows;
}

/** Fill #s-field-log-rows. Returns the rows painted, or null without the section. */
export function paintFieldLog({ doc = globalThis.document, log = pageLog.read() } = {}) {
  const list = doc?.getElementById?.('s-field-log-rows');
  if (!list) return null;
  const rows = fieldLogRows(log);
  list.replaceChildren(...rows.flatMap(({ key, label, value }) => {
    const dt = doc.createElement('dt');
    dt.textContent = label;
    const dd = doc.createElement('dd');
    dd.dataset.fieldLog = key;
    dd.textContent = value;
    return [dt, dd];
  }));
  return rows;
}

/** Paint now and on every change; Clear empties the log and says so. */
export function wireFieldLogView({ doc = globalThis.document, log = pageLog } = {}) {
  const status = doc?.getElementById?.('s-field-log-status');
  const paint = () => paintFieldLog({ doc, log: log.read() });
  log.subscribe((now) => {
    paint();
    // "Cleared." stands until the next count.
    if (status && Object.values(now.counts).some(Boolean)) status.textContent = '';
  });
  doc?.getElementById?.('s-field-log-clear')?.addEventListener('click', () => {
    log.clear();
    if (status) status.textContent = str('fieldlog.cleared');
  });
  paint();
  return { paint };
}
