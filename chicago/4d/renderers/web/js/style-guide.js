/**
 * style-guide.js — the written style guide on Inspect's Design tab, for EVERY building (T-3435).
 *
 * The owner, 2026-11-06: the Design tab "typically says 'no style guide has been written' and then
 * there is a long list of facts … turn that design tab into a style guide that discusses
 * intelligently the design of the building … make these cards consistent across the buildings."
 *
 * Only a dozen buildings have an authored summary and three a style module (data/styles/), so a
 * guide that waited for an author would stay empty for the rest of the town. This one is WRITTEN
 * FROM THE BUILDING'S OWN RECORD, the way fallback-summary.js writes the Overview's opening:
 * every sentence is a template filled from graded sidecar attributes, and each carries the
 * lowest grade of the attributes it was filled from. Nothing is claimed that the record does not
 * hold; a term the record uses (a balloon frame, a mansard, an oriel) may be explained in a few
 * plain words, which is a glossary, not a claim about the building.
 *
 * THE SAME SHAPE FOR EVERY BUILDING, in this order:
 *   head      the style's name where a module or the summary's key names one, else what it is
 *             ("Stone-fronted brick house"), with its built date, architect and use as chips
 *   lead      up to three sentences: what it is, its roof, its front
 *   look      up to four highlights — the record's own "On this house" items where an author
 *             wrote them (with Show me), else the features that set this building apart
 *   parts     Shape · Walls · Roof · Windows and doors · Grounds, always all five, each a few
 *             plain lines, or one line saying the records do not say
 *   basis     how the model was built, in the structure grade's own words
 * The style module's card and Compare styles follow, where a module is named. The whole list of
 * graded facts lives on the Details tab, and where each came from on Sources.
 *
 * Pure: no DOM. tools/test_nav_design.mjs runs it over every sidecar in every scene.
 */
import { clean } from './fallback-summary.js';

export const GRADES = ['attested', 'inferred', 'reconstructed'];
const RANK = { attested: 0, inferred: 1, reconstructed: 2 };
export const PART_KEYS = ['shape', 'walls', 'roof', 'openings', 'grounds'];

const NUM = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'];
const numWord = (n) => (Number.isInteger(n) && n >= 0 && n < NUM.length ? NUM[n] : String(n));
const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : '');
const article = (w) => (/^(?:one\b|one-|uni|eu)/i.test(w) ? 'a' : /^[aeiou]/i.test(w) ? 'an' : 'a');
const plural = (n, one, many) => `${numWord(n)} ${n === 1 ? one : many}`;

/** The worst grade among those given (a sentence is as sure as its least sure part). */
export function lowest(...gs) {
  const ok = gs.filter((g) => g in RANK);
  if (!ok.length) return null;
  return ok.reduce((a, b) => (RANK[b] > RANK[a] ? b : a));
}

/** One sidecar attribute, as {v, g}: its value and its grade; null where absent or ungraded. */
const entryOf = (table, key) => (table && typeof table === 'object' ? table[key] : undefined);
function attr(sidecar, key) {
  const claim = entryOf(sidecar?.attributes, key);
  if (!claim || typeof claim !== 'object' || claim.value === undefined || claim.value === null) return null;
  return { v: claim.value, g: claim.confidence in RANK ? claim.confidence : 'reconstructed' };
}

// ---- vocabulary ---------------------------------------------------------------------------
// Each table turns a value the record carries into the words a visitor reads. A value with no
// entry is spelled out from the record's own token where that reads as words, else left out.

