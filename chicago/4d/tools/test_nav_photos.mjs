#!/usr/bin/env node
// T-2645 (NAV-510): Inspect's Photos tab — pictures by date, each with its year, a templated
// caption and its credit; the 12 best first by the stated rule and the rest behind "All N";
// "From this spot" only where a solved camera records where the picture was taken, carried
// into the field by the building's placement. No browser: the tab is drawn into a small
// hand-made DOM, and on Glessner House from the pictures compile_pictures.py derives in
// memory from the tree. The smoke (part 14) opens it in the page on both viewports.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  BEST, yearLabel, captionOf, creditOf, spotTarget, chooseBest, photosTab, renderPhotos, byDate,
} from '../renderers/web/js/photos-tab.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
let n = 0;
const ok = (label, fn) => { fn(); n++; console.log(`  ok ${label}`); };

// ---- a small DOM ---------------------------------------------------------------------------
function fakeDoc() {
  const doc = {
    createElement(tag) {
      const fns = {};
      const el = {
        tagName: tag.toUpperCase(), className: '', dataset: {}, attrs: {}, style: {}, children: [], _text: '',
        get textContent() { return this._text + this.children.map((c) => c.textContent).join(''); },
        set textContent(v) { this._text = String(v); this.children = []; },
        setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
        append(...cs) { for (const c of cs) { c.parent = el; el.children.push(c); } },
        replaceChildren(...cs) { el.children = []; el.append(...cs); },
        addEventListener(type, fn) { (fns[type] ??= []).push(fn); },
        click() { for (const fn of fns.click ?? []) fn({ preventDefault() {} }); },
        ownerDocument: doc,
      };
      return el;
    },
  };
  return doc;
}
const all = (el, out = []) => { for (const c of el.children ?? []) { out.push(c); all(c, out); } return out; };
const cls = (el, c) => all(el).filter((e) => String(e.className).split(' ').includes(c));

// ---- the year, the caption, the credit --------------------------------------------------------
ok('the year is the data\'s own: one year, a range, one end open, or Undated', () => {
  assert.equal(yearLabel({ years: [1888, 1888] }), '1888');
  assert.equal(yearLabel({ years: [1887, 1892] }), '1887–1892');
  assert.equal(yearLabel({ years: [1887, null] }), '1887 or later');
  assert.equal(yearLabel({ years: [null, 1908] }), '1908 or earlier');
  assert.equal(yearLabel({}), 'Undated');
  assert.equal(yearLabel({ years: ['1888', 1890] }), '1890 or earlier', 'a year that is not a number is not read');
});
ok('the caption is templated from the view and kind, never the archival title', () => {
  assert.equal(captionOf({ view: 'rear', kind: 'PHOTO', title: '1. Historic American Buildings Survey VIEW: x' }), 'The back, a photo.');
  assert.equal(captionOf({ view: 'oblique front', kind: 'PLATE' }), 'The front from the corner, a printed plate.');
  assert.equal(captionOf({ kind: 'SOMETHING' }), 'The building, a picture.');
});
ok('the credit is the creator, else the holder\'s first clause, else nothing', () => {
  assert.equal(creditOf({ creator: 'J. W. Taylor', holder: 'RBA' }), 'J. W. Taylor');
  assert.equal(creditOf({ holder: 'Chicagology — secondary web compilation' }), 'Chicagology');
  assert.equal(creditOf({}), '');
});

// ---- From this spot: the footprint frame into the field ----------------------------------------
ok('a spot is carried into the field as walker.js turns a footprint, and none without one', () => {
  const p = { spot: { u: 10, v: 5, h: 1.7, bearing: 270, pitch: 2 } };
  const flat = spotTarget(p, { local_e: 100, local_n: -50, rotation_deg: 0 });
  assert.deepEqual(flat, { e: 110, n: -45, yaw: 270, pitch: 2 });
  const turned = spotTarget(p, { local_e: 100, local_n: -50, rotation_deg: 90 });
  // walker.js: [e0 + u cos + v sin, n0 - u sin + v cos] with the turn clockwise from north.
  assert.ok(Math.abs(turned.e - 105) < 1e-9 && Math.abs(turned.n - -60) < 1e-9, JSON.stringify(turned));
  assert.equal(turned.yaw, 0, 'the heading turns with the building');
  assert.equal(spotTarget({}, { local_e: 0, local_n: 0 }), null);
  assert.equal(spotTarget(p, null), null);
});

