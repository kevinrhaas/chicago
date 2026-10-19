#!/usr/bin/env node
// T-2732: Read frame pacing's arithmetic and its visibility rule, without a browser.
// The page drive itself is shown by tools/qa_pacing_read_t2732.mjs in the real app.
// T-2733: the readout's scene, Sharpness and drawn ratio, the longer run, and every
// scene's own poses walked against that scene's structure footprints.
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  pacingReadOffered, summarise, fell, verdict, formatReading, MOVES, MODES, READ_TIER, MIN_DRAWS,
  READ_SECONDS, LONG_SECONDS, SECONDS_OFFERED, SCENE_POSES, sceneOf, walkAt, poseFrom,
  describeSharpness, ratioRange,
} from '../renderers/web/js/pacing-read.js';
import { WALK } from '../renderers/web/js/travel-settings.js';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

const loc = (pathname, search = '') => ({ pathname, search });
const doc = (pill) => ({ getElementById: (id) => (pill && id === '__devpill' ? {} : null) });

// Offered on the dev preview (by its path or its banner) and with ?pacing=read; never on
// production without the parameter, and ?pacing=off hides it even on the preview.
assert.equal(pacingReadOffered(loc('/4d/walk/'), doc(false)), false);
assert.equal(pacingReadOffered(loc('/4d/1835/'), doc(false)), false);
assert.equal(pacingReadOffered(loc('/4d/dev/walk/'), doc(false)), true);
assert.equal(pacingReadOffered(loc('/4d/dev/1835/'), doc(false)), true);
assert.equal(pacingReadOffered(loc('/site/4d/walk/index.html'), doc(true)), true);
assert.equal(pacingReadOffered(loc('/4d/walk/', '?pacing=read'), doc(false)), true);
assert.equal(pacingReadOffered(loc('/4d/dev/walk/', '?pacing=off'), doc(true)), false);
assert.equal(pacingReadOffered(undefined, undefined), false);

// The moves and tier are the ones `measure_walk_frames.mjs --live` reads at the phone profile.
assert.deepEqual(MOVES, ['walk', 'turn', 'flight']);
assert.deepEqual(MODES, ['fixed', 'adaptive']);
assert.equal(READ_TIER, 'light');

// driveLive's arithmetic: population sd, p95 as the floor(0.95 n)-th sorted interval.
{
  // Intervals 10, 20, 30, 40: mean 25, population sd sqrt(125).
  const r = summarise([0, 10, 30, 60, 100]);
  assert.equal(r.draws, 5);
  assert.equal(r.mean, 25);
  assert.ok(Math.abs(r.sd - Math.sqrt(125)) < 1e-12);
  assert.equal(r.median, 30); // floor(0.5 * 4) = index 2
  assert.equal(r.p95, 40); // floor(0.95 * 4) = index 3
  assert.equal(r.max, 40);
  assert.equal(r.over33, 1);
  assert.equal(r.over50, 0);
}
{
  // A steady 60 Hz with one 50.1 ms hitch in twenty: the p95 is the hitch's index.
  const starts = [0];
  for (let i = 0; i < 20; i++) starts.push(starts.at(-1) + (i === 7 ? 50.1 : 16.7));
  const r = summarise(starts);
  assert.ok(Math.abs(r.p95 - 50.1) < 1e-9);
  assert.equal(r.over50, 1);
  assert.equal(r.over33, 1);
}
{
  // Nothing drawn, or one draw: zeros, never NaN.
  for (const s of [[], [5]]) {
    const r = summarise(s);
    assert.deepEqual([r.mean, r.sd, r.median, r.p95, r.max], [0, 0, 0, 0, 0]);
  }
}

// FELL needs both sd and p95 down; one alone is not a fall.
const m = (sd, p95) => ({ sd, p95 });
assert.equal(fell({ fixed: m(10, 40), adaptive: m(6, 30) }), true);
assert.equal(fell({ fixed: m(10, 40), adaptive: m(6, 45) }), false);
assert.equal(fell({ fixed: m(10, 40), adaptive: m(12, 30) }), false);
assert.equal(fell({ fixed: m(10, 40), adaptive: m(10, 40) }), false);

