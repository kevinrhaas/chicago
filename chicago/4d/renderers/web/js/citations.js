/**
 * citations.js — one way of showing a source, used everywhere a source is shown.
 *
 * The provenance card and the "what is not here" list both quote the same joined
 * citation records that `tools/compile_scene.py` writes into the sidecars. Two
 * renderers for one record is how two views start disagreeing about the evidence
 * — the liberties entry was pulled into one renderer for exactly that reason, and
 * this is the same move for the citation line.
 *
 * A citation with no archived copy says so. Whether a claim can be re-read is
 * part of the claim, and several of this project's hosts return 503 on a bad day.
 *
 * And a tier says what KIND of source it is, in words. The number alone has been
 * on this line since it was written — `tier 4`, at a visitor with no table to
 * look it up in — while the panel around it argues that a person should be able
 * to judge the evidence themselves. The words are compiled into the sidecar from
 * `data/source.schema.json` (see `tools/tiers.py`), which is the same ladder
 * `check_evidence_ladder` holds the dataset to, so what a value is graded
 * against and what a visitor is told cannot come apart.
 *
 * A rung is a judgement about a DOCUMENT, and on ten of these records the
 * document is not the page. `chicagology_lastwardance` is rung 2 because it
 * reprints the Chicago Tribune of 14 August 1910 carrying John Dean Caton's own
 * recollection — and a visitor following that citation arrived at a modern blog
 * stamped "tier 2 · near-primary recollection" with nothing here saying why,
 * which reads as an over-grade of the exact kind this ladder exists to prevent.
 * The reprints line is that reason, off `transcribes`; its opposite number
 * `carries_no_document` is the reading that established a page reprints nothing
 * at all, which is a finding and not an absence.
 *
 * And a source's own stated limits are on the line too. `hathaway_1834` records
 * that it does NOT supply building footprints — a claim that reached this
 * project's brief before anyone opened the scan at full resolution, and whose
 * correction then stayed in the repository for the life of the project. Showing
 * a source without its limits is the one thing this panel is not for.
 *
 * The limits collapse behind a `<details>`, for the reason the record's own
 * account does: several sources' lists run to three or four clauses each, and a
 * card with five citations open would push everything below it off a 62vh panel
 * on a phone. The reprints line does NOT collapse — it is one line, and it is
 * the line that makes the rung beside it legible.
 */

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

const list = (v) => (Array.isArray(v) ? v.filter(Boolean) : []);

/**
 * What document this page carries, in one line — or the finding that it carries
 * none. Rendered above the limits because it is what the rung is a judgement
 * about; a source that IS the document (a survey sheet, a book) says nothing
 * here, which is why a card stamping this on every citation is a bug rather
 * than a tidier design.
 */
function reprintsLine(c) {
  const t = list(c.transcribes);
  if (t.length) {
    return t.map((d) => `<p class="cite-reprints">reprints
      <span class="reprints-work">${escapeHtml(d.work ?? '')}</span>${d.date
        ? ` <span class="reprints-date">${escapeHtml(d.date)}</span>` : ''}</p>`).join('');
  }
  // Deliberately not "no document found": the field is a reading somebody did,
  // and the reading is in the details below.
  if (c.carries_no_document) return '<p class="cite-reprints">reprints no document</p>';
  return '';
}

/**
 * The source's own account of what it is good for, and what it is not.
 *
 * What is deliberately NOT here is the prose behind these two: the note inside
 * each `transcribes` entry and the reading in `carries_no_document`. Both are
 * addressed to whoever re-grades the source rather than to a visitor — they
 * quote rung numbers, name files in `data/`, and record HTTP statuses and
 * fetch dates. The finding they establish reaches the card (the document, or
 * that there is none); the working-out stays in the repository, where the
 * source record is one click away for anyone who wants it.
 */
function limitsBlock(c) {
  const supplies = list(c.what_it_supplies);
  const not = list(c.what_it_does_not_supply);
  const rows = [];
  if (supplies.length) {
    rows.push(`<p class="cite-lim-h">supplies</p><ul class="cite-lim">${
      supplies.map((s) => `<li>${escapeHtml(s)}</li>`).join('')}</ul>`);
  }
  if (not.length) {
    rows.push(`<p class="cite-lim-h">does not supply</p><ul class="cite-lim cite-lim-not">${
      not.map((s) => `<li>${escapeHtml(s)}</li>`).join('')}</ul>`);
  }
  if (!rows.length) return '';
  return `<details class="cite-more">
    <summary>what this source supplies, and does not</summary>${rows.join('')}</details>`;
}

/**
 * `<li>` rows for an `<ol class="cites">`.
 *
 * @param {object[]} citations  joined citation records: source_id, citation, url,
 *                              archived_url, tier, tier_label, and — when the
 *                              record carries them — transcribes,
 *                              carries_no_document, what_it_supplies,
 *                              what_it_does_not_supply
 * @param {object} [o]
 * @param {string} [o.empty]    what to say when there are none — the honest note
 *                              differs by context, and "none recorded" is itself
 *                              a finding rather than a blank
 * @param {boolean} [o.evidence] whether to show what the page reprints and what
 *                              the source says it cannot supply. On by default
 *                              and off in one place; see the note above the
 *                              `<li>` for why the not-here list is that place
 */
export function citationItems(citations, {
  empty = 'No citations in this record — that is itself a finding.',
  evidence = true,
} = {}) {
  if (!Array.isArray(citations) || !citations.length) return `<li>${escapeHtml(empty)}</li>`;
  return citations.map((c) => {
    const links = [];
    if (c.url) links.push(`<a href="${escapeHtml(c.url)}" target="_blank" rel="noopener">source</a>`);
    if (c.archived_url) {
      links.push(`<a href="${escapeHtml(c.archived_url)}" target="_blank" rel="noopener">archived</a>`);
    } else if (c.url) {
      links.push('<span title="No archived copy recorded; this link may not survive">not archived</span>');
    }
    // the label is the point; the bare number is the fallback for a rung the
    // compiled ladder has no words for, which is a finding for the validator
    // rather than something to print a guess about
    const tier = c.tier
      ? `<span class="tier">tier ${escapeHtml(c.tier)}${c.tier_label ? ` · ${escapeHtml(c.tier_label)}` : ''}</span>`
      : '';
    // The one context that turns this off is "What is not here", and the smoke
    // found the reason rather than a reviewer. A source's own account of what it
    // carries names buildings — `chicagology_prefire278` reprints the Inter
    // Ocean's "The Old Western Hotel: First Frame House on the West Side" — and
    // the Western Hotel is standing in this scene. Printed under a list of
    // researched absences, that sentence reads as a claim about the town, which
    // is the one thing that section may not do. The exclusion's own citation
    // line still says what it is and what rung it is on.
    const ev = evidence ? `${reprintsLine(c)} ${limitsBlock(c)}` : '';
    return `<li><span class="cite-text">${escapeHtml(c.citation ?? c.source_id)}</span>
      ${tier} ${links.join(' · ')}
      ${ev}</li>`;
  }).join('');
}
