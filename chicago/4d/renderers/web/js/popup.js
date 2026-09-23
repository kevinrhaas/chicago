/**
 * popup.js — pick a building, read its provenance.
 *
 * This is the other half of the confidence view, and the reason the project
 * exists: the tint you see and the citation you can quote come from the SAME
 * sidecar record, so they cannot drift apart. If the shader says amber, the
 * table says `reconstructed`, and the note underneath says why.
 *
 * The card reads top-down like a label and bottom-up like a catalogue. First
 * what the building IS: title, other names, its kind, where it stood, the flags
 * that qualify the whole record, the phase's own account (or a lead composed
 * strictly from record fields when none was written), and a facts grid —
 * standing, use, fabric, roof, address, ground, who was here, keepers — each
 * with a quiet dot for its grade. Then the households the residents layer
 * places here. Then, behind three tabs: EVIDENCE (what we included and where
 * it came from, where it stood, whether it was here, whether it was this shape,
 * every attribute with its chip and reasoning, the citations), WHAT WE MADE UP
 * (the liberties taken with THIS building and any tracked open question) and
 * RECORD (the record's own account, the production reference, the dossier
 * link). The dots and the chips grade the same claims: the dot is the label's
 * summary, the chip in the table is the claim itself, and the smoke counts only
 * the chips (`css/card.css` § facts explains why there is never a chip up top).
 *
 * The open question is the newest section and it qualifies the two claims above
 * it rather than adding a third. A chip says how sure we are; it cannot say that
 * the uncertainty is a live dispute between two sources, that the grade is being
 * held down deliberately until evidence arrives, and what would change if it did.
 * That was readable in the Evidence panel — whose entry for the standing one says
 * in as many words that "the provenance card shows it" — and not on the building
 * the panel is talking about. Same gap the liberties had, closed the same way.
 *
 * The shape is the newest of those and was the largest silence. The footprint is
 * the biggest single claim a visitor stands in front of, six of the eight in
 * this dataset are placeholders that say so in their first line, and the card
 * showed no chip, no source and no reasoning for any of them — while the
 * confidence tint had been narrowed to stop carrying dimensional uncertainty on
 * the stated understanding that the card would carry it instead.
 *
 * "Whether it was here at all" is the newest of those and was the oldest gap.
 * This file has read `documented_range` since it was written and the sidecar
 * compiler never wrote the field, so the line never rendered once: the claim the
 * entire scene rests on — that this building stood in Chicago on 1 July 1835 —
 * was the one claim on the card with no chip, no source and no reasoning, while
 * a roof pitch had all three. The same was half-true of the position, whose
 * argument is often the longest thing in the record and reached the card as a
 * bare chip. Both now render through the attribute table's own row renderer,
 * because a card that qualified its load-bearing claims differently from its
 * details is how the two drift.
 *
 * The liberties section is the answer to a gap this card had until now. An
 * attribute chip tells a visitor how sure we are of a value we recorded; it
 * cannot tell them about the decisions that belong to no attribute — that the
 * Green Tree's footprint was reasoned out of a room module and its side
 * additions deliberately left off, that three Wolf Point buildings were placed
 * from bank geometry because no corner survives. Those were readable in the
 * Evidence panel as one undifferentiated list of eighteen. Now the ones that
 * constrain the building you are looking at are on the building you are looking
 * at, which is where a visitor would think to ask.
 *
 * The attribute table now answers a second question beside "how sure are you":
 * whether you are looking at the thing at all. An attribute its archetype never
 * reads is marked — `not built` where the model contains nothing of it, `not
 * modelled from this` where a fixed default stands in its place — because a
 * `attested` chip over an unbuilt feature is true about the evidence and false
 * about the view, and the view is what a visitor is standing in.
 *
 * The record's own account is the newest section and the last of the compiled
 * fields that reached no visitor. Every structure record carries a
 * `research_note` written for a reader — what it actually asserts, which sources
 * disagree, what was decided and why, where the record is weakest — and it was
 * compiled into every sidecar and shown nowhere. That is not the same fault as
 * the two before it: nothing was broken, the field simply had no surface. It is
 * shown verbatim, because a note about how far the evidence goes is the last
 * thing on this card that should be summarised by a program.
 *
 * Nothing here invents a display value. An attribute with no note shows no note.
 * A citation with no archived copy says so, because the archived copy is part of
 * whether a claim can be re-read at all. And a building with no recorded
 * liberties says exactly that — that none were written down, which is not the
 * same claim as none having been taken.
 */

import { citationItems, escapeHtml } from './citations.js';
import { libertiesFor, libertyEntryHtml } from './liberties.js';
// The Evidence panel's own open-question entry, rendered here for the building
// being inspected. Shared for the liberties' reason: the panel's entry for the
// Western Hotel says in as many words that "the provenance card shows it", and
// two renderers would let the two surfaces describe one uncertainty differently.
import { openQuestionsFor, uncertaintyEntryHtml } from './exclusions.js';
// What the mesh does with a value its archetype never reads — `not built`, `not
// modelled from this`. Shared with the Evidence panel's ground section, which
// says the same thing about the terrain: one wording in one module, for the
// reason the liberties have one entry renderer. The argument for the mark, and
// for the two states that deliberately get none, is in that file.
import { geometryMark } from './geometry.js';
// The title a visitor reads, which since T-0076 is not the production identity the
// generators number a roof by. Shared with the Go-to menu and the liberties list for
// the reason every other renderer thing here is shared: three surfaces naming one
// building three ways is how a town becomes a spreadsheet.
import { displayName } from './display-name.js';
// The agency relation, rendered by the module that owns it so this card and the
// household browser cannot describe one holding two ways (T-1041).
import { agencySectionHtml } from './agencies.js';

const CONF_ORDER = { attested: 0, inferred: 1, reconstructed: 2 };

function prettyName(key) {
  return key.replace(/_/g, ' ').replace(/\bm\b/, '(m)');
}

function prettyValue(v) {
  if (v === true) return 'yes';
  if (v === false) return 'no';
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') return String(v);
  return String(v).replace(/_/g, ' ');
}

function chip(confidence) {
  const c = confidence || 'reconstructed';
  return `<span class="conf conf-${escapeHtml(c)}">${escapeHtml(c)}</span>`;
}

function sourceList(sources) {
  if (!Array.isArray(sources) || !sources.length) return '';
  return `<span class="attr-note">sources: ${sources.map(escapeHtml).join(', ')}</span>`;
}

/**
 * The reasoning, folded away behind `why`.
 *
 * Split out of the attribute row because the phase-level claims need exactly the
 * same affordance and a second implementation of it would drift — the same
 * argument that put the Evidence panel and this card on one liberty renderer.
 * An empty note renders nothing at all: a `why` button that opens on silence
 * teaches a visitor that the reasoning is missing everywhere.
 */
function noteToggle(note) {
  if (!note) return '';
  return `<span class="attr-note" data-note hidden>${escapeHtml(note)}</span>
    <button class="attr-toggle" type="button" data-toggle-note>why</button>`;
}

/** Chip, sources and reasoning — everything that qualifies a value. */
function evidence(claim) {
  return `${chip(claim.confidence)}${geometryMark(claim.geometry)}
    ${sourceList(claim.sources)}${noteToggle(claim.note)}`;
}

function attributeRows(attributes) {
  const entries = Object.entries(attributes || {});
  entries.sort((a, b) => (CONF_ORDER[a[1].confidence] ?? 3) - (CONF_ORDER[b[1].confidence] ?? 3)
    || a[0].localeCompare(b[0]));

  return entries.map(([key, attr]) => claimRow(prettyName(key), prettyValue(attr.value), attr))
    .join('');
}

/** One row of the evidence table. Used by the attribute table and by the
 *  phase-level claims above it, so the two cannot be styled or qualified
 *  differently for reasons nobody chose.
 *
 *  A `null` value renders no value cell at all, which is not the same as `—`.
 *  One claim here has no printable value and inventing one would be the exact
 *  fault this card exists to report — see `shapeSection`. The rest of the row is
 *  unchanged, because how sure we are and why is the whole of what a chip, a
 *  source list and a `why` are for. */
function claimRow(label, value, claim) {
  const val = value === null ? '' : `<span class="val">${escapeHtml(value)}</span>`;
  return `<tr>
    <th scope="row">${escapeHtml(label)}</th>
    <td>${val}${evidence(claim)}</td>
  </tr>`;
}

