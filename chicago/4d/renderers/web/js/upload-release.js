/**
 * upload-release.js — a phone keeps the town on the GPU, not twice.
 *
 * T-2158. Every vertex three.js draws is held twice: once in the page, in the
 * typed array the layer built, and once on the GPU, where `bufferData` copied
 * it. The page copy is only read again by code that re-reads geometry — a
 * pick, the far merge, a layer that rewrites its own colours — and on 1835 it
 * came to about 360 MB of a phone tab that iOS kills at the end of the load.
 *
 * So on a phone, each listed layer lets go of the page copy the moment three
 * has uploaded it (`BufferAttribute.onUpload`, the hook three provides for
 * exactly this). Nothing on screen changes: the GPU buffer is the one that was
 * always drawn. What is kept is what something still reads:
 *
 *  - `position` (and the index) of a layer that answers a tap by raycasting
 *    the chunk's own triangles — today only `structures` (and the uv and
 *    normal three would interpolate at the hit are set aside for the raycast —
 *    no pick reads them). The plank walks, fences and yard goods are picked by
 *    a one-pixel id pass on the GPU instead (gpu-pick.js, T-2572), so they keep
 *    nothing;
 *  - any attribute uploaded as DYNAMIC, because its layer rewrites it (the
 *    frontage's far walk index, the horizon's timber), and the whole geometry
 *    of anything whose position is dynamic;
 *  - every bounding volume, computed before the position can go, so the
 *    frustum never needs it again;
 *  - a BatchedMesh's index, whose element size three reads on every draw;
 *  - a geometry flagged `userData.rereadBeforeRelease`, which its layer will
 *    rebuild from its own arrays after this upload — the terrain's far base,
 *    which `batchDistantGround()` cuts into pieces once the frontage has
 *    protected it (T-2180). Its replacement is not flagged, so the next pass
 *    lets that one go as usual.
 *
 * The far merge reads chunk arrays to build a cluster; a cluster of released
 * chunks refuses and stays chunked (far-merge.js), which at `light` — the
 * phone's tier — never merges anything anyway.
 *
 * A lost WebGL context would need the page copies to re-upload. iOS drops a
 * context under memory pressure, so if one is lost after anything was let go,
 * the page reloads on restore rather than drawing nothing — once a session, and
 * never in a loop: crash-guard.js owns the context events (T-2547) and reads
 * `uploadReleaseState().attributes` to know whether a reload is needed.
 */

import * as THREE from 'three';
import { isSharedImage, retireSharedImage } from './shared-images.js';

/** Layer → attributes it must keep for a tap. Unlisted layers keep nothing. */
export const RELEASE_KEEP = {
  terrain: [],
  trees: [],
  'yard-ground': [],
  streets: [],
  // T-2572: picked on the GPU (gpu-pick.js), so their triangles go too.
  frontage: [],
  enclosures: [],
  yard: [],
  // The weathering handle rewrites the buildings' INSTANCE colours, which are
  // not vertex attributes (T-2568), so nothing more is kept for it.
  structures: ['position', 'index'],
};

function dropArray() { this.array = null; }

/**
 * HARNESS ONLY: `?keep-geometry=1` uploads exactly as a phone does but keeps
 * the page arrays, because the smoke's probes read vertices back to check what
 * was laid. `tools/check_upload_release.mjs` boots without it and holds the
 * release itself to account: the arrays go, and picking and walking still work.
 */
const KEEP_ARRAYS = (() => {
  try { return new URLSearchParams(window.location.search).get('keep-geometry') === '1'; } catch { return false; }
})();

const census = { geometries: 0, attributes: 0, bytes: 0, keptForHarness: KEEP_ARRAYS,
  // T-2548: the buildings' source glTF geometry, and their decoded images.
  sources: 0, sourceBytes: 0, images: 0, imageBytes: 0 };

function release(attr) {
  if (!attr || !attr.array || attr.userData?.uploadReleased) return;
  if (attr.usage !== THREE.StaticDrawUsage) return;
  if (attr.isInterleavedBufferAttribute || attr.isInstancedBufferAttribute) return;
  attr.userData = attr.userData || {};
  attr.userData.uploadReleased = true;
  census.attributes += 1;
  census.bytes += attr.array.byteLength;
  if (!KEEP_ARRAYS) attr.onUpload(dropArray);
}