const MATERIAL = {
  balloon_frame: 'balloon-frame', braced_frame: 'braced-frame', light_frame: 'light-frame', frame: 'frame',
  log: 'log', plank: 'plank', brick: 'brick', stone: 'stone', earth: 'earth', timber_crib: 'timber-crib',
  brick_with_stone_front: 'stone-fronted brick', stone_with_brick_rear: 'stone', glass: 'glass',
};
/** How the walls were made, with a few words on the method where the record names one. */
const WALLS = {
  balloon_frame: 'Balloon frame: light sawn studs, nailed rather than pegged',
  braced_frame: 'Braced frame: heavy timbers pegged together and braced at the corners',
  light_frame: 'Light timber frame',
  frame: 'Timber frame',
  log: 'Log walls, notched together at the corners',
  plank: 'Plank walls',
  brick: 'Brick walls',
  stone: 'Stone walls',
  earth: 'Earth walls',
  timber_crib: 'A timber crib, filled',
  split_rail: 'Split rails',
  brick_with_stone_front: 'Brick, with a stone street front',
  stone_with_brick_rear: 'Stone, with brick at the back',
  glass: 'Glass on a light frame',
};
const NOUN = {
  residence: 'house', dwelling: 'house', dwelling_farmstead: 'farmhouse', barn_or_carriage_shed: 'barn or carriage house',
  stable: 'stable', stable_and_wagon_yard: 'stable', outbuilding: 'outbuilding', glasshouse: 'glasshouse',
  church: 'church', railway_station: 'railway station', large_workshop: 'workshop', privy: 'privy',
  woodshed_or_storage_shed: 'shed', older_log_dwelling: 'log house', rough_plank_dwelling_or_shanty: 'shanty',
  one_room_frame_cottage: 'one-room cottage', two_room_frame_cottage: 'two-room cottage',
  deep_plan_frame_cottage: 'deep-plan cottage', one_and_a_half_story_frame_cottage: 'storey-and-a-half cottage',
  small_two_story_frame_house: 'small two-storey house', enlisted_mens_barracks: "enlisted men's barracks",
  officers_quarters: "officers' quarters", block_house: 'blockhouse', military_post_enclosure: 'stockade',
  tavern_inn: 'tavern and inn', store_residence: 'store and house', sutlers_store: "sutler's store",
  soap_candle_manufactory: 'soap and candle works', slaughterhouse_packing: 'slaughterhouse and packing house',
  meeting_house_school: 'meeting house and school', dwelling_to_let: 'house to let', agency_house_residence: 'agency house',
  commanding_officers_quarters: "commanding officer's quarters", cooper_wagon_or_wheelwright_shop: 'cooper or wheelwright shop',
};
/** Things that are not buildings: their noun takes no wall material ("Log company gardens"). */
const NOT_A_BUILDING = /garden|parade|crossing|field|camp|flagstaff|harbour|works|ground|enclosure|stockade/;
const STONE = {
  limestone_lemont: 'Lemont limestone', limestone_bedford: 'Bedford limestone', sandstone_brown: 'brown sandstone',
  sandstone_fawn: 'fawn sandstone', granite_rock_faced: 'granite',
};
const DRESSING = { smooth: 'smooth-cut', rock_faced: 'rock-faced' };
const ROOF = {
  gable: 'gable roof', hip: 'hipped roof', hip_steep: 'steep hipped roof', hip_deck: 'hipped roof with a flat deck',
  mansard: 'mansard roof', flat: 'flat roof', shed: 'shed roof', pyramid: 'pyramid roof', shaped_gable: 'shaped gable',
};
const ROOF_GLOSS = {
  mansard: 'Mansard: steep lower slopes that hold the top storey, nearly flat above',
  shed: 'One slope only, falling to the back or side',
  hip: 'Slopes on all four sides, no gable ends',
  hip_deck: 'Slopes on all four sides up to a flat deck',
  pyramid: 'Four slopes meeting at a point',
  gable: 'Two slopes meeting at a ridge, with gable ends',
  flat: 'Flat, or nearly so, behind the wall top',
};
const COVERING = {
  tin_standing_seam_painted: 'painted standing-seam tin', tin_flat_seam_painted: 'painted flat-seam tin',
  slate_pennsylvania: 'Pennsylvania slate', slate: 'slate', 'wood shingle': 'wood shingles', wood_shingle: 'wood shingles',
  'tar and gravel': 'tar and gravel', terracotta_tile: 'terracotta tile', 'tin, painted': 'painted tin',
};
const PAINT = {
  unpainted: 'Left unpainted', whitewash: 'Whitewashed', red: 'Painted red', yellow: 'Painted yellow',
  white: 'Painted white',
};
const CLADDING = { clapboard: 'Clapboard siding', vertical_board: 'Upright boards', log_and_vertical_boards: 'Logs, part boarded over',
  clapboard_part_way_up: 'Clapboards part way up' };
