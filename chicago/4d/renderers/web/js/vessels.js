/**
 * vessels.js — the working vessels of the river and the lake, 1812 and 1835 (T-3612).
 *
 * The owner, 2026-11-16: "the schooners boats in 1835 we're not realistic they should phot
 * match correct boats for 1835 with realistic wood and working crews on the boats, which some
 * may be anchored but others move down and around the river up or down river making a circuit
 * in and up or out to lake paths ... logically with time of day and season ... Would be nice if
 * I can board and pilot the schooners and all boats".
 *
 * data/boats/vessels_<scene>.json (tools/lay_vessels.py) lays every hull: moored, at anchor,
 * drawn up on the bank, alongside another, or under sail round the harbour loop. Each is built
 * at load by vessel-model.js (a planked hull, its rig and canvas, its fittings: no texture, no
 * model file). This layer:
 *
 *  - moves the sailing schooners round their loop by day, sails trimmed to the scene's wind and
 *    heeled to it, and brings each to its resting place at nightfall (the basin below the bend,
 *    or an anchorage in the offing);
 *  - lays every vessel up for the winter (canvas off, snow on the decks, nobody aboard) or takes
 *    it out of the scene when the record says it was not here then;
 *  - puts a crew aboard a schooner the visitor is near (anonymous working men, the profile's own
 *    reconstructed figures), standing their stations or walking the deck, an anchor watch at night;
 *  - answers a pick with the vessel's own card, and offers Take the helm (boat-pilot.js steers);
 *  - hands boat-pilot.js the navigation rules the file carries (obstacles, channel, depths).
 *
 * Every vertex is `reconstructed` for the Confidence view: the hulls are ours (L-vessels-3612)
 * even where the vessel's presence is documented.
 */
import * as THREE from 'three';
import { buildVessel, vesselLight } from './vessel-model.js';
import { resolveHumanIdentity } from './human-identity.js';

const DEG = Math.PI / 180;
const WATER_Y = 0;
/** A crew is aboard while the camera is this near (by detail), and never more than these at once. */
const CREW_NEAR_M = { full: 170, balanced: 140, light: 110 };
const CREW_CAP = { full: 14, balanced: 10, light: 6 };
/** Rope and ratlines are drawn this near; past it a hairline is noise. */
const DETAIL_NEAR_M = 220;
/** A boat the visitor left goes home once they are this far off, or out of sight and half as far. */
const HOME_FAR_M = 380;
const LAKE_E = 1520;
const CREW_PROFILE = { 1835: 'anonymous_adult_1835' };
const CREW_ASSET = { 1835: 'mahoney_patrick_1835' };
/** The town's own seamen and boatmen, considered for a crew and found standing ashore (their own days). */
const CREW_CONSIDERED = ['rc_newell_hiram', 'rc_tuttle_benjamin', 'rc_bourassa_hyacinthe', 'rc_dufresne_hyacinthe', 'rc_robillard_michel'];
const CREW_FALLBACK = 'The crews of the hulls the Marine Journal enters at this port came in with them from Green Bay, Milwaukee, Michigan and St. Joseph, and no record names a man of any of them. The town\'s own seaman, master mariner and boatmen are considered, and stand ashore at their own houses by their own days, so the hands aboard are anonymous working men.';
const CREW_BASIS = 'An anonymous hand of a lake schooner, 1835: his stations and his work are reconstructed (L-vessels-3612), never a man of the vessel\'s own crew, whom no record names.';

const KIND_WORDS = {
  topsail_schooner: 'A two-masted topsail schooner of the lakes: a fore-and-aft rig on both masts, a square topsail and a course on the fore, headsails on a long bowsprit, carvel planked, a cabin aft.',
  mackinaw_boat: 'A Mackinaw boat: an open, double-ended boat of the lake trade, planked, with a mast and a spritsail and oars, the freight boat of the traders and the lighters of the lake vessels.',
  bateau: 'A bateau: a flat-bottomed boat of sawn plank, flared and pointed at both ends, rowed.',
  rowboat: 'A rowboat of the river: a small planked boat with a transom, rowed with a pair of oars.',
  bark_canoe: 'A canoe of bark sewn over a light frame of ribs and gunwale poles, paddled.',
};
const PILOT_LABEL = {
  topsail_schooner: 'Go aboard and take the helm', mackinaw_boat: 'Take the steering oar',
  bateau: 'Take the oars', rowboat: 'Take the oars', bark_canoe: 'Take the paddle',
};

