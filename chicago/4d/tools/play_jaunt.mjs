#!/usr/bin/env node
/** Walk jaunts through the renderer's own reducer.
 *    node tools/play_jaunt.mjs <id> --all-paths     every reachable path of one jaunt
 *    node tools/play_jaunt.mjs --all [--json] [--scene 1835]
 *                                                    the whole library, one row a jaunt (T-2039)
 *  The library row is what tools/audit_jaunts.py gates: stops, the primary path's words and
 *  declared reading seconds, shown and hidden resources, endings reached, the keepsake and
 *  whether any path awards it. The primary path moves on wherever a stop lets it and
 *  otherwise takes the first offered choice — the same ride the travel harness takes. */
import fs from 'node:fs';
import path from 'node:path';
import { emptyState, reduce, currentStop, choicesFor, canNext, shownResource } from '../renderers/web/js/jaunts.js';

const NOT_JAUNTS = new Set(['schema.json', 'daybook.json', 'catalog-55.json']);
const args = process.argv.slice(2);
const words = text => (text || '').split(/\s+/).filter(Boolean).length;
const arrive = state => state.phase === 'travelling'
  ? reduce(state, { type: 'ARRIVE', session: state.session, leg: state.leg }) : state;

function begin(jaunt) {
  const state = reduce(emptyState(), { type: 'START', jaunt, session: 'walker', mode: jaunt.default_mode });
  return reduce(state, { type: 'ARRIVE', session: state.session, leg: state.leg });
}

function walkJaunt(jaunt) {
  const endings = new Set(), keepsakes = new Set(), failures = [], paths = [];
  function walk(state, choices = []) {
    if (state.events.length > 500) { failures.push(`${choices.join(' > ')}: state limit`); return; }
    if (new Set(state.events.map(event => event.id)).size !== state.events.length) {
      failures.push(`${choices.join(' > ')}: duplicate event id`); return;
    }
    if (state.phase === 'outcome') {
      const awards = state.outcome.completion_eligible ? [`${jaunt.id}:${jaunt.keepsake.id}`] : [];
      if (awards.length !== new Set(awards).size) failures.push(`${choices.join(' > ')}: double keepsake`);
      awards.forEach(value => keepsakes.add(value)); endings.add(state.outcome.id);
      paths.push({ choices, ending: state.outcome.id, effects: state.events.filter(e => e.type === 'decision').length, awards: awards.length });
      return;
    }
    if (state.phase !== 'atStop') { failures.push(`${choices.join(' > ')}: stopped in ${state.phase}`); return; }
    const stop = currentStop(state), choicesHere = choicesFor(state), actions = choicesHere.map(choice => ({ choice }));
    if (stop.next) actions.push({ choice: null });
    if (!actions.length || !canNext(state) && !choicesHere.length) {
      failures.push(`${choices.join(' > ')}: ${stop.id} has no viable move`); return;
    }
    for (const action of actions) {
      let next = state;
      if (action.choice) next = reduce(next, { type: 'CHOOSE', id: action.choice.id });
      next = arrive(reduce(next, { type: 'NEXT' }));
      if (next === state) failures.push(`${choices.join(' > ')}: ${stop.id} did not advance`);
      else walk(next, [...choices, `${stop.id}:${action.choice?.id ?? 'move-on'}`]);
    }
  }
  walk(begin(jaunt));
  return { endings, keepsakes, failures, paths };
}

/** One ride: move on where the stop allows it, otherwise the first offered choice. */
function primaryPath(jaunt) {
  let state = begin(jaunt);
  const stops = [];
  for (let guard = 0; state.phase === 'atStop' && guard < 50; guard++) {
    const stop = currentStop(state), first = choicesFor(state)[0];
    stops.push(stop);
    let next = state;
    if (!stop.next && first) next = reduce(next, { type: 'CHOOSE', id: first.id });
    next = arrive(reduce(next, { type: 'NEXT' }));
    if (next === state) break;
    state = next;
  }
  const ending = state.phase === 'outcome' ? state.outcome : null;
  return {
    stops: stops.map(stop => stop.id), ending: ending?.id ?? null,
    words: words(jaunt.opening.text) + stops.reduce((n, s) => n + words(s.text) + words(s.narrative), 0) + words(ending?.text),
    // The estimate's own content term (travel-estimate.js): opening, then each stop's read and action.
    read_s: jaunt.opening.read_s + stops.reduce((n, s) => n + s.read_s + (s.action_s || 0), 0),
    ending_read_s: ending?.read_s ?? 0,
  };
}

