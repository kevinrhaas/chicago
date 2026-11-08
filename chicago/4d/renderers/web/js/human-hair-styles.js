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
  // A woman's hair of the 1900s worn as a real bun (T-3434): her cap is a cleared bun hair
  // (hair_bun_brown) drawn back from the face to a bun at the back of the head, whose own
  // painted strands read finer than cards would, so it grows no scalp cards (brows and lashes
  // still grow from her face).
  drawn_back_bun_1904: Object.freeze({
    flow: 'swept_up', part_cm: 0, lengths_cm: Object.freeze({ top: 6, side: 5, back: 4 }),
    knot_cm: Object.freeze({ up: 5.5, back: 17 }), scalp_cards: false,
    lift_mm: Object.freeze({ root: .6, tip: 1.4 }), density: 1, curl: .04, hang: false,
  }),
  // An older man's fringe of about 1900 (T-3440, John J. Glessner): the crown bald from the
  // brow back over the top; short hair left at the sides and around the back, brushed back and
  // a little full over the ears, as his 1897 portrait plate shows it. `bald` keeps hair only
  // below a line `side_cm` above the eyes at the temples, rising to `back_cm` behind, and
  // none forward of `front_z_cm` (centimetres in the face's frame, as the facial regions).
  bald_crown_fringe_1904: Object.freeze({
    flow: 'side_part', part_cm: 3, lengths_cm: Object.freeze({ top: 1.4, side: 1.8, back: 1.5 }),
    bald: Object.freeze({ side_cm: 3.6, back_cm: 3.9, front_z_cm: -2.8 }), card_mm: 2.6,
    lift_mm: Object.freeze({ root: .5, tip: 1.4 }), density: 3.2, curl: .06, hang: false,
  }),
  // A soldier's crop of 1812 (T-3491, a reconstructed choice): short all round, a little
  // longer on top and brushed forward to the brow, close over the ears and at the nape.
  cropped_1812: Object.freeze({
    flow: 'forward', part_cm: 0, lengths_cm: Object.freeze({ top: 3.2, side: 1.3, back: 1.5 }),
    lift_mm: Object.freeze({ root: 1, tip: 2.6 }), density: 1.3, curl: .1, hang: false,
  }),
  // Worn long and drawn back to be tied or clubbed at the nape (T-3463..T-3467): the
  // Potawatomi and Miami men of 1812 ("hair long and tied or clubbed behind", Keating 1824 of
  // Metea) and the older men of the post who kept a queue (John Kinzie). The tie is where the
  // strands meet, low behind the head; the tail itself is not grown.
  clubbed_behind_1812: Object.freeze({
    flow: 'centre_part_back', part_cm: 0, lengths_cm: Object.freeze({ top: 8, side: 7, back: 8 }),
    knot_cm: Object.freeze({ up: -4, back: 11 }),
    lift_mm: Object.freeze({ root: .6, tip: 1.6 }), density: 1.3, curl: .02, hang: false,
  }),
  // A woman's of 1812 (T-3464, T-3467): parted in the middle and worn long, drawn smooth back
  // over the ears to be tied or clubbed low at the back of the head.
  centre_part_clubbed_1812: Object.freeze({
    flow: 'centre_part_back', part_cm: 0, lengths_cm: Object.freeze({ top: 8, side: 7, back: 7 }),
    knot_cm: Object.freeze({ up: -2, back: 12 }),
    lift_mm: Object.freeze({ root: .5, tip: 1.2 }), density: 1.35, curl: .02, hang: false,
  }),
  // Of the 1830s: fuller all round, brushed forward from the crown toward the brow and
  // temples, over the tops of the ears.
  brushed_forward_1835: Object.freeze({
    flow: 'forward', part_cm: 0, lengths_cm: Object.freeze({ top: 5.4, side: 3.2, back: 3.4 }),
    lift_mm: Object.freeze({ root: 1.6, tip: 4 }), density: 1.25, curl: .12, hang: true,
  }),
});

