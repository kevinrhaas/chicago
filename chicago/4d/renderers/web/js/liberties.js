/**
 * liberties.js — "what we made up", in the walkthrough.
 *
 * The project's standard is that a visitor should be able to tell you which
 * parts we made up. The confidence view and the provenance popup answer that
 * for attributes: pick a building and every value carries its own chip, its
 * sources and its reasoning.
 *
 * They cannot answer it for the decisions that belong to no attribute — that the
 * town is uniformly unpeopled, that two prairie swales were drawn where nothing
 * attests them, that the river is a wall to the walker, that the ground past the
 * box is a skirt and not a claim. Those are the liberties, they are written in
 * `docs/LIBERTIES.md`, and until this module they shipped nowhere a visitor
 * could read them. A confession filed where only the confessor looks is not one.
 *
 * The list is derived, never authored here: `tools/compile_liberties.py` turns
 * the append-only markdown into `data/liberties.json` and `tools/check.sh`
 * re-derives it on every commit, so the panel cannot quietly fall behind the
 * document it is quoting.
 */

import { displayName } from './display-name.js';

/** Escape first, then re-admit exactly two markdown inflections. */
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function inline(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
}

/**
 * A `Covers:` aspect as a visitor should read it. `footprint` and `position` are
 * already words; the form attributes carry a `form.` prefix that exists to keep
 * the token unambiguous for the gate and means nothing on a chip. The rest
 * matches how the provenance card labels the same attribute, because the chip
 * and the attribute row are naming one thing.
 */
function aspectLabel(aspect) {
  return String(aspect).replace(/^form\./, '').replace(/_/g, ' ').replace(/\bm\b/, '(m)');
}

/**
 * A ground claim's id as a reader would say it.
 *
 * The id carries its group for uniqueness — `swales.west_prairie_swale_a` — and
 * the group is already the sentence the visitor is reading, so the chip shows
 * the last segment. `bank` and `micro_relief` have only that one.
 */
function groundClaimLabel(claim) {
  const parts = String(claim).split('.');
  return parts[parts.length - 1].replace(/_/g, ' ');
}

const SECTION_LABEL = {
  standing: 'whole scene',
  per_subject: 'one subject',
  resolved: 'resolved',
};

/**
 * One liberty as a collapsed `<details>`. Exported because the provenance popup
 * shows the same entries filtered to the building being inspected, and two
 * renderers for one record is how the two views start disagreeing about what
 * we admitted to.
 *
 * @param {object} lib                   a liberty from the derived list
 * @param {object} [o]
 * @param {Map<string,string>} [o.names] structure_id -> display name
 * @param {boolean} [o.showSubjects]     list what it constrains (off where the
 *                                       subject is already the thing on screen)
 * @param {boolean} [o.showScope]        show the scope chip; suppressed for
 *                                       `per_subject` in a per-subject context,
 *                                       where it would only restate the obvious
 */
export function libertyEntryHtml(lib, { names = new Map(), showSubjects = true, showScope = true } = {}) {
  const fields = (lib.fields || [])
    // Recorded/Revised are shown as a dateline, not as rows of their own, and
    // `Covers:` is shown as its chips — its raw tokens are the gate's business.
    .filter((f) => !/^(Recorded|Revised|Covers)$/i.test(f.label));

  const rows = fields.map((f) => `
    <dt>${escapeHtml(f.label)}</dt>
    <dd>${inline(f.text)}</dd>`).join('');

  const subjects = showSubjects
    ? (lib.subjects || [])
      .map((id) => `<span class="lib-subject">${escapeHtml(names.get(id) || id)}</span>`)
      .join('')
    : '';

  const scope = showScope
    ? `<span class="lib-scope">${escapeHtml(SECTION_LABEL[lib.section] || lib.section)}</span>`
    : '';

  // What this entry admits it invented, from the document's own `Covers:` field.
  // The commit gate reads the same claims against the records in both directions,
  // so a chip here is not a description of the entry — it is the assertion the
  // build refuses to ship without.
  //
  // Two domains, and the chip says which. A building's admission is read against
  // its record; the ground's is read against the epoch's terrain spec, and the
  // terrain is not a structure — the `domain` on the claim is the document's own
  // word for that rather than something inferred here from the token's shape.
  // "the ground" is not suppressed with the subjects, because it names which
  // half of the dataset the claim lands in and not which building.
  const seen = new Set();
  const covers = (lib.covers || []).map((c) => {
    const ground = c.domain === 'terrain';
    const who = ground ? 'the ground' : (showSubjects ? (names.get(c.structure) || c.structure) : '');
    const what = ground ? groundClaimLabel(c.claim) : aspectLabel(c.aspect);
    const label = `${who} ${what}`.trim();
    if (seen.has(label)) return '';
    seen.add(label);
    const token = ground
      ? ['terrain', c.epoch, c.claim].join('.')
      : [c.structure, c.phase, c.aspect].filter(Boolean).join('.');
    return `<span class="lib-covers" title="admitted for ${escapeHtml(token)}">`
      + `${escapeHtml(who)}${who ? ' ' : ''}<em>${escapeHtml(what)}</em></span>`;
  }).join('');

  const dateline = lib.revised && lib.revised !== lib.recorded
    ? `recorded ${escapeHtml(lib.recorded)} · revised ${escapeHtml(lib.revised)}`
    : `recorded ${escapeHtml(lib.recorded || '—')}`;

  return `<details class="lib">
    <summary>
      <span class="lib-id">${escapeHtml(lib.id)}</span>
      <span class="lib-title">${escapeHtml(lib.title)}</span>
      ${scope}
    </summary>
    <dl class="lib-body">${rows}</dl>
    <p class="lib-meta">${covers}${subjects}<span class="lib-date">${dateline}</span></p>
  </details>`;
}

