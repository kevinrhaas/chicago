#!/usr/bin/env node
/**
 * THE IMAGE GATE (T-2368). A building that has a photograph or a drawing of it is built
 * until its render, from that picture's own camera, matches the picture — and the ticket
 * that builds it is not closed before then.
 *
 * WHY. The owner, 2026-10-11, on 1612 Prairie: it "bears little resemblance to the photo in
 * the research repo"; "if you have any views of the house those should be validated against
 * in development"; "you should work towards it until it's a photographic representation of
 * any images, even drawings are ok, but it should look exactly perfectly like the image or
 * drawing"; and, on the gate's shape, "you don't wrap the case until it matches the photo,
 * not that you can't change one without a photo". The draft and the refine of 1612 had both
 * been built from the Sanborn and a one-line summary while the library linked the photograph.
 *
 * SO THE GATE IS ON CLOSING, NOT ON CHANGING. Nothing here refuses an edit. `check.sh` runs
 * `--check`, which fails only a malformed view or match file and otherwise prints where every
 * gated building stands. `ticket.mjs done` refuses a ticket whose body carries an
 * `## Image gate` section until every building it names has, for every reference view:
 *   - a match record (`<view>.match.json`, written by tools/photo_match.mjs) made from the
 *     GLB that is in the tree NOW (a rebuild after the match makes it stale), and
 *   - `verdict: "matches"` with no difference left `open`.
 *
 * A GOOD-ENOUGH BAR (owner, 2026-10-25, T-3153). A difference is `open` only if a visitor
 * on the street would notice it: more than about 1 ft (0.3 m) off in size or place, an
 * element missing or the wrong shape, the wrong number of bays, openings or stacks, or the
 * wrong material or colour. Anything smaller, a pixel offset, or a gap two pictures or two
 * camera fits disagree about is `within tolerance`, which never blocks `matches`. Without
 * it every closer look found a smaller gap and filed it: Glessner took 115 tickets after
 * the gate opened, fixed 110 differences, and re-filed its own sign-off five times.
 *
 * AN OWNER RULING (T-3236). A difference the owner asked for, looking at the building against
 * its picture, is `owner ruling`: the build departs from the picture on purpose, and the
 * difference says what the picture shows, what was built and the ticket that ruled it. It never
 * blocks `matches`. 1812 Prairie's entrance bay is the first: both photographs set its windows
 * and porch arch about 0.3 m south of the bay's middle and cut the arch into the projection's
 * corner; the owner, 2026-10-28, asked for them centred on the bay with the arch on its face.
 *
 *   data/reference_views/<structure_id>/<view>.json        the camera (photo_match.mjs's header)
 *   data/reference_views/<structure_id>/<view>.match.json  the match record (photo_match writes it;
 *                                                         the builder sets verdict + differences)
 *
 *   node tools/image_gate.mjs --check                 every view and match record, one line each
 *   node tools/image_gate.mjs --structure <id> [...]  exit 1 unless every view of each matches
 *   node tools/image_gate.mjs --ticket <file.md>      the same, for the ids in its ## Image gate
 *   node tools/image_gate.mjs --test             the section parser and the refusals, on fixtures (unit tests; nothing fires on purpose)
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import os from 'node:os';
import {renderGroup, groupReview} from './photo_match_group.mjs';
import {enclosureReview} from './photo_match_enclosures.mjs';
import {floraReview} from './photo_match_flora.mjs';
import {testRenderGroups} from './test_photo_match_group.mjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
export let VIEWS_DIR = path.join(ROOT, 'data/reference_views');   // the self-test points it at a temp copy
const CAMERA_KEYS = ['structure_id', 'photo', 'image_px', 'principal_px', 'focal_px', 'eye', 'yaw_deg', 'solve'];
const VERDICTS = ['unreviewed', 'differs', 'matches'];
const DIFF_STATUS = ['open', 'fixed', 'not shown', 'within tolerance', 'owner ruling'];

const sha = (f) => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');

/** The GLB a structure is built as: its one manifest entry that is not a coach house. */
export function glbFor(structureId) {
  const m = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/manifest.json'), 'utf8'));
  const hits = Object.entries(m.assets || m).filter(([, v]) => v && v.structure_id === structureId);
  if (!hits.length) return null;
  return path.join('assets/gltf', hits[0][0]);
}