/**
 * Who was here.
 *
 * `data/residents/` reconstructs the town's population as a dataset and draws
 * nobody (docs/LIBERTIES.md L1 stands: v1 ships no human figures). Until this
 * section existed the layer reached no visitor at all — ninety-six researched
 * Chicagoans lived in a JSON file the renderer never fetched, which is
 * indistinguishable, from the street, from not having done the work.
 *
 * A person carries a GRADE, which is a different axis from an attribute's
 * confidence and must not be read as one: `attested` means a source names this
 * person, `inferred` means a real named person whose details are partly
 * reconstructed, `reconstructed` means a hypothesised resident filling a demonstrable
 * need of the town — a claim about a ratio, not about anybody. The chip is
 * therefore rendered in its own class, and an inferred household on a building
 * this project RAISED for it says so in the same breath, because otherwise the
 * card reads as evidence that somebody lived here.
 */
function gradeChip(grade) {
  const g = grade || 'reconstructed';
  return `<span class="grade grade-${escapeHtml(g)}">${escapeHtml(g)}</span>`;
}

/**
 * How many people this house could sleep — the one fact a lodging place is FOR.
 *
 * T-1370. The town model has always carried a bed bracket for the whole town and
 * has always said, in as many words, that it "seats nobody in any lodging place
 * and gives no boarding house a capacity of its own". So a visitor could open the
 * Green Tree Tavern and read its footprint, its storeys, its roof pitch and its
 * finish, and not the number that makes it a tavern rather than a large house.
 *
 * TWO NUMBERS, NOT ONE, and the gap between them is the claim. A lodging place in
 * a boom-year lake port did not have a capacity; it had an ordinary night and a
 * night when the boats had landed, and the difference between nine and thirty-five
 * is the whole of what the sources actually describe — "full meant three in a bed
 * sometimes, with the floor covered besides". A single averaged figure would lose
 * exactly the thing the evidence is about.
 *
 * THE GRADE IS THE CAPACITY'S OWN, not the building's. The Green Tree is an
 * attested tavern whose bed count is apportioned from an inferred outline, and
 * printing the building's grade beside the beds would let a visitor read an
 * arithmetic share as something a source said. It is the weakest claim under the
 * number, which is the rule the rest of this card already follows.
 *
 * AND IT SAYS WHO IS IN THEM (T-1406). This card used to end on the sentence
 * "Nobody is seated in these beds yet", which was true for one day. T-1371 then
 * slept 122 people in these fifteen houses and the sentence stayed, so the
 * Tremont's twelve beds held twelve people and its card said the house was empty
 * — the one failure mode this section was built to avoid, arriving from the other
 * direction. The occupancy line is compiled from that stage's own ledger and
 * keeps the four ways into a bed apart, because a person the sources house here,
 * a person seated here for want of a roof, and a lodger drawn for an empty bed
 * are three different claims and one number would read as a census of all three.
 *
 * AN EMPTY BED IS PRINTED WITH ITS REASON OR NOT AT ALL. The two houses standing
 * short are short because no committed record gives their division and a drawn
 * lodger has to come out of a division's bucket; the ledger's refusal is shown
 * verbatim. "5 beds empty" alone would read as a finding about 1835.
 *
 * A row with no beds at all — the Lake House, still going up — prints its reason
 * instead of its number, because a lodging place silent about its capacity reads
 * as an oversight rather than as a finding.
 */
function lodgingSection(s) {
  const l = s.lodging;
  if (!l) return '';

  const body = l.beds_ordinary === null
    ? `<p class="lodge-basis">${escapeHtml(l.note)}</p>`
    : `<p class="lodge-beds">
         <span class="lodge-n">${l.beds_ordinary}</span>
         <span class="lodge-when">on an ordinary night</span>
         <span class="lodge-sep">·</span>
         <span class="lodge-n">${l.beds_crowded}</span>
         <span class="lodge-when">when full</span>
         ${chip(l.confidence)}
       </p>
       <p class="lodge-basis">${escapeHtml(l.note)}${
         l.clamped_at_1840_maximum
           ? ` Held at ${l.ceiling}, the largest household the 1840 enumerator recorded here.`
           : ''}</p>
       ${noteToggle(l.replaceable_by)}`;

  const o = l.occupancy;
  const occupancy = !o ? '' : `
    <p class="lodge-who">
      <span class="lodge-n">${o.people}</span>
      <span class="lodge-when">slept here on this card</span>
      ${o.empty ? `<span class="lodge-sep">·</span>
        <span class="lodge-n lodge-short">${o.empty}</span>
        <span class="lodge-when">${o.empty === 1 ? 'bed' : 'beds'} empty</span>` : ''}
    </p>
    <p class="lodge-basis">${escapeHtml(o.statement)}</p>
    ${o.empty_note ? `<p class="lodge-empty">${escapeHtml(o.empty_note)}</p>` : ''}
    ${o.keeper_persons
      ? `<p class="lodge-basis">The keeper's own household stands at ${o.keeper_persons}
           ${o.keeper_persons === 1 ? 'person' : 'people'}.${
             o.keeper_owed ? ` ${escapeHtml(o.keeper_owed)}` : ''}</p>`
      : (o.keeper_owed ? `<p class="lodge-empty">${escapeHtml(o.keeper_owed)}</p>` : '')}`;

  return `<section class="pop-sec pop-lodging">
    <h3>How many slept here</h3>
    ${body}
    ${occupancy}
  </section>`;
}

function residentsSection(s) {
  const households = Array.isArray(s.residents) ? s.residents : [];
  if (!households.length) return '';

  const blocks = households.map((h) => {
    // `person`, not `p`: this module binds `p` to the sidecar's `placement`, and
    // the sidecar-contract scanner reads a bare `p.name` here as `placement.name`.
    const people = h.persons.map((person) => `<li>
        <span class="res-name">${escapeHtml(person.name)}</span>
        <span class="res-role">${escapeHtml(person.occupation ? person.occupation.replace(/_/g, ' ') : '')}${
          person.relationship && person.relationship !== 'head'
            ? ` · ${escapeHtml(person.relationship)}` : ''}</span>
        ${gradeChip(person.grade)}
        ${noteToggle(person.note)}
      </li>`).join('');
    const basis = h.basis ? `<p class="res-basis">${escapeHtml(h.basis)}</p>` : '';
    return `<div class="res-hh">
      <p class="res-head"><strong>${escapeHtml(h.name)}</strong> — ${escapeHtml(h.relation)}
        ${sourceList(h.sources)}${noteToggle(h.why)}</p>
      ${basis}
      <ul class="res-people">${people}</ul>
    </div>`;
  }).join('');

  return `<section class="pop-sec pop-residents">
    <h3>Who was here</h3>
    <p class="res-lead">From <code>data/residents/</code>. Nobody is drawn: this is the
      population as a dataset, and each person carries how much of them is reconstructed.</p>
    ${blocks}
  </section>`;
}

/**
 * What did we include at each level, and where did it come from?
 *
 * The owner asked for this from a card on the dev preview, and the ask was
 * precise: *"when you say what we made up, say what we included in the
 * recreation, or what we included in the inferred building, or what we included
 * in the attested building."* Everything needed to answer was already on the
 * card and none of it was answered — a visitor could read nineteen rows, each
 * with its own chip, and still not be able to say which parts of the building in
 * front of them are evidence and which are ours. The parts were all there; the
 * summary a person reads FIRST was not.
 *
 * It is a partition, not a highlight reel. Every graded claim the card renders
 * below lands in exactly one row here — the presence claim, the position, the
 * outline and every attribute — so the counts add up to the card and a claim
 * cannot be quietly left out of the summary of itself. That is also what makes
 * it gateable: `smoke_renderer.mjs` recounts the chips off the RENDERED card and
 * requires the same three numbers, which is the only form of this section that
 * cannot drift from the card it describes.
 *
 * The three glosses are the Evidence panel's own words, trimmed at a clause
 * boundary so each is a literal substring of the legend in `index.html` — the
 * liberties' rule, applied to prose that has no shared renderer to hold it. Two
 * surfaces defining `inferred` differently is exactly the drift K23a spent a run
 * cleaning up.
 *
 * WHAT THE SOURCES MEAN CHANGES WITH THE LEVEL, and printing one label over all
 * three would be the same category error the card's own history is made of. On
 * an `attested` claim a source is where the value came FROM. On a `reconstructed`
 * one it is what BOUNDED an invention — the record's own note says so in as many
 * words ("the spec is cited because the invention is bounded by it, which is what
 * makes it defensible rather than arbitrary") — and reading that as attribution
 * would turn the citation into evidence for a building nobody claims existed.
 *
 * An empty level says so rather than disappearing. A building with nothing
 * attested is the single most important thing this section can tell a visitor,
 * and a row that renders only when it is non-empty is a row that goes silent
 * exactly when it matters most. The same reasoning the liberties use for their
 * "none are recorded" note, in the opposite direction.
 *
 * And it does not claim to cover the liberties. A liberty belongs to no
 * attribute — that is why it has its own section — so the lead points at "What we
 * made up here" instead of pretending three rows of claim labels are the whole of
 * what was invented.
 */
