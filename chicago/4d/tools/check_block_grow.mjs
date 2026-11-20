#!/usr/bin/env node
/**
 * T-3676: "Watch a block grow" (renderers/web/js/block-grow.js and block-grow-scene.js),
 * read against the committed 1904 sidecars, with no browser.
 *
 *   node tools/check_block_grow.mjs
 *
 * Holds: the recorded years are read as the records write them and never guessed; the
 * blocks offered are the ones where most lots have a recorded year, the Glessner side of
 * the 1800 block first; the Glessner block's buildings stand, ghost or wait exactly as
 * their records say in every year from 1857 to 1904; an undated building is never shown
 * standing before 1904 and never hidden unless its lot's dated house is not yet built;
 * every year's source resolves to a committed source record and to the card's citation;
 * and the scene half holds exactly the year's unbuilt and ghosted buildings, draws a
 * ghost for each ghost, and on Leave lets go of every one, puts the doors back, removes
 * its ghosts and returns the eye where it was.
 */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const web = (name) => new URL(`../renderers/web/js/${name}`, import.meta.url).href;
const G = await import(web('block-grow.js'));
const { readableNote } = await import(web('block-grow-view.js'));
const vendor = new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
const sceneText = fs.readFileSync(new URL('../renderers/web/js/block-grow-scene.js', import.meta.url), 'utf8')
  .replace("from 'three'", `from ${JSON.stringify(vendor)}`)
  .replace("from './block-grow.js'", `from ${JSON.stringify(web('block-grow.js'))}`);
const S = await import(`data:text/javascript;base64,${Buffer.from(sceneText).toString('base64')}`);

let passed = 0;
const test = (name, fn) => { fn(); passed += 1; console.log(`PASS ${name}`); };

const dir = path.join(root, 'data/sidecars/1904');
const registry = new Map();
for (const f of fs.readdirSync(dir).filter((f) => f.endsWith('.json')).sort()) {
  let s;
  try { s = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); } catch { continue; }
  if (s && typeof s === 'object' && typeof s.id === 'string' && s.attributes) registry.set(s.id, { sidecar: s });
}

test('a recorded year is read as written, and nothing that names no year is given one', () => {
  assert.deepEqual(G.parseBuilt(1887), { from: 1887, by: 1887 });
  assert.deepEqual(G.parseBuilt('between 1870 and 1876'), { from: 1870, by: 1876 });
  assert.deepEqual(G.parseBuilt('1864 or 1875'), { from: 1864, by: 1875 });
  assert.deepEqual(G.parseBuilt('about 1832'), { from: 1832, by: 1832 });
  for (const v of [null, undefined, '', 'unknown', 'early', 18.5, {}]) assert.equal(G.parseBuilt(v), null);
});

const blocks = G.offeredBlocks(registry);
const glessner = blocks[0];

test('the blocks offered are those where most lots have a recorded year, Glessner first', () => {
  assert.deepEqual(blocks.map((b) => b.id), ['prairie-1800-west', 'prairie-1700-east', 'prairie-1900-west']);
  assert.equal(glessner.title, '1800 block of Prairie Avenue, west side');
  for (const b of blocks) assert(b.datedLots >= 2 && b.datedLots * 2 >= b.lots.length, b.id);
  // and a block mostly without recorded years is not offered (1800 east: 2 of 5 lots)
  const east = G.blocksOf(registry).find((b) => b.id === 'prairie-1800-east');
  assert(east && !blocks.includes(east));
});

const GLESSNER_BLOCK = {
  glessner_house: 1887,
  keith_house_1808_prairie: 1886,
  wheeler_house_1812_prairie: 1884,
  wheeler_house_1812_prairie_coach_house: null,
  henderson_house_1816_prairie: null,
  henderson_house_1816_prairie_coach_house: null,
  marsh_house_1824_prairie: 1857,
  marsh_house_1824_prairie_coach_house: null,
  house_1828_prairie: null,
  house_1828_prairie_coach_house: null,
  jones_house_1834_prairie: 1866,
  jones_house_1834_prairie_coach_house: null,
  shed_1834_1900_prairie: null,
};