/** Every reference view committed for a structure: [{view, camera, cameraFile, matchFile}]. */
export function viewsOf(structureId) {
  const dir = path.join(VIEWS_DIR, structureId);
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((f) => f.endsWith('.json') && !f.endsWith('.match.json')).sort()
    .map((f) => {
      const cameraFile = path.join(dir, f);
      return { view: f.replace(/\.json$/, ''), cameraFile, matchFile: cameraFile.replace(/\.json$/, '.match.json') };
    });
}

/** Problems that make a view or its match record unreadable (these fail --check). */
function malformed(structureId, v) {
  const out = [];
  let cam;
  try { cam = JSON.parse(fs.readFileSync(v.cameraFile, 'utf8')); } catch (e) { return [`${rel(v.cameraFile)}: not JSON (${e.message})`]; }
  for (const k of CAMERA_KEYS) if (cam[k] === undefined) out.push(`${rel(v.cameraFile)}: no "${k}"`);
  if (cam.structure_id && cam.structure_id !== structureId) out.push(`${rel(v.cameraFile)}: structure_id ${cam.structure_id} is not its folder's ${structureId}`);
  if (cam.photo && !fs.existsSync(path.resolve(path.dirname(v.cameraFile), cam.photo))) out.push(`${rel(v.cameraFile)}: photo ${cam.photo} is not in the tree`);
  if (!cam.source_id && !cam.library_image) out.push(`${rel(v.cameraFile)}: names neither a source_id nor a library_image — whose picture is it?`);
  if (cam.source_id && !fs.existsSync(path.join(ROOT, 'data/sources', cam.source_id + '.json'))) out.push(`${rel(v.cameraFile)}: source_id ${cam.source_id} does not resolve in data/sources/`);
  if (cam.also_render !== undefined) {
    try { renderGroup(ROOT, cam); } catch (e) { out.push(`${rel(v.cameraFile)}: ${e.message}`); }
  }
  if (cam.enclosures !== undefined) {
    try { enclosureReview(ROOT, cam); } catch (e) { out.push(`${rel(v.cameraFile)}: ${e.message}`); }
  }
  if (cam.flora !== undefined) {
    try { floraReview(ROOT, cam); } catch (e) { out.push(`${rel(v.cameraFile)}: ${e.message}`); }
  }
  if (fs.existsSync(v.matchFile)) {
    let m;
    try { m = JSON.parse(fs.readFileSync(v.matchFile, 'utf8')); } catch (e) { return [...out, `${rel(v.matchFile)}: not JSON (${e.message})`]; }
    if (!VERDICTS.includes(m.verdict)) out.push(`${rel(v.matchFile)}: verdict "${m.verdict}" is not one of ${VERDICTS.join(' | ')}`);
    if (!Array.isArray(m.differences)) out.push(`${rel(v.matchFile)}: differences is not a list`);
    else for (const [i, d] of m.differences.entries()) {
      if (!d || !d.what || !DIFF_STATUS.includes(d.status)) out.push(`${rel(v.matchFile)}: differences[${i}] needs "what" and a status of ${DIFF_STATUS.join(' | ')}`);
    }
    if (m.verdict === 'matches' && Array.isArray(m.differences) && m.differences.some((d) => d && d.status === 'open')) out.push(`${rel(v.matchFile)}: says "matches" with a difference still open`);
  }
  return out;
}

