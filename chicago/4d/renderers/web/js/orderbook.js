/**
 * orderbook.js — "Reconstructing the town", in the Evidence hub.
 *
 * T-1166. The walkthrough can show a visitor the town that IS standing. What it
 * has never been able to show is the town that is NOT: how many people the
 * models say were here on 1 July 1835 against the four hundred and fifty-six the
 * sources name, how many households, how many shops, how many roofs — and which
 * ticket owes each one. That arithmetic decided the whole shape of the next
 * three bands, and until now it lived in a JSON file in the repository, where
 * the one audience it is actually about cannot read it.
 *
 * It renders `data/reconstruction/1835_reconstruction_order_book.json` — the same
 * document `tools/build_order_book_1835.py --build` writes and `--check`
 * re-derives — and knows nothing about how any quota was arrived at. One
 * `<details>` per bucket family, in the document's own order, then the deltas the
 * roof programme still owes and the invariants the convergence tickets assert.
 *
 * IT IS ALSO THE PROGRESS VIEW. Every bucket carries a `filled` counter that the
 * reconstruction tools write through their own `--build`, so as the bands below
 * run, the bars on this panel fill. Nothing here is updated by hand: a bar that
 * has not moved is a band that has not run.
 *
 * NO NUMBER IS TYPED HERE, exactly as in population.js. Every figure comes out of
 * the JSON, so a model or a layer that moves moves this panel through the
 * generator and the gate, and a book that has fallen behind its inputs is red in
 * `check.sh` rather than wrong on the deployed site.
 */

import { escapeHtml } from './citations.js';

const num = (v) => (v === null || v === undefined ? '—' : Number(v).toLocaleString('en-US'));

/** A filled/to-do bar. Width is the ratio, and the ratio is the only claim it makes. */
function barHtml(filled, todo) {
  if (!todo) return '';
  const pct = Math.max(0, Math.min(100, Math.round((filled / todo) * 100)));
  return `<div class="ob-bar" role="img"`
    + ` aria-label="${num(filled)} of ${num(todo)} reconstructed">`
    + `<span style="width:${pct}%"></span></div>`;
}

/** The columns a bucket actually has: the families do not all carry the same ones. */
function bucketRow(b) {
  const target = b.target ?? b.roofs_gated ?? null;
  const known = b.known ?? (b.known_attested === undefined
    ? (b.standing ?? null)
    : (b.known_attested || 0) + (b.known_inferred || 0));
  const todo = b.to_reconstruct ?? b.to_build ?? null;
  const owner = b.owning_ticket || (b.owning_tickets || []).join(', ') || '—';
  return `<tr><td><code>${escapeHtml(b.key)}</code></td>`
    + `<td class="num">${num(target)}</td><td class="num">${num(known)}</td>`
    + `<td class="num">${num(todo)}</td><td class="num">${num(b.filled)}</td>`
    + `<td>${escapeHtml(owner)}</td></tr>`;
}

/** One bucket family, collapsed — the same `<details>` shape as a liberty. */
export function familyHtml(family) {
  const buckets = family.buckets || [];
  const todo = buckets.reduce((n, b) => n + (b.to_reconstruct ?? b.to_build ?? 0), 0);
  const filled = buckets.reduce((n, b) => n + (b.filled || 0), 0);
  const summary = Object.entries(family.summary || {})
    .filter(([, v]) => typeof v === 'string' || typeof v === 'number')
    .map(([k, v]) => `<p class="legend-note pop-note"><b>${escapeHtml(k.replace(/_/g, ' '))}</b> — `
      + `${escapeHtml(typeof v === 'number' ? num(v) : v)}</p>`).join('');
  return `<details class="lib pop ob">
    <summary>
      <span class="lib-title">${escapeHtml(family.title)}</span>
      <span class="lib-scope">${num(filled)} of ${num(todo)} done</span>
    </summary>
    <div class="lib-body">
      <p class="pop-lead">${escapeHtml(family.lead || '')}</p>
      ${barHtml(filled, todo)}
      ${summary}
      <figure class="pop-table"><div class="pop-scroll"><table>
        <thead><tr><th>bucket</th><th class="num">target</th><th class="num">known</th>
          <th class="num">to do</th><th class="num">filled</th><th>ticket</th></tr></thead>
        <tbody>${buckets.map(bucketRow).join('')}</tbody>
      </table></div></figure>
    </div>
  </details>`;
}

