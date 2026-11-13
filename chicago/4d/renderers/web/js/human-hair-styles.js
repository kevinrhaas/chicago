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
  // T-3553: Sarah Grey's hair as the owner's stand-in portrait shows it (a reconstructed
  // likeness, not a picture of her): the cleared bun hair drawn up from the face all round, its
  // bun turned up over the back of the head to sit as a knot high on the crown
  // (`bun_to_crown_deg`, human-hair.js bunToCrown). Like drawn_back_bun_1904 the cap carries its
  // own fine strands and grows no scalp cards; brows and lashes still grow from her face.
  swept_up_topknot_1904: Object.freeze({
    flow: 'swept_up', part_cm: 0, lengths_cm: Object.freeze({ top: 6, side: 5, back: 4 }),
    knot_cm: Object.freeze({ up: 10, back: 8 }), scalp_cards: false, bun_to_crown_deg: 62, bun_knot_scale: .7, cap_tint: Object.freeze([1.1, 1.3, 1.75]),
    lift_mm: Object.freeze({ root: .6, tip: 1.4 }), density: 1, curl: .04, hang: false,
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
  // T-3553: William L. Grey's hair as the owner's stand-in portrait shows it (a reconstructed
  // likeness, not a picture of him): thick and wavy, worn long over the ears to the collar and
  // swept straight back off a high forehead, with no parting, standing full at the sides.
  // T-3553, 2026-11-13: re-read from the owner's turnaround sheet of the stand-in: swept back
  // from the brow and falling in loose waves over the ears to below the jaw and the collar
  // behind, full at the sides.
  swept_back_wavy_1904: Object.freeze({
    flow: 'swept_back', part_cm: 0, lengths_cm: Object.freeze({ top: 11, side: 12.5, back: 15 }),
    lift_mm: Object.freeze({ root: 5, tip: 14 }), density: 5, curl: .35, hang: true, card_mm: 6.5, cap_tint: 12,
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
  // T-3506: the other ways the 1812 Potawatomi and Miami men and women wore long hair, so that
  // no two of a camp are alike (the owner, 2026-11-08). Each is the hair drawn back to a tie,
  // the tie set higher or lower, the parting moved; the hanging tail or club below the tie is
  // grown from the person's `tail_cm` (human-hair.js). Keating 1824 of Metea: "hair long and
  // tied or clubbed behind"; the 1826-37 Lewis and Winter portraits show partings and ties at
  // every height. Reconstructed choices, as all cuts here.
  tied_high_1812: Object.freeze({
    flow: 'centre_part_back', part_cm: 0, lengths_cm: Object.freeze({ top: 8, side: 8, back: 7 }),
    knot_cm: Object.freeze({ up: 2.5, back: 10.5 }),
    lift_mm: Object.freeze({ root: .7, tip: 1.8 }), density: 1.3, curl: .03, hang: false,
  }),
  clubbed_long_1812: Object.freeze({
    flow: 'centre_part_back', part_cm: 0, lengths_cm: Object.freeze({ top: 10, side: 10, back: 9 }),
    knot_cm: Object.freeze({ up: -6.5, back: 10 }),
    lift_mm: Object.freeze({ root: 1, tip: 2.6 }), density: 1.35, curl: .05, hang: false,
  }),
  side_part_tied_1812: Object.freeze({
    flow: 'side_part', part_cm: 2.6, lengths_cm: Object.freeze({ top: 8, side: 7, back: 7 }),
    knot_cm: Object.freeze({ up: -4.5, back: 10.5 }),
    lift_mm: Object.freeze({ root: .8, tip: 2 }), density: 1.3, curl: .04, hang: false,
  }),
  centre_part_low_1812: Object.freeze({
    flow: 'centre_part_back', part_cm: 0, lengths_cm: Object.freeze({ top: 9, side: 8, back: 8 }),
    knot_cm: Object.freeze({ up: -6, back: 10.5 }),
    lift_mm: Object.freeze({ root: .5, tip: 1.3 }), density: 1.35, curl: .02, hang: false,
  }),
  centre_part_tied_high_1812: Object.freeze({
    flow: 'centre_part_back', part_cm: 0, lengths_cm: Object.freeze({ top: 8, side: 8, back: 7 }),
    knot_cm: Object.freeze({ up: 1.5, back: 11 }),
    lift_mm: Object.freeze({ root: .6, tip: 1.4 }), density: 1.35, curl: .02, hang: false,
  }),
  // T-3520: the 1812 town's children (the owner, 2026-11-08: "their hair is short they all
  // look like boys"). A girl's hair worn longer than a boy's: parted in the middle, drawn back
  // over the ears and plaited at the nape, the plait hanging down her back (its length is the
  // person's `tail_cm`); or worn loose and curling to the shoulders. A little girl's to the neck; a boy's fuller
  // cut straight across the brow. Reconstructed choices (docs/RESEARCH/children-1812-3520).
  girl_plait_1812: Object.freeze({
    flow: 'centre_part_back', part_cm: 0, lengths_cm: Object.freeze({ top: 9, side: 9, back: 8 }),
    knot_cm: Object.freeze({ up: -6, back: 10 }),
    lift_mm: Object.freeze({ root: .6, tip: 1.5 }), density: 1.4, curl: .03, hang: false,
  }),
  girl_curls_1812: Object.freeze({
    flow: 'centre_part_down', part_cm: 0, lengths_cm: Object.freeze({ top: 10, side: 17, back: 22 }), card_mm: 5,
    lift_mm: Object.freeze({ root: 1.2, tip: 4 }), density: 3.4, curl: .18, hang: true,
  }),
  toddler_curls_1812: Object.freeze({
    flow: 'centre_part_down', part_cm: 0, lengths_cm: Object.freeze({ top: 7, side: 10, back: 12 }), card_mm: 4.5,
    lift_mm: Object.freeze({ root: 1.2, tip: 3.5 }), density: 3, curl: .25, hang: true,
  }),
  boy_fringe_1812: Object.freeze({
    flow: 'forward', part_cm: 0, lengths_cm: Object.freeze({ top: 4.6, side: 3, back: 3.2 }),
    lift_mm: Object.freeze({ root: 1.2, tip: 3 }), density: 1.3, curl: .08, hang: true,
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
  // Captioned 1902 portraits of Buckingham and Otis: a short full chin beard.
  // Its extent is reconstructed from one view, not a measured grooming record.
  beard_short: Object.freeze({
    region_cm: Object.freeze({ x: [0, 6.8], y: [-14, -8.5], z_min: -2.5 }), facing: 'front',
    length_cm: 2.1, fall: 1, outward: .25, lift_mm: Object.freeze({ root: 1, tip: 3 }), width_mm: 2.2, cover: 8, spread: .55,
  }),
  // T-3553: the full beard of William L. Grey's stand-in portrait, trimmed to about 2.5 cm and
  // rounded at the chin, over the chin, the jaw and the lower cheeks (`beard_full_1904`), over
  // the front of the cheeks (`beard_cheeks_front_1904`), and up the sides of the face to the
  // hair (`beard_cheeks_1904`). The owner (2026-11-13: "the beards in particular could be
  // improved significantly"): fine hairs in their thousands, not slabs, each turned its own
  // way and curling (`jitter_deg`, `curl`), standing off the skin to the beard's depth
  // (`loft`), a share of them grey (`grey`, the portrait's paler streaks), and thinning to
  // stubble up the cheeks and down the throat (`feather_cm`) as the portrait's does. And
  // (2026-11-13: "his lips are covered with hair and there is no space around his chin … look
  // at the beard line"): the lower lip and the skin under it stay clear, the beard's roots
  // starting below them (`top`), and its line runs up the cheek on the portrait's diagonal,
  // from the moustache's ends at the corners of the mouth to the sideburns before the ears.
  beard_full_1904: Object.freeze({
    region_cm: Object.freeze({ x: [0, 6.4], y: [-15, -6.4], z_min: -3.8, top: [[0, -9.2], [1.9, -9.15], [2.8, -8.5], [3.3, -8.1], [4.5, -7.1], [6.4, -5.4]] }), facing: 'front',
    length_cm: 3.8, fall: 1, outward: .03, lift_mm: Object.freeze({ root: 1.1, tip: 3.2 }), width_mm: 1, cover: 20, spread: .6, curl: .5,
    jitter_deg: 28, loft: 1.4, grey: .22, feather_cm: Object.freeze({ top: .5, bottom: 1.6 }),
  }),
  // The sides: from the jaw up the cheek's diagonal line to the sideburns before the ears,
  // where the long hair hangs over them.
  beard_cheeks_1904: Object.freeze({
    region_cm: Object.freeze({ x: [5, 8.6], y: [-13.5, 1], z_min: -7.6, z_max: -.3, top: [[5, -6.6], [6, -5.6], [7, -4.4], [7.8, -2.4], [8.6, -1]] }), facing: 'side',
    length_cm: 1.1, fall: 1, outward: .06, lift_mm: Object.freeze({ root: .7, tip: 2.2 }), width_mm: .9, cover: 16, spread: .6, curl: .45,
    jitter_deg: 32, loft: 1, grey: .2, feather_cm: Object.freeze({ top: 1.8, out: 1.4 }),
  }),
  // The front of the cheeks, below the line from the corners of the moustache out and up
  // toward the ears, where the face still looks forward and the side piece takes no roots.
  beard_cheeks_front_1904: Object.freeze({
    region_cm: Object.freeze({ x: [3, 6.6], y: [-10, -5.6], z_min: -3, top: [[3.3, -8.1], [4.5, -7.1], [6, -5.6], [6.6, -5]] }), facing: 'front',
    length_cm: 1.5, fall: 1, outward: .2, lift_mm: Object.freeze({ root: .9, tip: 3 }), width_mm: .9, cover: 16, spread: .6, curl: .45,
    jitter_deg: 32, loft: 1, grey: .18, feather_cm: Object.freeze({ top: 1.8 }),
  }),
  // His moustache, as the portrait shows it: thick and bristling, rooted between the nose and
  // the lip and falling over the upper lip to the line of the mouth (the lower lip shows
  // under it), its ends past the corners of the mouth into the beard, sandy with grey.
  moustache_heavy_1904: Object.freeze({
    region_cm: Object.freeze({ x: [0, 3.9], y: [-7.6, -6.2], z_min: .1, droop: .9 }), facing: 'front',
    length_cm: 1.05, fall: 1, outward: .35, lift_mm: Object.freeze({ root: 1.4, tip: 3.6 }), width_mm: .9, cover: 24, spread: .5, curl: .3,
    jitter_deg: 20, loft: .7, grey: .15, feather_cm: Object.freeze({ top: .5 }),
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
  // T-3553: the brows as the Greys' stand-in portraits set them, measured against the eyes on
  // the portrait and on a render of the fitted face by the same landmark model: Sarah's fine
  // brows sit 1.25 cm lower over the eyes than brows_fine draws them on the lady's body, and
  // William's full brows 0.7 cm lower than brows_full, on the brow bone close over the eyes as his
  // turnaround sheet shows them (re-measured 2026-11-13 on the faces refitted to the side views).
  brows_fine_low_1904: Object.freeze({
    region_cm: Object.freeze({ x: [1.3, 4.6], y: [.27, .67], z_min: -1.5, droop: .55 }), facing: 'front',
    length_cm: .45, fall: -.1, fall_ends: Object.freeze([-1, .35]), outward: 1, taper: .35, curl: .04, even: .7, exact: true,
    lift_mm: Object.freeze({ root: .12, tip: .25 }), width_mm: .55, cover: 2.2, spread: .3,
  }),
  // His are drawn hair by hair, spaced evenly and lying flatter (`even`, `exact`), so they read
  // as the portrait's soft sandy brows rather than a painted band.
  brows_full_high_1904: Object.freeze({
    region_cm: Object.freeze({ x: [1.1, 5], y: [.75, 1.5], z_min: -1.8, droop: .6 }), facing: 'front',
    length_cm: .7, fall: -.05, fall_ends: Object.freeze([-.8, .4]), outward: 1, taper: .3, curl: .08, even: .7, exact: true,
    lift_mm: Object.freeze({ root: .15, tip: .45 }), width_mm: .5, cover: 3.2, spread: .45, jitter_deg: 10,
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
  // T-3506: black hair is not one black. A cooler blue-black, and a black with brown in it in
  // the sun, so a camp's heads are not one colour.
  blue_black: Object.freeze([.008, .009, .012]),
  black_brown: Object.freeze([.022, .015, .011]),
  fair: Object.freeze([.30, .21, .11]),
  sandy: Object.freeze([.25, .13, .06]),
  red: Object.freeze([.20, .065, .025]),
  // White going grey (T-3440): an old man's hair, a little warm, not paper white.
  white_grey: Object.freeze([.44, .41, .36]),
  // Brown going grey at 56 (T-3483, Charles Nelson): mid brown with grey through it.
  grey_brown: Object.freeze([.15, .12, .095]),
  // Sandy brown going grey (T-3553, William L. Grey's stand-in): a light brown with red in it
  // and grey through it, as the sepia portrait's mid tone with paler streaks reads.
  sandy_grey: Object.freeze([.2, .135, .085]),
  // Re-read from the owner's turnaround sheets (T-3553, 2026-11-13), which are in colour: his
  // hair a mid-to-dark brown, grey through it and at the temples; his beard a grizzled russet,
  // the moustache warmest and the chin greyest.
  ash_brown_grey: Object.freeze([.12, .095, .078]),
  grizzled_russet: Object.freeze([.3, .2, .14]),
  // His beard and moustache (T-3553): warmer than his hair, a reddish sand, as the portrait's
  // beard reads a shade redder and lighter than the hair above it.
  sandy_red: Object.freeze([.26, .14, .075]),
  // Light brown going grey (T-3553, Sarah Grey's stand-in): a light brown with grey through it,
  // as the sepia portrait's hair reads, paler streaks in a mid tone.
  light_grey_brown: Object.freeze([.2, .14, .095]),
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
  // T-3553: William Grey's beard is warmer and greyer than his hair, as the owner's colour turnaround sheet
  // of the stand-in shows; the looks record (tools/prairie_people.py) gives his cut, beard and hair colour.
  pa1904_grey_w_l: Object.freeze({
    cut: 'swept_back_wavy_1904', facial: Object.freeze([]), colour: 'ash_brown_grey', brow_colour: 'grizzled_russet', grade: 'reconstructed',
    basis: 'Read from the owner\'s colour turnaround sheet of his stand-in (2026-11-13): hair brown going grey, beard and moustache a grizzled russet. Colours of a stand-in, not a record.',
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
