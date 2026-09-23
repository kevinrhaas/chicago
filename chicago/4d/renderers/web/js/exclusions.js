/**
 * exclusions.js — "what is not here", in the walkthrough.
 *
 * Eight buildings stand in a town the sources describe with roughly forty, and
 * from the air that emptiness is the most honest thing in the scene. What it
 * cannot show is the difference between three completely different statements:
 * a structure absent because nobody has researched it yet, one absent because
 * the evidence dates it after 1 July 1835, and one absent because it had already
 * come down. The first is a gap in the work. The other two are findings — they
 * cost research to establish, they carry citations, and until now they lived only
 * in `data/exclusions.json`, where the one audience that cannot read them is the
 * visitor standing in the gap.
 *
 * That file is the research record and stays authored by hand;
 * `tools/compile_scene.py` derives the per-scene view with the citations joined,
 * filtered by the scene's own year — an entry dating a building to 1837 is not an
 * exclusion from an 1837 scene — and `tools/check.sh` re-derives it, so this list
 * cannot fall behind the record it is quoting.
 *
 * The list deliberately does NOT claim to be everything missing. Most of the town
 * is simply not built yet, and saying otherwise would turn an honest hole into a
 * false claim of completeness — which is the failure mode this whole panel exists
 * to avoid.
 */

import { citationItems, escapeHtml } from './citations.js';

/**
 * One excluded structure, collapsed. Same `<details>` shape as a liberty, because
 * they are the same kind of disclosure and a visitor should not have to learn two
 * interfaces to read a confession.
 */
export function exclusionEntryHtml(ex) {
  // The chip is the record's own field, never a phrase derived from its absence:
  // an entry with no `earliest_scene` was excluded because it was GONE, not
  // because it was late, and inventing "gone by 1835" for it would be this
  // project's own sin in miniature. Those entries carry no chip; their reason
  // line says what happened.
  const when = ex.earliest_scene
    ? `<span class="lib-scope">not until ${escapeHtml(ex.earliest_scene)}</span>`
    : '';

  const detail = ex.detail
    ? `<dt>Detail</dt><dd>${escapeHtml(ex.detail)}</dd>`
    : '';

  return `<details class="lib excl">
    <summary>
      <span class="lib-title">${escapeHtml(ex.name || ex.id)}</span>
      ${when}
    </summary>
    <dl class="lib-body">
      <dt>Why it is not here</dt><dd>${escapeHtml(ex.reason || '')}</dd>
      ${detail}
    </dl>
    <ol class="cites excl-cites">${citationItems(ex.citations, {
      empty: 'No citation recorded for this exclusion.',
      // The one place the citation's own account of itself is withheld. A
      // source describing what it carries names buildings, and one of them —
      // the Western Hotel, in the Inter Ocean piece behind two entries here —
      // is standing in this scene. Under a heading that means "not here", that
      // is a claim about the town rather than about the source, and the smoke
      // asserts it cannot happen. See citations.js.
      evidence: false,
    })}</ol>
  </details>`;
}

/**
 * One open question, collapsed like an exclusion and a liberty, because it is the
 * same kind of disclosure with a different answer at the end.
 *
 * The chip is derived from the scene, not from the entry: whether a structure
 * resolves into 1 July 1835 is a fact about the dataset and the date, and the
 * compiler answers it. That is what keeps this section from being false about the
 * one building on it a visitor can walk up to — the Western Hotel is HERE, and its
 * doubt is about the date on its own card rather than about whether to build it.
 *
 * `onCard` is the same affordance the liberties have: one renderer, two surfaces,
 * so the panel and the provenance card cannot describe one uncertainty
 * differently. Two things change and nothing else does. The chip drops "standing
 * here", which on the card is the visitor's own position rather than news, and
 * carries only the grade of the claim the doubt sits on — a field's value, not a
 * phrase composed here. And the line that points at the card stops pointing at
 * the card it is printed on: on the panel it says the provenance card shows this
 * claim, and on the card it names the claim shown a few centimetres above.
 *
 * @param {object} u  one entry of the compiled `uncertain` list
 * @param {object} [opts]
 * @param {boolean} [opts.onCard]  rendered inside the provenance popup
 */
export function uncertaintyEntryHtml(u, { onCard = false } = {}) {
  const chip = onCard
    ? `<span class="lib-scope">${escapeHtml(u.carried_confidence || 'graded')}</span>`
    : u.standing
    ? `<span class="lib-scope">standing here — ${escapeHtml(u.carried_confidence || 'graded')}</span>`
    : '<span class="lib-scope">not built</span>';

  const consequence = u.consequence
    ? `<dt>What it would change</dt><dd>${escapeHtml(u.consequence)}</dd>`
    : '';

  // For a structure that IS in the scene, name the claim on its record that
  // carries the doubt, so this section and the provenance card cannot describe
  // the same uncertainty differently.
  const carried = u.standing && u.carried_by
    ? (onCard
      ? `<dt>Where it is carried</dt><dd>The doubt sits on this record's
         <code>${escapeHtml(u.carried_by)}</code>, graded
         <b>${escapeHtml(u.carried_confidence || '')}</b> — the claim shown above.</dd>`
      : `<dt>Where it is carried</dt><dd>This building is in the scene; the doubt sits on its
         <code>${escapeHtml(u.carried_by)}</code>, graded
         <b>${escapeHtml(u.carried_confidence || '')}</b>, and the provenance card shows it.</dd>`)
    : '';

  // An entry with no source record says so rather than showing an empty list of
  // citations, which would read as an oversight instead of the finding it is.
  const cites = u.no_source_record
    ? `<dl class="lib-body"><dt>No source record</dt>
       <dd>${escapeHtml(u.no_source_record)}</dd></dl>`
    : `<ol class="cites excl-cites">${citationItems(u.citations, {
        empty: 'No citation recorded for this question.',
        // Same reason as the exclusions above, and the same section of the
        // panel: what a source carries is not what this list is about.
        evidence: false,
      })}</ol>`;

  const dossier = u.dossier && u.dossier.file
    ? `<p class="legend-note">Research: <code>${escapeHtml(u.dossier.file)}</code>
       § ${escapeHtml(u.dossier.anchor || '')}</p>`
    : '';

  return `<details class="lib excl uncertain">
    <summary>
      <span class="lib-title">${escapeHtml(u.name || u.id)}</span>
      ${chip}
    </summary>
    <dl class="lib-body">
      <dt>What is open</dt><dd>${escapeHtml(u.question || '')}</dd>
      ${consequence}
      ${carried}
    </dl>
    ${cites}
    ${dossier}
  </details>`;
}

