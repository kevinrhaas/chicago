/**
 * texture-residency.js — a house's pictures are on the GPU only where they can be seen
 * (T-2598, piece 2 of T-2554).
 *
 * Every texture a building's GLB carries was uploaded at boot and kept to the last
 * frame, wherever the visitor stood. On 1904 that is most of the tab: the structures
 * layer held 477 MB of the 582 MB of GPU textures the desktop reading measured
 * (T-2546), and the owner's programme refines about sixty more photographic houses.
 * A house 300 m down Prairie Avenue covers a few dozen pixels; its 2048² stone map is
 * sampled at a mip level of 64 texels or less there, and the 21 MB the level chain
 * costs above that buys nothing on the screen.
 *
 * So each picture a GLB brought in — a texture SOURCE, shared by every house built on
 * the same kit (shared-images.js) — is in one of two states:
 *
 *   resident ... its own texture, every mip, on the GPU;
 *   distant .... a STAND-IN in the same material slot: the same picture at 64 texels
 *                (an image downscaled once, at boot; a KTX2's own tail mips), with the
 *                same sampler, colour space and uv channel, so the shader program is
 *                the same one and nothing recompiles. The full texture is disposed:
 *                its GPU memory goes back.
 *
 * WHICH IS WHICH is decided by distance — from the camera to the nearest instance
 * bounding sphere of any batch drawing with the source — with HYSTERESIS (a distant
 * source comes back inside `enterM`, a resident one leaves beyond `leaveM`, so a
 * visitor standing on the boundary does not make it flicker), and then under a
 * BUDGET: the wanted sources are taken nearest first until `budgetBytes` is spent,
 * and anything past it stays distant however near it is. Both are per tier
 * (`RESIDENCY`), since a phone at `light` draws fewer pixels from a smaller budget.
 *
 * UPLOADS ARE PACED. A source coming back is uploaded with `renderer.initTexture` —
 * a `texImage2D` here rather than in the middle of a draw — at most `uploadBytesPerFrame`
 * a frame, nearest first, and at least one source a frame so a picture larger than the
 * frame's allowance still arrives. Its slots are switched back only once it is up, so
 * the stand-in is what draws in between, never a black or missing material.
 *
 * A PHONE CLOSES DECODED IMAGES (T-2548, upload-release.js), so a picture that went
 * distant there cannot be uploaded again from the page. Where the loader kept the
 * picture's ENCODED bytes (shared-images.js, `keepEncoded`) it is decoded again from
 * them through the GLB's own image loader, uploaded, and closed again; the encoded
 * bytes are what the page holds meanwhile, a JPEG's or PNG's size rather than four
 * bytes a texel. A picture with no encoded copy is never closed here.
 * A PHONE LETS GO OF A KTX2's TRANSCODED LEVELS TOO (T-2828). They stayed in the page
 * after upload, so every GLB KTX2 was held twice, as image bitmaps were before T-2548:
 * 63 MB of the 1904 phone's 124 MB of ArrayBuffers at the Glessner front, beside the
 * same 63 MB on the GPU. Once every texture of a source is uploaded — or at once, for a
 * source that is distant and drawn by its stand-in — each level's bytes are replaced by
 * an empty array, and the source leaves the shared cache (a GLB parsed later transcodes
 * its own). Coming back, the source is transcoded again from the KTX2 file its GLB
 * carried (`keepEncoded`, about a tenth of the levels), uploaded, and let go again.
 *
 * WHAT DOES NOT CHANGE. Placement, picking (gpu-pick.js reads ids, not textures), the
 * card and the confidence view never read residency. Doctrine 5: a tier does not
 * degrade the reconstruction — this changes only what is UPLOADED at a distance where
 * the full picture could not be resolved, and a stand-in is that picture's own small
 * mip, not a substitute. `?residency=0` turns it off, which is how the before is read.
 */

import * as THREE from 'three';
import { glbImageSource, retireSharedImage } from './shared-images.js';
import { noteReleasedLevels } from './upload-release.js';

const MiB = 1048576;

/** The stand-in's longest side, in texels. */
export const STAND_IN_TEXELS = 64;