// Below MIN_DRAWS in either mode the pair says it cannot say, whatever its numbers.
{
  const d = (draws, sd, p95) => ({ draws, sd, p95 });
  assert.equal(verdict({ fixed: d(300, 10, 40), adaptive: d(300, 6, 30) }), 'FELL');
  assert.equal(verdict({ fixed: d(300, 10, 40), adaptive: d(300, 12, 30) }), 'DID NOT FALL');
  assert.equal(verdict({ fixed: d(MIN_DRAWS - 1, 10, 40), adaptive: d(300, 6, 30) }), 'TOO FEW FRAMES TO SAY');
  assert.equal(verdict({ fixed: d(300, 10, 40), adaptive: d(2, 0, 0) }), 'TOO FEW FRAMES TO SAY');
}

// The copied text names the device and carries a row per move and mode plus its verdict.
{
  const row = (sd, p95) => ({ draws: 300, mean: 16.8, sd, median: 16.7, p95, max: 70, over33: 3, over50: 1 });
  const pairs = Object.fromEntries(MOVES.map((mv) => [mv, { fixed: row(9, 33), adaptive: row(4, 17) }]));
  pairs.turn.adaptive = row(11, 20);
  pairs.flight.fixed = { ...row(9, 33), draws: 3 };
  pairs.walk.adaptive = { ...row(4, 17), ratio: { min: 0.67, max: 1 } };
  pairs.walk.fixed = { ...row(9, 33), ratio: { min: 1, max: 1 } };
  const text = formatReading({ when: '2026-10-17T18:00:00.000Z', tier: 'light', seconds: 5, build: 'v-test',
    scene: '1904', sharpness: { ceiling: 1, ratio: 1 },
    device: { screen: '390x844 (screen 390x844)', ratio: 3, ua: 'Mozilla/5.0 (iPhone)' }, pairs });
  // T-2733: the scene, the Sharpness stop and the ratio drawn, beside the device's ratio.
  assert.match(text, /^scene 1904, sharpness Low \(1\), drawn at 1 at rest$/m);
  assert.match(text, /^walk\s+fixed\s+300 .* 1$/m);
  assert.match(text, /^walk\s+adaptive\s+300 .* 0\.67-1$/m);
  assert.match(text, /^turn\s+fixed\s+300 .* \?$/m);
  assert.match(text, /^Read frame pacing \(T-2733\)/);
  assert.match(text, /390x844 \(screen 390x844\) at ratio 3, detail light, 5 s a mode/);
  assert.match(text, /Mozilla\/5\.0 \(iPhone\)/);
  for (const mv of MOVES) for (const md of MODES) assert.match(text, new RegExp(`^${mv}\\s+${md}\\s+(300|3) `, 'm'));
  assert.equal((text.match(/^ {2}FELL:/gm) ?? []).length, 1);
  assert.equal((text.match(/^ {2}TOO FEW FRAMES TO SAY:/gm) ?? []).length, 1);
  assert.equal((text.match(/^ {2}DID NOT FALL:/gm) ?? []).length, 1);
  assert.match(text, /DID NOT FALL: sd 9\.0 → 11\.0 ms, p95 33\.0 → 20\.0 ms/);
}

// T-2733: the Sharpness line and the drawn-ratio column.
assert.equal(describeSharpness({ ceiling: 1.5, ratio: 1.5 }), 'sharpness Medium (1.5), drawn at 1.5 at rest');
assert.equal(describeSharpness({ ceiling: 2, ratio: 2 }), 'sharpness High (2), drawn at 2 at rest');
assert.equal(describeSharpness({ ceiling: 1.25, ratio: 1.25 }), 'sharpness cap 1.25, drawn at 1.25 at rest');
assert.equal(describeSharpness(null), 'sharpness unknown');
assert.equal(ratioRange({ min: 1.5, max: 1.5 }), '1.5');
assert.equal(ratioRange({ min: 1.006, max: 1.5 }), '1.01-1.5');
assert.equal(ratioRange({ min: Infinity, max: -Infinity }), '?');
assert.equal(ratioRange(undefined), '?');