const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const turn = (a, b) => ((b - a + 540) % 360) - 180;

/** Local (x forward, z starboard) on a pose → ENU. */
export function localToEnu(pose, x, z) {
  const b = pose.bearing * DEG, fe = Math.sin(b), fn = Math.cos(b);
  return { e: pose.e + fe * x + fn * z, n: pose.n + fn * x - fe * z };
}

function placeGroup(g, p) {
  g.position.set(p.e, p.y ?? WATER_Y, -p.n);
  g.rotation.set(p.roll ?? 0, (90 - p.bearing) * DEG, p.pitch ?? 0, 'YZX');
}

/** The closed loop's pose `s` metres round it. */
function loopAt(route, s) {
  const pts = route.points, n = pts.length, step = route.length_m / n;
  const u = (((s % route.length_m) + route.length_m) % route.length_m) / step;
  const i = Math.floor(u) % n, f = u - Math.floor(u);
  const a = pts[i], b = pts[(i + 1) % n];
  return { e: lerp(a[0], b[0], f), n: lerp(a[1], b[1], f), bearing: (a[2] + turn(a[2], b[2]) * f + 360) % 360, i };
}

/** How the canvas sits on a heading, for the scene's wind. */
export function trimFor(bearing, windFrom) {
  const rel = ((windFrom - bearing) % 360 + 360) % 360;
  const side = rel > 180 ? 1 : -1;              // over the port side: the booms go to starboard
  const off = rel > 180 ? 360 - rel : rel;       // 0 dead ahead … 180 dead astern
  return {
    side, off,
    boom: Math.round(clamp(6 + (off - 35) * 0.45, 6, 70) / 2) * 2,
    brace: Math.round(clamp(10 + (off - 45) * 0.3, 5, 40) / 2) * 2,
    heel: side * (off < 40 ? 1.5 : off < 120 ? 4.5 : 2.5) * DEG,
  };
}

function cardRecordFor(v, ctx) {
  const rec = v.rec, ex = rec.existence ?? {}, h = rec.hull;
  const named = rec.name && (!rec.named_on || ctx.season === 'summer');
  const name = named ? (rec.kind === 'topsail_schooner' ? `The schooner ${rec.name}` : rec.name)
    : (rec.title ?? `A ${rec.rig_words?.replace(/^an? /, '') ?? 'boat'}`);
  const r = (value, note, confidence = 'reconstructed', sources = []) => ({ value, confidence, sources, note });
  const doing = {
    sailing: 'Under sail round the harbour: out of the river between the piers, a turn in the lake and in again.',
    resting: rec.circuit?.rest === 'offing' ? 'At anchor in the offing for the night.' : 'At anchor in the basin below the bend for the night.',
    laid_up: 'Laid up for the winter, her canvas unbent and ashore.',
    piloted: 'Under your hand.',
    left: 'Where you left her.',
  }[v.state] ?? v.dated?.doing ?? rec.doing ?? '';
  const attributes = {
    kind: r(rec.rig_words, KIND_WORDS[rec.kind] ?? ''),
    existence: r(ex.confidence === 'reconstructed' ? 'reconstructed' : 'recorded', ex.note ?? '', ex.confidence ?? 'reconstructed', ex.sources ?? []),
    length_m: r(h.length_m, 'Reconstructed within the run of its kind.'),
    beam_m: r(h.beam_m, 'Reconstructed within the run of its kind.'),
    draft_m: r(h.draft_m, 'Reconstructed; the pilot holds the boat to water this deep.'),
  };
  if (named && rec.master) attributes.master = r(rec.master, `The Marine Journal's own spelling of her master's name.`, ex.confidence ?? 'documented', ex.sources ?? []);
  if (!named && rec.named_on) {
    attributes.name = r('not known at this season', `The Marine Journal enters her by name across ${rec.named_on}; which hulls lay here at other seasons is not recorded, so she goes unnamed.`);
  }
  return {
    id: rec.id,
    sidecar: {
      name,
      phase: null,
      placement: {
        local_e: v.pose.e, local_n: v.pose.n,
        symbolic_location: doing,
        position_confidence: 'reconstructed', position_sources: [],
        position_note: 'Where she lies and where she sails are ours: laid by tools/lay_vessels.py on the scene\'s water.',
        vertical_anchor: 'water',
      },
      attributes,
      citations: [],
      research_note: `${KIND_WORDS[rec.kind] ?? ''} ${ex.note ?? ''} ${rec.crew?.day ? 'Her hands are anonymous working men: no record names any of her crew. ' : ''}`
        + `Her build, colours and rig are reconstructed; see ${rec.liberty}. Walk up to her and Interact to ${PILOT_LABEL[rec.kind]?.toLowerCase() ?? 'take her'}.`,
    },
  };
}