const LEVELS = ['attested', 'inferred', 'reconstructed'];

/** The Evidence panel's own definitions (`index.html`, the legend list), each a
 *  literal substring of the legend text so the smoke can prove the two agree. */
const LEVEL_GLOSS = {
  attested: 'a source attests this at the scene date',
  inferred: 'reasoned from evidence about this thing',
  reconstructed: 'no source speaks to this one; built to fill a demonstrable need of the town',
};

/** What a citation IS at this level. Not decoration — see the header. */
const LEVEL_SOURCE_LEAD = {
  attested: 'From',
  inferred: 'Reasoned from',
  reconstructed: 'Bounded by',
};

/** A level with no sources, said plainly. `attested` is the interesting one: the
 *  grade REQUIRES a resolving source (`validate.py`, CONFIDENCE), so a card that
 *  reaches this branch is reporting a defect in its own record rather than a
 *  quirk of presentation, and it should say so where a reader can see it. */
const LEVEL_NO_SOURCE = {
  attested: 'No source is cited — which this grade requires, so the record is at fault.',
  inferred: 'No source is cited; the reasoning for each is on its own row below.',
  reconstructed: 'Nothing is cited as bounding these.',
};

const LEVEL_EMPTY = {
  attested: 'Nothing about this building is attested by a source.',
  inferred: 'Nothing here was reasoned from evidence about this particular building.',
  reconstructed: 'Nothing here was invented.',
};

/** Every graded claim the card renders below, in the order it renders them, and
 *  under exactly the conditions each section uses — a summary that counted a
 *  claim the card suppresses would be describing a different card. */
function gradedClaims(s, place) {
  const claims = [];
  const range = s.documented_range;
  if (range && (range.from || range.to)) {
    claims.push({ label: 'whether it stood here', claim: range });
  }
  claims.push({ label: 'where it stood', claim: place });
  if (s.footprint?.confidence) claims.push({ label: 'its outline', claim: s.footprint });
  for (const [key, attr] of Object.entries(s.attributes || {})) {
    claims.push({ label: prettyName(key), claim: attr || {} });
  }
  return claims;
}

function basisRow(level, mine, total) {
  const sources = [...new Set(mine.flatMap((c) => (
    Array.isArray(c.claim.sources) ? c.claim.sources : [])))];
  const what = mine.length
    ? `<p class="basis-what">${mine.map((c) => escapeHtml(c.label)).join(' · ')}</p>`
    : `<p class="basis-what basis-empty">${escapeHtml(LEVEL_EMPTY[level])}</p>`;
  const from = !mine.length ? ''
    : sources.length
      ? `<p class="basis-from">${escapeHtml(LEVEL_SOURCE_LEAD[level])}:
           ${sources.map(escapeHtml).join(' · ')}</p>`
      : `<p class="basis-from">${escapeHtml(LEVEL_NO_SOURCE[level])}</p>`;
  // An `attested` chip over something the model does not contain is true about
  // the evidence and false about the view — the rows below already mark it, and
  // a summary of what was INCLUDED that ignored it would be the worse half of
  // the same fault.
  const absent = mine.filter((c) => c.claim.geometry === 'absent');
  const notBuilt = absent.length
    ? `<p class="basis-absent">Not in the model:
         ${absent.map((c) => escapeHtml(c.label)).join(' · ')}</p>`
    : '';

  return `<div class="basis-row" data-level="${escapeHtml(level)}">
    <p class="basis-head">${chip(level)}<span class="basis-count">${mine.length} of ${total}</span>
      <span class="basis-gloss">${escapeHtml(LEVEL_GLOSS[level])}</span></p>
    ${what}${from}${notBuilt}
  </div>`;
}

function basisSection(s, place) {
  const claims = gradedClaims(s, place);
  if (!claims.length) return '';

  const buckets = new Map(LEVELS.map((l) => [l, []]));
  // Anything outside the three-level scale. `validate.py` refuses it in the
  // data, so this is not an expected state — but silently folding an unknown
  // grade into `reconstructed` would make the counts lie to hide a bug, and the
  // counts are the whole reason this section can be gated.
  const offScale = [];
  for (const c of claims) {
    (buckets.get(c.claim.confidence || 'reconstructed') ?? offScale).push(c);
  }

  const rows = LEVELS.map((l) => basisRow(l, buckets.get(l), claims.length)).join('');
  const odd = offScale.length
    ? `<div class="basis-row"><p class="basis-head"><span class="basis-count">${offScale.length}
         of ${claims.length}</span> <span class="basis-gloss">not graded on this scale — a fault
         in the record</span></p>
       <p class="basis-what">${offScale.map((c) => escapeHtml(c.label)).join(' · ')}</p></div>`
    : '';

  return `<section class="pop-sec pop-basis">
    <h3>What did we include, and where did it come from?</h3>
    <p class="basis-lead">${claims.length} claims stand behind this building, and every one of
      them is in exactly one row here. The tables further down carry them one at a time, with
      the reasoning behind <em>why</em>; the decisions that belong to no single claim are under
      “What we made up here”.</p>
    ${rows}${odd}
  </section>`;
}

/**
 * Was this building here on the day you are standing in, and how do we know
 * where it stood?
 *
 * These two are the load-bearing claims of the whole scene and the card carried
 * neither of their arguments. The date span never rendered at all — the markup
 * read `documented_range` and the compiler never wrote it — so a visitor could
 * read why a roof pitch was 35 degrees and not why the building was in the town.
 *
 * The dates are printed as recorded rather than prettified. `1835-12-31` is
 * frequently the end of a continuity argument rather than an event, and turning
 * it into "December 1835" would dress a bound up as a date somebody wrote down;
 * the note beside it is where that is explained, in the record's own words.
 */
function presenceSection(s) {
  const range = s.documented_range;
  if (!range || !(range.from || range.to)) return '';

  const span = `${range.from || '?'} → ${range.to || '?'}`;
  // The phase's own account used to open this section. It now opens the CARD
  // (`leadHtml`), because it is the sentence a visitor reads first and it was
  // buried under a summary of grades; the table keeps the claim it qualified.
  return `<section class="pop-sec">
    <h3>Was it here?</h3>
    <table class="attrs"><tbody>
      ${claimRow('recorded standing', span, range)}
    </tbody></table>
  </section>`;
}

/**
 * Is this the shape it was?
 *
 * The outline is the largest claim a visitor is standing in front of and the
 * card said nothing about it whatever. Six of the eight footprints in this
 * dataset open with the word PLACEHOLDER — no dimension of the Sauganash, the
 * Wolf Point Tavern, Miller's house or Walker's meeting house is attested in
 * anything read — and two are the opposite: Hogan's store is twenty by
 * forty-five feet in Andreas, twice, and the North Branch bridge's deck is
 * Cleaver's ten feet across a span measured between the traced 1834 banks. A
 * visitor could read none of that. `compile_scene.py` carried the footprint's
 * confidence and dropped its sources and its argument.
 *
 * That gap has a specific history, which is why it is worth a section rather
 * than a line. The massing rule used to take the worst confidence across the
 * footprint, so an unknown SIZE dithered a well-documented building into ghost
 * massing; it was narrowed to the attributes that say what a building WAS, on
 * the stated understanding that dimensional uncertainty would be carried in the
 * sidecar where the popup shows it. The tint stopped saying it and nothing
 * started. So the one claim deliberately taken out of the view is the one the
 * card had no words for.
 *
 * NO DIMENSION IS PRINTED, and that is a decision rather than an omission. The
 * only value available is the polygon, and the only way to print a polygon in a
 * table is to reduce it — a bounding box over Miller's L-plan would be a new
 * invention on the card that exists to admit them, and it would be the reader's
 * impression of a measurement where the record has none. The shape itself is
 * already in front of the visitor at full size. What the card owes is how much
 * of it is evidence, and that is a chip, a source list and the record's own
 * reasoning.
 */
