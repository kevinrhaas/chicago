#!/usr/bin/env node
// The Navigator's People screen as a directory (T-3430), read off the real 1904 and 1812
// directories without a browser.
//
// The owner, 2026-11-06: People "should have some search to it to be able to find a person or
// household and then click and get details on that person and household". So, per scene:
//   1. every person is in exactly one household, and there are as many households as the
//      directory's own count says;
//   2. a household's family, staff and children of other years are its members, each once;
//   3. every household names the house it lives at, and in 1904 an address with a number;
//   4. households list in street order, then house number;
//   5. the search finds a household by its name, its address and its people's names, and a
//      person by name, work and household, every query word required, diacritics folded;
//   6. an empty query lists everyone;
//   7. a person leads back to their own household, and a house to the household living in it.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  directoryModel, search, householdOf, householdAt, splitHouseholdName, fold, surnameOf, householdCount,
} from '../renderers/web/js/people-directory.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const json = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const failures = [];
const fail = (m) => { if (failures.length < 25) failures.push(m); else if (failures.length === 25) failures.push('…'); };
const ok = (cond, m) => { if (!cond) fail(m); };

// The pure helpers.
ok(JSON.stringify(splitHouseholdName('The Roloson household at 2109 Prairie Avenue'))
  === JSON.stringify({ short: 'The Roloson household', address: '2109 Prairie Avenue', number: 2109, street: 'Prairie Avenue' }),
'splitHouseholdName reads the short name, the address, its number and street');
ok(splitHouseholdName('A household').short === 'A household' && splitHouseholdName('A household').address === '',
  'a household name with no "at" keeps its whole name and no address');
ok(fold('  Béaubien,  JR. ') === 'beaubien jr', 'fold drops accents, case and punctuation');
ok(surnameOf('Edson Keith jr.') === 'keith' && surnameOf('Mrs. Edson Keith jr.') === 'keith', 'surname sets "jr." aside');

const summary = [];
for (const scene of ['1904', '1812']) {
  const dir = json(`data/sidecars/${scene}/people.json`);
  const m = directoryModel(dir);
  const tag = `${scene}:`;
  // 1.
  ok(m.people.length === dir.people.length, `${tag} ${m.people.length} people read of ${dir.people.length}`);
  const want = dir.counts?.households ?? new Set(dir.people.map((p) => p.household)).size;
  ok(m.households.length === want, `${tag} ${m.households.length} households, the directory counts ${want}`);
  const seen = new Map();
  for (const h of m.households) for (const p of h.members) seen.set(p.id, (seen.get(p.id) ?? 0) + 1);
  for (const p of m.people) if (seen.get(p.id) !== 1) fail(`${tag} ${p.id} is in ${seen.get(p.id) ?? 0} households`);
  for (const h of m.households) {
    // 2.
    const parts = [...h.family, ...h.staff, ...h.away].map((p) => p.id).sort();
    if (JSON.stringify(parts) !== JSON.stringify(h.members.map((p) => p.id).sort())) fail(`${tag} ${h.id}: family + staff + away is not its members`);
    if (h.staff.some((p) => p.relationship !== 'servant')) fail(`${tag} ${h.id}: staff holds someone who is not staff`);
    if (h.members[0]?.relationship !== 'head' && h.members.some((p) => p.relationship === 'head')) fail(`${tag} ${h.id}: the head is not listed first`);
    // 3.
    if (!h.lives_at) fail(`${tag} ${h.id}: no house`);
    if (scene === '1904' && !(h.number > 0 && h.street)) fail(`${tag} ${h.id}: no numbered address in "${h.name}"`);
    if (!/\d+ (person|people)/.test(householdCount(h))) fail(`${tag} ${h.id}: count line "${householdCount(h)}"`);
    // 7.
    for (const p of h.members) if (householdOf(m, p.id) !== h) fail(`${tag} ${p.id} does not lead back to ${h.id}`);
    if (householdAt(m, h.lives_at)?.lives_at !== h.lives_at) fail(`${tag} ${h.lives_at} does not lead to a household living there`);
  }
  // 4.
  for (let i = 1; i < m.households.length; i++) {
    const a = m.households[i - 1], b = m.households[i];
    const c = fold(a.street).localeCompare(fold(b.street)) || (a.number ?? Infinity) - (b.number ?? Infinity);
    if (c > 0) { fail(`${tag} ${a.address} listed before ${b.address}`); break; }
  }
  // 6.
  const all = search(m, '   ');
  ok(all.query === '' && all.people.length === m.people.length && all.households.length === m.households.length,
    `${tag} an empty query does not list everyone`);
  // 5. Every household found by its own address and by its head's name; every person by name.
  for (const h of m.households) {
    if (h.address && !search(m, h.address).households.includes(h)) fail(`${tag} "${h.address}" does not find ${h.id}`);
    const head = h.members[0];
    if (!search(m, head.name).households.includes(h)) fail(`${tag} "${head.name}" does not find their household ${h.id}`);
  }
  for (const p of m.people) {
    if (!search(m, p.name).people.some((x) => x.id === p.id)) fail(`${tag} "${p.name}" does not find ${p.id}`);
  }
  summary.push(`${scene} ${m.households.length} households, ${m.people.length} people`);
}

// 5, by example, in 1904.
{
  const m = directoryModel(json('data/sidecars/1904/people.json'));
  const roloson = search(m, 'roloson');
  ok(roloson.households.some((h) => h.address === '2109 Prairie Avenue'), '1904: "roloson" does not find 2109 Prairie');
  ok(roloson.people.some((p) => p.name === 'Frank Allen'), '1904: "roloson" does not find the Rolosons\' coachman');
  ok(search(m, '2109').households.length === 1, '1904: "2109" finds more or less than its one house');
  const coach = search(m, 'coachman').people;
  ok(coach.length > 5 && coach.every((p) => /coachman/i.test(p.occupation ?? '')), `1904: "coachman" finds ${coach.length}, not all coachmen`);
  const both = search(m, 'allen roloson').people;
  ok(both.length === 1 && both[0].name === 'Frank Allen', '1904: every word of a query is required');
  ok(search(m, 'GLÉSSNER').households.some((h) => /1800 Prairie/.test(h.address)), '1904: "GLÉSSNER" does not find 1800 Prairie');
  ok(!search(m, 'zzqx').households.length && !search(m, 'zzqx').people.length, '1904: nonsense finds something');
  const ordered = m.people.map((p) => p.surname);
  ok(ordered.every((s, i) => !i || ordered[i - 1].localeCompare(s) <= 0), '1904: people are not in surname order');
}

// The screen itself: no main.js, and the card it draws is person-card.js's own.
{
  const src = fs.readFileSync(path.join(ROOT, 'renderers/web/js/apps/people-view.js'), 'utf8');
  ok(!/from ['"][^'"]*main\.js['"]/.test(src), 'people-view.js imports main.js');
  ok(/renderPersonCard/.test(src) && /formerResidentsBlock/.test(src), 'people-view.js does not draw the shared person card and former residents');
  ok(/data-ppl-go|pplGo/.test(src) && /goTo/.test(src), 'people-view.js has no Go to house');
}

if (failures.length) {
  console.error(`People directory: ${failures.length} failure(s)`);
  for (const f of failures) console.error(`  FAIL ${f}`);
  process.exit(1);
}
console.log(`People directory (T-3430): ok — ${summary.join('; ')}`);
