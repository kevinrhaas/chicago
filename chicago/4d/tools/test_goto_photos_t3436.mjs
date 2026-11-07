#!/usr/bin/env node
// T-3436: Go to's 1904 viewpoints and its Photos. The owner, 2026-11-06: the viewpoints
// "are all eyes and a long text that takes up too much space and we have new interesting
// viewpoints like pullman and the church", and a Go to "by photo" listing every picture
// with a photo view, sorted like Go to, that walks or flies you to where the camera stood.
// Reads the real destinations inventory, the 1904 scene, the menu glyphs and travel.js.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createDestinations, shortTitle, shortCredit } from '../renderers/web/js/destinations.js';
import { GO_TO_KINDS, QUICK_STARTS } from '../renderers/web/js/welcome.js';
import { iconSvg } from '../renderers/web/js/menu-icons.js';
import { spotTarget } from '../renderers/web/js/photos-tab.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const json = (p) => JSON.parse(read(p));

// ---- the 1904 viewpoints: short names, their own glyphs, and the featured six ------------------
const scene = json('data/scenes/1904.json');
const anchors = new Map(scene.anchors.map((a) => [a.id, a]));
const eye = iconSvg('view');
for (const a of scene.anchors) {
  assert(a.short && a.short.length <= 24, `${a.id}: a short name of at most 24 characters (${a.short})`);
  assert(a.glyph && iconSvg(a.glyph) !== eye, `${a.id}: a glyph of its own, not the eye (${a.glyph})`);
}
const featured = QUICK_STARTS['1904'];
assert(featured?.length >= 5 && featured.length <= 6, 'five or six featured 1904 viewpoints');
for (const [id, label, glyph] of featured) {
  assert(anchors.has(id), `featured ${id} is a 1904 anchor`);
  assert(label.length <= 12, `featured ${id}'s tile name is one or two words (${label})`);
  assert(iconSvg(glyph) !== eye, `featured ${id} has its own glyph`);
}
assert.equal(new Set(featured.map(([, , g]) => g)).size, featured.length, 'no two featured tiles share a glyph');
for (const id of ['pullman_house', 'first_presbyterian', 'field_house', 'prairie_from_above'])
  assert(anchors.has(id), `the new viewpoint ${id} is in the 1904 scene`);
assert(anchors.get('prairie_from_above').altitude_m > 0, 'From above is an aerial viewpoint');

// ---- the list names a viewpoint by its short name; the full line stays searchable --------------
const terrain = { surfaceHeight: () => 2, isWater: () => false };
const placement = (e, n, rotation_deg = 0) => ({ local_e: e, local_n: n, rotation_deg, position_confidence: 'attested' });
const record = (name, p) => ({ sidecar: { name, attributes: { function: { value: 'house' } }, documented_range: { confidence: 'attested' }, placement: p } });
const registry = new Map([
  ['pullman_house_1729_prairie', record('1729 Prairie Avenue — the George M. Pullman house (K01)', placement(100, 0, 90))],
  ['keith_house_1808_prairie', record('1808 Prairie Avenue — the Osborn Keith house', placement(0, -50))],
  ['first_presbyterian_church_2029_indiana', record('2029-2035 Indiana Avenue — First Presbyterian Church (district draft)', placement(-50, -200))],
]);
const d = createDestinations({ terrain, router: null, people: null, index: { intersections: [] }, registry,
  scene: { anchors: [{ id: 'pullman_house', label: 'Prairie at Eighteenth, facing the Pullman house across the corner', short: 'Pullman House', glyph: 'mansion', local_e: 90, local_n: -10, yaw_deg: 45 }] } });
const v = d.byId('anchor', 'pullman_house');
assert.equal(v.label, 'Pullman House');
assert.equal(v.glyph, 'mansion');
assert.equal(d.search('facing the pullman', { kind: 'anchor' }).length, 1, 'the full line is still searched');

// ---- Photos: one row per picture with a spot, at the camera, not in All ------------------------
const held = (id) => ({ t: `${id}-thumb.jpg`, f: `${id}.jpg`, a: 1.3 });
const shared = { id: 'det-pullman-from-sw', kind: 'PHOTO', view: 'oblique front', title: 'Pullman residence, from the south-west', creator: 'Detroit Publishing Co.',
  years: [1893, 1901], held: held('det'), spot: { u: 10, v: -20, h: 1.6, bearing: 30, pitch: 4 } };
