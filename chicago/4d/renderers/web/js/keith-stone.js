/** T-1883: Keith's light granite, independent of Glessner's tint.
 * The September 1886 Inland Architect notice calls the front granite. Its quarry
 * and colour are not named. The neutral light greige is reconstructed from the
 * pale front in the period photographs and the blue-cast 1965 colour print.
 * Applied at load so the glTF [0,1] colour factor does not clamp the lightening.
 * T-2566: re-read under neutral light (texture mean x tint, no sky or shade): the old
 * tint made the granite r/g 0.90, b/g 1.04, a green-grey, where the 1965 print's
 * shaded bow reads r/g 1.01 even under its blue cast. Both are now neutral at the
 * same lightness; the print's extra blue is its shade and cast, not the stone.
 * RECONSTRUCTED: docs/RESEARCH/k01-1808-keith-1883/stone-colour-measurement.json.
 */
import * as THREE from 'three';
export const KEITH_STONE = Object.freeze([2.17, 2.15, 2.35]);
export const KEITH_DRESSED_STONE = Object.freeze([0.82, 0.90, 1.16]);
const SLOTS = new Set(['rough_stone_trim','bay_stone','limestone_trim','dress_stone','stoop_stone','carved_trim']);
export function tintKeithStone(material, record) {
  if (record?.id !== 'keith_house_1808_prairie' || !SLOTS.has(material?.name) || material.userData.keithStone) return;
  material.userData.keithStone = 'light-neutral-greige';
  material.color = (material.color ?? new THREE.Color(1,1,1)).clone().multiply(new THREE.Color(...(['rough_stone_trim','bay_stone'].includes(material.name) ? KEITH_STONE : KEITH_DRESSED_STONE)));
}