/** Mark one layer's geometries to let go of their page arrays once uploaded. */
function markLayer(layer, keep) {
  layer.traverse((o) => {
    const geo = o.geometry;
    if (!geo || o.isInstancedMesh || geo.userData.uploadReleased) return;
    if (geo.userData.rereadBeforeRelease) return;
    const pos = geo.attributes.position;
    if (!pos || pos.usage !== THREE.StaticDrawUsage) return;
    geo.userData.uploadReleased = true;
    if (!geo.boundingSphere) geo.computeBoundingSphere();
    if (!geo.boundingBox) geo.computeBoundingBox();
    census.geometries += 1;
    for (const [attrName, attr] of Object.entries(geo.attributes)) {
      if (!keep.includes(attrName)) release(attr);
    }
    // A BatchedMesh reads its index's element size on every draw.
    if (geo.index && !keep.includes('index') && !o.isBatchedMesh) release(geo.index);
    if (keep.includes('position')) pickWithoutReleased(o);
  });
}

/** What three's raycast interpolates at a hit when the geometry carries it. */
const HIT_ATTRIBUTES = ['uv', 'uv1', 'uv2', 'uv3', 'normal'];

/**
 * A tap raycasts the chunk's own triangles, and three then interpolates the uv
 * and normal at the hit if the geometry carries them — reading arrays a phone
 * has let go of. No `pickAt` reads either (they resolve a hit by face and
 * point), so for the length of the raycast those attributes are set aside,
 * and put back before anything can draw.
 */
function pickWithoutReleased(o) {
  if (o.userData.uploadReleasedPick) return;
  o.userData.uploadReleasedPick = true;
  const raycast = o.raycast;
  o.raycast = function raycastReleased(raycaster, intersects) {
    const attrs = this.geometry?.attributes;
    const aside = [];
    if (attrs) {
      for (const name of HIT_ATTRIBUTES) {
        if (attrs[name] && attrs[name].array === null) { aside.push([name, attrs[name]]); delete attrs[name]; }
      }
    }
    try {
      return raycast.call(this, raycaster, intersects);
    } finally {
      for (const [name, attr] of aside) attrs[name] = attr;
    }
  };
}

/**
 * Mark every listed layer under `scene` to let go of its page arrays once they
 * are uploaded. Idempotent: a layer built later (the trees) is picked up by
 * calling it again, and a geometry already marked is passed over.
 */
export function releaseAfterUpload(scene, keepByLayer = RELEASE_KEEP) {
  for (const [name, keep] of Object.entries(keepByLayer)) {
    const layer = scene.getObjectByName(name);
    if (layer) markLayer(layer, keep);
  }
  return { ...census };
}

const _scissor = new THREE.Vector4();

/**
 * HAND A LAYER TO THE GPU AS SOON AS IT IS BUILT, on a phone, so its page
 * arrays go while the next layer is still being laid rather than all at once
 * under the first frame — where every layer's page copy and its GPU copy were
 * alive together, which is the moment iOS killed the tab.
 *
 * The layer is drawn once, alone (its siblings hidden, the lights kept, so the
 * programs are the ones the real frame uses), into one scissored pixel of the
 * canvas the loader still covers, with frustum culling off so every chunk that
 * is shown is uploaded, and with the sun's pass held so nothing else is drawn.
 * `hide(o)` keeps back what this tier never shows (the cross-street walks and
 * the woodpiles at `light`), so the GPU is not handed what it will never draw.
 * Everything touched is put back exactly as it was.
 */
export function uploadLayerNow(renderer, scene, camera, layer, { hide = () => false } = {}) {
  const keep = RELEASE_KEEP[layer?.name];
  if (!keep || !layer.visible) return;
  markLayer(layer, keep);
  const restore = [];
  for (const c of scene.children) {
    if (c !== layer && !c.isLight && c.visible) { restore.push([c, 'visible', true]); c.visible = false; }
  }
  layer.traverse((o) => {
    if (o !== layer && o.visible && hide(o)) { restore.push([o, 'visible', true]); o.visible = false; }
    if (o.frustumCulled) { restore.push([o, 'frustumCulled', true]); o.frustumCulled = false; }
    if (o.isBatchedMesh && o.perObjectFrustumCulled) {
      restore.push([o, 'perObjectFrustumCulled', true]); o.perObjectFrustumCulled = false;
    }
  });
  const shadow = renderer.shadowMap;
  const auto = shadow.autoUpdate;
  const needs = shadow.needsUpdate;
  const scissorTest = renderer.getScissorTest();
  renderer.getScissor(_scissor);
  shadow.autoUpdate = false;
  shadow.needsUpdate = false;
  renderer.setScissorTest(true);
  renderer.setScissor(0, 0, 1, 1);
  try {
    renderer.render(scene, camera);
  } finally {
    renderer.setScissor(_scissor);
    renderer.setScissorTest(scissorTest);
    shadow.autoUpdate = auto;
    shadow.needsUpdate = needs;
    for (const [o, key, value] of restore) o[key] = value;
  }
}

