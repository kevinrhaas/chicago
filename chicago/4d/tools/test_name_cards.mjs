#!/usr/bin/env node
// T-3614 — the name cards over people (renderers/web/js/name-cards.js): the pure halves.
//
// The owner, 2026-11-16: "make sure the names fit". So every person of every year's directory
// (data/sidecars/<year>/people.json: 1812's long "A man of the Chicago militia, name not
// recorded (1 of 6)" among them) fits its card, on one line or two, at a measure wider than any
// appearance's type (MEASURE_EM per character), with nothing cut. And who is carded, how big on
// the screen, the fade at reach, each appearance's colours, the pick under a point, the Settings
// default (on) and its switch, and the atlas's memory on a phone.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const m = await import(pathToFileURL(path.join(root, 'renderers/web/js/name-cards.js')).href);
let failures = 0;
const ok = (cond, label) => { if (cond) console.log(`ok   ${label}`); else { failures++; console.log(`FAIL ${label}`); } };

// Wider than every appearance's name type at its weight (Barlow, Cormorant Garamond, Jost,
// Saira average 0.47-0.56 em over mixed-case names; Saira's caps run widest).
const MEASURE_EM = 0.6;
const measure = (text, size) => text.length * size * MEASURE_EM;

// 1. Every name of every year fits, one line or two, nothing cut.
for (const year of ['1812', '1835', '1904']) {
  const file = path.join(root, 'data/sidecars', year, 'people.json');
  if (!fs.existsSync(file)) { ok(false, `${year}: people.json is there`); continue; }
  const people = JSON.parse(fs.readFileSync(file, 'utf8')).people ?? [];
  const cut = [], two = [];
  for (const p of people) {
    if (!p.name) continue;
    const fit = m.fitName(p.name, measure);
    if (fit.cut) cut.push(p.name);
    if (fit.lines.length > 1) two.push(p.name);
    if (fit.width > m.TEXT_MAX) cut.push(`${p.name} (over)`);
  }
  ok(people.length > 0 && cut.length === 0, `${year}: all ${people.length} names fit their card${cut.length ? ` — cut: ${cut.slice(0, 5).join(' | ')}` : ''} (${two.length} on two lines)`);
}
{
  const short = m.fitName('Paul Grummo', measure);
  ok(short.lines.length === 1 && short.size === m.NAME_SIZES[0], 'a short name is one line at the largest size');
  const long = m.fitName('A man of the Chicago militia, name not recorded (1 of 6)', measure);
  ok(long.lines.length === 2 && !long.cut && Math.abs(long.lines[0].length - long.lines[1].length) <= 12, `a long label breaks evenly over two lines: ${JSON.stringify(long.lines)}`);
  const huge = m.fitName('x'.repeat(200), measure);
  ok(huge.cut && huge.width <= m.TEXT_MAX && /…$/.test(huge.lines.at(-1)), 'past two lines at the smallest size a name is cut with an ellipsis, inside the card');
  ok(m.cardWidth(short) < m.SLOT_W && m.cardWidth(long) <= m.SLOT_W, 'a card is never wider than its slot');
}

// 2. Who is carded: the nearest in view within reach, at most the tier's number.
{
  const c = Array.from({ length: 40 }, (_, i) => ({ key: `p${i}`, distance: 50 - i, inView: i % 7 !== 0 }));
  const light = m.chooseCards(c, m.NAME_CARD_TIERS.light);
  ok(light.length === m.NAME_CARD_TIERS.light.max, `Light cards at most ${m.NAME_CARD_TIERS.light.max}`);
  ok(light.every((x) => x.distance <= m.NAME_CARD_TIERS.light.reach && x.inView), 'only within reach and in view');
  ok(light.every((x, i) => !i || light[i - 1].distance <= x.distance), 'nearest first');
  ok(m.NAME_CARD_TIERS.light.max < m.NAME_CARD_TIERS.balanced.max && m.NAME_CARD_TIERS.balanced.max <= m.NAME_CARD_TIERS.full.max
    && m.NAME_CARD_TIERS.light.reach < m.NAME_CARD_TIERS.full.reach, 'a phone (Light) cards fewer, nearer, than a desktop');
}

// 3. The size on the screen and the fade at reach.
{
  const r = 40;
  ok(m.cardPx(1, r) === m.CARD_PX.near && m.cardPx(r, r) === m.CARD_PX.far && m.cardPx(20, r) < m.CARD_PX.near, 'a card is larger close by and stays readable at reach');
  ok(m.reachAlpha(10, r) === 1 && m.reachAlpha(r, r) === 0 && m.reachAlpha(r - m.EDGE_M / 2, r) > 0 && m.reachAlpha(r - m.EDGE_M / 2, r) < 1, 'it fades over the last metres of its reach');
}