/**
 * The open questions about ONE structure — the join the provenance card needs.
 *
 * The same shape as `libertiesFor`: the panel says what the whole scene leaves
 * open, the card says what is open about the building you are standing in, and
 * both read one derived list so they cannot disagree. The join is the id, because
 * an entry names a structure and a card exists only for a structure in the scene;
 * `standing` is the compiler's separate answer to a different question and is
 * what the chip reads, not what selects.
 *
 * @param {object[]|null} uncertain  the compiled `uncertain` list
 * @param {string} structureId
 */
export function openQuestionsFor(uncertain, structureId) {
  if (!Array.isArray(uncertain)) return [];
  return uncertain.filter((u) => u.id === structureId);
}

/**
 * Fetch the scene's derived exclusions and render them into `mount`.
 *
 * Failure degrades the section and records a problem on the shared list, the same
 * way the liberties do — a missing file says so rather than rendering an empty
 * list, because an empty "what is not here" reads as "nothing was left out".
 *
 * The open questions ride the same fetch and the same derived file, because they
 * are the same document's other half: what was researched and ruled out, and what
 * was researched and could not be. One request, two mounts.
 *
 * `standardMount` and `uncertainStandardMount` take each list's own account of
 * what it is. `compile_scene.py` has written both sentences into this file since
 * the sections shipped and nothing rendered either: they were read into a return
 * value, which is enough for the derived-contract gate — that scan sees a NAME,
 * not a pixel — and the panel opened instead with a hand-written paraphrase of
 * each. Two statements of one thing with nothing holding them together is how a
 * panel and the document it quotes start disagreeing, and one of the paraphrases
 * had already drifted into a HAND-TYPED COUNT of the open questions, which goes
 * wrong the day a fifth is recorded. The compiled sentences are the ones on
 * screen now and the paraphrases are gone.
 *
 * @param {object} o
 * @param {HTMLElement|null} o.mount
 * @param {HTMLElement|null} [o.uncertainMount] where the open questions render
 * @param {HTMLElement|null} [o.standardMount] where the not-here list's own account goes
 * @param {HTMLElement|null} [o.uncertainStandardMount] the same, for the open questions
 * @param {URL} o.dataBase        where data/ lives
 * @param {string} o.sceneId      the scene whose sidecars to read
 * @param {string[]} [o.problems] the shared collector
 */
export async function mountExclusions({ mount, uncertainMount = null,
                                        standardMount = null,
                                        uncertainStandardMount = null,
                                        dataBase, sceneId, problems = [] }) {
  let doc = null;
  try {
    const url = new URL(`sidecars/${sceneId}/exclusions.json`, dataBase);
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    doc = await res.json();
  } catch (err) {
    problems.push(`exclusions: ${err.message} — the "what is not here" list is not shown`);
    for (const el of [mount, uncertainMount]) {
      if (!el) continue;
      el.innerHTML = '<p class="legend-note">The list of researched exclusions could not '
        + 'be loaded. It is committed at <code>data/exclusions.json</code>.</p>';
      el.removeAttribute('aria-busy');
    }
    // Emptied rather than left saying "Loading…", which after a failed fetch is
    // the panel telling a visitor to wait for something that is not coming —
    // the same degradation the liberties note takes.
    for (const el of [standardMount, uncertainStandardMount]) {
      if (!el) continue;
      el.textContent = '';
      el.removeAttribute('aria-busy');
    }
    return { count: 0, excluded: [], uncertainCount: 0, uncertain: [],
             error: String(err.message || err) };
  }

  // Verbatim, and before the entries: each sentence is the frame the list under
  // it is read inside, and a claim about the dataset's completeness is the last
  // text on this panel that should be restated in somebody else's words.
  if (standardMount) {
    standardMount.textContent = doc.standard || '';
    standardMount.removeAttribute('aria-busy');
  }
  if (uncertainStandardMount) {
    uncertainStandardMount.textContent = doc.uncertain_standard || '';
    uncertainStandardMount.removeAttribute('aria-busy');
  }

  const excluded = Array.isArray(doc.excluded) ? doc.excluded : [];
  if (mount) {
    mount.innerHTML = excluded.map(exclusionEntryHtml).join('')
      || '<p class="legend-note">No researched exclusions recorded for this scene.</p>';
    mount.removeAttribute('aria-busy');
  }

  const uncertain = Array.isArray(doc.uncertain) ? doc.uncertain : [];
  if (uncertainMount) {
    uncertainMount.innerHTML = uncertain.map(uncertaintyEntryHtml).join('')
      || '<p class="legend-note">No open questions recorded for this scene.</p>';
    uncertainMount.removeAttribute('aria-busy');
  }

  return {
    count: excluded.length,
    excluded,
    standard: doc.standard,
    uncertainCount: uncertain.length,
    uncertain,
    uncertainStandard: doc.uncertain_standard,
    error: null,
  };
}