/**
 * Per tier. `full` and `balanced` share a desktop's figures; `light` is a phone's.
 * The radii are where the full picture can first matter: at `leaveM` a house of 20 m
 * spans about 120 px of a 1280 px desktop view (50° fov), which samples its kit maps
 * (tiled several times across a facade) at or below their 64-texel mip; a phone at
 * `light` draws at pixel ratio 1 on 390 px and reaches the same footprint nearer.
 * The budgets are argued in docs/SITE-BUDGET.md § texture residency with the walk's
 * reading (tools/measure_memory.mjs --walk prairie).
 */
export const RESIDENCY = {
  full: { enterM: 160, leaveM: 200, budgetBytes: 512 * MiB, uploadBytesPerFrame: 16 * MiB },
  balanced: { enterM: 160, leaveM: 200, budgetBytes: 512 * MiB, uploadBytesPerFrame: 16 * MiB },
  light: { enterM: 70, leaveM: 90, budgetBytes: 256 * MiB, uploadBytesPerFrame: 4 * MiB },
};

/** What the GPU holds for one texture of this source, every level. */
function sourceBytes(texture) {
  if (texture.isCompressedTexture) {
    let sum = 0;
    for (const level of texture.mipmaps ?? []) sum += level?.data?.byteLength ?? 0;
    return sum;
  }
  const image = texture.image;
  const w = image?.width ?? 0;
  const h = image?.height ?? 0;
  return Math.round(w * h * 4 * (texture.generateMipmaps ? 4 / 3 : 1));
}

/** What a released KTX2 level holds: nothing, and an upload of it is a GL error, not a throw. */
const RELEASED = new Uint8Array(0);

const isBitmap = (image) => typeof ImageBitmap !== 'undefined' && image instanceof ImageBitmap;
/** A closed ImageBitmap reports 0 × 0: three cannot upload from it. */
const isClosed = (image) => isBitmap(image) && (image.width === 0 || image.height === 0);

/**
 * The picture at `STAND_IN_TEXELS`, as the same kind of texture with the same sampler.
 * Null when there is nothing to make it from (a closed bitmap, a KTX2 with no tail mip),
 * in which case the source simply stays resident.
 */
function makeStandIn(texture) {
  if (texture.isCompressedTexture) {
    const levels = (texture.mipmaps ?? []).filter((m) => m && Math.max(m.width, m.height) <= STAND_IN_TEXELS);
    if (!levels.length || levels.length === texture.mipmaps.length) return null;
    const stand = texture.clone();
    stand.source = new THREE.Source({ width: levels[0].width, height: levels[0].height });
    stand.mipmaps = levels.map((m) => ({ data: m.data.slice(), width: m.width, height: m.height }));
    stand.needsUpdate = true;
    return stand;
  }
  const image = texture.image;
  if (!image || isClosed(image) || !(image.width > 0 && image.height > 0)) return null;
  if (typeof document === 'undefined') return null;
  const scale = Math.min(1, STAND_IN_TEXELS / Math.max(image.width, image.height));
  // Powers of two, so the stand-in mipmaps under any sampler the source used.
  const pow2 = (v) => 2 ** Math.max(0, Math.round(Math.log2(Math.max(1, v))));
  const w = pow2(image.width * scale);
  const h = pow2(image.height * scale);
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(image, 0, 0, w, h);
  const stand = texture.clone();
  stand.source = new THREE.Source(canvas);
  stand.needsUpdate = true;
  return stand;
}

/** Decode a source again from the bytes its GLB carried, with that GLB's own loader. */
function redecode(encoded) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(new Blob([encoded.view], { type: encoded.mimeType }));
    const done = (fn) => (value) => { URL.revokeObjectURL(url); fn(value); };
    // A KTX2 comes back as the texture its loader transcoded: the caller takes its levels.
    encoded.imageLoader.load(url, done((got) => resolve(got?.isCompressedTexture ? got
      : got?.isTexture ? got.image : got)),
      undefined, done(reject));
  });
}

/** A source GLTF needs a fresh parse before rebuilding if its uploaded compressed
 * payloads were released. Inspect the actual arrays: a source texture clone can
 * share released descriptors without carrying the batch texture's userData marker.
 */
