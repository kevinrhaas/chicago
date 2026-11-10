/**
 * T-3341: the early town's remaining flat brick and stick-and-clay surfaces.
 *
 * The sheets are the existing procedural Chicago1835 library, whose material.json
 * labels fabric evidence separately from reconstructed module and appearance.
 * Their linear luminance ratio preserves the GLB's already ruled mean colour.
 * Metric face UVs need no mesh, UV or confidence changes. Already mapped period
 * recipes (T-3387) keep their own maps and K03 shuffle. No 1904 material is bound.
 */
import { BufferAttribute, BufferGeometry, Mesh, ShaderChunk, Vector3 } from 'three';
import { captureHooks, registerPatch } from './batch-material.js';
import { programKeyOf } from './confidence.js';
import { SCALARS_GLSL, structureFrameGLSL } from './compact-attributes.js';
import { resolveBases } from './scene-loader.js';
import { loadSubstrate } from './wall-relief.js';
import { bondUniformsFor, brickBondShader, SPREAD } from './brick-bond.js';

export const EARLY_MASONRY = Object.freeze({
  brick: 'masonry/chicago_clay_brick_lime_mortar',
  clay: 'masonry/cat_and_clay_chimney',
});
/** generate_1835_pbr_library.py::brick: 20 columns,48 courses, alternating half-bricks. */
export const EARLY_BRICK = Object.freeze({
  bond: 'running', modules: 20, courses: 48, joint_m: 0,
  // The generator's mortar masks are fractions of each module/course, not1904 joints.
  halfJoint: Object.freeze([0.055, 0.14]),
});
const MAX_COURSES = 48;
const shaderParts = brickBondShader({ coordinate: 'vNormalMapUv', maxCourses: MAX_COURSES });
const u = bondUniformsFor(EARLY_BRICK, { maxCourses: MAX_COURSES });
const value = (x) => x && typeof x === 'object' && !Array.isArray(x) ? x.value : x;

/** The existing stack-disposition ruling, docs/RESEARCH/chimneys.md §§2,3,6. */
export function masonrySubstrate(name, sidecar, mapped = false, statedFabric = null) {
  if (!['1812', '1835'].includes(String(sidecar?.scene)) || mapped) return null;
  if (['brick', 'draft_brick', 'k13_brick'].includes(name)) return 'brick';
  if (name === 'wall' && value(sidecar?.attributes?.construction) === 'brick') return 'brick';
  if (name !== 'chimney') return null;
  if (sidecar?.archetype !== 'log_dwelling') return 'brick';
  if (['brick', 'clay'].includes(statedFabric)) return statedFabric;
  const ridge = value(sidecar?.attributes?.chimney_ridge_at);
  return Array.isArray(ridge) && ridge.length ? 'brick' : 'clay';
}

/**
 * The two dispositions share one material in Miller's native asset. Read the
 * disconnected stack footprints, not generator dimensions: the exterior shaft
 * reaches its foot; the separately recorded addition ridge stack starts at the
 * roof. Its corbel and shaft overlap in plan and therefore stay together.
 */
export function chimneyComponents(points, indices) {
  const boxes = [];
  for (let i = 0; i < indices.length; i += 3) {
    const ids = indices.slice(i, i + 3), p = ids.map((n) => points[n]);
    boxes.push({ ids, lo: [0, 1, 2].map((k) => Math.min(...p.map((v) => v[k]))),
      hi: [0, 1, 2].map((k) => Math.max(...p.map((v) => v[k]))) });
  }
  const parents = boxes.map((_, i) => i);
  const root = (i) => parents[i] === i ? i : (parents[i] = root(parents[i]));
  for (let i = 0; i < boxes.length; i += 1) for (let j = i + 1; j < boxes.length; j += 1) {
    if ([0, 2].every((k) => boxes[i].lo[k] <= boxes[j].hi[k] + 0.001
      && boxes[j].lo[k] <= boxes[i].hi[k] + 0.001)) parents[root(i)] = root(j);
  }
  const groups = new Map();
  boxes.forEach((b, i) => {
    const key = root(i);
    if (!groups.has(key)) groups.set(key, { indices: [], foot: Infinity });
    const g = groups.get(key);
    g.indices.push(...b.ids); g.foot = Math.min(g.foot, b.lo[1]);
  });
  const out = [...groups.values()].sort((a, b) => a.foot - b.foot);
  if (out.length !== 2 || Math.abs(out[0].foot) > 0.03 || out[1].foot < out[0].foot + 0.75) {
    throw new Error('A declared mixed chimney needs one ground-foot exterior stack and one separate roof-foot stack');
  }
  return out.map((g, i) => ({ ...g, fabric: i === 0 ? 'clay' : 'brick' }));
}