// The longer run is offered, and offered first.
assert.equal(READ_SECONDS, 5);
assert.ok(LONG_SECONDS >= 3 * READ_SECONDS);
assert.deepEqual(SECONDS_OFFERED, [LONG_SECONDS, READ_SECONDS]);
{
  const html = readFileSync(join(ROOT, 'renderers/web/index.html'), 'utf8');
  const sel = html.match(/<select id="s-pacing-seconds">([\s\S]*?)<\/select>/);
  assert.ok(sel, 'index.html carries the reading-length select');
  assert.deepEqual([...sel[1].matchAll(/value="(\d+)"/g)].map((m) => Number(m[1])), SECONDS_OFFERED);
}

// The scene the page shows: the scene record's id, else the page's year.
assert.equal(sceneOf({ scene: { id: '1904' }, year: 1835 }), '1904');
assert.equal(sceneOf({ scene: null, year: 1835 }), '1835');
assert.equal(sceneOf(undefined), '');

// A walk follows its legs and holds at the end, facing the last leg.
{
  const w = { from: [0, 0], legs: [[90, 40], [180, 60]] };
  const at = (d) => { const p = walkAt(w, d); return [p.local_e, p.local_n, p.yaw_deg].map((x) => Math.round(x * 1e6) / 1e6); };
  assert.deepEqual(at(0), [0, 0, 90]);
  assert.deepEqual(at(10), [10, 0, 90]);
  assert.deepEqual(at(50), [40, -10, 180]);
  assert.deepEqual(at(1000), [40, -60, 180]);
}

// 1835 is driveLive's walk, move for move: east 40 m from lake_at_canal, then south.
{
  const scene = JSON.parse(readFileSync(join(ROOT, 'data/scenes/1835.json'), 'utf8'));
  const anchor = (id) => scene.anchors.find((x) => x.id === id);
  const live = (t, s = anchor('lake_at_canal'), v = 1.45) => {
    const b = s.yaw_deg; const r = (d) => d * Math.PI / 180;
    const d = Math.min(40, v * t); const d2 = Math.max(0, v * t - 40);
    return [s.local_e + Math.sin(r(b)) * d + Math.sin(r(b + 90)) * d2, s.local_n + Math.cos(r(b)) * d + Math.cos(r(b + 90)) * d2];
  };
  const walk = poseFrom(SCENE_POSES[1835], 'walk', 1.45);
  for (const t of [0, 5, 20, 30, 40]) {
    const p = walk(t); const q = live(t);
    assert.ok(Math.hypot(p.local_e - q[0], p.local_n - q[1]) < 1e-6, `1835 walk at ${t} s is driveLive's`);
  }
  const turn = anchor('lake_market');
  assert.deepEqual(SCENE_POSES[1835].turn, { at: [turn.local_e, turn.local_n], yaw_deg: turn.yaw_deg });
  const above = anchor('from_above');
  assert.deepEqual(SCENE_POSES[1835].flight, { from: [above.local_e, above.local_n], yaw_deg: above.yaw_deg,
    altitude_m: above.altitude_m, pitch_deg: above.pitch_deg });
}