function shapeSection(s) {
  const fp = s.footprint;
  if (!fp || !fp.confidence) return '';
  return `<section class="pop-sec pop-shape">
    <h3>Was it this shape?</h3>
    <table class="attrs"><tbody>
      ${claimRow('footprint', null, fp)}
    </tbody></table>
  </section>`;
}

/**
 * Is what this card just told you actually settled?
 *
 * `data/exclusions.json`'s watch list is the third category — researched, and
 * neither built nor ruled out — and one of its four entries is STANDING in the
 * scene. The Evidence panel has carried all four since they became data, and its
 * entry for the standing one ends by saying that the doubt sits on the record's
 * own dated claim "and the provenance card shows it". The card showed the claim.
 * It never showed that the claim is a tracked open question, so a visitor reading
 * `1834-01-01 → 1840-12-31` with an `reconstructed` chip over it could learn that we
 * are not certain, and could not learn that the uncertainty is a live dispute
 * between two sources, what settling it would change, or that this project is
 * holding the grade down on purpose until evidence arrives. The doubt reached
 * whoever opened a panel about the whole scene, not whoever walked up to the
 * building it is about — which is the gap the liberties had before they were
 * attached to their buildings.
 *
 * A building with nothing open renders NOTHING here, and that is the honest
 * shape rather than a missing empty state. "No open questions are recorded about
 * this building" would read as *this building is settled*, and the list cannot
 * support that: four entries against roughly forty researched structures, and an
 * open question nobody has noticed is exactly as invisible as a liberty nobody
 * noticed taking. Silence claims nothing; a reassurance would claim a lot.
 */
function openQuestionSection(questions, structureId) {
  if (!Array.isArray(questions)) return '';   // not loaded: claim nothing
  const mine = openQuestionsFor(questions, structureId);
  if (!mine.length) return '';                // nothing open: say nothing
  return `<section class="pop-sec pop-question">
    <h3>Is this settled?</h3>
    <p class="pop-question-lead">No — what this card tells you about this building is
      on the project's list of open questions.</p>
    <div class="liberties">${mine.map((u) => uncertaintyEntryHtml(u, { onCard: true })).join('')}</div>
  </section>`;
}

/**
 * The liberties taken with this building, or an honest note that none are
 * recorded. Rendered with the Evidence panel's own entry renderer so the two
 * views cannot describe the same liberty differently.
 *
 * The scope chip is suppressed for `per_subject` entries — here the subject IS
 * the card — but kept for anything broader, because a scene-wide liberty landing
 * on one building is a fact worth showing rather than flattening.
 */
function libertySection(liberties, structureId) {
  if (!Array.isArray(liberties)) return '';   // not loaded: claim nothing
  const mine = libertiesFor(liberties, structureId);
  const body = mine.length
    ? `<div class="liberties">${mine.map((lib) => libertyEntryHtml(lib, {
      showSubjects: false,
      showScope: lib.section !== 'per_subject',
    })).join('')}</div>`
    : `<p class="pop-lib-none">No liberties are recorded against this building —
         which means none were written down, not that none were taken.</p>`;

  return `<section class="pop-sec pop-liberties">
    <h3>What we made up here${mine.length ? ` <span class="pop-count">${mine.length}</span>` : ''}</h3>
    ${body}
  </section>`;
}

/**
 * What the record says about itself, in the record's own words.
 *
 * `research_note` is on every structure record and in every compiled sidecar,
 * and until now no surface in the walkthrough showed it — the sidecar-contract
 * gate reported it as compiled-and-never-read on 2026-08-10 and called it an
 * unshipped claim rather than dead weight. It is the paragraph that says which
 * of two sources was believed and why, that this building held the post office
 * and is not the post office on the day you are standing in, that the likeliest
 * reconciliation of the evidence is that this record models the wrong building.
 * None of that is expressible as a value with a chip over it, which is why it
 * was written as prose and why it belongs here rather than in a table.
 *
 * Verbatim, and folded away. Verbatim because a note whose subject is the limit
 * of the evidence is the last text on this card that should be trimmed,
 * re-punctuated or summarised — the record's emphasis is the author's, including
 * the shouted phrases, and a renderer that tidied it would be editing a source.
 * Folded because these run to several hundred words and an open one would push
 * the citations off the card on a phone, where the panel is 62vh.
 *
 * @param {object} s  the sidecar
 */
function researchSection(s) {
  const note = s.research_note;
  if (!note) return '';        // no note: no section, and no sentence about why
  return `<section class="pop-sec pop-research">
    <h3>The record's own account</h3>
    <details class="research">
      <summary>in the record's own words</summary>
      <p class="research-body">${escapeHtml(note)}</p>
    </details>
  </section>`;
}

/* ------------------------------------------------------------------------ */
/* THE TOP HALF OF THE CARD — what it was, where, since when, who was there.  */
/*                                                                            */
/* The owner's brief for the drawer redesign asked for the card to lead with  */
/* what the building IS and its key facts, with the provenance underneath     */
/* behind tabs. Everything above this comment is provenance and is unchanged; */
/* what follows is the label a visitor reads FIRST, composed strictly from    */
/* record fields the sections below already qualify one claim at a time. The  */
/* grade on each fact is a quiet dot, never a chip: the chips belong to the   */
/* evidence tables, and `smoke_renderer.mjs` counts them as the card's graded */
/* claims, so a second chip over the same claim would double the tally.       */
/* ------------------------------------------------------------------------ */

const GRADES = new Set(LEVELS);

/** The weaker of two grades, on the three-step scale. A composite fact ("braced
 *  frame · 2 storeys") is only as sure as its least-sure half. */
function weaker(a, b) {
  if (!GRADES.has(a)) return GRADES.has(b) ? b : undefined;
  if (!GRADES.has(b)) return a;
  return CONF_ORDER[a] >= CONF_ORDER[b] ? a : b;
}

/** A 7 px dot for a grade. Renders NOTHING for a grade off the scale — an
 *  ungraded fact gets no dot rather than a guessed one. `what` names the claim
 *  in the tooltip ("position: inferred"), because a dot with no words is a
 *  colour a visitor has to remember the meaning of. */
function factDot(grade, what) {
  if (!GRADES.has(grade)) return '';
  const gloss = {
    attested: 'a source states it',
    inferred: 'reasoned from evidence about this building',
    reconstructed: 'invented to fill a demonstrable need of the town',
  }[grade];
  const title = `${what ? `${what}: ` : ''}${grade} — ${gloss}`;
  return `<i class="fact-dot fact-${escapeHtml(grade)}" title="${escapeHtml(title)}"></i>`;
}

/** A value with its dot bound to its last word. A no-break space is not enough:
 *  CSS Text keeps a soft-wrap opportunity before an atomic inline even after
 *  U+00A0, so a dot alone on a wrapped line — a bullet for nothing — needs a
 *  `white-space: nowrap` span around the word it belongs to. */
function withDot(text, dot) {
  const words = String(text).split(' ');
  const last = words.pop();
  const head = words.length ? `${escapeHtml(words.join(' '))} ` : '';
  return `${head}<span class="fact-tail">${escapeHtml(last)}${dot}</span>`;
}

/** The `function` values that do not read once `_` becomes a space. Everything
 *  else goes through the generic rule below; this is for the tokens where a bare
 *  space misreads ("tavern inn"). Nothing here adds a word the record does not
 *  carry — it only punctuates the record's own compound. */