/** Why one view does not (yet) close its building, or null when it does. */
function blocker(structureId, v) {
  if (!fs.existsSync(v.matchFile)) return `${v.view}: never matched — run node tools/photo_match.mjs ${rel(v.cameraFile)}`;
  const m = JSON.parse(fs.readFileSync(v.matchFile, 'utf8'));
  const camera = JSON.parse(fs.readFileSync(v.cameraFile, 'utf8'));
  const members = camera.also_render?.length ? renderGroup(ROOT, camera) : null;
  const glb = members ? members[0].glb : glbFor(structureId);
  if (!glb || !fs.existsSync(path.join(ROOT, glb))) return `${v.view}: ${structureId} has no GLB in assets/manifest.json`;
  if (m.glb_sha256 !== sha(path.join(ROOT, glb))) return `${v.view}: the GLB changed after the match — rerun node tools/photo_match.mjs ${rel(v.cameraFile)} and look again`;
  if (m.camera_sha256 !== sha(v.cameraFile)) return `${v.view}: the camera changed after the match — rerun photo_match`;
  if (members && m.group_sha256 !== groupReview(ROOT, members).group_sha256)
    return `${v.view}: a rendered group member or its scene placement changed after the match — rerun photo_match`;
  const enclosures = enclosureReview(ROOT, camera);
  if (enclosures && m.enclosures_sha256 !== enclosures.review.enclosures_sha256)
    return `${v.view}: a rendered enclosure, native renderer or its anchor placement changed after the match — rerun photo_match`;
  const flora = floraReview(ROOT, camera);
  if (flora && m.flora_sha256 !== flora.review.flora_sha256)
    return `${v.view}: a rendered plant, its renderer or its anchor placement changed after the match — rerun photo_match`;
  if ((members || m.photo_sha256) && m.photo_sha256 !== sha(path.resolve(path.dirname(v.cameraFile), camera.photo)))
    return `${v.view}: the reference picture changed after the match — rerun photo_match`;
  const open = (m.differences || []).filter((d) => d.status === 'open');
  if (m.verdict !== 'matches') return `${v.view}: verdict "${m.verdict}"${open.length ? `, ${open.length} difference(s) open: ${open.map((d) => d.what).join('; ')}` : ''}`;
  return null;
}

const rel = (f) => path.relative(ROOT, f);

/** Every reason the named structures cannot close; [] when they all match. */
export function gateFor(structureIds) {
  const out = [];
  for (const id of structureIds) {
    const views = viewsOf(id);
    if (!views.length) { out.push(`${id}: no reference view — solve a camera for each picture of it into data/reference_views/${id}/ (data/reference_views/README.md)`); continue; }
    for (const v of views) {
      const bad = malformed(id, v);
      if (bad.length) { out.push(...bad.map((b) => `${id}: ${b}`)); continue; }
      const b = blocker(id, v);
      if (b) out.push(`${id}: ${b}`);
    }
  }
  return out;
}

/** The structure ids a ticket's `## Image gate` section names (bullets of ids, backticks optional). */
export function gatedStructures(body) {
  const m = /^## Image gate[^\n]*\n([\s\S]*?)(?=^## |(?![\s\S]))/m.exec(body || '');
  if (!m) return [];
  const ids = [];
  for (const line of m[1].split('\n')) {
    const b = /^\s*[-*]\s+`?([a-z0-9_]+)`?/.exec(line);
    if (b) ids.push(b[1]);
  }
  return ids;
}

