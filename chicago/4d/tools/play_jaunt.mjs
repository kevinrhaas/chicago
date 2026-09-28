#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { emptyState, reduce, currentStop, choicesFor, canNext } from '../renderers/web/js/jaunts.js';

const [id, flag] = process.argv.slice(2);
if (!id || flag !== '--all-paths') {
  console.error('usage: node tools/play_jaunt.mjs <id> --all-paths');
  process.exit(2);
}
const candidates = [path.join('data/jaunts', `${id}.json`), path.join('data/jaunts/_fixtures', `${id}.json`),
  path.join('data/sidecars/1835/jaunts', `${id}.json`)];
const source = fs.existsSync(id) ? id : candidates.find(file => fs.existsSync(file));
if (!source) { console.error(`JAUNT WALK FAIL — no jaunt ${id}`); process.exit(1); }
const jaunt = JSON.parse(fs.readFileSync(source));
const arrive = state => state.phase === 'travelling'
  ? reduce(state, { type: 'ARRIVE', session: state.session, leg: state.leg }) : state;
let initial = reduce(emptyState(), { type: 'START', jaunt, session: 'walker', mode: jaunt.default_mode });
initial = reduce(initial, { type: 'ARRIVE', session: initial.session, leg: initial.leg });
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

walk(initial);
console.log(`JAUNT WALK ${jaunt.id} — ${paths.length} path(s); endings: ${[...endings].join(', ') || 'none'}; effects committed: ${paths.reduce((n, p) => n + p.effects, 0)}; keepsakes awarded: ${keepsakes.size}`);
for (const row of paths) console.log(`  ${row.choices.join(' > ')} => ${row.ending}`);
for (const failure of failures) console.error(`  FAIL ${failure}`);
if (failures.length || !paths.length) process.exit(1);