// 4. Each appearance's card is its own CSS (skins.css).
{
  const css = fs.readFileSync(path.join(root, 'renderers/web/css/skins.css'), 'utf8');
  const block = (sel) => { const i = css.indexOf(sel); return i < 0 ? '' : css.slice(i, css.indexOf('}', i)); };
  const vars = (b) => Object.fromEntries([...b.matchAll(/(--[\w-]+):\s*([^;]+);/g)].map((x) => [x[1], x[2].trim()]));
  const seen = new Set();
  for (const skin of ['control-room', 'brass', 'worlds-fair', 'deep-space']) {
    const v = { ...vars(block(':root')), ...vars(block(`[data-skin="${skin}"]`)) };
    const t = m.cardTheme((k) => v[k], skin);
    ok(/^#|rgb/.test(t.panel) && /^#|rgb/.test(t.ink) && /^#|rgb/.test(t.accent) && t.panel !== t.ink, `${skin}: panel ${t.panel}, ink ${t.ink}, accent ${t.accent}`);
    seen.add(`${t.panel}|${t.accent}`);
  }
  ok(seen.size === 4, 'the four appearances give four different cards');
  const t = m.cardTheme(() => '', '');
  ok(t.panel && t.ink && t.font, 'with no CSS read, a card still has colours and a type');
  ok(m.cardTheme((k) => ({ '--r-control': '14px' })[k], 'worlds-fair').radius <= m.BODY_H / 2, 'Retro Future is a pill, never past half the body');
}

// 5. The pick: the nearest card under the point, only its body, only while it shows.
{
  const cards = [
    { key: 'a', cx: 0, cy: 0, hw: 0.1, hh: 0.03, depth: 9, alpha: 1 },
    { key: 'b', cx: 0.02, cy: 0, hw: 0.1, hh: 0.03, depth: 5, alpha: 1 },
    { key: 'c', cx: 0.5, cy: 0.5, hw: 0.1, hh: 0.03, depth: 2, alpha: 0.1 },
  ];
  ok(m.pickCard(cards, { x: 0.01, y: 0 })?.key === 'b', 'two cards under the point: the nearer');
  ok(m.pickCard(cards, { x: 0, y: 0.2 }) === null, 'above the body: nothing');
  ok(m.pickCard(cards, { x: 0.5, y: 0.5 }) === null, 'a card fading in or out is not picked');
}

// 5b. Cards that would cover one another stack, the nearer one lowest.
{
  const rects = [
    { cx: 0, cy: 0, hw: 0.2, hh: 0.03, depth: 8 },
    { cx: 0.05, cy: 0.01, hw: 0.2, hh: 0.03, depth: 6 },
    { cx: 0.7, cy: 0, hw: 0.1, hh: 0.03, depth: 9 },
  ];
  const lift = m.stackCards(rects);
  ok(lift[1] === 0 && lift[0] > 0.05 && lift[2] === 0, `the farther of two overlapping cards rises above the nearer (${lift.map((x) => x.toFixed(3)).join(', ')})`);
  // Three in a column: the third goes above the second, not back onto the first's top.
  const col = m.stackCards([
    { cx: 0.05, cy: 0.087, hw: 0.2, hh: 0.0365, depth: 6.5 },
    { cx: 0, cy: 0.09, hw: 0.2, hh: 0.0365, depth: 7 },
    { cx: 0, cy: 0.087, hw: 0.2, hh: 0.0365, depth: 8 },
  ]);
  ok(col[2] - col[1] > 0.07, `three overlapping cards stack three high (${col.map((x) => x.toFixed(3)).join(', ')})`);
  const crowd = Array.from({ length: 12 }, (_, i) => ({ cx: 0, cy: 0, hw: 0.2, hh: 0.03, depth: 5 + i }));
  ok(Math.max(...m.stackCards(crowd)) <= 4 * (0.06 + 0.008) + 1e-9, 'a crowd stacks at most four cards high');
}

// 6. The Settings switch: on by default, in Settings › Show, wired to the layer.
{
  const hud = fs.readFileSync(path.join(root, 'renderers/web/js/hud.js'), 'utf8');
  const html = fs.readFileSync(path.join(root, 'renderers/web/index.html'), 'utf8');
  const main = fs.readFileSync(path.join(root, 'renderers/web/js/main.js'), 'utf8');
  ok(/\n\s*nameCards: true,/.test(hud), 'the default is on (hud.js DEFAULT_SETTINGS.nameCards)');
  ok(/wireToggle\('s-name-cards', 'nameCards'\)/.test(hud) && /id="s-name-cards"/.test(html), 'the switch is a Settings row wired to nameCards');
  const show = html.indexOf('id="row-people"'), row = html.indexOf('id="row-name-cards"');
  const group = html.lastIndexOf('data-set-pane=', row);
  ok(row > show && html.slice(group, group + 30).includes('"show"'), 'it sits under People in the Show tab');
  ok(/key === 'nameCards'[\s\S]{0,120}nameCards\?\.setShown/.test(main), 'a change turns the cards on or off at once');
  ok(/nameCards\?\.pickAt\(ndc\)/.test(main) && /api\.humans\.select\(\{ actor: nameCard\.actor \}\)/.test(main), 'a click or tap on a card opens the person as clicking them does');
  ok(/jauntStage\?\.named/.test(main), "a jaunt stop's castmates are carded too");
}

// 7. A phone's atlas stays small.
ok(m.atlasBytes('light') <= 4 * 2 ** 20 && m.atlasBytes('full') <= 8 * 2 ** 20,
  `the atlas is ${(m.atlasBytes('light') / 2 ** 20).toFixed(1)} MiB on Light, ${(m.atlasBytes('full') / 2 ** 20).toFixed(1)} MiB on Full`);

console.log(failures ? `\n${failures} failed` : '\nall passed');
process.exit(failures ? 1 : 0);
