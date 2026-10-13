/** T-2446, T-2469. Glessner's granite colour, applied at load.
 *
 * The owner, 2026-10-13, with a photograph of the Eighteenth Street front: the stone "is a
 * bit more brown than this photo from real life, it's more grey but not a black and white
 * grey, kind of greige but leaning grey". T-2446 put five colours on `?stone=` to compare;
 * he chose grey-greige ("we can use that as the default. You can cull the others").
 *
 * The package bakes GRANITE_TINT (masonry_house_v4_materials.py) into the five granite
 * slots' base colour, the four variants each a little off it. Grey-greige cannot be baked
 * there: its green and blue are above 1, and Blender's glTF exporter clamps a
 * baseColorFactor to 1, so the stone would come out a tenth darker than the one chosen.
 * So every slot is multiplied here by GLESSNER_STONE / baked, before the batch moves the
 * colour into the per-vertex albedo, and the variants keep their spread around it.
 * Nothing is retinted but those five slots of glessner_house: the limestone trim, the
 * brick court and every other house stay as baked.
 */
import * as THREE from 'three';

/** GRANITE_TINT as the package carries it (linear). */
export const GLESSNER_STONE_BAKED = Object.freeze([1.0, 0.97, 0.94]);

/** Grey-greige, the main granite slot's linear tint. Set by rendering the app's sunlit east
 * front against the owner's photograph (sRGB red/green 1.04, blue/green 0.95 on its
 * stone): it reads 1.02-1.03 and 0.955-0.965 there, a shade greyer than the photograph,
 * and a little lighter than the bake. */
export const GLESSNER_STONE = Object.freeze([0.90, 1.067, 1.166]);

const GRANITE_SLOT = /^granite(?:_[1-4])?$/;
const LIFT = GLESSNER_STONE.map((v, i) => v / GLESSNER_STONE_BAKED[i]);

/** Retints one of glessner_house's granite slots in place, once. */
export function tintGlessnerGranite(material, record) {
  if (record?.id !== 'glessner_house' || !GRANITE_SLOT.test(material?.name ?? '')) return;
  if (material.userData.glessnerStone) return;
  material.userData.glessnerStone = 'grey-greige';
  material.color = (material.color ?? new THREE.Color(1, 1, 1)).clone().multiply(new THREE.Color(...LIFT));
}
