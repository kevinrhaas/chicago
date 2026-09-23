/**
 * seat.js — the address book's seat, said in words and offered as a destination.
 *
 * WHY THIS EXISTS. T-1491 wrote `data/reconstruction/1835_address_book.json`:
 * one row per household and per firm, seated at the rung its evidence reaches —
 * a named roof, a lot the plat holds, a block face of the street the paper
 * names, a division band, or nothing at all. The person card printed that row
 * in words from the day it landed. Nothing could GO there.
 *
 * That asymmetry had a measurable cost, and it fell on exactly the rows the
 * address book was built for. A firm the paper reaches to a street and no
 * further is housed by the street-face adoption on a block-face roof — 40 of
 * them on 21 September 2026 — and its card said "South Water Street", said the
 * housing was substitutable, and stopped. The visitor read where the house
 * stood and had no way to stand there. Meanwhile the 45 firms with a roof of
 * their own had a button, because a roof is what the button keyed on. So the
 * town was walkable exactly where the evidence was strongest and unwalkable
 * everywhere else, which inverts what this project is for: the weaker rungs are
 * the ones a visitor most needs shown, because they are the ones a reader will
 * otherwise assume are absences in the TOWN rather than in the RECORD.
 *
 * WHAT IT REFUSES. The button is offered for a seat and never for a reach. A
 * row that reaches a division and is not seated has nowhere to send anybody,
 * and this module says so rather than dealing a plausible roof: that is the
 * `owed` rung, and its seat is another ticket's to write. A seat this scene has
 * not loaded gets no button either — the caller passes `goable`, which it
 * decides against the structure registry, so a seat naming a roof the build has
 * not raised reads as words alone instead of a dead control.
 *
 * AND IT NEVER RE-GRADES. The verb changes with the rung — "the lot", "the
 * block face", "the seat the policy dealt it" — precisely so that arriving
 * somewhere cannot be mistaken for the record having put the house there. The
 * words under the button are `row.words`, written where the seat was dealt, and
 * the line under those is what would move it up the ladder.
 *
 * T-1493 (piece 3 of T-1198). Both the person card and the business card read
 * this, which is why it is a module and not a function in either of them.
 */

import { escapeHtml } from './citations.js';

/** The rung, as a card's heading says it. Derived here rather than carried in
 *  the file, because it is a LABEL and not a reading — the reading is
 *  `row.words`, written where the seat was dealt. */
const RUNG_LABEL = {
  structure: () => 'Seated at a named roof',
  lot: () => 'Placed on a lot the plat holds',
  face: (row) => `Housed on a face of ${row.reach_value || 'its street'}`,
  // T-1512. The division is the record's; the band inside it is the placement
  // policy's, and the label says which of the two a reader is looking at.
  division_band: (row) => (row.seat && row.seat.clause
    ? `Banded in the ${row.reach_value} division, on the policy's ground for its trade`
    : `Banded in the ${row.reach_value} division, and no class dealt`),
  // T-1522. The weakest seat this ladder makes, and the label must not let it
  // pass for the rung above. There the division is the household's own record
  // and only the ground inside it is drawn; here BOTH halves are dealt, off the
  // order book's household shape and the town model's employment distribution.
  policy_only: (row) => (row.seat && row.seat.division
    ? `Dealt a place in the ${row.seat.division} division, on nothing its record says`
    : 'Dealt a place, on nothing its record says'),
  unplaceable: () => 'Not seated in this town',
};

export function rungLabel(row) {
  const known = RUNG_LABEL[row.rung];
  if (known) return known(row);
  if (row.reach === 'division') return `Reaches the ${row.reach_value} division, and no nearer`;
  if (row.reach === 'face') return `Reaches ${row.reach_value}, and no nearer`;
  if (row.reach === 'structure_owed') return 'Reaches a roof this town has not built';
  return 'No source places this household';
}

/** What the button promises, which is the RUNG and never the evidence. Going to
 *  a block face must not read like going to an address. */
const GO_VERB = {
  structure: 'Go to the roof it is seated at',
  lot: 'Go to the lot it is seated on',
  face: 'Go to the block face it is housed on',
  division_band: 'Go to where the policy seats it',
  policy_only: 'Go to where the policy seats it',
};

export function seatVerb(row) {
  return GO_VERB[row?.rung] || 'Go to the seat';
}

/** The seat a row can be carried to, or null. `works_seat` is the fallback so a
 *  firm or a household seated only at its workplace still has somewhere to go. */
export function seatTarget(row) {
  const seat = row?.seat || row?.works_seat || null;
  // Only a seat naming a structure is somewhere to stand today. A lot or a band
  // seat is a rung T-1492 introduces; when it does, the walk has to learn to
  // frame one before this offers it, and until then words are the honest answer.
  if (!seat || seat.kind !== 'structure' || !seat.id) return null;
  return seat;
}

/**
 * The seat block a card prints: the button where there is one, then the rung,
 * the words the seat was dealt in, and what would replace it.
 *
 * @param {object} row               the address-book row
 * @param {object} [o]
 * @param {string|null} [o.title]    the seat's own title, as the scene names it
 * @param {boolean} [o.goable]       whether the scene actually holds that seat
 * @param {string}  [o.extraClass]   a class the calling card styles it by
 */
export function seatHtml(row, { title = null, goable = false, extraClass = '' } = {}) {
  if (!row) return '';
  const target = seatTarget(row);
  const button = target && goable
    ? `<button type="button" class="people-go biz-go seat-go" data-go="seat"
        data-structure="${escapeHtml(target.id)}"
        title="${escapeHtml(row.replaceable_by ? `Would move it up the ladder: ${row.replaceable_by}` : '')}">
        <span class="people-go-verb">${escapeHtml(seatVerb(row))}</span>
        <span class="people-go-title">${escapeHtml(title || target.id)}</span>${
  row.seat_is_substitutable
    ? '<span class="seat-go-sub">housing, not a reading — substitutable</span>'
    : ''}</button>`
    : '';
  const owed = row.owed_to
    ? `<span class="people-seat-owed">The seat is owed to ${escapeHtml(row.owed_to)}.</span>`
    : '';
  return `${button}<p class="people-seat${extraClass ? ` ${extraClass}` : ''}" data-rung="${escapeHtml(row.rung)}">
      <span class="people-seat-rung">${escapeHtml(rungLabel(row))}</span>
      <span class="people-seat-words">${escapeHtml(row.words)} ${owed}</span>
      <span class="people-seat-next">Would move it up the ladder: ${escapeHtml(row.replaceable_by)}.</span></p>`;
}
