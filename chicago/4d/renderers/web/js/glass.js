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
 * `transmission` keeps the GLB's own glass.
 *
 * WHICH ONE SHIPS IS THE OWNER'S PICK (T-2109, answered 2026-10-04: "dark at
 * balanced and light"). So the glass follows the Scene detail setting:
 * `full` keeps the GLB's transmission, where the frame budget is spent on
 * purpose for the inspection model, and `balanced` and `light` draw the dark
 * plate, which halved the 1904 landing frame at both viewports
 * (docs/measurements/T-2109-glessner-glass.md). `?glass=` still names one
 * mode for every setting, to compare.
 */
import * as THREE from 'three';

export const GLASS_MODES = Object.freeze(['transmission', 'clear', 'dark']);
/** The GLB's own glass: what a caller that names no mode gets. */
export const DEFAULT_GLASS = 'transmission';
/** The owner's pick, per Scene detail setting (T-2109, answer c). */
export const GLASS_BY_DETAIL = Object.freeze({ full: 'transmission', balanced: 'dark', light: 'dark' });

/** `?glass=clear|dark|transmission`, or null when the address names none. */
export function readGlassRequest(params) {
  const asked = params?.get?.('glass');
  return GLASS_MODES.includes(asked) ? asked : null;
}

/** The glass drawn at `detail`: the address's own mode when it names one,
 * otherwise the owner's pick for that setting. An unknown setting keeps the
 * GLB's glass rather than guessing a cheaper one. */
export function glassForDetail(detail, requested = null) {
  if (GLASS_MODES.includes(requested)) return requested;
  return Object.hasOwn(GLASS_BY_DETAIL, detail) ? GLASS_BY_DETAIL[detail] : DEFAULT_GLASS;
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
