// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * traffic-cards.js — horse-drawn traffic on the distant streets, as cards (T-3555).
 *
 * The owner, 2026-11-10: horses, carriages and wagons are core and are never dropped; and
 * 2026-11-12, consolidating T-2796 ("move horse-drawn traffic through distant streets") into
 * T-3555. A team is built whole (vehicle, two horses, harness, driver: town-transport.js) only
 * within its tier's reach of the eye (90 / 60 / 45 m), and the 1835 streets' streamed teams
 * only the nearest few at a time; past that it was nothing, so a street seen from a block
 * away had no traffic on it. Town transport keeps every team going about its round all the
 * same (its ghosts and its unbuilt circuits: `distant()`, which gives each team's place,
 * heading and whether it is moving, stopping where it stops for a crossing or a team in the
 * way); this layer draws each of them as a card from one atlas, baked here from the same
 * vehicle and horse files the built team is made of (TEAM_YAWS headings, lit flat), so the
 * card is that team's own picture, never a stand-in.
 *
 * Cost: one atlas row per kind of team in the scene (TEAM_CELL[tier] pixels a heading), one
 * draw for every card, CAP[tier] of them at most, nearest first, out to FAR_M[tier].
 * The vehicle and horse files are leased while a row is baked and let go after (the horse's
 * lease is shared with the built teams: draft-horse-assets.js).
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { cardMaterial } from './crowd.js';
import { acquireDraftHorse } from './draft-horse-assets.js';
import { disposeLoadedAsset } from './scene-loader.js';
import { offHours } from './town-transport.js';

/** Headings a team's card is baked from (a long thing reads its heading more than a person). */
export const TEAM_YAWS = 16;
/** A heading's picture, pixels (2:1, the card's own aspect). */
export const TEAM_CELL = Object.freeze({ full: Object.freeze([128, 64]), balanced: Object.freeze([128, 64]), light: Object.freeze([96, 48]) });
/** How far the cards reach, metres, and how many are drawn at most. */
export const FAR_M = Object.freeze({ full: 700, balanced: 500, light: 350 });
export const CAP = Object.freeze({ full: 32, balanced: 20, light: 12 });
/** Seconds a card takes to come in (a team out of its built reach is a card at once). */
export const IN_S = 0.4;

/**
 * The scene's teams out of their built reach: town transport's `distant(eye)` where it gives one
 * (its unbuilt teams, the 1835 streets' streamed ones), and its loaded teams that go on about
 * their round beyond the reach that draws them (town-transport.js: "a loaded journey keeps
 * approaching the visitor offscreen") — not drawn, not put up for the night, on their own
 * round. One entry a team, in the same shape either way.
 */
export function distantTeams(transport, eye, { hour = null, rows = new Map() } = {}) {
  if (!transport) return [];
  const given = typeof transport.distant === 'function' ? transport.distant(eye) ?? [] : [];
  const out = [...given];
  const listed = new Set(given.map((d) => d.id));
  for (const a of transport.actors ?? []) {
    if (a.disposed || a.visible || a.mode !== 'route' || !a.pose || listed.has(a.id)) continue;
    if (offHours(rows.get(a.id)?.hours, hour)) continue;
    out.push({ id: a.id, e: a.pose.e, n: a.pose.n, heading_deg: a.heading_deg, moving: a.state === 'moving' });
  }
  return out;
}

/** The row's kind of team: one atlas row each (vehicle file, horse model, light or not). */
export function teamKind(row, coarse = false) {
  const vehicle = (coarse && row.vehicle_file_light) || row.vehicle_file;
  return vehicle ? `${vehicle}|${row.horse_model ?? ''}` : null;
}

/**
 * THE LAYER. `transport()` returns the scene's town transport (or null before it mounts); its
 * `distant(cameraPosition)` is read every frame. `config` is transport/driven/loops.json.
 */