// EVERY SCENE HAS ITS OWN POSES, AND NONE ENTERS A STRUCTURE. The owner's 1904 attempt
// (T-2828) walked due west from the one anchor there into the Glessner front, because
// the poses knew only 1835's anchor ids. The footprints are the walker's own
// (walker.js footprintsFrom — copied here because that module imports three, which
// node does not resolve): each sidecar's polygon turned by its placement, skipping
// decks on water, records another layer draws, and camps.
const CLEARANCE_M = 1.5; // the walker's 0.34 m shoulder, and room to spare
const inside = (e, n, pts) => {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i]; const [xj, yj] = pts[j];
    if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
};
const edgeDistance = (e, n, pts) => {
  let best = Infinity;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [ax, ay] = pts[j]; const [bx, by] = pts[i];
    const dx = bx - ax; const dy = by - ay; const len2 = dx * dx + dy * dy || 1e-9;
    const t = Math.max(0, Math.min(1, ((e - ax) * dx + (n - ay) * dy) / len2));
    best = Math.min(best, Math.hypot(e - ax - dx * t, n - ay - dy * t));
  }
  return best;
};
function footprints(scene) {
  const dir = join(ROOT, 'data/sidecars', scene);
  const out = [];
  for (const f of readdirSync(dir).filter((x) => x.endsWith('.json'))) {
    const sc = JSON.parse(readFileSync(join(dir, f), 'utf8'));
    const raw = sc.footprint;
    const poly = Array.isArray(raw) ? raw : raw?.polygon;
    if (!Array.isArray(poly) || poly.length < 3) continue;
    const p = sc.placement ?? {};
    if (p.vertical_anchor === 'water' || sc.drawn_by || sc.archetype === 'camp') continue;
    const th = (p.rotation_deg ?? 0) * Math.PI / 180;
    const cos = Math.cos(th); const sin = Math.sin(th);
    const e0 = p.local_e ?? 0; const n0 = p.local_n ?? 0;
    out.push({ id: sc.id, pts: poly.map(([u, v]) => [e0 + u * cos + v * sin, n0 - u * sin + v * cos]) });
  }
  return out;
}
const scenes = readdirSync(join(ROOT, 'data/scenes')).filter((f) => /^\d+\.json$/.test(f)).map((f) => f.replace('.json', ''));
assert.ok(scenes.length >= 3);
for (const scene of scenes) {
  const poses = SCENE_POSES[scene];
  assert.ok(poses, `scene ${scene} has reading poses of its own`);
  const fps = footprints(scene);
  assert.ok(fps.length > 0, `scene ${scene} has footprints to walk against`);
  const clear = (e, n, what) => {
    for (const fp of fps) {
      assert.ok(!inside(e, n, fp.pts), `${scene} ${what} at ${e.toFixed(1)},${n.toFixed(1)} is inside ${fp.id}`);
      const d = edgeDistance(e, n, fp.pts);
      assert.ok(d >= CLEARANCE_M, `${scene} ${what} at ${e.toFixed(1)},${n.toFixed(1)} is ${d.toFixed(2)} m from ${fp.id}`);
    }
  };
  // The whole walk, every half metre, to its end — so a longer run or a faster pace
  // only ever stops at the end, inside nothing.
  const length = poses.walk.legs.reduce((t, [, len]) => t + len, 0);
  assert.ok(length >= WALK.sprintSpeed * LONG_SECONDS,
    `${scene} walk is ${length} m, short of ${LONG_SECONDS} s at a jog`);
  for (let d = 0; d <= length; d += 0.5) {
    const p = walkAt(poses.walk, d);
    clear(p.local_e, p.local_n, `walk at ${d} m`);
  }
  clear(poses.turn.at[0], poses.turn.at[1], 'turn');
  // The flight is above the roofs (a house's chimneys stand under 30 m) and looks down.
  assert.ok(poses.flight.altitude_m >= 100, `${scene} flight flies at ${poses.flight.altitude_m} m`);
  assert.ok(poses.flight.pitch_deg < 0);
  for (const move of MOVES) {
    const p = poseFrom(poses, move, 1.45)(LONG_SECONDS);
    assert.ok(Number.isFinite(p.local_e) && Number.isFinite(p.local_n) && Number.isFinite(p.yaw_deg));
  }
}

// 1904's walk is along Prairie Avenue, not across it: within a degree of the
// street's own line, and on the east walk band the whole way.
{
  const grid = JSON.parse(readFileSync(join(ROOT, 'data/street_grid/1904.json'), 'utf8'));
  const face = grid.faces.find((f) => f.id === 'prairie__prairie_calumet_18_20');
  const [[e0, n0], [e1, n1]] = face.street_line_local_m;
  const street = (Math.atan2(e1 - e0, n1 - n0) * 180 / Math.PI + 360) % 360;
  const legs = SCENE_POSES[1904].walk.legs;
  for (const [bearing] of legs) assert.ok(Math.abs(bearing - street) < 1, `1904 walk ${bearing} vs Prairie ${street.toFixed(2)}`);
  const band = face.bands.walk[0];
  for (let d = 0; d <= legs[0][1]; d += 5) {
    const p = walkAt(SCENE_POSES[1904].walk, d);
    assert.ok(inside(p.local_e, p.local_n, band), `1904 walk at ${d} m is on Prairie's east walk`);
  }
}

console.log('pacing-read: visibility, driveLive arithmetic, verdict and copied text hold (T-2732);'
  + ` the readout names scene, Sharpness and ratio, and ${scenes.length} scenes' poses keep out of every footprint (T-2733)`);