const TRIM = { plain: 'Plain trim', boxed: 'Boxed cornice and trim', scant: 'Very little trim' };
const PLAN = {
  hall_parlour: 'Hall-and-parlour plan: two rooms side by side',
  single_pen: 'One room, a single pen',
  centre_passage: 'Centre-passage plan: a hall between two rooms',
  chapel_side: 'A chapel plan, entered from the side',
};
const CORNICE = {
  'k10.cornice.bracketed_timber': 'A wooden cornice on brackets at the eaves',
  'k10.cornice.moulded_stone': 'A moulded stone cornice at the eaves',
};
const HEADS = {
  'k09.trim.lintel_cornice_hood': 'Window heads capped by small cornices',
  'k01.flat_lintel': 'Plain flat lintels over the windows',
  'k09.surround.rowhouse_restrained': 'Plain, restrained window surrounds',
};
const WINDOWS = {
  'k06.opening.sash_2over2_flat': 'two-over-two sash under flat heads',
  'k06.opening.sash_round_fanlight': 'round-headed sash with fanlights',
  'k06.opening.sash_round_fanlight_wide': 'wide round-headed windows with fanlights',
  'k06.opening.sash_1over1_segmental': 'one-over-one sash under shallow arches',
  'k06.opening.sash_2over2_segmental': 'two-over-two sash under shallow arches',
  'k06.opening.sash_paired_flat': 'paired sash windows',
  'k06.opening.sash_paired_round': 'paired round-headed sash',
  'k06.opening.sash_triple_flat': 'triple sash windows',
  'k06.opening.sash_transom_flat': 'sash with transoms',
  'k06.opening.casement_pair_mullioned': 'mullioned casements',
  'k06.opening.casement_pair_transom_mullioned': 'mullioned casements with transoms',
  'k06.opening.casement_four_transom_mullioned': 'banks of four mullioned casements',
  'k06.opening.casement_pair_transom_squared': 'casements with square transoms',
  'k06.opening.sash_round_lattice_wide': 'a wide round-headed lattice window',
  'k06.opening.sash_segmental_fanlight_wide': 'a wide arched window with a fanlight',
  'k06.opening.fixed_round_leaded_bordered': 'a round leaded window',
};
const ENTRANCE = {
  'k07.entrance.panel_door_stoop': 'A panelled front door up a stoop',
  'k07.entrance.double_door_deep_arch': 'Double doors set deep in a round arch',
};
const BAYS = {
  'k08.tower.round': ['Round tower', 'Rises above the eaves'],
  'k08.tower.octagonal': ['Eight-sided tower', 'Rises above the eaves'],
  'k08.bay.bowed': ['Bowed bay', 'A curved bay window, glazed round its face'],
  'k08.bay.canted': ['Angled bay', 'A three-sided bay window'],
  'k08.bay.canted_hooded': ['Angled bay with a hood', 'A three-sided bay under its own little roof'],
  'k08.bay.rectangular': ['Square bay', 'A box bay window'],
  'k08.oriel.canted_corbelled': ['Oriel', 'A bay hung out from the upper wall on corbels'],
  'k08.projection.full_height': ['Projecting front section', 'Stands forward of the wall, full height'],
};
const FENCE = {
  'k11.fence.spear_on_curb': 'Iron spear-topped fence on a stone curb',
  'k11.fence.scroll_band': 'Iron fence with a scrolled band',
  'k11.fence.scroll_panel': 'Iron fence in scrolled panels',
  'k11.fence.lattice_arcade': 'Lattice fence in arches',
  'k11.fence.side_boards': 'Board fences down the sides',
};
const BOUNDARY = {
  stone_coping_wall: 'A low stone coping wall on the street line',
  open: 'Open to the walk: no fence or wall in front',
  stone_posts_rails: 'Stone posts and rails along the street',
  front_garden: 'A front garden',
};
const WALK = { stone_flags: 'Stone-flag front walk' };
const DOOR = { man: 'A plain board door', stable: 'A stable door', wagon: 'Wide wagon doors', cargo: 'A cargo door' };
const SIDE = { north: 'at the north end of the front', south: 'at the south end of the front', centre: 'in the middle of the front',
  front: 'on the front', right: 'on the side' };
const WALL_KIND = { picket_stockade: 'A stockade of upright pickets', worm_fence: 'A zig-zag worm fence of split rails' };
const SHUTTER = { green: 'Green shutters', black: 'Black shutters', bright_blue: 'Bright blue shutters' };

/** Attributes a record writes as plain prose (the measured houses, Glessner first): the part
 *  each belongs to and its label. The value is shown as written, and only where it is clean. */
const PROSE = {
  front_door: ['openings', 'Front door'],
  porte_cochere_doors: ['openings', 'Carriage doors'],
  ironwork_finish: ['walls', 'Ironwork'],
  vines: ['walls', 'Vines'],
  planting: ['grounds', 'Planting'],
};
/** Attributes a measured record carries for one feature: present means built, in these words. */
const FEATURE = {
  tower_stair: ['shape', 'A round stair tower'],
  tower_north: ['shape', 'A tower at the north end'],
  hall_bow: ['shape', 'A bowed wall around the hall'],
  bay_dining: ['openings', 'A dining-room bay'],
  dormers: ['roof', 'Small dormers in the roof'],
  turret_stable: ['roof', 'A small louvred turret on the stable roof'],
  eave_cornice: ['walls', 'A stone cornice under the eaves'],
  courtyard_gate: ['grounds', 'A gate into the courtyard'],
  courtyard_wall: ['grounds', 'A wall closing the courtyard'],
  courtyard_ground: ['grounds', 'A planted courtyard inside the walls'],
};