const FUNCTION_WORDS = {
  tavern_inn: 'tavern & inn',
  store_residence: 'store & residence',
  dwelling_to_let: 'dwelling, to let',
  hotel_under_construction: 'hotel, under construction',
  slaughterhouse_packing: 'slaughterhouse & packing house',
  forwarding_commission_warehouse: 'forwarding & commission warehouse',
  meeting_house_school: 'meeting house & school',
  soap_candle_manufactory: 'soap & candle manufactory',
  dwelling_farmstead: 'farmstead dwelling',
  physicians_office: "physician's office",
  agency_house_residence: 'agency house & residence',
  // T-1311 closed the `function` vocabulary and folded 109 free strings onto 106
  // terms. These are the ones whose PROSE the card had been printing straight off
  // the record — hyphens, commas, apostrophes and all — and which the generic rule
  // would now flatten. The card goes on saying exactly what it said before the
  // vocabulary was closed; the punctuation is the record's, not an addition.
  one_room_frame_cottage: 'one-room frame cottage',
  two_room_frame_cottage: 'two-room frame cottage',
  deep_plan_frame_cottage: 'deep-plan frame cottage',
  one_and_a_half_story_frame_cottage: 'one-and-a-half-story frame cottage',
  larger_one_and_a_half_story_house: 'larger one-and-a-half-story house',
  small_two_story_frame_house: 'small two-story frame house',
  narrow_two_story_store: 'narrow two-story store',
  narrow_two_story_warehouse: 'narrow two-story warehouse',
  cooper_wagon_or_wheelwright_shop: 'cooper, wagon or wheelwright shop',
  parade_and_drill_ground: 'parade and drill ground',
  block_house: 'block-house',
  county_court_house: 'county court-house',
  commanding_officers_quarters: "commanding officer's quarters",
  officers_quarters: "officers' quarters",
  enlisted_mens_barracks: "enlisted men's barracks",
  sutlers_store: "sutler's store",
  // The three records whose function was a SENTENCE about a use that had ended.
  // `kindWords` below still cuts each at its first semicolon, so the kind line
  // reads "dwelling" / "log house" / "log cabin" exactly as it always has, and the
  // Use row still carries the whole of it.
  dwelling_former_school_use_unattested:
    "dwelling; used as John Watkins' school in 1833, use on the scene date unattested",
  log_house_former_school_use_unattested:
    'log house; infant school 1833-34, use on the scene date unattested',
  log_cabin_former_store_and_school_use_unattested:
    "log cabin; Chicago's first drug store 1832, let 1832-33, Eliza Chappel's school "
    + '1833-34; use on the scene date unattested',
};

/** The record's `function`, in words. Already-prose values ("one-room frame
 *  cottage") pass through untouched; tokens lose their underscores and `_and_`
 *  becomes an ampersand. */
function functionWords(value) {
  if (value === null || value === undefined) return '';
  const raw = String(value).trim();
  if (!raw) return '';
  if (FUNCTION_WORDS[raw]) return FUNCTION_WORDS[raw];
  if (!raw.includes('_')) return raw;
  return raw.replace(/_and_/g, ' & ').replace(/_/g, ' ');
}

/** The kind line's short form: a `function` that runs to a clause about the
 *  building's history ("log cabin; Chicago's first drug store 1832, …") is cut
 *  at its first semicolon HERE ONLY. The Use row and the attribute table carry
 *  the whole value; this line is a label, and a label is one phrase. */
function kindWords(value) {
  return functionWords(value).split(';')[0].trim();
}

/** The archetype the generators built from, in words. `bridge_timber` and
 *  `pier_crib` are the schema's noun-first order and read wrongly reversed. */
const ARCHETYPE_WORDS = { bridge_timber: 'timber bridge', pier_crib: 'crib pier' };
function archetypeWords(archetype) {
  if (!archetype) return '';
  return ARCHETYPE_WORDS[archetype] ?? String(archetype).replace(/_/g, ' ');
}

const ISO_DATE = /^(\d{4})-\d{2}-\d{2}$/;

/** The standing span as years, when — and only when — both ends are ISO dates.
 *  `1831-01-01 → 1851-03-04` reads as "1831 – 1851"; a bound that is the end of a
 *  continuity argument (`1835-12-31`) reads as the year it bounds, which is what a
 *  year means. Anything odd is shown raw, because a renderer that tidies an odd
 *  date is guessing what it meant. The "Was it here" row keeps the raw pair. */
function standingWords(range) {
  if (!range || !(range.from || range.to)) return '';
  const f = ISO_DATE.exec(range.from ?? '');
  const t = ISO_DATE.exec(range.to ?? '');
  if (f && t) return f[1] === t[1] ? f[1] : `${f[1]} – ${t[1]}`;
  return `${range.from || '?'} → ${range.to || '?'}`;
}

/** Heads of the households the residents layer places here, by name. */
function headsOf(s) {
  const households = Array.isArray(s.residents) ? s.residents : [];
  const heads = [];
  for (const h of households) {
    for (const person of h.persons ?? []) {
      if (person.relationship === 'head' && person.name) heads.push(person.name);
    }
  }
  return heads;
}

/** "braced frame · 2 storeys" — the fabric in one phrase, or as much of it as
 *  the record has. */
function builtWords(attrs) {
  const parts = [];
  const cons = attrs.construction?.value;
  if (cons !== null && cons !== undefined && cons !== '') parts.push(prettyValue(cons));
  const st = attrs.stories?.value;
  if (typeof st === 'number') parts.push(`${st} ${st === 1 ? 'storey' : 'storeys'}`);
  else if (st) parts.push(`${prettyValue(st)} storeys`);
  return parts.join(' · ');
}

function roofWords(attrs) {
  const type = attrs.roof_type?.value;
  if (type === null || type === undefined || type === '') return '';
  const pitch = attrs.roof_pitch_deg?.value;
  const words = prettyValue(type);
  return typeof pitch === 'number' && type !== 'none' ? `${words}, ${pitch}°` : words;
}

/**
 * The head: title, other names, what kind of thing it is, where it stood, and the
 * flags that qualify the whole card. The flags are the same five sentences the
 * old `.pop-meta` block carried (provisional position, anonymous reconstruction,
 * no recorded household, placeholder mesh) plus one that had no surface at all:
 * `review_required` (T-0268). Nine records are held under AGENTS.md's standing
 * constraint and until now the flag reached a browser once, as a console line
 * about the scene. The sentence is standing text keyed on the boolean — the
 * record's own reasoning is in its notes below, verbatim, as the ticket says —
 * and it names what the record is held for, because "held" alone tells a reader
 * that a decision was made and nothing about what it rests on. The record's own
 * sentence follows it, from `review_reason` on the sidecar.
 */
function headHtml(s, record, called, p, place) {
  const aka = Array.isArray(s.aka) && s.aka.length
    ? `<p class="pop-aka">also ${s.aka.map(escapeHtml).join(' · ')}</p>` : '';

  const kind = kindWords(s.attributes?.function?.value);
  const arche = archetypeWords(s.archetype);
  // "dwelling · frame dwelling" says one thing twice. When one phrase contains
  // the other, the longer one carries both and stands alone; otherwise the
  // function and the archetype are two facts and both are shown.
  const k = kind.toLowerCase(); const a = arche.toLowerCase();
  const kindParts = kind && arche
    ? (a.includes(k) ? [arche] : k.includes(a) ? [kind] : [kind, arche])
    : [kind || arche].filter(Boolean);
  const kindLine = kindParts.length
    ? `<p class="pop-kind">${kindParts.map(escapeHtml).join(' · ')}</p>` : '';

  const whereLine = `<p class="pop-where-line"><strong>${
    withDot(p.symbolic_location ?? 'Location not recorded', factDot(place.confidence, 'position'))
  }</strong></p>`;

  const flags = [];
  if (p.placement_provisional) {
    flags.push(`<span class="pop-flag">Position is provisional — the coordinates are a stand-in,
      not a survey. Georeferencing from the 1834 sheets is not better than about
      ±${escapeHtml(p.uncertainty_m ?? 20)} m even once traced.</span>`);
  }
  // `inferred_anonymous` is the machine value and is never printed; the words a
  // visitor reads say `reconstructed`, which is the tier every attribute of these
  // roofs carries. The history of this line losing its flag is in the git log
  // of the old `show()` and in STATUS § 28.
  if (s.reconstruction?.status === 'inferred_anonymous') {
    flags.push(`<span class="pop-flag"><strong>Reconstructed — anonymous ${
      escapeHtml(s.reconstruction.family)} roof.</strong>
      Its family and district come from the modern production specification;
      this is not an attested named building or a recovered parcel.</span>`);
  }
  // A title that says "vacant" or "to let" asserts an ABSENCE, and an absence is
  // not a finding. The residents layer reaches 104 of the anonymous roofs; the
  // rest are unmodelled, not attested empty.
  if (called.vacant) {
    flags.push(`<span class="pop-flag">No household is recorded here, which is not evidence
      that it stood empty. The residents layer models the households this town's
      trades demand and reaches 104 of the anonymous roofs; this is one of the
      others, so the title describes the building rather than its occupancy.</span>`);
  }
  // A fact about the MESH, not the record: it arrives on the registry entry from
  // the loader that opened the file (the compiler cannot know it).
  if (record.assetIsPlaceholder) {
    flags.push('<span class="pop-flag">This shape is a placeholder massing, not a bake from the record.</span>');
  }
  // The one flag on this card that is not about how well the building is known.
  // The four above qualify a reconstruction; this one says the project has stopped
  // short of a claim on purpose, and it outranks them — so it is rendered last, in
  // its own treatment, and it is the only flag that quotes the record.
  //
  // The quote is the point. Standing text can say a building is HELD; only the
  // record can say what it is held FOR, and the sentence is the one
  // `measure_review_constraint.py` assertion 6 judges, carried here by the
  // compiler through the module the two of them share (T-0268). Before this the
  // reason lived in a 400-word `research_note` the card shows verbatim and folded
  // away, which is a reason a visitor never reads.
  if (s.review_required === true) {
    const reason = typeof s.review_reason === 'string' ? s.review_reason.trim() : '';
    flags.push(`<span class="pop-flag pop-flag-held"><strong>Held pending consultation.</strong>
      This record touches the standing constraint on depicting Indigenous history in
      1835: the project depicts the built fabric and stops there until the people
      whose history it is have been consulted.${
        reason ? `<em class="pop-held-why">${escapeHtml(reason)}</em>` : ''
      }</span>`);
  }
  const flagBlock = flags.length ? `<div class="pop-flags">${flags.join('')}</div>` : '';

  return `<div class="pop-head">
    <div class="pop-title-row">
      <h2>${escapeHtml(called.title)}</h2>
      <button class="pop-close" type="button" data-close aria-label="Close">×</button>
    </div>
    ${aka}
    ${kindLine}
    ${whereLine}
    ${flagBlock}
  </div>`;
}