function selfTest() {
  testRenderGroups();
  let fails = 0;
  const ok = (c, what) => { console.log(`${c ? 'ok  ' : 'FAIL'} image gate self-test: ${what}`); if (!c) fails++; };
  const body = 'Text.\n\n## Image gate\n- `goodman_house_1612_prairie`\n* house_1608_prairie — its 1886 plate\n\n## Later\n- not_this_one\n';
  const ids = gatedStructures(body);
  ok(ids.join() === 'goodman_house_1612_prairie,house_1608_prairie', 'reads the bullets of ## Image gate and stops at the next heading');
  ok(gatedStructures('## Image gate (owner, 2026-10-11)\n- a_b\n').join() === 'a_b', 'a heading with a note, at the end of the body');
  ok(gatedStructures('No section.\n- x\n').length === 0, 'no section, nothing gated');
  const none = gateFor(['no_such_structure_t2367']);
  ok(none.length === 1 && /no reference view/.test(none[0]), 'a gated building with no reference view does not close');
  // a fixture view: a match record made from another GLB is stale, and a differs verdict blocks
  // in a temp folder: check.sh runs --check beside this in its pool, and must never see it
  const id = '__image_gate_selftest__', real = VIEWS_DIR;
  VIEWS_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'image-gate-'));
  const dir = path.join(VIEWS_DIR, id);
  fs.mkdirSync(dir, { recursive: true });
  try {
    fs.writeFileSync(path.join(dir, 'front.json'), JSON.stringify({ structure_id: id, source_id: 'no_such_source', photo: 'missing.jpg', image_px: [1, 1], principal_px: [0, 0], focal_px: 1, eye: [0, 0, 0], yaw_deg: 0, solve: 'fixture' }));
    const bad = gateFor([id]);
    ok(bad.some((b) => /photo missing\.jpg is not in the tree/.test(b)) && bad.some((b) => /does not resolve/.test(b)), 'a camera whose photo or source is missing is malformed');
    fs.writeFileSync(path.join(dir, 'p.jpg'), 'x');
    fs.writeFileSync(path.join(dir, 'front.json'), JSON.stringify({ structure_id: id, library_image: 'fixture', photo: 'p.jpg', image_px: [1, 1], principal_px: [0, 0], focal_px: 1, eye: [0, 0, 0], yaw_deg: 0, solve: 'fixture' }));
    ok(gateFor([id]).some((b) => /never matched/.test(b)), 'a view with no match record does not close');
    fs.writeFileSync(path.join(dir, 'front.match.json'), JSON.stringify({ verdict: 'matches', differences: [{ what: 'cornice', status: 'open' }] }));
    ok(gateFor([id]).some((b) => /"matches" with a difference still open/.test(b)), 'matches with an open difference is malformed');
    fs.writeFileSync(path.join(dir, 'front.match.json'), JSON.stringify({ verdict: 'matches', differences: [{ what: 'cornice 0.2 ft low', status: 'within tolerance' }] }));
    ok(!gateFor([id]).some((b) => /needs "what" and a status|still open/.test(b)), 'a difference within tolerance is well formed and does not hold "matches" open (T-3153)');
    fs.writeFileSync(path.join(dir, 'front.match.json'), JSON.stringify({ verdict: 'matches', differences: [{ what: 'cornice', status: 'close enough' }] }));
    ok(gateFor([id]).some((b) => /needs "what" and a status/.test(b)), 'a status outside the five is still malformed');
    fs.writeFileSync(path.join(dir, 'front.match.json'), JSON.stringify({ verdict: 'matches', differences: [{ what: 'door centred where the picture has it off', status: 'owner ruling' }] }));
    ok(!gateFor([id]).some((b) => /needs "what" and a status|still open/.test(b)), 'an owner ruling is well formed and does not hold "matches" open (T-3236)');
    // Exercise the actual closing gate, not only the fingerprint helper. The
    // camera and match live in the temporary view tree; real scene assets are read.
    const anchor = 'first_fort_dearborn_blockhouse_nw';
    const groupDir = path.join(VIEWS_DIR, anchor);
    fs.mkdirSync(groupDir);
    fs.writeFileSync(path.join(groupDir, 'p.jpg'), 'fixture picture');
    const camera = {structure_id: anchor, library_image: 'fixture', scene: '1812',
      also_render: ['first_fort_dearborn_blockhouse_se'], photo: 'p.jpg',
      image_px: [1, 1], principal_px: [0, 0], focal_px: 1, eye: [0, 0, 0], yaw_deg: 0, solve: 'fixture'};
    const cameraFile = path.join(groupDir, 'group.json'), matchFile = path.join(groupDir, 'group.match.json');
    fs.writeFileSync(cameraFile, JSON.stringify(camera));
    const members = renderGroup(ROOT, camera);
    const match = {verdict: 'matches', differences: [], glb_sha256: sha(path.join(ROOT, members[0].glb)),
      camera_sha256: sha(cameraFile), photo_sha256: sha(path.join(groupDir, 'p.jpg')),
      ...groupReview(ROOT, members)};
    fs.writeFileSync(matchFile, JSON.stringify(match));
    ok(gateFor([anchor]).length === 0, 'a current group review can close');
    fs.writeFileSync(matchFile, JSON.stringify({...match, group_sha256: 'old group'}));
    ok(gateFor([anchor]).some(b => /group member or its scene placement changed/.test(b)),
      'a stale group refuses closure even with a current anchor GLB and camera');
    fs.writeFileSync(matchFile, JSON.stringify(match));
    fs.writeFileSync(path.join(groupDir, 'p.jpg'), 'different fixture picture');
    ok(gateFor([anchor]).some(b => /reference picture changed/.test(b)), 'a changed picture refuses closure');
    // A native procedural fence is part of the image just as a second GLB is.
    const jail = 'log_jail', jailDir = path.join(VIEWS_DIR, jail);
    fs.mkdirSync(jailDir);
    fs.writeFileSync(path.join(jailDir, 'p.jpg'), 'fixture jail picture');
    const fenceCamera = {...camera, structure_id: jail, scene: '1835', also_render: [],
      enclosures: ['log_jail_palisade']};
    const fenceCameraFile = path.join(jailDir, 'fence.json');
    const fenceMatchFile = path.join(jailDir, 'fence.match.json');
    fs.writeFileSync(fenceCameraFile, JSON.stringify(fenceCamera));
    const fenceMatch = {verdict: 'matches', differences: [], glb_sha256: sha(path.join(ROOT, glbFor(jail))),
      camera_sha256: sha(fenceCameraFile), photo_sha256: sha(path.join(jailDir, 'p.jpg')),
      ...enclosureReview(ROOT, fenceCamera).review};
    fs.writeFileSync(fenceMatchFile, JSON.stringify(fenceMatch));
    ok(gateFor([jail]).length === 0, 'a current native enclosure review can close');
    fs.writeFileSync(fenceMatchFile, JSON.stringify({...fenceMatch, enclosures_sha256: 'old fence'}));
    ok(gateFor([jail]).some(b => /rendered enclosure, native renderer or its anchor placement changed/.test(b)),
      'the actual closing gate refuses a stale native fence signature');
  } finally { fs.rmSync(VIEWS_DIR, { recursive: true, force: true }); VIEWS_DIR = real; }
  return fails ? 1 : 0;
}

