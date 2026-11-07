/**
 * camp-surfaces.js — the 1812 Potawatomi camp's natural coverings, bound by name (T-3342).
 *
 * The camp's lodges are covered in cat-tail mats and elm bark and its arbors roofed in
 * cut boughs (generators/archetypes/lodge_camp.py). A covering drawn as a flat colour
 * reads as nothing at all — the owner's word for the camp this replaced was that "the
 * texture don't look like anything" — so each of the three is bound here to its sheet in
 * T-3342's library, `assets/textures/camp_1812_pbr/`: base colour, OpenGL normal, and the
 * packed ORM as both roughness and occlusion, the way roof-relief.js binds a roof.
 *
 * ## How it differs from the roofs and walls
 *
 * Those derive their UV in the shader from the position, because the town's GLBs carry
 * no metric UV. These carry their own: the builder writes every mat and bark sheet its
 * tile coordinates, in tiles of the sheet's `span_m`, each piece at its own offset so no
 * two lodges repeat in step. They ride as the custom attribute `_UV` (three reads it as
 * `_uv`) because no texture is embedded in the GLB and the web derivative's prune drops a
 * TEXCOORD_0 that nothing samples. `apply` copies it to `uv` on the source geometry,
 * which normalizeGeometry then carries like any other UV — a tiling one, so it stays
 * float (compact-attributes.js).
 *
 * The base colour IS bound, unlike the roofs': the mats' colour is the mats. The
 * material's own colour is whitened so the instance colour the batch multiplies in
 * leaves the sheet as it is; a sheet that fails to load leaves the GLB's colour, which
 * is each sheet's mean, so the camp degrades to the flat look it had, never to white.
 *
 * ## Only where a camp stands
 *
 * Nine sheets are not loaded into a scene with no camp in it: the caller says whether
 * one is drawn (`wanted`), and an unwanted load binds nothing and costs nothing. The hay
 * sheets (T-3401) follow the same rule on their own flag (`hay`).
 * The names are pinned in docs/GLB-CONTRACT.md § Camp coverings.
 */

import * as THREE from 'three';
import { resolveBases } from './scene-loader.js';
import { ktx2Beside, loadSheet } from './ktx2.js';

/** Material name -> the library directory that covers it (docs/GLB-CONTRACT.md). */
export const CAMP_COVERINGS = {
  camp_cattail_mat: 'cattail_mat',
  camp_elm_bark: 'elm_bark',
  camp_boughs: 'bough_thatch',
};

/**
 * T-3401: the hay of the stacks at Lee's Place (generators/archetypes/haystack.py), in
 * the same library and bound the same way: combed stems on a stack's outside, the greyed
 * thatch of its crown or of a stack that stood the winter, and the brighter heart where
 * hay was pulled or eaten out of it. Loaded only where a haystack is drawn (`hay`).
 */
export const HAY_COVERINGS = {
  stack_hay: 'hay_stack',
  stack_hay_weathered: 'hay_weathered',
  stack_hay_cut: 'hay_cut',
};

const LIBRARY = 'textures/camp_1812_pbr/';

async function sheet(loader, url, srgb) {
  let tex;
  try {
    tex = await loadSheet(ktx2Beside(url), url, loader, { srgb });
  } catch {
    throw new Error(`camp covering map did not load — ${url}`);
  }
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  tex.anisotropy = 8;
  return tex;
}

/**
 * Load the three coverings' sheets when `wanted`, and the three hay sheets when `hay`.
 * Returns `{ problem, apply, bound }`; `apply(material, geometry)` binds the covering a
 * material names, if it names one, and returns a warning string or null. It degrades
 * rather than throws, like the roofs.
 */
export async function loadCampSurfaces({ wanted = false, hay = false, assetBase = resolveBases().assetBase } = {}) {
  const none = { problem: null, bound: 0, apply: () => null };
  const coverings = { ...(wanted ? CAMP_COVERINGS : {}), ...(hay ? HAY_COVERINGS : {}) };
  if (!Object.keys(coverings).length) return none;
  const loader = new THREE.TextureLoader();
  const base = new URL(LIBRARY, assetBase);
  const sheets = new Map();
  try {
    await Promise.all(Object.entries(coverings).map(async ([name, dir]) => {
      const here = new URL(`${dir}/`, base);
      const res = await fetch(new URL('material.json', here), { cache: 'no-cache' });
      if (!res.ok) throw new Error(`${res.status} — ${new URL('material.json', here)}`);
      const doc = await res.json();
      const web = doc.web ?? {};
      const file = (map) => new URL(web[map] ?? `${doc.id}_${map}_web.jpg`, here).href;
      const [map, normalMap, orm] = await Promise.all([
        sheet(loader, file('basecolor'), true),
        sheet(loader, file('normal_gl'), false),
        sheet(loader, file('orm'), false),
      ]);
      sheets.set(name, { map, normalMap, orm });
    }));
  } catch (err) {
    return { ...none, problem: `camp coverings not bound — ${err.message}` };
  }
  const state = {
    problem: null,
    bound: 0,
    apply(material, geometry) {
      const covering = sheets.get(material?.name);
      if (!covering) return null;
      const uv = geometry?.getAttribute?.('_uv');
      if (!uv && !geometry?.getAttribute?.('uv')) {
        return `${material.name}: a camp covering with no _UV tile coordinates — left unbound`;
      }
      if (uv && !geometry.getAttribute('uv')) geometry.setAttribute('uv', uv);
      if (material.userData?.chiCampSurface) return null;
      material.map = covering.map;
      material.normalMap = covering.normalMap;
      // ORM: R = occlusion, G = roughness — one resident texture in two slots.
      material.roughnessMap = covering.orm;
      material.aoMap = covering.orm;
      material.color.setRGB(1, 1, 1);
      material.roughness = 1;
      material.userData = { ...(material.userData ?? {}), chiCampSurface: material.name };
      material.needsUpdate = true;
      state.bound += 1;
      return null;
    },
  };
  return state;
}