export const FACIAL_HAIR = Object.freeze({
  // A full moustache over the upper lip, falling a little at its ends (August Billings, T-3484).
  moustache: Object.freeze({
    region_cm: Object.freeze({ x: [0, 2.6], y: [-6.5, -5.3], z_min: .4, droop: .35 }), facing: 'front',
    length_cm: 1.05, fall: 1, outward: .3, lift_mm: Object.freeze({ root: 1.2, tip: 2.8 }), width_mm: 3, cover: 7, spread: .5,
  }),
  // A full moustache (T-3440, Glessner's in his 1897 plate): thick over the whole upper lip
  // and down over its edge, its ends drooping past the corners of the mouth.
  moustache_full: Object.freeze({
    region_cm: Object.freeze({ x: [0, 3.7], y: [-8.6, -6.8], z_min: .1, droop: .9 }), facing: 'front',
    length_cm: 1.6, fall: 1, outward: .5, lift_mm: Object.freeze({ root: 1.8, tip: 4 }), width_mm: 3, cover: 13, spread: .5,
  }),
  // An older man's brows (T-3440): fuller and coarser than brows_fine, a few hairs straying.
  brows_full: Object.freeze({
    region_cm: Object.freeze({ x: [1.1, 5], y: [1.45, 2.2], z_min: -1.8, droop: .6 }), facing: 'front',
    length_cm: .75, fall: -.05, outward: 1, lift_mm: Object.freeze({ root: .3, tip: .9 }), width_mm: .5, cover: 4.5, spread: .7,
  }),
  // Fine arched eyebrows (T-3434): short hairs combed out from the nose along the brow
  // bone, a little up at the inner end, the tail falling toward the temple. Without them a
  // face reads bare and hard at 3 m.
  // T-3456 (owner, 2026-11-07: "super clumpy bunchy"): roots kept point by point and spaced evenly, the hairs
  // turning from up at the nose to down at the tail and shorter toward it, wider soft cards
  // lifted clear of the skin, and a straighter lay, so the brow reads as one smooth band.
  // T-3493 (owner, 2026-11-07, of Frances: "they are dark and dont look good"): sparser, finer
  // and lying flatter to the skin, so the brow reads as a soft band, not a pen stroke.
  brows_fine: Object.freeze({
    region_cm: Object.freeze({ x: [1.3, 4.6], y: [1.5, 1.9], z_min: -1.5, droop: .55 }), facing: 'front',
    length_cm: .45, fall: -.1, fall_ends: Object.freeze([-1, .35]), outward: 1, taper: .35, curl: .04, even: .7, exact: true,
    lift_mm: Object.freeze({ root: .12, tip: .25 }), width_mm: .55, cover: 2.2, spread: .3,
  }),
  // Upper lashes (T-3434): a short dark fringe along the upper lid, swept out and up. At 3 m
  // it reads as the dark line that makes an eye look open and soft rather than bare.
  // T-3493 (owner, 2026-11-07: "look like they are double eyebrows ... her eyelashes dont
  // move"): rooted on the upper lid's own edge, `per_cm` of it, and standing free of the skin,
  // out from the edge and curling `rise` radians up, swept out by `splay` toward the outer
  // corner, rather than combed up over the lid (a dark band a few millimetres above the eye,
  // read as a second brow). They shut with the lid (human-hair.js facialMorphs).
  lashes_upper: Object.freeze({
    lid: 'upper', per_cm: 70, length_cm: .55, width_mm: .3, rise: 1, splay: .35,
  }),
  // Short side whiskers of the 1810s (T-3491): from the temple to about the ear's lobe, cut close.
  side_whiskers_short: Object.freeze({
    region_cm: Object.freeze({ x: [5.9, 8.4], y: [-2.6, 1.2], z_min: -7.4, z_max: -3.9 }), facing: 'side',
    length_cm: .55, fall: 1, outward: 0, lift_mm: Object.freeze({ root: .4, tip: 1 }), width_mm: 2.4, cover: 7,
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
  // A light brown (T-3493): brows a shade lighter than a cleared bun hair's own texture, as
  // light brows read in a photograph of a fair-haired woman (Frances Glessner's, 1892).
  // The 1812 registers' "light" hair (T-3491) takes it too.
  light_brown: Object.freeze([.22, .145, .095]),
  // The registers' other words for hair (T-3491), each a linear colour: black, fair, sandy
  // (a reddish fair) and red.
  black: Object.freeze([.012, .010, .009]),
  fair: Object.freeze([.30, .21, .11]),
  sandy: Object.freeze([.25, .13, .06]),
  red: Object.freeze([.20, .065, .025]),
  // White going grey (T-3440): an old man's hair, a little warm, not paper white.
  white_grey: Object.freeze([.44, .41, .36]),
  // Brown going grey at 56 (T-3483, Charles Nelson): mid brown with grey through it.
  grey_brown: Object.freeze([.15, .12, .095]),
  // Ash fair (T-3484, August Billings): a Swede's light brown-blond, cool rather than golden.
  ash_blond: Object.freeze([.24, .18, .11]),
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
  glessner_john_j: Object.freeze({
    cut: 'bald_crown_fringe_1904', facial: Object.freeze(['moustache_full', 'brows_full']), colour: 'white_grey', grade: 'attested',
    source_id: 'glessner_commercial_club_1910_presidents_plate',
    basis: 'His 1897 portrait plate (The Commercial Club of Chicago, 1910, p. 81) shows the crown bald, short white hair at the sides and back, a full moustache over the upper lip and full brows. The colour, white going grey, is read from the plate\'s light tone (a monochrome halftone) and his age; lengths and fullness are fitted to the plate by eye. Seven years on, in 1904, he is drawn as the plate shows him.',
  }),
  glessner_williamson_martha_l: Object.freeze({
    cut: 'drawn_back_bun_1904', facial: Object.freeze(['brows_fine', 'lashes_upper']), colour: 'mid_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice: a working woman of 1904 with her hair drawn back from the face to a bun, as the 1903 Wasson stereographs of a cook and a maid show. No picture of Martha Williamson has been read.',
  }),
  glessner_frances_m: Object.freeze({
    cut: 'drawn_back_bun_1904', facial: Object.freeze(['brows_fine', 'lashes_upper']), colour: 'mid_brown', brow_colour: 'light_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice: a lady of 56 in 1904 with her hair drawn up from the face to a knot behind, under her hat, as the women of the 1905 Johnston photograph and the 1904 Easter crowd wear it (lady_1904 reference set). Her 1892 conservatory photograph (Chicago History Museum, ICHi-061818) shows her hair drawn back from the face and her brows light and fine, barely darker than her skin; the brows are drawn a light brown for that (T-3493). Whether her hair was grey by 1904 is not recorded, and the cleared bun hair keeps its brown.',
  }),
  pa1904_glessner_john_j_c1900_mary_reynolds: Object.freeze({
    cut: 'drawn_back_bun_1904', facial: Object.freeze(['brows_fine', 'lashes_upper']), colour: 'dark_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice: a house maid of 1904 with her hair drawn up from the face to a knot on the crown, under her cap, as the 1904 Kelley maid and the 1903 Wasson cook wear it (maid_1904 reference set). No picture of Mary Reynolds is known.',
  }),
  pa1904_glessner_john_j_c1900_kate_ryan: Object.freeze({
    cut: 'drawn_back_bun_1904', facial: Object.freeze(['brows_fine', 'lashes_upper']), colour: 'grey_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice: an Irish cook of 54 in 1904 with her hair drawn up from the face and covered by a cloth bound over it, as the older cook of the 1903 Wasson stereograph wears hers (cook_1904). Her brows are drawn brown going grey for her age; the cleared bun hair under the cloth keeps its brown. No picture of Kate Ryan is known.',
  }),
  pa1904_glessner_john_j_c1900_christine_nelson: Object.freeze({
    cut: 'drawn_back_bun_1904', facial: Object.freeze(['brows_fine', 'lashes_upper']), colour: 'mid_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice: a parlor maid of 31 in 1904 out on an errand, her hair drawn up from the face to a knot under a straw sailor hat, as the women of Shinn\'s 1904 drawing and the 1909 shirtwaist strikers wear theirs (errand_1904). She was born in Sweden, but no colour of her hair is recorded: the cleared bun hair keeps its brown and her brows match it. No picture of Christine Nelson is known.',
  }),
  rc_flynn_mary: Object.freeze({
    cut: 'centre_part_knot_1835', facial: Object.freeze(['brows_fine', 'lashes_upper']), colour: 'dark_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice for a working woman in the Chicago of 1835: hair parted in the middle, drawn smooth over the ears and pinned up in a knot behind, as women of the 1830s wore it. No picture of Mary Flynn is known.',
  }),
  rc_bardwell_otis: Object.freeze({
    cut: 'brushed_forward_1835', facial: Object.freeze(['side_whiskers']), colour: 'mid_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice for a teamster in the Chicago of 1835: hair worn fuller and brushed forward, side whiskers, the chin shaved. No picture of Otis Bardwell is known.',
  }),
  pa1904_glessner_john_j_c1900_charles_nelson: Object.freeze({
    cut: 'short_side_part_1904', facial: Object.freeze(['brows_full']), colour: 'grey_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice for a Swedish coachman of 56 in 1904: short hair parted at the side under his hat, brown going grey, full brows, and clean-shaven, as the liveried coachmen of the Seely plates (1902), the older man in mourning livery among them, and of the coachman_1904 set are. No picture of Charles Nelson is known.',
  }),
  pa1904_glessner_john_j_c1900_august_billings: Object.freeze({
    cut: 'short_side_part_1904', facial: Object.freeze(['moustache']), colour: 'ash_blond', grade: 'reconstructed',
    basis: 'A reconstructed choice for a Swedish stable helper of 29 in 1904: short hair parted at the side, ash fair, and a moustache, as working men of the decade commonly wore one; a stable hand was not held to the livery\'s clean shave. No picture of August Billings is known.',
  }),
  peck_philip: Object.freeze({
    cut: 'brushed_forward_1835', facial: Object.freeze(['side_whiskers']), colour: 'dark_brown', grade: 'reconstructed',
    basis: 'A reconstructed choice for a merchant of 1835: hair brushed forward at the temples and short side whiskers, the chin shaved, as Durand painted the New York merchant Luman Reed that year (merchant_1835 reference set). No picture of Philip F. W. Peck has been read.',
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