function main(argv) {
  if (argv[0] === '--test') return selfTest();
  if (argv[0] === '--check') {
    const ids = fs.existsSync(VIEWS_DIR) ? fs.readdirSync(VIEWS_DIR, { withFileTypes: true }).filter((e) => e.isDirectory()).map((e) => e.name).sort() : [];
    let bad = 0, closing = 0, views = 0;
    for (const id of ids) {
      for (const v of viewsOf(id)) {
        views++;
        const mal = malformed(id, v);
        if (mal.length) { bad += mal.length; for (const x of mal) console.log(`FAIL image gate: ${x}`); continue; }
        const b = blocker(id, v);
        if (b) console.log(`   image gate: ${id} ${b}`);
        else { closing++; console.log(`   image gate: ${id} ${v.view}: matches`); }
      }
    }
    console.log(`image gate: ${views} reference view(s) on ${ids.length} building(s), ${closing} matching; ${bad ? bad + ' malformed' : 'none malformed'}`);
    return bad ? 1 : 0;
  }
  let ids = [];
  if (argv[0] === '--structure') ids = argv.slice(1);
  else if (argv[0] === '--ticket') ids = gatedStructures(fs.readFileSync(argv[1], 'utf8'));
  else { console.error('usage: node tools/image_gate.mjs --check | --structure <id>... | --ticket <file.md>'); return 2; }
  const why = gateFor(ids);
  for (const w of why) console.log(w);
  if (!why.length) console.log(ids.length ? `image gate: ${ids.join(', ')} match every reference view` : 'image gate: nothing gated');
  return why.length ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) process.exit(main(process.argv.slice(2)));