/** Split only a recorded mixed primitive; every triangle and confidence is retained. */
export function masonryMeshes(meshes, sidecar) {
  if (!['1812', '1835'].includes(String(sidecar?.scene)) || sidecar?.archetype !== 'log_dwelling'
    || !value(sidecar?.attributes?.frame_addition_ridge_stack)) return meshes;
  return meshes.flatMap(({ mesh, matrix }) => {
    if (mesh.material?.name !== 'chimney' || mesh.material.map) return [{ mesh, matrix }];
    const geo = mesh.geometry, pos = geo.getAttribute('position'), v = new Vector3();
    const points = Array.from({ length: pos.count }, (_, i) =>
      v.fromBufferAttribute(pos, i).applyMatrix4(matrix).toArray());
    const idx = geo.getIndex();
    const indices = idx ? Array.from({ length: idx.count }, (_, i) => idx.getX(i))
      : Array.from({ length: pos.count }, (_, i) => i);
    return chimneyComponents(points, indices).map((part) => {
      const ids = [...new Set(part.indices)], slots = new Map(ids.map((id, i) => [id, i]));
      const piece = new BufferGeometry();
      for (const [name, attr] of Object.entries(geo.attributes)) {
        const data = new Float32Array(ids.length * attr.itemSize);
        ids.forEach((id, i) => {
          for (let k = 0; k < attr.itemSize; k += 1) {
            data[i * attr.itemSize + k] = attr[['getX', 'getY', 'getZ', 'getW'][k]](id);
          }
        });
        piece.setAttribute(name, new BufferAttribute(data, attr.itemSize));
      }
      piece.setIndex(part.indices.map((id) => slots.get(id)));
      const material = mesh.material.clone();
      material.userData = { ...material.userData, chiMasonryFabric: part.fabric };
      const next = new Mesh(piece, material);
      next.name = `${mesh.name}-${part.fabric}`;
      return { mesh: next, matrix, transientMasonry: true };
    });
  });
}

/** Query-only before frame, leaving native mean colours intact. */
export function masonryOff(search = globalThis.location?.search ?? '') {
  return new URLSearchParams(search).get('masonry') === 'flat';
}

