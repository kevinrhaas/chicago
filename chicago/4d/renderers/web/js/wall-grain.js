/**
 * wall-grain.js — which wall substrate a record's walls are, and how much of the
 * wood's grain its finish lets through. T-1963.
 *
 * A pure function of the sidecar, with no three.js in it, so that
 * `tools/check_wall_relief.py` can run the SAME code over every record and hold
 * it to what the generators actually built. That check is what makes this a
 * rule rather than a guess: `docs/GLB-CONTRACT.md` § Wall substrates (PROPOSED,
 * T-1963) explains why the renderer reads the substrate off the record (route 2
 * of `docs/RESEARCH/1835_photographic_fabric_preparation.md` § 5) instead of off
 * a material name nobody has pinned yet.
 *
 * ## The substrate
 *
 * Two of the library's wall faces have NO course line in them —
 * `clapboard_board_face` and `hewn_log_face`, regenerated for the T-1801 proof
 * so that the only courses on a wall are the modelled ones. They are bound:
 *
 *   `wall` on the three frame archetypes -> clapboard. `frame_dwelling` and
 *       `frame_tavern` call `materials.wall_substrate(cladding="clapboard")`
 *       outright; `frame_storefront` passes the record's own construction and
 *       cladding, and the three storefronts dealt `vertical_board` are left
 *       flat. An upright board grained across its length is the fabric proof's
 *       defect 4, and it would be worse than no grain at all.
 *   `log` on the archetypes whose logs lie down -> hewn log. A palisade's logs
 *       stand up and a bridge's are piles and stringers, so neither is bound.
 *
 * ## The grain
 *
 * `materials.wall_finish()`'s order, verbatim: a stated coating wins, then the
 * record's `finish_key`, then bare stock. A COATING (`whitewash`, `red_oxide`,
 * `white_paint`, the three rows the sheet marks `coating: True`) hides the
 * wood's colour and keeps its relief, so it lets 0.3 of the grain's albedo
 * through. Bare stock lets all of it through. 0.3 is the fabric proof's reading
 * of a weathered coat, and it is a reconstruction (L350).
 * A log wall wears no finish here: every `log` material in the town is the
 * sheet's `HEWN_RGBA`, and the check holds that true.
 */

/** `materials.FINISHES` rows with `coating=True`. */
export const COATINGS = new Set(['whitewash', 'red_oxide', 'white_paint']);

/** `materials._PAINT_FINISH` — `paint` values that name a coating (ochre is a wash, not a coat). */
const PAINT_FINISH = {
  white: 'white_paint',
  whitewash: 'whitewash',
  red: 'red_oxide',
  red_oxide: 'red_oxide',
  ochre: 'ochre',
};

/** How much of the wood's own albedo figure a finish lets through. */
export const GRAIN_BARE = 1.0;
export const GRAIN_COATED = 0.3;

/** Archetypes whose `wall` primitive is lapped clapboard (unless a storefront says otherwise). */
const CLAPBOARD_ARCHETYPES = new Set(['frame_dwelling', 'frame_storefront', 'frame_tavern']);
/** `materials._CLADDING_SUBSTRATE` keys that are NOT clapboard. */
const UPRIGHT_CLADDING = new Set(['vertical_board', 'board_and_batten']);
/** Archetypes whose `log` primitives are laid horizontally, course on course. */
const LAID_LOG_ARCHETYPES = new Set(['log_dwelling', 'outbuilding', 'fort_structure']);

/** A stated attribute's value, whether the record writes it bare or as `{ value, confidence }`. */
function valueOf(a) {
  return a && typeof a === 'object' && !Array.isArray(a) ? a.value : a;
}

/** `materials.wall_finish(paint, finish_key)` — the finish KEY, defaulting to `unpainted`. */
export function wallFinishKey(sidecar) {
  const paint = valueOf(sidecar?.attributes?.paint);
  if (typeof paint === 'string' && PAINT_FINISH[paint]) return PAINT_FINISH[paint];
  const key = sidecar?.reconstruction?.finish_key;
  return typeof key === 'string' && key ? key : 'unpainted';
}

/**
 * The relief this record's walls take, by material name:
 * `{ wall: { substrate, grain } | null, log: { substrate, grain } | null }`.
 * A `null` leaves that material exactly as the town drew it before T-1963.
 */
export function wallRelief(sidecar) {
  const archetype = sidecar?.archetype;
  let wall = null;
  if (CLAPBOARD_ARCHETYPES.has(archetype)) {
    const cladding = archetype === 'frame_storefront' ? valueOf(sidecar?.attributes?.cladding) : null;
    if (!UPRIGHT_CLADDING.has(cladding)) {
      const finish = wallFinishKey(sidecar);
      wall = { substrate: 'clapboard', finish, grain: COATINGS.has(finish) ? GRAIN_COATED : GRAIN_BARE };
    }
  }
  const log = LAID_LOG_ARCHETYPES.has(archetype)
    ? { substrate: 'hewn_log', finish: null, grain: GRAIN_BARE }
    : null;
  return { wall, log };
}
