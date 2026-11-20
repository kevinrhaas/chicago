/**
 * block-grow.js — "Watch a block grow" (T-3676; docs/CLASSROOM-FEATURES.md item 20).
 *
 * The owner's list of 17 November asks for a single block's timeline, one state at a
 * time, inside the town already loaded. So this is the 1904 town and nothing else: no
 * other year is fetched or kept. A slider steps the years; each year shows only the
 * buildings this block's records say were standing by then, from each one's own `built`
 * attribute (compiled into the 1904 sidecars by tools/compile_scene.py, T-3037).
 *
 * The rules, and they are the whole of what this file decides:
 *
 *   - A building with a recorded year is HIDDEN before it and STANDING from it.
 *   - A recorded span ("between 1870 and 1876", "1864 or 1875") is GHOSTED from its
 *     first year and STANDING from its last: by then every reading has it built.
 *   - A building with NO recorded year is never given one. Every year before the scene's
 *     own date it is a GHOST, an outline saying "it stood by 1904; when it rose is not
 *     recorded", and it is listed as undated.
 *   - An outbuilding with no year of its own (a coach house, a conservatory, a shed of
 *     the same lot) is kept out of view while its lot's dated house is not yet built, and
 *     a ghost after. Where nothing on the lot is dated, it is a ghost like any undated one.
 *   - In the scene's own year (1904) every building is standing: that is the town itself.
 *
 * Every building is drawn as the 1904 scene draws it, in every year: a later front or
 * wing is not taken off for an earlier year, and the yards, walks, fences and trees stay
 * as 1904 lays them. The panel says so. Only Prairie Avenue addresses are read.
 *
 * Pure: a test reads it with the sidecars and no page (tools/check_block_grow.mjs).
 */
import { displayName } from './display-name.js';

/** The scene this works in, and the year its town already stands at. */
export const SCENE_YEAR = 1904;

/** The suffixes a lot's outbuildings carry after their house's id. */
const PART_SUFFIX = /_(?:coach_house|conservatory|ranges|frame_house|rear_building|alley_building|shed|front|rear_dwelling|stable|dwelling)$/;

/** An address on Prairie Avenue as the records write it: "1812 S. Prairie Avenue". */
const PRAIRIE_ADDRESS = /^(\d{4})(?:\s*-\s*\d{3,4})?\s+(?:S\.?\s+)?Prairie\s+Av/i;
const PRAIRIE_ID = /_(\d{4})_prairie(?:_|$)/;

/**
 * A recorded `built` value as the first and last year it names, or null when it names
 * none. 1887 → 1887..1887; "between 1870 and 1876" → 1870..1876; "1864 or 1875" →
 * 1864..1875; "about 1832" → 1832..1832. Anything else is no year at all.
 */
export function parseBuilt(value) {
  if (Number.isInteger(value)) return { from: value, by: value };
  if (typeof value !== 'string') return null;
  const years = [...value.matchAll(/\b(1[6-9]\d\d)\b/g)].map((m) => Number(m[1]));
  if (!years.length) return null;
  return { from: Math.min(...years), by: Math.max(...years) };
}

/** A record's Prairie Avenue street number, or null. */
export function prairieNumber(sidecar, id = sidecar?.id ?? '') {
  for (const a of sidecar?.aka ?? []) {
    const m = PRAIRIE_ADDRESS.exec(String(a));
    if (m) return Number(m[1]);
  }
  const m = PRAIRIE_ID.exec(id);
  return m ? Number(m[1]) : null;
}

/** The lot a record belongs to: its id without an outbuilding's suffix. */
export const stemOf = (id) => String(id).replace(PART_SUFFIX, '');

/** Which side of Prairie Avenue a number is on: the even numbers are the west side. */
export const sideOf = (number) => (number % 2 === 0 ? 'west' : 'east');

/** The block's key and its name, as a visitor reads it. */
export const blockId = (hundred, side) => `prairie-${hundred}-${side}`;
export const blockTitle = (hundred, side) => `${hundred} block of Prairie Avenue, ${side} side`;

/** One building's row: its name, its recorded year and the sources that record it. */
function memberOf(id, sidecar) {
  const rec = sidecar?.attributes?.built ?? null;
  const span = parseBuilt(rec?.value);
  const citations = new Map((sidecar?.citations ?? []).map((c) => [c.source_id, c]));
  return {
    id,
    stem: stemOf(id),
    number: prairieNumber(sidecar, id),
    name: displayName(sidecar ?? {}, id).title || id,
    built: span ? {
      value: rec.value, from: span.from, by: span.by,
      confidence: rec.confidence ?? null,
      note: typeof rec.note === 'string' ? rec.note : '',
      sources: (rec.sources ?? []).map((s) => ({
        id: s,
        citation: citations.get(s)?.citation ?? '',
        url: citations.get(s)?.url ?? '',
      })),
    } : null,
  };
}

