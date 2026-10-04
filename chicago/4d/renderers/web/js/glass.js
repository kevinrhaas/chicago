/**
 * T-2109 — a cheaper glass for a model whose GLB asks for transmission.
 *
 * 1904's Glessner house carries `KHR_materials_transmission` on its one glass
 * material (both the full and the `.light` model). Any visible transmissive
 * material makes three draw every opaque object a second time into a target
 * the glass samples, and T-2099's still-frame reading put that pass at about
 * half of every frame at the 1904 landing, at both viewports.
 *
 * Two cheaper glasses replace it at load, without touching the GLB (the file
 * still says what the glass is; this is how the browser draws it):
 *
 *   clear — see-through: no transmission, alpha-blended, the interior shows
 *           through un-refracted. One sorted transparent batch.
 *   dark  — opaque dark plate: no transmission, no blending; reads the way
 *           plate glass reads from a street in daylight. Batches with the
 *           house's own opaque surfaces.
 *
 * `transmission` keeps the GLB's own glass. Which one ships is the owner's
 * pick (T-2109); until then the default is unchanged and `?glass=` chooses.
 */
import * as THREE from 'three';

export const GLASS_MODES = Object.freeze(['transmission', 'clear', 'dark']);
export const DEFAULT_GLASS = 'transmission';

/** `?glass=clear|dark|transmission`; anything else is the default. */
export function readGlassMode(params) {
  const asked = params?.get?.('glass');
  return GLASS_MODES.includes(asked) ? asked : DEFAULT_GLASS;
}

export function isTransmissive(material) {
  return Boolean(material && material.transmission > 0);
}

/** The material to draw instead of `material`, or `material` itself when it is
 * not transmissive or the mode keeps transmission. Never mutates its input. */
export function cheapenGlass(material, mode = DEFAULT_GLASS) {
  if (mode === 'transmission' || !isTransmissive(material)) return material;
  const glass = new THREE.MeshStandardMaterial({
    name: material.name,
    color: material.color.clone(),
    roughness: material.roughness,
    metalness: material.metalness,
    side: material.side,
    envMap: material.envMap ?? null,
    envMapIntensity: material.envMapIntensity ?? 1,
  });
  if (mode === 'clear') {
    // The GLB's near-white tint at full strength would read as frosted; a
    // quarter of it over the room behind is a pane with the room seen through.
    glass.color.multiplyScalar(0.35);
    glass.transparent = true;
    glass.opacity = 0.28;
    glass.depthWrite = false;
  } else {
    glass.color.multiplyScalar(0.12);
  }
  glass.userData.cheapenedFrom = 'KHR_materials_transmission';
  glass.userData.glassMode = mode;
  return glass;
}
