/**
 * fauna.js — the animals of 1 July 1835, in the Evidence panel.
 *
 * ROADMAP K51, from K42 finding 2. `data/fauna/` holds 139 animal records across
 * ten habitat zones, every one of them graded to the scene date and carrying its
 * sources — and until this module no file under `renderers/` named the directory
 * and `tools/publish.sh` did not copy it, so a browser had never been offered the
 * layer. Three separate documents implied otherwise. A researched dataset that
 * stops at the repository reads exactly like work that was never done, which is
 * the argument `tools/publish.sh` already makes in as many words about the
 * residents.
 *
 * WHAT THIS IS NOT. It is a card, not a herd: nothing here is drawn in the 3-D
 * scene, no animal geometry is proposed, and the standing constraint on
 * depicting people is untouched. The section says what the research says — what
 * each habitat reads as on the scene date, and for each animal its July status,
 * whether a visitor would see it, hear it, or find only its sign, how many of
 * them, what it would be doing, and which sources say so.
 *
 * WHY IT READS `data/fauna/` DIRECTLY. `tools/measure_layer_reads.py` scans the
 * renderer's own text for the read of every figure, so a layer routed through a
 * compiled intermediate would be a layer whose census could not be taken. The
 * zone records and the manifest are fetched as committed. The one thing that IS
 * compiled is the citation join — a bare `source_id` on a card is not a citation,
 * and `citations.js` is the one place a source is rendered, so
 * `tools/compile_scene.py` joins the seven sources this layer cites into
 * `sidecars/<scene>/fauna_sources.json` and this module looks them up by id.
 *
 * THE VOCABULARIES ARE READ, NOT RESTATED. The manifest carries eight closed
 * sets, and each one is both the order a chip row is sorted into and the list a
 * visitor is shown under "the words on these cards". A word this module invented
 * would be a gloss the dataset never agreed to; the sets are the dataset's own.
 */

import { citationItems, escapeHtml } from './citations.js';

/** A closed-set token as a reader should see it: `year_round_resident`. */
function words(token) {
  return String(token ?? '').replace(/_/g, ' ');
}

/** Order a value by its own vocabulary, unknown words last and marked. */
function rank(list, value) {
  const i = Array.isArray(list) ? list.indexOf(value) : -1;
  return i < 0 ? 999 : i;
}

/**
 * The confidence swatch the Evidence panel's own legend defines. One vocabulary
 * for the whole walkthrough: a fauna record grades `attested` / `inferred` /
 * `reconstructed` exactly as a building does, so it gets the same chip rather
 * than a second one meaning the same thing.
 */
function swatch(confidence) {
  const cls = { attested: 'sw-doc', inferred: 'sw-inf' }[confidence] || 'sw-rec';
  return `<i class="sw ${cls}" title="${escapeHtml(confidence || 'reconstructed')}"></i>`;
}

/** A `<dt>/<dd>` pair, omitted entirely when the record carries nothing. */
function row(label, value) {
  if (value === null || value === undefined || value === '') return '';
  return `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd>`;
}

/**
 * A graded claim — `july.status`, `july.presence`, `july.abundance` — as the
 * value, its grade, its reasoning and its sources. The reasoning is the point:
 * on this layer it routinely carries the argument that a source was read too
 * generously, and a card printing only the value would be hiding the best part
 * of the record.
 *
 * `value` is passed in beside the claim rather than dug out of it here, and that
 * is deliberate: `tools/measure_layer_reads.py` proves a read declaration by
 * finding the expression in this renderer's own text, so a field read through a
 * generic accessor is a field the census cannot see. Naming it at the call site
 * keeps the map honest at no cost to the reader.
 */
function claimRow(label, value, claim, citationsById) {
  if (!claim || value === undefined || value === null) return '';
  const note = claim.note ? `<br><span class="fauna-why">${escapeHtml(claim.note)}</span>` : '';
  const cites = (claim.sources || [])
    .map((id) => citationsById.get(id))
    .filter(Boolean);
  const list = cites.length
    ? `<ol class="cites excl-cites">${citationItems(cites)}</ol>`
    : '';
  return `<dt>${escapeHtml(label)}</dt>
    <dd>${swatch(claim.confidence)} <b>${escapeHtml(words(value))}</b>${note}${list}</dd>`;
}

/**
 * One animal, collapsed. Collapsed for the reason the liberties and the
 * exclusions are: twenty-one records in the marsh, each with three graded claims
 * and their reasoning, would push everything below this section off a phone.
 */