/** The deltas the roof programme still owes, and the invariants that close the town. */
function listHtml(title, chip, lead, rows) {
  return `<details class="lib pop ob">
    <summary><span class="lib-title">${escapeHtml(title)}</span>
      <span class="lib-scope">${escapeHtml(chip)}</span></summary>
    <div class="lib-body">
      <p class="pop-lead">${escapeHtml(lead)}</p>
      ${rows.join('')}
    </div>
  </details>`;
}

export async function mountOrderBook({ mount, noteMount = null, dataBase, problems = [] }) {
  let doc = null;
  try {
    const url = new URL('reconstruction/1835_reconstruction_order_book.json', dataBase);
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    doc = await res.json();
  } catch (err) {
    problems.push(`reconstruction order book: ${err.message} — the town's quota is not shown`);
    if (mount) {
      mount.innerHTML = '<p class="legend-note">The reconstruction order book could not be loaded. '
        + 'It is committed at <code>data/reconstruction/1835_reconstruction_order_book.json</code>.</p>';
      mount.removeAttribute('aria-busy');
    }
    // Emptied rather than left saying "Loading…", for population.js's reason: after a
    // failed fetch that is the panel telling a visitor to wait for something not coming.
    if (noteMount) { noteMount.textContent = ''; noteMount.removeAttribute('aria-busy'); }
    return { count: 0, families: [], error: String(err.message || err) };
  }

  const t = doc.totals || {};
  if (noteMount) {
    noteMount.textContent = `The models want ${num(t.persons_target)} people in `
      + `${num(t.households_target)} households under ${num(t.roofs_target)} roofs. `
      + `The sources name ${num(t.persons_known)} of those people and `
      + `${num(t.roofs_standing)} of those roofs are standing, so `
      + `${num(t.persons_to_reconstruct)} people, ${num(t.households_to_reconstruct)} households, `
      + `${num(t.businesses_to_reconstruct)} businesses and ${num(t.roofs_to_build)} roofs are `
      + `still to reconstruct. Every one of them will be marked reconstructed, with its reason. `
      // THE NUMBER SAID OUT LOUD (T-1463). The panel printed target, known and to-do and
      // never once multiplied them out against the town already standing, which is how the
      // book came to order a replacement for 826 people the layer held. This sentence is
      // that arithmetic, and the same figures the builder refuses to ship outside the range.
      + `${num(t.persons_standing)} of them already stand, so filling the book converges on `
      + `${num(t.persons_when_the_book_is_filled)} people — inside the model's `
      + `${num(t.persons_target_range && t.persons_target_range[0])}–`
      + `${num(t.persons_target_range && t.persons_target_range[1])}.`;
    noteMount.removeAttribute('aria-busy');
  }

  if (mount) {
    const families = (doc.bucket_families || []).map(familyHtml);
    // `programme groups` names what the programme side actually sums, and a row that reads
    // its model figure off those same groups says so rather than showing a zero that looks
    // like an agreement (T-1439).
    const deltas = (doc.programme_deltas || []).map((d) => {
      const groups = (d.programme_groups || []).join(' + ');
      return `<p class="legend-note pop-note">`
        + `<b>${escapeHtml(d.id.replace(/_/g, ' '))}</b> — ${escapeHtml(d.statement)} `
        + `<span class="ob-delta">model ${num(d.model)} · programme ${num(d.programme)}`
        + `${groups ? ` (${escapeHtml(groups)})` : ''}</span></p>`;
    });
    const invariants = (doc.invariants || []).map((i) => `<p class="legend-note pop-note">`
      + `<b>${escapeHtml(i.id.replace(/_/g, ' '))}</b> (${escapeHtml(i.owning_ticket)}) — `
      + `${escapeHtml(i.statement)} <i>Now: ${escapeHtml(i.measured_now)}</i></p>`);
    mount.innerHTML = [
      ...families,
      listHtml('Where the model and the roof programme disagree',
        `${deltas.length} delta${deltas.length === 1 ? '' : 's'}`,
        'The book carries the model. Every difference is listed for the ticket that re-cuts '
        + 'the 668-roof schedule against it.', deltas),
      listHtml('What must be true when the town is finished',
        `${invariants.length} invariant${invariants.length === 1 ? '' : 's'}`,
        'The assertions the convergence tickets close on, each measured as it stands today.',
        invariants),
    ].join('');
    mount.removeAttribute('aria-busy');
  }
  return {
    count: (doc.bucket_families || []).length + 2,
    families: doc.bucket_families || [],
    totals: t,
  };
}
