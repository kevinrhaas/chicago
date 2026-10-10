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
 *                       the scene (§ 11) and hands the engine only those it may draw: L1 stands
 *                       (`contract.json § l1.in_force`), so today that is none of them. A scene
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
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { loadMeshoptDecoder, disposeLoadedAsset } from './scene-loader.js';
import { enuToWorld } from './terrain.js';

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

/** § 7: the clip a state plays when the record names none the asset carries. */
const STATE_CLIPS = {
  standing: ['idle'], walking: ['walk'], talking: ['talk', 'idle'],
  working: ['work', 'idle'], seated: ['sit', 'idle'],
};
const FADE_S = 0.25;
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
export function createHumanAssets({ assetBase, loader = new GLTFLoader(), fetchImpl = fetch } = {}) {
  const entries = new Map();
  let decoder = null;
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
      e.gltf.then(disposeLoadedAsset, () => {});
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
  constructor({ instance, person = null, assets, heightAt = () => 0, clipLibrary = [], tier = 'full' }) {
    this.instance = instance;
    this.person = person;
    this.personId = instance.person_id;
    this.id = instance.id;
    this.assets = assets;
    this.heightAt = heightAt;
    this.tier = tier;
    this.state = instance.behaviour?.state ?? 'standing';
    this.root = new THREE.Group();
    this.root.name = `human:${instance.id}`;
    this.root.userData.personId = this.personId;
    this.proxy = new THREE.Mesh(PROXY_GEOMETRY, PROXY_MATERIAL);
    // Never submitted (a raycast tests layers, not visibility), so it is never uploaded either.
    this.proxy.visible = false;
    this.proxy.userData.actor = this;
    this.root.add(this.proxy);
    this.libraryClips = clipLibrary;
    this.lod = -1;
    this.wanted = -1;
    this.body = null;           // { lod, scene, meshes, mixer, clips, actions, faces }
    this.pending = null;
    this.clipName = null;
    this.phase = instance.animation?.phase ?? 0;
    this.costs = '';
    this.counters = { updates: 0, animated: 0, faced: 0, swaps: 0 };
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
    this.place();
  }

  /** Where it stands, in local ENU metres, with its feet on the ground. */
  get position() { return { e: this.e, n: this.n, y: this.root.position.y }; }

  place() {
    enuToWorld(this.e, this.n, this.heightAt(this.e, this.n), this.root.position);
    this.root.rotation.y = headingToYaw(this.heading);
  }

  /** Load (or switch to) `lod`. Resolves when it is drawn; the previous LOD stays up until then. */
  async setLod(lod) {
    if (this.disposed || lod === this.lod || lod === this.wanted) return this.pending ?? this.body;
    this.wanted = lod;
    const assetId = this.instance.appearance.asset_id;
    const job = this.assets.acquire(assetId, lod).then((gltf) => {
      if (this.disposed || this.wanted !== lod) { this.assets.release(assetId, lod); return this.body; }
      const next = this.build(gltf, lod);
      const prev = this.body;
      // The new LOD takes up the clip where the old one was, so a swap is not a stumble.
      const time = prev?.action ? prev.action.time : null;
      this.body = next;
      this.lod = lod;
      this.root.add(next.scene);
      this.play(this.clipName ?? this.defaultClip(), { fade: 0, time });
      if (prev) { this.counters.swaps++; this.teardown(prev); }
      this.costs = '';
      this.applyCosts();
      this.applyFace(this.expression);
      return next;
    }, (err) => { if (this.wanted === lod) this.wanted = this.lod; throw err; });
    this.pending = job;
    job.finally(() => { if (this.pending === job) this.pending = null; }).catch(() => {});
    return job;
  }

  build(gltf, lod) {
    const scene = cloneSkinned(gltf.scene);
    const meshes = [];
    scene.traverse((o) => {
      if (!o.isSkinnedMesh) return;
      meshes.push(o);
      o.frustumCulled = false;    // a skinned bound is the rest pose's, not the walk's
    });
    // Measured through the node transforms: a quantised derivative's positions are not metres.
    scene.updateMatrixWorld(true);
    const height = new THREE.Box3().setFromObject(scene).max.y;
    this.proxy.scale.y = height > 0.3 ? height : 1.7;
    const clips = new Map();
    for (const c of gltf.animations ?? []) clips.set(c.name, c);
    for (const c of this.libraryClips) if (!clips.has(c.name)) clips.set(c.name, c);
    // § 6: the face, where this LOD carries one. lod2/lod3 may not, and then it holds still.
    const faces = meshes.filter((m) => m.morphTargetDictionary && Object.keys(m.morphTargetDictionary).length);
    const mixer = new THREE.AnimationMixer(scene);
    mixer.addEventListener('finished', (ev) => { if (ev.action === this.body?.oneShot) this.endGesture(); });
    return { lod, scene, meshes, faces, mixer, clips, action: null, oneShot: null, assetId: this.instance.appearance.asset_id };
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
    const named = this.instance.animation?.clip;
    if (named && this.body && findClip(this.body.clips, named)) return named;
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

  /** Advance along a walking route at the walk clip's stated ground speed (§ 7: in place). */
  walk(dt) {
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
  update(dt, cameraPosition) {
    if (this.disposed) return false;
    this.recheck -= dt;
    if (!this.inRange && this.recheck > 0) return false;
    this.distance = cameraPosition.distanceTo(this.root.position);
    const lod = chooseHumanLod(this.distance, this.tier, this.lod, this.instance.lod);
    this.inRange = lod >= 0;
    if (!this.inRange) {
      this.root.visible = false;
      this.recheck = RECHECK_S;
      return false;
    }
    this.counters.updates++;
    this.root.visible = !!this.body;
    if (lod !== this.lod && lod !== this.wanted) this.setLod(lod).catch(() => {});
    this.walk(dt);
    const b = this.body;
    if (!b) return true;
    if (this.distance < ANIMATE_M) {
      b.mixer.update(dt);
      this.counters.animated++;
    }
    if (this.distance < FACE_M && b.faces.length) {
      // A slow, deterministic blink, so a near face is alive and a still one is a choice.
      this.blinkClock += dt;
      const t = this.blinkClock % 4;
      const w = t < 0.15 ? Math.sin((t / 0.15) * Math.PI) : 0;
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
export function createHumanLayer({ assetBase, assets = null, heightAt = () => 0, tier = 'full', clipLibrary = [] } = {}) {
  const group = new THREE.Group();
  group.name = 'humans';
  const events = new EventTarget();
  const actors = new Map();
  const store = assets ?? createHumanAssets({ assetBase });
  const raycaster = new THREE.Raycaster();
  const near = new Set();
  let hovered = null;

  const detail = (actor) => ({
    personId: actor.personId, instanceId: actor.id, state: actor.state,
    opens: actor.instance.interaction?.opens ?? 'none', person: actor.person,
  });
  const emit = (type, actor) => events.dispatchEvent(new CustomEvent(type, { detail: detail(actor) }));

  const layer = {
    group,
    events,
    assets: store,
    on(type, fn) { events.addEventListener(type, (ev) => fn(ev.detail)); return layer; },
    get count() { return actors.size; },
    get actors() { return [...actors.values()]; },
    get(personId) { return [...actors.values()].find((a) => a.personId === personId) ?? null; },

    /** Stand one figure in the group. Refuses a second instance of one person (§ 11). */
    add(instance, { person = null } = {}) {
      if (actors.has(instance.id) || layer.get(instance.person_id)) {
        throw new Error(`humans: ${instance.person_id} already stands in this scene`);
      }
      const actor = new HumanActor({ instance, person, assets: store, heightAt, clipLibrary, tier });
      actors.set(instance.id, actor);
      group.add(actor.root);
      return actor;
    },

    remove(id) {
      const a = actors.get(id) ?? layer.get(id);
      if (!a) return false;
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
    update(dt, camera, visitor = null) {
      if (!actors.size) return;
      const eye = camera.getWorldPosition ? camera.getWorldPosition(new THREE.Vector3()) : camera.position;
      const ve = visitor ? visitor.e : eye.x;
      const vn = visitor ? visitor.n : -eye.z;
      for (const a of actors.values()) {
        a.update(dt, eye);
        const r = a.instance.interaction?.radius_m;
        if (!r || !a.inRange) continue;
        const inside = Math.hypot(a.e - ve, a.n - vn) <= r;
        if (inside && !near.has(a)) {
          near.add(a);
          emit('approach', a);
          if (a.instance.interaction?.opens === 'resident_card') emit('open', a);
        } else if (!inside && near.has(a)) {
          near.delete(a);
          emit('leave', a);
        }
      }
    },

    /** The selectable, drawn figure under `ndc` (the crosshair when null), nearest first. */
    pickAt(ndc, camera) {
      if (!actors.size || !camera) return null;
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
      if (a.instance.interaction?.opens === 'resident_card') emit('open', a);
      return detail(a);
    },

    dispose() {
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
 * not drawn when it is `withheld`, when L1 is in force, when it is review_required, when its
 * person does not resolve, or when its person already stands. Every refusal but `withheld`
 * (which is what a record says when it wants nothing drawn) is a line in `problems`.
 */
export async function mountHumans({
  dataBase = null, assetBase, assets = null, sceneId, people = null, terrain = null, tier = 'full',
  problems = [], fetchImpl = fetch, contract = null,
} = {}) {
  const heightAt = terrain ? (e, n) => terrain.surfaceHeight(e, n) : () => 0;
  const layer = createHumanLayer({ assetBase, assets, heightAt, tier });
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
  for (const rec of records.filter(Boolean)) {
    out.records.push(rec);
    const refuse = (why) => { out.refused.push({ id: rec.id, why }); problems.push(`humans: ${rec.id} is not drawn — ${why}`); };
    const person = byId.get(rec.person_id);
    if (String(rec.scene) !== String(sceneId)) refuse(`it is filed under ${sceneId} and says scene ${rec.scene}`);
    else if (!person) refuse(`its person ${rec.person_id} is not in sidecars/${sceneId}/people.json`);
    else if (rec.display !== 'shown') out.withheld.push(rec.id);
    else if (l1) refuse('L1 is in force (data/humans/contract.json § l1): no human figure is drawn');
    else if (rec.review_required) refuse('its person carries a standing review, and no review record exists yet');
    else if (layer.get(rec.person_id)) refuse(`${rec.person_id} already stands in this scene`);
    else layer.add(rec, { person });
  }
  return out;
}