// ---- the rule: a spot first, then period, nearness, kind; viewpoints in turn -------------------
const mk = (id, view, year, extra = {}) => ({ id, view, kind: 'PHOTO', period: 'in-period', years: [year, year], ...extra });
ok('a picture with a spot ranks first, and a second viewpoint takes its turn before the eleventh front', () => {
  const pool = [...Array.from({ length: 15 }, (_, i) => mk(`f${String(i).padStart(2, '0')}`, 'front elevation', 1904)),
    mk('cam', 'front elevation', 1965, { spot: { u: 0, v: 0, bearing: 0 } }), mk('side', 'rear', 1950)];
  const chosen = chooseBest(pool, 1904).map((p) => p.id);
  assert.equal(chosen.length, BEST);
  assert.equal(chosen[0], 'cam');
  assert.equal(chosen[1], 'side', 'views take turns');
});
ok('within a view: in-period before later, nearer the scene year first, photographs before drawings', () => {
  const pool = [mk('later', 'rear', 1904, { period: 'later' }), mk('far', 'rear', 1960), mk('near', 'rear', 1900),
    mk('drawing', 'rear', 1900, { kind: 'DRAWING' })];
  assert.deepEqual(chooseBest(pool, 1904).map((p) => p.id), ['near', 'drawing', 'far', 'later']);
});

// ---- the tab as data, on a fixture ------------------------------------------------------------
const store = { base_url: 'https://store.test/files/' };
const held = (id) => ({ t: `${id}-thumb.jpg`, f: `${id}.jpg`, a: 1.5 });
const fixture = {
  image_store: store,
  by_structure: {
    house: [
      ...Array.from({ length: 14 }, (_, i) => ({ ...mk(`p${i}`, i % 2 ? 'rear' : 'front elevation', 1880 + i), holder: 'A library', held: held(`p${i}`) })),
      { ...mk('nocredit', 'rear', 1890), held: held('nocredit') },
      { ...mk('undated', 'interior', null), years: undefined, creator: 'Someone', held: held('undated') },
      { ...mk('spot', 'side elevation', 1887), creator: 'J. W. Taylor', held: held('spot'), spot: { u: 1, v: 2, h: 1.7, bearing: 233, pitch: 0 } },
      { ...mk('away', 'rear', 1888), holder: 'A museum', url: 'https://holder.test/away' },
    ],
  },
};
ok('the tab shows the held, credited pictures by date, the best 12 by date, and lists the rest as links', () => {
  const tab = photosTab(fixture, 'house', 1904);
  assert.equal(tab.count, 16);
  assert.equal(tab.best.length, BEST);
  assert.deepEqual(tab.all, [...tab.all].sort(byDate));
  assert.deepEqual(tab.best, [...tab.best].sort(byDate));
  assert.equal(tab.all.at(-1).id, 'undated', 'undated sorts last');
  assert.ok(tab.best.some((p) => p.id === 'spot'), 'the picture with a spot is among the best');
  assert.deepEqual(tab.links.map((p) => p.id).sort(), ['away', 'nocredit'], 'no picture is shown without its credit; an unheld one is a link');
  const order = fixture.by_structure.house.filter((p) => p.held);
  for (const p of tab.all) assert.equal(order[p.at].id, p.id, 'each tile opens its own picture in the card viewer');
  assert.equal(photosTab(null, 'house', 1904), null);
  assert.deepEqual(photosTab(fixture, 'nobody', 1904), { count: 0, all: [], best: [], links: [] });
});

