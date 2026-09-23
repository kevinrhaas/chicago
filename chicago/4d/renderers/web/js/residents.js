/**
 * residents.js — the town's people, in the Evidence panel.
 *
 * ROADMAP K52, from K51. `data/residents/` holds 201 households and 237 person
 * entries, every one of them graded and most of them cited, and unlike this
 * morning's fauna the layer already had *a* reader: `tools/compile_scene.py`
 * attaches a household to a building's sidecar and `popup.js` names it on the
 * building card. K52's own box says that makes it the harder question rather
 * than the easier one — *"a layer with one reader is exactly where an unread
 * figure hides, because 'the browser has it' reads as 'somebody looks at it'."*
 *
 * IT HID SEVENTEEN HOUSEHOLDS. `compile_residents()` reaches a building through
 * `lives_at` or `works_at`, so a household whose residence and workplace are
 * both unattested at the scene date attaches to nothing and appears on no card
 * anywhere — 17 households and 20 person entries, and one of them is the Mark
 * Beaubien household, which is the most famous in the town and one of the
 * thinnest records in the dataset. A dataset that drops a record for being
 * *poorly evidenced* is doing the opposite of what this project's confidence
 * model is for.
 *
 * AND IT CARRIED ONLY A THIRD OF EACH RECORD IT DID REACH. The building card
 * shows a household's name, division, relation, its note and its persons' names,
 * relationships, grades and occupation words. `arrival`, `origin`,
 * `reason_for_coming`, `party_size_on_arrival`, `present_on_scene_date` and
 * `touches_removal` reach nothing; nor do a person's `sex`, `age_on_scene_date`,
 * `birth_year`, `name_basis` or their own `sources`, nor the occupation's grade
 * and reasoning, nor the ten `researched_not_resident` findings — which are the
 * exclusions-style half of the dataset and as load-bearing as the households.
 *
 * TWO EVIDENCE STRENGTHS, KEPT APART (T-0378). The newspaper register reads people
 * out of the Democrat and the American, and the two kinds it reads are not the same
 * claim: a man who advertised his stock is named, dated, placed and given a trade,
 * while a name in the post office's list of uncalled-for letters is a name and
 * nothing else. `mint_letter_list_residents.py` carries `letter_list_only` onto the
 * person for the second kind, and this file is where the distinction has to survive
 * — it reached `gazetteer.json` and `register_1835.json` and stopped there, so on the
 * card the two read identically. It is now a row of its own on the person, and a
 * clause in the section's own count sentence.
 *
 * WHAT THIS IS NOT. It is a card, not a crowd. Nothing here is drawn: L1 and
 * AGENTS.md stand, v1 ships no human figures, and the standing constraint on
 * depicting the Potawatomi in the year of the removal is untouched by a section
 * that publishes what the sources say and nothing else.
 *
 * AND THEN THAT DISTINCTION BECAME THE SHAPE OF THE SECTION (T-0379). The owner was
 * asked how many of the letter-list names the town should hold and ruled, on
 * 30 August 2026, that it should hold every one the evidence admits. That is the
 * largest single change to this town's population the corpus can make — it took it
 * from a couple of hundred people to most of a thousand, roughly three quarters of
 * them a name on a post-office list and nothing else — and the ruling set its own
 * test for whether the implementation was any good: *a visitor who looks at the
 * whole must be able to tell at a glance which three quarters are names alone. If
 * that reads as a wall of undifferentiated people, the ruling has been implemented
 * badly, not chosen badly.* So the list is SPLIT rather than sorted: the households
 * the rest of the corpus documents keep the section they had, at the length they
 * had, and the cohort sits under them in one closed group that says what it is.
 *
 * ONE FETCH, THEN ONE PER HOUSEHOLD A VISITOR OPENS. The manifest is a
 * denormalised summary of every record — `tools/validate.py` fails the build
 * when a copy disagrees with its record — so the list renders from a single
 * file, and the full record is fetched the first time its own row is opened.
 * A fetch per household on mount, to show that many collapsed summaries, would be
 * a worse card and a slower one; the summary is the manifest's job and the manifest
 * says so. That was true of 201 records and it is the load-bearing decision at 920.
 */

import { citationItems, escapeHtml } from './citations.js';
import { tierOf, isNotAsserted, TIER_LABEL, TIER_TITLE } from './attribute-tiers.js';
// The agency relation, rendered by the module that owns it — one rendering of a
// holding for the building card and the person card both (T-1041).
import { agencySectionHtml, loadAgencies } from './agencies.js';

/** A closed-set token as a reader should see it: `tavern_keeper`. */
export function words(token) {
  return String(token ?? '').replace(/_/g, ' ');
}

/** Order a value by its own vocabulary, unknown words last. */
function rank(list, value) {
  const i = Array.isArray(list) ? list.indexOf(value) : -1;
  return i < 0 ? 999 : i;
}

/**
 * The Evidence panel's own confidence swatch — one vocabulary for the whole
 * walkthrough. A person's `grade` and an attribute's `confidence` are two
 * different axes (the manifest is emphatic that they must not be conflated) but
 * they share the three words, so they share the chip rather than inventing a
 * second one that means the same thing.
 */
export function swatch(level) {
  const cls = { attested: 'sw-doc', inferred: 'sw-inf', unknown: 'sw-unk' }[level] || 'sw-rec';
  return `<i class="sw ${cls}" title="${escapeHtml(TIER_TITLE[level] || level || 'reconstructed')}"></i>`;
}

/**
 * The tier's own word, beside the chip (T-1158). The chip alone was a colour with a
 * tooltip, which is not a reading: a visitor scanning a card could see that two rows
 * differed without being told how. `unknown` prints nothing here, because its value
 * already reads "not recorded" and the row would otherwise say it twice.
 */
function tierWord(tier) {
  if (!tier || tier === 'unknown') return '';
  return `<span class="res-tier" title="${escapeHtml(TIER_TITLE[tier])}">${
    escapeHtml(TIER_LABEL[tier])}</span>`;
}

/**
 * What a reconstructed value rests on, and what would retire it — the half of the tier
 * a reader has to be able to open (T-1158). Collapsed, because forty blocks in the
 * whole layer carry one and a card should not make the other ten thousand pay for it.
 *
 * `basis.kind` is the distinction worth reading: `model` was DRAWN and carries the seed
 * that redraws it, `rule` was ARGUED and carries the rule it was argued under. A drawn
 * value nobody can redraw is not reproducible, so the seed is printed rather than kept
 * for the gate.
 */
function basisHtml(block) {
  const basis = block && block.basis;
  if (!basis || typeof basis !== 'object') return '';
  const rep = block.replaceable_by || null;
  const drawn = basis.kind === 'model';
  return `<details class="res-basis"><summary>${
    drawn ? 'Drawn from a model' : 'Argued from a rule'} — <code>${
    escapeHtml(String(basis.id || ''))}</code></summary>
    <span class="res-why">${escapeHtml(String(basis.note || ''))}${
    drawn && block.seed ? ` Redrawn with the seed <code>${escapeHtml(String(block.seed))}</code>.` : ''}${
    rep ? ` This value is replaced the moment the project holds ${escapeHtml(String(rep.match || ''))}.` : ''}
    </span></details>`;
}

/**
 * `1835-07-01` as a reader should see it. The letter-list records carry the dates
 * of the returns that printed them as ISO strings so a gate can read them; a card
 * is not a database, and a visitor reading which day the post office was holding
 * a letter should not have to parse one.
 */
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
  'August', 'September', 'October', 'November', 'December'];

export function printedOn(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso ?? ''));
  if (!m) return String(iso ?? '');
  return `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}`;
}

/** A `<dt>/<dd>` pair, omitted entirely when the record carries nothing. */
/**
 * The birth year as its arithmetic left it (T-1303). Every interval this project derives
 * from an age — an age at death in Fergus's obituary list, an age a man gave at the
 * Calumet Club in 1879 — leaves the birth in ONE year or in TWO, and `precision` says
 * which. A card printing only the lower year would state a precision the page does not
 * have, which is the direction this project is careful never to lie in.
 */
function bornYears(born) {
  if (!born) return null;
  if (born.precision === 'band' && Array.isArray(born.band)) {
    return `${born.band[0]} or ${born.band[1]}`;
  }
  return born.value;
}

/**
 * An age band as a reader should meet it (T-1304). The 1840 schedule's bands are decadal
 * above twenty and the block carries their edges, so the card prints the interval rather
 * than the machine-readable `20-29` — and the top band, which has no upper edge, prints
 * as "70 or older" rather than as a range with a hole in it.
 *
 * NOTHING HERE TURNS A BAND INTO A YEAR. The whole point of the band is that the project
 * does not know the year; a card that printed a midpoint would undo that in one line.
 */
function bandYears(band) {
  if (!band || band.value === null || band.value === undefined) return null;
  const low = band.low;
  const high = band.high;
  if (typeof low !== 'number') return String(band.value);
  if (typeof high !== 'number') return `${low} or older`;
  if (low === 0) return `under ${high + 1}`;
  return `${low} to ${high}`;
}

function row(label, value) {
  if (value === null || value === undefined || value === '') return '';
  return `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd>`;
}

/**
 * A graded household claim — `arrival`, `origin`, `reason_for_coming`,
 * `lives_at`, `works_at`, `present_on_scene_date` — as its value, its
 * confidence, its reasoning and its sources.
 *
 * The reasoning is the point. On this layer a note routinely says the record is
 * NOT attested and why the figure is carried anyway, and a card printing only
 * the value would be hiding the best part of it: Mark Beaubien's arrival year is
 * *"the figure in general circulation … carried as a conjecture that cites
 * nothing, precisely so that a reader can see it is not evidence."*
 *
 * `value` is passed in beside the block rather than dug out of it here, the same
 * way `fauna.js` does it and for the same reason: a figure read through a
 * generic accessor is a figure a read census cannot see in this file's text.
 */
/**
 * The dated evidence leg under an `uncertain` presence (T-1144, acceptance 9).
 *
 * A card that says "here on 1 July 1835: uncertain" is making a finding, and the thing
 * that makes it one is a date — the last day the corpus can still see this person. That
 * date is derived onto the record by `tools/derive_presence_evidence_leg.py`, so the
 * card can print it instead of leaving a reader to infer it from the paragraph above.
 *
 * WHAT THE ROW WILL NOT DO is let a date read as a sighting when it is not one. The leg
 * says which kind it is — a dated reading, the far end of a cited source's SPAN, or an
 * arrival bound — and a reading whose own window covers 1 July 1835 (a source that says
 * only `1835`) pins no day before it and says so here.
 */
