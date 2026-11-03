/** Compiled occupied components beside a building's unchanged core reference.
 * One owner may have several solid rings; the ground between them stays open.
 * No archetype/layout logic belongs here: the compiler supplies the exact rings.
 */
export function occupiedPolygons(raw) {
  const core = Array.isArray(raw) ? raw : raw?.polygon;
  const result = Array.isArray(core) && core.length >= 3 ? [core] : [];
  const extras = Array.isArray(raw) ? [] : (raw?.additional_polygons ?? []);
  if (!Array.isArray(extras)) throw new Error('footprint.additional_polygons must be an array');
  for (const part of extras) {
    const polygon = part?.polygon;
    if (!Array.isArray(polygon) || polygon.length < 3
        || polygon.some(p => !Array.isArray(p) || p.length !== 2 || !p.every(Number.isFinite))) {
      throw new Error('malformed additional occupied polygon');
    }
    result.push(polygon);
  }
  return result;
}