function patch(material, set, substrate, shuffle) {
  const hooks = captureHooks(material), prior = material.onBeforeCompile;
  const priorKey = programKeyOf(material);
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    Object.assign(shader.uniforms, {
      chiMasonryTileM: { value: set.tileM }, chiMasonryRough: { value: set.meanRough },
      chiMasonryShuffle: { value: substrate === 'brick' && shuffle ? 1 : 0 },
      chiBondPanel: { value: new Float32Array(u.panel) },
      chiBondCourse: { value: new Float32Array(u.course.flat()) },
      chiBondList: { value: new Float32Array(u.list.flat()) },
      chiBondSpread: { value: new Float32Array([SPREAD.lightness, SPREAD.warmth, SPREAD.mottle]) },
    });
    shader.vertexShader = SCALARS_GLSL.declare(`uniform float chiMasonryTileM;
varying float vChiMasonryRough;
flat varying vec2 vChiBondSeat;
` + shader.vertexShader.replace('#include <batching_vertex>', `#include <batching_vertex>
  #ifdef USE_BATCHING
    vChiBondSeat = batchingMatrix[ 3 ].xz;
  #else
    vChiBondSeat = modelMatrix[ 3 ].xz;
  #endif`).replace('#include <project_vertex>', `#include <project_vertex>
  {
    ${structureFrameGLSL('chiMasonryLocal')}
    vec3 p = ( modelMatrix * vec4( chiMasonryLocal, 1.0 ) ).xyz;
    vec3 n = normalize( mat3( modelMatrix ) * objectNormal );
    vec3 t = cross( n, vec3( 0.0, 1.0, 0.0 ) );
    t = length( t ) > 1e-4 ? normalize( t ) : vec3( 1.0, 0.0, 0.0 );
    vec3 b = cross( t, n );
    vec2 uv = vec2( dot( p, t ), dot( p, b ) ) / chiMasonryTileM;
    vNormalMapUv = uv;
    vRoughnessMapUv = uv;
    vAoMapUv = uv;
    vChiMasonryRough = ${SCALARS_GLSL.roughness};
  }`));
    let fragment = shader.fragmentShader.replace('#include <map_fragment>', `
vec2 chiBondShift = vec2( 0.0 );
vec3 chiBondTint = vec3( 1.0 );
if ( chiMasonryShuffle > 0.5 ) ${shaderParts.resolve}
`);
    fragment = fragment.replace('#include <color_fragment>', `#include <color_fragment>
  diffuseColor.rgb *= 2.0 * textureGrad( roughnessMap, vRoughnessMapUv + chiBondShift,
    dFdx( vRoughnessMapUv ), dFdy( vRoughnessMapUv ) ).b * chiBondTint;
`).replace('#include <roughnessmap_fragment>', `
  float roughnessFactor = vChiMasonryRough * clamp( textureGrad( roughnessMap,
    vRoughnessMapUv + chiBondShift, dFdx( vRoughnessMapUv ), dFdy( vRoughnessMapUv ) ).g
    / chiMasonryRough, 0.0, 1.6 );
`);
    if (!shaderParts.normal) throw new Error('The brick shuffle no longer recognizes the normal-map sample');
    fragment = fragment.replace('#include <normal_fragment_maps>', shaderParts.normal);
    const ao = ShaderChunk.aomap_fragment.replaceAll('texture2D( aoMap, vAoMapUv )',
      'textureGrad( aoMap, vAoMapUv + chiBondShift, dFdx( vAoMapUv ), dFdy( vAoMapUv ) )');
    fragment = fragment.replace('#include <aomap_fragment>', ao);
    shader.fragmentShader = `uniform float chiMasonryRough;
uniform float chiMasonryShuffle;
varying float vChiMasonryRough;
` + shaderParts.pars + fragment;
  };
  material.customProgramCacheKey = () => `early-masonry-v1|over:${priorKey}`;
  registerPatch(material, hooks, 'early-masonry-v1', { substrate, tileM: set.tileM, shuffle });
  material.needsUpdate = true;
}

const cache = new Map(), patched = new WeakSet();

/** Only early scenes pay for these shared pairs; a failed sheet is reported, never hidden. */
export async function loadMasonrySurfaces({ wanted = false, lowSpec = false,
  assetBase = resolveBases().assetBase, off = masonryOff(), shuffle = true } = {}) {
  const none = { off, problem: null, sets: null, apply: () => null };
  if (!wanted || off) return none;
  const key = `${assetBase}|${lowSpec ? 'light' : 'full'}`;
  if (!cache.has(key)) {
    const base = new URL('textures/chicago_1835_pbr/', assetBase);
    cache.set(key, Promise.all(Object.entries(EARLY_MASONRY).map(async ([name, dir]) =>
      [name, await loadSubstrate(base, dir, lowSpec)])).then((rows) => new Map(rows)));
  }
  let sets;
  try { sets = await cache.get(key); } catch (err) {
    cache.delete(key);
    return { ...none, problem: `early masonry surfaces not bound — ${err.message}` };
  }
  return {
    off: false, problem: null,
    sets: Object.fromEntries([...sets].map(([k, s]) => [k, {
      id: s.id, px: s.px, tileM: s.tileM, ktx2: s.ktx2,
    }])),
    apply(material, sidecar, originalName = material?.name) {
      const substrate = masonrySubstrate(originalName, sidecar, !!material?.map,
        material?.userData?.chiMasonryFabric);
      if (!substrate) return null;
      const set = sets.get(substrate);
      if (!patched.has(material)) {
        patched.add(material);
        material.normalMap = set.normal;
        material.roughnessMap = material.aoMap = set.orl;
        patch(material, set, substrate, shuffle);
        material.userData = { ...(material.userData ?? {}), chiMasonrySurface: substrate };
      }
      return substrate;
    },
  };
}