function presenceLegRow(hh, citationsById) {
  const presence = hh.present_on_scene_date || {};
  const leg = presence.last_dated_appearance;
  if (!leg || presence.value !== 'uncertain') return '';
  const kind = {
    sighting: 'a dated reading of this person',
    source_span: "the far end of a cited source's span, which is not a sighting",
    arrival_bound: 'an arrival bound, which is not a sighting',
  }[leg.leg];
  if (!leg.as_read) {
    return `<dt>Last dated evidence before that day</dt>
      <dd>${swatch('unknown')}none${
        leg.note ? `<br><span class="res-why">${escapeHtml(leg.note)}</span>` : ''}</dd>`;
  }
  // A COARSE READING SAYS SO. `precision` is how exact the source was — a day, a
  // month, a year — and `reaches` the latest day that reading can still mean. A year
  // whose window covers 1 July 1835 pins nothing before it, and the row says which.
  const exactness = { day: 'to the day', month: 'to the month', year: 'to the year' }[
    leg.precision] || leg.precision;
  const reach = leg.includes_scene_date
    ? `read ${exactness}, so it can mean any day up to ${leg.reaches} — a window that `
      + 'covers 1 July 1835 itself, and pins nothing before it'
    : `read ${exactness}, reaching ${leg.reaches} — ${leg.days_before_scene_date} `
      + 'day(s) before the scene date';
  const cites = (leg.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  const list = cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : '';
  return `<dt>Last dated evidence before that day</dt>
    <dd>${escapeHtml(leg.as_read)} — ${escapeHtml(kind || leg.leg)}, ${escapeHtml(reach)}${
      leg.note ? `<br><span class="res-why">${escapeHtml(leg.note)}</span>` : ''}${list}</dd>`;
}

function claimRow(label, value, block, citationsById) {
  if (!block) return '';
  // T-1158. The chip is the TIER now, not the raw confidence, and the two part company
  // on exactly the rows a reader most needs them to: a null value under `confidence:
  // "reconstructed"` is not an invention, it is an absence, and it gets the `unknown`
  // chip and no tier word rather than the hatched one that says we made it up.
  const tier = tierOf(block) || block.confidence;
  const shown = value === null || value === undefined || value === ''
    ? 'not recorded' : value;
  const note = block.note ? `<br><span class="res-why">${escapeHtml(block.note)}</span>` : '';
  const cites = (block.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  const list = cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : '';
  return `<dt>${escapeHtml(label)}</dt>
    <dd>${swatch(tier)}${tierWord(tier)}${escapeHtml(shown)}${basisHtml(block)}${note}${list}</dd>`;
}

/**
 * The household's kin rows — a relationship that crosses to ANOTHER household
 * record (T-0597).
 *
 * `persons[].relationship` is a person's place inside one household and stops
 * at its edge, so until `kin` existed the only place a family tie between two
 * records could go was a free-text note, where a reader may find it and a query
 * never will. The row renders like any other graded claim, which is the whole
 * argument: the tie carries its confidence swatch, its reasoning and its
 * citations exactly as an arrival does, because it is exactly as much of a
 * claim as an arrival is.
 *
 * The far person and household are shown as their ids, humanised the same way
 * the collapsed summary humanises a household id. The card holds ONE record —
 * the others are fetched only when their own row is opened — so printing a
 * neighbour's display name here would mean either a fetch per kin row or a
 * denormalised copy that can go stale, and the manifest's rule is that a copy
 * which can disagree with its record does not get made.
 */
function kinRows(hh, citationsById) {
  const kin = Array.isArray(hh.kin) ? hh.kin : [];
  return kin.map((k) => claimRow(
    'Related to',
    `${words(k.person)} is the ${words(k.relation)} of ${words(k.value)}, `
      + `in the ${words(String(k.household ?? '').replace(/^hh_/, ''))} household`,
    k,
    citationsById,
  )).join('');
}

/**
 * One person. `grade` says how much of the PERSON is reconstructed and the
 * occupation's `confidence` says how well that one attribute is evidenced —
 * the manifest's two orthogonal axes, shown as two chips rather than merged
 * into a single misleading one.
 *
 * The five placeholder entries are the reason `name_basis` and the note are
 * printed here: an unnamed wife or "four children" is an ADMISSION carrying a
 * count, and the record says in as many words that it must not be counted as an
 * individual. That sentence belongs in front of a reader, not in a JSON file.
 *
 * THREE OF THESE ARE GRADED CLAIM BLOCKS AND WERE PRINTED AS OBJECTS. `age_on_
 * scene_date`, `birth_year` and `name_basis` carry `{value, confidence, note,
 * sources}` exactly like the household's own claims, and this function handed
 * the whole block to `row()`, which escapes whatever it is given: 113 person
 * rows read `How this person is named — [object Object]` and nine read it twice
 * more for the age and the birth year. The census of ROADMAP K52 (T-0021) is
 * what found it, and it is the finding that section exists to make — a figure
 * that reaches the card as `[object Object]` has not reached a visitor, and the
 * sentence it was hiding is the one this project most needs read: *"THE NAME IS
 * INVENTED. No source names this resident."* They go through `claimRow` now,
 * with the same swatch, reasoning and citations every other graded claim gets.
 */
function researchHtml(review, citationsById) {
  if (!review) return '';
  const labels = {
    corroborated_enrichment: 'corroborated profile finding',
    candidate_identity: 'candidate identity — not merged',
    no_corroboration: 'reviewed — no safe match found',
  };
  const cites = (review.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  const candidates = (review.candidates || []).map((candidate) => {
    const cc = (candidate.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
    return `<li><b>${escapeHtml(candidate.name)}</b> · ${escapeHtml(words(candidate.assessment))}
      <br><span class="res-why">${escapeHtml(candidate.basis)} ${escapeHtml((candidate.conflicts || []).join(' '))}
      This candidate is not an asserted identity.</span>
      ${cc.length ? `<ol class="cites">${citationItems(cc)}</ol>` : ''}</li>`;
  }).join('');
  return `<dt>Resident research review</dt><dd><span class="res-chip res-research">${
      escapeHtml(labels[review.outcome] || words(review.outcome))}</span>
    <span class="res-why">Reviewed ${escapeHtml(printedOn(review.reviewed_on))}. ${
      escapeHtml(review.summary)} A no-find records the limits of this search; it is not
      evidence that the person did not exist.</span>
    ${candidates ? `<ul class="res-candidates">${candidates}</ul>` : ''}
    ${cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : ''}</dd>`;
}

/**
 * The 1840 census household a person's record is bridged to — five years after
 * this scene, and that gap is the whole reason this block is rendered rather
 * than banked.
 *
 * PR #670 attached the bridge to three people and declared none of its figures,
 * so twenty-four values were being shipped to a browser with nothing reading
 * them (T-0491). Banking them would have been the cheap answer and the wrong
 * one: an identity bridge is an ARGUMENT — a transcribed name, a normalised
 * reading of it, the page and row it stands on, the serial it was assigned and
 * three separate confidences in those steps — and an argument a visitor cannot
 * see is an assertion. It is shown whole, headed by the year, so that no part of
 * it can be mistaken for an 1835 fact.
 *
 * THE HOUSEHOLD TALLIES ARE SHOWN FOR THE SAME REASON. They are the strongest
 * temptation on this card — six people under a roof in 1840 is not six people
 * under it in 1835 — and the record's own note says so in as many words. The
 * note is printed directly beneath them, because a figure withheld cannot be
 * argued with and a figure shown with its refusal can.
 */
function laterCensusHtml(census, citationsById) {
  if (!census) return '';
  const hh = census.household || {};
  const cite = citationsById.get(census.source_id);
  const tallies = [
    ['People in the household', hh.persons],
    ['Children under ten', hh.children_under_10],
    ['Male', hh.male],
    ['Female', hh.female],
    ['Employed in agriculture', hh.agriculture],
    ['Employed in commerce', hh.commerce],
    ['Employed in manufactures and trades', hh.manufactures_trades],
    ['Employed in inland navigation', hh.inland_navigation],
    ['In a learned profession or engineering', hh.professions_engineering],
    ['Foreigners not naturalized', hh.foreigners_not_naturalized],
    ['Over twenty-one and unable to read or write', hh.illiterate_over_21],
  ].filter(([, n]) => Number.isFinite(n))
    .map(([label, n]) => `<li>${escapeHtml(label)}: ${escapeHtml(String(n))}</li>`)
    .join('');
  return `<dt>Found again in the ${escapeHtml(String(census.year))} census</dt>
    <dd>${swatch(null)}Head of household <b>${escapeHtml(census.head_name_normalized)}</b>,
      transcribed on the page as <q>${escapeHtml(census.head_name_transcribed)}</q>${
        census.bridge_status ? ` · ${escapeHtml(words(census.bridge_status))} bridge` : ''}
      <br><span class="res-why">Page ${escapeHtml(String(census.census_page))}, row ${
        escapeHtml(String(census.census_row))}, enumeration serial ${
        escapeHtml(String(census.serial))}${
        census.source_image ? `, from image ${escapeHtml(census.source_image)}` : ''}${
        census.source_kind ? ` (${escapeHtml(census.source_kind)})` : ''}.
        The reading of the name is graded ${escapeHtml(words(census.name_confidence))}, the
        identification of it with this person ${escapeHtml(words(census.identity_confidence))},
        and the assignment of the row to that serial ${
        escapeHtml(words(census.serial_mapping_confidence))} — three separate steps, each of
        which can be wrong on its own.</span>
      <br><span class="res-why">${escapeHtml(census.bridge_basis)}</span>
      ${tallies ? `<ul class="res-candidates">${tallies}</ul>` : ''}
      ${census.note ? `<span class="res-why">${escapeHtml(census.note)}</span>` : ''}
      ${cite ? `<ol class="cites">${citationItems([cite])}</ol>` : ''}</dd>
    ${scanHtml(census, citationsById)}`;
}

/**
 * The same line, read off the photograph of the sheet (T-0530).
 *
 * The block above it is a RECOVERY: 210 rows taken out of a workbook the owner
 * has ruled lost, which cite no line on any page. Where the page has since been
 * read — column by column, checked against the footings the enumerator wrote at
 * the bottom of his own sheet — the two do not always agree, and on the one
 * household this reaches they disagree about how many people in it were men.
 *
 * BOTH ARE SHOWN, and the sentence between them says which is senior and why.
 * Replacing the recovered figures with the scan would have been tidier and would
 * have destroyed the finding: the bridge that put this person on this line was
 * built out of the workbook's row, so a card showing only the sheet would be
 * quoting evidence the identification never rested on.
 */
function scanHtml(census, citationsById) {
  const scan = census.scan_verified;
  if (!scan) return '';
  const cites = (scan.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  const tallies = [
    ['People on the line', scan.free_persons],
    ['Male', scan.males],
    ['Female', scan.females],
    ['Children under ten', scan.children_under_10],
  ].filter(([, n]) => Number.isFinite(n))
    .map(([label, n]) => `<li>${escapeHtml(label)}: ${escapeHtml(String(n))}</li>`)
    .join('');
  return `<dt>Read again off the page itself</dt>
    <dd>${swatch('attested')}Line ${escapeHtml(String(scan.line))} of the photographed sheet,
      where the head of the household is written <q>${escapeHtml(scan.head_name_as_read)}</q>.
      <br><span class="res-why">From ${escapeHtml(scan.image)}, read by ${escapeHtml(scan.read_by)}.</span>
      ${tallies ? `<ul class="res-candidates">${tallies}</ul>` : ''}
      <span class="res-why">On the line, band by band: ${escapeHtml(scan.age_bands)}.</span>
      <br><span class="res-why">The sheet foots its own columns and that footing is the only
        check this reading has: ${escapeHtml(scan.column_totals_check)}.</span>
      ${census.scan_disagreement
        ? `<br><span class="res-why">${escapeHtml(census.scan_disagreement)}</span>` : ''}
      ${cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : ''}</dd>`;
}

/**
 * The Chicago directories of 1839, 1843 and 1844, on the people they meet (T-0632).
 *
 * Every volume here is later than this scene and that gap is the whole reason this
 * is rendered rather than banked. A later line can only do two things for a person
 * of 1835 — say they were still in Chicago, and print a trade or a street the 1835
 * record never had — and both of those are ARGUMENTS a reader can only disagree
 * with if they can see the line, the page and the rule that reached it.
 *
 * THE THREE STATUSES ARE ALL SHOWN, and that is the point of the section rather
 * than a caveat on it. A person met by one entry nobody else meets is a single
 * entry; met by several, this project does not choose between them; sharing one
 * entry with another person in this town, no match is made. A section that showed
 * only the first would be reporting the crosswalks' successes and hiding their
 * arithmetic.
 *
 * WHAT CROSSES AND WHAT DOES NOT. Norris's alphabetical volume sets a partnership
 * where the trade would go — "of Horace Norton & Co", twice simply "of" — so its
 * split yields a value containing no trade at all and T-0569 refused it. The line
 * is quoted and its parse is not. The Fergus volumes set the trade first and its
 * qualifiers after, so their split crosses with the caution printed beside it.
 */
function laterDirectoryHtml(found, citationsById) {
  if (!found) return '';
  const cites = (found.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  const volumes = (found.appearances || []).map((a) => {
    const lines = (a.entries || []).map((e) => `<li><q>${escapeHtml(e.as_printed)}</q>${
      e.firm ? ` — ${escapeHtml(e.firm)}` : ''}
      <br><span class="res-why">Printed page ${escapeHtml(String(e.printed_page))}, entry ${
        escapeHtml(e.claim_id)}.</span></li>`).join('');
    const holds = (a.holds || []).map((c) => (c === 'occupation' ? 'a trade' : 'a street'));
    // T-0987 stretch 6: a split is refused per FIELD, so the chip names which of the two
    // does not cross rather than saying it of the whole line. `split_refused` maps a
    // field to a clause key; the clause itself is on the ruling, in the ledger.
    const noCross = Object.keys(a.split_refused || {}).sort()
      .map((c) => (c === 'occupation' ? "the trade's split" : "the street's split"));
    return `<dt>Found again in ${escapeHtml(a.title)}</dt>
      <dd>${swatch(null)}<span class="res-chip res-research">${
        escapeHtml(words(a.match_status))}</span>${
        holds.length
          ? `<span class="res-chip res-research">${escapeHtml(String(a.year))} holds ${
              escapeHtml(holds.join(' and '))}${noCross.length
                ? `, and ${escapeHtml(noCross.join(' and '))} does not cross` : ''}</span>`
          : ''}
        ${lines ? `<ul class="res-candidates">${lines}</ul>` : ''}
        <span class="res-why">${escapeHtml(a.match_rule)}</span></dd>`;
  }).join('');
  return `${volumes}
    <dd><span class="res-why">${escapeHtml(found.standard || '')}</span>
      ${cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : ''}</dd>`;
}

/**
 * And what the RECORD itself now carries (T-0632). The layer above holds the
 * printed lines and the crosswalks' arithmetic; the household record holds the
 * CLAIM — the later trade and the later address, each graded, dated to the year
 * it describes and citing the volume it was read out of. It is rendered from the
 * record rather than from the layer on purpose: the record is what a reader who
 * opens the JSON sees, and a card showing something its own file does not say
 * would be two answers to one question.
 */
function laterClaimHtml(block, citationsById) {
  if (!block) return '';
  const one = (claim, label) => {
    if (!claim) return '';
    const cites = (claim.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
    return `<dt>${escapeHtml(label)} in ${escapeHtml(String(claim.describes_date))}</dt>
      <dd>${swatch(claim.confidence)}${escapeHtml(claim.value)}
        <br><span class="res-why">${escapeHtml(claim.note)}</span>
        ${cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : ''}</dd>`;
  };
  return one(block.occupation_later, 'A trade printed against this name')
    + one(block.address_later, 'An address printed against this name')
    + backProjectionHtml(block.back_projection)
    + residenceBackProjectionHtml(block.residence_back_projection, citationsById);
}

/**
 * And what was done with the later address (T-0633), which is the half a reader
 * cannot check from the address alone.
 *
 * `docs/ADDRESS-BACK-PROJECTION.md` is the fourth grammar for placing a business:
 * a street printed four to nine years after the scene, read backwards, carried as
 * the business's street FACE and nothing narrower. Fifteen of the eighty-seven
 * addresses on this layer earn one; the other seventy-two do not.
 *
 * ALL EIGHTY-SEVEN ARE SHOWN, and that is the section rather than a caveat on it.
 * An address the pass declines is a reading it made — the 1835 record prints no
 * trade to position, or the directory prints a home and not a shop, or the street
 * is `Michigan ave` where 1835 has Michigan Street, or `cor. Monroe` puts a grocer
 * three blocks outside the platted town. A card showing only the placements would
 * be reporting this pass's successes and hiding its arithmetic, which is exactly
 * what the crosswalks' three match statuses above already refuse to do.
 *
 * NOTHING IS DRAWN. The face has no geometry, on purpose: dealing a roof to a
 * back-projected address would be two inventions under one chip (L218, and
 * `STREET-FACE-ADOPTION.md` limit 3). This row is where the placement reaches a
 * visitor, the same way the fauna layer reaches one under L2.
 */
function backProjectionHtml(bp) {
  if (!bp) return '';
  const placed = bp.outcome === 'placed';
  const label = {
    placed: 'Positioned by reading that address backwards',
    already_better_placed: 'Not read backwards — something better already places it',
  }[bp.outcome] || 'That address was refused, and here is why';
  const where = placed
    ? `${bp.value} — ${bp.placement === 'face'
      ? 'the street face, and nothing narrower'
      : `${words(bp.placement)} on a crossing at ${
        (bp.position_local_enu_m || []).join(', ')} m in the scene's local frame`}`
    : 'no position taken';
  const carried = bp.read_back_years
    ? `<span class="res-chip res-research">${escapeHtml(String(bp.read_back_years))} years back, from ${
      escapeHtml(String(bp.describes_date))}</span>` : '';
  const clause = bp.clause
    ? `<span class="res-chip res-research">clause ${escapeHtml(String(bp.clause))}</span>` : '';
  // A chip only where there is a claim to grade. A refusal is not a figure held
  // at low confidence; it is the absence of a figure, and the record carries no
  // `confidence` on one for exactly that reason.
  const chip = placed ? swatch(bp.confidence) : '';
  return `<dt>${escapeHtml(label)}</dt>
    <dd>${chip}${escapeHtml(where)}${carried}${clause}
      <br><span class="res-why">${escapeHtml(bp.note)}</span></dd>`;
}

/**
 * And the same question asked about a HOME (T-0669), which is a different question and
 * so gets a different row rather than a wider one.
 *
 * `docs/RESIDENCE-BACK-PROJECTION.md` is L218's mechanism aimed at where a man slept:
 * a street the volume prints as `res` or `bds`, read backwards and carried as the
 * household's street FACE. It departs from the business rule in two places, and both
 * are visible here. A home needs no attested trade — everybody the town holds lived
 * somewhere in it — which is why forty-four of these forty-eight belong to people the
 * 1835 papers give no trade and the business pass refused before it ever asked about
 * their houses. And a home never reaches a POINT, not even where the volume prints a
 * corner: that corner hangs off a street number from a grid 1835 did not have.
 *
 * BOTH ROWS CAN APPEAR ON ONE CARD, and that is deliberate. One printed address can
 * carry two rulings because two policies asked two questions of it, and a card showing
 * only the second would leave a reader wondering what became of the first.
 */
function residenceBackProjectionHtml(rp, citationsById) {
  if (!rp) return '';
  const placed = rp.outcome === 'placed';
  const label = {
    placed: 'That home address was read backwards, and here is what it reaches',
    already_better_placed: 'Not read backwards — something better already houses him',
  }[rp.outcome] || 'That home address was refused, and here is why';
  // `rp.placement` is always `face` and is read rather than assumed: the day this
  // policy grows a second unit, the row says so instead of the prose lying.
  const where = placed
    ? `${rp.value} — the ${words(rp.placement)}, and nothing narrower`
    : 'no position taken';
  const kind = rp.kind
    ? `<span class="res-chip res-research">${escapeHtml(
      rp.kind === 'boards' ? 'printed as a lodging' : 'printed as a residence')}</span>` : '';
  const carried = rp.read_back_years
    ? `<span class="res-chip res-research">${escapeHtml(String(rp.read_back_years))} years back, from ${
      escapeHtml(String(rp.describes_date))}</span>` : '';
  const clause = rp.clause
    ? `<span class="res-chip res-research">clause ${escapeHtml(String(rp.clause))}</span>` : '';
  // A chip only where there is a claim to grade, for the reason the row above gives.
  const chip = placed ? swatch(rp.confidence) : '';
  const cites = (rp.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  return `<dt>${escapeHtml(label)}</dt>
    <dd>${chip}${escapeHtml(where)}${kind}${carried}${clause}
      <br><span class="res-why">${escapeHtml(rp.note)}</span>
      ${cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : ''}</dd>`;
}

/**
 * THE CONSOLIDATION'S OWN READING, WHICH NOTHING SHOWED (T-0668).
 *
 * `tools/consolidate_resident_evidence.py` reads seven source domains, decides who
 * is who, and grades each person on a ratified ladder. It writes the whole of that
 * work onto the person: the rung it fired (`ladder_rule`), the fact that the person
 * exists in this layer because that consolidation minted them (`civic_mint`), and
 * every appearance it spent — a quoted reading of the name, the list it stands in,
 * where on the page, the record id, the date the line describes and the source.
 *
 * FORTY-FOUR FIGURES ACROSS 531 PEOPLE, and `tools/measure_layer_reads.py` had
 * every one of them banked as reaching nothing. That is the defect T-0491 named on
 * the 1840 bridge, at twenty times the scale: a grade is a VERDICT, the appearances
 * are the argument that produced it, and a verdict shipped without its argument is
 * an assertion. A reader cannot disagree with `attested` unless they can see the
 * rung that awarded it and the lines it was awarded on.
 *
 * THE RUNG'S TEXT COMES FROM THE DATA, not from here. `GRADE_RULES` in the
 * consolidation tool is the ratified ladder and it is Python; this section reads
 * `vocabulary.ladder_rules` out of `data/residents/index.json`, which that tool
 * writes and its gated `--check` holds equal to the constant. Restating a rung in
 * JavaScript would have been two answers to one question, and the one on the card
 * would be the one that drifted.
 *
 * EVERY LINE CARRIES THE DATE IT DESCRIBES, and that is the section rather than a
 * caveat on it. The domains are not contemporaries of each other: the 1833-1835
 * press names a person in this town, the 1844 directory names them nine years
 * after this scene, and the ladder grades those differently on purpose. A block
 * that showed the readings without their dates would flatten the one distinction
 * the whole consolidation is built on.
 */
const EVIDENCE_DOMAINS = [
  ['press_evidence', 'Named by the town\u2019s own newspapers'],
  ['civic_evidence', 'Named on a civic list \u2014 poll, tax or muster'],
  ['church_evidence', 'Named in the parish register'],
  ['book_evidence', 'Named in a directory or a recollection'],
  ['census_evidence', 'Named in a census'],
];

function evidenceLineHtml(entry, citationsById) {
  const cite = citationsById.get(entry.source);
  return `<li><q>${escapeHtml(String(entry.as_read ?? ''))}</q>
    <br><span class="res-why">In <b>${escapeHtml(words(entry.list))}</b>, describing ${
      escapeHtml(printedOn(entry.describes_date))}${
      entry.locator ? `, at ${escapeHtml(String(entry.locator))}` : ''}. Record ${
      escapeHtml(String(entry.record_id))}, accepted by rung ${
      escapeHtml(String(entry.rule))}.</span>
    ${cite ? `<ol class="cites">${citationItems([cite])}</ol>` : ''}</li>`;
}

function evidenceLadderHtml(person, citationsById, ladderRules) {
  const domains = EVIDENCE_DOMAINS
    .map(([key, label]) => [label, (person[key] || []).filter(Boolean)])
    .filter(([, list]) => list.length);
  const bio = person.biographical_evidence || null;
  if (!domains.length && !person.ladder_rule && !bio) return '';

  const rung = person.ladder_rule
    ? (ladderRules || []).find((r) => r.rung === person.ladder_rule) : null;
  const rungRow = person.ladder_rule
    ? `<dt>The rung this person is graded on</dt>
      <dd>${swatch(rung && rung.grade)}<span class="res-chip res-research">${
        escapeHtml(String(person.ladder_rule))}</span>${
        rung ? escapeHtml(rung.rule) : 'The manifest carries no text for this rung.'}
        <br><span class="res-why">The ladder was ratified on 3 September 2026 and every
          person it reaches is graded by ONE of its rungs, named here. ${
        person.civic_mint
          ? 'This person is in the town because that consolidation minted them: they were '
            + 'read out of the lists below and matched to nobody the project already carried.'
          : 'This person was already in the town; the consolidation graded them rather than '
            + 'minted them.'}</span></dd>`
    : '';

  const evidence = domains.map(([label, list]) => `<dt>${escapeHtml(label)}</dt>
    <dd>${swatch(null)}<span class="res-chip res-research">${list.length} ${
      list.length === 1 ? 'appearance' : 'appearances'}</span>
      <ul class="res-candidates">${
        list.map((e) => evidenceLineHtml(e, citationsById)).join('')}</ul></dd>`).join('');

  const age = bio && bio.age_on_1835_07_01;
  const ageValue = age && age.value && Number.isFinite(age.value.min)
    ? (age.value.min === age.value.max
      ? `${age.value.min}`
      : `between ${age.value.min} and ${age.value.max}`)
    : null;
  const biography = bio
    ? claimRow('Born', bio.birth_year && bio.birth_year.value, bio.birth_year, citationsById)
      + claimRow('Age on 1 July 1835', ageValue, age, citationsById)
    : '';

  return `${rungRow}${evidence}${biography}${
    evidence
      ? `<dd><span class="res-why">Each line above is an APPEARANCE — somebody wrote this
        name down, on that date, in that place. It is evidence about this person and it is
        not an 1835 fact: a directory line of 1844 says the person was in Chicago in 1844,
        and the rung above says what this project was willing to conclude from the set of
        them together.</span></dd>` : ''}`;
}

/**
 * WHEN a trade is unrecorded, on the cards that hold one for a later year (T-0693).
 *
 * `none_recorded` was carrying two different states. "This project holds no trade for
 * this person anywhere" and "it holds none for 1835 and a dated one for 1839" are not
 * the same fact, and a reader could not tell them apart from the field the card reads
 * out. `tools/qualify_later_trades.py` writes a `later_occupation` pointer on the second
 * kind, derived wholly from the `directories` block already on the record; this renders
 * it BESIDE the 1835 value and never in place of it. The 1835 claim is still
 * `none_recorded`, still `reconstructed`, and still says nothing about the scene date.
 */
function laterOccupationHtml(later, citationsById) {
  if (!later || !later.value) return '';
  const cites = (later.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  return `<br><span class="res-why">Recorded for ${escapeHtml(String(later.describes_date))},
    and not for 1835: ${swatch(later.confidence)}${escapeHtml(later.value)}.
    ${escapeHtml(later.note || '')}</span>
    ${cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : ''}`;
}

/**
 * WHAT THE RESEARCH ACTUALLY SAID ABOUT THIS PERSON (T-1232).
 *
 * The layer carries 94 research blocks whose identity the project ASSERTED — its own
 * verdict that the person behind the reading is the person on the card — and the facts
 * inside them sat in paragraphs. `hh_andrus_thomas` is the defect in one record: the
 * DuPage history gives "arrival in Chicago Dec. 1, 1833" and the card's origin said
 * "Not attested."
 *
 * `tools/spend_person_facts.py` adjudicates every one of those candidates and writes the
 * asserted ones onto the person as `profile_facts`. This renders them — each with the
 * DATE IT SPEAKS ABOUT, which is the distinction the whole consolidation rests on, and
 * the sentence it was read from, so a reader can disagree with the verdict rather than
 * take it.
 *
 * THESE ARE NOT THE PERSON'S 1835 CLAIMS. The household's `arrival` block above is a
 * separate claim and this section never displaces it: a postal bound and a stated
 * arrival are different things and both are true at once. A row marked `outside_chicago`
 * is here because it is the reason a presence could not be lifted.
 */
const FACT_LABELS = new Map([
  ['arrival_at_chicago', 'Came to Chicago'],
  ['origin', 'Came from'],
  ['reason_for_coming', 'Why they came'],
  ['sex', 'Sex'],
  ['name_as_printed', 'Also printed as'],
  ['birth_year_bound', 'Born'],
  ['death', 'Died'],
  ['marriage', 'Married'],
  ['life_event', 'What the sources record'],
  ['departure_from_chicago', 'Left Chicago'],
  ['workplace', 'Worked at'],
  ['role', 'Trade or office'],
]);

function profileFactsHtml(facts, citationsById) {
  const rows = (facts || []).filter(Boolean);
  if (!rows.length) return '';
  const body = rows.map((f) => {
    const cites = (f.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
    const label = FACT_LABELS.get(f.field) || words(f.field);
    return `<li><b>${escapeHtml(label)}</b> ${swatch(f.confidence)}${escapeHtml(String(f.value ?? ''))}${
      f.precision ? ` — the source is exact to the ${escapeHtml(words(f.precision))}` : ''}
      <br><span class="res-why">Describing ${escapeHtml(printedOn(f.describes_date))}${
        f.place_class === 'outside_chicago' ? ', and somewhere other than this town' : ''}.
        <q>${escapeHtml(String(f.as_read ?? ''))}</q> ${escapeHtml(String(f.note ?? ''))}
        Record ${escapeHtml(String(f.record_id))}.</span>
      ${cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : ''}</li>`;
  }).join('');
  return `<dt>Spent from the matched research</dt>
    <dd>${swatch(null)}<span class="res-chip res-research">${rows.length} ${
      rows.length === 1 ? 'fact' : 'facts'}</span>
      <ul class="res-candidates">${body}</ul>
      <span class="res-why">Every candidate the research proposed is adjudicated in
        <code>data/residents/person_facts.json</code> — these are the ones this project was
        willing to assert. The rest are withheld WITH THEIR REASON: a volume printed after
        the scene may date and corroborate and may never promote, a source that puts the
        person somewhere else cannot make them a resident here, and a trade belongs to the
        occupation field rather than to this one.</span></dd>`;
}

/**
 * A SOURCE ID IN A SENTENCE IS NOT A CITATION (T-1233).
 *
 * The research blocks are prose, and some of that prose names its sources by their
 * internal handles: a G2b refusal reads "This card rests on 3 thing(s) the consolidation
 * did not read — andreas_1884_v1, fergus_chicago_directory_1839, …". Printed as written,
 * that is the defect the smoke has asserted against since this section was built — the
 * household records must QUOTE their sources, not print their ids — and it caught this
 * wiring on its first run, which is what that assertion is for.
 *
 * So every token in a rendered sentence that resolves to a citation is swapped for the
 * head of that citation, and the citations themselves are listed under the block. The
 * text is escaped BEFORE the swap and the replacement escaped on its way in: the handles
 * are `[a-z0-9_]` and survive escaping unchanged, so the order is safe and the swapped-in
 * title cannot carry markup. A token that resolves to nothing is left exactly as written
 * — inventing a source is worse than showing a handle.
 */
// Every lowercase run, not just the snake_cased ones: `baptisthistoryhomepage` is a
// citation id with no underscore in it, and a pattern that demanded one let exactly that
// handle through. The MAP is the filter — a token that resolves to no citation is left
// alone — so widening the match costs nothing and closes the hole.
const SOURCE_ID = /[a-z][a-z0-9]*(?:_[a-z0-9]+)*/g;

function citeHead(citation) {
  const text = String(citation ?? '');
  if (text.length <= 56) return text;
  const cut = text.slice(0, 56);
  return `${cut.slice(0, Math.max(cut.lastIndexOf(' '), 32))}…`;
}

/** The citations a block declares and the ones its own sentences named, as one list. */
function citesFor(named, citationsById) {
  const cites = [...named].map((id) => citationsById.get(id)).filter(Boolean);
  return cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : '';
}

function prose(text, citationsById, found = null) {
  return escapeHtml(String(text ?? '')).replace(SOURCE_ID, (id) => {
    const cite = citationsById.get(id);
    if (!cite) return id;
    if (found) found.add(id);
    return escapeHtml(citeHead(cite.citation ?? id));
  });
}

/**
 * THE WITHHELD HALF OF THE MATCHED RESEARCH (T-1233).
 *
 * T-1232 put the ASSERTED facts on the card — 40 of them — and left the other 204 in
 * `data/residents/person_facts.json`, a file no renderer opens. That is the shape this
 * project spends most of its effort refusing: a refusal a reader never learns of is
 * indistinguishable from a reading nobody made, and on this layer the refusals are the
 * majority and the argument. `tools/spend_person_facts.py` now projects them to
 * `person_facts_withheld.json` — the full table is 800 kB and three quarters of it says
 * "read, nothing proposed", which is a fact about the search and not about the person.
 *
 * EACH ROW IS THE REASON, NOT THE FACT. The value is printed so the reader can see what
 * was on offer, and it is printed UNDER a heading that says it was not taken; nothing
 * here carries a confidence swatch, because a withheld candidate has no grade — granting
 * it one is the exact move the six rulings exist to stop.
 */
const WITHHELD_HEADS = new Map([
  ['later_only', 'Printed after the scene'],
  ['outside_chicago', 'Puts the person somewhere else'],
  ['contradicted', 'Two readings disagree'],
  ['insufficient_identity', 'Not tied firmly enough to this person'],
  ['duplicate', 'The record already holds it'],
  ['unresolved', 'Handed to another ticket'],
]);

function withheldFactsHtml(rows, citationsById) {
  const list = (rows || []).filter(Boolean);
  if (!list.length) return '';
  const body = list.map((w) => {
    const verdict = String(w.adjudication ?? '');
    const [kind, ticket] = verdict.split(':');
    const cite = citationsById.get(w.source_id);
    const label = FACT_LABELS.get(w.field) || words(w.field);
    return `<li><b>${escapeHtml(WITHHELD_HEADS.get(kind) || words(kind))}</b>${
      ticket ? ` — ${escapeHtml(ticket)}` : ''}
      ${w.field === 'none' ? '' : `<br>${escapeHtml(label)}: <i>${
        escapeHtml(String(w.proposed_value ?? ''))}</i>${
        w.place_class === 'outside_chicago' ? ', and somewhere other than this town' : ''}`}
      <br><span class="res-why">${prose(w.reason, citationsById)}
        Describing ${escapeHtml(printedOn(w.describes_date))}.
        <q>${prose(w.quote, citationsById)}</q>
        Record ${escapeHtml(String(w.claim_or_record_id ?? ''))}.</span>
      ${cite ? `<ol class="cites">${citationItems([cite])}</ol>` : ''}</li>`;
  }).join('');
  return `<dt>Withheld from this card, and why</dt>
    <dd><span class="res-chip res-research">${list.length} ${
      list.length === 1 ? 'refusal' : 'refusals'}</span>
      <ul class="res-candidates">${body}</ul>
      <span class="res-why">These are readings this project made and would not assert. A
        withheld candidate is NOT a fact about this person and must not be read as one —
        it is the reasoning, published so it can be argued with. Every row is adjudicated
        in <code>data/residents/person_facts.json</code>.</span></dd>`;
}

/**
 * THE RESEARCH BLOCK ON THE RECORD ITSELF (T-1233).
 *
 * `researchHtml` above renders `data/residents/research_pilot.json`, which is the
 * published review payload and holds 375 reviews. The RECORDS hold 850 research blocks.
 * So 476 people carried a dated identity review — its verdict, the evidence for and
 * against, the candidates it weighed and the downgrades it refused — and the card said
 * nothing about any of it, because the only reader in the project opened the other copy.
 *
 * That is the K42 census's own finding arriving on the layer it was written for: twenty-
 * three figures over hundreds of people, shipped to a browser and read by nothing. The
 * pilot is not wrong, it is PARTIAL, so this renders the record's block beside it and
 * suppresses the two lines the pilot has already printed rather than printing them twice.
 *
 * `refusals[]` is the part that had to reach a reader. A refusal here is this project
 * declining to move a grade — "the downgrade to inferred", withheld under rule G3 — and
 * a grade whose refusal is invisible is a grade a reader cannot weigh.
 */
function recordResearchHtml(rr, citationsById, pilotShown) {
  if (!rr) return '';
  // The sources the block declares, plus any its own sentences name by handle.
  const named = new Set(rr.source_ids || []);

  const candidates = (rr.candidates || []).map((c) => {
    const cc = (c.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
    return `<li><b>${escapeHtml(c.name || words(c.candidate_id) || words(c.id))}</b>${
      c.candidate_id ? ` <code>${escapeHtml(String(c.candidate_id))}</code>` : ''}
      · ${escapeHtml(c.asserted ? 'asserted as this person' : 'weighed and not asserted')}${
      c.assessment ? ` · ${escapeHtml(words(c.assessment))}` : ''}
      <br><span class="res-why">${prose(c.basis, citationsById, named)}
        ${prose((c.conflicts || []).join(' '), citationsById, named)}</span>
      ${cc.length ? `<ol class="cites">${citationItems(cc)}</ol>` : ''}</li>`;
  }).join('');
  const refusals = (rr.refusals || []).map((r) => `<li><b>Withheld: ${
    escapeHtml(String(r.withheld ?? ''))}</b> · rule ${escapeHtml(String(r.rule ?? ''))}${
    r.regraded_on ? `, regraded ${escapeHtml(printedOn(r.regraded_on))}` : ''}
    <br><span class="res-why">${prose(r.reason, citationsById, named)}</span></li>`).join('');
  return `<dt>The research block on this record</dt>
    <dd>${swatch(null)}<span class="res-chip res-research">${
      escapeHtml(rr.asserted_identity ? 'identity asserted' : 'identity not asserted')}</span>${
      pilotShown ? '' : `<span class="res-chip res-research">${
        escapeHtml(words(rr.outcome))}</span>`}
      <span class="res-why">${pilotShown ? '' : `${prose(rr.summary, citationsById, named)} `}Read
        under ${escapeHtml(String(rr.programme ?? 'the resident research programme'))} for
        ${escapeHtml(String(rr.ticket ?? ''))}, reviewed ${
        escapeHtml(printedOn(rr.reviewed_on))}${
        rr.regraded_on ? `, regraded ${escapeHtml(printedOn(rr.regraded_on))} under rule ${
          escapeHtml(String(rr.rule ?? ''))}` : ''}.</span>
      ${rr.evidence_for ? `<br><span class="res-why"><b>For:</b> ${
        prose(rr.evidence_for, citationsById, named)}</span>` : ''}
      ${rr.evidence_against ? `<br><span class="res-why"><b>Against:</b> ${
        prose(rr.evidence_against, citationsById, named)}</span>` : ''}
      ${rr.proposed_facts ? `<br><span class="res-why"><b>Proposed:</b> ${
        prose(rr.proposed_facts, citationsById, named)}</span>` : ''}
      ${rr.notes ? `<br><span class="res-why">${prose(rr.notes, citationsById, named)}</span>` : ''}
      ${candidates ? `<ul class="res-candidates">${candidates}</ul>` : ''}
      ${refusals ? `<ul class="res-candidates">${refusals}</ul>` : ''}
      ${(rr.candidate_ids || []).length ? `<span class="res-why">Candidates weighed: ${
        escapeHtml((rr.candidate_ids || []).map((id) => words(id)).join(', '))}.</span>` : ''}
      ${citesFor(named, citationsById)}</dd>`;
}

/**
 * WHY THIS PERSON IS NAMED WHAT THEY ARE NAMED (T-1233).
 *
 * Three people on this layer carry a `name_ruling`: two readings of one printed line
 * disagreed on the letters, and somebody ruled which one the card takes. The ruling names
 * the line, what it takes, what it takes it OVER, the reasoning, and — the part a reader
 * of a URL needs — that the id did not move with the name.
 *
 * Nine figures, and every one of them unread until now. A displayed name that changed
 * silently is the same defect as an unattributed grade: the card asserts a spelling and
 * keeps the argument for it in a file.
 */
function nameRulingHtml(ruling, citationsById) {
  if (!ruling) return '';
  const named = new Set();
  const body = `<dt>Why this name, and not the other one</dt>
    <dd>${swatch(null)}Ruled by ${escapeHtml(String(ruling.ruled_by ?? ''))} under rule ${
      escapeHtml(String(ruling.rule ?? ''))}${
      Number.isFinite(ruling.printed_line) ? `, at printed line ${
        escapeHtml(String(ruling.printed_line))}` : ''}, and written down in
      <code>${escapeHtml(String(ruling.ruling ?? ''))}</code>.
      <br><span class="res-why">The card takes ${prose(ruling.takes, citationsById, named)},
        over ${prose(ruling.over, citationsById, named)}. It had displayed
        <q>${escapeHtml(String(ruling.displayed_name_was ?? ''))}</q>.
        ${prose(ruling.reasoning, citationsById, named)}
        ${prose(ruling.the_id_did_not_move, citationsById, named)}</span>`;
  return `${body}${citesFor(named, citationsById)}</dd>`;
}

/**
 * THE CARDS FOLDED INTO THIS ONE, AND THE PAIRS THAT WERE WEIGHED AND KEPT APART (T-1233).
 *
 * `merged_from` is on 31 people and `merge_ruling` on 78, and both were unread. The
 * second is the more important of the two: a verdict of `distinct` is this project
 * deciding that two cards which look like one person are two people, and it carries the
 * case FOR the merge as well as the case against — written down precisely so a reader who
 * disagrees has something to disagree with. A verdict published without its losing
 * argument is an assertion, which is the sentence `laterCensusHtml` above already makes
 * about the 1840 bridge.
 */
function mergedFromHtml(merged, citationsById) {
  const list = (merged || []).filter(Boolean);
  if (!list.length) return '';
  const named = new Set();
  const body = list.map((m) => `<li><b>${
    escapeHtml((m.cards || []).map((c) => words(c)).join(', '))}</b>
    <br><span class="res-why">Folded under rule ${escapeHtml(String(m.rule ?? ''))} by ${
    escapeHtml(String(m.ticket ?? ''))}, in the ${escapeHtml(String(m.cluster ?? ''))}
    cluster. ${prose(m.note, citationsById, named)}</span></li>`).join('');
  return `<dt>Cards folded into this person</dt>
    <dd>${swatch(null)}<ul class="res-candidates">${body}</ul>${
      citesFor(named, citationsById)}</dd>`;
}

function mergeRulingHtml(rulings, citationsById) {
  const list = (rulings || []).filter(Boolean);
  if (!list.length) return '';
  const named = new Set();
  const body = list.map((r) => `<li><b>${escapeHtml(words(r.verdict))}</b> from ${
    escapeHtml((r.weighed_against || []).map((c) => words(c)).join(', '))}, under rule ${
    escapeHtml(String(r.rule ?? ''))} in the ${escapeHtml(String(r.cluster ?? ''))} cluster
    (${escapeHtml(String(r.ticket ?? ''))})${
    r.referred_to ? `, referred to ${escapeHtml(String(r.referred_to))}` : ''}
    <br><span class="res-why"><b>For a merge:</b> ${prose(r.for_merge, citationsById, named)}</span>
    <br><span class="res-why"><b>Against:</b> ${prose(r.against_merge, citationsById, named)}</span></li>`).join('');
  return `<dt>Weighed against another card</dt>
    <dd>${swatch(null)}<ul class="res-candidates">${body}</ul>
      <span class="res-why">Both sides are printed. A verdict that two look-alike cards are
        two people is a judgement, and the case for the other answer is what makes it one.</span>${
      citesFor(named, citationsById)}</dd>`;
}

/**
 * THE OLD-SETTLER DEATH NOTICE, ON THE PERSON IT WAS MATCHED TO (T-1233).
 *
 * Fergus's 1843 directory (1896) prints an obituary list, and 63 households carry a
 * reading of it — 19 figures, none of them read. The match is a SURNAME AND A FIRST
 * INITIAL and the record says so in three separate fields; the birth year is this
 * project's own subtraction from a printed age, shown with the arithmetic so a reader can
 * redo it. THE HEADER OF THE LIST IS THE LIMIT THE WHOLE READING TURNS ON — it admits
 * people who arrived after 1843 and people merely "prominently connected with Illinois
 * history" — so it is quoted on the card rather than summarised.
 *
 * It is a death, not an 1835 fact. Nothing here moves a grade; T-0513's ladder is what
 * says so and T-0514/T-0515 apply it.
 */
function oldSettlerDeathHtml(block, personId, citationsById) {
  if (!block) return '';
  const entry = (block.people || []).find((p) => p.person_id === personId);
  if (!entry) return '';
  const named = new Set(block.sources || []);
  const initialOnly = entry.matched_on_initial_only || entry.entry_given_is_initial_only
    || entry.resident_given_is_initial_only;
  return `<dt>A death notice that meets this name</dt>
    <dd>${swatch(null)}${escapeHtml(String(entry.manner_of_death ?? 'died'))} at ${
      escapeHtml(String(entry.place_of_death ?? 'a place the page does not give'))} on ${
      escapeHtml(printedOn(entry.death_date))}, ${
      escapeHtml(String(entry.age_as_printed ?? ''))}${
      entry.trade_or_office ? ` · ${escapeHtml(words(entry.trade_or_office))}` : ''}
      <br><span class="res-why">Matched as ${escapeHtml(String(entry.matched_as ?? ''))} — ${
        prose(entry.matched_by, citationsById, named)} The agreement is ${
        escapeHtml(String(entry.the_agreement ?? ''))}; the entry's given name reads
        <q>${escapeHtml(String(entry.entry_given_as_read ?? ''))}</q>${
        initialOnly ? ' and the match rests on an initial alone' : ''}.
        Born between ${escapeHtml(String(entry.birth_year_earliest ?? ''))} and ${
        escapeHtml(String(entry.birth_year_latest ?? ''))}: ${
        prose(entry.birth_year_arithmetic, citationsById, named)}
        The page reads <q>${escapeHtml(String(entry.as_read ?? ''))}</q>, record ${
        escapeHtml(String(entry.record_id ?? ''))}.</span>
      <br><span class="res-why">THE LIST'S OWN HEADER IS THE LIMIT:
        <q>${escapeHtml(String(block.the_header_admission ?? ''))}</q>
        ${prose(block.note, citationsById, named)}</span>
      ${citesFor(named, citationsById)}</dd>`;
}

/**
 * THE PLURAL DATED PLACES (T-1240, folded into T-1255; schema from T-1238).
 *
 * A household had exactly one home and exactly one workplace and neither carried
 * a date, which is not how the sources read: Andreas has Peck invite Porter to
 * make his "temporary lodging place and study" in the loft of an unfinished store
 * in 1833, and says nothing about whether he was still in it on 1 July 1835.
 * Written into a singular `lives_at`, that comes out as the household's residence
 * at the scene date — the one claim the source refuses to make. `associated_with[]`
 * is the shape that can hold it, and until this block nothing read it: seven rows
 * on four records reached a browser and were rendered nowhere.
 *
 * WHAT THIS BLOCK WILL NOT DO IS DECIDE WHETHER A ROW REACHES THE SCENE DATE.
 * A role carries the record's own `covers_scene_date` and this block prints it; a
 * place carries no such figure, and computing one here is precisely the
 * flattening the plural shape exists to refuse. An open `to` on this layer means
 * NO SOURCE CLOSES THE RELATIONSHIP — Porter's loft and his charge both say so in
 * their own notes — so an open row is printed as open and the question is left
 * unanswered rather than answered wrongly. Three things can honestly be said, and
 * each is said in the row's own words: a relationship that ENDED before 1 July
 * 1835 (Eliza Chappel Porter's infant school, 1833 to 1834, which nothing in the
 * singular shape could express at all), one that is UNDATED at both ends and
 * admits it, and one that is open at the far end and therefore undecided.
 *
 * The rung is part of the claim, not decoration: `resolves_to` says how far the
 * evidence reached — a roof, a street, a part of town — and a row that names a
 * street is not a row that names a building.
 */
const SCENE_DATE = '1835-07-01';

/**
 * Does a closed far end reach 1 July 1835? A bound is stored at the precision its
 * source permits, so `1834` and `1835-06` have to be read as the LAST day they can
 * mean before they are compared — `1835-06` is June, and June ends before the day
 * this scene is set on.
 */
function endsOnOrAfterSceneDate(to) {
  const s = String(to ?? '');
  if (/^\d{4}$/.test(s)) return `${s}-12-31` >= SCENE_DATE;
  if (/^\d{4}-\d{2}$/.test(s)) return `${s}-31` >= SCENE_DATE;
  return s >= SCENE_DATE;
}

function associationReach(link) {
  if (link.undated || (!link.from && !link.to)) return ['res-role-off', 'not dated'];
  if (!link.to) return ['', 'no source closes it'];
  return endsOnOrAfterSceneDate(link.to)
    ? ['res-role-scene', 'reaches 1 July 1835']
    : ['res-role-off', 'ended before 1 July 1835'];
}

function associationRowHtml(link, citationsById) {
  const cite = citationsById.get(link.source_id);
  const [cls, mark] = associationReach(link);
  const at = cls === 'res-role-scene';
  const place = link.place_or_structure_id
    ? escapeHtml(words(link.place_or_structure_id)) : 'a place the record does not name';
  return `<li class="res-role-row${at ? ' res-role-at' : ''}">
    <span class="res-role-when">${escapeHtml(associationBound(link))}</span>
    ${swatch(link.tier)}${escapeHtml(words(link.kind))} · ${place}
    <span class="res-chips">${link.resolves_to
      ? `<span class="res-chip">reaches a ${escapeHtml(words(link.resolves_to))}</span>` : ''}<span
      class="res-chip ${cls}">${escapeHtml(mark)}</span></span>
    ${link.note ? `<span class="res-why">${escapeHtml(link.note)}</span>` : ''}
    ${cite ? `<ol class="cites">${citationItems([cite])}</ol>` : ''}</li>`;
}

function associationBound(link) {
  const one = (iso) => {
    const s = String(iso ?? '');
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return printedOn(s);
    const m = /^(\d{4})-(\d{2})$/.exec(s);
    return m ? `${MONTHS[Number(m[2]) - 1]} ${m[1]}` : s;
  };
  if (link.undated || (!link.from && !link.to)) return 'no date either end';
  if (link.from && link.to) {
    return String(link.from) === String(link.to) ? one(link.from)
      : `${one(link.from)} to ${one(link.to)}`;
  }
  return link.from ? `from ${one(link.from)}, no end recorded`
    : `until ${one(link.to)}, no start recorded`;
}

export function associationsHtml(links, citationsById, label) {
  const list = (links || []).filter(Boolean);
  if (!list.length) return '';
  const order = [...list].sort((a, b) => {
    const key = (l) => (l.undated ? '9999' : String(l.from ?? l.to ?? '9999'));
    return key(a).localeCompare(key(b));
  });
  const undated = order.filter((l) => l.undated || (!l.from && !l.to)).length;
  return `<dt>${escapeHtml(label)}</dt>
    <dd>${swatch(null)}<span class="res-chip res-research">${order.length} dated ${
      order.length === 1 ? 'connection' : 'connections'}</span>${undated
      ? `<span class="res-chip res-role-off">${undated} with no date either end</span>` : ''}
      <br><span class="res-why">A home, a lodging, a workplace, a business premises, a
        church, a civic seat, a school or land bought — each with how far the evidence
        reached and the years it permits. An open end means no source closes the
        relationship, so this list does not say whether such a row held on 1 July 1835;
        where a source DOES close one before that day, the row says so. The single
        <q>Lived at</q> and <q>Worked at</q> claims above are the older shape of the same
        facts, and the build refuses to let the two disagree.</span>
      <ol class="res-roles">${order.map((l) => associationRowHtml(l, citationsById)).join('')}</ol></dd>`;
}

/**
 * THE DATED ROLES, AS A TIMELINE (T-1255, of T-1145; folds in T-1283).
 *
 * `persons[].roles[]` is the canonical record of a trade, a profession or an
 * office — `index.json` `_roles_doc` states it — and `occupation` is a GENERATED
 * view of the roles that cover 1 July 1835. Until this block the card showed only
 * the view, which meant a card could show at most one trade and could show none
 * at all for a man the sources word three times: Daniel Elston is printed a soap
 * and candle manufacturer in November 1833 and a brickmaker in 1839, and his card
 * read `none_recorded` for 1835 with both roles unrendered. 262 people carry 267
 * roles; 140 of them are outside the scene window and were visible nowhere.
 *
 * SO IT IS A TIMELINE, AND EACH ROW SAYS WHETHER IT REACHES THE SCENE DATE. The
 * order is the year a bound opens, undated last. A role that does not reach
 * 1 July 1835 is marked as not reaching it rather than dropped or dimmed away:
 * the whole point of the plural field is that a life has more than one year in
 * it, and `covers_scene_date` is the record's own answer, never recomputed here.
 *
 * WHAT A ROW PRINTS AND WHAT IT DOES NOT. The controlled word where the source's
 * wording has been adjudicated into `vocabulary.occupations`, the wording AS
 * PRINTED where it has not — and where `role` is null the row SAYS the wording is
 * not adjudicated, because a printed word standing in for a controlled one is a
 * weaker claim and T-1254 is where the rest are ruled on. The bound is printed at
 * the precision the record gives it, `dated_by` says how it was dated, and an
 * unknown date stays unknown: nothing here widens a bound to the scene date.
 *
 * A role carries no PLACE and no employer yet — that is T-1254's migration — so
 * this block makes no claim about where the work was done. The location half of
 * AND WHETHER THE TRADE HAD PREMISES (T-1404). `premises` is the half of the
 * workplace question that is not a business record: a clerk keeps somebody
 * else's counter and a teamster drives on the road, so the role itself says
 * `no_fixed_premises` and the row prints that chip. An `own_premises` role needs
 * no chip — the house it implies is a record of its own in the business layer,
 * and the card's Works-at row is where it shows.
 *
 * T-1240 waits on the same data: no record in the layer carries a dated location
 * link or a location limit, and the household's `lives_at`/`works_at` are single
 * undated claims, rendered as such by `householdHtml` above.
 */
function roleBound(role) {
  const one = (iso) => {
    const s = String(iso ?? '');
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return printedOn(s);
    const m = /^(\d{4})-(\d{2})$/.exec(s);
    return m ? `${MONTHS[Number(m[2]) - 1]} ${m[1]}` : s;
  };
  const from = role.from ?? null;
  const to = role.to ?? null;
  if (!from && !to) return 'not dated';
  if (from && to) return String(from) === String(to) ? one(from) : `${one(from)} to ${one(to)}`;
  return from ? `from ${one(from)}` : `until ${one(to)}`;
}

/** The year a bound opens in, for the order — undated last. */
function roleOpensIn(role) {
  const m = /^(\d{4})/.exec(String(role.from ?? role.to ?? ''));
  return m ? Number(m[1]) : Infinity;
}

function roleRowHtml(role, citationsById) {
  const cites = (role.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  const printed = role.as_printed ? `<q>${escapeHtml(String(role.as_printed))}</q>` : '';
  const controlled = role.role ? escapeHtml(words(role.role)) : '';
  const said = controlled && printed ? `${controlled} · printed ${printed}`
    : controlled || printed || 'a role the source does not word';
  const at = Boolean(role.covers_scene_date);
  const precision = role.precision && role.precision !== 'unknown'
    ? ` to the ${escapeHtml(words(role.precision))}` : '';
  // T-1299 — WHERE THE ROLE WAS WORKED, AND FOR WHOM. Both figures have been on every
  // row since T-1254 and banked unread since T-1255 shipped this renderer beside it;
  // 164 roles state a place and 56 a body. `not_stated` is the record's assertion that
  // its source does not say, and it prints as nothing rather than as an empty line.
  const place = role.place && role.place !== 'not_stated' ? String(role.place) : '';
  const body = role.employer_or_body && role.employer_or_body !== 'not_stated'
    ? String(role.employer_or_body) : '';
  const where = place || body
    ? `<span class="res-why">${place ? `Worked at ${escapeHtml(place)}` : 'Worked'}${
        body ? `${place ? ', ' : ' '}for ${escapeHtml(body)}` : ''}, as the record that
        prints this role states it.</span>`
    : '';
  return `<li class="res-role-row${at ? ' res-role-at' : ''}">
    <span class="res-role-when">${escapeHtml(roleBound(role))}</span>
    ${swatch(role.confidence)}${said}
    <span class="res-chips">${role.kind
      ? `<span class="res-chip">${escapeHtml(words(role.kind))}</span>` : ''}<span
      class="res-chip ${at ? 'res-role-scene' : 'res-role-off'}">${at
        ? 'reaches 1 July 1835' : 'not on 1 July 1835'}</span>${role.premises === 'no_fixed_premises'
      ? '<span class="res-chip res-role-off">no premises of its own</span>' : ''}${role.role
      ? '' : '<span class="res-chip res-role-off">wording not adjudicated</span>'}</span>
    <span class="res-why">Dated by ${escapeHtml(words(role.dated_by || 'undated'))}${precision}.${
      role.note ? ` ${escapeHtml(role.note)}` : ''}</span>
    ${where}
    ${cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : ''}</li>`;
}

export function rolesHtml(roles, citationsById) {
  const list = (roles || []).filter(Boolean);
  if (!list.length) return '';
  const ordered = [...list].sort((a, b) => roleOpensIn(a) - roleOpensIn(b));
  const at = ordered.filter((r) => r.covers_scene_date).length;
  return `<dt>What this person did, and when</dt>
    <dd>${swatch(null)}<span class="res-chip res-research">${list.length} dated ${
      list.length === 1 ? 'role' : 'roles'}</span><span class="res-chip ${
      at ? 'res-role-scene' : 'res-role-off'}">${at
        ? `${at} reaching 1 July 1835` : 'none reaching 1 July 1835'}</span>
      <br><span class="res-why">A trade, a profession or an office, each held to the
        bound its own sources permit. This is the record; the <q>Occupation</q> row
        above is a generated view of the roles that cover 1 July 1835, which is why a
        role printed in another year does not fill it. A role outside the window is
        kept and marked, not dropped. Where a source states the place a role was worked
        or the body it was worked for, the row says so. The houses a source names this
        person IN are the row below.</span>
      <ol class="res-roles">${ordered.map((r) => roleRowHtml(r, citationsById)).join('')}</ol></dd>`;
}

/**
 * Why a person nobody named is standing in this town, on their own card (T-1314).
 *
 * A `reconstructed` person is the one kind of record here that a visitor could
 * mistake for a finding, so the card says the opposite out loud: which stage of the
 * reconstruction programme wrote them, what counted them, what age the count puts
 * them at, and what would retire them. `basisHtml` already prints the basis, the
 * seed that redraws a model draw and the replacement rule — the same three parts a
 * reconstructed ATTRIBUTE shows — so the person reuses it rather than growing a
 * second vocabulary for the same idea.
 */
function reconstructionHtml(person) {
  const rc = person && person.reconstruction;
  if (!rc || typeof rc !== 'object') return '';
  const age = rc.age_on_scene_date || null;
  const span = age
    ? (age.high === null || age.high === undefined ? `${age.low} or older` : `${age.low}–${age.high}`)
    : '';
  return `<dt>Why this person is here</dt><dd>${swatch('reconstructed')}No source names them.
    They are written by the <code>${escapeHtml(String(rc.stage || ''))}</code> stage of
    ${escapeHtml(String(rc.programme || 'the reconstruction programme'))}${
    rc.counted_by ? `, counted by ${escapeHtml(String(rc.counted_by))}` : ''}.${
    rc.band_1840 ? `<br><span class="res-why">The record that counts them reads
      “${escapeHtml(String(rc.band_1840))}”${span ? `, which is ${escapeHtml(span)} on 1 July 1835` : ''}.
      </span>` : ''}${
    rc.community ? `<br><span class="res-why">The invented forename is drawn from the
      ${escapeHtml(String(rc.community))} pool.</span>` : ''}
    ${basisHtml(person)}</dd>`;
}

/**
 * A BIRTH INTERVAL THE CARD REFUTED (T-1179).
 *
 * `tools/spend_person_sex_age.py` spends an obituary's arithmetic into a `birth_year`,
 * and until T-1179 it spent it without ever reading the rest of the card. George Smith
 * advertised the Exchange Coffee House in the Democrat through 1834 and 1835 and his
 * card said he was born in 1831, so the town held a coffee-house keeper of four.
 *
 * The match is not withdrawn and no age is put in its place — the refusal is of the
 * SPEND, and the block that records it lives in `birth_year` like any other, asserting
 * no value. It takes the Born row rather than leaving it blank, because a card that
 * simply stopped printing a birth year would tell a reader nothing about the obituary
 * still sitting further down the same card. The `unknown` chip is the right one: after
 * the refusal this project asserts no birth year for the person at all.
 */
function birthRefusedHtml(block, citationsById) {
  const cites = (block.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  const [from, to] = block.refused_interval || [];
  const years = from === to ? `${from}` : `${from} or ${to}`;
  return `<dt>Born</dt>
    <dd>${swatch('unknown')}${tierWord('unknown')}not recorded — an obituary matched to
      this name puts the birth in ${escapeHtml(years)}, and this card refuses it
      <br><span class="res-why">${escapeHtml(block.note || '')}</span>${
      block.as_read ? `<br><span class="res-why">The page reads <q>${
        escapeHtml(String(block.as_read))}</q>, record ${
        escapeHtml(String(block.record_id ?? ''))}.</span>` : ''}${
      cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : ''}</dd>`;
}

/**
 * WHERE THIS PERSON WORKED (T-1432, piece 1 of T-1189).
 *
 * The business layer has always known: 144 of its person rows carry a `person_id` and
 * 110 town cards answer to them. The cards did not — `persons[]` held no workplace at
 * all, so a man who kept a store and a card that said nothing about a store were the
 * same person read from two ends. `tools/staff_businesses_1835.py` writes the join
 * down and `tools/check.sh` holds it from both ends; this prints it.
 *
 * It is `workplaces` and NOT `works_at` deliberately. `works_at` is the BUILDING: a
 * singular, undated structure id that `validate.py` polices as a link, and the card
 * prints it on the household above. This is the FIRM, plural and dated, one entry a
 * (house, role). Two questions, two words.
 *
 * NOTHING IS UPGRADED BY BEING SHOWN. Each row wears the tier the business record gave
 * it and opens on that record's own citation, which is why a partner the register read
 * out of a firm style and a partner matched to a card do not read alike here.
 */
function workplacesHtml(rows, citationsById) {
  const list = (rows || []).filter(Boolean);
  if (!list.length) return '';
  const item = (w) => {
    // The citation join is keyed by SOURCE id; `claim_ids` are the individual
    // notices inside that source, which the row counts rather than lists.
    const cites = [w.source_id].filter(Boolean).map((id) => citationsById.get(id)).filter(Boolean);
    const notices = (w.claim_ids || []).length;
    const from = w.from ? printedOn(w.from) : '';
    const to = w.to ? printedOn(w.to) : '';
    const when = from && to && from !== to ? `${from} – ${to}` : (from || to || '');
    return `<li>${swatch(w.tier)}${tierWord(w.tier)}<b>${escapeHtml(w.business_name || w.business_id)}</b>
      <span class="res-role">${escapeHtml(words(w.role || ''))}</span>${
      w.business_present_at_scene_date ? '' : '<span class="res-chip res-role-off">not trading on 1 July 1835</span>'}
      ${when ? `<br><span class="res-why">The ${notices ? `${notices} ` : ''}${
  notices === 1 ? 'notice' : 'notices'} that carry this run ${escapeHtml(when)}. They bound
        the READING and do not date the employment.</span>` : ''}
      ${w.printed_as && w.printed_as !== (w.business_name || '')
    ? `<br><span class="res-why">Printed as <q>${escapeHtml(w.printed_as)}</q>.</span>` : ''}
      ${w.basis ? `<br><span class="res-why">${escapeHtml(w.basis)}</span>` : ''}
      ${cites.length ? `<ol class="cites">${citationItems(cites)}</ol>` : ''}</li>`;
  };
  return `<dt>Where they worked</dt>
    <dd>${swatch(null)}<span class="res-chip res-research">${list.length} ${
  list.length === 1 ? 'house' : 'houses'} the sources name them in</span>
      <br><span class="res-why">Carried from the business layer, which is where the
        evidence for it lives, at that record\u2019s own grade — nothing is upgraded by
        being joined. A house nobody named them in is not here: the hands the staffing
        model says a house of this kind employed are reconstructed work and are not
        written onto anybody\u2019s card by this row.</span>
      <ul class="res-workplaces">${list.map(item).join('')}</ul></dd>`;
}


/**
 * WHERE A RECONSTRUCTED TRADE WAS FOLLOWED, OR WHY NOWHERE (T-1433, piece 2 of T-1189).
 *
 * The row above prints the houses a SOURCE names this person in. This one is the other
 * half of the town: 524 residents this project reconstructed, each given a trade by the
 * town model and, until now, nowhere to follow it. `tools/seat_reconstructed_trades_1835.py`
 * seats the ones the staffing model can seat and states, for every one it cannot, the
 * reason in the words of the ruling that decided it.
 *
 * IT IS A JOIN BESIDE THE LAYER, NOT A FIELD ON THE CARD, and that is not a detail of
 * plumbing. Two thirds of these people stand on cards a reconstruction STAGE derives
 * whole and compares byte for byte, so a key appended to one of those cards breaks that
 * stage's gate rather than adding a field. The seating is loaded the way
 * `residents/directories.json` is, keyed on person_id, and a load that fails costs this
 * block and never the card.
 *
 * IT IS DRAWN AND IT SAYS SO, EVERY TIME. The chip is the `reconstructed` hatch, the
 * block carries the seed it was drawn from, and `chosen_by` names which term of the
 * order rule actually decided the seat — because two of the three terms the rule states
 * are inert against the layer as it stands, and a card that hid that would be claiming
 * a precision the data does not have.
 */
function employmentHtml(seatingByPerson, personId) {
  const e = seatingByPerson && seatingByPerson.get(personId);
  if (!e) return '';
  const basis = e.basis && e.basis.note ? e.basis.note : '';
  const drawn = {
    seated: 'Seated by the staffing model',
    class_held_no_house: 'No house of this kind has room',
    keeps_their_own_house: 'Owed a house of their own',
    no_employer_named: 'No employer can be named',
    no_ruling: 'No ruling on this trade yet',
  }[e.kind] || e.kind;
  const term = {
    division_match: 'the house stands in their own division',
    nearest: 'it is the nearest house of the trade to where they live',
    seeded_draw: 'a seeded draw — no division and no distance separated the candidates',
  };
  const how = (e.chosen_by || []).map((t) => term[t] || t).join('; ');
  return `<dt>Where this reconstructed trade was followed</dt>
    <dd>${swatch('reconstructed')}${tierWord('reconstructed')}<span class="res-chip res-research">${
  escapeHtml(drawn)}</span>
      ${e.business_id ? `<br><b>${escapeHtml(e.business_name || e.business_id)}</b>${
        e.role ? `<span class="res-role">${escapeHtml(words(e.role))}</span>` : ''}` : ''}
      ${how ? `<br><span class="res-why">Chosen because ${escapeHtml(how)}${
        e.candidates_considered ? ` — ${e.candidates_considered} house${
          e.candidates_considered === 1 ? '' : 's'} of the trade were open to them` : ''}.</span>` : ''}
      ${basis ? `<br><span class="res-why">${escapeHtml(basis)}</span>` : ''}
      ${e.replaceable_by && e.replaceable_by.match
    ? `<br><span class="res-why">Withdrawn by ${escapeHtml(e.replaceable_by.match)}.</span>` : ''}
      <br><span class="res-why">Drawn, not read. No source places this person at work
        anywhere; the seat is a pointer at a house the business layer already holds,
        reproducible from the seed <code>${escapeHtml(e.seed || '')}</code>. Nothing is
        written onto the house itself until the staffing shortfall is minted.</span></dd>`;
}


/**
 * WAS THIS PERSON AT WORK, AND IF NOT, WHY NOT (T-1461, piece 1 of T-1449).
 *
 * The two blocks above are both true and neither covers the town. `workplaces` prints
 * the 112 cards a SOURCE names in a house; the seating prints the 524 reconstructed
 * trade-holders. That is 636 people of 3,243, and the other 2,607 carried no workplace,
 * no seat and no reason — a card that had never been asked the question looked exactly
 * like a card that had been asked and answered no.
 *
 * `tools/employment_coverage_1835.py` gives every person ONE answer from a closed set of
 * five, and this prints it on every card, including the ones the blocks above already
 * detail. That is deliberate: the guarantee is that a reader who opens any card finds
 * the question answered, and a guarantee with exceptions is not one. Where a block above
 * carries the houses, this carries the sentence and points at them.
 *
 * IT SAYS "AT WORK" AND "NOT PLACED" AS TWO DIFFERENT THINGS. The soldier at the post
 * and the laundress over her own tub follow a trade and have no employer in the business
 * layer. Printing them as unemployed would be false; printing them as placed would be an
 * invention. `at_a_trade_with_no_house_to_join` is neither, and the sentence says which.
 *
 * Its own loader, degrading like every other join here: a miss costs this block on a
 * card and never the card.
 */
const COVERAGE_HEADLINE = {
  at_a_named_house: 'At a house a source names',
  at_a_seat_this_project_drew: 'At a seat this project drew',
  on_their_own_account: 'On their own account',
  at_a_trade_with_no_house_to_join: 'At a trade with no house to join them to',
  no_trade_recorded: 'No trade recorded',
};

const COVERAGE_AGE = {
  below_working_age: 'The age band on this card lies wholly below the youngest age the '
    + 'staffing model puts anybody to work at, so no employment is looked for.',
  age_is_not_settled: 'The age band on this card does not settle whether this person was '
    + 'of working age — it straddles the model\u2019s floor, or the card carries none. '
    + 'They are answered anyway, and counted apart so a reader can take them out again.',
};

function employmentCoverageHtml(coverage, personId) {
  const row = coverage && coverage.byPerson && coverage.byPerson.get(personId);
  if (!row) return '';
  const headline = COVERAGE_HEADLINE[row.status] || words(row.status || '');
  const placed = !!(coverage.placed && coverage.placed.has(row.status));
  const sentence = (coverage.words && coverage.words[row.reason]) || '';
  const age = COVERAGE_AGE[row.age_scope] || '';
  return `<dt>Were they at work?</dt>
    <dd><span class="res-chip ${placed ? 'res-research' : 'res-role-off'}">${
  escapeHtml(headline)}</span>
      ${sentence ? `<br><span class="res-why">${escapeHtml(sentence)}</span>` : ''}
      ${age ? `<br><span class="res-why">${escapeHtml(age)}</span>` : ''}
      ${row.decided_by ? `<br><span class="res-why">Decided by <code>${
    escapeHtml(row.decided_by)}</code>.</span>` : ''}
      <br><span class="res-why">One answer, from a closed set of five, for every person in
        the layer \u2014 so a card that has never been asked cannot read like a card that
        was asked and answered no. Nothing here supplies a trade, seats anybody or writes
        a byte onto a business record.</span></dd>`;
}


export function personHtml(person, citationsById, researchByPerson, directoryByPerson,
  directoriesOnRecord, ladderRules, withheldByPerson = new Map(), oldSettlerDeaths = null,
  seatingByPerson = new Map(), coverage = null) {
  const occ = person.occupation || {};
  // The roles are the record and `occupation` is the view of them that covers the
  // scene date (T-1255): the summary says how many there are so a card with a
  // trade printed in another year does not read, closed, as a card with no trade.
  const roles = (person.roles || []).filter(Boolean);
  const rolesAtScene = roles.filter((r) => r.covers_scene_date).length;
  const cites = (person.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  const occCites = (occ.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
  const born = person.birth_year || null;
  const aged = person.age_on_scene_date || null;
  const named = person.name_basis || null;
  // T-1303. Where a sex was READ — off a gendered title, off a forename that stands in
  // one sex's naming only — the reasoning travels with it and the row is a graded claim
  // like every other. Where it came off a source with the rest of the record, the mints
  // wrote the bare string and there is no reasoning of ours to print.
  //
  // T-1304 writes the same block for a sex it DREW, graded `reconstructed`, and that is
  // the whole reason no new rendering was needed for it: `claimRow` already prints the
  // tier, the reasoning, the model the value was drawn from, the seed that redraws it and
  // the evidence that would retire it. A drawn value that rendered like a read one would
  // be the misrepresentation; a drawn value that renders THROUGH the same graded row,
  // wearing the reconstructed chip and opening on its own seed, is the opposite.
  const basis = person.sex_basis || null;
  return `<details class="lib res-person">
    <summary><span class="lib-title">${swatch(person.grade)}${escapeHtml(person.name || 'unnamed')}</span>
      <span class="res-role">${escapeHtml(words(person.relationship))}${
        occ.value ? ` · ${escapeHtml(words(occ.value))}` : ''}${
        occ.later_occupation ? ` for 1835 · a trade is printed for ${
          escapeHtml(String(occ.later_occupation.describes_date))}` : ''}${
        roles.length ? ` · ${roles.length} dated ${roles.length === 1 ? 'role' : 'roles'}${
          rolesAtScene ? '' : ', none on 1 July 1835'}` : ''}</span></summary>
    <dl class="lib-body">
      ${row('In the household as', words(person.relationship))}
      ${basis
        ? claimRow('Sex', words(basis.value), basis, citationsById)
        : row('Sex', words(person.sex))}
      ${claimRow('Age on 1 July 1835', aged && aged.value, aged, citationsById)}
      ${born && born.refused_because
        ? birthRefusedHtml(born, citationsById)
        : claimRow('Born', bornYears(born), born, citationsById)}
      ${born && born.contradicted_by_the_card
        ? `<dd><span class="res-why">${escapeHtml(born.contradicted_by_the_card)}</span></dd>`
        : ''}
      ${claimRow('Age band on 1 July 1835', bandYears(person.age_band),
        person.age_band, citationsById)}
      ${occ.value ? `<dt>Occupation</dt><dd>${swatch(tierOf(occ))}${tierWord(tierOf(occ))}${
        isNotAsserted(occ) ? 'not recorded' : escapeHtml(words(occ.value))}${
        occ.later_occupation ? ' for 1835' : ''}${
        occ.note ? `<br><span class="res-why">${escapeHtml(occ.note)}</span>` : ''}${
        laterOccupationHtml(occ.later_occupation, citationsById)}${
        occCites.length ? `<ol class="cites">${citationItems(occCites)}</ol>` : ''}</dd>` : ''}
      ${rolesHtml(roles, citationsById)}
      ${workplacesHtml(person.workplaces, citationsById)}
      ${employmentHtml(seatingByPerson, person.id)}
      ${employmentCoverageHtml(coverage, person.id)}
      ${associationsHtml(person.associated_with, citationsById,
        'Where this person was, and when')}
      ${claimRow('How this person is named', named && named.value, named, citationsById)}
      ${reconstructedHtml(person)}
      ${person.letter_list_only
        ? `<dt>How this person is known</dt><dd>${swatch('attested')}Only from the post office's lists of uncalled-for letters. A name on one of those lists is somebody a correspondent believed was reachable at Chicago; it gives no trade, no street and no household, and it is the weakest evidence this project accepts for a resident. A shopkeeper who advertised his stock is a different claim, and this row is here so the two never read as the same one.</dd>` : ''}
      ${person.letter_list_only && (person.letter_list_returns || []).length
        ? `<dt>The post office was holding a letter on</dt><dd>${swatch('attested')}${
          (person.letter_list_returns || []).map((d) => escapeHtml(printedOn(d))).join(' · ')
        }<br><span class="res-why">Each date is a separate return of uncalled-for letters
          carrying this name — not a reprint of one. It is the sharpest thing this record
          can be dated by: a letter waiting on 1 July 1835 is the day this scene is set,
          and one waiting eighteen months earlier is a different claim about the same
          person.</span></dd>` : ''}
      ${person.note ? `<dt>What the sources say</dt><dd>${escapeHtml(person.note)}</dd>` : ''}
      ${reconstructionHtml(person)}
      ${nameRulingHtml(person.name_ruling, citationsById)}
      ${profileFactsHtml(person.profile_facts, citationsById)}
      ${withheldFactsHtml(withheldByPerson.get(person.id), citationsById)}
      ${evidenceLadderHtml(person, citationsById, ladderRules)}
      ${researchHtml(researchByPerson.get(person.id), citationsById)}
      ${recordResearchHtml(person.resident_research, citationsById,
        Boolean(researchByPerson.get(person.id)))}
      ${mergedFromHtml(person.merged_from, citationsById)}
      ${mergeRulingHtml(person.merge_ruling, citationsById)}
      ${oldSettlerDeathHtml(oldSettlerDeaths, person.id, citationsById)}
      ${laterCensusHtml(person.later_census, citationsById)}
      ${laterDirectoryHtml(directoryByPerson.get(person.id), citationsById)}
      ${laterClaimHtml((directoriesOnRecord || []).find((row) => row.person_id === person.id), citationsById)}
      ${cites.length ? `<dt>Sources</dt><dd><ol class="cites">${citationItems(cites)}</ol></dd>` : ''}
    </dl>
  </details>`;
}

/** The grade tally a manifest entry already carries, as chips. */
function gradeChips(grades) {
  return ['attested', 'inferred', 'reconstructed']
    .filter((g) => (grades || {})[g])
    .map((g) => `<span class="res-chip">${swatch(g)}${grades[g]} ${escapeHtml(g)}</span>`)
    .join('');
}

/**
 * One household, closed. The summary is the manifest's denormalised copy; the
 * body arrives on first open, from the record itself, which is authoritative.
 *
 * `data-file` and `data-loaded` are how the lazy read is driven, and `data-reach`
 * is the finding: a household with neither residence nor workplace attested
 * reaches no building sidecar, so before this section it appeared nowhere a
 * visitor could go.
 */
function householdSummary(entry, { orphanChip = true } = {}) {
  const reaches = Boolean(entry.lives_at || entry.works_at);
  const label = entry.id.replace(/^hh_/, '').replace(/_/g, ' ');
  return `<details class="lib res-hh" data-file="${escapeHtml(entry.file)}"
      data-id="${escapeHtml(entry.id)}" data-loaded="0"
      data-reach="${reaches ? 'building' : 'nowhere'}">
    <summary><span class="lib-title">${escapeHtml(label)}</span>
      <span class="res-role">${escapeHtml(words(entry.division))} division · ${
        entry.persons} ${entry.persons === 1 ? 'person' : 'people'}</span>
      <span class="res-chips">${gradeChips(entry.grades)}${
        entry.civic_mint
          ? '<span class="res-chip res-research">minted by the evidence consolidation</span>' : ''}${
        entry.census_1840_linked
          ? `<span class="res-chip res-research">${entry.census_1840_linked} bridged to an 1840 census household</span>` : ''}${
        reaches || !orphanChip
          ? '' : '<span class="res-chip res-orphan">on no building card</span>'}</span></summary>
    <div class="lib-body res-hh-body"><p class="legend-note">Loading…</p></div>
  </details>`;
}

/** The household record itself, rendered into an opened row. */
/**
 * Why a reconstructed person is in the town, on their own row (T-1171).
 *
 * The attribute tiers reach a card through `claimRow` because they sit on a value. A
 * RECONSTRUCTED PERSON has no value to hang the disclosure off — the person IS the drawn
 * thing — so the same disclosure is printed about them: the stage of the programme that
 * wrote them, the model row it drew from, the seed a reader can retype to redraw them and
 * the evidence that would retire them. `basisHtml` takes the person record itself, which
 * carries `basis`, `seed` and `replaceable_by` in exactly the shape it reads.
 *
 * A drawn person shipped to a browser looking like a found one is the misrepresentation
 * this whole layer is against; a drawn person wearing the reconstructed swatch and opening
 * on their own seed is the opposite.
 */
function reconstructedHtml(person) {
  const rc = person && person.reconstruction;
  if (!rc || typeof rc !== 'object') return '';
  return `<dt>Why this person is in the town</dt><dd>${swatch('reconstructed')}Nobody a source
    names. Drawn by the <code>${escapeHtml(String(rc.stage || ''))}</code> stage of the 1835
    resident reconstruction programme${rc.ticket ? ` (${escapeHtml(String(rc.ticket))})` : ''}${
    rc.community ? `, named from the ${escapeHtml(words(rc.community))} pool` : ''}.${
    rc.review_required ? ' This reconstruction carries a standing review.' : ''}
    ${basisHtml(person)}</dd>`;
}

/**
 * The household block the modelled-families stage writes: what size the 1840 histogram
 * drew this house at, how much of it is kin, and what the stage deliberately did not seat.
 */
function modelledFamilyHtml(block) {
  if (!block || typeof block !== 'object') return '';
  return `<dt>The family the household model drew</dt><dd>${swatch('reconstructed')}A
    ${escapeHtml(words(block.household_type))} of ${escapeHtml(String(block.size_drawn))},
    drawn at the head's own size band from the 1840 city's household histogram;
    ${escapeHtml(String(block.kin_seated))} of them are seated here as kin.
    <br><span class="res-why">Drawn by stage <code>${escapeHtml(String(block.stage))}</code>
    of the 1835 resident reconstruction programme, ${escapeHtml(String(block.ticket))}.
    ${escapeHtml(String(block.note || ''))}${
    block.seed ? ` Redrawn with the seed <code>${escapeHtml(String(block.seed))}</code>.` : ''}
    </span></dd>`;
}

export function householdHtml(hh, citationsById, researchByPerson, directoryByPerson, ladderRules,
  agencies = null, withheldByPerson = new Map(), seatingByPerson = new Map(), coverage = null) {
  // T-0632's block on the record: `directories.note` states what a later volume is
  // worth and `directories.sources` names every one that met this household.
  const onRecord = hh.directories || {};
  const persons = Array.isArray(hh.persons) ? hh.persons : [];
  const party = hh.party_size_on_arrival || null;
  return `<dl class="lib-body res-fields">
      ${claimRow('Came to Chicago', (hh.arrival || {}).value, hh.arrival, citationsById)}
      ${row('How exact that year is', words((hh.arrival || {}).precision))}
      ${claimRow('The year they are carried at', (hh.arrival_year || {}).value,
        hh.arrival_year, citationsById)}
      ${claimRow('In a party of', party && party.value, party, citationsById)}
      ${claimRow('Came from', (hh.origin || {}).value, hh.origin, citationsById)}
      ${claimRow('Why they came', (hh.reason_for_coming || {}).value,
        hh.reason_for_coming, citationsById)}
      ${claimRow('Lived at', (hh.lives_at || {}).value, hh.lives_at, citationsById)}
      ${claimRow('Worked at', (hh.works_at || {}).value, hh.works_at, citationsById)}
      ${claimRow('Here on 1 July 1835', (hh.present_on_scene_date || {}).value,
        hh.present_on_scene_date, citationsById)}
      ${presenceLegRow(hh, citationsById)}
      ${associationsHtml(hh.associated_with, citationsById,
        'Where this household was, and when')}
      ${kinRows(hh, citationsById)}
      ${modelledFamilyHtml(hh.modelled_family)}
      ${hh.touches_removal
        ? `<dt>Touches the removal of 1835</dt><dd>Yes — read the standing constraint in
           <code>AGENTS.md</code>. This record is published as research; nothing about the
           removal is depicted or staged in the scene.</dd>` : ''}
      ${hh.surname_collision
        ? `<dt>Another card holds this family name</dt><dd>${
            escapeHtml(hh.surname_collision.refusal)} — ${
            escapeHtml((hh.surname_collision.holds_the_surname || []).join('; '))}.
           Nothing is retired: ${escapeHtml(hh.surname_collision.ruling)}.
           ${escapeHtml(hh.surname_collision.note)}</dd>` : ''}
      ${hh.research_note
        ? `<dt>What this record is worth</dt><dd>${escapeHtml(hh.research_note)}</dd>` : ''}
    </dl>
    ${onRecord.note ? `<p class="res-why">${escapeHtml(onRecord.note)} Volumes cited on this record: ${
        escapeHtml((onRecord.sources || []).join(', '))}.</p>` : ''}
    ${agencySectionHtml(agencies, 'household_id', hh.id, escapeHtml)}
    <div class="res-people">${persons.map((p) => personHtml(p, citationsById, researchByPerson, directoryByPerson, onRecord.people, ladderRules,
      withheldByPerson, hh.old_settler_deaths, seatingByPerson, coverage)).join('')}</div>`;
}

/**
 * The researched-and-not-resident list — the exclusions-style half.
 *
 * Its own manifest doc calls it "as load-bearing as the households" and it
 * reached nobody at all: three kinds of finding, ten people, including one this
 * project believes was here and cannot cite, *"recorded so that the gap is
 * visible rather than quietly filled."* That is this project's whole argument
 * about evidence, and it was in a file nothing opened.
 */
function notResidentHtml(entries, citationsById) {
  const body = entries.map((e) => {
    const cites = (e.sources || []).map((id) => citationsById.get(id)).filter(Boolean);
    return `<details class="lib res-nr">
      <summary><span class="lib-title">${escapeHtml(e.name || e.id)}</span>
        <span class="res-role">${escapeHtml(words(e.category))}</span></summary>
      <dl class="lib-body">
        ${row('Why not a household here', e.reason)}
        ${e.note ? `<dt>The reasoning</dt><dd>${escapeHtml(e.note)}</dd>` : ''}
        ${cites.length ? `<dt>Sources</dt><dd><ol class="cites">${citationItems(cites)}</ol></dd>` : ''}
      </dl>
    </details>`;
  }).join('');
  return `<details class="lib res-nr-group">
    <summary><span class="lib-title">Researched, and not a resident of this town</span>
      <span class="res-role">${entries.length} people</span></summary>
    <div class="lib-body">
      <p class="legend-note">Three different findings share this list: someone who arrived
        after 1 July 1835, someone the sources place at Chicago but not as a household of it,
        and someone this project believes was here and <b>cannot cite</b>. The third kind is
        recorded so the gap stays visible instead of being quietly filled, which is the same
        rule the excluded buildings follow.</p>
      ${body}
    </div>
  </details>`;
}

/**
 * The letter-list cohort, held together in one group (T-0379).
 *
 * The owner ruled on 30 August 2026 that every name the post office's lists of
 * uncalled-for letters yields, and the mint's refusals admit, joins the town. That
 * took it from a couple of hundred people to most of a thousand and made roughly
 * three quarters of them a name on a list and nothing else — which is a change to
 * what a visitor is looking at, not only to what the data holds, and the ruling
 * said so in as many words: *if that reads as a wall of undifferentiated people,
 * the ruling has been implemented badly, not chosen badly.*
 *
 * So they do not sit interleaved with the town's evidenced households. They are one
 * closed disclosure that says what they are and how many, and the list above it is
 * the town as the rest of the corpus documents it — the same records, in the same
 * order, at the same length it was before the ruling. Opening this group is a
 * deliberate act, and the rows inside it behave exactly like every other row.
 *
 * The `on no building card` chip is dropped inside here on purpose. On an evidenced
 * household it is a FINDING — a record this project could not attach to a building.
 * On 727 rows that by construction have no address it is wallpaper, and the group's
 * own summary says the same thing once, where it means something.
 */
function letterListGroupHtml(entries, persons) {
  if (!entries.length) return '';
  const share = persons ? Math.round((entries.length / persons) * 100) : 0;
  return `<details class="lib res-ll-group">
    <summary><span class="lib-title">Known only from the post office's letter lists</span>
      <span class="res-role">${entries.length} ${entries.length === 1 ? 'person' : 'people'}
        · about ${share}% of this town</span></summary>
    <div class="lib-body">
      <p class="legend-note">Each of these is a name the Chicago post office printed in a
        list of letters nobody had called for. That establishes one thing: a correspondent
        believed a person of that name was reachable at Chicago on that date. It does
        <b>not</b> establish that they lived here, kept a trade here, or were here on
        1 July 1835 — and the office served the country around the town as well as the town.
        It is the weakest evidence this project accepts for a resident, and it is admitted
        by an owner's ruling of 30 August 2026 rather than by the sources getting better.
        Every row carries the date of the return that printed it; none of them has a
        building, a household or a trade, because a letter list gives none.</p>
      ${entries.map((entry) => householdSummary(entry, { orphanChip: false })).join('')}
    </div>
  </details>`;
}

/** The manifest's closed sets, shown rather than paraphrased. */
function vocabularyHtml(vocab) {
  const sets = [
    ['How much of a person is reconstructed', vocab.grades],
    ['Here on the scene date', vocab.presence],
    ['Divisions of the town', vocab.divisions],
    ['How exact an arrival year is', vocab.arrival_precision],
    ['Places in a household', vocab.relationships],
    // T-0597. A place in a household and a tie between two households are
    // different questions, so they are two sets: `relationships` stops at the
    // household's edge and `kin_relations` is what may cross it. Shown for the
    // same reason every other set here is — the degrees are the point, and a
    // reader who cannot see that `half_brother` and `brother` are both in the
    // set cannot see that the dataset keeps them apart.
    ['Ties between two households', vocab.kin_relations],
    // Shown because `sex` is shown. The census of T-0021 found this set reaching
    // nothing while the value it governs was on every person's card — five closed
    // sets listed and the sixth withheld, which reads as a set the dataset does
    // not have rather than one nobody printed.
    ['Sex, as the records give it', vocab.sexes],
    ['Trades', vocab.occupations],
  ];
  const rows = sets
    .filter(([, list]) => Array.isArray(list) && list.length)
    .map(([label, list]) => `<dt>${escapeHtml(label)}</dt>
      <dd>${list.map((v) => `<code>${escapeHtml(words(v))}</code>`).join(' · ')}</dd>`)
    .join('');
  return `<details class="lib res-vocab">
    <summary><span class="lib-title">The words on these cards, and they are a closed set</span></summary>
    <dl class="lib-body">
      <p class="legend-note">Two of these are different questions and the dataset refuses to
        merge them. <b>How much of a person is reconstructed</b> grades the PERSON; the
        swatch beside any single figure grades that one attribute's evidence. A documented
        man can have a conjectural arrival year, and this town has several.</p>
      ${rows}
    </dl>
  </details>`;
}

/**
 * Fetch the residents layer and render it into `mount`.
 *
 * Failure is reported, never papered over, the same way the liberties, the
 * exclusions and the wildlife do it: a missing manifest leaves a line saying so
 * and pushes the reason onto the loader's shared problem list, and a household
 * whose own file 404s says so inside its own row rather than taking the section
 * down.
 *
 * @param {object} o
 * @param {HTMLElement|null} o.mount        where the households go
 * @param {HTMLElement|null} [o.noteMount]  where the count sentence goes
 * @param {string} o.sceneId                which scene's citation join to read
 * @param {URL} o.dataBase                  where data/ lives
 * @param {string[]} [o.problems]           the shared collector
 */
export async function mountResidents({ mount, noteMount = null, sceneId, dataBase, problems = [] }) {
  const fail = (message) => {
    problems.push(`residents: ${message} — the town's people are not shown`);
    if (mount) {
      mount.innerHTML = '<p class="legend-note">The household records could not be loaded. '
        + 'They are committed at <code>data/residents/</code>.</p>';
      mount.removeAttribute('aria-busy');
    }
    if (noteMount) {
      noteMount.textContent = '';
      noteMount.removeAttribute('aria-busy');
    }
    return { households: 0, persons: 0, offCard: 0, error: message };
  };

  const getJson = async (rel) => {
    const res = await fetch(new URL(rel, dataBase), { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${rel}: ${res.status} ${res.statusText}`);
    return res.json();
  };

  // The agency relation. A man who held one is named on his own town card, and a
  // failure here leaves the block off rather than the card — `loadAgencies` returns
  // null and `agencySectionHtml` renders nothing from a null.
  const agencies = await loadAgencies({ dataBase, problems });

  let index;
  try {
    index = await getJson('residents/index.json');
  } catch (err) {
    return fail(String(err.message || err));
  }

  // The citation join. Its absence degrades the section to bare notes rather
  // than taking it down: a card without its sources is poorer, not wrong.
  const citationsById = new Map();
  try {
    const joined = await getJson(`sidecars/${sceneId}/residents_sources.json`);
    for (const [id, record] of Object.entries(joined.citations || {})) {
      citationsById.set(id, record);
    }
  } catch (err) {
    problems.push(`residents: ${err.message} — the household records are shown without their citations`);
  }

  // The deliberately separate review layer. A possible identity must not
  // become an asserted household fact merely because its biography is useful.
  const researchByPerson = new Map();
  let researchCounts = {};
  let researchEligible = 0;
  try {
    const pilot = await getJson('residents/research_pilot.json');
    researchCounts = pilot.counts || {};
    researchEligible = pilot.eligible_real_named_people || 0;
    for (const review of pilot.reviews || []) researchByPerson.set(review.person_id, review);
  } catch (err) {
    problems.push(`residents: ${err.message} — resident research reviews are not shown`);
  }

  // T-1233. The refusals — 204 candidate facts this project read and would not assert,
  // projected out of the 800 kB adjudication table by tools/spend_person_facts.py. Its
  // own loader, because it degrades the way every other join here does: a miss costs the
  // withheld block on a card and never the card.
  const withheldByPerson = new Map();
  try {
    const withheld = await getJson('residents/person_facts_withheld.json');
    for (const row of withheld.rows || []) {
      if (!withheldByPerson.has(row.person_id)) withheldByPerson.set(row.person_id, []);
      withheldByPerson.get(row.person_id).push(row);
    }
  } catch (err) {
    problems.push(`residents: ${err.message} — the withheld research facts are not shown`);
  }

  // The four directory crosswalks, joined on person_id (T-0632, replacing T-0569's
  // 1844-only layer). Beside the records as well as on them: the record carries the
  // later trade and street and cites the volume, and this layer carries the printed
  // lines, the match rule and the arithmetic the card has no room for. Its absence
  // costs the section this block and nothing else.
  // T-1433. WHERE A RECONSTRUCTED TRADE WAS FOLLOWED — the seats and the stated
  // absences `tools/seat_reconstructed_trades_1835.py` draws for the 524 residents this
  // project reconstructed with a trade and no attested workplace. Beside the layer and
  // not on the cards, because two thirds of those cards are the byte-compared output of
  // a reconstruction stage. Its own loader, degrading like every other join here: a miss
  // costs the block on a card and never the card.
  const seatingByPerson = new Map();
  try {
    const seating = await getJson('residents/reconstructed_seating.json');
    for (const row of seating.rows || []) seatingByPerson.set(row.person_id, row);
  } catch (err) {
    problems.push(`residents: ${err.message} — the reconstructed trade seatings are not shown`);
  }

  // T-1461. THE EMPLOYMENT COVERAGE ANSWER — one answer per person for all 3,243 of
  // them, where the two joins above between them reach 636. Loaded and degraded exactly
  // as the seating is: a miss costs the block on every card and never a card.
  let coverage = null;
  try {
    const found = await getJson('residents/employment_coverage.json');
    const byPerson = new Map();
    for (const row of found.rows || []) byPerson.set(row.person_id, row);
    const statuses = (found.vocabulary || {}).statuses || {};
    coverage = {
      byPerson,
      words: (found.vocabulary || {}).reasons || {},
      placed: new Set(Object.entries(statuses)
        .filter(([, v]) => v && v.places_them_at_work).map(([k]) => k)),
      counts: found.counts || {},
      model: found.against_the_town_model || {},
    };
  } catch (err) {
    problems.push(`residents: ${err.message} — the employment coverage answers are not shown`);
  }

  const directoryByPerson = new Map();
  let directoryCounts = {};
  let directoryVolumes = [];
  try {
    const found = await getJson('residents/directories.json');
    directoryCounts = found.counts || {};
    directoryVolumes = found.volumes || [];
    for (const row of found.people || []) {
      directoryByPerson.set(row.person_id, { ...row, standard: found.standard });
    }
  } catch (err) {
    problems.push(`residents: ${err.message} — the directory findings are not shown`);
  }

  const vocab = index.vocabulary || {};
  const entries = Array.isArray(index.households) ? [...index.households] : [];
  if (!entries.length) return fail('the manifest lists no household');
  entries.sort((a, b) => rank(vocab.divisions, a.division) - rank(vocab.divisions, b.division)
    || String(a.id).localeCompare(String(b.id)));

  const notResident = Array.isArray(index.researched_not_resident)
    ? index.researched_not_resident : [];
  const counts = index.counts || {};
  const persons = counts.persons ?? entries.reduce((n, e) => n + (e.persons || 0), 0);
  const offCard = entries.filter((e) => !e.lives_at && !e.works_at).length;
  const offCardPersons = entries
    .filter((e) => !e.lives_at && !e.works_at)
    .reduce((n, e) => n + (e.persons || 0), 0);
  // T-0379. The manifest says which rows are the letter-list cohort, so the split
  // is read from the data rather than from a mint tool's id prefix — and it is a
  // split rather than a sort because after the ruling those rows outnumber the
  // town's evidenced households roughly three to one.
  const letterList = entries.filter((e) => e.letter_list_only);
  const evidenced = entries.filter((e) => !e.letter_list_only);
  const letterListOffCard = letterList.filter((e) => !e.lives_at && !e.works_at).length;

  if (noteMount) {
    // The layer's own grade tally, which the manifest has always carried and
    // nothing read (T-0021). "Every one of them graded" was true and told a
    // visitor nothing: the shape of this dataset is that most of its people are
    // hypotheses, and a sentence that does not say so is the wrong sentence.
    const byGrade = counts.by_grade || {};
    noteMount.textContent = `${entries.length} households and ${persons} people — `
      + `${byGrade.attested} named by a source, ${byGrade.inferred} real people whose `
      + `details are partly reconstructed, and ${byGrade.reconstructed} hypothesised to `
      + `fill a demonstrable need of the town. `
      + `${offCard} of the households are attached to no building in this scene — neither `
      + `where they lived nor where they worked is attested on 1 July 1835 — so ${offCardPersons} `
      + `people reached no card anywhere until this section existed. `
      + (counts.letter_list_only
        ? `${counts.letter_list_only} of the people here are known ONLY from the post `
          + `office's lists of uncalled-for letters, which is the weakest evidence this `
          + `layer carries and is marked as such on each of their cards. That is about `
          + `${Math.round((counts.letter_list_only / persons) * 100)} per cent of this `
          + `town: the owner ruled on 30 August 2026 that every such name the evidence `
          + `admits should be held, so they are listed together, below the households the `
          + `rest of the corpus documents, and which of these people are a name and `
          + `nothing else can be seen without opening anything. ` : '')
      + (counts.census_1840_linked
        // T-0491. Three people carry an identity bridge to a named head of household
        // in the 1840 census, and the bridge is an argument rather than a fact: it is
        // shown whole on the person's card, three confidences and all. The count is
        // here so that a reader can see how few of them there are before opening one.
        ? `${counts.census_1840_linked} of these people are bridged to a named household `
          + `in the 1840 census, five years after this scene — later evidence, shown with `
          + `its reasoning and never read back onto 1835. ` : '')
      + (counts.civic_mint
        // T-0668. The consolidation of 3 September 2026 read seven source domains and
        // minted this many of the people below — they are here because a list the town
        // made of its own inhabitants names them, and nothing the project already
        // carried matched. The number is here so a reader can see how much of this
        // town is that one pass before opening a single card.
        ? `${counts.civic_mint} of these people were minted by the evidence `
          + `consolidation, which graded every one of them on a named rung of a ratified `
          + `ladder and wrote the appearances it spent onto their cards — the quoted `
          + `reading, the list, the page and the date each line describes. `
          + `That is ${Math.round((counts.civic_mint / persons) * 100)} per cent of the `
          + `people here, and the rung and its lines are on each of their cards so that `
          + `the grade can be disagreed with rather than taken. ` : '')
      + (researchByPerson.size
        ? `${researchByPerson.size} real named people (${Math.round((researchByPerson.size / researchEligible) * 100)}% of the eligible research population) received a dated identity review: `
          + `${researchCounts.corroborated_enrichment || 0} corroborated findings, `
          + `${researchCounts.candidate_identity || 0} candidate identities kept unmerged, and `
          + `${researchCounts.no_corroboration || 0} searches with no safe match. ` : '')
      + (directoryByPerson.size
        // T-0632. The earliest Chicago directory is of 1839 and this town is of 1835,
        // so the sentence leads with the gap rather than with the number: what these
        // people gain is corroboration, a line to read and — where the volume prints
        // one — a trade or a street OF ITS OWN YEAR, never a date, a trade or a street
        // in 1835.
        ? `${directoryByPerson.size} of them are met by a name in one of the `
          + `${directoryVolumes.length} Chicago directories read here, of 1839, 1843 and `
          + `1844 — ${directoryCounts.people_met_by_more_than_one_volume || 0} in more `
          + `than one. ${directoryCounts.carrying_an_occupation || 0} carry a trade the `
          + `1835 record never had and ${directoryCounts.carrying_an_address || 0} an `
          + `address, each written as its own year's and read back onto nobody; `
          + `${directoryCounts.split_refused_trades || 0} printed line(s) name a firm or `
          + `a door where the trade would go and ${
              directoryCounts.split_refused_addresses || 0} give an address that is only a `
          + `ditto, so those fields do not cross and the line is quoted instead. ` : '')
      + (coverage && coverage.counts && coverage.counts.people
        // T-1461. THE EMPLOYMENT COVER. Every person in the layer now carries one
        // employment answer, and the number worth putting in front of a reader is not
        // how many are at work but how many are NOT ACCOUNTED FOR — because until this
        // pass ran, a card nobody had asked the question of and a card that had been
        // asked and answered no were the same blank. The sentence leads with the cover
        // and follows with what it is worth against the town model's own band.
        ? `Every one of the ${coverage.counts.people} people here now carries one `
          + `employment answer and none of them carries none: `
          + `${coverage.counts.placed_at_work} are placed at work — at a house a source `
          + `names, at a seat this project drew, or on their own account — and the rest `
          + `carry a stated reason they are not, in the words of the rule that decided `
          + `it. ${coverage.counts.working_age_with_no_trade_recorded} of those reasons `
          + `are the same one: no source records a trade for them and no stage has given `
          + `them one, which is a statement about the evidence rather than about the `
          + `person. The town model puts ${coverage.model?.employed_persons?.model_low} `
          + `to ${coverage.model?.employed_persons?.model_high} people of this town in `
          + `work, so the cover falls inside the band — which is where the argument `
          + `starts and not where it finishes. ` : '')
      + `Nobody is drawn: this is the research, not a population.`;
    noteMount.removeAttribute('aria-busy');
  }

  if (mount) {
    mount.innerHTML = vocabularyHtml(vocab)
      + notResidentHtml(notResident, citationsById)
      + evidenced.map((entry) => householdSummary(entry)).join('')
      + letterListGroupHtml(letterList, persons);
    mount.removeAttribute('aria-busy');

    // The lazy read. A row's body arrives the first time it is opened, from the
    // household record rather than from the manifest's summary of it — the
    // manifest is denormalised for the list and the record is authoritative for
    // everything else.
    mount.addEventListener('toggle', async (event) => {
      const el = event.target;
      if (!(el instanceof HTMLElement) || !el.classList.contains('res-hh')) return;
      if (!el.open || el.dataset.loaded === '1') return;
      el.dataset.loaded = '1';
      const body = el.querySelector('.res-hh-body');
      try {
        const hh = await getJson(`residents/${el.dataset.file}`);
        if (body) body.innerHTML = householdHtml(hh, citationsById, researchByPerson, directoryByPerson,
          vocab.ladder_rules, agencies, withheldByPerson, seatingByPerson, coverage);
      } catch (err) {
        el.dataset.loaded = '0';
        problems.push(`residents: ${err.message} — one household record is missing`);
        if (body) {
          body.innerHTML = `<p class="legend-note">This household's record could not be
            loaded. It is committed at <code>data/residents/${escapeHtml(el.dataset.file || '')}</code>.</p>`;
        }
      }
    }, true);
  }

  return {
    households: entries.length,
    persons,
    offCard,
    offCardPersons,
    // T-0379's two halves, separately, because the interesting assertion is not
    // the total: it is that the town's evidenced households did not move when
    // seven hundred letter-list names joined it, and that the cohort is held
    // apart where a visitor can see it.
    evidenced: evidenced.length,
    letterList: letterList.length,
    letterListOffCard,
    notResident: notResident.length,
    researchReviewed: researchByPerson.size,
    researchCounts,
    error: null,
  };
}

/**
 * The joins a household card needs, loaded once for a caller that is not this
 * section (the People directory, `people.js`).
 *
 * `mountResidents` above fetches the citation join, the identity reviews and the
 * directory crosswalks and keeps them in its own closure, because until the
 * directory existed it was the only thing that rendered a household record. The
 * directory renders the same record with the same `householdHtml`, and a card
 * that quoted a bare source id because its caller skipped the join would be the
 * defect `compile_residents_sources` exists to prevent. So the four reads are
 * repeated here as ONE function returning the shapes `householdHtml` takes, and
 * cached per scene so the two sections opening the same town cost one set of
 * fetches between them. `mountResidents` is left as it was — the read census in
 * `tools/measure_layer_reads.py` scans this file's text — and a failure here
 * degrades exactly the way it does there: a missing join is reported and the
 * card renders without that block, never not at all.
 *
 * @param {URL} dataBase   where data/ lives
 * @param {string} sceneId which scene's citation join to read
 * @param {string[]} [problems] the shared collector
 * @returns {Promise<{citationsById: Map, researchByPerson: Map, directoryByPerson: Map,
 *   withheldByPerson: Map, ladderRules: object[], agencies: object|null,
 *   seatByHousehold: Map, getJson: (rel: string) => Promise<any>}>}
 */
const residentJoinCache = new Map();
export function loadResidentJoins(dataBase, sceneId, problems = []) {
  const key = `${sceneId}@${String(dataBase)}`;
  if (residentJoinCache.has(key)) return residentJoinCache.get(key);
  const getJson = async (rel) => {
    const res = await fetch(new URL(rel, dataBase), { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${rel}: ${res.status} ${res.statusText}`);
    return res.json();
  };
  const promise = (async () => {
    const citationsById = new Map();
    const researchByPerson = new Map();
    const directoryByPerson = new Map();
    const withheldByPerson = new Map();
    let ladderRules = [];
    const seatByHousehold = new Map();
  // …and the same book's firms, keyed by the REGISTER id the business index
  // crosswalks to (`register_id`), which is the id the address book files them
  // under. T-1493: the business card reads this the way the person card does.
  const seatByBusiness = new Map();
    const [joined, pilot, found, index, agencies, withheld, addressBook] = await Promise.all([
      getJson(`sidecars/${sceneId}/residents_sources.json`).catch((err) => {
        problems.push(`people: ${err.message} — person cards are shown without their citations`);
        return null;
      }),
      getJson('residents/research_pilot.json').catch((err) => {
        problems.push(`people: ${err.message} — resident research reviews are not shown on person cards`);
        return null;
      }),
      getJson('residents/directories.json').catch((err) => {
        problems.push(`people: ${err.message} — the directory findings are not shown on person cards`);
        return null;
      }),
      getJson('residents/index.json').catch((err) => {
        problems.push(`people: ${err.message} — the grading ladder's text is not shown on person cards`);
        return null;
      }),
      // The agency relation. Its own loader, because it degrades the same way and
      // pushes its own problem; a null here costs the block and not the card.
      loadAgencies({ dataBase, problems }),
      // T-1233's refusals, the same way.
      getJson('residents/person_facts_withheld.json').catch((err) => {
        problems.push(`people: ${err.message} — the withheld research facts are not shown`);
        return null;
      }),
      // T-1491. The address book: one row per household and per firm, at the rung its
      // evidence reaches. A card WITHOUT it falls back to "No known address", which is
      // the sentence this join exists to replace — so its absence costs the sentence
      // and never the card.
      getJson('reconstruction/1835_address_book.json').catch((err) => {
        problems.push(`people: ${err.message} — the address book's seats are not shown on person cards`);
        return null;
      }),
    ]);
    for (const [id, record] of Object.entries(joined?.citations || {})) citationsById.set(id, record);
    for (const review of pilot?.reviews || []) researchByPerson.set(review.person_id, review);
    for (const row of withheld?.rows || []) {
      if (!withheldByPerson.has(row.person_id)) withheldByPerson.set(row.person_id, []);
      withheldByPerson.get(row.person_id).push(row);
    }
    for (const row of found?.people || []) {
      directoryByPerson.set(row.person_id, { ...row, standard: found.standard });
    }
    ladderRules = index?.vocabulary?.ladder_rules || [];
    for (const row of addressBook?.rows || []) {
      if (row.kind === 'household') seatByHousehold.set(row.id, row);
      else if (row.kind === 'business') seatByBusiness.set(row.id, row);
    }
    return { citationsById, researchByPerson, directoryByPerson, withheldByPerson, ladderRules,
      agencies, seatByHousehold, seatByBusiness, getJson };
  })();
  residentJoinCache.set(key, promise);
  return promise;
}
