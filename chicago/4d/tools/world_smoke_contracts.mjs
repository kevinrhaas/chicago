/**
 * Semantic batch identities, from buildings.js' source-owned shader bindings.
 * T-3411: `brick:common_buff_common_6` is the one K03 panel the 1816 fort and the
 * Lake House wear (T-3387), every brick wall and stack in the town in one batch.
 */
export const STRUCTURE_BATCH_KEYS = Object.freeze([
  'opaque', 'night-windows-v2', 'roof:roof_board', 'roof:roof_shingle',
  'wall:clapboard', 'wall:hewn_log', 'brick:common_buff_common_6', 'lantern-glass',
].sort());

/** The groups that carry a relief map: two roof coverings, two wall substrates, one brick panel. */
export const MAPPED_BATCH = /^(roof|wall|brick):/;

export function structureBatchContract(batches) {
  const keys = batches.map((b) => b.key).sort();
  return keys.length === STRUCTURE_BATCH_KEYS.length
    && keys.every((key, i) => key === STRUCTURE_BATCH_KEYS[i])
    && batches.every((b) => b.owners.length > 0 && b.validMaterial
      && b.mapped === MAPPED_BATCH.test(b.key))
    && batches.filter((b) => b.mapped).length
      === STRUCTURE_BATCH_KEYS.filter((key) => MAPPED_BATCH.test(key)).length;
}

/** Both source readings retain their own liveness/absence contract. */
export function greenTreeYardMode({ enclosed, sheds, coveredWagons, ghostSpans,
  refusal, shoulderGeometry }) {
  if (enclosed === true) return sheds === 0 && coveredWagons === 0
    && ghostSpans === 0 && refusal === true && shoulderGeometry === true;
  return (enclosed === false || enclosed === null) && sheds === 1
    && coveredWagons === 1 && ghostSpans === 0 && refusal === false;
}