function speciesHtml(sp, vocab, citationsById) {
  const july = sp.july || {};
  const presence = july.presence?.value;
  const known = Array.isArray(vocab.presence_modes) && vocab.presence_modes.includes(presence);
  const presenceChip = presence
    ? `<span class="lib-scope${known ? '' : ' fauna-unknown'}">${escapeHtml(words(presence))}</span>`
    : '';

  const periods = Array.isArray(sp.active_periods) ? sp.active_periods : [];
  const ordered = [...periods].sort((a, b) => rank(vocab.active_periods, a) - rank(vocab.active_periods, b));
  const abroad = ordered.length
    ? `${words(sp.activity)} — ${ordered.map(words).join(', ')}`
    : words(sp.activity);

  const group = Number.isFinite(july.max_group)
    ? (july.max_group === 1 ? 'one at a time' : `up to ${july.max_group} together`)
    : '';

  return `<details class="lib fauna-sp">
    <summary>
      ${swatch(sp.confidence)}
      <span class="lib-title">${escapeHtml(sp.common || sp.id)}
        <em class="fauna-binomial">${escapeHtml(sp.binomial || '')}</em></span>
      ${presenceChip}
    </summary>
    <dl class="lib-body">
      ${row('On 1 July', july.behaviour)}
      ${row('What you would be looking at', july.appearance)}
      ${row('Sign it leaves', july.trace)}
      ${claimRow('Status on the scene date', july.status?.value, july.status, citationsById)}
      ${claimRow('Seen, heard, or neither', july.presence?.value, july.presence, citationsById)}
      ${claimRow('How many', july.abundance?.value, july.abundance, citationsById)}
      ${row('Voice in July', words(july.vocalization))}
      ${row('Abroad', abroad)}
      ${row('At most', group)}
      ${row('Kind', words(sp.class))}
      ${sp.note ? `<dt>Note on the record</dt><dd>${escapeHtml(sp.note)}</dd>` : ''}
    </dl>
  </details>`;
}

/** One habitat, with its species grouped in the manifest's own class order. */
function zoneHtml(zone, vocab, citationsById) {
  const species = Array.isArray(zone.species) ? [...zone.species] : [];
  species.sort((a, b) => (rank(vocab.classes, a.class) - rank(vocab.classes, b.class))
    || String(a.common || '').localeCompare(String(b.common || '')));

  const hero = Array.isArray(zone.soundscape?.hero) ? zone.soundscape.hero : [];
  const heroNames = hero
    .map((id) => species.find((s) => s.id === id))
    .filter(Boolean)
    .map((s) => s.common);
  const chorus = zone.soundscape?.dawn_chorus;
  const sound = chorus
    ? `<dt>What you would hear</dt><dd>Dawn chorus <b>${escapeHtml(words(chorus))}</b>${
      heroNames.length ? ` — led by ${escapeHtml(heroNames.join(', '))}` : ''}${
      zone.soundscape?.note ? `<br><span class="fauna-why">${escapeHtml(zone.soundscape.note)}</span>` : ''}</dd>`
    : '';

  // Two zones' habitats have no modelled ground in this scene. Saying so is not
  // a caveat bolted on: a visitor cannot walk to the bur oak savanna here, and a
  // list that read the same for ground the scene draws and ground it does not
  // would be making a claim about the town.
  const ground = zone.in_modelled_extent
    ? `<dd>The ground for this habitat is drawn in the scene, on the same extent as the
       plant community <code>${escapeHtml(zone.extent_from?.flora_zone || '')}</code>${
      zone.extent_from?.kind ? ` (${escapeHtml(words(zone.extent_from.kind))})` : ''}.</dd>`
    : `<dd>This habitat's ground is <b>not modelled</b> in this scene, so nothing here stands
       anywhere you can walk. The record is kept because the animals were there.</dd>`;

  const cites = (zone.sources || []).map((id) => citationsById.get(id)).filter(Boolean);

  return `<details class="lib fauna-zone">
    <summary>
      <span class="lib-id">${escapeHtml(words(zone.habitat))}</span>
      <span class="lib-title">${escapeHtml(zone.name || zone.id)}</span>
      <span class="lib-scope">${species.length} species</span>
    </summary>
    <dl class="lib-body">
      ${row('It reads as', zone.reads_as)}
      ${sound}
      <dt>Where it is</dt>${ground}
      ${zone.note ? `<dt>Note on the record</dt><dd>${escapeHtml(zone.note)}</dd>` : ''}
    </dl>
    ${cites.length ? `<ol class="cites excl-cites">${citationItems(cites)}</ol>` : ''}
    <div class="fauna-species">${species
      .map((sp) => speciesHtml(sp, vocab, citationsById)).join('')}</div>
  </details>`;
}

/**
 * The manifest's eight closed sets, shown rather than paraphrased.
 *
 * Every chip on every card above comes out of one of these lists, and the lists
 * are the dataset's own — `presence_modes` in particular carries the distinction
 * this whole layer is built on, between an animal a visitor would see, one they
 * would only hear, and one present as sign alone.
 */