// ---- the tab drawn ---------------------------------------------------------------------------
ok('the pane draws 12 tiles with year, caption and credit; All N shows every one; From this spot only on a spot', () => {
  const doc = fakeDoc();
  const pane = doc.createElement('section');
  const spots = [];
  assert.equal(renderPhotos(pane, { doc: fixture, id: 'house', sceneYear: '1904', onSpot: (p) => spots.push(p.id) }), true);
  const tiles = () => cls(pane, 'ph-item');
  assert.equal(tiles().length, BEST);
  for (const t of tiles()) {
    assert.ok(cls(t, 'ph-year')[0].textContent, 'a year');
    assert.match(cls(t, 'ph-cap')[0].textContent, /^[A-Z].*\.$/, 'a caption');
    assert.ok(cls(t, 'ph-credit')[0].textContent.trim(), 'a credit');
    assert.match(cls(t, 'ph-thumb')[0].src, /^https:\/\/store\.test\/files\/.+-thumb\.jpg$/);
  }
  const spotButtons = () => cls(pane, 'ph-spot');
  assert.equal(spotButtons().length, 1);
  assert.equal(spotButtons()[0].parent.dataset.photo, 'spot');
  assert.equal(spotButtons()[0].textContent, 'From this spot');
  spotButtons()[0].click();
  assert.deepEqual(spots, ['spot']);
  const more = cls(pane, 'ph-all')[0];
  assert.equal(more.textContent, 'All 16');
  more.click();
  assert.equal(tiles().length, 16);
  assert.equal(cls(pane, 'ph-grid')[0].dataset.showing, 'all');
  assert.ok(tiles().some((t) => cls(t, 'ph-year')[0].textContent === 'Undated'), 'an undated picture says so');
  assert.equal(more.textContent, 'Best 12');
  more.click();
  assert.equal(tiles().length, BEST);
  const text = pane.textContent;
  assert.doesNotMatch(text, /[A-Za-z0-9]_[A-Za-z0-9]|\.json\b|\.jpg\b|\bT-\d{3,}/, 'no id, path or snake_case');
  // No onSpot (an app without the action): no button at all.
  const bare = doc.createElement('section');
  renderPhotos(bare, { doc: fixture, id: 'house', sceneYear: 1904 });
  assert.equal(cls(bare, 'ph-spot').length, 0);
  // No pictures file: the caller keeps the card's pane.
  assert.equal(renderPhotos(doc.createElement('section'), { doc: null, id: 'house', sceneYear: 1904 }), false);
});

