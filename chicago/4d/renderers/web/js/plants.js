/**
 * plants.js — what grows in the ten plant communities, in the Evidence panel.
 *
 * T-0281, and it is the last of the three gaps this project kept finding in the
 * same shape. K51 found the animal records reaching no browser, K52 found the
 * households reaching none, and `data/flora/zones/*.json` — ten communities,
 * their matrix, forb, shrub and tree lists, every species with its recorded
 * density, height, width, July phenology and sources — was read by `flora.js`,
 * which plants it, and by nothing a visitor can open. A dataset that is only
 * drawn is a dataset whose evidence cannot be judged.
 *
 * IT IS NOT flora.js AND MUST NOT BECOME IT. `flora.js` deals the sward: it is
 * the layer that decides which species fills a lattice slot and what it looks
 * like. This module makes no planting decision and draws nothing. The two read
 * the same committed records and answer different questions — what is planted,
 * and what the research says — and keeping them apart is what lets the second
 * one tell the truth about the first.
 *
 * THE SECOND REASON, AND IT IS THE SHARPER ONE. T-0019 measured what the forb
 * lattice's ceiling costs and declared it in `tools/forb_clamp_baseline.json`:
 * ten (community, stratum, side) layers ask for more plants than the lattice can
 * carry, and `z06_dense_forest` draws half of one per cent of the flowering
 * plants its own records ask for. Until this section that figure lived in
 * `docs/STATUS.md` and in docs/LIBERTIES.md L186 — which is to say it was
 * declared to reviewers and to nobody else. A visitor standing in the dense
 * timber is looking at 0.5 % of the bloom the research put there, and this
 * project's whole bar is that it never misrepresents what it built.
 *
 * SO THE SHARE IS READ, NEVER TYPED. The clamp figures come from
 * `sidecars/<scene>/flora_clamp.json`, which `tools/compile_scene.py` carries
 * unchanged out of the declaration the sward gate holds, and which
 * `tools/compile_scene.py --check` fails on the moment the two disagree. A table
 * typed into this file would be a fourth copy of numbers that have already
 * drifted twice — K55 and T-0034 both moved this set under a green tree.
 */

import { citationItems, escapeHtml } from './citations.js';

/** A closed-set token as a reader should see it: `shrub_low` → `shrub low`. */
function words(token) {
  return String(token ?? '').replace(/_/g, ' ');
}

/** Order a value by its own vocabulary, unknown words last and marked. */
function rank(list, value) {
  const i = Array.isArray(list) ? list.indexOf(value) : -1;
  return i < 0 ? 999 : i;
}

/**
 * The confidence swatch the Evidence panel's own legend defines — one
 * vocabulary for the whole walkthrough, so a plant record grades exactly as a
 * building and an animal do rather than getting a second chip meaning the same.
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

/** A range the records state as `[low, high]`, in the records' own units. */
function range(pair, unit, digits = 2) {
  if (!Array.isArray(pair) || pair.length !== 2) return '';
  const [lo, hi] = pair.map((n) => Number(n));
  if (!Number.isFinite(lo) || !Number.isFinite(hi)) return '';
  const fmt = (n) => (Number.isInteger(n) ? String(n) : n.toFixed(digits));
  return lo === hi ? `${fmt(lo)} ${unit}` : `${fmt(lo)}–${fmt(hi)} ${unit}`;
}

/** A fraction as a percentage a reader can hold: 0.005212 → `0.5 %`. */
function percent(fraction) {
  const n = Number(fraction);
  if (!Number.isFinite(n)) return '';
  if (n > 0 && n < 0.001) return '<0.1 %';
  return `${(n * 100).toFixed(n < 0.1 ? 1 : 0)} %`;
}

/**
 * How much of a species a record asks for, in whichever of the three units that
 * record states — and stated in that unit rather than converted to a common one.
 *
 * The three are not interchangeable and this project has already paid for
 * pretending they were: `cover_fraction` is the share of ground a matrix grass
 * closes over, `stems_per_m2` is a count of individual plants, and
 * `density_per_ha` is how trees are recorded. K55 took the clamped-layer count
 * from four to six by fixing a unit error in exactly this arithmetic, so the
 * card shows what the record says and leaves the conversion to the one tool that
 * owns it.
 */