/**
 * T-2548. A PHONE LETS GO OF EACH BUILDING'S SOURCE GEOMETRY ONCE ITS BATCH HOLDS
 * A COPY. `createBuildings` normalises every source mesh into a float32 copy in
 * the batch, and the source — the GLB's quantized, interleaved arrays — was then
 * kept in the registry for nothing but a detail rebuild: about 49 MB of the 1904
 * phone's ArrayBuffers, 12.5 MB of it Glessner's. The scene graph, materials and
 * textures stay (the batch draws with those textures, and the card reads the
 * record); the attributes and the index go. A released row is marked
 * `sourceReleased`, and a rebuild re-reads its GLB first (main.js, from the HTTP
 * cache). Idempotent: a row already released is passed over.
 */
export function releaseSources(registry) {
  for (const row of registry.values()) {
    if (!row.gltf || row.sourceReleased) continue;
    const buffers = new Set();
    row.gltf.scene?.traverse((o) => {
      const geo = o.geometry;
      if (!geo) return;
      for (const attr of [...Object.values(geo.attributes), geo.index]) {
        const array = attr?.isInterleavedBufferAttribute ? attr.data.array : attr?.array;
        if (array?.buffer) buffers.add(array.buffer);
      }
      for (const name of Object.keys(geo.attributes)) geo.deleteAttribute(name);
      geo.setIndex(null);
      geo.dispose();
    });
    row.sourceReleased = true;
    census.sources += 1;
    for (const buffer of buffers) census.sourceBytes += buffer.byteLength;
  }
}

/**
 * T-2548. A PHONE CLOSES A BUILDING'S DECODED IMAGE ONCE THE GPU HOLDS IT. Three
 * keeps every `texture.image` (an ImageBitmap) after upload, so each picture a
 * house is painted with was held twice, decoded in the page and again on the GPU.
 *
 * Only an image that came out of a GLB through the shared-image cache is closed
 * (shared-images.js), and only when EVERY texture of the structures batch that
 * draws from it has its GPU texture and the source is uploaded — three uploads
 * once per source and sampler setup, and a second sampler on a source would
 * otherwise read a closed bitmap. The image also leaves the cache, so a GLB
 * parsed later (a detail rebuild) decodes its own copy rather than being handed
 * this closed one. Anything not yet uploaded is left open: nothing re-uploads a
 * building texture after the build, and a restored context needs the page back,
 * which crash-guard.js reloads for when the census counts a closed image.
 */
export function closeUploadedImages(group, renderer) {
  const bySource = new Map();
  group.traverse((o) => {
    // A shadow's own depth material can sample the same map with its own sampler.
    for (const material of [].concat(o.material ?? [], o.customDepthMaterial ?? [],
      o.customDistanceMaterial ?? [])) {
      for (const value of Object.values(material)) {
        if (!value?.isTexture || !value.source) continue;
        if (!bySource.has(value.source)) bySource.set(value.source, new Set());
        bySource.get(value.source).add(value);
      }
    }
  });
  const props = renderer.properties;
  for (const [source, textures] of bySource) {
    const image = source.data;
    if (typeof ImageBitmap === 'undefined' || !(image instanceof ImageBitmap)) continue;
    if (!isSharedImage(image)) continue;
    const uploaded = props.get(source).__version === source.version
      && [...textures].every((t) => props.get(t).__webglTexture !== undefined);
    if (!uploaded) continue;
    retireSharedImage(image);
    census.images += 1;
    census.imageBytes += image.width * image.height * 4;
    image.close();
  }
}

/** What has been marked so far — read by the harness, never by the scene. */
export function uploadReleaseState() { return { ...census }; }