export function hasReleasedTextureLevels(gltf) {
  let released = false;
  gltf?.scene?.traverse?.((node) => {
    if (released) return;
    for (const material of [].concat(node.material ?? [])) {
      for (const value of Object.values(material ?? {})) {
        if (value?.isCompressedTexture && value.mipmaps?.some((level) => level?.data?.byteLength === 0)) {
          released = true;
        }
      }
    }
  });
  return released;
}

/** Required texture-slot multiplicities for one unchanged source asset. Compare
 * stable node/material ordinals, material names and slot keys, never runtime IDs
 * or compressed format choices.
 */
export function hasRequiredSourceTextures(previous, replacement) {
  const slots = (gltf) => {
    const counts = new Map();
    let ordinal = 0;
    gltf?.scene?.traverse?.((node) => {
      const nodeOrdinal = ordinal++;
      for (const [materialIndex, material] of [].concat(node.material ?? []).entries()) {
        for (const [slot, value] of Object.entries(material ?? {})) {
          if (!value?.isTexture) continue;
          const key = JSON.stringify([nodeOrdinal, materialIndex, material.name ?? '', slot]);
          counts.set(key, (counts.get(key) ?? 0) + 1);
        }
      }
    });
    return counts;
  };
  const fresh = slots(replacement);
  return [...slots(previous)].every(([key, count]) => (fresh.get(key) ?? 0) >= count);
}

/**
 * @param {object} o
 * @param {THREE.Object3D} o.group       the structures group (buildings.js)
 * @param {THREE.WebGLRenderer} o.renderer
 * @param {string} o.tier                'full' | 'balanced' | 'light'
 * @param {boolean} o.releaseCompressedLevels  release uploaded compressed source arrays
 *                                       on any device; requires encoded bytes for refill.
 * @param {boolean} o.closeImages        a phone: close a distant source's bitmap when
 *                                       its encoded bytes were kept, and close a
 *                                       re-decoded one once it is uploaded again; let
 *                                       go of a KTX2's transcoded levels likewise
 */
