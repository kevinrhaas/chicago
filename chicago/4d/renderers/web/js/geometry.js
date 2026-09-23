/**
 * geometry.js — "you are not looking at this", in the visitor's words.
 *
 * A confidence chip answers how sure we are of a value. It cannot answer whether
 * the value is in front of you, and the two come apart in the worst possible
 * direction: the Wolf Point Tavern's painted wolf sign was `documented`, the
 * strongest claim this project makes, on a building with no sign on it — and the
 * ground says, `documented`, that the South Division is black loam over
 * quicksand over blue clay, on a surface that is one earth colour from one edge
 * of the box to the other.
 *
 * Both halves of the walkthrough now report that, so the mark lives in one place
 * rather than two. The provenance card takes it from a record's `geometry:`
 * declaration and the Evidence panel's ground section from a terrain claim's
 * `mesh:` map — different keys because in a GeoJSON `geometry` is the
 * coordinates (see `generators/terrain_inputs.py`), one vocabulary, and one
 * sentence shown to a visitor either way.
 *
 * `record_only` and `restated_in_code` get no marker, on purpose and for
 * opposite reasons. A rejected reading carried in a record is not a thing
 * missing from the view, and marking it would send a visitor looking for
 * something that was never there. A value the generator restates in code — the
 * water plane's literal zero, the bank's ease-out — describes the ground
 * accurately; the fact that no line of data drives it is a warning to whoever
 * edits the generator, not a caveat to somebody standing on it.
 */

import { escapeHtml } from './citations.js';

export const GEOMETRY_LABEL = {
  absent: ['not built', 'Attested, and nothing of it is in the model.'],
  simplified: ['not modelled from this', 'Something stands in its place, but this value does not drive it.'],
};

/** The mark for one declaration, or nothing at all. */
export function geometryMark(state) {
  const mark = GEOMETRY_LABEL[state];
  if (!mark) return '';
  return `<span class="geom geom-${escapeHtml(state)}" title="${escapeHtml(mark[1])}"
    >${escapeHtml(mark[0])}</span>`;
}
