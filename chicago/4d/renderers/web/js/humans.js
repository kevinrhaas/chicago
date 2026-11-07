/**
 * humans.js — T-1788. THE BROWSER HUMAN ACTOR: one rigged figure as a normal scene object.
 *
 * The road T-1786 (the contract) and T-1787 (the export path) built ends here: a figure
 * exported to `assets/humans/web/<asset_id>.lod<N>.glb` is loaded through the renderer's own
 * GLTFLoader and Meshopt decoder, cloned safely onto its own skeleton, stood on the terrain,
 * animated, LOD-switched, picked and disposed. docs/HUMAN-ASSET-CONTRACT.md is the authority;
 * the section numbers below are its.
 *
 * TWO HALVES, AND ONLY ONE OF THEM IS A POLICY.
 *
 *   createHumanLayer()  the ENGINE. Holds actors, updates them, picks them, disposes them.
 *                       It draws whatever it is handed and decides nothing about who may be
 *                       drawn. tools/human_actor.html, a test page that is never published,
 *                       drives it with the CI fixture (`c4d_fixture`, who is nobody).
 *   mountHumans()       the SCENE path main.js calls. It reads the instance records filed under
 *                       the scene (§ 11) and hands the engine only eligible records. The owner
 *                       lifted L1 for the portable path (T-2672); an explicit gate remains. A scene
 *                       that does not list the `humans` layer is given no data base, fetches
 *                       nothing and draws nobody — the scene-year gate.
 *
 * Identity stays with the residents layer. An actor is bound to a person record that already
 * exists (`data/sidecars/<scene>/people.json`), carries its id, and opens that person's own
 * card; this file never mints a person and holds no second directory.
 *
 * WHAT A FAR FIGURE DOES NOT PAY FOR (§ 8; T-1792 scales it). The LOD is chosen from the camera
 * distance within the detail tier's allowed LODs, with a hysteresis band so a figure standing
 * on a threshold does not flicker. Beyond FACE_M the face holds still; beyond SHADOW_M it casts
 * no shadow; beyond ANIMATE_M its mixer is not advanced (the pose holds); beyond DRAW_M it is
 * hidden and re-examined only every RECHECK_S, so a crowd out of range costs a timer, not a
 * frame of work each.
 */
import * as THREE from 'three';
import { resolveHumanIdentity, humanRoleCard } from './human-identity.js';
import { createHumanLife } from './human-life.js';
import { createHumanActions } from './human-actions.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { registerKTX2 } from './ktx2.js';
import { shareImageSources } from './shared-images.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { loadVariationKit, personVariation, applyVariation, disposeVariants } from './human-variation.js';
import { loadMeshoptDecoder, disposeLoadedAsset } from './scene-loader.js';
import { enuToWorld } from './terrain.js';
import { dressSkin } from './human-skin.js';
import { dressHair } from './human-hair.js';
import { dressSpectacles } from './human-spectacles.js';

/** § 8: the LODs each scene-detail tier may draw. `light` stays the floor. */
export const HUMAN_TIERS = Object.freeze({ full: [0, 1, 2, 3], balanced: [1, 2, 3], light: [2, 3] });

/** Camera distance, metres, at which each LOD gives way to the next one down. */
export const LOD_BANDS_M = Object.freeze([8, 20, 45]);
/** A figure must cross a band by this share of it before its LOD changes back. */
export const LOD_HYSTERESIS = 0.12;
export const FACE_M = 20;
export const SHADOW_M = 30;
export const ANIMATE_M = 70;
export const DRAW_M = 140;
export const RECHECK_S = 0.5;
/** T-3439: seconds a level drawn before is kept, parked, for a swap back to it. */
export const PARK_S = 180;

/** § 7: the clip a state plays when the record names none the asset carries. */
const STATE_CLIPS = {
  standing: ['idle'], walking: ['walk'], talking: ['talk', 'idle'],
  working: ['work', 'idle'], seated: ['sit', 'idle'],
};
const FADE_S = 0.25;
/** T-3442: how fast a figure walking a path turns to its next leg, degrees a second; it
 *  slows to a stand while it turns further than PATH_STAND_TURN_DEG, so it turns, then goes. */
export const PATH_TURN_DEG_S = 220;
const PATH_STAND_TURN_DEG = 75;
const BLINK = ['eyeBlinkLeft', 'eyeBlinkRight'];

/**
 * The LOD to draw at `distance`, deterministic: the band's LOD clamped into the tier, and,
 * given the LOD drawn now, held until the distance clears the band by LOD_HYSTERESIS.
 * Returns -1 beyond DRAW_M (not drawn).
 */
export function chooseHumanLod(distance, tier = 'full', current = -1, { policy = 'auto', fixed = 0 } = {}) {
  if (!(distance <= DRAW_M)) return -1;
  const allowed = HUMAN_TIERS[tier] ?? HUMAN_TIERS.full;
  const clamp = (lod) => Math.min(Math.max(lod, allowed[0]), allowed[allowed.length - 1]);
  if (policy === 'fixed') return clamp(fixed);
  let lod = LOD_BANDS_M.findIndex((band) => distance < band);
  if (lod < 0) lod = LOD_BANDS_M.length;
  if (current >= 0 && current !== lod) {
    // Moving out to a coarser LOD needs the distance past the band by the margin; moving
    // back in needs it short of the band by the same margin.
    const edge = LOD_BANDS_M[Math.min(current, lod)];
    const margin = edge * LOD_HYSTERESIS;
    if (lod > current ? distance < edge + margin : distance > edge - margin) lod = current;
  }
  return clamp(lod);
}

/** § 2: heading degrees clockwise from grid north → three.js rotation.y for a +Z-facing asset. */
export function headingToYaw(headingDeg) { return Math.PI - (headingDeg * Math.PI) / 180; }

const verbOf = (name) => String(name).split('_')[0];

/** The first clip whose name is `want` or whose verb is `want`, in the order given. */
function findClip(clips, want) {
  return clips.get(want) ?? [...clips.values()].find((c) => verbOf(c.name) === want) ?? null;
}