export function createTextureResidency({ group, renderer, tier = 'full', closeImages = false,
  releaseCompressedLevels = closeImages, settings = null } = {}) {
  const cfg = {};
  const tierSettings = (t) => ({ ...(RESIDENCY[t] ?? RESIDENCY.full), ...(settings ?? {}) });
  Object.assign(cfg, tierSettings(tier));
  /** source -> entry */
  const entries = new Map();
  const sphere = new THREE.Sphere();
  const matrix = new THREE.Matrix4();
  const problems = [];

  group.updateWorldMatrix(true, true);
  // Every GLB picture the batches draw with, every slot that reads it, and the
  // instances whose distance decides it.
  group.traverse((o) => {
    if (!o.isMesh) return;
    const materials = [].concat(o.material ?? [], o.customDepthMaterial ?? [], o.customDistanceMaterial ?? []);
    const spheres = [];
    const addSphere = () => {
      sphere.applyMatrix4(o.matrixWorld);
      spheres.push(sphere.center.x, sphere.center.y, sphere.center.z, sphere.radius);
    };
    let measured = false;
    for (const material of materials) {
      for (const key of Object.keys(material)) {
        const tex = material[key];
        if (!tex?.isTexture || !tex.source || !glbImageSource(tex.source)) continue;
        if (!measured) {
          measured = true;
          if (o.isBatchedMesh) {
            // Every live instance, drawn or not this frame: the shadow pass and the
            // frustum toggle visibility, and neither says how far a house is.
            const slots = o._instanceInfo?.length ?? o.instanceCount;
            for (let i = 0; i < slots; i += 1) {
              if (o._instanceInfo && !o._instanceInfo[i]?.active) continue;
              let geometryId;
              try { geometryId = o.getGeometryIdAt(i); } catch { continue; }
              if (!(geometryId >= 0)) continue;
              o.getBoundingSphereAt(geometryId, sphere);
              sphere.applyMatrix4(o.getMatrixAt(i, matrix));
              addSphere();
            }
          } else {
            if (!o.geometry.boundingSphere) o.geometry.computeBoundingSphere();
            sphere.copy(o.geometry.boundingSphere);
            addSphere();
          }
        }
        let entry = entries.get(tex.source);
        if (!entry) {
          entry = { source: tex.source, textures: new Map(), spheres: [], bytes: 0,
            state: 'resident', distance: Infinity, decoding: null, encoded: glbImageSource(tex.source).encoded,
            compressed: !!tex.isCompressedTexture };
          entries.set(tex.source, entry);
        }
        if (!entry.textures.has(tex)) entry.textures.set(tex, { owners: [], standIn: null });
        entry.textures.get(tex).owners.push([material, key]);
        if (!entry.meshes) entry.meshes = new Set();
        if (!entry.meshes.has(o)) { entry.meshes.add(o); entry.spheres.push(...spheres); }
      }
    }
  });
  for (const entry of entries.values()) {
    entry.spheres = Float32Array.from(entry.spheres);
    // One GPU copy per source and sampler, as three uploads them: clones that sample
    // the picture the same way share one, and a clone with its own sampler is its own.
    const samplers = new Set();
    for (const tex of entry.textures.keys()) {
      const key = [tex.wrapS, tex.wrapT, tex.magFilter, tex.minFilter, tex.anisotropy, tex.format,
        tex.type, tex.colorSpace, tex.generateMipmaps, tex.flipY, tex.premultiplyAlpha].join(',');
      if (samplers.has(key)) continue;
      samplers.add(key);
      entry.bytes += sourceBytes(tex);
    }
  }

  const state = {
    tier, ...cfg, sources: entries.size, resident: entries.size, residentBytes: 0,
    allBytes: 0, peakResidentBytes: 0, pending: 0, uploads: 0, evictions: 0, redecodes: 0,
    standIns: 0, standInBytes: 0, encodedBytes: 0, wantedBytes: 0, overBudget: 0, problems,
    released: 0, releasedBytes: 0, retranscodes: 0,
  };
  for (const entry of entries.values()) {
    state.allBytes += entry.bytes;
    if (entry.encoded) state.encodedBytes += entry.encoded.view.byteLength;
  }

  // Prepare a stand-in before releasing its source: every decoded image on a
  // phone, or recoverable compressed levels on desktop. Regular desktop images
  // stay decoded; their stand-ins can be made lazily if distance later evicts them.
  for (const entry of entries.values()) {
    if (closeImages || (releaseCompressedLevels && entry.compressed && entry.encoded)) ensureStandIns(entry);
  }

  // T-2828: the KTX2 sources whose transcoded levels a phone still holds, and can let
  // go of because the file is kept to transcode them from again.
  const holding = new Set();
  if (releaseCompressedLevels) {
    for (const entry of entries.values()) if (entry.compressed && entry.encoded) holding.add(entry);
  }
  const uploaded = (tex) => {
    const p = renderer.properties.get(tex);
    return p.__webglTexture !== undefined && p.__version === tex.version;
  };

  /** Let go of every held source the GPU no longer needs the levels of. */
  function releaseLevels() {
    for (const entry of holding) {
      // Loading is about to upload; resident waits for every texture to be up.
      if (entry.state === 'loading' || entry.decoding) continue;
      if (entry.state === 'resident' && ![...entry.textures.keys()].every(uploaded)) continue;
      let bytes = 0;
      // What each texture's levels were, kept for a reader pricing the GPU copy
      // (resident-estimate.js, the memory meter's layer table).
      for (const tex of entry.textures.keys()) {
        tex.userData.releasedBytes = (tex.mipmaps ?? []).reduce((s, m) => s + (m?.data?.byteLength ?? 0), 0)
          || tex.userData.releasedBytes || 0;
      }
      for (const tex of entry.textures.keys()) {
        for (const level of tex.mipmaps ?? []) {
          if (!level?.data?.byteLength) continue;
          bytes += level.data.byteLength;
          level.data = RELEASED;
        }
      }
      retireSharedImage(entry.source.data);
      entry.released = true;
      holding.delete(entry);
      state.released += 1;
      state.releasedBytes += bytes;
      noteReleasedLevels(bytes);
    }
  }

  /** A released source's levels, transcoded again, put back where three reads them. */
  function refill(entry, fresh) {
    const levels = fresh?.mipmaps ?? [];
    let ok = true;
    for (const tex of entry.textures.keys()) {
      (tex.mipmaps ?? []).forEach((level, i) => {
        const got = levels[i];
        if (got && got.width === level.width && got.height === level.height) level.data = got.data;
        else ok = false;
      });
    }
    fresh?.dispose?.();
    if (!ok) problems.push('texture residency: a KTX2 transcoded again to different levels');
    entry.released = false;
    holding.add(entry);
    state.retranscodes += 1;
  }

  function distanceOf(entry, eye, flat) {
    const s = entry.spheres;
    let best = Infinity;
    for (let i = 0; i < s.length; i += 4) {
      const dx = s[i] - eye.x; const dy = flat ? 0 : s[i + 1] - eye.y; const dz = s[i + 2] - eye.z;
      const d = Math.sqrt(dx * dx + dy * dy + dz * dz) - s[i + 3];
      if (d < best) best = d;
    }
    return Math.max(0, best);
  }

  function ensureStandIns(entry) {
    for (const [tex, slot] of entry.textures) {
      if (slot.standIn) continue;
      slot.standIn = makeStandIn(tex);
      if (!slot.standIn) return false;
      state.standIns += 1;
      state.standInBytes += sourceBytes(slot.standIn);
    }
    return true;
  }

  /** Swap to the stand-ins and give the full textures' GPU memory back. */
  function evict(entry) {
    if (!ensureStandIns(entry)) return false;
    for (const [tex, slot] of entry.textures) {
      for (const [material, key] of slot.owners) material[key] = slot.standIn;
      tex.dispose();
    }
    const image = entry.source.data;
    if (closeImages && entry.encoded && isBitmap(image) && !isClosed(image)) {
      retireSharedImage(image);
      image.close();
    }
    entry.state = 'distant';
    state.evictions += 1;
    return true;
  }

  /** Upload the full textures (paced by the caller) and swap them back in. */
  function restore(entry) {
    for (const tex of entry.textures.keys()) renderer.initTexture(tex);
    for (const [tex, slot] of entry.textures) {
      for (const [material, key] of slot.owners) material[key] = tex;
    }
    const image = entry.source.data;
    if (closeImages && entry.encoded && entry.redecoded && isBitmap(image)) image.close();
    entry.redecoded = false;
    entry.state = 'resident';
    state.uploads += 1;
  }

  /** True when the source can be uploaded now; otherwise starts its decode. */
  function ready(entry) {
    const image = entry.source.data;
    if (entry.compressed ? !entry.released : !isClosed(image)) return true;
    if (!entry.encoded) return false;
    if (!entry.decoding) {
      entry.decoding = redecode(entry.encoded).then((fresh) => {
        entry.decoding = null;
        if (entry.compressed) {
          if (entry.state === 'loading') refill(entry, fresh);
          else fresh?.dispose?.();
          return;
        }
        if (entry.state !== 'loading') { if (isBitmap(fresh)) fresh.close(); return; }
        entry.source.data = fresh;
        entry.source.needsUpdate = true;
        entry.redecoded = true;
        state.redecodes += 1;
      }, (error) => {
        entry.decoding = null;
        entry.state = 'distant';
        problems.push(`texture residency: a picture did not decode again (${error?.message ?? error})`);
      });
    }
    return false;
  }

  let frame = 0;
  let override = null;
  const lastEye = new THREE.Vector3(Infinity, Infinity, Infinity);
  let queue = [];

  /**
   * Decide every source from where the eye is. `immediate` (the boot, before anything
   * is uploaded) evicts and restores without pacing.
   */
  function evaluate(eye, flat = false) {
    for (const entry of entries.values()) entry.distance = distanceOf(entry, eye, flat);
    const wanted = [...entries.values()]
      .filter((e) => e.distance < (e.state === 'resident' ? cfg.leaveM : cfg.enterM))
      .sort((a, b) => a.distance - b.distance);
    const keep = new Set();
    let sum = 0;
    // What the reach asks for, and how many of those the budget turned away, at this
    // decision — the walk's reading quotes both.
    state.wantedBytes = wanted.reduce((a, e) => a + e.bytes, 0);
    state.overBudget = 0;
    for (const entry of wanted) {
      if (sum + entry.bytes > cfg.budgetBytes) { state.overBudget += 1; continue; }
      keep.add(entry);
      sum += entry.bytes;
    }
    // Leave first, so what arrives never stacks on what is going.
    for (const entry of entries.values()) {
      if (keep.has(entry)) continue;
      if (entry.state === 'loading') entry.state = 'distant';
      else if (entry.state === 'resident' && !evict(entry)) keep.add(entry);
    }
    queue = [...keep].filter((e) => e.state !== 'resident')
      .sort((a, b) => a.distance - b.distance);
    for (const entry of queue) entry.state = 'loading';
  }

  function pump(immediate = false) {
    let spent = 0;
    let uploaded = 0;
    const rest = [];
    for (const entry of queue) {
      if (entry.state !== 'loading') continue;
      const allowed = immediate || uploaded === 0 || spent + entry.bytes <= cfg.uploadBytesPerFrame;
      if (allowed && ready(entry)) {
        restore(entry);
        spent += entry.bytes;
        uploaded += 1;
      } else {
        rest.push(entry);
      }
    }
    queue = rest;
  }

  function tally() {
    let resident = 0; let bytes = 0; let pending = 0;
    for (const entry of entries.values()) {
      if (entry.state === 'resident') { resident += 1; bytes += entry.bytes; }
      if (entry.state === 'loading') pending += 1;
    }
    state.resident = resident;
    state.residentBytes = bytes;
    state.pending = pending;
    state.peakResidentBytes = Math.max(state.peakResidentBytes, bytes);
  }

  return {
    state,
    /**
     * At boot, before the batches are uploaded: what is distant never goes up. `flat`
     * reads plan distance only, for an eye whose height is not known yet.
     */
    prime(eye, { flat = false } = {}) {
      evaluate(eye, flat);
      pump(true);
      if (holding.size) releaseLevels();
      lastEye.copy(eye);
      tally();
    },
    /** Every frame, before the draw. Re-decides when the eye has moved or every 30 frames. */
    tick(eye) {
      if (!entries.size) return;
      frame += 1;
      if (lastEye.distanceToSquared(eye) > 4 || frame % 30 === 0) {
        evaluate(eye);
        lastEye.copy(eye);
      }
      if (queue.length) pump(false);
      if (holding.size) releaseLevels();
      tally();
    },
    /** The detail tier changed: its reach and budget apply from the next frame. */
    setTier(next) {
      Object.assign(cfg, tierSettings(next), override ?? {});
      Object.assign(state, cfg, { tier: next });
      lastEye.set(Infinity, Infinity, Infinity);
    },
    /**
     * A tool's override of the tier's figures (`{ enterM, leaveM, budgetBytes }`), or
     * null to go back to them. `everything()` keeps every picture resident: the
     * capture comparison's "as before" (tools/measure_memory.mjs --captures).
     */
    override(patch) {
      override = patch;
      this.setTier(state.tier);
    },
    async everything() {
      this.override({ enterM: Infinity, leaveM: Infinity, budgetBytes: Infinity });
      // Unpaced: a capture tool wants the before now, not a frame at a time. A phone's
      // closed pictures decode first.
      evaluate(lastEye.x === Infinity ? new THREE.Vector3() : lastEye);
      await Promise.all([...entries.values()].map((e) => (ready(e) ? null : e.decoding)));
      pump(true);
      tally();
    },
    /** Put every full texture back in its slot (the batches are being retired). */
    dispose() {
      for (const entry of entries.values()) {
        for (const [tex, slot] of entry.textures) {
          for (const [material, key] of slot.owners) material[key] = tex;
          slot.standIn?.dispose();
          slot.standIn = null;
        }
      }
      entries.clear();
      queue = [];
    },
  };
}