test('the Glessner block holds every building of its lots, each with its recorded year or none', () => {
  assert.deepEqual(Object.fromEntries(glessner.members.map((m) => [m.id, m.built ? m.built.value : null])), GLESSNER_BLOCK);
  assert.deepEqual(G.yearsOf(glessner), Array.from({ length: 1904 - 1857 + 1 }, (_, i) => 1857 + i));
});

// What each year shows on the Glessner block. Outlines: the undated houses and sheds in
// every year, an outbuilding once its house is up. Not yet built: the rest.
const sorted = (a) => [...a].sort();
const expect = (year, standing, outbuildingsOf) => {
  const undatedLots = ['henderson_house_1816_prairie', 'henderson_house_1816_prairie_coach_house',
    'house_1828_prairie', 'house_1828_prairie_coach_house', 'shed_1834_1900_prairie'];
  const coach = { wheeler_house_1812_prairie: 'wheeler_house_1812_prairie_coach_house',
    marsh_house_1824_prairie: 'marsh_house_1824_prairie_coach_house', jones_house_1834_prairie: 'jones_house_1834_prairie_coach_house' };
  const ghost = [...undatedLots, ...standing.map((id) => coach[id]).filter(Boolean)];
  const hidden = Object.keys(GLESSNER_BLOCK).filter((id) => !standing.includes(id) && !ghost.includes(id));
  return { year, standing: sorted(standing), ghost: sorted(ghost), hidden: sorted(hidden) };
};
const GLESSNER_YEARS = [
  expect(1857, ['marsh_house_1824_prairie']),
  expect(1865, ['marsh_house_1824_prairie']),
  expect(1866, ['marsh_house_1824_prairie', 'jones_house_1834_prairie']),
  expect(1883, ['marsh_house_1824_prairie', 'jones_house_1834_prairie']),
  expect(1884, ['marsh_house_1824_prairie', 'jones_house_1834_prairie', 'wheeler_house_1812_prairie']),
  expect(1885, ['marsh_house_1824_prairie', 'jones_house_1834_prairie', 'wheeler_house_1812_prairie']),
  expect(1886, ['marsh_house_1824_prairie', 'jones_house_1834_prairie', 'wheeler_house_1812_prairie', 'keith_house_1808_prairie']),
  expect(1887, ['marsh_house_1824_prairie', 'jones_house_1834_prairie', 'wheeler_house_1812_prairie', 'keith_house_1808_prairie', 'glessner_house']),
  expect(1903, ['marsh_house_1824_prairie', 'jones_house_1834_prairie', 'wheeler_house_1812_prairie', 'keith_house_1808_prairie', 'glessner_house']),
];

test('each year of the Glessner block shows exactly the buildings its records have standing by then', () => {
  for (const want of GLESSNER_YEARS) {
    const got = G.stateAt(glessner, want.year);
    assert.deepEqual({ year: got.year, standing: sorted(got.standing), ghost: sorted(got.ghost), hidden: sorted(got.hidden) }, want, `year ${want.year}`);
  }
  const appears = {};
  for (const y of G.yearsOf(glessner)) for (const a of G.stateAt(glessner, y).appearing) appears[a.id] = y;
  assert.deepEqual(appears, { marsh_house_1824_prairie: 1857, jones_house_1834_prairie: 1866, wheeler_house_1812_prairie: 1884,
    keith_house_1808_prairie: 1886, glessner_house: 1887 }, 'each dated house has its card in its own year and only then');
  const final = G.stateAt(glessner, 1904);
  assert.equal(final.final, true);
  assert.deepEqual(sorted(final.standing), sorted(Object.keys(GLESSNER_BLOCK)), '1904 is the town itself');
  assert.equal(final.ghost.length + final.hidden.length + final.appearing.length, 0);
});