// ---- link-only source identity and publication context -----------------------------------------
ok('link-only cards keep sourced identity warnings and creator plus holder without changing captions', () => {
  // Derived from the tree, as the Glessner case below is: data/pictures/ is written only at
  // publish, after this pooled step may already have run, so a clean checkout has no file.
  const py = 'import sys, json; sys.path.insert(0, "tools"); import compile_pictures as cp; '
    + 'print(json.dumps(cp.derive(*cp.read_tree())["1835"]))';
  const pictures = JSON.parse(execFileSync('python3', ['-c', py], { cwd: ROOT, encoding: 'utf8', maxBuffer: 64 << 20 }));
  for (const [sid, sourceId, leaf] of [
    ['jb_beaubien_homestead', 'kinzie_1857_chicago_1831_panorama', null],
    ['green_tree_tavern', 'andreas_1884_green_tree_hotel_plate', '1301'],
    ['sauganash_hotel', 'andreas_1884_sauganash_hotel_plate', '1297'],
  ]) {
    const picture = pictures.by_structure[sid].find(p => p.id === sourceId);
    assert.ok(picture && !picture.held, `${sourceId}: real compiled link-only entry`);
    const doc = fakeDoc(), pane = doc.createElement('section');
    renderPhotos(pane, { doc: { ...pictures, by_structure: { [sid]: [picture] } }, id: sid, sceneYear: 1835 });
    const link = all(pane).find(e => e.tagName === 'A');
    assert.equal(link.href, picture.url, 'original holder URL is unchanged');
    assert.equal(link.textContent, `${yearLabel(picture)} · ${captionOf(picture)}`, 'templated caption is unchanged');
    assert.ok(pane.textContent.includes(picture.title), 'the actual catalogue title is visible');
    assert.ok(pane.textContent.includes(creditOf(picture)), 'actual creator credit is retained');
    if (leaf) {
      assert.match(pane.textContent, /Andreas/i, 'the actual publication holder is visible');
      assert.match(pane.textContent, /1884/);
      assert.match(link.href, new RegExp(`/historyofchicago01andr/page/n${leaf}/mode/1up$`));
    } else {
      assert.match(pane.textContent, /unresolved.*Beaubien|Beaubien.*unresolved/i);
      assert.match(pane.textContent, /Kinzie/i);
      assert.match(pane.textContent, /Wikimedia Commons/);
      assert.doesNotMatch(pane.textContent, /chicago\/reference\//, 'local-copy locator is not newly exposed');
    }
  }
});

// ---- Glessner House, from the tree ------------------------------------------------------------
ok('Glessner House: more than 12 pictures, 12 best by date, every one credited, a spot only where a solved camera names it', () => {
  const py = 'import sys, json; sys.path.insert(0, "tools"); import compile_pictures as cp; '
    + 'print(json.dumps(cp.derive(*cp.read_tree())["1904"]))';
  let doc = null;
  try { doc = JSON.parse(execFileSync('python3', ['-c', py], { cwd: ROOT, encoding: 'utf8', maxBuffer: 64 << 20 })); } catch (err) {
    assert.fail(`compile_pictures.py could not derive the pictures: ${err.message}`);
  }
  const tab = photosTab(doc, 'glessner_house', 1904);
  assert.ok(tab.count > BEST, `Glessner has ${tab.count} pictures`);
  assert.equal(tab.best.length, BEST);
  assert.deepEqual(tab.best.map((p) => p.id), [...tab.best].sort(byDate).map((p) => p.id));
  assert.ok(tab.all.every((p) => creditOf(p)), 'every shown picture is credited');
  // A spot is exactly a picture a reference view of this building names (and not a far-off drawing camera).
  const dir = path.join(ROOT, 'data/reference_views/glessner_house');
  const named = new Set();
  for (const f of fs.readdirSync(dir).filter((f) => f.endsWith('.json') && !f.endsWith('.match.json'))) {
    const cam = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
    const fov = 2 * Math.atan(cam.image_px[1] / 2 / cam.focal_px) * 180 / Math.PI;
    if (fov >= 5) for (const k of [cam.library_image, cam.source_id]) if (k) named.add(k);
  }
  const withSpot = tab.all.filter((p) => p.spot);
  assert.ok(withSpot.length >= 1, 'at least one held picture of Glessner has a solved camera');
  assert.ok(withSpot.every((p) => named.has(p.id)), `spots: ${withSpot.map((p) => p.id)}`);
  assert.ok(tab.best.filter((p) => p.spot).length === withSpot.length, 'every picture with a spot is among the best');
  assert.ok(tab.all.every((p) => !/Historic American Buildings Survey|VIEW:/.test(captionOf(p))));
  // Standing at the NE camera of the c. 1887 photograph puts the visitor east of the house, facing it.
  const sc = JSON.parse(read('data/sidecars/1904/glessner_house.json'));
  const taylor = tab.all.find((p) => p.id === 'a18-rba-taylor-2135-glessner-ne');
  if (taylor) {
    const at = spotTarget(taylor, sc.placement);
    assert.ok(at.e > sc.placement.local_e + 49 && at.yaw > 180 && at.yaw < 270, JSON.stringify(at));
  }
});

// ---- the wiring ----------------------------------------------------------------------------------
ok('Inspect draws its Photos tab with renderPhotos, and the page offers From this spot through Show me', () => {
  const view = read('renderers/web/js/apps/inspect-view.js');
  assert.match(view, /renderPhotos\(pane, \{ doc: ctx\.picturesDoc/);
  const main = read('renderers/web/js/main.js');
  assert.match(main, /fromSpot: \(id, picture\) => fromSpotFor\(id, picture\)/);
  assert.match(main, /spotTarget\(picture, loaded\.registry\.get\(id\)\?\.sidecar\?\.placement\)/);
  assert.match(read('renderers/web/index.html'), /<link rel="stylesheet" href="\.\/css\/photos\.css">/);
});

console.log(`test_nav_photos: OK (${n} checks)`);