function abundance(sp) {
  const a = sp.abundance || {};
  if (a.cover_fraction) {
    const [lo, hi] = a.cover_fraction;
    return `${percent(lo)}–${percent(hi)} of the ground covered`;
  }
  if (a.stems_per_m2) return range(a.stems_per_m2, 'plants per m²');
  if (a.density_per_ha) return range(a.density_per_ha, 'per hectare', 0);
  return '';
}

/** The joined citation list for a record's `sources`, or nothing. */
function cites(sources, citationsById) {
  const found = (sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  return found.length ? `<ol class="cites excl-cites">${citationItems(found)}</ol>` : '';
}

/**
 * What the flower or fruit head IS, on 1 July — and it is a record, not a word.
 *
 * `july.inflorescence` carries `{ shape, rgb, height_frac, size_m }` on the
 * ninety-seven species that have one and `null` on the fifty-eight that do not,
 * and only `shape` is in the manifest's closed set. The two figures beside it
 * are what `flora.js` draws the head at, so a visitor reading "head globe,
 * 15–30 cm across" is being told the size of the thing in front of them rather
 * than a word for its outline.
 *
 * It reads `.shape` rather than the object because the object stringifies to
 * `[object Object]` — which is not a hypothetical here: this row shipped exactly
 * that on the first render of this section, the same fault T-0021 found on the
 * residents card, and the smoke now asserts against it.
 */
function inflorescence(july) {
  const inf = july.inflorescence;
  if (!inf || typeof inf !== 'object' || !inf.shape) return '';
  const size = Array.isArray(inf.size_m) && inf.size_m.length === 2
    ? ` — ${inf.size_m.map((n) => `${Math.round(Number(n) * 100)}`).join('–')} cm`
    : '';
  return `${words(inf.shape)}${size}`;
}

/**
 * Where a figure came from — `abundance_provenance` and `width_provenance`.
 *
 * THESE ARE GRADED CLAIM BLOCKS AND NOT STRINGS, which is the whole reason this
 * function exists rather than a `row()` call. Each carries `confidence`,
 * `sources` and a `note` that is usually several hundred words of reasoning:
 * how a recorded cover fraction was turned into a count of plants, or which
 * committed clump a width was reasoned from, and whether that reasoning is
 * `inferred` or `reconstructed`. A record that says how wide a plant is and a
 * record that says WHY it is that wide are two different claims and this project
 * grades them separately.
 *
 * T-0021 IS WHY THIS IS SPELT OUT. The residents card handed three graded claim
 * blocks of exactly this shape straight to a text renderer and shipped 113 rows
 * reading "[object Object]" — past every assertion it had, because a card that
 * renders the WRONG STRING still renders a string. The same three fields exist
 * here, this section was written from the same template, and the smoke asserts
 * `[object Object]` appears nowhere in this mount for that reason.
 */
function provenanceRow(label, claim, citationsById) {
  if (!claim || typeof claim !== 'object' || !claim.note) return '';
  return `<dt>${escapeHtml(label)}</dt>
    <dd>${swatch(claim.confidence)} <b>${escapeHtml(words(claim.confidence || 'reconstructed'))}</b>
      <span class="fauna-why">${escapeHtml(claim.note)}</span>
      ${cites(claim.sources, citationsById)}</dd>`;
}

/**
 * One species, collapsed — for the liberties' and the wildlife's reason. The
 * marsh alone records twenty-six plants, and ten communities opened flat would
 * push everything below this section off a phone.
 */
function speciesHtml(sp, vocab, citationsById) {
  const july = sp.july || {};
  const known = Array.isArray(vocab.roles) && vocab.roles.includes(sp.role);
  const roleChip = sp.role
    ? `<span class="lib-scope${known ? '' : ' fauna-unknown'}">${escapeHtml(words(sp.role))}</span>`
    : '';
  const why = (label, claim) => provenanceRow(label, claim, citationsById);

  return `<details class="lib fauna-sp plant-sp">
    <summary>
      ${swatch(sp.confidence)}
      <span class="lib-title">${escapeHtml(sp.common || sp.id)}
        <em class="fauna-binomial">${escapeHtml(sp.binomial || '')}</em></span>
      ${roleChip}
    </summary>
    <dl class="lib-body">
      ${row('How much of it the record asks for', abundance(sp))}
      ${row('Height', range(sp.height_m, 'm'))}
      ${row('Width', range(sp.width_m, 'm'))}
      ${row('On 1 July', words(july.phenology))}
      ${row('What you would be looking at', july.appearance)}
      ${row('In flower or fruit', inflorescence(july))}
      ${row('It grows on', words(sp.substrate))}
      ${row('Drawn as', words(sp.form))}
      ${row('Also recorded as', sp.synonym)}
      ${why('Where the density figure comes from', sp.abundance_provenance)}
      ${why('Where the width figure comes from', sp.width_provenance)}
      ${sp.note ? `<dt>Note on the record</dt><dd>${escapeHtml(sp.note)}</dd>` : ''}
    </dl>
    ${cites(sp.sources, citationsById)}
  </details>`;
}

/**
 * What the lattice cannot carry, for one community — the section's whole second
 * reason, and every number in it read off the declaration.
 *
 * Stated per stratum and per side because that is how the ceiling binds: the
 * marsh is clamped on its dry ground and over its standing water separately, and
 * the dense forest is clamped in two strata at once. Flattening those into one
 * row per community would be inventing a figure none of them states.
 */
function clampHtml(rows, ceilingPerM2) {
  if (!rows.length) return '';
  const items = rows.map((r) => {
    const where = r.side && r.side !== 'dry' ? ` (${escapeHtml(words(r.side))} ground)` : '';
    return `<li><b>${escapeHtml(words(r.stratum))}</b>${where} — the records ask for
      <b>${Number(r.askedPerM2).toFixed(r.askedPerM2 < 10 ? 2 : 1)}</b> plants per m²,
      the lattice offers <b>${Number(r.offeredPerM2).toFixed(3)}</b>, so the scene draws
      <b>${percent(r.drawsFraction)}</b> of the record.</li>`;
  }).join('');
  return `<dt>What the scene cannot draw</dt>
    <dd><ul class="plant-clamp">${items}</ul>
      <span class="fauna-why">The small plants are dealt onto a lattice that holds at most
        ${Number(ceilingPerM2).toFixed(3)} plants per square metre, whatever a community's
        records ask for. Where a record asks for more, the number of plants a visitor stands
        in is a rendering budget and not the evidence — so it is stated here rather than left
        to read as a gap in the research.</span></dd>`;
}

/** One community, with its species grouped in the manifest's own role order. */
function zoneHtml(zone, vocab, clampByZone, ceilingPerM2, citationsById) {
  const species = Array.isArray(zone.species) ? [...zone.species] : [];
  species.sort((a, b) => (rank(vocab.roles, a.role) - rank(vocab.roles, b.role))
    || String(a.common || '').localeCompare(String(b.common || '')));

  const cover = zone.cover || {};
  const matrix = Number.isFinite(cover.matrix_fraction)
    ? `${percent(cover.matrix_fraction)} closed sward`
      + (cover.bare_soil_fraction ? `, ${percent(cover.bare_soil_fraction)} bare soil` : '')
      + (cover.standing_water_fraction
        ? `, ${percent(cover.standing_water_fraction)} standing water` : '')
    : '';

  // The extent is the community's weakest claim and the records say so: the
  // vegetation is documented and the BOUNDARY between one community and the next
  // is almost never surveyed. Showing the grade beside the reasoning is the whole
  // of T-0025's rule, and eight of the ten records already keep it.
  const extent = zone.extent || {};
  const extentRow = extent.kind
    ? `<dt>Where it is</dt>
       <dd>${swatch(extent.confidence)} <b>${escapeHtml(words(extent.kind))}</b>${
  extent.note ? `<br><span class="fauna-why">${escapeHtml(extent.note)}</span>` : ''}
         ${cites(extent.sources, citationsById)}</dd>`
    : '';

  // Three of the ten communities have no modelled ground in this scene. Saying so
  // is the wildlife section's argument exactly: a list that read the same for
  // ground the scene draws and ground it does not would be making a claim about
  // the town rather than about the research.
  const standing = zone.plantable_in_scene
    ? ''
    : `<dt>Standing in the scene</dt><dd>This community's ground is <b>not modelled</b> in
       this scene, so nothing here is planted anywhere you can walk. The record is kept
       because the plants were there.</dd>`;

  const clampRows = clampByZone.get(zone.id) || [];
  const clampChip = clampRows.length
    ? `<span class="lib-scope plant-clamped">${clampRows.length === 1 ? 'one stratum'
      : `${clampRows.length} strata`} clamped</span>`
    : '';

  return `<details class="lib fauna-zone plant-zone">
    <summary>
      <span class="lib-id">${escapeHtml(String(zone.id || ''))}</span>
      <span class="lib-title">${escapeHtml(zone.name || zone.id)}</span>
      <span class="lib-scope">${species.length} species</span>
      ${clampChip}
    </summary>
    <dl class="lib-body">
      ${row('It reads as', zone.reads_as)}
      ${row('Ground cover', matrix)}
      ${extentRow}
      ${standing}
      ${clampHtml(clampRows, ceilingPerM2)}
      ${zone.note ? `<dt>Note on the record</dt><dd>${escapeHtml(zone.note)}</dd>` : ''}
      ${row('Dossier', zone.dossier)}
    </dl>
    ${cites(zone.sources, citationsById)}
    <div class="fauna-species">${species
    .map((sp) => speciesHtml(sp, vocab, citationsById)).join('')}</div>
  </details>`;
}

/**
 * The manifest's closed sets, shown rather than paraphrased — the wildlife
 * section's argument, and for the same reason: every chip on every card above
 * comes out of one of these lists, and a word this module invented would be a
 * gloss the dataset never agreed to.
 */
function vocabularyHtml(vocab) {
  const sets = [
    ['What a plant is doing in its community', vocab.roles],
    ['On 1 July', vocab.phenology],
    ['It grows on', vocab.substrates],
    ['Drawn as, in the sward', vocab.forms_flora],
    ['Drawn as, in the canopy', vocab.forms_trees],
    ['In flower or fruit', vocab.inflorescence_shapes],
  ];
  const rows = sets
    .filter(([, list]) => Array.isArray(list) && list.length)
    .map(([label, list]) => `<dt>${escapeHtml(label)}</dt>
      <dd>${list.map((v) => `<code>${escapeHtml(words(v))}</code>`).join(' · ')}</dd>`)
    .join('');
  return `<details class="lib fauna-vocab plant-vocab">
    <summary><span class="lib-title">The words on these cards, and they are a closed set</span></summary>
    <dl class="lib-body">${rows}</dl>
  </details>`;
}

/**
 * Fetch the plant records and render them into `mount`.
 *
 * Failure is reported, never papered over, exactly as the liberties, the
 * exclusions and the wildlife do it: a missing manifest leaves a line saying so
 * and pushes the reason onto the loader's shared problem list, and a community
 * whose file 404s is named individually rather than taking the section down. The
 * published tree and the source tree have disagreed about a subdirectory before,
 * and a partial list that says which community is missing is worth more than an
 * empty one.
 *
 * @param {object} o
 * @param {HTMLElement|null} o.mount        where the communities go
 * @param {HTMLElement|null} [o.noteMount]  where the count sentence goes
 * @param {string} o.sceneId                which scene's derived files to read
 * @param {URL} o.dataBase                  where data/ lives
 * @param {string[]} [o.problems]           the shared collector
 */
export async function mountPlants({ mount, noteMount = null, sceneId, dataBase, problems = [] }) {
  const fail = (message) => {
    problems.push(`plants: ${message} — what grows in 1835 is not shown`);
    if (mount) {
      mount.innerHTML = '<p class="legend-note">The plant records could not be loaded. '
        + 'They are committed at <code>data/flora/</code>.</p>';
      mount.removeAttribute('aria-busy');
    }
    if (noteMount) {
      noteMount.textContent = '';
      noteMount.removeAttribute('aria-busy');
    }
    return { zones: 0, species: 0, clamped: 0, error: message };
  };

  const getJson = async (rel) => {
    const res = await fetch(new URL(rel, dataBase), { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${rel}: ${res.status} ${res.statusText}`);
    return res.json();
  };

  let index;
  try {
    index = await getJson('flora/index.json');
  } catch (err) {
    return fail(String(err.message || err));
  }

  // The citation join. Its absence degrades the section to bare records rather
  // than taking it down: a card without its sources is poorer, not wrong.
  const citationsById = new Map();
  try {
    const joined = await getJson(`sidecars/${sceneId}/flora_sources.json`);
    for (const [id, record] of Object.entries(joined.citations || {})) {
      citationsById.set(id, record);
    }
  } catch (err) {
    problems.push(`plants: ${err.message} — the plant records are shown without their citations`);
  }

  // The declared ceiling. Its absence is NOT a degradation the section can shrug
  // off the way it can a missing citation: without it the cards would show ten
  // communities' recorded densities with nothing saying that nine of them are not
  // what a visitor is standing in, which is the misrepresentation this section
  // exists to end. So it is reported as a problem and the clamp rows are omitted
  // rather than guessed at.
  let clamp = null;
  try {
    clamp = await getJson(`sidecars/${sceneId}/flora_clamp.json`);
  } catch (err) {
    problems.push(`plants: ${err.message} — the plant records are shown without the share of `
      + 'each one the lattice is able to draw');
  }
  const clampByZone = new Map();
  for (const r of clamp?.clamped ?? []) {
    if (!clampByZone.has(r.community)) clampByZone.set(r.community, []);
    clampByZone.get(r.community).push(r);
  }
  const ceilingPerM2 = clamp?.ceiling_per_m2;

  const vocab = index.vocabulary || {};
  const entries = Array.isArray(index.zones) ? [...index.zones] : [];
  entries.sort((a, b) => (a.zone ?? 99) - (b.zone ?? 99));

  const zones = [];
  for (const entry of entries) {
    try {
      const zone = await getJson(`flora/${entry.file}`);
      // The manifest's copies are denormalised on purpose so a renderer can work
      // from one fetch, and `tools/validate.py` fails the build if they disagree
      // with the zone record. Read from the manifest where the zone record is
      // silent, which is what the denormalisation is for.
      zone.plantable_in_scene = zone.plantable_in_scene ?? entry.plantable_in_scene;
      zones.push(zone);
    } catch (err) {
      problems.push(`plants: ${err.message} — one community is missing from the plant list`);
    }
  }

  if (!zones.length) return fail('no community record loaded');

  const speciesCount = zones.reduce((n, z) => n + (z.species?.length || 0), 0);
  const planted = zones.filter((z) => z.plantable_in_scene).length;
  const clampedZones = zones.filter((z) => clampByZone.has(z.id)).length;

  if (noteMount) {
    // The count sentence carries the finding rather than the total, because the
    // total is the flattering half. `worst` is read off the declaration like
    // every other figure here — it is the smallest share any layer draws.
    const worst = (clamp?.clamped ?? [])
      .reduce((lo, r) => (lo === null || r.drawsFraction < lo.drawsFraction ? r : lo), null);
    noteMount.textContent = `${speciesCount} plants across ${zones.length} communities, `
      + `${planted} of them on ground this scene plants, every one of them recorded for `
      + `1 July rather than for the year.`
      + (worst
        ? ` ${clampedZones} of those communities ask for more plants than the sward lattice `
          + `can hold: the worst is ${worst.community.replace(/^z\d+_/, '').replace(/_/g, ' ')}, `
          + `where the scene draws ${percent(worst.drawsFraction)} of the `
          + `${worst.stratum} layer its own records ask for.`
        : '');
    noteMount.removeAttribute('aria-busy');
  }

  if (mount) {
    mount.innerHTML = vocabularyHtml(vocab)
      + zones.map((zone) => zoneHtml(zone, vocab, clampByZone, ceilingPerM2, citationsById)).join('');
    mount.removeAttribute('aria-busy');
  }

  return {
    zones: zones.length,
    species: speciesCount,
    planted,
    clamped: (clamp?.clamped ?? []).length,
    clampedZones,
    ceilingPerM2,
    error: null,
  };
}