/**
 * The lead: the phase's own account, verbatim, when the record wrote one.
 *
 * Fourteen records (the Fort Dearborn buildings and the lighthouse) carry no
 * `change_note`. For those the lead is COMPOSED, and the rule is strict so that
 * the smoke can hold it: title, function words and symbolic location joined by
 * "was a … at …", then the first household's own `name` and `relation` as the
 * record wrote them ("The Murphy household lived and worked here."). No
 * adjective is added and no field is paraphrased; a record with neither
 * function nor location gets "{Title} stood here." and nothing more, because the
 * alternative is prose about a building the record says nothing about.
 */
/** A location that already opens with its own preposition ("Inside the south-west
 *  of Fort Dearborn…", "At the south-west angle…") is joined as it stands, with
 *  its capital lowered; anything else is introduced with "at". */
const LEADING_PREPOSITION = /^(at|on|in|inside|near|by|between|behind|beside|along|under|within|across|opposite|off|outside|over|astride|facing)\b/i;
function whereClause(where) {
  const w = String(where).trim().replace(/\.$/, '');
  if (LEADING_PREPOSITION.test(w)) return w.charAt(0).toLowerCase() + w.slice(1);
  // "at The open court" — an article keeps its capital only at a sentence start.
  const lowered = /^(The|An?)\b/.test(w) ? w.charAt(0).toLowerCase() + w.slice(1) : w;
  return `at ${lowered}`;
}

function composedLead(s, called, p) {
  const title = called.title;
  const fn = kindWords(s.attributes?.function?.value);
  const where = p.symbolic_location;
  // "Fort Dearborn — block-house was a block-house" says the noun twice; when the
  // title already carries the function's words the sentence only needs the place.
  const titled = fn && title.toLowerCase().includes(fn.toLowerCase());
  const article = /^[aeiou]/i.test(fn) ? 'an' : 'a';
  let text;
  if (fn && !titled && where) text = `${title} was ${article} ${fn} ${whereClause(where)}.`;
  else if (fn && !titled) text = `${title} was ${article} ${fn}.`;
  else if (where) text = `${title} stood ${whereClause(where)}.`;
  else text = `${title} stood here.`;
  const h = Array.isArray(s.residents) ? s.residents[0] : null;
  if (h?.name && h?.relation) text += ` ${String(h.name).trim()} ${String(h.relation).trim().replace(/\.$/, '')}.`;
  return text;
}

function leadHtml(s, called, p) {
  const text = s.change_note ? String(s.change_note) : composedLead(s, called, p);
  const composed = s.change_note ? '' : ' data-composed';
  return `<p class="pop-lead pop-account"${composed}>${escapeHtml(text)}</p>`;
}

/**
 * The facts: a two-column definition list of the record's key values, each with
 * a grade dot. Every value here is ALSO a row in the evidence tables below with
 * its chip, sources and reasoning — this is the label, that is the catalogue.
 * A row with no value is omitted rather than shown as "—", because a museum
 * label does not list what it does not know; the tables do that job.
 */
/**
 * THE FIRMS IN THIS ROOF, on the line that already says what the roof was FOR.
 *
 * A building card has always been able to say "store". It could not say WHOSE
 * store, or open it: the business layer reached a visitor only through the
 * Businesses directory, so somebody standing at Hogan's door had to leave the
 * building, open the drawer and search a name they were already looking at. The
 * Use row is where that question is asked, so the answer goes on the Use row.
 *
 * TWO RELATIONS, ASKED SEPARATELY. A `premises` firm is one the register puts IN
 * this roof. An `anchored` firm has no roof of its own and the paper sites it BY
 * this one — "next door to the Sauganash" — and until T-1401 that landmark lived
 * only inside `limit_reason`'s prose, so this row could not say which four houses
 * stand against the Tremont House and refused to guess. The compiler resolves the
 * register's own `action_target` now, so the two groups print as two leads and a
 * reader is never told a house was here when the source said it was beside here.
 * The grade dot is the FIRM's, not the building's, because the firm is what
 * tapping opens.
 *
 * @param {object[]} firms  `firmCrosswalk().byStructure` for this record's id
 * @param {boolean} fromSign  the visitor aimed at this building's signboard
 */
function firmChipsHtml(firms, fromSign) {
  if (!firms?.length) return '';
  const chips = (list) => list.map((f) => `<button type="button"
      class="pop-firm" data-business="${escapeHtml(f.id)}"
      title="${escapeHtml([f.trade, f.present ? 'trading on 1 July 1835' : 'not trading on 1 July 1835']
    .filter(Boolean).join(' \u2014 '))}"><i class="grade-dot grade-${escapeHtml(f.grade)}"></i>${
  escapeHtml(f.name)}</button>`).join('');
  const inRoof = firms.filter((f) => f.relation !== 'against');
  const against = firms.filter((f) => f.relation === 'against');
  const groups = [];
  if (inRoof.length) {
    groups.push([fromSign
      ? (inRoof.length === 1 ? 'The board hangs for' : 'The board hangs over')
      : (inRoof.length === 1 ? 'The register puts one house here'
        : `The register puts ${inRoof.length} houses here`), inRoof]);
  }
  // NOT "HERE". The paper sited these by this building and gave them no roof, and
  // the words have to keep that distance or the card claims a premises the source
  // never gave.
  if (against.length) {
    groups.push([against.length === 1
      ? 'One house is sited against it'
      : `${against.length} houses are sited against it`, against]);
  }
  return `<span class="pop-firms"${fromSign ? ' data-from-sign="yes"' : ''}>${groups.map(
    ([lead, list]) => `<span class="pop-firms-lead">${escapeHtml(lead)}</span>${chips(list)}`).join('')}</span>`;
}