/**
 * Refcounted loads of `<asset_id>.lod<N>.glb`. One parse per file however many people wear
 * it; the parsed source is disposed when the last actor wearing it lets it go.
 */
export function createHumanAssets({ assetBase, loader = registerKTX2(new GLTFLoader()), fetchImpl = fetch } = {}) {
  // T-3453: every figure carries the same hair, skin and eye pictures (published once under
  // humans/web/sheets/, T-3453); decode each once and hand every figure a clone of it, as
  // the houses do (T-2464). disposeLoadedAsset closes a bitmap only when its last user goes.
  if (typeof loader?.register === 'function') shareImageSources(loader);
  const entries = new Map();
  let decoder = null;
  let variation = null;
  const url = (assetId, lod) => new URL(`humans/web/${assetId}.lod${lod}.glb`, assetBase);

  async function parse(href) {
    const res = await fetchImpl(href);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${href}`);
    const buf = await res.arrayBuffer();
    // The same sniff scene-loader.js makes: the decoder only when the file needs it.
    const dv = new DataView(buf);
    const json = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 20, dv.getUint32(12, true))));
    if ((json.extensionsUsed ?? []).includes('EXT_meshopt_compression')) {
      decoder ??= loadMeshoptDecoder();
      loader.setMeshoptDecoder(await decoder);
    }
    return loader.parseAsync(buf, String(new URL('.', href)));
  }

  return {
    url,
    acquire(assetId, lod) {
      const key = `${assetId}.lod${lod}`;
      let e = entries.get(key);
      if (!e) { e = { refs: 0, gltf: parse(url(assetId, lod)) }; entries.set(key, e); }
      e.refs++;
      e.gltf.catch(() => entries.get(key) === e && entries.delete(key));
      return e.gltf;
    },
    release(assetId, lod) {
      const key = `${assetId}.lod${lod}`;
      const e = entries.get(key);
      if (!e || --e.refs > 0) return;
      entries.delete(key);
      e.gltf.then((gltf) => {
        const geometries = new Set();
        gltf?.scene?.traverse((node) => { if (node.geometry) geometries.add(node.geometry); });
        disposeVariants(geometries);
        disposeLoadedAsset(gltf);
      }, () => {});
    },
    /**
     * T-3412: the shared body/face delta kit and each drawn person's record (age, a fitted
     * face), fetched once. Never rejects: without them every figure is the asset as drawn.
     */
    variation() {
      variation ??= Promise.all([
        loadVariationKit(new URL('humans/web/', assetBase), fetchImpl),
        Promise.resolve(fetchImpl(new URL('humans/web/hm08_variation_persons.json', assetBase)))
          .then((r) => (r.ok ? r.json() : null)).catch(() => null),
      ]).then(([kit, persons]) => (kit ? { kit, persons: persons?.persons ?? {} } : null), () => null);
      return variation;
    },
    get loaded() { return [...entries.keys()]; },
  };
}

/** Hit proxy: a figure is picked by an upright box at its rest height, never by its skin. */
const PROXY_GEOMETRY = new THREE.BoxGeometry(0.6, 1, 0.45).translate(0, 0.5, 0);
const PROXY_MATERIAL = new THREE.MeshBasicMaterial({ visible: false });

/**
 * One figure: an instance record (§ 11) bound to its person, drawn from one asset.
 * `heightAt(e, n)` stands it on the ground; `clipLibrary` (AnimationClips on the contract
 * skeleton, § 7) adds clips the body's own file does not carry.
 */
export class HumanActor {
  constructor({ instance, person = null, identity = null, assets, heightAt = () => 0, clipLibrary = [], tier = 'full', variation = 'full', prepare = null }) {
    this.instance = instance;
    this.person = person;
    this.identity = identity ?? { kind: 'person', personId: instance.person_id, person, profile: null, role: null };
    this.personId = this.identity.personId;
    this.id = instance.id;
    this.assets = assets;
    this.heightAt = heightAt;
    this.tier = tier;
    this.state = instance.behaviour?.state ?? 'standing';
    this.root = new THREE.Group();
    this.root.name = `human:${instance.id}`;
    this.root.userData.personId = this.personId;
    this.root.userData.instanceId = this.id;
    this.root.userData.identityKind = this.identity.kind;
    this.proxy = new THREE.Mesh(PROXY_GEOMETRY, PROXY_MATERIAL);
    // Never submitted (a raycast tests layers, not visibility), so it is never uploaded either.
    this.proxy.visible = false;
    this.proxy.userData.actor = this;
    this.root.add(this.proxy);
    this.libraryClips = clipLibrary;
    // T-3439: `prepare(object)` readies a new level's programs off the frame (main.js passes
    // renderer.compileAsync) before it is drawn; without it the first draw compiles them.
    this.prepare = prepare;
    // T-3412: this person's own height, build and face (human-variation.js). `face` keeps a
    // seated driver's body as fitted to his seat and reins; `none` draws the asset as it is.
    this.variationScope = variation;
    this.variation = null;
    this.varied = null;
    this.lod = -1;
    this.wanted = -1;
    this.visualIdleBody = null;
    // T-3402: breathing, weight shifts, gaze and blinks over the clip (human-life.js).
    // One per figure, rebound on a LOD swap; null until a contract-skeleton body loads.
    this.life = null;
    // T-3415: what the arms and hands do (human-actions.js), after the life layer.
    this.actions = null;
    this.body = null;           // { lod, scene, meshes, mixer, clips, actions, faces }
    // T-3439: levels drawn before and kept for a swap back (lod -> body), on this clock.
    this.parked = new Map();
    this.clock = 0;
    this.pending = null;
    this.clipName = null;
    this.phase = instance.animation?.phase ?? 0;
    this.costs = '';
    this.counters = { updates: 0, animated: 0, faced: 0, swaps: 0, reused: 0 };
    this.expression = {};
    this.blinkClock = hashPhase(instance.id) * 4;
    this.distance = Infinity;
    this.inRange = false;
    this.recheck = 0;
    this.disposed = false;
    const p = instance.placement;
    this.e = p.local_e;
    this.n = p.local_n;
    this.heading = p.heading_deg;
    this.route = instance.behaviour?.route?.length ? [{ local_e: p.local_e, local_n: p.local_n }, ...instance.behaviour.route] : null;
    this.leg = 0;
    this.legT = 0;
    // T-3442: a one-way walk (walkPath), and the height it last stood the figure at.
    this.path = null;
    this.standY = null;
    // T-3443: gone indoors (house-errands.js): not drawn, not picked, met by nobody.
    this.indoors = false;
    this.place();
  }

  /** Where it stands, in local ENU metres, with its feet on the ground. */
  get position() {
    const p = this.root.getWorldPosition(new THREE.Vector3());
    return { e: p.x, n: -p.z, y: p.y };
  }

  place() {
    // T-3442: on a walked path the path says how high each point is (a tread, a sill).
    enuToWorld(this.e, this.n, this.standY ?? this.heightAt(this.e, this.n), this.root.position);
    this.root.rotation.y = headingToYaw(this.heading);
  }

  /**
   * Load (or switch to) `lod`. Resolves when it is drawn; the previous LOD stays up until then.
   *
   * T-3439: a level drawn before is kept, parked, and a swap back to it is a switch, not a
   * load. Before, every swap let the old level go, and a visitor walking about a figure
   * crossed her 8 m and 20 m bands again and again: each crossing parsed her GLB anew,
   * uploaded its 2048 px pictures, regrew her strand hair and, because letting go of the old
   * level's materials dropped the last user of her skin, hair and eye programs, compiled
   * those programs again on the next frame. That was the Glessner courtyard's freeze. A
   * parked level costs no draw and no update; it is let go when the figure goes out of
   * range, when the detail tier no longer allows it, or after PARK_S unused. Every level is
   * kept, not only the neighbours: a courtyard walk spans three bands (2 to 25 m), and
   * letting the far one go reloaded it on every lap.
   */
  async setLod(lod) {
    if (this.disposed || lod === this.lod || lod === this.wanted) return this.pending ?? this.body;
    const parked = this.parked.get(lod);
    if (parked) {
      this.parked.delete(lod);
      this.wanted = lod;
      this.counters.reused++;
      return this.show(parked);
    }
    this.wanted = lod;
    const assetId = this.instance.appearance.asset_id;
    const job = Promise.all([this.assets.acquire(assetId, lod), this.assets.variation?.() ?? null]).then(async ([gltf, variation]) => {
      if (this.disposed || this.wanted !== lod) { this.assets.release(assetId, lod); return this.body; }
      const next = this.build(gltf, lod, variation);
      if (this.prepare) {
        // Shadows as the level will be drawn, so the programs compiled are the ones it uses.
        for (const m of next.meshes) { m.castShadow = this.distance < SHADOW_M && lod <= 1; m.receiveShadow = this.distance < SHADOW_M; }
        try { await this.prepare(next.scene); } catch { /* the first draw compiles them instead */ }
        if (this.disposed) { this.teardown(next); return this.body; }
        // Wanted elsewhere meanwhile: keep it for a swap back, as a level drawn before is kept.
        if (this.wanted !== lod) { next.parkedAt = this.clock; if (this.parked.has(lod)) this.teardown(next); else this.parked.set(lod, next); this.prune(); return this.body; }
      }
      return this.show(next);
    }, (err) => { if (this.wanted === lod) this.wanted = this.lod; throw err; });
    this.pending = job;
    job.finally(() => { if (this.pending === job) this.pending = null; }).catch(() => {});
    return job;
  }

  /** Draw `next` in place of the body drawn now, which is parked, not let go. */
  show(next) {
    const prev = this.body;
    // The new LOD takes up the clip where the old one was, so a swap is not a stumble.
    const time = prev?.action ? prev.action.time : null;
    this.body = next;
    this.lod = next.lod;
    this.hair = next.hair ?? null;
    this.root.add(next.scene);
    this.play(this.clipName ?? this.defaultClip(), { fade: 0, time });
    if (this.life) this.life.bind(next.scene);
    else this.life = createHumanLife({ id: this.personId ?? this.id, scene: next.scene });
    if (this.actions) this.actions.bind(next.scene);
    else {
      // The dress assembly's figures greet with a nod (T-3423); the GLB's scene extras name it.
      // A later woman's assembly says `"skirt": true` there itself (T-3447).
      const dressed = /adult_dress_v1|"skirt":\s*true/.test(next.scene.userData?.chicago4d_human?.wardrobe_assembly_json ?? '');
      this.actions = createHumanActions({ id: this.personId ?? this.id, scene: next.scene, greeting: dressed ? 'nod' : 'brow', skirt: dressed });
    }
    if (prev) { this.counters.swaps++; this.park(prev); }
    this.costs = '';
    this.applyCosts();
    this.applyFace(this.expression);
    this.prune();
    return next;
  }

  /** Take `body` out of the scene and keep it for a swap back (T-3439). */
  park(body) {
    body.mixer.stopAllAction();
    body.action = null;
    body.oneShot = null;
    body.scene.removeFromParent();
    body.parkedAt = this.clock;
    const old = this.parked.get(body.lod);
    if (old && old !== body) this.teardown(old);
    this.parked.set(body.lod, body);
  }

  /** Let go of parked levels when out of range, outside the tier, or unused for PARK_S. */
  prune(all = false) {
    const allowed = HUMAN_TIERS[this.tier] ?? HUMAN_TIERS.full;
    for (const [lod, body] of this.parked) {
      if (all || !allowed.includes(lod) || this.clock - body.parkedAt > PARK_S) {
        this.parked.delete(lod);
        this.teardown(body);
      }
    }
  }

  /** T-3412: this person's own face, height and build, from the shared kit, on the clone. */
  vary(scene, variation) {
    if (!variation?.kit || this.variationScope === 'none') return;
    const assetId = this.instance.appearance.asset_id;
    this.variation ??= personVariation({ kit: variation.kit, key: this.personId ?? this.id,
      record: variation.persons?.[this.personId] ?? null, assetId, sceneYear: Number(this.instance.scene) || null });
    this.varied = applyVariation(scene, variation.kit, this.variation, { scope: this.variationScope });
  }

  build(gltf, lod, variation = null) {
    const scene = cloneSkinned(gltf.scene);
    this.vary(scene, variation);   // before dressSkin, which reads the varied rest pose
    const meshes = [];
    scene.traverse((o) => {
      if (!o.isSkinnedMesh) return;
      meshes.push(o);
      o.frustumCulled = false;    // a skinned bound is the rest pose's, not the walk's
    });
    // T-3400: skin with pores, blood and a glow, hair with a strand sheen, wet eyes, on
    // every person (human-skin.js; a shader patch, no texture). Bound to the rest pose.
    dressSkin(scene);
    // Measured through the node transforms: a quantised derivative's positions are not metres.
    scene.updateMatrixWorld(true);
    const height = new THREE.Box3().setFromObject(scene).max.y;
    this.proxy.scale.y = height > 0.3 ? height : 1.7;
    // T-3414: at the near levels, strand-card hair, beard and whiskers grown from this body's
    // own scalp and face, by the person's cut (human-hair-styles.js). Not counted in its height.
    const hair = dressHair(scene, { lod, person: this.personId ?? null, year: Number(this.instance.scene) || null });
    // T-3440: spectacles, for a person whose portrait shows them (human-spectacles.js).
    this.spectacles = dressSpectacles(scene, { lod, person: this.personId ?? null });
    const clips = new Map();
    for (const c of gltf.animations ?? []) clips.set(c.name, c);
    for (const c of this.libraryClips) if (!clips.has(c.name)) clips.set(c.name, c);
    // § 6: the face, where this LOD carries one. lod2/lod3 may not, and then it holds still.
    const faces = meshes.filter((m) => m.morphTargetDictionary && Object.keys(m.morphTargetDictionary).length);
    const mixer = new THREE.AnimationMixer(scene);
    mixer.addEventListener('finished', (ev) => { if (ev.action === this.body?.oneShot) this.endGesture(); });
    return { lod, scene, meshes, faces, mixer, clips, hair, action: null, oneShot: null, assetId: this.instance.appearance.asset_id };
  }

  teardown(body) {
    body.mixer.stopAllAction();
    body.mixer.uncacheRoot(body.scene);
    body.scene.removeFromParent();
    const skeletons = new Set(body.meshes.map((m) => m.skeleton).filter(Boolean));
    for (const s of skeletons) s.dispose();
    this.assets.release(body.assetId, body.lod);
  }

  /** The clip names this figure can play now (body plus library). */
  get clips() { return this.body ? [...this.body.clips.keys()] : []; }

  defaultClip() {
    // T-3456 (owner, 2026-11-07: "he does not walk he slides and doesnt move his legs"): the
    // record's own clip is what it plays in the state it was placed in. Walking a path (a
    // stroll, the way home) plays the walk, not the record's idle.
    const named = this.instance.animation?.clip;
    const placed = this.instance.behaviour?.state ?? 'standing';
    if (named && this.state === placed && this.body && findClip(this.body.clips, named)) return named;
    for (const want of STATE_CLIPS[this.state] ?? ['idle']) {
      const c = this.body && findClip(this.body.clips, want);
      if (c) return c.name;
    }
    return 'idle';
  }

  /** Cross-fade to a named clip (or a verb). Returns false if this asset has none. */
  play(name, { fade = FADE_S, loop = this.instance.animation?.loop ?? true, time = null } = {}) {
    const b = this.body;
    if (!b) { this.clipName = name; return false; }
    const clip = findClip(b.clips, name);
    if (!clip) return false;
    const action = b.mixer.clipAction(clip);
    action.setLoop(loop ? THREE.LoopRepeat : THREE.LoopOnce, Infinity);
    action.clampWhenFinished = !loop;
    action.enabled = true;
    action.reset();
    // The first clip a figure plays starts at its record's phase, so a crowd is not in step.
    const first = this.clipName === null;
    action.time = time !== null ? time % clip.duration : first ? this.phase * clip.duration : 0;
    action.play();
    if (b.action && b.action !== action && fade > 0) b.action.crossFadeTo(action, fade, false);
    else if (b.action && b.action !== action) b.action.stop();
    b.action = action;
    this.clipName = clip.name;
    b.mixer.update(0);
    return true;
  }

  /** Play one gesture clip once, then return to what the state plays. */
  gesture(name = 'gesture') {
    const b = this.body;
    const clip = b && findClip(b.clips, name);
    if (!clip) return false;
    const resume = this.clipName;
    const action = b.mixer.clipAction(clip);
    action.reset().setLoop(THREE.LoopOnce, 1);
    action.clampWhenFinished = true;
    action.play();
    if (b.action) b.action.crossFadeTo(action, FADE_S, false);
    b.oneShot = action;
    b.resume = resume;
    b.action = action;
    this.clipName = clip.name;
    return true;
  }

  endGesture() {
    const b = this.body;
    if (!b?.oneShot) return;
    const shot = b.oneShot;
    b.oneShot = null;
    const back = findClip(b.clips, b.resume ?? this.defaultClip());
    if (!back) return;
    const action = b.mixer.clipAction(back);
    action.reset().setLoop(THREE.LoopRepeat, Infinity).play();
    shot.crossFadeTo(action, FADE_S, false);
    b.action = action;
    this.clipName = back.name;
  }

  setState(state) {
    if (!STATE_CLIPS[state]) return false;
    this.state = state;
    return this.play(this.defaultClip());
  }

  /**
   * Set morph weights by contract name (§ 6). Returns the names the current LOD applied;
   * a LOD with no face applies none and nothing throws.
   */
  setExpression(weights) {
    Object.assign(this.expression, weights);
    return this.applyFace(this.expression);
  }

  applyFace(weights) {
    const applied = new Set();
    for (const m of this.body?.faces ?? []) {
      for (const [name, w] of Object.entries(weights)) {
        const i = m.morphTargetDictionary[name];
        if (i === undefined) continue;
        m.morphTargetInfluences[i] = w;
        applied.add(name);
      }
    }
    return [...applied];
  }

  /** Shadows and the face, by distance and LOD. Writes only when a band is crossed. */
  applyCosts() {
    const b = this.body;
    if (!b) return;
    const shadow = this.distance < SHADOW_M && b.lod <= 1;
    const face = this.distance < FACE_M && b.faces.length > 0;
    const key = `${shadow}|${face}`;
    if (key === this.costs) return;
    this.costs = key;
    for (const m of b.meshes) { m.castShadow = shadow; m.receiveShadow = this.distance < SHADOW_M; }
    // A face out of reach holds still: the blink is let go, the set expression kept.
    if (!face) this.applyFace({ ...this.expression, ...Object.fromEntries(BLINK.map((k) => [k, this.expression[k] ?? 0])) });
  }

  /** What a far figure is spared, now: for the harness and T-1792's budgets. */
  get costsNow() {
    const b = this.body;
    return {
      lod: this.lod, drawn: this.root.visible, distance: +this.distance.toFixed(2),
      animates: this.distance < ANIMATE_M, face: !!b && this.distance < FACE_M && b.faces.length > 0,
      shadow: !!b && b.meshes.some((m) => m.castShadow), morphs: b ? b.faces.length > 0 : false,
    };
  }

  /**
   * T-3442: walk once along `points` — [{ e, n, y }] local ENU metres with the height to
   * stand at each (house-doors.js `path()`: the sidewalk, up each tread, through a door) —
   * at the walk clip's ground speed, turning to each leg as it goes, the feet at each
   * point's height (a missing `y` is the ground's), and stand and idle at the end, turned
   * to `endHeading` (compass degrees) if one is given. `onArrive(actor)` is called once,
   * when it has stopped and turned. Returns false for a path of fewer than two points.
   */
  walkPath(points, { endHeading = null, onArrive = null, speed = null } = {}) {
    const pts = (points ?? []).map((p) => ({ e: p.e ?? p.local_e ?? p[0], n: p.n ?? p.local_n ?? p[1], y: Number.isFinite(p.y) ? p.y : null }))
      .filter((p) => Number.isFinite(p.e) && Number.isFinite(p.n));
    if (pts.length < 2) return false;
    this.path = { pts, leg: 0, t: 0, endHeading, onArrive, speed, arrived: false };
    this.e = pts[0].e;
    this.n = pts[0].n;
    this.standY = pts[0].y;
    this.setState('walking');
    this.place();
    return true;
  }

  /**
   * T-3443: turn where it stands to face `heading` (compass degrees) at the walk's turn
   * rate, then call `onArrive(actor)`. A walk under way is given up for it.
   */
  turnTo(heading, { onArrive = null } = {}) {
    if (!Number.isFinite(heading)) return false;
    this.path = { pts: [{ e: this.e, n: this.n, y: this.standY }], leg: 0, t: 0, endHeading: heading, onArrive, speed: null, arrived: true };
    if (this.state === 'walking') this.setState('standing');
    return true;
  }

  /** T-3443: in the house (not drawn, picked or met) or back out on its step. */
  setIndoors(on) {
    this.indoors = !!on;
    if (this.indoors) { this.root.visible = false; this.inRange = false; }
    else this.recheck = 0;
    return this.indoors;
  }

  /** T-3442: stop a path where the figure is, standing. */
  stopPath() {
    if (!this.path) return false;
    this.path = null;
    this.setState('standing');
    return true;
  }

  /** T-3442: one frame of a walkPath. */
  followPath(dt) {
    const p = this.path;
    const turnToward = (want) => {
      const diff = ((want - this.heading + 540) % 360) - 180;
      const turn = Math.sign(diff) * Math.min(Math.abs(diff), PATH_TURN_DEG_S * dt);
      this.heading = (this.heading + turn + 360) % 360;
      return Math.abs(diff - turn);
    };
    if (p.arrived) {
      // Stood at the end: turn to face where it was asked, then it is done.
      const left = p.endHeading === null ? 0 : turnToward(p.endHeading);
      if (left < 0.5) {
        this.path = null;
        p.onArrive?.(this);
      }
      this.place();
      return;
    }
    const clip = this.body && findClip(this.body.clips, 'walk');
    const speed = p.speed ?? clip?.userData?.speed_m_s ?? this.walkSpeed ?? 1.3;
    const a0 = p.pts[p.leg], b0 = p.pts[p.leg + 1];
    const off = turnToward((Math.atan2(b0.e - a0.e, b0.n - a0.n) * 180 / Math.PI + 360) % 360);
    // A figure facing well away from its way turns before it walks on.
    let left = speed * dt * Math.max(0, Math.cos(Math.min(90, off * 90 / PATH_STAND_TURN_DEG) * Math.PI / 180));
    while (left > 0 && p.leg < p.pts.length - 1) {
      const a = p.pts[p.leg], b = p.pts[p.leg + 1];
      const len = Math.hypot(b.e - a.e, b.n - a.n);
      const step = Math.min(left, len * (1 - p.t));
      p.t = len > 1e-9 ? p.t + step / len : 1;
      left -= step;
      if (p.t >= 1 - 1e-9) { p.leg += 1; p.t = 0; if (step <= 0 && len > 1e-9) break; }
    }
    const a = p.pts[Math.min(p.leg, p.pts.length - 1)], b = p.pts[Math.min(p.leg + 1, p.pts.length - 1)];
    this.e = a.e + (b.e - a.e) * p.t;
    this.n = a.n + (b.n - a.n) * p.t;
    this.standY = a.y !== null && b.y !== null ? a.y + (b.y - a.y) * p.t : null;
    if (p.leg >= p.pts.length - 1) {
      p.arrived = true;
      this.setState('standing');
    }
    this.place();
  }

  /** Advance along a walking route at the walk clip's stated ground speed (§ 7: in place). */
  walk(dt) {
    if (this.path) { this.followPath(dt); return; }
    if (this.state !== 'walking' || !this.route || this.route.length < 2) return;
    const clip = this.body && findClip(this.body.clips, 'walk');
    const speed = clip?.userData?.speed_m_s ?? this.walkSpeed ?? 1.3;
    let left = speed * dt;
    while (left > 0) {
      const a = this.route[this.leg];
      const b = this.route[(this.leg + 1) % this.route.length];
      const len = Math.hypot(b.local_e - a.local_e, b.local_n - a.local_n) || 1e-6;
      const step = Math.min(left, len * (1 - this.legT));
      this.legT += step / len;
      left -= step;
      this.e = a.local_e + (b.local_e - a.local_e) * this.legT;
      this.n = a.local_n + (b.local_n - a.local_n) * this.legT;
      this.heading = ((Math.atan2(b.local_e - a.local_e, b.local_n - a.local_n) * 180) / Math.PI + 360) % 360;
      if (this.legT >= 1 - 1e-9) { this.leg = (this.leg + 1) % this.route.length; this.legT = 0; }
      if (step <= 0) break;
    }
    this.place();
  }

  /**
   * One frame. `camera` is a three.js camera (or anything with a world `position`).
   * Returns false when the figure was out of range and nothing was done.
   */
  update(dt, cameraPosition, visualDt = dt) {
    if (this.disposed) return false;
    if (this.indoors) { this.root.visible = false; this.inRange = false; return false; }
    this.recheck -= dt;
    this.clock += dt;
    if (!this.inRange && this.recheck > 0) return false;
    this.distance = cameraPosition.distanceTo(this.root.position);
    const lod = chooseHumanLod(this.distance, this.tier, this.lod, this.instance.lod);
    this.inRange = lod >= 0;
    if (this.parked.size) this.prune(!this.inRange);
    if (!this.inRange) {
      this.root.visible = false;
      this.visualIdleBody = null;
      this.recheck = RECHECK_S;
      return false;
    }
    this.counters.updates++;
    this.root.visible = !!this.body;
    if (lod !== this.lod && lod !== this.wanted) this.setLod(lod).catch(() => {});
    this.walk(dt);
    const b = this.body;
    if (!b) { this.visualIdleBody = null; return true; }
    if (this.distance < ANIMATE_M) {
      const naturalStanding = this.state === 'standing' && this.clipName === 'idle_natural_v1' && !b.oneShot;
      const idleDt = Number.isFinite(visualDt) && visualDt >= 0 ? visualDt : 0;
      const clipDt = naturalStanding ? (this.visualIdleBody === b ? idleDt : 0) : dt;
      b.mixer.update(clipDt);
      // Life rides the clip's own clock, so a held clip holds it too.
      if (this.life?.bound && !b.oneShot) this.life.apply(clipDt, { state: this.state, root: this.root, viewer: cameraPosition });
      if (this.actions?.bound && !b.oneShot) {
        this.actions.apply(clipDt, { state: this.state, root: this.root, viewer: cameraPosition });
        if (this.actions.takeNod()) this.life?.nod();
      }
      this.visualIdleBody = naturalStanding ? b : null;
      this.counters.animated++;
    } else this.visualIdleBody = null;
    if (this.distance < FACE_M && b.faces.length) {
      // A deterministic blink, so a near face is alive and a still one is a choice: the
      // life layer's irregular one (T-3402) where it is bound, else every 4 s.
      this.blinkClock += dt;
      const t = this.blinkClock % 4;
      const w = this.life?.bound ? this.life.blink : t < 0.15 ? Math.sin((t / 0.15) * Math.PI) : 0;
      this.applyFace({ ...this.expression, eyeBlinkLeft: w, eyeBlinkRight: w });
      this.counters.faced++;
    }
    this.applyCosts();
    return true;
  }

  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    this.wanted = -1;
    if (this.body) this.teardown(this.body);
    this.prune(true);
    this.visualIdleBody = null;
    this.body = null;
    this.root.removeFromParent();
  }
}

/** A stable 0-1 phase from an id, so the same figure blinks at the same moment on every load. */
function hashPhase(id) {
  let h = 2166136261;
  for (const ch of String(id)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return ((h >>> 0) % 1000) / 1000;
}

/**
 * THE ENGINE. A group of actors with update, pick, select, approach and dispose.
 *
 * Events (an EventTarget): `select` and `hover` with { personId, instanceId, state, opens },
 * `approach` and `leave` when the visitor crosses an actor's interaction.radius_m, and `open`
 * when a selection or an approach asks for the person's resident card (`opens:
 * resident_card`). Nothing here is a conversation: L1 allows no invented dialogue, and the
 * card is the person record's own.
 */
export function createHumanLayer({ assetBase, assets = null, heightAt = () => 0, tier = 'full', clipLibrary = [], prepare = null } = {}) {
  const group = new THREE.Group();
  group.name = 'humans';
  const events = new EventTarget();
  const actors = new Map();
  // A vehicle temporarily owns a person's depiction, never a second copy in town.
  const withheld = new Map();
  let disposed = false;
  const store = assets ?? createHumanAssets({ assetBase });
  const raycaster = new THREE.Raycaster();
  const near = new Set();
  let hovered = null;
  // T-3439: Settings › Show › People. Hidden, nobody is drawn, updated, loaded or picked,
  // a seated driver included (his vehicle owns him, so only his root is hidden).
  let shown = true;
  // T-3495: a jaunt's hold on the everyday people. null, nobody is held; a Set, only the
  // people it names (by person id or instance id) are drawn, advanced, met or picked.
  let keep = null;
  const kept = (a) => !keep || keep.has(a.personId) || keep.has(a.id);

  const detail = (actor) => ({
    personId: actor.personId, instanceId: actor.id, state: actor.state,
    opens: actor.instance.interaction?.opens ?? 'none', person: actor.person,
    identityKind: actor.identity.kind, profileId: actor.identity.profile?.id ?? null, role: actor.identity.role,
    roleCard: humanRoleCard(actor.identity, actor.instance),
  });
  const emit = (type, actor) => events.dispatchEvent(new CustomEvent(type, { detail: detail(actor) }));

  const layer = {
    group,
    events,
    assets: store,
    on(type, fn) { events.addEventListener(type, (ev) => fn(ev.detail)); return layer; },
    get count() { return actors.size + [...withheld.values()].filter(t => t.externalActor).length; },
    get actors() { return [...actors.values(), ...[...withheld.values()].map(t => t.externalActor).filter(Boolean)]; },
    get(personId) { return actors.get(personId) ?? (personId ? layer.actors.find((a) => a.id === personId || a.personId === personId) : null) ?? null; },
    // External depictions remain addressable for People/Find, but their vehicle
    // alone advances, places and chooses the LOD of the seated body.
    external(personId) { return withheld.get(personId)?.externalActor ?? null; },

    get shown() { return shown; },
    /** T-3439: show or hide every figure, drivers on their seats included. */
    setShown(on) {
      shown = on !== false;
      group.visible = shown;
      for (const token of withheld.values()) if (token.externalActor?.root) token.externalActor.root.visible = shown;
      if (!shown) {
        for (const a of near) emit('leave', a);
        near.clear();
        hovered = null;
      }
      return shown;
    },

    /**
     * T-3495: hold the everyday people out of the scene while a jaunt is under way, but for
     * `ids` (the people its stop calls for). Drivers on their seats belong to their vehicles
     * and are not held. Settings › Show › People stays the master switch: hidden there,
     * nobody is drawn, held or not.
     */
    holdCrowd(ids = []) {
      keep = new Set(Array.from(ids ?? [], String));
      for (const a of actors.values()) {
        if (kept(a)) { a.recheck = 0; continue; }
        a.root.visible = false;
        if (near.delete(a)) emit('leave', a);
        if (hovered === a) hovered = null;
      }
      return keep.size;
    },
    /** T-3495: give every held figure back to the scene. */
    releaseCrowd() {
      if (!keep) return false;
      keep = null;
      for (const a of actors.values()) a.recheck = 0;
      return true;
    },
    /** T-3495: the person ids a jaunt keeps, or null when nobody is held. */
    get crowdKept() { return keep ? [...keep] : null; },
    /** T-3495: whether a jaunt is holding this figure out of the scene. */
    isHeld(actor) { return !!actor && actors.has(actor.id) && !kept(actor); },

    /** Stand one figure in the group. Refuses a second instance of one person (§ 11). */
    add(instance, { person = null, profile = null, identity: validatedIdentity = null } = {}) {
      if (disposed || actors.has(instance.id) || (instance.person_id
          && (layer.get(instance.person_id) || withheld.has(instance.person_id)))) {
        throw new Error(`humans: ${instance.person_id} already stands in this scene`);
      }
      const identity = validatedIdentity ?? (instance.anonymous_profile_id
        ? resolveHumanIdentity(instance, { profiles: profile ? [profile] : [] })
        : { kind: 'person', personId: instance.person_id, person, profile: null, role: null });
      const actor = new HumanActor({ instance, person, identity, assets: store, heightAt, clipLibrary, tier, prepare });
      actors.set(instance.id, actor);
      group.add(actor.root);
      return actor;
    },

    /** Transfer only the standing depiction; the vehicle owns its seated actor.
     * Detaching its root AND update/pick entry prevents the next frame drawing it again.
     * The release restores the exact original actor, or retires it with a disposed layer.
     */
    withhold(personId, { instanceId = null, externalActor = null } = {}) {
      if (disposed || !personId || withheld.has(personId)) throw Error('humans: person already transferred or layer disposed');
      if (externalActor && (externalActor.personId !== personId
          || (instanceId && externalActor.id !== instanceId))) throw Error('humans: external driver identity differs');
      const actor = layer.get(personId);
      if (actor && instanceId && actor.id !== instanceId) throw Error('humans: transferred instance differs from the driver');
      const parent = actor?.root.parent ?? null;
      const visible = actor?.root.visible;
      const token = { actor, externalActor, release: null };
      withheld.set(personId, token);
      if (externalActor?.root && !shown) externalActor.root.visible = false;
      if (actor) {
        actors.delete(actor.id); near.delete(actor);
        if (hovered === actor) hovered = null;
        actor.root.removeFromParent();
      }
      let released = false;
      token.release = () => {
        if (released) return;
        released = true;
        if (withheld.get(personId) !== token) return;
        withheld.delete(personId);
        if (!actor) return;
        if (disposed || actor.disposed) { actor.dispose(); return; }
        actors.set(actor.id, actor);
        actor.tier = tier; actor.recheck = 0; actor.root.visible = visible && kept(actor);
        (parent ?? group).add(actor.root);
      };
      return token.release;
    },

    remove(id) {
      const a = actors.get(id) ?? layer.get(id);
      if (!a) return false;
      // The vehicle alone retires its seated actor; release the transfer first.
      if ([...withheld.values()].some(token => token.externalActor === a)) return false;
      actors.delete(a.id);
      near.delete(a);
      if (hovered === a) hovered = null;
      a.dispose();
      return true;
    },

    setTier(next) {
      if (!HUMAN_TIERS[next]) return false;
      tier = next;
      for (const a of actors.values()) { a.tier = next; a.recheck = 0; }
      return true;
    },

    /**
     * One frame for every actor. `visitor` (local ENU {e, n}, the walker) is what crosses an
     * interaction radius; it defaults to the camera's ground position.
     */
    update(dt, camera, visitor = null, visualDt = dt) {
      if (!actors.size || !shown) return;
      const eye = camera.getWorldPosition ? camera.getWorldPosition(new THREE.Vector3()) : camera.position;
      const ve = visitor ? visitor.e : eye.x;
      const vn = visitor ? visitor.n : -eye.z;
      for (const a of actors.values()) {
        if (!kept(a)) continue;
        a.update(dt, eye, visualDt);
        const r = a.instance.interaction?.radius_m;
        if (!r || !a.inRange) continue;
        const inside = Math.hypot(a.e - ve, a.n - vn) <= r;
        if (inside && !near.has(a)) {
          near.add(a);
          emit('approach', a);
          if (a.instance.interaction?.opens === 'resident_card' && a.identity.kind === 'person') emit('open', a);
          if (a.instance.interaction?.opens === 'role_card' && a.identity.kind === 'anonymous') emit('role_open', a);
        } else if (!inside && near.has(a)) {
          near.delete(a);
          emit('leave', a);
        }
      }
    },

    /** The selectable, drawn figure under `ndc` (the crosshair when null), nearest first. */
    pickAt(ndc, camera) {
      if (!actors.size || !camera || !shown) return null;
      raycaster.setFromCamera(ndc ?? new THREE.Vector2(0, 0), camera);
      raycaster.far = DRAW_M + 10;
      const proxies = [];
      for (const a of actors.values()) {
        if (a.root.visible && a.body && a.instance.interaction?.selectable) proxies.push(a.proxy);
      }
      group.updateMatrixWorld(true);
      const hit = raycaster.intersectObjects(proxies, false)[0];
      if (!hit) return null;
      const a = hit.object.userData.actor;
      return { ...detail(a), actor: a, distance: hit.distance, point: hit.point.clone() };
    },

    hoverAt(ndc, camera) {
      const hit = layer.pickAt(ndc, camera);
      const a = hit?.actor ?? null;
      if (a !== hovered) { hovered = a; if (a) emit('hover', a); }
      return hit;
    },

    /** Select by person id (or a pick); fires `select`, and `open` when the record opens a card. */
    select(target) {
      const a = typeof target === 'string' ? layer.get(target) : target?.actor ?? null;
      if (!a || !a.instance.interaction?.selectable) return null;
      emit('select', a);
      if (a.instance.interaction?.opens === 'resident_card' && a.identity.kind === 'person') emit('open', a);
          if (a.instance.interaction?.opens === 'role_card' && a.identity.kind === 'anonymous') emit('role_open', a);
      return detail(a);
    },

    dispose() {
      disposed = true;
      for (const token of [...withheld.values()]) token.release();
      for (const id of [...actors.keys()]) layer.remove(id);
      group.removeFromParent();
    },
  };
  return layer;
}

/**
 * THE SCENE PATH. Reads `humans/instances/<scene>/index.json` (a static host cannot be
 * globbed, so the scene's set is published as data, as the sidecar index is) and every record
 * it names, binds each to its person, and stands in the engine only the ones that may be drawn.
 *
 * `dataBase` null — the scene does not list `humans` — fetches nothing. A record is kept and
 * not drawn when it is `withheld`, when L1 is in force, when it drops person review metadata, when its
 * person does not resolve, or when its person already stands. Every refusal but `withheld`
 * (which is what a record says when it wants nothing drawn) is a line in `problems`.
 */
export async function mountHumans({
  dataBase = null, assetBase, assets = null, sceneId, people = null, getPeople = null, terrain = null, tier = 'full',
  problems = [], fetchImpl = fetch, contract = null, groundHeight = null, prepare = null,
} = {}) {
  const heightAt = groundHeight ?? (terrain ? (e, n) => terrain.surfaceHeight(e, n) : () => 0);
  const layer = createHumanLayer({ assetBase, assets, heightAt, tier, prepare });
  const out = Object.assign(layer, { records: [], withheld: [], refused: [] });
  if (!dataBase) return out;

  const getJson = async (rel) => {
    const res = await fetchImpl(new URL(rel, dataBase), { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${rel}: ${res.status} ${res.statusText}`);
    return res.json();
  };
  let index;
  let rules = contract;
  try {
    [index, rules] = await Promise.all([
      getJson(`humans/instances/${sceneId}/index.json`),
      rules ? Promise.resolve(rules) : getJson('humans/contract.json'),
    ]);
  } catch (err) {
    problems.push(`humans: the scene lists the layer and its instance index did not load (${err.message}) — nobody is drawn`);
    return out;
  }
  const byId = new Map((Array.isArray(people?.people) ? people.people : []).map((p) => [p.id, p]));
  const l1 = rules?.l1?.in_force !== false;
  const ids = Array.isArray(index.instances) ? index.instances : [];
  const records = await Promise.all(ids.map((id) => getJson(`humans/instances/${sceneId}/${id}.json`)
    .catch((err) => { problems.push(`humans: ${id} did not load (${err.message})`); return null; })));
  // A scene whose directory loads lazily (1904 lists no `residents`, T-3423) passes `getPeople`:
  // it is read only when a record names a person the eager list does not hold, and only the
  // rows the records name are kept from it.
  const wanted = new Set(records.filter(Boolean).map(r => r.person_id).filter(id => id && !byId.has(id)));
  if (getPeople && wanted.size) {
    try {
      const directory = await getPeople();
      for (const p of Array.isArray(directory?.people) ? directory.people : []) if (wanted.has(p.id)) byId.set(p.id, p);
    } catch (err) { problems.push(`humans: the people directory did not load (${err.message})`); }
  }
  const profiles = new Map();
  for (const id of new Set(records.filter(Boolean).map(r => r.anonymous_profile_id).filter(Boolean))) {
    if (!/^anonymous_[a-z0-9_]+$/.test(id)) continue;
    try { const profile = await getJson(`humans/role_profiles/${id}.json`); if (profile.id === id) profiles.set(id, profile); }
    catch (err) { problems.push(`humans: anonymous profile ${id} did not load (${err.message})`); }
  }
  for (const rec of records.filter(Boolean)) {
    out.records.push(rec);
    const refuse = (why) => { out.refused.push({ id: rec.id, why }); problems.push(`humans: ${rec.id} is not drawn — ${why}`); };
    let identity;
    try { identity = resolveHumanIdentity(rec, { sceneId, people: [...byId.values()], profiles: [...profiles.values()] }); }
    catch (err) { refuse(err.message); continue; }
    const person = identity.person;
    if (person && (person.review_required || person.touches_removal) && !rec.review_required) refuse('its person carries review metadata that the instance dropped');
    else if (rec.display !== 'shown') out.withheld.push(rec.id);
    else if (l1) refuse('L1 is in force (data/humans/contract.json § l1): no human figure is drawn');
    else if (layer.get(rec.id) || (rec.person_id && layer.get(rec.person_id))) refuse('instance identity already stands in this scene');
    else layer.add(rec, { person, profile: identity.profile, identity });
  }
  return out;
}