const pictures = {
  image_store: { base_url: 'https://example.test/files/' },
  names: { pullman_house_1729_prairie: 'Pullman House', keith_house_1808_prairie: 'Osborn Keith House' },
  by_structure: {
    // The same picture under two buildings is listed once, under the one its title names.
    keith_house_1808_prairie: [{ ...shared, spot: { u: 5, v: 5, h: 1.6, bearing: 30, pitch: 0 } },
      { id: 'no-spot', kind: 'PHOTO', creator: 'X', held: held('n'), years: [1890, 1890] },
      { id: 'not-held', kind: 'PHOTO', creator: 'Y', years: [1890, 1890], spot: { u: 1, v: 1, bearing: 0 } }],
    pullman_house_1729_prairie: [shared],
    first_presbyterian_church_2029_indiana: [{ id: 'church-1887', kind: 'PHOTO', creator: 'Otis', years: [1887, 1887], held: held('c'), spot: { u: 30, v: 0, h: 1.5, bearing: 270, pitch: 0 } }],
  },
};
assert.equal(d.search('', { kind: 'photo' }).length, 0, 'no Photos before the pictures file is read');
assert.equal(d.addPhotos(pictures), 2, 'two pictures stand in the town: one shared, one alone');
assert.equal(d.addPhotos(pictures), 0, 'read once');
const photos = d.search('', { kind: 'photo', sort: 'name' });
assert.deepEqual(photos.map((r) => r.id), ['church-1887', 'det-pullman-from-sw']);
const pullman = d.byId('photo', 'det-pullman-from-sw');
assert.equal(pullman.of, 'pullman_house_1729_prairie', 'a shared picture goes to the building its title names');
assert.equal(pullman.label, 'Pullman House · 1893–1901');
assert.equal(pullman.thumb, 'https://example.test/files/det-thumb.jpg');
const at = spotTarget(shared, registry.get('pullman_house_1729_prairie').sidecar.placement);
assert.deepEqual([pullman.e, pullman.n, pullman.yaw_deg, pullman.pitch_deg], [at.e, at.n, at.yaw, at.pitch], 'the row stands where From this spot stands');
assert.equal(d.byId('photo', 'church-1887').label, 'First Presbyterian Church · 1887', 'an unnamed building takes its title\'s name');
assert(!d.search('', { kind: 'all' }).some((r) => r.kind === 'photo'), 'Photos stay out of All');
assert.equal(d.search('detroit', { kind: 'photo' }).length, 1, 'a photo is found by its photographer');
assert(d.resolve(pullman) && !d.resolve(pullman).structureId, 'a photo resolves to its own spot, not the building\'s stand');
assert.equal(d.search('', { kind: 'photo', sort: 'near', visitor: { e: at.e, n: at.n } })[0].id, 'det-pullman-from-sw', 'nearest first');
// Places take the jaunts' short names once the file is read; the full title stays searchable.
const keith = d.byId('structure', 'keith_house_1808_prairie');
assert.equal(keith.label, 'Osborn Keith House');
assert.match(keith.sub, /^1808 Prairie Avenue · /);
assert.equal(d.search('osborn keith house', { kind: 'structure' }).length, 1);
assert.equal(d.search('the osborn keith house', { kind: 'structure' }).length, 1, 'the record\'s own title is still searched');
assert.equal(shortCredit('Glessner House Museum (reproduced on its blog "The Story of a House")'), 'Glessner House Museum');
assert.equal(shortCredit('unknown photographer'), 'Unknown photographer');
assert.equal(shortCredit('Detroit Publishing Co., publisher'), 'Detroit Publishing Co.');
assert.equal(shortTitle('1801 Prairie Avenue — W. W. Kimball\'s Chateauesque house in Bedford stone, built on K01 at the massing'), '1801 Prairie Avenue');
assert(GO_TO_KINDS.some(([id, l]) => id === 'photo' && l === 'Photos'));

