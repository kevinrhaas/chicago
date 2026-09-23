/**
 * ground.js — what the ground claims, in the walkthrough.
 *
 * Every building in this scene can tell you what it asserts, how sure we are of
 * it, which sources say so, and where the record is weakest. The surface all of
 * them stand on could tell you none of that, and it is not because the ground
 * had nothing to say: `data/terrain/epochs/<e>/terrain_spec.json` grades itself
 * as carefully as any structure record. A documented water plane. Three inferred
 * division levels argued out of period narrative feet. A conjectural bank face
 * that is the largest unsourced assumption in the build, and a channel
 * cross-section whose own note says it carries no evidence at all.
 *
 * None of it reached a visitor. The ground even DITHERS under the confidence
 * view — the terrain mesh carries the same `_CONFIDENCE` channel a building
 * does — so the walkthrough has been showing that a grade exists while saying
 * nothing about what was graded, which is the least useful half of the claim.
 *
 * Derived, never authored here: `tools/compile_scene.py` reads the spec and the
 * generated heightfield and writes `sidecars/<scene>/terrain.json`, and
 * `tools/check.sh` re-derives it, so this section cannot fall behind the spec it
 * is quoting. `tools/validate.py` holds those claims to the same citation rule a
 * record answers to — which nothing did while the file was read only by the
 * generator.
 *
 * Nothing here composes a display value. A claim's figures are the spec's own
 * numbers under the spec's own key names; its reasoning is the spec's note,
 * verbatim; and a claim with no reasoning recorded says exactly that, because a
 * section that quietly rendered a blank would be hiding the one thing this panel
 * exists to show. Three INFERRED claims had none when this was written and none
 * do since 2026-08-10, so the case that matters — a claim that owes an argument
 * and gives none — is no longer in the data and the smoke exercises it directly
 * rather than letting a disclaimer rot unseen. Two documented soil claims still
 * show it, and that is the right reading: they cite evidence and were never
 * asked for an argument.
 */

import { citationItems, escapeHtml } from './citations.js';
import { geometryMark } from './geometry.js';

/** `near_ft` -> `near (ft)`. The unit lives in the key; a visitor should not. */
function fieldName(key) {
  return String(key).replace(/_(ft|m|m2|deg)$/, ' ($1)').replace(/_/g, ' ');
}

/**
 * A field value as the spec states it.
 *
 * Underscores are opened up only in a value that is a single token —
 * `black_loam_over_quicksand_over_blue_clay` is a phrase written as an
 * identifier and reads as a phrase. A value that already contains spaces is a
 * sentence or a formula somebody wrote, and rewriting it would be editing the
 * record on the way to the screen.
 */
function fieldValue(value) {
  if (Array.isArray(value)) return value.map(fieldValue).join(' – ');
  if (value === true) return 'yes';
  if (value === false) return 'no';
  if (typeof value === 'number') return String(value);
  const s = String(value);
  return /\s/.test(s) ? s : s.replace(/_/g, ' ');
}

function chip(confidence) {
  const c = confidence || 'reconstructed';
  return `<span class="conf conf-${escapeHtml(c)}">${escapeHtml(c)}</span>`;
}

/**
 * One graded statement the ground makes, collapsed — the same `<details>` shape
 * as a liberty and an exclusion, because a visitor should not have to learn a
 * third interface to read the same kind of disclosure.
 */
