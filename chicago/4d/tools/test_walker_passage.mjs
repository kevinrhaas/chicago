#!/usr/bin/env node
/**
 * T-2943 — a visitor walks through a building's modelled passage.
 *
 * The walker holds every footprint solid; a sidecar's `footprint.passages` carves the
 * opening the model really has (Glessner's carriage passage, Prairie Avenue to the court)
 * wherever its clear height clears the eye. Here: a box with a passage through it and the
 * same box without one, on flat ground — through, the walk passes and the side walls hold;
 * without, it stops at the façade; a rider whose eye would strike the soffit is stopped.
 * Then the real 1904 Glessner sidecar: from Prairie Avenue through the passage into the
 * court, the visitor never inside the masonry and held off both reveals.
 *
 *   node tools/test_walker_passage.mjs
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { createWalker, footprintsFrom, passageLane, WALK, HEADROOM_MARGIN_M, LANE_REACH_M } = await import('../renderers/web/js/walker.js');
const { createIntent } = await import('../renderers/web/js/controls/intent.js');
const { Heightfield, distantBaseGeometry } = await import('../renderers/web/js/terrain.js');
const { passageGroundFrom, passageDepth } = await import('../renderers/web/js/passage-ground.js');
const { structureOutlines } = await import('../renderers/web/js/navigation.js');
const { createContextFloorIndex, cityContextCard } = await import('../renderers/web/js/city-context.js');
const { createPopup } = await import('../renderers/web/js/popup.js');

// Generated context has a runtime card, not a compiled structure sidecar. Its
// scene-level liberty must reach the actual popup count, pane and Sources API.
{
  const read=path=>JSON.parse(fs.readFileSync(new URL(`../${path}`,import.meta.url),'utf8'));
  const doc=read('data/context/1871.json'),definition=read('data/context/1871/kit.json');
  const liberties=read('data/liberties.json').liberties;
  const declared=liberties.find(lib=>lib.id===doc.liberty);
  assert(declared,'the generated document declares an existing liberty');
  const building=doc.buildings[0],tree=doc.trees[0];
  const buildingInput={...building,w:building.width_m,d:building.depth_m,h:building.eave_m,
    t:definition.templates.find(t=>t.id===building.kit)};
  const records=[
    cityContextCard(buildingInput,doc,definition),
    cityContextCard({...tree,h:tree.height_m,isTree:true},doc,definition),
  ];
  assert.deepEqual(cityContextCard(buildingInput,{...doc,liberty:'L-scene-fixture'},definition).libertyIds,
    ['L-scene-fixture'],'the producer follows the scene declaration, not a hardcoded identifier');
  assert.deepEqual(cityContextCard(buildingInput,{...doc,liberty:null},definition).libertyIds,
    [],'a missing scene declaration is not invented by the producer');
  const savedDocument=globalThis.document;
  globalThis.document={documentElement:{classList:{add(){},remove(){}}}};
  const mount={innerHTML:'',addEventListener(){},setAttribute(){},removeAttribute(){},dispatchEvent(){}};
  const popup=createPopup(mount,{});
  try {
    popup.setLiberties(liberties);
    for(const record of records) {
      assert.deepEqual(record.libertyIds,[doc.liberty],'the card uses the generated document’s declared liberty');
      assert(!Object.hasOwn(record.sidecar,'liberty_ids'),'runtime metadata does not invent a compiled sidecar field');
      assert.equal(popup.show(record),true,'the real popup opens the generated context card');
      assert.match(mount.innerHTML,/Liberties taken here <span class="pop-count">1<\/span>/,'the actual pane counts its liberty');
      assert(mount.innerHTML.includes(declared.title),'the actual pane renders its declared liberty');
      assert.deepEqual(popup.sections(record).liberties.map(lib=>lib.id),[doc.liberty],'Inspect Sources receives the same liberty');
      assert.deepEqual(record.sidecar.citations,definition.citations,'the source citations remain intact');
      const missing={...record,libertyIds:[]};
      assert.deepEqual(popup.sections(missing).liberties,[],'a missing runtime binding is observable, never silently guessed');
      const wrong={...record,libertyIds:['L-unresolved-context-fixture']};
      assert.deepEqual(popup.sections(wrong).liberties,[],'an unresolved runtime binding does not invent a liberty');
    }
    const native={id:'native-liberty-fixture',sidecar:{name:'Native structure',placement:{},attributes:{}}};
    popup.setLiberties([{id:'L-native-fixture',subjects:[native.id]}]);
    assert.deepEqual(popup.sections(native).liberties.map(lib=>lib.id),['L-native-fixture'],'ordinary structure subject lookup remains unchanged');
  } finally {globalThis.document=savedDocument;}
  console.log('CITY CONTEXT CARDS PASS — building and tree declare the generated scene liberty in actual popup counts, panes and Sources; citations and native subject lookup preserved; missing bindings stay missing');
}

const flat = { walkHeight: () => 0, surfaceHeight: () => 0, isWater: () => false };
const inside = (e, n, pts) => {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j];
    if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
};

/** Walk `seconds` at 60 fps holding forward (and `strafe`), facing `yawDeg` (compass). */
function walk(footprints, from, yawDeg, seconds, { strafe = 0 } = {}) {
  const camera = new THREE.PerspectiveCamera();
  const w = createWalker({ camera, terrain: flat, footprints, spawn: { local_e: from[0], local_n: from[1], yaw_deg: yawDeg } });
  const intent = createIntent();
  const path = [];
  for (let i = 0; i < seconds * 60; i++) {
    intent.forward = 1; intent.strafe = strafe;
    w.update(1 / 60, intent);
    path.push([w.state.e, w.state.n, w.state.groundY]);
  }
  return { w, path, end: path.at(-1) };
}