function vocabularyHtml(vocab) {
  const sets = [
    ['Seen, heard, or neither', vocab.presence_modes],
    ['Status on the scene date', vocab.july_status],
    ['How many', vocab.abundance],
    ['Voice in July', vocab.vocalization],
    ['Abroad', vocab.activity],
    ['Times of day', vocab.active_periods],
    ['Kinds', vocab.classes],
    ['Habitats', vocab.habitats],
  ];
  const rows = sets
    .filter(([, list]) => Array.isArray(list) && list.length)
    .map(([label, list]) => `<dt>${escapeHtml(label)}</dt>
      <dd>${list.map((v) => `<code>${escapeHtml(words(v))}</code>`).join(' · ')}</dd>`)
    .join('');
  return `<details class="lib fauna-vocab">
    <summary><span class="lib-title">The words on these cards, and they are a closed set</span></summary>
    <dl class="lib-body">${rows}</dl>
  </details>`;
}

/**
 * Fetch the fauna layer and render it into `mount`.
 *
 * Failure is reported, never papered over, exactly as the liberties and the
 * exclusions do it: a missing file leaves a line saying the list could not be
 * loaded and pushes the reason onto the loader's shared problem list. A zone
 * whose file 404s is named individually rather than taking the section down —
 * the published tree and the source tree have disagreed about a subdirectory
 * before, and a partial list that says which habitat is missing is worth more
 * than an empty one.
 *
 * @param {object} o
 * @param {HTMLElement|null} o.mount        where the habitats go
 * @param {HTMLElement|null} [o.noteMount]  where the count sentence goes
 * @param {string} o.sceneId                which scene's citation join to read
 * @param {URL} o.dataBase                  where data/ lives
 * @param {string[]} [o.problems]           the shared collector
 */
export async function mountFauna({ mount, noteMount = null, sceneId, dataBase, problems = [] }) {
  const fail = (message) => {
    problems.push(`fauna: ${message} — the wildlife of 1835 is not shown`);
    if (mount) {
      mount.innerHTML = '<p class="legend-note">The animal records could not be loaded. '
        + 'They are committed at <code>data/fauna/</code>.</p>';
      mount.removeAttribute('aria-busy');
    }
    if (noteMount) {
      noteMount.textContent = '';
      noteMount.removeAttribute('aria-busy');
    }
    return { zones: 0, species: 0, error: message };
  };

  const getJson = async (rel) => {
    const res = await fetch(new URL(rel, dataBase), { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${rel}: ${res.status} ${res.statusText}`);
    return res.json();
  };

  let index;
  try {
    index = await getJson('fauna/index.json');
  } catch (err) {
    return fail(String(err.message || err));
  }

  // The citation join. Its absence degrades the section to bare notes rather
  // than taking it down: a card without its sources is poorer, not wrong.
  const citationsById = new Map();
  try {
    const joined = await getJson(`sidecars/${sceneId}/fauna_sources.json`);
    for (const [id, record] of Object.entries(joined.citations || {})) {
      citationsById.set(id, record);
    }
  } catch (err) {
    problems.push(`fauna: ${err.message} — the animal records are shown without their citations`);
  }

  const vocab = index.vocabulary || {};
  const entries = Array.isArray(index.zones) ? [...index.zones] : [];
  entries.sort((a, b) => rank(vocab.habitats, a.habitat) - rank(vocab.habitats, b.habitat));

  const zones = [];
  for (const entry of entries) {
    try {
      const zone = await getJson(`fauna/${entry.file}`);
      // The manifest's copies are denormalised on purpose so a renderer can work
      // from one fetch, and `tools/validate.py` fails the build if they disagree
      // with the zone record. Read from the manifest where the zone record is
      // silent, which is what the denormalisation is for.
      zone.habitat = zone.habitat ?? entry.habitat;
      zone.in_modelled_extent = zone.in_modelled_extent ?? entry.in_modelled_extent;
      zone.extent_from = zone.extent_from ?? entry.extent_from;
      zones.push(zone);
    } catch (err) {
      problems.push(`fauna: ${err.message} — one habitat is missing from the wildlife list`);
    }
  }

  if (!zones.length) return fail('no habitat record loaded');

  const speciesCount = zones.reduce((n, z) => n + (z.species?.length || 0), 0);
  const drawn = zones.filter((z) => z.in_modelled_extent).length;

  if (noteMount) {
    noteMount.textContent = `${speciesCount} animals across ${zones.length} habitats, `
      + `${drawn} of them on ground this scene draws, every one of them stated for `
      + `1 July rather than for the year. None of them is in the scene: this is the `
      + `research, not a population.`;
    noteMount.removeAttribute('aria-busy');
  }

  if (mount) {
    mount.innerHTML = vocabularyHtml(vocab)
      + zones.map((zone) => zoneHtml(zone, vocab, citationsById)).join('');
    mount.removeAttribute('aria-busy');
  }

  return { zones: zones.length, species: speciesCount, drawn, error: null };
}