export function groundClaimHtml(claim) {
  // A figure the terrain generator does not read is marked with the same words
  // the provenance card uses on a building's attribute, from the same module.
  // The ground's version of the Wolf Point wolf sign is on this panel: two
  // surface materials are `documented`, and the mesh draws almost none of what
  // they describe, so a chip alone tells a visitor how sure we are of a soil
  // they are largely not looking at. NARROWED BY T-1055, which took the sentence
  // "the ground is one earth colour from one edge of the box to the other" out of
  // this comment by making it false: terrain.js now paints the two flora zones
  // with box extents — z09_sand_prairie and z08_lakeshore, the beach-ridge belt
  // and the lakeshore, the sand bar inside them — their own recorded
  // `ground.rgb`. It is still the right warning everywhere else. The soil claims
  // on this panel are the terrain spec's `surface_materials`, whose every entry
  // still reads `"mesh": { "material": "simplified" }`, and the prairie the rest
  // of the box is drawn in is a texture, not those records.
  const rows = (claim.fields || []).map((f) => `
    <dt>${escapeHtml(fieldName(f.key))}</dt>
    <dd>${escapeHtml(fieldValue(f.value))}${geometryMark(f.mesh)}</dd>`).join('');

  // An `inferred` value with no stated reasoning is an error on a structure
  // record and, since 2026-08-10, on a ground claim too — so the empty state is
  // now a guard rather than a finding: a spec that slipped past the gate says so
  // to a visitor at the same moment a reviewer would see it.
  const notes = (claim.notes || []).filter((n) => String(n).trim());
  const reasoning = notes.length
    ? notes.map((n) => `<dd class="ground-note">${escapeHtml(n)}</dd>`).join('')
    : '<dd class="ground-note">No reasoning is recorded for this claim.</dd>';

  return `<details class="lib ground">
    <summary>
      <span class="lib-title">${escapeHtml(fieldName(claim.label))}</span>
      <span class="lib-scope">${escapeHtml(claim.group)}</span>
      ${chip(claim.confidence)}
    </summary>
    <dl class="lib-body">
      ${rows}
      <dt>Why</dt>${reasoning}
    </dl>
    <ol class="cites ground-cites">${citationItems(claim.citations, {
      empty: 'No source is cited for this claim.',
    })}</ol>
  </details>`;
}

/**
 * Fetch the scene's derived ground claims and render them into `mount`.
 *
 * Failure degrades the section and records a problem, the same way the liberties
 * and the exclusions do: an empty list where the ground's claims should be reads
 * as "the ground claims nothing", which is the opposite of true.
 *
 * @param {object} o
 * @param {HTMLElement|null} o.mount
 * @param {URL} o.dataBase        where data/ lives
 * @param {string} o.sceneId      the scene whose sidecars to read
 * @param {string[]} [o.problems] the shared collector
 */
export async function mountGround({ mount, dataBase, sceneId, problems = [] }) {
  let doc = null;
  try {
    const url = new URL(`sidecars/${sceneId}/terrain.json`, dataBase);
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    doc = await res.json();
  } catch (err) {
    problems.push(`ground: ${err.message} — the terrain's own claims are not shown`);
    if (mount) {
      mount.innerHTML = '<p class="legend-note">The ground\'s claims could not be loaded. '
        + 'They are committed at <code>data/terrain/epochs/</code>.</p>';
      mount.removeAttribute('aria-busy');
    }
    return { count: 0, claims: [], error: String(err.message || err) };
  }

  const claims = Array.isArray(doc.claims) ? doc.claims : [];
  if (mount) {
    // WHICH ground. The claims below are about a 640 m box at the forks and say
    // nothing about the town east of it, which a visitor who has flown up and
    // seen the ground end has every reason to ask about. The spec has stated
    // its own extent since it was written and the sentence had never left the
    // repository — compiled into this sidecar, read by nobody, for the life of
    // the project. It comes first because it is the frame every claim under it
    // is read inside.
    const covers = doc.scope
      ? `<p class="legend-note ground-scope"><b>What these claims cover</b> — ${
        escapeHtml(doc.scope)}</p>` : '';
    // The caveat is the spec's, verbatim and first: it is the sentence that says
    // no land elevation here is better than inferred, and every claim below it
    // is read differently once you have it.
    const caveat = doc.standard
      ? `<p class="legend-note ground-standard">${escapeHtml(doc.standard)}</p>` : '';
    const context = (doc.context || []).map((c) => `
      <p class="legend-note"><b>${escapeHtml(c.label)}</b> — ${escapeHtml(c.text)}</p>`).join('');
    // The terrain's own "what is not here": zones this project researched, sited,
    // and left outside the modelled box. Same disclosure, one scale up.
    const outside = (doc.not_modelled || []).length
      ? `<p class="legend-note"><b>Researched and outside this box</b> — ${
        doc.not_modelled.map((z) => escapeHtml(z.why)).join('; ')}.</p>`
      : '';
    mount.innerHTML = covers + caveat + context
      + (claims.map(groundClaimHtml).join('')
        || '<p class="legend-note">This scene\'s terrain records no graded claims.</p>')
      + outside;
    mount.removeAttribute('aria-busy');
  }
  // `scope` rides the handle so the smoke can compare what a visitor reads
  // against what the spec recorded, rather than against a phrase copied into the
  // test — the comparison that would have caught this field being unread.
  return { count: claims.length, claims, standard: doc.standard, scope: doc.scope,
           error: null };
}