test('a recorded span is an outline from its first year and standing from its last (Pullman, 1870-1876)', () => {
  const b = blocks.find((x) => x.id === 'prairie-1700-east');
  for (const [year, state] of [[1869, 'hidden'], [1870, 'ghost'], [1875, 'ghost'], [1876, 'standing']]) {
    const s = G.stateAt(b, year);
    const of = (id) => (s.standing.includes(id) ? 'standing' : s.ghost.includes(id) ? 'ghost' : 'hidden');
    assert.equal(of('pullman_house_1729_prairie'), state, `${year}`);
    assert.equal(of('pullman_house_1729_prairie_ranges'), state, `${year} ranges`);
    // its conservatory has no year of its own: out of view until the house is begun, then an outline
    assert.equal(of('pullman_house_1729_prairie_conservatory'), year < 1870 ? 'hidden' : 'ghost', `${year} conservatory`);
  }
  assert.deepEqual(G.stateAt(b, 1870).appearing.map((a) => [a.id, a.state]),
    [['pullman_house_1729_prairie', 'ghost'], ['pullman_house_1729_prairie_ranges', 'ghost']]);
  assert.deepEqual(G.stateAt(b, 1876).appearing.map((a) => a.id), ['pullman_house_1729_prairie', 'pullman_house_1729_prairie_ranges']);
});

test('no year is ever guessed: an undated building is never standing before 1904, nor hidden unless its lot waits on its house', () => {
  for (const b of blocks) {
    for (const y of G.yearsOf(b)) {
      if (y === G.SCENE_YEAR) continue;
      const s = G.stateAt(b, y);
      for (const m of b.undated) {
        assert(!s.standing.includes(m.id), `${b.id} ${y} ${m.id} standing`);
        const lot = b.lots.find((l) => l.stem === m.stem);
        const waits = lot.members.some((x) => x.built) && !lot.members.some((x) => x.built && y >= x.built.from);
        assert.equal(s.hidden.includes(m.id), waits, `${b.id} ${y} ${m.id}`);
      }
      assert.equal(s.standing.length + s.ghost.length + s.hidden.length, b.members.length);
      assert.deepEqual(sorted(G.heldAt(s)), sorted([...s.ghost, ...s.hidden]));
    }
  }
});

test('every recorded year names its confidence and its sources, and each source is committed and cited on the card', () => {
  for (const b of blocks) {
    for (const m of b.dated) {
      assert(['attested', 'inferred', 'reconstructed'].includes(m.built.confidence), m.id);
      assert(m.built.sources.length > 0, `${m.id} has no source`);
      for (const s of m.built.sources) {
        assert(fs.existsSync(path.join(root, 'data/sources', `${s.id}.json`)), `${m.id}: ${s.id} is not a committed source`);
        assert(s.citation.length > 10, `${m.id}: ${s.id} has no citation on the card`);
      }
      assert(!/_house|_prairie/.test(m.name), `${m.id} is named by its id`);
    }
  }
  assert.equal(readableNote("The marker: 'John Glessner Residence. Built 1887'; the family moved in that December."),
    "The marker: 'John Glessner Residence. Built 1887'; the family moved in that December.");
  assert.equal(readableNote('Chicagology (chicagology_1736_prairie_page) says 1875.'), '', 'a note naming a record id is not shown');
});

