#!/usr/bin/env node
// write_entry_pages.mjs — the app's front doors on chicago.polecat.live.
//
//   node tools/write_entry_pages.mjs <site/4d>
//
// The renderer is published at `walk/` (tools/publish.sh copies renderers/web
// there), but nobody is sent to that address: the app is reached at
//
//   /4d/            temporal observatory menu
//   /4d/<year>/     a named year — /4d/1835/, /4d/1812/, /4d/1880/
//   /4d/dev/…       the same doors on the dev preview (deploy copies the tree)
//
// Year doors load the one shared `walk/index.html`, adding a `<base href>` before
// the browser parses it. The small door keeps the short URL; it does not redirect
// or make five copies of the renderer. Every relative URL (./css, ./js, the import
// map and scene-loader.js's data base) still resolves from walk/. main.js reads
// the year from the door's path; `?year=` and any further query parameters still
// override. The separate root menu forwards explicit query deep links to a year door.
//
// A door is written for every scene in data/scenes/ and for every year in
// PLANNED. A planned year with no scene yet opens to a gate that says so rather
// than a GitHub 404 — and when its scene lands, the same URL starts working.
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync, mkdtempSync, rmSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';

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

/** Runs in the small year page; the renderer is parsed once at the same URL. */
async function openSharedDoor(baseHref, withBase) {
  const shared = new URL('index.html', document.baseURI);
  const fallback = new URL(shared);
  fallback.search = location.search;
  if (!fallback.searchParams.get('year')) {
    const year = location.pathname.match(/\/(\d{4})(?:\/index\.html)?\/?$/)?.[1];
    if (year) fallback.searchParams.set('year', year);
  }
  fallback.hash = location.hash;
  document.getElementById('entry-fallback').href = fallback.href;
  try {
    const response = await fetch(shared, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`The city page returned ${response.status}`);
    const html = withBase(await response.text(), baseHref);
    document.open();
    document.write(html);
    document.close();
  } catch {
    document.getElementById('entry-status').textContent = 'The city could not open. Try the link below or reload this page.';
    document.getElementById('entry-fallback').hidden = false;
  }
}

/** A small, stamped loader. The full renderer lives only at walk/index.html. */
export function sharedDoor(html, baseHref) {
  door(html, baseHref); // Refuse malformed canonical markup during publication.
  const stamp = html.match(/<p class="gate-build" id="gate-build"[^>]*>.*?<\/p>/s)?.[0] ?? '';
  const icon = html.match(/<link rel="icon"[^>]*>/)?.[0] ?? '';
  return `<!doctype html>
<html lang="en"><head>
<base href="${baseHref}">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>4D Chicago</title>
${icon}
<style>body{background:#16150f;color:#eee;font:16px system-ui;margin:2rem}a{color:#e8b45a}</style>
</head><body>
<p id="entry-status" role="status">Opening the city…</p>
<a id="entry-fallback" hidden>Open the city</a>
${stamp}
<noscript><p>JavaScript is needed to enter the city. <a href="../">Return to the Observatory</a>.</p></noscript>
<script>(${openSharedDoor.toString()})(${JSON.stringify(baseHref)}, ${door.toString()});</script>
</body></html>
`;
}

