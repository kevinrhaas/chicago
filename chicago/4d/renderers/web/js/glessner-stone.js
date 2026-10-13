/** T-2446. Glessner's granite colour, chosen at load from the URL.
 *
 * The owner, 2026-10-13, with a photograph of the Eighteenth Street front: the stone "is a
 * bit more brown than this photo from real life, it's more grey but not a black and white
 * grey, kind of greige but leaning grey ... do a Glessner color option on the url to show
 * different options ... then we will finalize a default".
 *
 * The package bakes GRANITE_TINT (masonry_house_v4_materials.py) into the five granite
 * slots' base colour, the four variants each a little off it. A preset names the tint the
 * main slot should have had; every slot is multiplied by preset / baked, so the variants
 * keep their spread around it. `?stone=baked` shows the package as it is, and
 * `?stone=r,g,b` takes a linear tint directly. Nothing is retinted but those five slots
 * of glessner_house: the limestone trim, the brick court and every other house stay.
 */
import * as THREE from 'three';

/** GRANITE_TINT as the package carries it (linear). */
export const GLESSNER_STONE_BAKED = Object.freeze([1.0, 0.97, 0.94]);

/** Linear tints for the main granite slot, set by rendering the app's sunlit east front
 * against the owner's photograph (sRGB red/green 1.04, blue/green 0.95 on its stone).
 * greige meets it there, a tenth lighter than the bake; warm-greige and grey-greige sit
 * either side of it, and light-greige is greige lighter again, toward the photograph's
 * overcast brightness. In the July sun the shaded north wall reads cooler than any of
 * them, because the sky lights it. */
export const GLESSNER_STONES = Object.freeze({
  greige: Object.freeze([0.935, 1.067, 1.133]),
  'warm-greige': Object.freeze([1.0, 1.067, 1.078]),
  'grey-greige': Object.freeze([0.90, 1.067, 1.166]),
  'light-greige': Object.freeze([1.105, 1.26, 1.34]),
  baked: GLESSNER_STONE_BAKED,
});

export const GLESSNER_STONE_DEFAULT = 'greige';

const GRANITE_SLOT = /^granite(?:_[1-4])?$/;

/** The stone the URL asks for, or the default. An unknown name falls back to the default
 * rather than failing the scene. */
export function readGlessnerStone(search = globalThis.location?.search ?? '') {
  let asked = null;
  try { asked = new URLSearchParams(search).get('stone'); } catch { asked = null; }
  const name = asked?.trim().toLowerCase();
  if (name && Object.hasOwn(GLESSNER_STONES, name)) return { name, tint: GLESSNER_STONES[name] };
  const parts = name?.split(',').map(Number);
  if (parts?.length === 3 && parts.every((v) => Number.isFinite(v) && v > 0 && v <= 1.5)) {
    return { name: parts.join(','), tint: Object.freeze(parts) };
  }
  return { name: GLESSNER_STONE_DEFAULT, tint: GLESSNER_STONES[GLESSNER_STONE_DEFAULT] };
}

/** Retints one of glessner_house's granite slots in place, once. Runs before the batch
 * whitens the material, so the colour lands in the per-vertex albedo like any tint. */
export function tintGlessnerGranite(material, record, stone) {
  if (record?.id !== 'glessner_house' || !GRANITE_SLOT.test(material?.name ?? '')) return;
  if (material.userData.glessnerStone !== undefined) return;
  material.userData.glessnerStone = stone.name;
  if (stone.tint === GLESSNER_STONE_BAKED) return;
  const [r, g, b] = stone.tint.map((v, i) => v / GLESSNER_STONE_BAKED[i]);
  material.color = (material.color ?? new THREE.Color(1, 1, 1)).clone().multiply(new THREE.Color(r, g, b));
}