const box = [[0, 0], [10, 0], [10, 10], [0, 10]];
const passage = { kind: 'carriage passage', polygon: [[0, 6], [0, 4], [10, 4], [10, 6]], open_edges: [[0, 1], [2, 3]], floor_m: 0, clear_m: 2.2 };
const reg = (fp) => new Map([['b', { id: 'b', sidecar: { id: 'b', placement: { local_e: 0, local_n: 0, rotation_deg: 0 }, footprint: fp } }]]);
const speedWas = WALK.speed, eyeWas = WALK.eyeHeight;
WALK.speed = 1.5;
try {
  // The 1871 renderer emits the road and both boardwalks above the heightfield.
  // Stepping onto a visible walk must raise the same walker's feet, not merely
  // change a reported number. No floor callback preserves the legacy surface.
  const floors=createContextFloorIndex([
    {a:[0,0],b:[20,0],width_m:6,y:3.23},
    {a:[0,4],b:[20,4],width_m:2,y:3.32},
    {a:[62,62],b:[70,70],width_m:2,y:3.32},
  ]);
  const cityGround={walkHeight:()=>3.20,surfaceHeight:()=>3.20,isWater:()=>false};
  const cityWalker=createWalker({camera:new THREE.PerspectiveCamera(),terrain:cityGround,
    spawn:{local_e:5,local_n:2.5,yaw_deg:0},decks:[{id:'higher-deck',y:3.50,pts:[[8,3],[10,3],[10,5],[8,5]]}]});
  assert.equal(cityWalker.surfaceAt(5,4),3.20,'without the callback, legacy heightfield walking is unchanged');
  cityWalker.setContextFloor((e,n)=>floors.heightAt(e,n));
  cityWalker.resettle();
  assert.equal(cityWalker.state.groundY,3.23,'feet start on the emitted road, not the lower field');
  const cityIntent=createIntent();
  for(let i=0;i<60;i++){cityIntent.forward=1;cityWalker.update(1/60,cityIntent);}
  assert.ok(cityWalker.state.n>3.9&&!cityWalker.state.blocked,'the 9cm step from road onto plank walk is traversable');
  assert.equal(cityWalker.state.groundY,3.32,'walking onto the plank ribbon raises actual feet to its rendered y');
  assert.ok(Math.abs(cityWalker.state.eyeY-(3.32+WALK.eyeHeight))<1e-8,'the eye stays one person-height above the planks');
  assert.equal(cityWalker.surfaceAt(9,4),3.50,'a higher bridge/quay deck still wins over a context walk');
  assert.equal(cityWalker.surfaceAt(5,6),3.20,'outside the finite ribbons the terrain still wins');
  assert.equal(floors.heightAt(64,64),3.32,'a diagonal ribbon remains supported across a spatial-cell boundary');
  assert.equal(floors.heightAt(21,4),null,'no capsule-shaped extension is invented past the actual ribbon end');
  assert.equal(floors.heightAt(64,66),null,'the diagonal rectangle does not fill its bounding box');
  cityWalker.setContextFloor(()=>3.1);
  assert.equal(cityWalker.surfaceAt(5,4),3.20,'a lower context surface cannot sink dry-land feet');
  cityWalker.setContextFloor(null);
  assert.equal(cityWalker.surfaceAt(5,4),3.20,'removing the optional callback restores the legacy path');
  floors.clear();
  assert.equal(floors.heightAt(5,4),null,'disposed spatial data does not retain a phantom floor');

  // Separate occupied components retain one owner and leave the open yard gap
  // walkable. The same compiler rings drive map outlines, routing and keep-outs.
  const compound = reg({ polygon: [[0, 0], [4, 0], [4, 4], [0, 4]],
    additional_polygons: [
      { id: 'connector', polygon: [[8, 0], [10, 0], [10, 4], [8, 4]] },
      { id: 'turned-range', polygon: [[10, 1], [12, 2], [11, 4], [9, 3]] },
    ] });
  const compoundFeet = footprintsFrom(compound);
  assert.equal(compoundFeet.length, 3);
  assert.deepEqual(compoundFeet.map(f => f.id), ['b', 'b', 'b']);
  const gapWalk = walk(compoundFeet, [6, -3], 0, 8);
  assert.ok(gapWalk.end[1] > 5, 'the open bay gap is not filled by a bounding polygon');
  const annexWalk = walk(compoundFeet, [8.8, -3], 0, 8);
  assert.ok(annexWalk.end[1] < 0, 'the actual connector wall blocks the walk');
  assert.deepEqual(structureOutlines(compound).map(r => [...r]), compoundFeet.map(f => f.pts));
  const turned = reg({ polygon: [[0, 0], [1, 0], [1, 1]],
    additional_polygons: [{ polygon: [[2, 1], [4, 2], [3, 4]] }] });
  turned.get('b').sidecar.placement.rotation_deg = 90;
  const turnedFeet = footprintsFrom(turned)[1].pts;
  assert.ok(Math.abs(turnedFeet[0][0] - 1) < 1e-9 && Math.abs(turnedFeet[0][1] + 2) < 1e-9,
    'compiled rotated-component coordinates receive the same clockwise placement');
  assert.deepEqual(structureOutlines(turned)[1].map(p => [...p]), turnedFeet);
  assert.throws(() => footprintsFrom(reg({ polygon: box,
    additional_polygons: [{ polygon: [[0, 0], [1, NaN], [2, 0]] }] })), /occupied polygon/);

  // ---- the lane: open ends reach past the walls; the side walls are the other edges
  const lane = passageLane(passage);
  assert.equal(lane.walls.length, 2, 'two side walls, two open ends');
  assert.deepEqual(lane.lane[0], [-LANE_REACH_M, 6]); assert.deepEqual(lane.lane[2], [10 + LANE_REACH_M, 4]);
  assert.equal(passageLane({ polygon: [[0, 0], [1, 1]] }), null, 'a malformed passage is ignored');
  assert.equal(HEADROOM_MARGIN_M, 0.1);

  // ---- without the passage: the façade stops the walk
  const solid = footprintsFrom(reg({ polygon: box }));
  assert.equal(solid[0].passages, undefined, 'a footprint with no passage is as before');
  const blocked = walk(solid, [-3, 5], 90, 8);
  assert(blocked.end[0] < -WALK.radius + 0.01, `without the passage the walk stops at the façade (${blocked.end[0].toFixed(2)})`);

  // ---- with it: through, never inside the masonry, held off the reveals
  const open = footprintsFrom(reg({ polygon: box, passages: [passage] }));
  assert.equal(open[0].passages.length, 1);
  const through = walk(open, [-3, 5], 90, 12);
  assert(through.end[0] > 12, `with the passage the walk comes out the far side (${through.end[0].toFixed(2)})`);
  for (const [e, n] of through.path) assert(!(inside(e, n, box) && (n < 4 + WALK.radius - 1e-6 || n > 6 - WALK.radius + 1e-6)), `never in the walls at ${e.toFixed(2)},${n.toFixed(2)}`);
  // Strafing into a reveal mid-passage: held WALK.radius off it.
  const scrape = walk(open, [2, 5], 90, 3, { strafe: 1 });
  for (const [e, n] of scrape.path) if (e > 0 && e < 10) assert(n >= 4 + WALK.radius - 1e-6 && n <= 6 - WALK.radius + 1e-6, `held off the reveal at ${e.toFixed(2)},${n.toFixed(3)}`);
  // Beside the mouth, outside the lane, the façade still stands.
  const beside = walk(open, [-3, 8], 90, 6);
  assert(beside.end[0] < -WALK.radius + 0.01, 'the wall beside the opening is still a wall');
  // A rider's eye (the seat raises it) that would strike the soffit is stopped at the mouth.
  WALK.eyeHeight = 1.68 + 0.75;
  const rider = walk(open, [-3, 5], 90, 8);
  assert(rider.end[0] < 0, `a rider who would strike the 2.2 m soffit stops (${rider.end[0].toFixed(2)})`);
  WALK.eyeHeight = eyeWas;

  // ---- the real thing: Glessner's sidecar, Prairie Avenue to the court, on flat ground
  const side = JSON.parse(fs.readFileSync(new URL('../data/sidecars/1904/glessner_house.json', import.meta.url)));
  const gl = footprintsFrom(new Map([[side.id, { id: side.id, sidecar: side }]]));
  assert.equal(gl[0].passages?.length, 1, 'Glessner declares its carriage passage');
  const g = gl[0].passages[0];
  assert(g.clear >= 1.68 + HEADROOM_MARGIN_M, `its ${g.clear} m clears a standing eye`);
  // The mouth's centre on Prairie, and the court end's centre, in world metres.
  const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const mouth = mid(g.pts[0], g.pts[1]), court = mid(g.pts[2], g.pts[3]);
  const bearing = (Math.atan2(court[0] - mouth[0], court[1] - mouth[1]) * 180 / Math.PI + 360) % 360;
  const start = [mouth[0] + (mouth[0] - court[0]) * 0.4, mouth[1] + (mouth[1] - court[1]) * 0.4];
  const run = walk(gl, start, bearing, 14);
  const past = (court[0] - mouth[0]) * (run.end[0] - court[0]) + (court[1] - mouth[1]) * (run.end[1] - court[1]);
  assert(past > 0, `from Prairie Avenue the walk comes out into the court (ended ${run.end.map((v) => v.toFixed(2))})`);
  for (const [e, n] of run.path) {
    if (!inside(e, n, gl[0].pts)) continue;
    assert(inside(e, n, g.pts), `inside the house only within the passage (${e.toFixed(2)},${n.toFixed(2)})`);
  }
  // T-2976: the floor sunk where the HABS sheets draw it, the passage clears a seated
  // driver (eye 1.68 + 0.5 m) and the walk steps down onto the paving, not the field.
  assert(g.clear >= 1.68 + 0.5 + HEADROOM_MARGIN_M, `its ${g.clear} m clears a driver's eye`);
  const sunk = passageGroundFrom(new Map([[side.id, { id: side.id, sidecar: side }]]));
  // T-2978: and the court ground's fall to the mouth, four quads (bank and low ground,
  // each out to the section plane and on to where it rises back to the court's level).
  assert.equal(sunk.length, 8, 'approach, threshold, passage floor, court ramp and the court fall are declared');
  const atMouth = passageDepth(sunk, mouth[0] + (mouth[0] - court[0]) * 0.005, mouth[1] + (mouth[1] - court[1]) * 0.005);
  assert(Math.abs(atMouth - -0.3536) < 0.01, `the mouth's paving is 1.16 ft under the sidewalk (${atMouth})`);
  const atCourt = passageDepth(sunk, court[0] - (mouth[0] - court[0]) * 0.001, court[1] - (mouth[1] - court[1]) * 0.001);
  assert(Math.abs(atCourt - -0.6858) < 0.01, `the court mouth's paving is 2.45 ft under the court face's zero, 9.65 ft under its lintel (${atCourt})`);
  assert.equal(passageDepth(sunk, mouth[0] + 50, mouth[1]), null, 'off the carriage way the field is the ground');
  const sunkTerrain = { ...flat, walkHeight: (e, n) => passageDepth(sunk, e, n) ?? 0 };
  {
    const camera = new THREE.PerspectiveCamera();
    const w = createWalker({ camera, terrain: sunkTerrain, footprints: gl, spawn: { local_e: start[0], local_n: start[1], yaw_deg: bearing } });
    const intent = createIntent();
    let lowest = Infinity;
    for (let i = 0; i < 14 * 60; i++) { intent.forward = 1; w.update(1 / 60, intent); lowest = Math.min(lowest, w.state.groundY); }
    const past = (court[0] - mouth[0]) * (w.state.e - court[0]) + (court[1] - mouth[1]) * (w.state.n - court[1]);
    assert(past > 0, 'down the approach, through the sunk passage and up the ramp into the court');
    assert(lowest < -0.3, `the walk went down onto the sunk floor (lowest ${lowest.toFixed(3)} m)`);
  }
  const solidG = footprintsFrom(new Map([[side.id, { id: side.id, sidecar: { ...side, footprint: { ...side.footprint, passages: undefined } } }]]));
  const before = walk(solidG, start, bearing, 14);
  const gone = (court[0] - mouth[0]) * (before.end[0] - mouth[0]) + (court[1] - mouth[1]) * (before.end[1] - mouth[1]);
  assert(gone < 0, 'without the passage the same walk stops on Prairie Avenue, as the owner found it');
  // The distant city base retains a river narrower than the legacy six-sample stride.
  {
    const hf = new Heightfield();
    const samples = new Float32Array(9 * 9).fill(3.2);
    for (let row = 0; row < 9; row++) samples[row * 9 + 3] = -3;
    hf.adopt({ epoch: 'e1871_prefire', cols: 9, rows: 9, cell_m: 25, origin_e: 0, origin_n: 0 }, samples.buffer);
    const base = distantBaseGeometry(hf);
    const p = base.getAttribute('position'), grade = base.getAttribute('_confidence');
    let channel = 0;
    for (let i = 0; i < p.count; i++) {
      if (p.getY(i) < 0) channel++;
      assert.equal(grade.getX(i), 1, 'city ground stays reconstructed at distance');
    }
    assert.equal(channel, 9, 'all narrow river samples survive in the aerial base');
    base.dispose();
  }
  // The municipal overview stays at its authored altitude on the next frame.
  {
    const w = createWalker({ camera: new THREE.PerspectiveCamera(), terrain: flat, maxFlyAltitude: 4500 });
    w.teleport({ local_e: 0, local_n: 0, altitude_m: 2200, pitch_deg: -26 });
    w.update(1 / 60, { ...createIntent(), flying: true });
    assert.equal(w.state.eyeY, 2200, 'city overview does not snap to the small-scene ceiling');
  }
  // City context uses the same capsule/slide rules, with a nearby-only provider.
  {
    const w = createWalker({ camera: new THREE.PerspectiveCamera(), terrain: flat,
      spawn: { local_e: 5, local_n: -3, yaw_deg: 0 } });
    const intent = createIntent();
    let queried = 0;
    w.setContextFootprints((e, n) => {
      queried++;
      assert(Number.isFinite(e) && Number.isFinite(n), 'spatial query receives ENU metres');
      return [{ id: 'context-house', pts: box }];
    });
    for (let i = 0; i < 8 * 60; i++) { intent.forward = 1; w.update(1 / 60, intent); }
    assert(queried > 0 && w.state.n < 0, 'nearby context wall stops the visitor');
    w.setContextFootprints(null);
    for (let i = 0; i < 4 * 60; i++) w.update(1 / 60, intent);
    assert(w.state.n > 1, 'retiring the provider removes its collision');
  }
} finally { WALK.speed = speedWas; WALK.eyeHeight = eyeWas; }
console.log('WALKER PASSAGE PASS — a declared passage is walked through where its soffit clears the eye, held off its reveals, the façade beside it still a wall, a rider stopped; Glessner from Prairie Avenue into the court, which a solid footprint refuses');
