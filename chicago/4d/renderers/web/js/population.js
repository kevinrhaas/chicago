/**
 * population.js — "The town's people, 1 July 1835", in the Evidence hub.
 *
 * T-1160. The walkthrough can show a visitor 371 roofs and a few dozen named
 * people standing under them, and what it cannot show is the SHAPE of what is
 * known: that 1,282 person entries carry 10 dated ages between them, that 95% of
 * the arrival dates are a postal bound rather than an arrival, that the layer
 * holds no identified child at all. Those are the most important facts about this
 * reconstruction and until now they lived in a markdown file in the repository,
 * where the one audience that cannot read them is the visitor standing in the town.
 *
 * It renders `data/reconstruction/1835_population_profile.json` — the same
 * document `tools/profile_population_1835.py --build` writes and `--check`
 * re-derives — and knows nothing about how any figure was arrived at. One
 * `<details>` per section, in the document's own order, each holding the section's
 * lead sentence, its tables and its notes. The hub counts `> details` children of
 * the mount, so the tile's number is the number of axes, which is the honest
 * thing for it to be.
 *
 * NO NUMBER IS TYPED HERE. Every figure comes out of the JSON, so a resident pass
 * that moves the layer moves this panel through the generator and the gate, and a
 * profile that has fallen behind its layer is red in `check.sh` rather than wrong
 * on the deployed site.
 */

import { escapeHtml } from './citations.js';

/** One table, as the JSON gives it: headers, an alignment string, rows. */
function tableHtml(t) {
  const aligns = t.aligns || 'l'.repeat(t.headers.length);
  const cell = (tag, text, i) => `<${tag}${aligns[i] === 'r' ? ' class="num"' : ''}>`
    + `${escapeHtml(String(text))}</${tag}>`;
  const head = t.headers.map((h, i) => cell('th', h, i)).join('');
  const body = t.rows.map((row) => '<tr>' + row.map((c, i) => cell('td', c, i)).join('') + '</tr>').join('');
  return `<figure class="pop-table">`
    + `<figcaption>${escapeHtml(t.title || '')}</figcaption>`
    + `<div class="pop-scroll"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`
    + (t.note ? `<p class="legend-note">${escapeHtml(t.note)}</p>` : '')
    + `</figure>`;
}

/** One axis of the profile, collapsed — the same `<details>` shape as a liberty. */
export function sectionHtml(section) {
  const tables = (section.tables || []).map(tableHtml).join('');
  const notes = (section.notes || [])
    .map((n) => `<p class="legend-note pop-note">${escapeHtml(n)}</p>`).join('');
  // The chip is the section's own first table's row count where it has one — a
  // measure of the axis, never a phrase invented about it.
  const rows = (section.tables || []).reduce((n, t) => n + t.rows.length, 0);
  return `<details class="lib pop">
    <summary>
      <span class="lib-title">${escapeHtml(section.title)}</span>
      <span class="lib-scope">${rows} row${rows === 1 ? '' : 's'}</span>
    </summary>
    <div class="lib-body">
      <p class="pop-lead">${escapeHtml(section.lead || '')}</p>
      ${tables}
      ${notes}
    </div>
  </details>`;
}

export async function mountPopulation({ mount, noteMount = null, dataBase, problems = [] }) {
  let doc = null;
  try {
    const url = new URL('reconstruction/1835_population_profile.json', dataBase);
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    doc = await res.json();
  } catch (err) {
    problems.push(`population profile: ${err.message} — the town's people list is not shown`);
    if (mount) {
      mount.innerHTML = '<p class="legend-note">The population profile could not be loaded. '
        + 'It is committed at <code>data/reconstruction/1835_population_profile.json</code>.</p>';
      mount.removeAttribute('aria-busy');
    }
    // Emptied rather than left saying "Loading…", which after a failed fetch is the
    // panel telling a visitor to wait for something that is not coming.
    if (noteMount) { noteMount.textContent = ''; noteMount.removeAttribute('aria-busy'); }
    return { count: 0, sections: [], error: String(err.message || err) };
  }

  const c = doc.counts || {};
  if (noteMount) {
    // The lead is assembled from the document's own counts, so it cannot drift from
    // the tables under it the way a sentence typed into the markup would.
    noteMount.textContent = `${c.persons} person entries in ${c.households} households, `
      + `profiled on ${(doc.sections || []).length} axes. `
      + `${c.persons_with_a_sex} carry a sex, ${c.persons_with_a_dated_age} a dated age, `
      + `${c.persons_with_a_role} a role. It is a profile of the evidence, not of the town: `
      + `the town census of November 1835 counts 3,265 people.`;
    noteMount.removeAttribute('aria-busy');
  }

  if (mount) {
    mount.innerHTML = (doc.sections || []).map(sectionHtml).join('');
    mount.removeAttribute('aria-busy');
  }
  return { count: (doc.sections || []).length, sections: doc.sections || [], counts: c };
}