// ---- going there: travel stands a photo where its camera stood, at its tilt ---------------------
const travel = read('renderers/web/js/travel.js');
assert(/target\.kind === 'photo' && p\) \{\s*teleport\?\.\(\{ local_e: p\.e, local_n: p\.n, yaw_deg: target\.yaw_deg \?\? 0, pitch_deg: target\.pitch_deg \?\? 0 \}\)/.test(travel), 'Go instantly stands at the camera');
assert(/\(r\.kind === 'photo' \|\| r\.kind === 'anchor'\) && Number\.isFinite\(r\.target\?\.pitch_deg\)/.test(travel), 'a ride settles to the camera\'s tilt');
const main = read('renderers/web/js/main.js');
assert(/photos: \(\) => ensurePictures\(\)/.test(main), 'Go to reads the cards\' pictures file');
// The owner, 2026-11-06: "you already have from this spot so that should be doing most of the
// work on that with the highlighted photo yellow rim at the end".
assert(/resolved\.kind === 'photo'\) \{\s*return travel\.go\(resolved, \{ onArrive: \(\) => \{\s*void api\.fromSpot\?\.\(resolved\.of, resolved\.picture\);/.test(main),
  'arriving at a photo view ends in From this spot, the building outlined');
// The owner, 2026-11-07: "pop open the photo in the card that you are navigating to so you can
// see the larger version and be able to open in new window".
assert(/openBuilding\(resolved\.of, \{ photo: resolved\.picture\?\.id \?\? resolved\.id \}\)/.test(main), 'and the building\'s card opens on that photo');
assert(/photo \? \{ app: 'inspect', id, tab: 'photos', photo \}/.test(main), 'a photo link opens the Photos tab');
const inspect = read('renderers/web/js/apps/inspect-view.js');
assert(/if \(next\.photo\) link\.photo = next\.photo;/.test(read('renderers/web/js/navigator.js')), 'the Navigator carries the photo to Inspect');
assert(/if \(photo\) \{ photoLinked = ctx\.link; tab = 'photos'; \}/.test(inspect) && /featured: photo \}/.test(inspect), 'the card shows that photo first');
const walk = read('renderers/web/css/walk.css');
assert(/\.welcome-quick \{ display: grid; grid-template-columns: repeat\(3, minmax\(0, 1fr\)\);/.test(walk), 'the featured tiles are compact, three to a row');
assert(/\.welcome-destination \.welcome-thumb \{/.test(walk), 'a photo row shows its picture');
assert(/\.nav-screen \.welcome-results \{ overflow-y: visible; overscroll-behavior: auto;/.test(walk), 'in the Navigator the list leaves the mouse wheel to the screen');
// A phone keeps the chips three to a row, icon over name, rather than one row scrolling
// sideways: the T-2656 reflow check at 140 % text finds a sideways strip a fault.
const phone = walk.match(/On a phone the chips stay three to a row[\s\S]*?\n\}/)?.[0] ?? '';
assert(/\.welcome-quick-start \{ flex-direction: column;/.test(phone) && !/overflow-x|grid-auto-flow: column/.test(phone), 'phone chips stack, no sideways strip');
// The featured picture: large at the head of the Photos tab, a tap opening the viewer on it,
// and the full-size copy a link away in its own window.
{
  const { renderPhotos } = await import('../renderers/web/js/photos-tab.js');
  const mk = (tag) => ({ tagName: tag.toUpperCase(), children: [], dataset: {}, attrs: {}, className: '', textContent: '',
    append(...k) { this.children.push(...k); }, replaceChildren(...k) { this.children = [...k]; }, addEventListener() {},
    setAttribute(k, v) { this.attrs[k] = v; }, get isConnected() { return true; } });
  const fake = { createElement: mk };
  const pane = { ownerDocument: fake, children: [], append(...k) { this.children.push(...k); } };
  const find = (n, pred) => (pred(n) ? n : (n.children ?? []).map((c) => find(c, pred)).find(Boolean) ?? null);
  const pics = { image_store: { base_url: 'https://example.test/files/' }, by_structure: { pullman_house_1729_prairie: [shared, { id: 'other', kind: 'PHOTO', creator: 'Z', years: [1899, 1899], held: held('o') }] } };
  assert(renderPhotos(pane, { doc: pics, id: 'pullman_house_1729_prairie', sceneYear: 1904, featured: 'det-pullman-from-sw' }));
  const sec = pane.children[0];
  const fig = find(sec, (n) => n.className === 'ph-hero');
  assert(fig && sec.children.indexOf(fig) === 1, 'the arrived-at picture heads the tab, under its title');
  assert.equal(fig.dataset.photo, 'det-pullman-from-sw');
  const open = find(fig, (n) => n.className === 'ph-hero-open');
  assert.equal(open.dataset.pic, '0', 'a tap opens the viewer on it');
  assert.equal(find(fig, (n) => n.className === 'ph-hero-img').src, 'https://example.test/files/det-thumb.jpg', 'the thumbnail shows at once');
  const a = find(fig, (n) => n.className === 'ph-hero-full');
  assert.equal(a.href, 'https://example.test/files/det.jpg');
  assert.equal(a.target, '_blank', 'the full size opens in a new window');
  const plain = { ownerDocument: fake, children: [], append(...k) { this.children.push(...k); } };
  renderPhotos(plain, { doc: pics, id: 'pullman_house_1729_prairie', sceneYear: 1904 });
  assert(!find(plain.children[0], (n) => n.className === 'ph-hero'), 'no picture is featured unless one was gone to');
}
console.log('test_goto_photos_t3436: 1904 viewpoints by short name and glyph, six featured, Photos listed at their cameras and gone to like any place');