// ---- the scene half, against a stand-in town ----------------------------------------
{
  const T = await import(vendor);
  const calls = [];
  const fakeBuildings = {
    setHeld(ids) { calls.push([...ids]); return ids; },
    instanceBounds() {
      const out = {};
      for (const m of glessner.members) out[m.id] = { size: [10, 12, 20], min: [-5, 0, -10], max: [5, 12, 10] };
      return out;
    },
    matrixOf(id) {
      const p = registry.get(id).sidecar.placement;
      return new T.Matrix4().makeTranslation(p.local_e, 0, -p.local_n);
    },
  };
  const door = new T.Group(); door.name = 'house-door:glessner_house:front';
  const otherDoor = new T.Group(); otherDoor.name = 'house-door:kimball_house_1801_prairie:front';
  const doors = new T.Group(); doors.add(door, otherDoor);
  const coach = new T.Group(); coach.name = 'coach-house';
  const room = new T.Mesh(); room.userData.structure_id = 'glessner_house'; coach.add(room);
  const scene3d = new T.Scene();
  const before = scene3d.children.length;
  const state = { e: 1400, n: -3300, pitch: 0, flying: false, altitude: 0 };
  const teleports = [], flys = [];
  const walker = { state, get bearingDeg() { return 90; }, teleport(v) { teleports.push(v); } };
  const hud = { setFly(on) { flys.push(on); } };
  const scene = S.createBlockGrowScene({ scene3d, buildings: () => fakeBuildings, walker, hud,
    camera: { fov: 60, aspect: 390 / 780 }, registry, doorGroups: () => [doors, coach] });
  let s = scene.enter(glessner, 1886);
  assert.deepEqual(sorted(calls.at(-1)), sorted(G.heldAt(s)), 'enter holds the year');
  assert(calls.at(-1).includes('glessner_house') && !calls.at(-1).includes('keith_house_1808_prairie'));
  assert.equal(door.visible, false, "Glessner's door goes with its house");
  assert.equal(otherDoor.visible, true, 'a door on another block stays');
  assert.equal(coach.visible, false, "Glessner's coach-house doors go with it");
  const ghosts = scene3d.getObjectByName('block-grow-ghosts');
  assert(ghosts, 'ghosts drawn');
  const shownGhosts = ghosts.children.filter((g) => g.visible).map((g) => g.name.split(':')[1]);
  assert.deepEqual(sorted(shownGhosts), sorted(s.ghost), 'one ghost for each ghost');
  assert.equal(flys.at(-1), true);
  const view = teleports.at(-1);
  assert(view.altitude_m > 40 && view.pitch_deg < 0, 'the eye is raised over the block');
  assert(view.local_e > 1360, 'and stands on the street side (east) of a west-side block, never behind it');
  s = scene.setYear(1887);
  assert(!calls.at(-1).includes('glessner_house'));
  assert.equal(door.visible, true); assert.equal(coach.visible, true);
  scene.setYear(1904);
  assert.deepEqual(calls.at(-1), [], '1904 holds nothing');
  scene.setYear(1860);
  scene.leave();
  assert.deepEqual(calls.at(-1), [], 'leave lets every building go');
  assert.equal(door.visible, true); assert.equal(coach.visible, true);
  assert.equal(scene3d.children.length, before, 'no ghost is left behind');
  assert.deepEqual(teleports.at(-1), { local_e: 1400, local_n: -3300, yaw_deg: 90, altitude_m: null, pitch_deg: 0 }, 'the eye goes back');
  assert.equal(flys.at(-1), false);
  assert.equal(scene.active, false);
  passed += 1;
  console.log('PASS the scene holds the year, ghosts the ghosts, and Leave restores the town and the eye exactly');
}

test('the raised view keeps the whole block in the part of the screen the bar leaves clear', () => {
  const pts = [{ e: 1340, n: -3220 }, { e: 1390, n: -3340 }];
  for (const [side, streetEast] of [['west', true], ['east', false]]) {
    for (const [aspect, reserve] of [[1280 / 800, { right: 432 / 1280 }], [390 / 780, { bottom: 0.48 }]]) {
      const v = S.viewOver(pts, side, { fovDeg: 60, aspect, reserve });
      assert(v, `${side} ${aspect}: a view`);
      assert(v.altitude_m > 40 && v.pitch_deg < -20, `${side} ${aspect}: raised and looking down`);
      // never from behind the block: from its street side, or along the street from the south
      assert(streetEast ? v.local_e >= 1360 : v.local_e <= 1370, `${side} ${aspect}: street side`);
      const toBlock = (Math.atan2(1365 - v.local_e, -3280 - v.local_n) * 180 / Math.PI + 360) % 360;
      assert(Math.abs(((toBlock - v.yaw_deg + 540) % 360) - 180) < 45, `${side} ${aspect}: faces the block`);
    }
  }
  const phone = S.viewOver(pts, 'west', { aspect: 390 / 780, reserve: { bottom: 0.48 } });
  assert(phone.local_n < -3340, 'a tall screen looks along the block, from the south');
});

console.log(`check_block_grow: ${passed} passed`);