function libraryRow(jaunt) {
  const { endings, keepsakes, failures, paths } = walkJaunt(jaunt);
  const variables = Object.entries(jaunt.variables || {});
  const shown = variables.filter(([, spec]) => shownResource(spec)).map(([name]) => name);
  if (jaunt.inventory) shown.push('basket');
  return {
    id: jaunt.id, title: jaunt.title, category: jaunt.category, featured: !!jaunt.featured,
    default_mode: jaunt.default_mode, allowed_modes: jaunt.allowed_modes, stops: jaunt.stops.length,
    primary: primaryPath(jaunt), resources: { shown, hidden: variables.filter(([, spec]) => !shownResource(spec)).map(([name]) => name) },
    quiet: !shown.length, paths: paths.length, endings_declared: jaunt.endings.map(e => e.id), endings_reached: [...endings],
    keepsake: { id: jaunt.keepsake.id, family: jaunt.keepsake.family, secondary_family: jaunt.secondary_family ?? null, awarded: keepsakes.size > 0 },
    failures,
  };
}

function readJaunt(file) { return JSON.parse(fs.readFileSync(file)); }

if (args[0] === '--all') {
  const at = args.indexOf('--scene'), scene = at >= 0 ? args[at + 1] : '1835';
  const rows = fs.readdirSync('data/jaunts').filter(name => name.endsWith('.json') && !NOT_JAUNTS.has(name)).sort()
    .map(name => readJaunt(path.join('data/jaunts', name))).filter(jaunt => jaunt.scene === scene).map(libraryRow);
  if (args.includes('--json')) { console.log(JSON.stringify({ scene, jaunts: rows }, null, 1)); process.exit(0); }
  const pad = (v, n) => String(v).padEnd(n);
  console.log(`${pad('jaunt', 24)} ${pad('stops', 5)} ${pad('words', 5)} ${pad('read', 5)} ${pad('mode', 6)} ${pad('paths', 5)} ${pad('ends', 5)} ${pad('family', 17)} resources`);
  for (const r of rows) {
    console.log(`${pad(r.id, 24)} ${pad(r.stops, 5)} ${pad(r.primary.words, 5)} ${pad(`${r.primary.read_s}s`, 5)} ${pad(r.default_mode, 6)} ${pad(r.paths, 5)} `
      + `${pad(`${r.endings_reached.length}/${r.endings_declared.length}`, 5)} ${pad(r.keepsake.family + (r.keepsake.awarded ? '' : ' (none)'), 17)} `
      + `${r.quiet ? 'quiet' : r.resources.shown.join(', ')}${r.resources.hidden.length ? ` · hidden: ${r.resources.hidden.join(', ')}` : ''}`);
  }
  const failed = rows.filter(r => r.failures.length);
  for (const r of failed) console.log(`JAUNT WALK FAIL ${r.id} — ${r.failures[0]}`);
  console.log(`JAUNT LIBRARY ${scene} — ${rows.length} jaunt(s); ${rows.filter(r => r.quiet).length} quiet; `
    + `${rows.reduce((n, r) => n + r.paths, 0)} path(s) walked; ${failed.length} with failures`);
  process.exit(failed.length ? 1 : 0);
}

const [id, flag] = args;
if (!id || flag !== '--all-paths') {
  console.error('usage: node tools/play_jaunt.mjs <id> --all-paths | --all [--json] [--scene 1835]');
  process.exit(2);
}
const candidates = [path.join('data/jaunts', `${id}.json`), path.join('data/jaunts/_fixtures', `${id}.json`),
  path.join('data/sidecars/1835/jaunts', `${id}.json`)];
const source = fs.existsSync(id) ? id : candidates.find(file => fs.existsSync(file));
if (!source) { console.error(`JAUNT WALK FAIL — no jaunt ${id}`); process.exit(1); }
const jaunt = readJaunt(source);
const { endings, keepsakes, failures, paths } = walkJaunt(jaunt);
console.log(`JAUNT WALK ${jaunt.id} — ${paths.length} path(s); endings: ${[...endings].join(', ') || 'none'}; effects committed: ${paths.reduce((n, p) => n + p.effects, 0)}; keepsakes awarded: ${keepsakes.size}`);
for (const row of paths) console.log(`  ${row.choices.join(' > ')} => ${row.ending}`);
for (const failure of failures) console.error(`  FAIL ${failure}`);
if (failures.length || !paths.length) process.exit(1);
