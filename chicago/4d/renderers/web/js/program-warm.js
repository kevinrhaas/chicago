// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * program-warm.js — nothing is drawn before its program is built (T-3728).
 *
 * Bill's PC (Intel UHD 630, ANGLE on D3D11), profiled 2026-11-22: once the railway and the
 * brougham's glass were fixed, the first jaunt of a visit still froze about 6 s, and boot had
 * tasks of 2 to 6 s, all in getProgramInfoLog. A material drawn for the first time (a stage's
 * people and props, the buildings, yards and railway of the place a jaunt flies to) has its
 * program linked by the draw itself, and the draw then waits on the link: one frame stands
 * still for every program the new place needs, on a GPU that links slowly.
 *
 * The boot already builds the town's programs with `compileAsync` before its first frame
 * (main.js), and a person's new level is built the same way (humans.js `prepare`). This is the
 * same for everything else: an object of the world whose material has no ready program is left
 * out of that frame, its program is started off the frame (KHR_parallel_shader_compile: the
 * link runs on the driver's own threads and is polled, never waited on), and it is drawn from
 * the frame its program is ready, a frame or a few later. What is drawn is unchanged; only the
 * moment a new thing first appears moves, by those frames.
 *
 * A material whose program is about to change under it (a jaunt's season patches every
 * building, yard and railway material the first time it is not summer: season.js) is not held
 * back, which would empty the town for as long as the links take: `rekey` builds the changed
 * programs first, on copies of the materials, and makes the change only once they are ready.
 * Until then the town draws with the programs it has.
 *
 * Only where the GPU can link in parallel: without the extension a link is waited on wherever
 * it is started, so holding the draw back would buy nothing (software renderers, the harness).
 * Only the world's own draws with the object's own material: a shadow's depth pass, a pick
 * pass, an override and a bake into another scene are drawn as they always were. A material
 * still not ready after GIVE_UP_MS is drawn anyway, as before this.
 */

const GIVE_UP_MS = 4000;

/**
 * @param {THREE.WebGLRenderer} renderer
 * @param {{ scene: THREE.Scene, camera: THREE.Camera, enabled?: boolean }} options
 * @returns {{ active: boolean, counters: object, rekey(changes: Map): Promise<void>, dispose(): void }}
 */
export function warmBeforeDraw(renderer, { scene, camera: worldCamera = null, enabled = true } = {}) {
  const counters = { deferredDraws: 0, warmed: 0, gaveUp: 0, failed: 0, batches: 0 };
  const active = !!(enabled && scene && renderer?.extensions?.has?.('KHR_parallel_shader_compile'));
  /** Without parallel links there is nothing to build ahead: the changes are made at once. */
  const changeNow = async (changes) => { for (const [m, c] of changes) c.change(m); };
  if (!active) return { active, counters, rekey: changeNow, dispose() {} };

  const properties = renderer.properties;
  const draw = renderer.renderBufferDirect;
  const waiting = new Map();      // material -> first time it was held back
  const drawAnyway = new WeakSet(); // materials whose compile failed or took too long
  const queued = new Set();       // objects to compile at the next flush
  const compiling = new WeakSet(); // objects whose compile is in flight
  let camera = worldCamera, flushing = false;

  const owns = (object, material) => object.material === material
    || (Array.isArray(object.material) && object.material.includes(material));
  const ready = (material) => {
    const program = properties.get(material).currentProgram;
    return !!program && program.isReady();
  };

  function flush() {
    flushing = false;
    if (shadowQueue.length) flushShadows();
    const list = [...queued];
    queued.clear();
    if (!list.length || !camera) return;
    for (const o of list) compiling.add(o);
    counters.batches += 1;
    // compile() walks `root` for meshes and for lights; the world's lights come from `scene`.
    const root = {
      traverse(cb) { for (const o of list) cb(o); },
      traverseVisible(cb) { for (const o of list) if (o.visible) cb(o); },
    };
    const done = (ok) => {
      for (const o of list) {
        compiling.delete(o);
        for (const m of [].concat(o.material)) {
          if (!m) continue;
          if (!ok) drawAnyway.add(m);
          if (waiting.delete(m)) counters.warmed += ok ? 1 : 0;
        }
      }
      if (!ok) counters.failed += 1;
    };
    let job;
    try { job = renderer.compileAsync(root, camera, scene); } catch { done(false); return; }
    job.then(() => done(true), () => done(false));
  }

  /*
   * T-3728, second pass (Bill's PC, 2026-11-23): the sun's shadow. Its depth pass draws with
   * three's own depth materials (scene null), which the boot's `compileAsync` never builds, so
   * the first shadow frame linked a dozen depth programs inside it: the 1.4-2.3 s pause after
   * boot. A caster whose depth program is not ready is left out of that shadow refresh and its
   * program built off the frame, as for the world's own draws: a copy of the depth material in
   * the state three set for this caster, on the caster itself (Object.create), compiled against
   * the shadow map's own target and in no scene, which is what decides the program's key (no
   * tone mapping, the working colour space, no fog). One check per kind of caster and depth
   * state, not per caster.
   */
  const shadowChecks = new Map();   // signature -> { clone, program, since, ready, queued }
  const shadowSeen = new WeakMap(); // caster -> { material, side, map, alphaTest, check }
  const shadowQueue = [];
  let shadowTarget = null;
  const lights = [];
  const lightsOnly = { traverseVisible(cb) { for (const l of lights) cb(l); } };
  const builtIn = (m) => m.onBeforeCompile === Object.getPrototypeOf(m).onBeforeCompile
    && !Object.prototype.hasOwnProperty.call(m, 'customProgramCacheKey');
  const shadowSignature = (o, m) => [m.type, builtIn(m) ? '' : m.uuid, m.side, m.map ? m.map.channel : -1,
    m.alphaTest > 0 ? 1 : 0, m.alphaMap ? m.alphaMap.channel : -1, m.displacementMap ? 1 : 0,
    m.clipShadows ? m.clippingPlanes?.length ?? 0 : 0, m.depthPacking ?? -1, m.wireframe ? 1 : 0,
    o.isBatchedMesh ? (o._colorsTexture ? 2 : 1) : 0,
    o.isInstancedMesh ? (o.instanceColor ? 2 : 1) + (o.morphTexture ? 4 : 0) : 0, o.isSkinnedMesh ? 1 : 0,
    o.geometry?.morphAttributes?.position?.length ?? 0, o.geometry?.morphAttributes?.normal?.length ?? 0,
    o.geometry?.morphAttributes?.color?.length ?? 0].join('|');
  function shadowCheckFor(o, m) {
    const seen = shadowSeen.get(o);
    if (seen && seen.material === m && seen.side === m.side && seen.map === m.map && seen.alphaTest === m.alphaTest) return seen.check;
    const sig = shadowSignature(o, m);
    let check = shadowChecks.get(sig);
    if (!check) {
      let clone = null;
      try {
        clone = m.clone();
        clone.onBeforeCompile = m.onBeforeCompile;
        if (Object.prototype.hasOwnProperty.call(m, 'customProgramCacheKey')) clone.customProgramCacheKey = m.customProgramCacheKey;
      } catch { clone = null; }
      check = { clone, program: null, since: performance.now(), ready: !clone, stand: null };
      if (clone) { check.stand = Object.create(o, { material: { value: clone, writable: true } }); shadowQueue.push(check); }
      shadowChecks.set(sig, check);
    }
    shadowSeen.set(o, { material: m, side: m.side, map: m.map, alphaTest: m.alphaTest, check });
    return check;
  }
  function flushShadows() {
    const list = shadowQueue.splice(0);
    if (!list.length || !camera || !shadowTarget) { for (const c of list) c.ready = true; return; }
    counters.shadowBatches = (counters.shadowBatches ?? 0) + 1;
    const before = renderer.getRenderTarget(), face = renderer.getActiveCubeFace(), mip = renderer.getActiveMipmapLevel();
    try {
      renderer.setRenderTarget(shadowTarget);
      const root = { traverse(cb) { for (const c of list) cb(c.stand); }, traverseVisible(cb) { for (const c of list) cb(c.stand); } };
      // The depth pass draws in no scene (three's empty one: no fog, which keys a program even
      // where the material draws none) under the world's lights: the same lights, on their own.
      lights.length = 0;
      scene.traverseVisible((o) => { if (o.isLight) lights.push(o); });
      renderer.compile(root, camera, lightsOnly);
      for (const c of list) { c.program = properties.get(c.clone).currentProgram ?? null; c.since = performance.now(); if (!c.program) c.ready = true; }
    } catch { for (const c of list) c.ready = true; }
    finally { renderer.setRenderTarget(before, face, mip); }
  }
  function holdShadow(material, object) {
    const check = shadowCheckFor(object, material);
    if (check.ready) return false;
    if (check.program) {
      if (check.program.isReady() || performance.now() - check.since > GIVE_UP_MS) {
        check.ready = true;
        counters.shadowWarmed = (counters.shadowWarmed ?? 0) + 1;
        return false;
      }
    } else {
      shadowTarget = renderer.getRenderTarget();
      if (!flushing) { flushing = true; queueMicrotask(flush); }
    }
    counters.shadowHeld = (counters.shadowHeld ?? 0) + 1;
    return true;
  }

  renderer.renderBufferDirect = function warmedDraw(cam, drawScene, geometry, material, object, group) {
    if (drawScene === null && object && material && (material.isMeshDepthMaterial || material.isMeshDistanceMaterial)
      && holdShadow(material, object)) return undefined;
    if (drawScene === scene && object && material && !drawAnyway.has(material) && owns(object, material)
      && !ready(material)) {
      const now = performance.now();
      const since = waiting.get(material);
      if (since === undefined) waiting.set(material, now);
      if (since === undefined || now - since < GIVE_UP_MS) {
        counters.deferredDraws += 1;
        camera = cam;
        if (!compiling.has(object)) queued.add(object);
        // After this render returns: compile() resets the render state a draw is using.
        if (!flushing) { flushing = true; queueMicrotask(flush); }
        return undefined;
      }
      waiting.delete(material); drawAnyway.add(material); counters.gaveUp += 1;
    }
    return draw.call(this, cam, drawScene, geometry, material, object, group);
  };

  return {
    active,
    counters,
    /**
     * `changes`: Map of material -> { change(material), objects: [the meshes drawing it] }. Each
     * change is first made to a copy of its material (the same hooks, so the same program key
     * the changed material will ask for), the copies' programs are built off the frame as the
     * objects would draw them, and only then is each change made to the material itself: its
     * next draw finds its program built. A material that cannot be copied is changed with the
     * rest, as before this. Resolves once every change is made.
     */
    async rekey(changes) {
      const stand = [], copies = [];
      for (const [m, c] of changes) {
        let copy;
        try {
          copy = m.clone();
          copy.onBeforeCompile = m.onBeforeCompile;
          copy.onBeforeRender = m.onBeforeRender;
          if (Object.prototype.hasOwnProperty.call(m, 'customProgramCacheKey')) copy.customProgramCacheKey = m.customProgramCacheKey;
          c.change(copy);
        } catch { copy?.dispose?.(); continue; }
        copies.push(copy);
        // The mesh as it is, drawing the copy: what decides its program (batching, instancing,
        // skinning, shadows received) is read through to the mesh itself.
        for (const o of c.objects ?? []) stand.push(Object.create(o, { material: { value: copy, writable: true } }));
      }
      counters.rekeyed = (counters.rekeyed ?? 0) + copies.length;
      if (stand.length && camera) {
        const root = { traverse(cb) { for (const o of stand) cb(o); }, traverseVisible(cb) { for (const o of stand) cb(o); } };
        try { await renderer.compileAsync(root, camera, scene); } catch { /* the draws compile what is missing */ }
      }
      for (const [m, c] of changes) { try { c.change(m); } catch { /* as it would have failed before */ } }
      // The copies hold the built programs until the materials themselves have drawn with them
      // (three keeps a program while anything uses it), then go.
      setTimeout(() => { for (const copy of copies) copy.dispose(); }, 60_000);
    },
    dispose() { if (renderer.renderBufferDirect !== draw) renderer.renderBufferDirect = draw; },
  };
}
