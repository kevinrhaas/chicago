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
 *  - `position` (and the index) of a layer that answers a tap, because
 *    `pickAt` raycasts the chunk's own triangles (and the uv and normal three
 *    would interpolate at the hit are set aside for the raycast — no pick
 *    reads them);
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
 * the page reloads on restore rather than drawing nothing.
 */

import * as THREE from 'three';

/** Layer → attributes it must keep for a tap. Unlisted layers keep nothing. */
export const RELEASE_KEEP = {
  terrain: [],
  trees: [],
  'yard-ground': [],
  streets: [],
  frontage: ['position', 'index'],
  enclosures: ['position', 'index'],
  yard: ['position', 'index'],
  // The weathering slider rewrites the buildings' colour in place.
  structures: ['position', 'index', 'color'],
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

const census = { geometries: 0, attributes: 0, bytes: 0, keptForHarness: KEEP_ARRAYS };
let watching = false;

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

function watchContext(renderer) {
  if (watching || !renderer?.domElement || !census.attributes) return;
  watching = true;
  let lost = false;
  renderer.domElement.addEventListener('webglcontextlost', () => { lost = true; });
  renderer.domElement.addEventListener('webglcontextrestored', () => {
    if (lost) window.location.reload();
  });
}

/**
 * Mark every listed layer under `scene` to let go of its page arrays once they
 * are uploaded. Idempotent: a layer built later (the trees) is picked up by
 * calling it again, and a geometry already marked is passed over.
 */
export function releaseAfterUpload(scene, renderer, keepByLayer = RELEASE_KEEP) {
  for (const [name, keep] of Object.entries(keepByLayer)) {
    const layer = scene.getObjectByName(name);
    if (layer) markLayer(layer, keep);
  }
  watchContext(renderer);
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
  watchContext(renderer);
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

/** What has been marked so far — read by the harness, never by the scene. */
export function uploadReleaseState() { return { ...census }; }