function factsHtml(s, firms = [], fromSign = false) {
  const attrs = s.attributes ?? {};
  const rows = [];
  // A value that will not fit half a column — the address, the ground's entry,
  // a long keepers line, the firms in the roof — takes the whole row rather than
  // wrapping to a sliver.
  const row = (dt, dd, grade, what, extra = '') => {
    if (!dd && !extra) return;
    const wide = extra || String(dd).length > 28 ? ' fact-wide' : '';
    const value = dd ? withDot(dd, factDot(grade, what ?? dt.toLowerCase())) : '';
    rows.push(`<div class="fact${wide}"><dt>${escapeHtml(dt)}</dt><dd>${value}${extra}</dd></div>`);
  };

  row('Standing', standingWords(s.documented_range), s.documented_range?.confidence, 'standing');
  row('Use', functionWords(attrs.function?.value), attrs.function?.confidence, 'use',
    firmChipsHtml(firms, fromSign));
  row('Built', builtWords(attrs),
    weaker(attrs.construction?.confidence, attrs.stories?.confidence), 'fabric');
  row('Roof', roofWords(attrs),
    attrs.roof_pitch_deg && attrs.roof_type?.value !== 'none'
      ? weaker(attrs.roof_type?.confidence, attrs.roof_pitch_deg?.confidence)
      : attrs.roof_type?.confidence, 'roof');
  if (attrs.lot_address?.value) {
    row('Address', prettyValue(attrs.lot_address.value), attrs.lot_address.confidence, 'address');
  }
  // T-1478. The other half of "where is this, exactly?": `Address` above is a lot a
  // SOURCE printed, this is the lot the grid drew afterwards and found this footprint
  // already standing on. Its own note says at length that nobody claimed it, and the
  // chip carries the grade, so the label stays modest — "Stands on", not "Address".
  if (attrs.stands_on_lot?.value) {
    row('Stands on', prettyValue(attrs.stands_on_lot.value),
      attrs.stands_on_lot.confidence, 'the lot it stands on');
  }
  if (attrs.land_owner?.value) {
    row('Owner of the ground', prettyValue(attrs.land_owner.value),
      attrs.land_owner.confidence, 'ground');
  }
  // Heads of households carry a GRADE per person, not a confidence — a different
  // axis, shown on their own rows in "Who was here". No dot here, deliberately.
  const heads = headsOf(s);
  if (heads.length) {
    const joined = heads.join(' · ');
    rows.push(`<div class="fact${joined.length > 28 ? ' fact-wide' : ''}"><dt>Lived here</dt><dd>${
      escapeHtml(joined)}</dd></div>`);
  }
  if (attrs.occupants?.value) {
    row('Keepers', prettyValue(attrs.occupants.value), attrs.occupants.confidence, 'keepers');
  }
  if (!rows.length) return '';
  return `<dl class="pop-facts">${rows.join('')}</dl>`;
}

/**
 * Where did it stand? The position's argument, on its own row in the evidence
 * pane. It used to sit in the head as a chip beside the location; the head now
 * carries a dot, and the chip — which the smoke counts as one of the card's
 * graded claims — moves into a `table.attrs` row so it is qualified exactly the
 * way every other claim is. The `why` here is often the longest argument in the
 * record (three of the eight named placements are derived from bank geometry
 * because no corner survives).
 */
function whereSection(p, place) {
  if (!place.confidence && !p.symbolic_location) return '';
  return `<section class="pop-sec pop-where">
    <h3>Where did it stand?</h3>
    <table class="attrs"><tbody>
      ${claimRow('recorded position', p.symbolic_location ?? 'Location not recorded', place)}
    </tbody></table>
  </section>`;
}

/**
 * The town's own law, on the building it fell on or did not.
 *
 * The 5 August 1835 ordinance is the only DOCUMENTED statement this project holds
 * about where the built-up town ended in the scene year — a boundary the Trustees
 * walked street by street, inside which a hay stack cost twenty-five dollars. It
 * is a fire rule, so the line IS their answer to "where is the town built up?",
 * and every other answer in this dataset is derived from the plat, the land deal
 * and measured frontage instead.
 *
 * Nothing is drawn in the scene for it: a legal limit is not a fence. This row is
 * where it reaches a visitor, and it says which side of the line the building a
 * visitor just clicked on stood on.
 *
 * Silent in two cases, both deliberate. `limits` null means the derived file did
 * not load, and "not loaded" is not the same claim as "this building was outside".
 * A null answer means the record commits no position, so there is no side to
 * be on. The ordinance is also five weeks LATER than the scene date, which the
 * row says rather than hides.
 */
function ordinanceSection(limits, p) {
  if (!limits) return '';
  const covered = limits.coversPlacement(p);
  if (covered === null) return '';
  const ord = limits.ordinance ?? {};
  const inside = covered
    ? 'Inside the limit — hay could not lawfully be stacked here.'
    : 'Outside the limit — the rule did not reach this ground.';
  const quote = ord.quote
    ? `<blockquote class="pop-quote">${escapeHtml(ord.quote)}</blockquote>` : '';
  return `<section class="pop-sec pop-ordinance">
    <h3>Was it inside the town's fire limit?</h3>
    <p class="pop-ordinance-stands">${escapeHtml(inside)}</p>
    <p class="pop-ordinance-lead">Section 22 of the by-laws the Trustees passed on
      5 August 1835 made it unlawful to stack hay inside a boundary they walked street
      by street — ${limits.areaAcres ? `${escapeHtml(String(limits.areaAcres))} acres` : 'a boundary'}
      of it — under twenty-five dollars a stack. It is the town's own statement of where
      it was built up closely enough to burn, five weeks after this scene.</p>
    ${quote}
    <p class="pop-ordinance-cite">The Chicago Democrat, 19 August 1835, page 1 —
      the limit is derived from committed street lines, never drawn in the scene.</p>
  </section>`;
}

/** The three panes under the facts, and the strip that switches them. The last
 *  tab a visitor chose is remembered for the session — module scope, not
 *  storage — so walking from one building to the next keeps the reader where
 *  they were reading. All three panes stay in the DOM: a pane hidden by
 *  `[hidden]` is still the record, and the smoke reads it after activating its
 *  tab rather than trusting a collapsed read. */
const TABS = [
  { id: 'evidence', label: 'Evidence' },
  { id: 'liberties', label: 'What we made up' },
  { id: 'record', label: 'Record' },
];
let lastTab = 'evidence';

function tabsHtml(counts) {
  const buttons = TABS.map((t) => {
    const n = counts[t.id];
    const count = n ? ` <span class="pop-count">${n}</span>` : '';
    const on = t.id === lastTab;
    return `<button class="pop-tab" type="button" role="tab" data-pop-tab="${t.id}"
      aria-selected="${on}" aria-controls="pop-pane-${t.id}" tabindex="${on ? 0 : -1}">${
      escapeHtml(t.label)}${count}</button>`;
  }).join('');
  return `<nav class="pop-tabs" role="tablist" aria-label="About this record">${buttons}</nav>`;
}

function paneHtml(id, inner) {
  const on = id === lastTab;
  return `<div class="pop-pane" id="pop-pane-${id}" role="tabpanel" data-pop-pane="${id}"${
    on ? '' : ' hidden'}>${inner}</div>`;
}

/** Switch panes inside one card. Called from the click handler and from `show()`
 *  (which renders the remembered tab directly, so this is the click path). */
function selectPopTab(root, id) {
  if (!TABS.some((t) => t.id === id)) return;
  lastTab = id;
  for (const b of root.querySelectorAll('.pop-tab[data-pop-tab]')) {
    const on = b.dataset.popTab === id;
    b.setAttribute('aria-selected', String(on));
    b.tabIndex = on ? 0 : -1;
  }
  for (const pane of root.querySelectorAll('.pop-pane[data-pop-pane]')) {
    pane.toggleAttribute('hidden', pane.dataset.popPane !== id);
  }
}

/**
 * Where a dossier is READ, which is not where it lives in this repository.
 *
 * The card used to link `docBase + s.research_doc` — a path relative to the page,
 * which resolves in the source tree and nowhere a visitor stands: `publish.sh`
 * deliberately leaves `docs/` out of the payload ("the uncompressed GLB masters,
 * the research dossiers and the raw dataset all stay in the repo and out of the
 * payload"), so every card on the deployed site linked to a 404 (ROADMAP K26).
 * The dossiers are markdown and a browser will not render markdown, so publishing
 * them would want a viewer; GitHub already is one, and renders the file with its
 * tables and its images intact.
 *
 * `main` and not `dev`, deliberately: this is the branch a visitor's copy of the
 * walkthrough was promoted from. A dossier written on `dev` and not yet promoted
 * therefore links to a page that appears when the promotion lands — the same lag
 * the rest of the tier carries, rather than a second one.
 */
export const DOSSIER_BASE = 'https://github.com/kevinrhaas/custom/blob/main/chicago/4d/';

/**
 * @param {HTMLElement} root  the <aside> to render into
 * @param {object} opts
 * @param {string} opts.docBase  where a dossier is read — see DOSSIER_BASE
 */