export function writeEntryPages(site) {
  const walk = path.join(site, 'walk', 'index.html');
  if (!existsSync(walk)) throw new Error(`${walk} does not exist — publish the renderer first`);
  const html = readFileSync(walk, 'utf8');
  const written = ['index.html'];
  writeFileSync(path.join(site, 'index.html'), readFileSync(path.join(ROOT4D, 'renderers/web/portal/index.html'), 'utf8'));
  for (const year of doorYears()) {
    mkdirSync(path.join(site, year), { recursive: true });
    writeFileSync(path.join(site, year, 'index.html'), year === '1812' && !existsSync(path.join(ROOT4D, 'data/scenes/1812.json'))
      ? readFileSync(path.join(ROOT4D, 'renderers/web/portal/pending.html'), 'utf8')
      : sharedDoor(html, '../walk/'));
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
    const fixture = mkdtempSync(path.join(os.tmpdir(), 'temporal-doors-'));
    try {
      mkdirSync(path.join(fixture, 'walk'));
      writeFileSync(path.join(fixture, 'walk/index.html'), html);
      writeEntryPages(fixture);
      const menu = readFileSync(path.join(fixture, 'index.html'), 'utf8');
      if (menu !== readFileSync(path.join(ROOT4D, 'renderers/web/portal/index.html'), 'utf8')) fail('root menu differs from its authored template');
      for (const year of ['1835', '1904', '1871']) {
        if (!menu.includes(`href="${year}/"`)) fail(`${year} is missing its relative destination link`);
        if (readFileSync(path.join(fixture, year, 'index.html'), 'utf8') !== sharedDoor(html, '../walk/')) fail(`${year} lost the shared renderer door`);
      }
      if (existsSync(path.join(ROOT4D, 'data/scenes/1812.json')) && readFileSync(path.join(fixture, '1812/index.html'), 'utf8') !== sharedDoor(html, '../walk/')) fail('1812 has its scene (T-2050) and did not get the shared renderer door');
      if (!existsSync(path.join(ROOT4D, 'data/scenes/1812.json')) && !/reconstruction pending/i.test(readFileSync(path.join(fixture, '1812/index.html'), 'utf8'))) fail('1812 must state its missing scene');
      const large = html.replace('<body>', '<body>' + '<div>shared renderer</div>'.repeat(4000));
      if (Buffer.byteLength(sharedDoor(large, '../walk/')) >= 4096) fail('a year door copied the renderer instead of sharing it');
      const stamped = large.replace('</body>', '<p class="gate-build" id="gate-build">build abc1234 · fixture</p></body>');
      if (!sharedDoor(stamped, '../walk/').includes('id="gate-build">build abc1234 · fixture</p>')) fail('the small door lost its raw build marker');
    } finally { rmSync(fixture, { recursive: true, force: true }); }
    // Exercise the actual loader: replacement is a new parse at the same URL,
    // while recovery carries the path's year only when no query overrides it.
    const saved = { document: globalThis.document, location: globalThis.location, fetch: globalThis.fetch };
    try {
      for (const href of ['https://fixture.test/4d/1835/?anchor=river#view',
        'https://fixture.test/4d/1871/?year=&anchor=river#view',
        'https://fixture.test/4d/dev/1871/index.html?year=1904&device=weak#view']) {
        for (const outcome of ['ok', 'http', 'malformed']) {
          const at = new URL(href), base = new URL('../walk/', at).href;
          const elements = { 'entry-status': { textContent: 'Opening the city…' }, 'entry-fallback': { hidden: true } };
          let written = null, opened = 0, closed = 0, requested = null;
          globalThis.location = at;
          globalThis.document = { baseURI: base, getElementById: id => elements[id],
            open: () => opened++, write: value => { written = value; }, close: () => closed++ };
          globalThis.fetch = async url => {
            requested = String(url);
            return { ok: outcome !== 'http', status: 503, text: async () => outcome === 'malformed' ? '<p>broken</p>' : html };
          };
          await openSharedDoor('../walk/', door);
          if (requested !== new URL('index.html', base).href || at.href !== href) fail(`${outcome}: loader changed its URL or fetched another page`);
          const recover = new URL(elements['entry-fallback'].href);
          const expectedYear = at.searchParams.get('year') || at.pathname.match(/\/(\d{4})(?:\/index\.html)?\/?$/)?.[1];
          if (recover.searchParams.get('year') !== expectedYear
            || recover.searchParams.get('anchor') !== at.searchParams.get('anchor')
            || recover.searchParams.get('device') !== at.searchParams.get('device')
            || recover.hash !== at.hash) fail(`${outcome}: recovery lost the year override or deep link`);
          if (outcome === 'ok') {
            if (written !== door(html, '../walk/') || opened !== 1 || closed !== 1 || !elements['entry-fallback'].hidden)
              fail('successful shared page was not parsed once with its base');
          } else if (written !== null || opened || closed || elements['entry-fallback'].hidden
            || !elements['entry-status'].textContent.includes('could not open')) fail(`${outcome}: failed page has no usable recovery`);
        }
      }
    } finally {
      for (const [key, value] of Object.entries(saved)) {
        if (value === undefined) delete globalThis[key]; else globalThis[key] = value;
      }
    }
    if (!process.exitCode) console.log(`write_entry_pages: self-test ok (doors: ${years.join(', ')})`);
  } else {
    const site = process.argv[2];
    if (!site) { console.error('usage: node tools/write_entry_pages.mjs <site/4d> | --self-test'); process.exit(2); }
    console.log(`entry pages: ${writeEntryPages(site).join(', ')}`);
  }
}
