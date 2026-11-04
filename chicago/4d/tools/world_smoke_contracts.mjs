/** Semantic batch identities, from buildings.js' source-owned shader bindings. */
export const STRUCTURE_BATCH_KEYS = Object.freeze([
  'opaque', 'night-windows-v2', 'roof:roof_board', 'roof:roof_shingle',
  'wall:clapboard', 'wall:hewn_log', 'lantern-glass',
].sort());

export function structureBatchContract(batches) {
  const keys = batches.map((b) => b.key).sort();
  return keys.length === STRUCTURE_BATCH_KEYS.length
    && keys.every((key, i) => key === STRUCTURE_BATCH_KEYS[i])
    && batches.every((b) => b.owners.length > 0 && b.validMaterial
      && b.mapped === /^(roof|wall):/.test(b.key))
    && batches.filter((b) => b.mapped).length === 4;
}

/** Both source readings retain their own liveness/absence contract. */
export function greenTreeYardMode({ enclosed, sheds, coveredWagons, ghostSpans,
  refusal, shoulderGeometry }) {
  if (enclosed === true) return sheds === 0 && coveredWagons === 0
    && ghostSpans === 0 && refusal === true && shoulderGeometry === true;
  return (enclosed === false || enclosed === null) && sheds === 1
    && coveredWagons === 1 && ghostSpans === 0 && refusal === false;
}