export function createPopup(root, { docBase = DOSSIER_BASE, onBusiness = null } = {}) {
  let currentId = null;
  /** Null until the derived list loads; never faked to an empty list. */
  let liberties = null;
  /** Same rule for the scene's open questions: null means "not loaded", which is
   *  not the same claim as "nothing is open about this building". */
  let openQuestions = null;
  /** Null until the derived ordinance limits load; see `ordinanceSection`. */
  let ordinanceLimits = null;
  /** Null until the compiled agency relation loads. Same rule as the liberties:
   *  null means "not loaded", which is not the claim that this house held none. */
  let agencies = null;
  /** Null until the business index loads, and the same rule again: null is not
   *  the claim that no firm traded here. */
  let businessesByStructure = null;
  let currentRecord = null;
  /** Whether the card on screen was opened by aiming at this building's signboard,
   *  kept so a redraw (the liberties, the agencies) does not lose the fact. */
  let currentFromSign = false;

  function close() {
    currentId = null;
    currentRecord = null;
    currentFromSign = false;
    root.setAttribute('hidden', '');
    root.innerHTML = '';
    document.documentElement.classList.remove('card-open');
  }

  root.addEventListener('click', (e) => {
    if (e.target.closest('[data-close]')) { close(); return; }
    const firm = e.target.closest('.pop-firm');
    if (firm) { onBusiness?.(firm.dataset.business); return; }
    const tab = e.target.closest('[data-pop-tab]');
    if (tab) { selectPopTab(root, tab.dataset.popTab); return; }
    const toggle = e.target.closest('[data-toggle-note]');
    if (toggle) {
      const note = toggle.parentElement.querySelector('[data-note]');
      const shown = !note.hasAttribute('hidden');
      note.toggleAttribute('hidden', shown);
      toggle.textContent = shown ? 'why' : 'hide';
    }
  });

  return {
    get openId() { return currentId; },
    close,

    /**
     * Hand the popup the derived liberties once they load. Boot awaits the list
     * before the gate opens, so in practice a card is never drawn without it —
     * but a card already on screen is redrawn rather than left stale, because
     * the one failure mode that matters here is a building quietly showing
     * fewer admissions than the record holds.
     *
     * @param {object[]|null} list  `data/liberties.json`'s `liberties`
     */
    setLiberties(list) {
      liberties = Array.isArray(list) ? list : null;
      if (currentRecord) this.show(currentRecord, { fromSign: currentFromSign });
    },

    /**
     * Hand the popup the scene's open questions, for the same reason and with the
     * same redraw: the failure that matters is a card quietly showing fewer
     * caveats than the dataset holds.
     *
     * @param {object[]|null} list  the compiled `uncertain` list for this scene
     */
    setOpenQuestions(list) {
      openQuestions = Array.isArray(list) ? list : null;
      if (currentRecord) this.show(currentRecord, { fromSign: currentFromSign });
    },

    /**
     * Hand the popup the derived town ordinance limits, on the same terms as the
     * liberties and the open questions: a card already on screen is redrawn rather
     * than left without a row the dataset can now fill.
     *
     * @param {object|null} limits  `loadOrdinanceLimits()`'s handle, or null
     */
    setOrdinanceLimits(limits) {
      ordinanceLimits = limits ?? null;
      if (currentRecord) this.show(currentRecord, { fromSign: currentFromSign });
    },

    /**
     * Hand the popup the compiled agency relation once it loads. Redrawn like the
     * liberties, for the same reason: a card already on screen showing fewer
     * relations than the dataset holds is the one failure mode that matters.
     *
     * @param {object|null} doc  `loadAgencies()`'s handle, or null
     */
    setAgencies(doc) {
      agencies = doc ?? null;
      if (currentRecord) this.show(currentRecord, { fromSign: currentFromSign });
    },

    /**
     * Hand the popup the structure-to-firms crosswalk once the business index
     * loads, on exactly the terms the four handles above keep: a card already on
     * screen is redrawn, because a building quietly showing no keeper the
     * register knows is the failure that matters.
     *
     * @param {Map<string, object[]>|null} map  `firmCrosswalk().byStructure`
     */
    setBusinesses(map) {
      businessesByStructure = map ?? null;
      if (currentRecord) this.show(currentRecord, { fromSign: currentFromSign });
    },

    /**
     * @param {object} record  a registry entry: { id, sidecar, ... }
     * @param {object} [opts]
     * @param {boolean} [opts.fromSign]  the visitor aimed at this building's
     *   signboard rather than at the roof — a board is a firm's advertisement, so
     *   the Use row leads with the firm it hangs for instead of making the visitor
     *   work out that the board and the house are the same thing.
     */
    show(record, { fromSign = false } = {}) {
      if (!record?.sidecar) return false;
      const s = record.sidecar;
      currentId = record.id;
      currentRecord = record;
      currentFromSign = !!fromSign;
      const firms = businessesByStructure?.get?.(record.id) ?? [];

      const p = s.placement ?? {};
      // The position's own reasoning, on the row that shows the position. Every
      // placement here is an argument — three of the eight named ones are derived
      // from bank geometry because no corner survives.
      const place = {
        confidence: p.position_confidence,
        sources: p.position_sources,
        note: p.position_note,
      };

      // WHAT THIS BUILDING IS CALLED (T-0076, the owner on 2026-08-18: "give the
      // locations useful names not technical D3 #03 names, you can have that somewhere
      // on the card for reference identity purposes but dont make it the title"). The
      // rule and its reasoning are in display-name.js; the production identity keeps
      // a line on the Record pane, because `Reconstructed D3 one-room frame cottage
      // #017` is what the parcel re-derives, what the GLB is named for, and what
      // somebody reading the dataset has in hand.
      const called = displayName(s, record.id);
      const spec = called.spec
        ? `<p class="pop-spec">Reconstruction reference
             <code>${escapeHtml(called.spec)}</code></p>`
        : '';

      // Empty when no dossier has been WRITTEN for this record — the compiler
      // resolves the path against the repository rather than naming one by
      // convention and hoping (ROADMAP K26). Offering a link that breaks taught a
      // visitor to distrust the ones that do not, so the sentence says which it is.
      const doc = s.research_doc
        ? `<a href="${escapeHtml(docBase + s.research_doc)}" target="_blank" rel="noopener">
             ${escapeHtml(s.research_doc)}</a>`
        : 'no dossier written for this building yet';

      // The liberties count on its tab, so a visitor can see there is something
      // to read before opening it. Null lists (not loaded) count as nothing, which
      // is the same "claim nothing" rule `libertySection` applies.
      const libertyCount = Array.isArray(liberties)
        ? libertiesFor(liberties, record.id).length : 0;
      const questionCount = Array.isArray(openQuestions)
        ? openQuestionsFor(openQuestions, record.id).length : 0;

      const evidencePane = `
        ${basisSection(s, place)}
        ${whereSection(p, place)}
        ${ordinanceSection(ordinanceLimits, p)}
        ${presenceSection(s)}
        ${shapeSection(s)}
        <section class="pop-sec">
          <h3>Attributes and evidence</h3>
          <table class="attrs"><tbody>${attributeRows(s.attributes)}</tbody></table>
        </section>
        <section class="pop-sec">
          <h3>Citations</h3>
          <ol class="cites">${citationItems(s.citations)}</ol>
        </section>`;

      const libertiesPane = `
        ${libertySection(liberties, record.id)}
        ${openQuestionSection(openQuestions, record.id)}`;

      const recordPane = `
        ${researchSection(s)}
        ${spec}
        <p class="pop-foot">Full dossier: ${doc}<br>
          Phase <code>${escapeHtml(s.phase ?? '—')}</code> ·
          record <code>${escapeHtml(record.id)}</code></p>`;

      root.innerHTML = `
        ${headHtml(s, record, called, p, place)}
        ${leadHtml(s, called, p)}
        ${factsHtml(s, firms, currentFromSign)}
        ${lodgingSection(s)}
        ${residentsSection(s)}
        ${agencySectionHtml(agencies, 'structure_id', record.id, escapeHtml)}
        ${tabsHtml({ liberties: libertyCount + questionCount })}
        ${paneHtml('evidence', evidencePane)}
        ${paneHtml('liberties', libertiesPane)}
        ${paneHtml('record', recordPane)}
      `;
      root.removeAttribute('hidden');
      // On a phone the sheet takes the lower screen and the building is framed into
      // the strip above it (T-0824); the map and compass would cover that strip.
      document.documentElement.classList.add('card-open');
      root.scrollTop = 0;
      return true;
    },
  };
}
