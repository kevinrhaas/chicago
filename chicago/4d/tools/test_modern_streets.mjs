#!/usr/bin/env node
// T-2741 — today's street and house number, read off the City's centrelines
// (renderers/web/js/modern-streets.js over data/modern/streets.json), and the 1904
// context city's names in where.js. Pure: no browser.
import fs from 'node:fs';
import path from 'node:path';
import { createModernStreets, houseNumber, todayText } from '../renderers/web/js/modern-streets.js';
import { createWhere } from '../renderers/web/js/where.js';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const doc = JSON.parse(fs.readFileSync(path.join(HERE, '..', 'data', 'modern', 'streets.json'), 'utf8'));
const m = createModernStreets(doc);
const fails = [];
const expect = (name, ok, got) => { if (!ok) fails.push(`${name}: ${JSON.stringify(got)}`); };

// The corner this project holds OSM control for (data/traces/prairie_1904_control.json).
const corner = m.at(1401.86, -3206.93);
expect('Prairie & 18th is a corner', corner?.mode === 'corner'
  && [corner.street, corner.cross].sort().join('|') === 'E 18th St|S Prairie Ave', corner);
// Glessner's side of Prairie (west) is even, Kimball's (east) odd — 1800 and 1801.
const west = m.at(1390, -3150);
const east = m.at(1415, -3150);
expect('west side of Prairie between 16th and 18th is an even 17xx', /^17\d[02468] S Prairie Ave$/.test(west?.address ?? ''), west);
expect('east side is an odd 17xx', /^17\d[13579] S Prairie Ave$/.test(east?.address ?? ''), east);
// Not 800 to the mile: a formula off State and Madison would say about 1733 at 18th.
expect('south of 18th on Prairie reads 18xx', /^18\d\d S Prairie Ave$/.test(m.at(1415, -3300)?.address ?? ''), m.at(1415, -3300));
expect('the Loop: Dearborn north of Madison', /^\d{1,2} N Dearborn St$/.test(m.at(700, -440)?.address ?? ''), m.at(700, -440));
expect('LaSalle is spelt as the signs spell it', /N LaSalle St/.test(todayText(m.at(452.5, -110.4))), todayText(m.at(452.5, -110.4)));
expect('out in the 1812 lake there is no street today', m.at(1600, 0) === null && todayText(null) === 'no street here today', m.at(1600, 0));
expect('a parity is honoured', houseNumber(1800, 1898, 0.5, 'E') % 2 === 0 && houseNumber(1801, 1899, 0.5, 'O') % 2 === 1, null);
expect('a side with no numbers says none', houseNumber(0, 0, 0.5, 'E') === null, null);

// where.js: the 1904 context city's named centrelines answer past the traced grid.
const w = createWhere({ lines: [{ name: 'Michigan Avenue', e0: 1130, n0: -2900, e1: 1135, n1: -3800 }] });
expect('a context line is the street you are on', w.at(1135, -3200)?.place === 'Michigan Avenue', w.at(1135, -3200));
expect('and nothing far from it', w.at(1400, -3200) === null, w.at(1400, -3200));

if (fails.length) {
  for (const f of fails) console.log(`FAIL ${f}`);
  process.exit(1);
}
console.log(`MODERN STREETS PASS — ${doc.counts.segments} City segments; Prairie & 18th is a corner, 17xx/18xx S Prairie read off the block ranges with each side's parity, LaSalle spelt as signed, no street in the lake; 1904 context lines name a street past the grid`);
