/** T-1883: Keith's light granite, independent of Glessner's tint.
 * The September 1886 Inland Architect notice calls the front granite. Its quarry
 * and colour are not named. The neutral light greige is reconstructed from the
 * pale front in the period photographs and the blue-cast 1965 colour print.
 * Applied at load so the glTF [0,1] colour factor does not clamp the lightening.
 */
import * as THREE from 'three';
export const KEITH_STONE = Object.freeze([1.95, 2.15, 2.45]);
export const KEITH_DRESSED_STONE = Object.freeze([0.72, 0.90, 1.23]);
const SLOTS = new Set(['rough_stone_trim','bay_stone','limestone_trim','dress_stone','stoop_stone','carved_trim']);
export function tintKeithStone(material, record) {
  if (record?.id !== 'keith_house_1808_prairie' || !SLOTS.has(material?.name) || material.userData.keithStone) return;
  material.userData.keithStone = 'light-neutral-greige';
  material.color = (material.color ?? new THREE.Color(1,1,1)).clone().multiply(new THREE.Color(...(['rough_stone_trim','bay_stone'].includes(material.name) ? KEITH_STONE : KEITH_DRESSED_STONE)));
}