export function createTrafficCards({ renderer, transport, config, sceneId, tier = 'full', coarse = false,
  heightAt = () => 0, moduleBase = new URL('../', import.meta.url), problems = [] } = {}) {
  const group = new THREE.Group();
  group.name = 'traffic-cards';
  const rows = new Map((config?.rows ?? []).filter((r) => String(r.scene) === String(sceneId)).map((r) => [r.id, r]));
  const kinds = new Map();          // kind -> { row (atlas), status, size: [w, h], centre: [x, z] }
  for (const r of rows.values()) { const k = teamKind(r, coarse); if (k && !kinds.has(k)) kinds.set(k, { row: kinds.size, status: 'new', sample: r }); }
  const stats = { cards: 0, distant: 0, baked: 0, ms: 0 };
  let atlas = null, mesh = null, attrs = null, cell = null, shown = true, disposed = false;
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const url = (file) => new URL(file, moduleBase).href;
  const seen = new Map();           // id -> { v }
  let wroteFor = '';

  function ensure() {
    const want = TEAM_CELL[tier] ?? TEAM_CELL.full;
    if (atlas && cell === want) return true;
    if (!renderer || !kinds.size) return false;
    drop();
    cell = want;
    atlas = new THREE.WebGLRenderTarget(TEAM_YAWS * want[0], kinds.size * want[1], {
      type: THREE.UnsignedByteType, generateMipmaps: true, minFilter: THREE.LinearMipmapLinearFilter, magFilter: THREE.LinearFilter,
    });
    atlas.texture.colorSpace = THREE.SRGBColorSpace;
    atlas.texture.name = 'traffic_atlas';
    const cap = CAP[tier] ?? CAP.full;
    const quad = new THREE.PlaneGeometry(1, 0.5).translate(0, 0.25, 0);
    const geometry = new THREE.InstancedBufferGeometry();
    geometry.index = quad.index;
    for (const k of ['position', 'normal', 'uv']) geometry.setAttribute(k, quad.attributes[k]);
    attrs = { pos: new THREE.InstancedBufferAttribute(new Float32Array(cap * 4), 4), cell: new THREE.InstancedBufferAttribute(new Float32Array(cap * 4), 4), cap };
    attrs.pos.setUsage(THREE.DynamicDrawUsage); attrs.cell.setUsage(THREE.DynamicDrawUsage);
    geometry.setAttribute('iPos', attrs.pos);
    geometry.setAttribute('iCell', attrs.cell);
    geometry.instanceCount = 0;
    mesh = new THREE.Mesh(geometry, cardMaterial(atlas.texture, TEAM_YAWS, kinds.size, TEAM_YAWS));
    mesh.name = 'traffic_cards';
    mesh.frustumCulled = false;
    group.add(mesh);
    for (const k of kinds.values()) if (k.status === 'ready') k.status = 'new';
    return true;
  }
  function drop() {
    if (mesh) { group.remove(mesh); mesh.geometry.dispose(); mesh.material.dispose(); mesh = null; }
    atlas?.dispose(); atlas = null; attrs = null;
  }

  /** Load a kind's vehicle and horse, stand the team as it is built, bake its headings. */
  async function bakeKind(kind) {
    const k = kinds.get(kind);
    k.status = 'loading';
    const r = k.sample;
    const spec = config?.horse_models?.[r.horse_model] ?? null;
    let vehicle = null, lease = null;
    try {
      vehicle = await loader.loadAsync(url((coarse && r.vehicle_file_light) || r.vehicle_file));
      if (spec?.file && spec.sha256) {
        lease = await acquireDraftHorse({ url: url(spec.file), sha256: spec.sha256,
          materialVariant: spec.material_variant ?? 'source_native', loader });
      }
      if (disposed || !atlas) return;
      const team = new THREE.Group();
      team.add(vehicle.scene);
      if (lease?.asset && Array.isArray(r.horse_offset_m)) {
        for (const side of [-1, 1]) {
          const horse = cloneSkinned(lease.asset.scene);
          horse.position.set(r.horse_offset_m[0] + side * (r.team_half_spacing_m ?? 0.65), r.horse_offset_m[1], r.horse_offset_m[2]);
          team.add(horse);
        }
      }
      team.updateMatrixWorld(true);
      const box = new THREE.Box3().setFromObject(team);
      const size = box.getSize(new THREE.Vector3()), centre = box.getCenter(new THREE.Vector3());
      // The card is twice as wide as high; wide enough for the team seen end on or broadside.
      const w = Math.max(Math.hypot(size.x, size.z), size.y * 2) + 0.3;
      k.size = w; k.centre = [centre.x, centre.z];
      const scene = new THREE.Scene();
      scene.add(team);
      // Lit flat (an ambient of pi is the albedo itself): the card is lit again where it stands.
      scene.add(new THREE.AmbientLight(0xffffff, Math.PI * 0.85));
      const key = new THREE.DirectionalLight(0xffffff, 0.6); key.position.set(0.3, 1, 0.4); scene.add(key);
      const cam = new THREE.OrthographicCamera(-w / 2, w / 2, w / 4, -w / 4, 0.1, 100);
      const prevTarget = renderer.getRenderTarget();
      const prevClear = renderer.getClearColor(new THREE.Color()), prevAlpha = renderer.getClearAlpha();
      const [cw, ch] = cell;
      renderer.setClearColor(0x000000, 0);
      for (let i = 0; i < TEAM_YAWS; i++) {
        const a = (i * Math.PI * 2) / TEAM_YAWS;
        cam.position.set(centre.x + Math.sin(a) * 40, w / 4, centre.z + Math.cos(a) * 40);
        cam.lookAt(centre.x, w / 4, centre.z);
        cam.updateMatrixWorld();
        atlas.viewport.set(i * cw, k.row * ch, cw, ch);
        atlas.scissor.set(i * cw, k.row * ch, cw, ch);
        atlas.scissorTest = true;
        renderer.setRenderTarget(atlas);
        renderer.render(scene, cam);
      }
      atlas.scissorTest = false;
      atlas.viewport.set(0, 0, atlas.width, atlas.height);
      atlas.scissor.set(0, 0, atlas.width, atlas.height);
      renderer.setRenderTarget(prevTarget);
      renderer.setClearColor(prevClear, prevAlpha);
      team.traverse((o) => { if (o.isSkinnedMesh) o.skeleton.dispose(); });
      k.status = 'ready';
      stats.baked++;
    } catch (err) {
      k.status = 'failed';
      problems.push(`traffic cards: ${kind} could not be baked (${err?.message ?? err})`);
    } finally {
      if (vehicle) disposeLoadedAsset(vehicle);
      lease?.release();
    }
  }

  const eye = new THREE.Vector3();
  return {
    group,
    stats,
    get shown() { return shown; },
    setShown(on) { shown = on !== false; group.visible = shown; return shown; },
    setTier(next) { if (!CAP[next] || next === tier) return false; tier = next; drop(); return true; },
    census() { return { ...stats, kinds: kinds.size, status: [...kinds.values()].map((k) => k.status), atlas: atlas ? [atlas.width, atlas.height] : null,
      bytes: atlas ? Math.round(atlas.width * atlas.height * 4 * 4 / 3) : 0, tier }; },
    update(dt, camera, { hidden = false, hour = null } = {}) {
      if (disposed) return;
      const t0 = performance.now();
      const t = transport?.();
      group.visible = shown && !hidden;
      if (!group.visible || !camera || !t) { if (mesh) mesh.visible = false; return; }
      camera.getWorldPosition ? camera.getWorldPosition(eye) : eye.copy(camera.position);
      let list = [];
      try { list = distantTeams(t, eye, { hour, rows }); } catch (err) { problems.push(`traffic cards: ${err?.message ?? err}`); list = []; }
      stats.distant = list.length;
      if (!list.length || !ensure()) { if (mesh) mesh.visible = false; stats.cards = 0; return; }
      const far = FAR_M[tier] ?? FAR_M.full;
      const near = [];
      for (const d of list) {
        const r = rows.get(d.id), kind = r ? teamKind(r, coarse) : null, k = kind ? kinds.get(kind) : null;
        if (!k || !Number.isFinite(d.e) || !Number.isFinite(d.n)) continue;
        const dist = Math.hypot(d.e - eye.x, d.n + eye.z);
        if (dist > far) continue;
        if (k.status === 'new') void bakeKind(kind);
        if (k.status !== 'ready') continue;
        near.push({ d, k, dist });
      }
      near.sort((a, b) => a.dist - b.dist);
      // A held frame (no time passing) with nothing moved or newly baked writes nothing, so a
      // paused scene is still.
      let key = `${eye.x},${eye.y},${eye.z}|${stats.baked}|${tier}`;
      for (const { d } of near) key += `|${d.id},${d.e},${d.n},${d.heading_deg}`;
      if (!(dt > 0) && key === wroteFor) return;
      wroteFor = key;
      const cap = Math.min(CAP[tier] ?? CAP.full, attrs.cap);
      const live = new Set();
      let n = 0;
      for (const { d, k } of near) {
        if (n >= cap) break;
        live.add(d.id);
        let s = seen.get(d.id);
        if (!s) { s = { v: 0 }; seen.set(d.id, s); }
        s.v = Math.min(1, s.v + Math.max(0, dt || 0) / IN_S);
        const yaw = Math.PI - ((d.heading_deg ?? 0) * Math.PI) / 180;
        const c = Math.cos(yaw), sn = Math.sin(yaw);
        // The card stands at the team's middle (its picture's), not at the vehicle's root.
        const x = d.e + k.centre[0] * c + k.centre[1] * sn, z = -d.n - k.centre[0] * sn + k.centre[1] * c;
        const h = heightAt(x, -z);
        attrs.pos.setXYZW(n, x, Number.isFinite(h) ? h : 0, z, yaw);
        attrs.cell.setXYZW(n, k.size, k.row * TEAM_YAWS, s.v, 1);
        n++;
      }
      for (const id of [...seen.keys()]) if (!live.has(id)) seen.delete(id);
      mesh.geometry.instanceCount = n;
      mesh.visible = n > 0;
      for (const a of [attrs.pos, attrs.cell]) { a.needsUpdate = true; a.clearUpdateRanges?.(); a.addUpdateRange?.(0, n * 4); }
      stats.cards = n;
      stats.ms = stats.ms * 0.9 + (performance.now() - t0) * 0.1;
    },
    dispose() { disposed = true; drop(); group.removeFromParent(); },
  };
}
