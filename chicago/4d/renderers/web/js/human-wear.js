// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-wear.js — how a body's plain clothes are worn: the colours of its cloth, what is set aside
 * and the hat, by name (T-3553).
 *
 * Kevin, 2026-11-27, of the 1904 working man's clothes ("A sack coat, a waistcoat and trousers,
 * with a cap"): "That outfit as described does not look very good ... provide better coloring
 * and more options and more people with more clothing options", "And fix any people with that
 * clothes". The body anonymous_working_driver_1904 came with a tan linen shirt and a pale grey
 * waistcoat over pale trousers, and no hat: at any distance a knit suit. Worn here as a working
 * man of the time is photographed: a collarless shirt gone to oatmeal, a dark wool waistcoat and
 * trousers, a flat cap (human-hats.js 'cap'); and, on the 1904 gentleman's body with its coat's
 * skirts set aside, the short coat over them (`working_coat_1904`).
 *
 * A wear has `base` (a dress as human-looks.js dressCloth and human-hats.js dressHat read it) and
 * `looks`: colourings one of which each person wears, picked by their key, so a crowd is not one
 * suit. A body named in ASSET_WEAR wears its wear unless its figure says otherwise
 * (`appearance.wear`: another wear's id, or null for none); a recorded person's own dress is
 * laid over it (mergeDress). Colours and their cut are reconstructed (docs/LIBERTIES.md L-wear-3553):
 * period working dress in the run of photographs of Chicago streets of 1890-1910, no garment of
 * anyone claimed.
 */

const SHIRT_OAT = Object.freeze([0.42, 0.395, 0.34]);
const SHIRT_GREY = Object.freeze([0.3, 0.3, 0.29]);
const SHIRT_BLUE = Object.freeze([0.2, 0.24, 0.3]);
const BROWN = Object.freeze([0.042, 0.032, 0.024]);
const CHARCOAL = Object.freeze([0.03, 0.03, 0.032]);
const TWEED = Object.freeze([0.12, 0.1, 0.07]);
const CAP_TWEED = Object.freeze([0.07, 0.06, 0.045]);
const OLIVE = Object.freeze([0.04, 0.042, 0.03]);
const NAVY = Object.freeze([0.022, 0.026, 0.04]);
const DARK = Object.freeze([0.026, 0.024, 0.022]);
const GREY = Object.freeze([0.06, 0.06, 0.062]);
const BOOT = Object.freeze([0.03, 0.02, 0.014]);
const HORN = Object.freeze([0.02, 0.016, 0.012]);
const GLOVE = Object.freeze([0.06, 0.04, 0.025]);
const LINEN = Object.freeze([0.62, 0.6, 0.55]);
const SERGE_BLUE = Object.freeze([0.03, 0.04, 0.075]);
const PLUM = Object.freeze([0.05, 0.022, 0.034]);
const BOTTLE = Object.freeze([0.02, 0.04, 0.03]);
const DOVE = Object.freeze([0.16, 0.155, 0.15]);
const CALICO = Object.freeze([0.09, 0.12, 0.19]);
const MADDER = Object.freeze([0.15, 0.045, 0.04]);
const BUTTERNUT = Object.freeze([0.2, 0.13, 0.07]);

const cap = (rgb) => Object.freeze({ kind: 'cap', rgb: rgb === TWEED ? CAP_TWEED : rgb });

export const WEARS = Object.freeze({
  // The shirt-and-waistcoat body (anonymous_working_driver_1904): every working man, groom and
  // watcher who wears it.
  working_1904: Object.freeze({
    label: 'Shirt and waistcoat',
    worn: 'A collarless shirt, a wool waistcoat and trousers, with a flat cap.',
    base: Object.freeze({
      colours: Object.freeze({ garment_upper__shirt_linen: SHIRT_OAT, garment_outer__waistcoat_wool: BROWN,
        garment_lower__highwaist_pantaloons: DARK, footwear__closed_leather_shoes: BOOT }),
      hat: cap(TWEED),
    }),
    looks: Object.freeze([
      Object.freeze({ id: 'brown', label: 'Brown', colours: { garment_outer__waistcoat_wool: BROWN, garment_lower__highwaist_pantaloons: DARK }, hat: cap(TWEED) }),
      Object.freeze({ id: 'charcoal', label: 'Charcoal', colours: { garment_outer__waistcoat_wool: CHARCOAL, garment_lower__highwaist_pantaloons: GREY, garment_upper__shirt_linen: SHIRT_GREY }, hat: cap(CHARCOAL) }),
      Object.freeze({ id: 'tweed', label: 'Tweed', colours: { garment_outer__waistcoat_wool: TWEED, garment_lower__highwaist_pantaloons: BROWN }, hat: cap(BROWN) }),
      Object.freeze({ id: 'navy', label: 'Navy', colours: { garment_outer__waistcoat_wool: NAVY, garment_lower__highwaist_pantaloons: DARK, garment_upper__shirt_linen: SHIRT_BLUE }, hat: cap(NAVY) }),
    ]),
  }),
  // The coat and cap of the photographs (Kevin's picture, 2026-11-27): the 1904 gentleman's body
  // (glessner_john_j_1904) with the frock coat's skirts, the tie and the derby set aside, its
  // body a short coat over the waistcoat, all in a working man's wool.
  working_coat_1904: Object.freeze({
    label: 'Coat and cap',
    worn: 'A short wool coat over a waistcoat and a collarless shirt, dark trousers and a flat cap.',
    base: Object.freeze({
      hide: Object.freeze(['frock_coat_skirts', 'four_in_hand_tie', 'headwear_derby']),
      colours: Object.freeze({ garment_outer__frock_coat_black: BROWN, garment_upper__shirt_linen_1904: SHIRT_OAT,
        garment_lower__trousers_grey_1904: DARK, footwear__black_boots: BOOT }),
      hat: cap(TWEED),
    }),
    looks: Object.freeze([
      Object.freeze({ id: 'brown', label: 'Brown', colours: { garment_outer__frock_coat_black: BROWN, garment_lower__trousers_grey_1904: DARK }, hat: cap(TWEED) }),
      Object.freeze({ id: 'charcoal', label: 'Charcoal', colours: { garment_outer__frock_coat_black: CHARCOAL, garment_lower__trousers_grey_1904: GREY }, hat: cap(CHARCOAL) }),
      Object.freeze({ id: 'tweed', label: 'Tweed', colours: { garment_outer__frock_coat_black: TWEED, garment_lower__trousers_grey_1904: BROWN }, hat: cap(BROWN) }),
      Object.freeze({ id: 'olive', label: 'Olive', colours: { garment_outer__frock_coat_black: OLIVE, garment_lower__trousers_grey_1904: DARK }, hat: cap(OLIVE) }),
      Object.freeze({ id: 'navy', label: 'Navy', colours: { garment_outer__frock_coat_black: NAVY, garment_lower__trousers_grey_1904: CHARCOAL }, hat: cap(NAVY) }),
    ]),
  }),

  // The dresses the visitor may choose (data/humans/visitor_person.json `dress.wear`), each in
  // the colourings its cloth was worn in. Worn only where an outfit names them: the town's people
  // in these bodies keep their own dress.
  // A long overcoat and cap: the coachman's body (nelson_charles_1904_coachman) with its livery
  // made a plain overcoat (horn buttons, leather gloves, no silk hat) over dark trousers and boots.
  long_coat_1904: Object.freeze({
    label: 'Long coat and cap',
    base: Object.freeze({
      // The gloves are kept, in leather: the body has no hands under them.
      hide: Object.freeze(['headwear_top_hat']),
      colours: Object.freeze({ garment_outer__livery_coat_green_1904: BROWN, garment_upper__white_stock_1904: SHIRT_OAT,
        accessory__white_cotton_gloves: GLOVE,
        garment_lower__breeches_white_1904: DARK, footwear__black_top_boots: BOOT, accessory__white_metal_livery_buttons: HORN }),
      hat: cap(TWEED),
    }),
    looks: Object.freeze([
      Object.freeze({ id: 'brown', label: 'Brown', colours: { garment_outer__livery_coat_green_1904: BROWN }, hat: cap(TWEED) }),
      Object.freeze({ id: 'charcoal', label: 'Charcoal', colours: { garment_outer__livery_coat_green_1904: CHARCOAL }, hat: cap(CHARCOAL) }),
      Object.freeze({ id: 'navy', label: 'Navy', colours: { garment_outer__livery_coat_green_1904: NAVY }, hat: cap(NAVY) }),
      Object.freeze({ id: 'olive', label: 'Olive', colours: { garment_outer__livery_coat_green_1904: OLIVE }, hat: cap(BROWN) }),
    ]),
  }),
  // Shirtsleeves (billings_august_1904_stable_helper): the striped shirt as drawn, or a plain one.
  shirtsleeves_1904: Object.freeze({
    label: 'Shirtsleeves',
    base: Object.freeze({}),
    looks: Object.freeze([
      Object.freeze({ id: 'stripe', label: 'Striped shirt', colours: {} }),
      Object.freeze({ id: 'blue', label: 'Blue shirt', colours: { garment_upper__shirt_striped_1904: SHIRT_BLUE, headwear__felt_hat_light_1904: CHARCOAL } }),
      Object.freeze({ id: 'oat', label: 'Plain shirt', colours: { garment_upper__shirt_striped_1904: SHIRT_OAT, garment_lower__trousers_dark_1904: BROWN, headwear__felt_hat_light_1904: TWEED } }),
      Object.freeze({ id: 'grey', label: 'Grey shirt', colours: { garment_upper__shirt_striped_1904: SHIRT_GREY, garment_lower__trousers_dark_1904: GREY } }),
    ]),
  }),
  // The shirtwaist and walking skirt (nelson_christine_1904_errand): the skirt in its colours.
  errand_1904: Object.freeze({
    label: 'Shirtwaist and skirt',
    base: Object.freeze({}),
    looks: Object.freeze([
      Object.freeze({ id: 'navy', label: 'Navy', colours: {} }),
      Object.freeze({ id: 'brown', label: 'Brown', colours: { garment_lower__errand_skirt_navy: BROWN } }),
      Object.freeze({ id: 'grey', label: 'Grey', colours: { garment_lower__errand_skirt_navy: GREY } }),
      Object.freeze({ id: 'green', label: 'Green', colours: { garment_lower__errand_skirt_navy: BOTTLE } }),
      Object.freeze({ id: 'black', label: 'Black', colours: { garment_lower__errand_skirt_navy: CHARCOAL } }),
    ]),
  }),
  // A tailored jacket and gored skirt (the 1904 lady's body, glessner_frances_m_1904) in a
  // walking suit's colours, never her own black.
  suit_1904: Object.freeze({
    label: 'Jacket and skirt',
    base: Object.freeze({
      colours: Object.freeze({ garment_outer__lady_jacket_black: SERGE_BLUE, garment_lower__lady_skirt_black: SERGE_BLUE,
        headwear__lady_hat_black: CHARCOAL }),
    }),
    looks: Object.freeze([
      Object.freeze({ id: 'navy', label: 'Navy', colours: { garment_outer__lady_jacket_black: SERGE_BLUE, garment_lower__lady_skirt_black: SERGE_BLUE } }),
      Object.freeze({ id: 'brown', label: 'Brown', colours: { garment_outer__lady_jacket_black: BROWN, garment_lower__lady_skirt_black: BROWN, headwear__lady_hat_black: BROWN } }),
      Object.freeze({ id: 'grey', label: 'Grey', colours: { garment_outer__lady_jacket_black: DOVE, garment_lower__lady_skirt_black: DOVE, accessory__lady_hat_plumes: GREY } }),
      Object.freeze({ id: 'plum', label: 'Plum', colours: { garment_outer__lady_jacket_black: PLUM, garment_lower__lady_skirt_black: PLUM, headwear__lady_hat_black: PLUM } }),
      Object.freeze({ id: 'green', label: 'Green', colours: { garment_outer__lady_jacket_black: BOTTLE, garment_lower__lady_skirt_black: BOTTLE } }),
    ]),
  }),
  // A work dress and apron (the 1904 cook's study body, williamson_mattie_1904_cook_study): the
  // dress in a print's ground colour, the apron white.
  work_dress_1904: Object.freeze({
    label: 'Work dress and apron',
    base: Object.freeze({ colours: Object.freeze({ garment_outer__plain_apron: LINEN }) }),
    looks: Object.freeze([
      Object.freeze({ id: 'blue', label: 'Blue', colours: { garment_upper__plain_dress: CALICO, garment_lower__plain_dress: CALICO } }),
      Object.freeze({ id: 'brown', label: 'Brown', colours: { garment_upper__plain_dress: BUTTERNUT, garment_lower__plain_dress: BUTTERNUT } }),
      Object.freeze({ id: 'red', label: 'Red', colours: { garment_upper__plain_dress: MADDER, garment_lower__plain_dress: MADDER } }),
      Object.freeze({ id: 'grey', label: 'Grey', colours: { garment_upper__plain_dress: DOVE, garment_lower__plain_dress: DOVE } }),
      Object.freeze({ id: 'black', label: 'Black', colours: { garment_upper__plain_dress: CHARCOAL, garment_lower__plain_dress: CHARCOAL } }),
    ]),
  }),
});

/** The bodies that wear a wear unless their figure names another (or none). */
export const ASSET_WEAR = Object.freeze({ anonymous_working_driver_1904: 'working_1904' });

/** A small stable number for a key (FNV-1a). */
function hashKey(key) {
  let h = 2166136261;
  for (const ch of String(key ?? '')) { h ^= ch.codePointAt(0); h = Math.imul(h, 16777619) >>> 0; }
  return h;
}

/**
 * The dress a wear gives: its base with one of its looks laid over, the look `look` names, or
 * else the one `key` picks. Null for no wear.
 */
export function wearFor(id, { key = '', look = null } = {}) {
  const w = id ? WEARS[id] : null;
  if (!w) return null;
  const looks = w.looks ?? [];
  const pick = (look && looks.find((l) => l.id === look)) ?? (looks.length ? looks[hashKey(key) % looks.length] : null);
  return mergeDress(w.base, pick ? { colours: pick.colours, ...(pick.hat ? { hat: pick.hat } : {}) } : null);
}

/** The wear a figure wears: `appearance.wear` where it names one (null: none), else its body's. */
export function figureWear(appearance) {
  if (appearance && Object.prototype.hasOwnProperty.call(appearance, 'wear')) return appearance.wear ?? null;
  return ASSET_WEAR[appearance?.asset_id] ?? null;
}

/**
 * `over` laid on `under`: its colours and pieces over theirs, both sets aside, its hat (or its
 * headcloth, which takes the hat's place) over theirs. Either may be null.
 */
export function mergeDress(under, over) {
  if (!under) return over ?? null;
  if (!over) return under;
  const out = { ...under, ...over };
  if (under.colours || over.colours) out.colours = { ...under.colours, ...over.colours };
  if (under.pieces || over.pieces) out.pieces = { ...under.pieces, ...over.pieces };
  if (under.hide || over.hide) out.hide = [...new Set([...(under.hide ?? []), ...(over.hide ?? [])])];
  out.hat = over.hat ?? (over.headcloth || over.hat === null ? null : under.hat ?? null);
  if (!out.hat) delete out.hat;
  return out;
}

/**
 * The dress a figure wears (humans.js; `actor` a HumanActor, its `instance.appearance` and key):
 * its recorded dress (`recorded`, or null) laid over its wear, the one the record names (`wear`,
 * null for none) or else its body's (figureWear), in the colouring the record or the figure names
 * (`look`) or else the one its key picks. A figure that keeps its own hat (`appearance.wear_hat
 * === false`: a coachman in livery) wears the wear's cloth without its hat.
 */
export function wornDress(recorded, actor = null) {
  const a = actor?.instance?.appearance ?? {};
  let worn = wearFor(recorded && Object.prototype.hasOwnProperty.call(recorded, 'wear') ? recorded.wear : figureWear(a),
    { key: actor?.personId ?? actor?.id ?? '', look: recorded?.look ?? a.look ?? null });
  if (worn?.hat && a.wear_hat === false) { worn = { ...worn }; delete worn.hat; }
  return mergeDress(worn, recorded);
}
