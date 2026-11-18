/** A shareable view contains only bounded scene state, never account or notebook data. */
import { FLY } from './travel-settings.js';
export const MOMENT_YEARS = Object.freeze(['1812', '1835', '1904']);
export const PHOTO_EDGE = 1280;
const ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$/;
const SEASONS = ['spring', 'summer', 'fall', 'winter'];
const number = (v, min, max) => v !== null && v !== '' && Number.isFinite(Number(v))
  && Number(v) >= min && Number(v) <= max ? Number(v) : null;
const validDate = value => /^1[789]\d{2}-\d{2}-\d{2}$/.test(value ?? '')
  && Number.isFinite(Date.parse(`${value}T12:00:00Z`))
  && new Date(`${value}T12:00:00Z`).toISOString().slice(0, 10) === value;
const round = n => Math.round(n * 100) / 100;

/** Malformed coordinates reject the whole view; optional bad values are omitted. */
export function normalMoment(raw) {
  if (!raw || !MOMENT_YEARS.includes(String(raw.year))) return null;
  const e = number(raw.e, -100000, 100000), n = number(raw.n, -100000, 100000);
  if (e === null || n === null) return null;
  const bearing = number(raw.bearing, 0, 360), pitch = number(raw.pitch, -89, 89);
  const altitude = number(raw.altitude, 0, FLY.maxAltitude);
  return { date: validDate(raw.date) ? raw.date : null, year: String(raw.year), e: round(e), n: round(n), bearing: round(bearing ?? 0),
    pitch: round(pitch ?? 0), altitude: altitude === null ? null : round(altitude),
    season: SEASONS.includes(raw.season) ? raw.season : null,
    person: ID.test(raw.person ?? '') ? raw.person : null,
    structure: ID.test(raw.structure ?? '') ? raw.structure : null,
    hour: /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(raw.hour ?? '') ? raw.hour : null };
}
export function parseMoment(search) {
  try {
    const p = new URLSearchParams(search);
    if (p.get('moment') !== '1') return null;
    return normalMoment(Object.fromEntries(['date', 'year', 'e', 'n', 'bearing', 'pitch', 'altitude', 'season', 'person', 'structure', 'hour']
      .map(key => [key, p.get(key)])));
  } catch { return null; }
}
/** Keep the current source/preview/production path; discard unrelated query and fragment. */
export function momentLink(raw, href = globalThis.location?.href) {
  const m = normalMoment(raw);
  if (!m) return null;
  const url = new URL(href);
  if (!['http:', 'https:'].includes(url.protocol)) return null;
  url.search = ''; url.hash = '';
  url.searchParams.set('moment', '1');
  for (const [key, value] of Object.entries(m)) if (value !== null) url.searchParams.set(key, String(value));
  return url.href;
}
/** Scene coverage and the normal navigation obstruction map must both allow the view. */
export function momentFits(m, { year, inBounds, blockedAt } = {}) {
  return !!m && m.year === String(year) && inBounds?.(m.e, m.n) === true
    && (m.altitude !== null || !blockedAt?.(m.e, m.n));
}
export function photoSize(width, height, edge = PHOTO_EDGE) {
  if (!(width > 0 && height > 0)) throw new Error('The view is not ready.');
  const scale = Math.min(1, edge / Math.max(width, height));
  return { width: Math.max(1, Math.round(width * scale)), height: Math.max(1, Math.round(height * scale)) };
}
/** Copy during the rendered frame, before WebGL clears it. No extra GPU target is kept. */
export function stampMoment(canvas, metadata, { doc = globalThis.document } = {}) {
  const footer = 106;
  const size = photoSize(canvas.width, canvas.height, PHOTO_EDGE - footer);
  const out = doc.createElement('canvas');
  out.width = size.width; out.height = size.height + footer;
  const ctx = out.getContext('2d');
  if (!ctx) throw new Error('Your browser could not save this view.');
  ctx.drawImage(canvas, 0, 0, size.width, size.height);
  ctx.fillStyle = '#17232a'; ctx.fillRect(0, size.height, out.width, footer);
  ctx.fillStyle = '#ffffff';
  const font = Math.max(11, Math.min(18, size.width / 35));
  const line = (text, row, bold = false) => {
    ctx.font = `${bold ? '600 ' : ''}${font}px sans-serif`;
    let value = String(text ?? '').replace(/[\r\n]+/g, ' ');
    while (value.length > 1 && ctx.measureText(value).width > out.width - 24) value = `${value.slice(0, -2)}…`;
    ctx.fillText(value, 12, size.height + 24 + row * 24);
  };
  line(`4D Chicago · ${metadata.year} · ${metadata.place}`, 0, true);
  line([metadata.date, metadata.season, metadata.hour, metadata.personName].filter(Boolean).join(' · '), 1);
  const sources = metadata.sources ?? [];
  line(sources.length ? `Sources for ${metadata.sourceSubject || 'selected place'}: ${sources.map(s => s.title).join('; ')}`
    : 'Reconstructed view · Open cards in the town to read their sources.', 2);
  line('A reconstruction, not a historical photograph.', 3);
  return new Promise((resolve, reject) => {
    try { out.toBlob(blob => {
      // Release the temporary full-size raster after the encoder has finished.
      out.width = 1; out.height = 1;
      if (blob) resolve({ ...metadata, blob }); else reject(new Error('Your browser could not save this view.'));
    }, 'image/png'); } catch (error) { out.width = 1; out.height = 1; reject(error); }
  });
}