/** A token as words, only where it reads as words once its underscores go. */
function tokenWords(v) {
  if (typeof v !== 'string') return '';
  const w = v.replace(/_or_/g, ' or ').replace(/_and_/g, ' and ').replace(/_/g, ' ').trim();
  return /^[a-z][a-z' -]*$/i.test(w) ? w : '';
}

function storeysWords(n) {
  const x = Number(n);
  if (!Number.isFinite(x) || x <= 0) return '';
  if (x === 1.5) return 'one and a half storeys';
  if (Number.isInteger(x)) return plural(x, 'storey', 'storeys');
  return '';
}
function storeysAdj(n) {
  const x = Number(n);
  if (x === 1.5) return 'storey-and-a-half';
  return Number.isInteger(x) && x >= 1 && x < NUM.length ? `${NUM[x]}-storey` : '';
}

/** What the building is, as a noun: its use in words. */
function nounOf(fn) {
  if (typeof fn !== 'string') return '';
  const w = NOUN[fn] ?? tokenWords(fn.split(';')[0]);
  // The storeys are said on their own; "two story" inside a use reads twice.
  return w.replace(/\b(?:one|two|three)(?: and a half)? story\s*/g, '').replace(/\s+/g, ' ').trim();
}

/** The roof's form, from the record's own form, its type, or its draft's main part. */
function roofForm(sc) {
  const f = attr(sc, 'roof_form') ?? attr(sc, 'roof_type');
  if (f && typeof f.v === 'string' && f.v !== 'none') return f;
  if (attr(sc, 'mansard')) return { v: 'mansard', g: attr(sc, 'mansard').g };
  const plan = attr(sc, 'draft_plan');
  const main = Array.isArray(plan?.v?.parts) ? plan.v.parts.find((p) => p.role === 'main') : null;
  if (main?.roof) return { v: main.roof, g: plan.g };
  return null;
}

function pitchWord(deg, form) {
  const d = Number(deg);
  if (!Number.isFinite(d) || form === 'flat' || form === 'mansard') return '';
  if (d >= 50) return 'steep';
  if (d <= 25) return 'low';
  return '';
}

function covering(sc) {
  const c = attr(sc, 'roof_covering');
  if (!c) return null;
  const raw = typeof c.v === 'string' ? c.v : (c.v.fabric ?? c.v.material);
  const w = COVERING[raw] ?? tokenWords(raw);
  return w ? { text: w, g: c.g } : null;
}

/** Bays, towers and oriels the record builds, in its order, distinct by kind. */
function projections(sc) {
  const out = [];
  const seen = new Set();
  const b = attr(sc, 'bays');
  if (b && Array.isArray(b.v)) {
    for (const x of b.v) {
      const words = BAYS[x?.variant];
      if (!words || seen.has(x.variant)) continue;
      seen.add(x.variant);
      out.push({ kind: x.variant, text: words[0], detail: words[1], grade: b.g, n: b.v.filter((y) => y?.variant === x.variant).length });
    }
  }
  const e = attr(sc, 'draft_elevation');
  for (const f of Array.isArray(e?.v?.features) ? e.v.features : []) {
    if (f?.kind !== 'corner_tower' || seen.has('tower')) continue;
    seen.add('tower');
    const shape = f.sides === 8 ? 'Eight-sided' : f.sides === 4 ? 'Square' : 'Round';
    out.push({ kind: 'tower', text: `${shape} corner tower`, detail: 'Rises above the eaves', grade: e.g, n: 1 });
  }
  return out;
}

function footprintFt(sc) {
  const fp = sc?.footprint;
  const poly = Array.isArray(fp?.polygon) ? fp.polygon : null;
  if (!poly || poly.length < 3) return null;
  const xs = poly.map((p) => Number(p[0])), ys = poly.map((p) => Number(p[1]));
  if (![...xs, ...ys].every(Number.isFinite)) return null;
  const w = Math.max(...xs) - Math.min(...xs), d = Math.max(...ys) - Math.min(...ys);
  if (!(w > 0.5 && d > 0.5)) return null;
  const ft = (m) => Math.round(m / 0.3048);
  const [a, b] = [ft(Math.min(w, d)), ft(Math.max(w, d))];
  return { text: `About ${a} × ${b} ft on the ground`, g: fp.confidence in RANK ? fp.confidence : 'reconstructed' };
}

function glazingWords(v) {
  const m = /^(\d+)_over_(\d+)_(\d+)x(\d+)$/.exec(String(v ?? ''));
  if (!m) return '';
  return `${numWord(+m[1])}-over-${numWord(+m[2])} sash windows, ${m[3]} × ${m[4]} in. panes`;
}

// ---- the guide ----------------------------------------------------------------------------

const line = (text, grade, extra = {}) => ({ text: String(text), grade: grade ?? null, ...extra });

/** The five parts, each a list of graded lines. */
function partsOf(sc) {
  const P = Object.fromEntries(PART_KEYS.map((k) => [k, []]));
  const add = (k, text, g) => { if (text && g && clean(text)) P[k].push(line(cap(text), g)); };

  // Shape.
  const st = attr(sc, 'stories');
  if (st) add('shape', cap(storeysWords(st.v)), st.g);
  const fl = attr(sc, 'principal_floor_m');
  if (fl && Number(fl.v) >= 0.6) add('shape', `Main floor raised ${Math.round(Number(fl.v) / 0.3048)} ft above the ground`, fl.g);
  const fp = footprintFt(sc);
  if (fp) add('shape', fp.text, fp.g);
  const plan = attr(sc, 'plan');
  if (plan) add('shape', PLAN[plan.v] ?? '', plan.g);
  const loft = attr(sc, 'loft');
  if (loft?.v === true) add('shape', 'A loft under the roof', loft.g);
  const gf = attr(sc, 'gable_front');
  if (gf?.v === true) add('shape', 'Gable end turned to the street', gf.g);
  const rc = attr(sc, 'round_corner');
  if (rc) add('shape', 'A rounded corner', rc.g);
  const wings = attr(sc, 'rear_wings');
  if (wings && Array.isArray(wings.v) && wings.v.length) add('shape', wings.v.length === 1 ? 'A rear wing behind the main block' : `${cap(numWord(wings.v.length))} rear wings`, wings.g);
  const ell = attr(sc, 'rear_ell');
  if (ell?.v === true) add('shape', 'A rear ell', ell.g);
  const dp = attr(sc, 'draft_plan');
  if (dp && Array.isArray(dp.v?.parts) && !wings) {
    // The draft's parts are rectangles fitted inside the map's outline, so only which kinds of
    // part it has are said, never how many rectangles.
    const has = (role) => dp.v.parts.some((p) => p.role === role);
    const bits = [['wing', 'side wings'], ['range', 'a range behind'], ['porch', 'a porch'], ['bay', 'bays']]
      .filter(([r]) => has(r)).map(([, w]) => w);
    if (bits.length) add('shape', `A main block with ${bits.length > 1 ? `${bits.slice(0, -1).join(', ')} and ${bits.at(-1)}` : bits[0]}`, dp.g);
  }
  const ov = attr(sc, 'upper_overhang_m');
  if (ov && Number(ov.v) > 0) add('shape', 'The upper storey overhangs the lower', ov.g);

  // Walls.
  const con = attr(sc, 'construction');
  if (con) add('walls', WALLS[con.v] ?? tokenWords(con.v), con.g);
  const sf = attr(sc, 'stone_front');
  if (sf && typeof sf.v === 'object') {
    const stone = STONE[sf.v.fabric];
    const dress = DRESSING[sf.v.dressing];
    if (stone) add('walls', `Street front of ${dress ? `${dress} ` : ''}${stone}`, sf.g);
  }
  const swb = attr(sc, 'service_wall_brick');
  if (swb && /common_buff/.test(String(swb.v))) add('walls', 'Side and back walls of common buff brick', swb.g);
  else if (swb && /red/.test(String(swb.v))) add('walls', 'Side and back walls of red-brown brick', swb.g);
  const clad = attr(sc, 'cladding');
  if (clad) add('walls', CLADDING[clad.v] ?? '', clad.g);
  const paint = attr(sc, 'paint');
  if (paint && typeof paint.v === 'string') add('walls', PAINT[paint.v] ?? '', paint.g);
  const lf = attr(sc, 'log_finish');
  if (lf?.v === 'whitewash') add('walls', 'Logs whitewashed', lf.g);
  const wh = attr(sc, 'wall_head');
  if (wh && typeof wh.v === 'object') add('walls', CORNICE[wh.v.cornice] ?? '', wh.g);
  const trim = attr(sc, 'trim');
  if (trim) add('walls', TRIM[trim.v] ?? '', trim.g);
  const wk = attr(sc, 'wall_kind');
  if (wk) add('walls', WALL_KIND[wk.v] ?? '', wk.g);

  // Roof.
  const form = roofForm(sc);
  if (form) add('roof', ROOF_GLOSS[form.v] ?? cap(ROOF[form.v] ?? tokenWords(form.v)), form.g);
  const pitch = attr(sc, 'roof_pitch_deg');
  if (pitch && Number.isFinite(Number(pitch.v)) && form?.v !== 'flat' && form?.v !== 'mansard') add('roof', `Pitched at ${Math.round(Number(pitch.v))}°`, pitch.g);
  const mans = attr(sc, 'mansard');
  if (mans && /convex/.test(String(mans.v?.variant ?? ''))) add('roof', 'Its mansard faces curve outward', mans.g);
  const cov = covering(sc);
  if (cov) add('roof', `Covered in ${cov.text}`, cov.g);
  const ch = attr(sc, 'chimneys');
  // A count, a kit's list of stacks, or a measured record's stacks by name.
  const named = ch && ch.v && typeof ch.v === 'object' && !Array.isArray(ch.v) && !('stacks' in ch.v)
    && Object.values(ch.v).every((x) => x && typeof x === 'object' && 'top' in x) ? Object.keys(ch.v).length : null;
  const stacks = ch ? (typeof ch.v === 'number' ? ch.v : Array.isArray(ch.v?.stacks) ? ch.v.stacks.length : named) : null;
  if (Number.isInteger(stacks) && stacks > 0) add('roof', stacks === 1 ? 'One chimney' : `${cap(numWord(stacks))} chimneys`, ch.g);
  const dor = attr(sc, 'dormer');
  if (dor || (mans && mans.v?.dormers)) add('roof', 'Dormer windows in the roof', (dor ?? mans).g);
  const sp = attr(sc, 'stovepipes');
  if (sp && Number(sp.v) > 0) add('roof', `${cap(numWord(Number(sp.v)))} stovepipes through the roof`, sp.g);

  // Windows and doors.
  const gl = attr(sc, 'glazing');
  if (gl) add('openings', cap(glazingWords(gl.v)), gl.g);
  const wkit = attr(sc, 'window_kit');
  if (wkit && typeof wkit.v === 'object') {
    const kinds = [...new Set(Object.values(wkit.v).map((x) => (typeof x === 'string' ? x : x?.variant)).filter((x) => WINDOWS[x]))];
    if (kinds.length) add('openings', `Windows: ${kinds.slice(0, 3).map((k) => WINDOWS[k]).join('; ')}`, wkit.g);
  }
  const sft = attr(sc, 'street_front_trim');
  const heads = Array.isArray(sft?.v?.by_storey) ? [...new Set(sft.v.by_storey)].filter((x) => HEADS[x]) : [];
  if (heads.length) add('openings', HEADS[heads[0]], sft.g);
  const fb = attr(sc, 'bays');
  if (fb && Number.isInteger(fb.v) && fb.v > 0) add('openings', `${cap(numWord(fb.v))} bays across the front`, fb.g);
  const front = attr(sc, 'front_bays');
  if (front && Array.isArray(front.v) && front.v.length) add('openings', `${cap(plural(front.v.length, 'bay', 'bays'))} of openings across the front`, front.g);
  const ekit = attr(sc, 'entrance_kit');
  const door = ekit && typeof ekit.v === 'object' ? Object.values(ekit.v).map((x) => (typeof x === 'string' ? x : x?.variant)).find((x) => ENTRANCE[x]) : null;
  const eb = attr(sc, 'entrance_bay');
  const draftEl = attr(sc, 'draft_elevation');
  const where = eb ? { v: SIDE[eb.v], g: eb.g } : draftEl?.v?.entrance && SIDE[draftEl.v.entrance] ? { v: SIDE[draftEl.v.entrance], g: draftEl.g } : null;
  if (door) add('openings', ENTRANCE[door], ekit.g);
  if (where?.v) add('openings', `Front door ${where.v}`, where.g);
  const d1835 = attr(sc, 'door');
  const dside = attr(sc, 'door_side');
  if (d1835 && DOOR[d1835.v]) add('openings', `${DOOR[d1835.v]}${dside && SIDE[dside.v] ? ` ${SIDE[dside.v]}` : ''}`, lowest(d1835.g, dside?.g));
  const porch = attr(sc, 'porch');
  if (porch?.v === 'stoop') add('openings', 'A stoop at the door', porch.g);
  if (porch?.v === 'roofed') add('openings', 'A roofed porch at the door', porch.g);
  const sh = attr(sc, 'shutters');
  if (sh) add('openings', SHUTTER[sh.v] ?? '', sh.g);
  const shop = attr(sc, 'shopfront');
  if (shop?.v === true) add('openings', 'A shop front on the street', shop.g);
  const goods = attr(sc, 'goods_door');
  if (goods?.v === true) add('openings', 'A goods door for loading', goods.g);
  const hoist = attr(sc, 'hoist_door');
  if (hoist?.v === true) add('openings', 'A hoist door high in the gable', hoist.g);
  const gal = attr(sc, 'gallery');
  if (gal?.v === true) add('openings', 'A gallery along the front', gal.g);
  const lh = attr(sc, 'loopholes');
  if (lh?.v === true) add('openings', 'Loopholes to fire through', lh.g);
  for (const p of projections(sc)) add('openings', p.n > 1 ? `${cap(numWord(p.n))} × ${p.text.toLowerCase()}` : p.text, p.grade);
  const cons = attr(sc, 'conservatory');
  if (cons) add('openings', 'A glass conservatory', cons.g);

  // Grounds.
  const bd = attr(sc, 'boundary');
  if (bd && typeof bd.v === 'object') {
    if (FENCE[bd.v.fence]) add('grounds', FENCE[bd.v.fence], bd.g);
    else if (BOUNDARY[bd.v.layout]) add('grounds', BOUNDARY[bd.v.layout], bd.g);
    if (bd.v.entrance_gate) add('grounds', 'A gate to the front walk', bd.g);
  }
  const yd = attr(sc, 'yard');
  if (yd && WALK[yd.v?.front_walk?.surface]) add('grounds', WALK[yd.v.front_walk.surface], yd.g);
  const ph = attr(sc, 'picket_height_m');
  if (ph && Number(ph.v) > 0) add('grounds', `Pickets ${Math.round(Number(ph.v) / 0.3048)} ft tall`, ph.g);
  const gates = attr(sc, 'gate_sides');
  if (gates && Array.isArray(gates.v) && gates.v.length) add('grounds', `Gates on ${plural(gates.v.length, 'side', 'sides')}`, gates.g);
  const dock = attr(sc, 'dock');
  if (dock?.v === true) add('grounds', 'Its own dock on the river', dock.g);

  // A measured record's own features and its prose, in the parts they belong to.
  for (const [key, [part, words]] of Object.entries(FEATURE)) {
    const a = attr(sc, key);
    if (a) add(part, words, a.g);
  }
  for (const [key, [part, label]] of Object.entries(PROSE)) {
    const a = attr(sc, key);
    if (a && typeof a.v === 'string' && clean(a.v) && a.v.split(/\s+/).length <= 30) add(part, `${label}: ${a.v.replace(/\.$/, '')}`, a.g);
  }

  return PART_KEYS.map((key) => ({ key, lines: P[key].slice(0, 7) }));
}

/** The features that set this building apart, from its record (at most four). */
function standouts(sc) {
  const out = [];
  const push = (text, detail, grade) => { if (grade && clean(text) && !out.some((o) => o.text === text)) out.push({ text, detail: detail ?? '', grade }); };
  for (const p of projections(sc)) if (p.kind !== 'k08.projection.full_height') push(p.text, p.detail, p.grade);
  const rc = attr(sc, 'round_corner');
  if (rc) push('Rounded corner', 'The wall turns the corner in a curve', rc.g);
  const cons = attr(sc, 'conservatory');
  if (cons) push('Glass conservatory', 'A glasshouse built onto the house', cons.g);
  const form = roofForm(sc);
  if (form?.v === 'mansard') push('Mansard roof', 'Steep lower slopes hold the top storey', form.g);
  const wh = attr(sc, 'wall_head');
  const de = attr(sc, 'draft_elevation');
  if (wh?.v?.cornice === 'k10.cornice.bracketed_timber') push('Bracketed cornice', 'Carved brackets under deep eaves', wh.g);
  else if (de?.v?.brackets === true) push('Bracketed cornice', 'Brackets under the eaves', de.g);
  const sf = attr(sc, 'stone_front');
  if (sf?.v?.dressing === 'rock_faced') push('Rock-faced stone front', 'Stone left rough-faced, not smooth', sf.g);
  const ek = attr(sc, 'entrance_kit');
  if (ek && Object.values(ek.v ?? {}).some((x) => (x?.variant ?? x) === 'k07.entrance.double_door_deep_arch')) push('Deep arched doorway', 'Double doors set back in a round arch', ek.g);
  const bd = attr(sc, 'boundary');
  if (FENCE[bd?.v?.fence]) push(FENCE[bd.v.fence].split(' on ')[0], '', bd.g);
  const shop = attr(sc, 'shopfront');
  if (shop?.v === true) push('Shop front', 'Wide windows to show goods to the street', shop.g);
  const gal = attr(sc, 'gallery');
  if (gal?.v === true) push('Gallery', 'A long porch along the front', gal.g);
  const porch = attr(sc, 'porch');
  if (porch?.v === 'roofed') push('Roofed porch', '', porch.g);
  const sh = attr(sc, 'shutters');
  if (SHUTTER[sh?.v]) push(SHUTTER[sh.v], '', sh.g);
  const paint = attr(sc, 'paint');
  if (paint?.v === 'whitewash') push('Whitewashed walls', '', paint.g);
  const gf = attr(sc, 'gable_front');
  if (gf?.v === true) push('Gable to the street', 'The roof’s end faces the road', gf.g);
  const ov = attr(sc, 'upper_overhang_m');
  if (ov && Number(ov.v) > 0) push('Overhanging upper storey', 'Lets defenders fire straight down', ov.g);
  const lh = attr(sc, 'loopholes');
  if (lh?.v === true) push('Loopholes', 'Slits in the wall to fire through', lh.g);
  const hoist = attr(sc, 'hoist_door');
  if (hoist?.v === true) push('Hoist door', 'Goods lifted straight up into the loft', hoist.g);
  return out.slice(0, 4);
}

/** The guide's head: a name, a line under it, and its chips. */
function headOf(sc, sum, mod) {
  const st = attr(sc, 'stories');
  const con = attr(sc, 'construction');
  const fn = attr(sc, 'function');
  const noun = nounOf(fn?.v) || (sc?.archetype ? tokenWords(sc.archetype) : '');
  const mat = MATERIAL[con?.v] ?? '';
  const matShown = mat && !NOT_A_BUILDING.test(noun) && !noun.toLowerCase().includes(mat.replace(/-.*$/, '')) ? mat : '';
  const kind = cap([matShown, noun || (matShown ? 'building' : '')].filter(Boolean).join(' '));
  const keyStyle = (Array.isArray(sum?.key) ? sum.key : []).find((k) => /^style$/i.test(k.label ?? ''));
  let name;
  if (mod?.name) name = { text: mod.name, grade: mod.description?.grade ?? null, from: 'module' };
  else if (keyStyle?.value && clean(keyStyle.value)) name = { text: keyStyle.value, grade: keyStyle.grade ?? null, from: 'summary' };
  else name = { text: kind || 'A building', grade: lowest(con?.g, fn?.g), from: 'record' };
  const sub = name.from === 'record' ? null : (kind ? { text: kind, grade: lowest(con?.g, fn?.g) } : null);

  const chips = [];
  const built = attr(sc, 'built');
  const sb = sum?.built;
  if (sb?.year || sb?.phrase) chips.push({ k: 'built', text: String(sb.phrase ?? sb.year), grade: sb.grade ?? null });
  else if (built && (typeof built.v === 'number' || /^\d{4}$/.test(String(built.v)))) chips.push({ k: 'built', text: String(built.v), grade: built.g });
  const arch = (Array.isArray(sum?.key) ? sum.key : []).find((k) => /^architect/i.test(k.label ?? ''));
  if (arch?.value && clean(arch.value) && !/not known|unknown/i.test(arch.value)) chips.push({ k: 'architect', text: arch.value, grade: arch.grade ?? null });
  if (st && storeysWords(st.v)) chips.push({ k: 'storeys', text: storeysWords(st.v), grade: st.g });
  return { name, sub, chips, noun, mat: matShown };
}

/** Up to three sentences: what it is, its roof, its front. Each graded by its least sure part. */
function leadOf(sc, head) {
  const out = [];
  const st = attr(sc, 'stories');
  const con = attr(sc, 'construction');
  const fn = attr(sc, 'function');
  const tall = storeysAdj(st?.v);
  const what = [tall, head.mat, head.noun].filter(Boolean).join(' ');
  if (what && (head.noun || head.mat)) {
    const sf = attr(sc, 'stone_front');
    const stone = sf ? STONE[sf.v?.fabric] : '';
    const plain = stone ? what.replace('stone-fronted brick', 'brick') : what;
    const s = stone ? `${cap(article(plain))} ${plain}, its street front of ${stone}.` : `${cap(article(what))} ${what}.`;
    out.push(line(s, lowest(st?.g, con?.g, fn?.g, stone ? sf.g : null)));
  }
  const form = roofForm(sc);
  if (form && ROOF[form.v]) {
    const pitch = attr(sc, 'roof_pitch_deg');
    const adj = pitchWord(pitch?.v, form.v);
    const cov = covering(sc);
    const r = `${adj ? `${adj} ` : ''}${ROOF[form.v]}`;
    out.push(line(`Its roof is ${article(r)} ${r}${cov ? ` of ${cov.text}` : ''}.`, lowest(form.g, adj ? pitch.g : null, cov?.g)));
  }
  const cov0 = covering(sc);
  if (!(form && ROOF[form.v]) && cov0) out.push(line(`Its roofs are covered in ${cov0.text}.`, cov0.g));
  const bays = attr(sc, 'bays');
  const front = attr(sc, 'front_bays');
  const de = attr(sc, 'draft_elevation');
  const n = Number.isInteger(bays?.v) ? { v: bays.v, g: bays.g }
    : Array.isArray(front?.v) && front.v.length ? { v: front.v.length, g: front.g }
      : Number.isInteger(de?.v?.front_bays) && de.v.front_bays > 0 ? { v: de.v.front_bays, g: de.g } : null;
  const eb = attr(sc, 'entrance_bay') ?? (de?.v?.entrance ? { v: de.v.entrance, g: de.g } : null) ?? attr(sc, 'door_side');
  const where = eb && SIDE[eb.v] && eb.v !== 'front' ? SIDE[eb.v].replace(' of the front', '') : '';
  if (n && n.v > 0) out.push(line(`The front is ${numWord(n.v)} ${n.v === 1 ? 'bay' : 'bays'} wide${where ? `, with the door ${where}` : ''}.`, lowest(n.g, where ? eb.g : null)));
  else if (where) out.push(line(`The door is ${where}.`, eb.g));
  // A measured record with no front to count: the features it builds, in its own order.
  if (out.length < 3) {
    const feats = Object.entries(FEATURE).map(([k, [, w]]) => ({ a: attr(sc, k), w })).filter((x) => x.a).slice(0, 2);
    if (feats.length) {
      const words = feats.map((x) => x.w.charAt(0).toLowerCase() + x.w.slice(1));
      out.push(line(`It has ${words.join(' and ')}.`, lowest(...feats.map((x) => x.a.g))));
    }
  }
  return out.filter((l) => clean(l.text)).slice(0, 3);
}

/** How the model was built: the structure grade's own words (sidecar `grade.why`). */
function basisOf(sc) {
  const g = sc?.grade;
  const why = typeof g?.why === 'string' ? clean(g.why) : '';
  if (!why || !(g.value in RANK)) return null;
  const draft = !!attr(sc, 'draft');
  return { text: why, grade: g.value, draft };
}

/**
 * The style guide for one building.
 * @param {{ sidecar: object|null, sum: object|null, mod: object|null }} o
 */
export function styleGuide({ sidecar = null, sum = null, mod = null } = {}) {
  const head = headOf(sidecar, sum, mod);
  return {
    name: head.name,
    sub: head.sub,
    chips: head.chips,
    lead: leadOf(sidecar, head),
    look: standouts(sidecar),
    parts: partsOf(sidecar),
    basis: basisOf(sidecar),
  };
}

export const _test = { attr, roofForm, projections, footprintFt, glazingWords, storeysWords, nounOf };
