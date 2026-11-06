// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Haircuts, beards and moustaches for the portable humans (T-3414): the TABLE human-hair.js
 * grows strand cards from. Data only; no code reads a person here that human-hair.js does not.
 *
 * A cut is lengths (centimetres, at the top, the sides and the back of the head), a flow (the
 * way the hair is combed), a part and how far the hair stands off the scalp. A facial piece is
 * a region of the face, in centimetres from the middle of the eyes (x out to either side, y up,
 * z forward), and the length and fall of the hair grown there.
 *
 * Every person's choice is graded and carries its basis. No haircut, beard, colour or likeness
 * of any resident is claimed from a source unless the row cites one: these are reconstructed
 * choices for the person's year and work (liberty L418, its hair supplement).
 */

export const HAIR_CUTS = Object.freeze({
  // A working man's cut of about 1900: clipped short at the back and sides, longer on top and
  // combed from a side part across and back.
  short_side_part_1904: Object.freeze({
    flow: 'side_part', part_cm: 3.2, lengths_cm: Object.freeze({ top: 4.6, side: 1.5, back: 1.7 }),
    lift_mm: Object.freeze({ root: .8, tip: 2 }), density: 1.25, curl: .04, hang: false,
  }),
  // A woman's hair of the 1830s (T-3423): parted in the middle, drawn smooth and close over
  // the tops of the ears and back to a knot behind the head (the bun is in the body itself).
  centre_part_knot_1835: Object.freeze({
    flow: 'centre_part_back', part_cm: 0, lengths_cm: Object.freeze({ top: 7, side: 6, back: 5 }),
    knot_cm: Object.freeze({ up: 5, back: 12 }),
    lift_mm: Object.freeze({ root: .5, tip: 1.2 }), density: 1.3, curl: .03, hang: false,
  }),
  // A woman's hair of the 1900s (T-3423): drawn up from the face all round, full over the
  // brow and temples, to a knot high on the crown, as the 1903 Wasson stereographs show.
  swept_up_knot_1904: Object.freeze({
    flow: 'swept_up', part_cm: 0, lengths_cm: Object.freeze({ top: 8, side: 8, back: 7 }),
    knot_cm: Object.freeze({ up: 9, back: 9 }),
    lift_mm: Object.freeze({ root: 2.5, tip: 4 }), density: 1.3, curl: .05, hang: false,
  }),
  // Of the 1830s: fuller all round, brushed forward from the crown toward the brow and
  // temples, over the tops of the ears.
  brushed_forward_1835: Object.freeze({
    flow: 'forward', part_cm: 0, lengths_cm: Object.freeze({ top: 5.4, side: 3.2, back: 3.4 }),
    lift_mm: Object.freeze({ root: 1.6, tip: 4 }), density: 1.25, curl: .12, hang: true,
  }),
});

export const FACIAL_HAIR = Object.freeze({
  // A full moustache over the upper lip, falling a little at its ends (no one wears it yet).
  moustache: Object.freeze({
    region_cm: Object.freeze({ x: [0, 2.6], y: [-6.5, -5.3], z_min: .4, droop: .35 }), facing: 'front',
    length_cm: 1.05, fall: 1, outward: .3, lift_mm: Object.freeze({ root: 1.2, tip: 2.8 }), width_mm: 3, cover: 7, spread: .5,
  }),
  // Side whiskers: down from the temple in front of the ear to about the line of the mouth.
  side_whiskers: Object.freeze({
    region_cm: Object.freeze({ x: [5.8, 8.6], y: [-5.2, 1.2], z_min: -7.6, z_max: -3.6 }), facing: 'side',
    length_cm: .9, fall: 1, outward: 0, lift_mm: Object.freeze({ root: .6, tip: 1.4 }), width_mm: 3, cover: 8,
  }),
});

/** Linear RGB, as the cards' own colour (the scalp cap keeps its texture beneath). */
export const HAIR_COLOURS = Object.freeze({
  dark_brown: Object.freeze([.042, .026, .016]),
  mid_brown: Object.freeze([.062, .036, .020]),
});

/** What each era's people wear when their row names nothing. */
export const ERA_DEFAULT = Object.freeze({
  1835: Object.freeze({ cut: 'brushed_forward_1835', facial: Object.freeze([]), colour: 'mid_brown' }),
  1904: Object.freeze({ cut: 'short_side_part_1904', facial: Object.freeze([]), colour: 'dark_brown' }),
});

/** Per person, by the id their actor carries. */
export const PEOPLE_HAIR = Object.freeze({
  pa1904_otis_f_r_c1900_hans_johnson: Object.freeze({
    cut: 'short_side_part_1904', facial: Object.freeze([]), colour: 'dark_brown', grade: 'reconstructed',
    basis: 'Clean-shaven, with short hair showing below the hat, as the liveried coachmen of the people-match reference set are (coachman_1904: Rau 1902, Griffith 1905); the cut and the colour are reconstructed. No picture of Hans Johnson is known.',
  }),
  glessner_williamson_martha_l: Object.freeze({
    cut: 'swept_up_knot_1904', facial: Object.freeze([]), colour: 'dark_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice: a working woman of 1904 with her hair drawn up from the face to a knot on the crown, as the 1903 Wasson stereographs of a cook and a maid show. No picture of Martha Williamson has been read.',
  }),
  rc_flynn_mary: Object.freeze({
    cut: 'centre_part_knot_1835', facial: Object.freeze([]), colour: 'dark_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice for a working woman in the Chicago of 1835: hair parted in the middle, drawn smooth over the ears and pinned up in a knot behind, as women of the 1830s wore it. No picture of Mary Flynn is known.',
  }),
  rc_bardwell_otis: Object.freeze({
    cut: 'brushed_forward_1835', facial: Object.freeze(['side_whiskers']), colour: 'mid_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice for a teamster in the Chicago of 1835: hair worn fuller and brushed forward, side whiskers, the chin shaved. No picture of Otis Bardwell is known.',
  }),
});

/** The hair a person wears in a year: their own row, else their era's, else none. */
export function hairFor(personId, year) {
  const own = personId ? PEOPLE_HAIR[personId] : null;
  if (own) return own;
  const era = Object.keys(ERA_DEFAULT).map(Number).filter(y => Number.isFinite(year) && Math.abs(y - year) <= 20)
    .sort((a, b) => Math.abs(a - year) - Math.abs(b - year))[0];
  return era ? { ...ERA_DEFAULT[era], grade: 'reconstructed', basis: `The era default for ${era}.` } : null;
}