/**
 * Every Prairie Avenue block side in the registry, each with its buildings, grouped by
 * lot. `records` is the scene's registry (id → { sidecar }) or any iterable of
 * [id, { sidecar }].
 */
export function blocksOf(records) {
  const blocks = new Map();
  for (const [id, row] of records) {
    const sidecar = row?.sidecar;
    if (!sidecar?.asset) continue;            // a record no layer draws as a building
    const number = prairieNumber(sidecar, id);
    if (number === null) continue;
    const hundred = Math.floor(number / 100) * 100, side = sideOf(number);
    const key = blockId(hundred, side);
    if (!blocks.has(key)) blocks.set(key, { id: key, title: blockTitle(hundred, side), hundred, side, members: [] });
    blocks.get(key).members.push(memberOf(id, sidecar));
  }
  for (const block of blocks.values()) {
    block.members.sort((a, b) => (a.number - b.number) || a.id.localeCompare(b.id));
    const lots = new Map();
    for (const m of block.members) {
      if (!lots.has(m.stem)) lots.set(m.stem, []);
      lots.get(m.stem).push(m);
    }
    block.lots = [...lots.entries()].map(([stem, members]) => ({ stem, members }));
    block.datedLots = block.lots.filter((l) => l.members.some((m) => m.built)).length;
    block.dated = block.members.filter((m) => m.built);
    block.undated = block.members.filter((m) => !m.built);
    block.first = block.dated.length ? Math.min(...block.dated.map((m) => m.built.from)) : null;
  }
  return [...blocks.values()];
}

/**
 * The blocks offered: those where at least two lots, and at least half of them, have a
 * building with a recorded year. The Glessner side of the 1800 block comes first.
 */
export function offeredBlocks(records) {
  const all = blocksOf(records).filter((b) => b.datedLots >= 2 && b.datedLots * 2 >= b.lots.length);
  const glessner = (b) => (b.members.some((m) => m.id === 'glessner_house') ? 0 : 1);
  return all.sort((a, b) => glessner(a) - glessner(b) || a.hundred - b.hundred || a.side.localeCompare(b.side));
}

/** The years the slider steps through: the block's first recorded year to the scene's. */
export function yearsOf(block) {
  if (!block?.first) return [];
  const out = [];
  for (let y = block.first; y <= SCENE_YEAR; y++) out.push(y);
  return out;
}

/**
 * The block in `year`: each building STANDING, a GHOST (with why) or HIDDEN, and the
 * buildings whose recorded year arrives this year (`appearing`, the card's rows).
 *
 * ghost reasons: 'undated' (no recorded year), 'span' (inside a recorded span),
 * 'outbuilding' (no year of its own; its lot's house stands).
 */
export function stateAt(block, year) {
  const standing = [], ghost = [], hidden = [], appearing = [], why = {};
  const final = year >= SCENE_YEAR;
  for (const lot of block.lots) {
    const dated = lot.members.filter((m) => m.built);
    // the lot's house is up once any of its dated buildings is (a ghost or standing)
    const lotUp = dated.some((m) => year >= m.built.from);
    for (const m of lot.members) {
      let state, reason = null;
      if (final) state = 'standing';
      else if (m.built) {
        if (year >= m.built.by) state = 'standing';
        else if (year >= m.built.from) { state = 'ghost'; reason = 'span'; }
        else state = 'hidden';
      } else if (dated.length) {
        if (lotUp) { state = 'ghost'; reason = 'outbuilding'; } else state = 'hidden';
      } else { state = 'ghost'; reason = 'undated'; }
      ({ standing, ghost, hidden })[state].push(m.id);
      if (reason) why[m.id] = reason;
      if (m.built && !final && (m.built.by === year || (m.built.from === year && m.built.by > year))) {
        appearing.push({ id: m.id, name: m.name, built: m.built, state });
      }
    }
  }
  return { year, final, standing, ghost, hidden, appearing, why };
}

/** The ids a year keeps out of the drawn town: the hidden and the ghosted. */
export const heldAt = (state) => [...state.hidden, ...state.ghost];