/**
 * The liberties that constrain one structure.
 *
 * `subjects` is written by `tools/compile_liberties.py` from the markdown's own
 * subject line, so this filter is a lookup, not a judgement — a liberty appears
 * against a building because the document says it does.
 *
 * @param {object[]} liberties  the derived list
 * @param {string} subjectId    a structure_id
 */
export function libertiesFor(liberties, subjectId) {
  if (!subjectId || !Array.isArray(liberties)) return [];
  return liberties.filter((lib) => Array.isArray(lib.subjects) && lib.subjects.includes(subjectId));
}

/**
 * Fetch the derived liberties and render them into `mount`.
 *
 * Failure is reported, never papered over: a missing file leaves a line saying
 * the list could not be loaded and pushes the reason onto the loader's problem
 * list, the same one every other integration fault lands on.
 *
 * `noteMount` takes the document's own account of what this list is. That
 * sentence is compiled out of `docs/LIBERTIES.md` and was rendered nowhere,
 * while the panel opened with a hand-written paraphrase of it — two statements
 * of one thing with nothing holding them together, which is how the panel and
 * the document start disagreeing about what a liberty is. The markdown's
 * sentence is the one on screen now, and the paraphrase is gone.
 *
 * @param {object} o
 * @param {HTMLElement|null} o.mount    where the list goes
 * @param {HTMLElement|null} [o.noteMount] where the document's own note goes
 * @param {URL} o.dataBase              where data/ lives
 * @param {Map<string, object>} [o.registry]  loaded structures, for subject names
 * @param {string[]} [o.problems]       the shared collector
 */
export async function mountLiberties({ mount, noteMount = null, dataBase,
                                       registry = new Map(), problems = [] }) {
  const names = new Map();
  // The card's own title for the building, so a liberty's subject reads as the
  // building a visitor just clicked on rather than as its parcel number (T-0076).
  for (const [id, record] of registry) {
    names.set(id, displayName(record?.sidecar ?? {}, id).title || id);
  }

  let doc = null;
  try {
    const url = new URL('liberties.json', dataBase);
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    doc = await res.json();
  } catch (err) {
    problems.push(`liberties: ${err.message} — the "what we made up" list is not shown`);
    if (mount) {
      mount.innerHTML = '<p class="legend-note">The liberties list could not be loaded. '
        + 'It is committed at <code>docs/LIBERTIES.md</code>.</p>';
      mount.removeAttribute('aria-busy');
    }
    if (noteMount) {
      // Emptied rather than left saying "Loading…", which after a failed fetch
      // is the panel telling a visitor to wait for something that is not coming.
      noteMount.textContent = '';
      noteMount.removeAttribute('aria-busy');
    }
    return { count: 0, liberties: [], error: String(err.message || err) };
  }

  if (noteMount) {
    noteMount.textContent = doc.note || '';
    noteMount.removeAttribute('aria-busy');
  }

  const liberties = Array.isArray(doc.liberties) ? doc.liberties : [];
  if (mount) {
    mount.innerHTML = liberties.map((lib) => libertyEntryHtml(lib, { names })).join('')
      || '<p class="legend-note">No liberties recorded.</p>';
    mount.removeAttribute('aria-busy');
  }
  return { count: liberties.length, liberties, standard: doc.standard, note: doc.note,
           error: null };
}