/**
 * @param {object} o
 *   dataBase · sceneId · terrain · confidence · problems · detail · coarse · humans (the people
 *   layer, for crews) · getPeople () => Promise<{people}> · hour () => number|null · season () =>
 *   'summer'|'spring'|'fall'|'winter' · pilot () => the boat pilot (boat-pilot.js), once made
 */
export async function createVessels({
  dataBase, sceneId, terrain, confidence = null, problems = [], detail = 'full', coarse = false,
  humans = null, getPeople = null, hour = () => null, season = () => 'summer', pilot = () => null,
  date = () => null,
} = {}) {
  const group = new THREE.Group();
  group.name = 'vessels';
  const out = {
    group, vessels: [], things: [], keepOut: [], nav: null, doc: null,
    census: { vessels: 0, schooners: 0, sailing: 0, crew: 0, refused: 0 },
    pickAt: () => null, update: () => {}, craftOf: () => null, hulls: () => [], dispose: () => {},
  };
  if (!dataBase || !terrain) return out;
  let doc;
  try {
    const res = await fetch(new URL(`boats/vessels_${sceneId}.json`, dataBase), { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${res.status} — boats/vessels_${sceneId}.json`);
    doc = await res.json();
  } catch (err) {
    problems.push(`vessels: ${err.message}`);
    return out;
  }
  out.doc = doc;
  out.nav = doc.navigation ?? null;
  const route = doc.routes?.harbour_loop ?? null;
  const windFrom = doc.wind?.from_bearing ?? 290;
  const sailFrom = doc.sailing_hours?.from ?? 6, sailTo = doc.sailing_hours?.to ?? 19.5;
  const tier = coarse ? 'light' : (detail === 'light' ? 'light' : detail === 'balanced' ? 'balanced' : 'full');
  const byId = new Map();
  const peopleLayer = () => (typeof humans === 'function' ? humans() : humans);

  for (const rec of doc.vessels ?? []) {
    let model;
    try {
      model = buildVessel({ ...rec, id: rec.id }, { confidence, coarse });
    } catch (err) {
      problems.push(`vessels: ${rec.id} refused — ${err.message}`);
      out.census.refused++;
      continue;
    }
    model.group.traverse((o) => { o.userData.vessel = rec.id; });
    const b = rec.berth;
    const v = {
      rec, model, id: rec.id, kind: rec.kind,
      L: rec.hull.length_m, B: rec.hull.beam_m, T: rec.hull.draft_m,
      pose: { e: b.e, n: b.n, bearing: b.bearing, roll: 0, pitch: 0, y: WATER_Y },
      state: rec.mode, s: 0, speed: 0, crew: [], crewKey: '', present: true,
      seed: (rec.look?.seed ?? 1) * 0.37, trim: null, sails: null, detailNear: true,
    };
    if (rec.mode === 'circuit' && route) {
      v.restS = route.length_m * (rec.circuit.rest_index / route.points.length);
      v.s = v.restS;
    }
    if (rec.mode === 'beached') beachPose(v);
    placeGroup(model.group, v.pose);
    group.add(model.group);
    out.vessels.push(v);
    byId.set(rec.id, v);
    out.census.vessels++;
    if (rec.kind === 'topsail_schooner') out.census.schooners++;
    if (rec.mode === 'beached') {
      const pts = model.hullOutline().map(([x, z]) => { const q = localToEnu(v.pose, x, z); return [q.e, q.n]; });
      out.keepOut.push({ id: `${rec.id}__hull`, pts });
    }
    v.thing = thingFor(v);
    out.things.push(v.thing);
  }

  /** A hull drawn up on the bank sits on the ground at bow and stern, its stern afloat if the water reaches it. */
  function beachPose(v) {
    const p = v.pose;
    const bow = localToEnu(p, v.L * 0.45, 0), stern = localToEnu(p, -v.L * 0.45, 0);
    const keel = (q) => Math.max(terrain.surfaceHeight(q.e, q.n), WATER_Y - v.T);
    const yb = keel(bow), ys = keel(stern);
    p.pitch = Math.atan2(yb - ys, v.L * 0.9);
    p.y = (yb + ys) / 2 + v.T - 0.04;
    p.roll = (v.rec.look?.seed ?? 1) % 2 ? 3 * DEG : -2.5 * DEG;
  }

  function homePose(v) {
    const b = v.dated?.berth ?? v.rec.berth;
    v.pose = { e: b.e, n: b.n, bearing: b.bearing, roll: 0, pitch: 0, y: WATER_Y };
    if (v.rec.mode === 'circuit' && route) v.s = v.restS;
    if (v.rec.mode === 'beached') beachPose(v);
    v.speed = 0;
  }

  /* ---------------------------------------------------------------- the pilot */

  function displayName(v, sea) {
    const rec = v.rec;
    if (rec.name && (!rec.named_on || sea === 'summer')) return rec.kind === 'topsail_schooner' ? `the ${rec.name}` : rec.name.replace(/^The /, 'the ');
    return { topsail_schooner: 'a schooner', mackinaw_boat: 'a Mackinaw boat', bateau: 'a bateau', rowboat: 'a rowboat', bark_canoe: 'a bark canoe' }[rec.kind] ?? 'a boat';
  }

  /** What boat-pilot.js steers: this vessel's pose, its helm and how it moves. */
  function craftOf(v) {
    if (v.craft) return v.craft;
    const m = v.model;
    v.craft = {
      id: v.id, layer: 'vessels', kind: v.kind, masted: !!m.masted,
      length: v.L, beam: v.B, draft: v.T, airDraft: m.dims.airDraft,
      helm: m.helm,
      get name() { return displayName(v, season()); },
      get pose() { return v.pose; },
      begin() {
        v.state = 'piloted';
        v.speed = 0;
        if (v.rec.mode === 'beached') {
          // Run her off the bank: the nearest water that floats her, bow out.
          const launch = launchPose(v);
          if (launch) Object.assign(v.pose, launch);
        }
        v.pose.y = WATER_Y; v.pose.pitch = 0; v.pose.roll = 0;
        placeGroup(m.group, v.pose);
      },
      move(p, { speed = 0, rudder = 0 } = {}) {
        v.pose.e = p.e; v.pose.n = p.n; v.pose.bearing = p.bearing;
        v.speed = speed;
        v.rudder = rudder;
      },
      end() { v.state = 'left'; v.speed = 0; },
    };
    return v.craft;
  }
  out.craftOf = (id) => { const v = byId.get(id); return v ? craftOf(v) : null; };

  function launchPose(v) {
    const p = v.pose, need = v.T + 0.1;
    let best = null;
    for (let r = 2; r <= 18 && !best; r += 1.5) {
      for (let k = 0; k < 24; k++) {
        const a = (k / 24) * 360, rad = a * DEG;
        const e = p.e + Math.sin(rad) * r, n = p.n + Math.cos(rad) * r;
        const ok = [0, v.L * 0.45, -v.L * 0.45].every((x) => {
          const q = localToEnu({ e, n, bearing: a }, x, 0);
          return -terrain.surfaceHeight(q.e, q.n) >= need;
        });
        if (ok) { best = { e, n, bearing: a }; break; }
      }
    }
    return best;
  }

  function thingFor(v) {
    const rec = v.rec;
    const schooner = rec.kind === 'topsail_schooner';
    return {
      id: `vessel:${rec.id}`,
      name: rec.name ?? rec.title ?? rec.rig_words,
      kind: 'boat',
      states: ['here', 'aboard'],
      state: 'here',
      at: [v.pose.e, v.pose.n],
      // A schooner in the stream is hailed from the bank: a boat puts the visitor aboard.
      reach: schooner ? v.L / 2 + 30 : Math.max(4.5, v.L / 2 + 2.5),
      actions: {
        here: [{
          id: 'pilot',
          label: PILOT_LABEL[rec.kind] ?? 'Take her',
          said: () => `Aboard ${displayName(v, season())}`,
          refuse: () => {
            if (!v.present) return 'Not here at this season';
            if (v.state === 'laid_up') return 'Laid up for the winter: the river is frozen';
            const p = pilot();
            if (!p) return 'Nobody can take a boat here';
            if (p.active) return 'Already at the helm of a boat';
            return null;
          },
          steps: [
            { label: schooner ? 'Hailing her: a boat puts you aboard' : 'Stepping in', seconds: schooner ? 1.6 : 1.0, run: (t) => { if (t >= 1) pilot()?.take(craftOf(v)); } },
          ],
        }],
        // At her helm, the key puts the visitor ashore (the travel bar's Go ashore does the same).
        aboard: [{
          id: 'ashore', label: 'Go ashore', said: () => 'Ashore',
          refuse: () => (pilot()?.craft?.id === v.id ? null : 'Not aboard'),
          steps: [{ label: 'Going ashore', seconds: 0.4, run: (t) => { if (t >= 1) pilot()?.leave(); } }],
        }],
      },
    };
  }

  /* ---------------------------------------------------------------- the crews */

  let crewKit = null;      // { profile, people } once loaded, false when this scene has none
  let crewLoading = null;
  function loadCrewKit() {
    if (crewKit !== null || crewLoading) return;
    const pid = CREW_PROFILE[sceneId];
    if (!pid) { crewKit = false; return; }
    // The people layer mounts after this one: asked for again until it is there.
    if (!peopleLayer()?.createActor) return;
    crewLoading = (async () => {
      try {
        const res = await fetch(new URL(`humans/role_profiles/${pid}.json`, dataBase));
        if (!res.ok) throw new Error(`${res.status} — ${pid}`);
        const profile = await res.json();
        const dir = (await getPeople?.()) ?? null;
        const people = Array.isArray(dir?.people) ? dir.people : [];
        crewKit = { profile, people, considered: CREW_CONSIDERED.filter((id) => people.some((p) => p.id === id)) };
      } catch (err) {
        problems.push(`vessels: no crews — ${err.message}`);
        crewKit = false;
      } finally { crewLoading = null; }
    })();
  }

  /** The jobs aboard by what the vessel is doing: [station id | 'walk', state]. */
  function jobsFor(v, day) {
    const piloted = v.state === 'piloted';
    if (v.state === 'sailing' || piloted) return [[piloted ? 'main_rail' : 'helm', 'standing'], ['fore_rail', 'standing'], ['walk', 'walking']];
    if (!day) return [['helm', 'standing']];
    if (v.state === 'resting' || v.state === 'anchored') return [['main_rail', 'standing'], ['walk', 'walking']];
    return [['main_hatch_s', 'standing'], ['main_hatch_p', 'standing'], ['walk', 'walking']];
  }

  function makeCrew(v, k, job) {
    const { profile, people, considered } = crewKit;
    const [where, state] = job;
    const instance = {
      id: `crew:${v.id}:${k}`, contract_version: 1, scene: String(sceneId), display: 'shown', review_required: false,
      anonymous_profile_id: profile.id, role: state === 'walking' ? 'walking' : 'standing',
      fallback_basis: CREW_FALLBACK, considered_person_ids: considered,
      appearance: { asset_id: CREW_ASSET[sceneId] },
      placement: { local_e: v.pose.e, local_n: v.pose.n, heading_deg: v.pose.bearing, anchor: 'terrain' },
      animation: { clip: 'idle', loop: true, phase: (k * 0.37) % 1 },
      behaviour: { state }, interaction: { selectable: false, radius_m: 0, opens: 'none' },
      lod: { policy: 'auto' },
      provenance: { grade: 'reconstructed', basis: CREW_BASIS, liberty: v.rec.liberty },
    };
    const identity = resolveHumanIdentity(instance, { sceneId: String(sceneId), people, profiles: [profile] });
    const actor = peopleLayer().createActor(instance, { identity });
    const c = { actor, where, state, walkT: k * 0.31, v };
    actor.standY = WATER_Y;
    actor.tow = () => crewAt(c);
    actor.setState?.(state);
    group.add(actor.root);
    return c;
  }

  function stationOf(v, id) {
    return v.model.stations.find((s) => s.id === id) ?? v.model.stations[0];
  }

  /** Where a hand stands this frame: on the deck, wherever the vessel is. */
  function crewAt(c) {
    const v = c.v, m = v.model;
    let x, z, heading;
    if (c.where === 'walk' && m.walk?.length > 1) {
      const pts = m.walk, n = pts.length;
      const u = ((c.walkT % n) + n) % n, i = Math.floor(u), f = u - i;
      const a = pts[i], b = pts[(i + 1) % n];
      x = lerp(a[0], b[0], f); z = lerp(a[1], b[1], f);
      // Local +x is ahead and +z starboard, so the way he faces is clockwise from the bow.
      heading = Math.atan2(b[1] - a[1], b[0] - a[0]) / DEG;
    } else {
      const s = stationOf(v, c.where);
      x = s.x; z = s.z; heading = s.heading ?? 0;
    }
    const q = localToEnu(v.pose, x, z);
    c.actor.standY = (v.pose.y ?? WATER_Y) + m.deckY(x) + x * Math.sin(v.pose.pitch ?? 0) - z * Math.sin(v.pose.roll ?? 0);
    return { e: q.e, n: q.n, heading: (v.pose.bearing + heading + 360) % 360 };
  }

  function stepCrew(c, dt) {
    if (c.where !== 'walk') return;
    const pts = c.v.model.walk;
    if (!pts?.length) return;
    const n = pts.length, i = Math.floor(((c.walkT % n) + n) % n);
    const a = pts[i], b = pts[(i + 1) % n];
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    c.walkT += (0.85 * dt) / len;
  }

  function dropCrew(v) {
    for (const c of v.crew) { try { c.actor.dispose(); } catch { /* gone */ } c.actor.root.removeFromParent(); }
    v.crew = [];
    v.crewKey = '';
  }

  /* ---------------------------------------------------------------- the day */

  let checkIn = 0, clock = 0;
  let lastSeason = null, lastDay = null;
  const frustum = new THREE.Frustum(), projView = new THREE.Matrix4(), sphere = new THREE.Sphere();

  function present(v, sea) {
    if (sea === 'winter' && v.rec.winter === 'absent') return false;
    return true;
  }

  /** Season and hour: who is here, what each is doing, its canvas. */
  function toRest(v) {
    v.s = v.restS; v.state = 'resting'; v.speed = 0; v.sails = null;
    const p = loopAt(route, v.s);
    v.pose.e = p.e; v.pose.n = p.n; v.pose.bearing = p.bearing;
  }

  function settle(sea, day, unseen = null) {
    const winter = sea === 'winter';
    const today = date() ?? null;
    for (const v of out.vessels) {
      // A jaunt's stop on another day can find a boat elsewhere that day (the 1812 battle's).
      if (v.rec.dated) {
        const d = (today && v.rec.dated.find((x) => today >= x.from && today <= x.to)) || null;
        if (d !== (v.dated ?? null)) {
          v.dated = d;
          if (['moored', 'anchored', 'beached', 'alongside'].includes(v.state)) homePose(v);
        }
      }
      const here = present(v, sea);
      if (here !== v.present) {
        v.present = here; v.model.group.visible = here;
        if (!here) { dropCrew(v); v.state = 'absent'; v.speed = 0; } else if (v.state === 'absent') { v.state = v.rec.mode; homePose(v); v.sails = null; }
      }
      if (!here) continue;
      if (v.state === 'piloted' || v.state === 'left') continue;
      if (winter) {
        if (v.state !== 'laid_up') {
          v.state = 'laid_up';
          const wb = v.rec.winter_berth ?? v.rec.berth;
          v.pose = { e: wb.e, n: wb.n, bearing: wb.bearing, roll: 0, pitch: 0, y: WATER_Y };
          if (v.rec.mode === 'beached') beachPose(v);
        }
        continue;
      }
      if (v.state === 'laid_up') { v.state = v.rec.mode; homePose(v); }
      if (v.rec.mode === 'circuit' && route) {
        if (day && (v.state === 'resting' || v.state === 'circuit')) v.state = 'sailing';
        else if (!day && v.state === 'circuit') v.state = 'resting';
        // Nightfall out of the visitor's sight: she is already brought up at her resting place.
        else if (!day && v.state === 'sailing' && unseen?.(v)) toRest(v);
      }
    }
  }

  function sailsFor(v, sea) {
    const m = v.model;
    if (!m.masted && !m.hasSail) return;
    let want = 'furled', trim = null;
    if (v.state === 'laid_up') want = 'bare';
    else if (v.state === 'sailing' || (v.state === 'piloted' && Math.abs(v.speed) > 0.25)) {
      want = 'set';
      trim = trimFor(v.pose.bearing, windFrom);
    }
    const key = want === 'set' ? `set:${trim.side}:${trim.boom}:${trim.brace}` : want;
    if (key === v.sails) return trim;
    v.sails = key;
    if (want === 'set') m.setSails('set', trim.side, trim.boom, trim.brace);
    else m.setSails(want);
    return trim;
  }

  /** The sailing loop: on round it by day; at nightfall on to its resting place, and there. */
  function sail(v, dt, day, pilotCraft) {
    if (!route || v.state !== 'sailing') return;
    const L = route.length_m;
    // Slower through the turns and in the river, more way on in the open lake.
    const here = loopAt(route, v.s), ahead = loopAt(route, v.s + 14);
    const bend = Math.abs(turn(here.bearing, ahead.bearing));
    let target = (v.rec.circuit.speed_m_s ?? 2.4) * (here.e > LAKE_E ? 1.3 : 1) * (bend > 25 ? 0.55 : bend > 12 ? 0.8 : 1);
    // She heaves to for a boat the visitor holds across her bow.
    if (pilotCraft && pilotCraft.id !== v.id) {
      const bow = localToEnu(v.pose, v.L / 2 + 10, 0);
      const pp = pilotCraft.pose;
      if (Math.hypot(pp.e - bow.e, pp.n - bow.n) < pilotCraft.length / 2 + 12) target = 0;
    }
    v.speed += clamp(target - v.speed, -0.4 * dt, 0.15 * dt);
    const s0 = v.s, s1 = v.s + v.speed * dt;
    if (!day) {
      // Passing her resting place: she brings up there.
      const d0 = ((v.restS - s0) % L + L) % L;
      if (d0 <= s1 - s0 + 1e-6) { v.s = v.restS; v.state = 'resting'; v.speed = 0; }
      else v.s = s1 % L;
    } else v.s = s1 % L;
    const p = loopAt(route, v.s);
    v.pose.e = p.e; v.pose.n = p.n; v.pose.bearing = p.bearing;
  }

  /** The water's own motion, and the heel of a vessel under canvas. */
  function ride(v, trim) {
    if (v.rec.mode === 'beached' && v.state !== 'piloted' && v.state !== 'left') return;
    const lake = v.pose.e > LAKE_E;
    const a = lake ? 1 : 0.25;
    const t = clock + v.seed * 10;
    const scale = v.L > 15 ? 1 : 1.6;
    v.pose.y = WATER_Y + Math.sin(t * 0.9) * 0.05 * a * scale;
    v.pose.pitch = Math.sin(t * 0.7 + 1.3) * 0.9 * DEG * a * (v.L > 15 ? 0.6 : 1.2);
    const heel = trim && (v.state === 'sailing' || v.state === 'piloted') ? trim.heel * clamp(Math.abs(v.speed) / 1.5, 0, 1) : 0;
    v.pose.roll = heel + Math.sin(t * 0.55 + 0.4) * 1.1 * DEG * a * scale;
  }

  out.update = (dt, camera) => {
    if (!camera) return;
    dt = Math.min(Math.max(dt, 0), 0.25);
    clock += dt;
    const sea = season() ?? 'summer';
    const h = hour();
    const day = h == null || (h >= sailFrom && h < sailTo);
    // The light through the canvas: full by day, none at night, eased through dawn and dusk.
    vesselLight.value = h == null ? 1 : clamp(Math.min(h - 4.5, 20.5 - h) / 1.5, 0, 1);
    const pilotNow = pilot()?.active ? pilot().craft : null;
    if ((checkIn -= dt) <= 0 || sea !== lastSeason) {
      checkIn = 0.5;
      lastSeason = sea;
      projView.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
      frustum.setFromProjectionMatrix(projView);
      const away = (v) => {
        const d = Math.hypot(v.pose.e - camera.position.x, v.pose.n + camera.position.z);
        sphere.center.set(v.pose.e, 4, -v.pose.n); sphere.radius = v.L;
        return d > HOME_FAR_M || (!frustum.intersectsSphere(sphere) && d > HOME_FAR_M / 2);
      };
      // A change of hour is one step (the frame is relit at once), so the boats keep up at once too.
      settle(sea, day, day !== lastDay ? () => true : away);
      lastDay = day;
      for (const v of out.vessels) {
        if (v.state !== 'left') continue;
        // Gone home once the visitor is well away, or out of sight of them.
        if (away(v)) {
          v.state = v.rec.mode;
          homePose(v);
          v.sails = null;
          settle(sea, day);
        }
      }
      updateCrews(camera, day, sea);
    }
    let sailing = 0;
    const ce = camera.position.x, cn = -camera.position.z;
    for (const v of out.vessels) {
      if (!v.present) continue;
      sail(v, dt, day, pilotNow);
      if (v.state === 'sailing') sailing++;
      const trim = sailsFor(v, sea);
      const near = Math.hypot(v.pose.e - ce, v.pose.n - cn) < DETAIL_NEAR_M;
      if (near !== v.detailNear) { v.detailNear = near; v.model.setDetail(near); }
      ride(v, trim ?? (v.sails?.startsWith('set') ? trimFor(v.pose.bearing, windFrom) : null));
      if (v.model.stroke) v.model.stroke((clock * 0.55) % 1, v.state === 'piloted' && Math.abs(v.speed) > 0.1);
      placeGroup(v.model.group, v.pose);
      v.thing.at = [v.pose.e, v.pose.n];
      v.thing.state = pilotNow?.id === v.id ? 'aboard' : 'here';
      for (const c of v.crew) { stepCrew(c, dt); c.actor.update(dt, camera.position); }
    }
    out.census.sailing = sailing;
  };

  function updateCrews(camera, day, sea) {
    const ce = camera.position.x, cn = -camera.position.z;
    const near = CREW_NEAR_M[tier], cap = CREW_CAP[tier];
    const wanted = [];
    for (const v of out.vessels) {
      const count = v.present && v.state !== 'laid_up' && sea !== 'winter' ? (day ? v.rec.crew?.day : v.rec.crew?.night) ?? 0 : 0;
      const d = Math.hypot(v.pose.e - ce, v.pose.n - cn);
      if (count > 0 && d < near) wanted.push({ v, d, count: coarse ? Math.min(count, 2) : count });
      else if (v.crew.length) dropCrew(v);
    }
    if (wanted.length) loadCrewKit();
    if (!crewKit) return;
    wanted.sort((a, b) => a.d - b.d);
    let left = cap;
    for (const w of wanted) {
      const jobs = jobsFor(w.v, day).slice(0, Math.min(w.count, left));
      left -= jobs.length;
      const key = jobs.map((j) => j.join('/')).join(',');
      if (key === w.v.crewKey) continue;
      dropCrew(w.v);
      try {
        w.v.crew = jobs.map((job, k) => makeCrew(w.v, k, job));
        w.v.crewKey = key;
      } catch (err) {
        problems.push(`vessels: crew refused — ${err.message}`);
        crewKit = false;
        return;
      }
    }
    out.census.crew = out.vessels.reduce((a, v) => a + v.crew.length, 0);
  }

  /** For the smoke and the Inspector: whether crews can be made here, and how many stand aboard. */
  out.crewState = () => ({ kit: crewKit === null ? 'unloaded' : crewKit ? 'ready' : 'none', loading: !!crewLoading,
    aboard: out.vessels.reduce((a, v) => a + v.crew.length, 0) });

  /** The hulls on the water now, for the pilot's clearance: { id, e, n, bearing, length, beam }. */
  out.hulls = () => out.vessels.filter((v) => v.present).map((v) => ({
    id: v.id, e: v.pose.e, n: v.pose.n, bearing: v.pose.bearing, length: v.L, beam: v.B, beached: v.rec.mode === 'beached' && v.state !== 'piloted' && v.state !== 'left',
  }));

  /* ---------------------------------------------------------------- picking */

  const raycaster = new THREE.Raycaster();
  raycaster.params.Line.threshold = 0.15;
  const ray = new THREE.Ray();
  out.pickAt = (ndc, camera) => {
    if (!camera) return null;
    raycaster.setFromCamera(ndc ?? new THREE.Vector2(0, 0), camera);
    raycaster.far = 900;
    let best = null;
    for (const v of out.vessels) {
      if (!v.present || !v.model.group.visible) continue;
      const hits = raycaster.intersectObject(v.model.group, true).filter((h) => h.object.name !== 'water-lid');
      if (hits.length && (!best || hits[0].distance < best.distance)) best = { v, distance: hits[0].distance, point: hits[0].point.clone() };
      // A hand aboard answers for his vessel.
      ray.copy(raycaster.ray);
      for (const c of v.crew) {
        const p = c.actor.root.position;
        const foot = new THREE.Vector3(p.x, p.y, p.z), head = new THREE.Vector3(p.x, p.y + 1.75, p.z);
        const sq = ray.distanceSqToSegment(foot, head, null, null);
        if (sq < 0.35 * 0.35) {
          const d = ray.origin.distanceTo(p);
          if (!best || d < best.distance) best = { v, distance: d, point: p.clone() };
        }
      }
    }
    if (!best) return null;
    return { id: best.v.id, record: cardRecordFor(best.v, { season: season() }), point: best.point, distance: best.distance };
  };

  out.dispose = () => {
    for (const v of out.vessels) { dropCrew(v); v.model.dispose(); }
  };
  group.userData.census = out.census;
  return out;
}
