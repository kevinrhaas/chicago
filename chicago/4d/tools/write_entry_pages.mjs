#!/usr/bin/env node
// write_entry_pages.mjs — the app's front doors on chicago.polecat.live.
//
//   node tools/write_entry_pages.mjs <site/4d>
//
// The renderer is published at `walk/` (tools/publish.sh copies renderers/web
// there), but nobody is sent to that address: the app is reached at
//
//   /4d/            the target year (1835)
//   /4d/<year>/     a named year — /4d/1835/, /4d/1812/, /4d/1880/
//   /4d/dev/…       the same doors on the dev preview (deploy copies the tree)
//
// Each door is `walk/index.html` with one `<base href>` added, pointing into
// walk/. Every relative URL on the page (./css, ./js, the import map, the data
// layer via scene-loader.js's document base) therefore resolves exactly as it
// does from walk/ itself, and the address bar keeps the short path. main.js reads
// the year from the door's path; `?year=` and any further query parameters still
// override, so /4d/?year=1835&debug=1 works as it always has.
//
// A door is written for every scene in data/scenes/ and for every year in
// PLANNED. A planned year with no scene yet opens to a gate that says so rather
// than a GitHub 404 — and when its scene lands, the same URL starts working.
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from 'node:fs';
import path from 'node:path';

export const PLANNED = ['1812', '1835', '1880'];

const HERE = path.dirname(new URL(import.meta.url).pathname);
const ROOT4D = path.resolve(HERE, '..');

export function doorYears(scenesDir = path.join(ROOT4D, 'data/scenes')) {
  const built = existsSync(scenesDir)
    ? readdirSync(scenesDir).map((f) => (f.match(/^(\d{4})\.json$/) || [])[1]).filter(Boolean)
    : [];
  return [...new Set([...PLANNED, ...built])].sort();
}

/** walk/index.html with `<base href>` inserted as the first child of <head>. */
export function door(html, baseHref) {
  if (/<base\s/i.test(html)) throw new Error('walk/index.html already carries a <base>');
  const out = html.replace(/<head([^>]*)>/i, `<head$1>\n<base href="${baseHref}">`);
  if (out === html) throw new Error('walk/index.html has no <head> to put a <base> in');
  return out;
}

export function writeEntryPages(site) {
  const walk = path.join(site, 'walk', 'index.html');
  if (!existsSync(walk)) throw new Error(`${walk} does not exist — publish the renderer first`);
  const html = readFileSync(walk, 'utf8');
  const written = ['index.html'];
  writeFileSync(path.join(site, 'index.html'), door(html, 'walk/'));
  for (const year of doorYears()) {
    mkdirSync(path.join(site, year), { recursive: true });
    writeFileSync(path.join(site, year, 'index.html'), door(html, '../walk/'));
    written.push(`${year}/index.html`);
  }
  return written;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  if (process.argv[2] === '--self-test') {
    const fail = (m) => { console.error(`FAIL  ${m}`); process.exitCode = 1; };
    const html = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
      + '<link rel="stylesheet" href="./css/walk.css">\n</head><body></body></html>';
    const d = door(html, '../walk/');
    if (!/<head>\n<base href="\.\.\/walk\/">\n<meta charset/.test(d)) fail('the <base> is not the first child of <head>');
    let threw = false;
    try { door(d, 'walk/'); } catch { threw = true; }
    if (!threw) fail('a page that already carries a <base> was given a second one');
    const years = doorYears();
    for (const y of PLANNED) if (!years.includes(y)) fail(`planned year ${y} gets no door`);
    if (!years.includes('1835')) fail('the target year gets no door');
    if (!process.exitCode) console.log(`write_entry_pages: self-test ok (doors: ${years.join(', ')})`);
  } else {
    const site = process.argv[2];
    if (!site) { console.error('usage: node tools/write_entry_pages.mjs <site/4d> | --self-test'); process.exit(2); }
    console.log(`entry pages: ${writeEntryPages(site).join(', ')}`);
  }
}
