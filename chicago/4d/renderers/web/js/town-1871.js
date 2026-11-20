/**
 * T-3690 (the owner, 2026-11-19: "1871 people, horses and wagons on every street"): the 1871
 * city's carded people put on its own streets.
 *
 * data/humans/inside_1871.json (tools/town_people_1871.py) gives each household a place in the
 * city (`near`, [local_e, local_n]) and nothing finer, because the city it stands in is the
 * anonymous context city (data/context/1871.json, L-1871-city-baseline), regenerated as the
 * street and building work on it goes on. So the door and the places outside it are found here,
 * once at load, on the context city as it is today: the plank walk nearest the household's place,
 * the building face behind that walk (or the walk's house side where no building is near), a door
 * on that face, and for each person a place before the door (`front`), a few steps along it
 * (`front_end`), and a stretch of the walk to stroll (`stroll`, `stroll_end`). Everyone stands on
 * a walk and walks along one; nobody is put in a carriageway or inside a building.
 *
 * placeTown1871(inside, city) fills each entry's `points` and `door` in place and returns the
 * doors file human-days.js reads ({ structures: [{ structure, name, doors: [...] }] }) and a
 * census ({ households, placed, dropped }). A household with no walk within FIND_M of its place
 * is dropped (and counted), never put at a guess.
 */

const CELL_M = 64;
const FIND_M = 260;
const DOOR_SEARCH_M = 9;

function hashUnit(text) {
  let h = 2166136261;
  for (let i = 0; i < text.length; i += 1) { h ^= text.charCodeAt(i); h = Math.imul(h, 16777619); }
  return ((h >>> 0) % 100000) / 100000;
}

const bearing = (de, dn) => ((Math.atan2(de, dn) * 180 / Math.PI) + 360) % 360;
const r2 = (v) => Math.round(v * 100) / 100;

/** The context city's walks (kind 'walk') indexed by cell, for the nearest-walk search. */
export function walkIndex(surfaces = []) {
  const cells = new Map();
  const rows = [];
  for (const s of surfaces) {
    if (s?.kind !== 'walk' || !Array.isArray(s.a) || !Array.isArray(s.b) || !(s.width_m > 0)) continue;
    const de = s.b[0] - s.a[0], dn = s.b[1] - s.a[1], length = Math.hypot(de, dn);
    if (!(length > 2)) continue;
    const row = { id: s.id, a: s.a, ue: de / length, un: dn / length, length, half: s.width_m / 2, y: s.y };
    rows.push(row);
    const seen = new Set();
    for (let t = 0; t <= length + CELL_M / 2; t += CELL_M / 2) {
      const q = Math.min(t, length);
      const key = `${Math.floor((s.a[0] + row.ue * q) / CELL_M)},${Math.floor((s.a[1] + row.un * q) / CELL_M)}`;
      if (seen.has(key)) continue;
      seen.add(key);
      if (!cells.has(key)) cells.set(key, []);
      cells.get(key).push(row);
    }
  }
  return {
    rows,
    /** The nearest walk's foot point to (e, n) within `within` m: { row, along, d } or null. */
    nearest(e, n, within = FIND_M) {
      let best = null;
      const reach = Math.ceil(within / CELL_M);
      const ci = Math.floor(e / CELL_M), cj = Math.floor(n / CELL_M);
      for (let i = ci - reach; i <= ci + reach; i += 1) {
        for (let j = cj - reach; j <= cj + reach; j += 1) {
          for (const r of cells.get(`${i},${j}`) ?? []) {
            const de = e - r.a[0], dn = n - r.a[1];
            const along = Math.min(r.length, Math.max(0, de * r.ue + dn * r.un));
            const d = Math.hypot(e - (r.a[0] + r.ue * along), n - (r.a[1] + r.un * along));
            if (d <= within && (!best || d < best.d)) best = { row: r, along, d };
          }
        }
      }
      return best;
    },
  };
}

/**
 * Which side of a walk its houses stand on (+1 its left, -1 its right), and how far from its
 * middle the nearest building face is there: { side, face } (face null where no building is
 * within DOOR_SEARCH_M of the walk's edge). The house side is the side a building is found on,
 * else the side that is not a carriageway (the city's floor there is lower than the walk's).
 */
function houseSide(city, row, e, n) {
  const ne = -row.un, nn = row.ue;   // the walk's left
  let pick = null;
  for (const side of [1, -1]) {
    for (let t = row.half + .3; t <= row.half + DOOR_SEARCH_M; t += .5) {
      if (city.containsBuilding?.(e + side * ne * t, n + side * nn * t, 0)) {
        if (!pick || t < pick.face) pick = { side, face: t };
        break;
      }
    }
  }
  if (pick) return pick;
  for (const side of [1, -1]) {
    const y = city.floorHeight?.(e + side * ne * (row.half + 1.2), n + side * nn * (row.half + 1.2));
    if (Number.isFinite(y) && Number.isFinite(row.y) && y < row.y - .04) return { side: -side, face: null };
  }
  return { side: 1, face: null };
}

export function placeTown1871(inside, city) {
  const census = { households: 0, placed: 0, dropped: 0, faces: 0 };
  const index = walkIndex(city?.doc?.walk_surfaces ?? []);
  const structures = [];
  const homes = new Map();
  if (!index.rows.length) return { doors: { structures }, census, dropped: new Set() };
  const dropped = new Set();
  const entries = [...(inside?.people ?? []), ...(inside?.care ?? [])];
  for (const entry of entries) {
    if (!entry?.home || homes.has(entry.home) || dropped.has(entry.home)) continue;
    census.households += 1;
    const near = entry.near;
    const hit = Array.isArray(near) ? index.nearest(near[0], near[1]) : null;
    if (!hit) { dropped.add(entry.home); census.dropped += 1; continue; }
    const { row } = hit;
    // Keep the door off a walk's very ends (a corner), where the walk meets the cross street.
    const along = Math.min(row.length - 6, Math.max(6, hit.along));
    const e = row.a[0] + row.ue * along, n = row.a[1] + row.un * along;
    const { side, face } = houseSide(city, row, e, n);
    if (face != null) census.faces += 1;
    const ne = -row.un * side, nn = row.ue * side;   // toward the houses
    const leafT = face != null ? Math.max(row.half - .2, face - .35) : row.half - .15;
    const leaf = { local_e: r2(e + ne * leafT), local_n: r2(n + nn * leafT) };
    const step = { local_e: r2(e + ne * (leafT - .7)), local_n: r2(n + nn * (leafT - .7)) };
    const outward = r2(bearing(-ne, -nn));
    const id = `${entry.home}:front`;
    structures.push({ structure: entry.home, name: inside?.homes?.[entry.home] ?? null,
      doors: [{ id, leaf, step, outward_deg: outward, width_m: 1 }] });
    homes.set(entry.home, { row, along, side, ne, nn, outward, id });
    census.placed += 1;
  }
  for (const entry of entries) {
    const h = homes.get(entry.home);
    if (!h) continue;
    const { row, along, ne, nn, outward } = h;
    const u = (k) => hashUnit(`${entry.person}:${k}`);
    const at = (t, across) => {
      const q = Math.min(row.length - .5, Math.max(.5, t));
      return [r2(row.a[0] + row.ue * q + ne * across), r2(row.a[1] + row.un * q + nn * across)];
    };
    const width = row.half * 2;
    // Before their own door: within a few steps of it, on the house half of the walk.
    const f = along + (u('f') - .5) * 5;
    const front = [...at(f, row.half * (.15 + .5 * u('fx'))), outward];
    const dir = u('fd') < .5 ? -1 : 1;
    const frontEnd = at(f + dir * (6 + 12 * u('fe')), row.half * (.1 + .5 * u('fy')));
    // A stretch of the walk to stroll, on either half of it, either way.
    const sAt = along + (u('s') - .5) * 40;
    const sDir = (sAt + 60 > row.length) ? -1 : (sAt - 60 < 0) ? 1 : (u('sd') < .5 ? -1 : 1);
    const sx = (u('sx') - .5) * Math.max(.2, width - .9);
    const stroll = [...at(sAt, sx), r2(bearing(row.ue * sDir, row.un * sDir))];
    const strollEnd = at(sAt + sDir * (35 + 70 * u('se')), sx + (u('sy') - .5) * .4);
    entry.points = { front, front_end: frontEnd, stroll, stroll_end: strollEnd };
    entry.door = h.id;
  }
  if (dropped.size && inside) {
    inside.people = (inside.people ?? []).filter((x) => !dropped.has(x.home));
    inside.care = (inside.care ?? []).filter((x) => !dropped.has(x.home));
  }
  return { doors: { format: 'chicago4d_doors_runtime_1871', structures }, census, dropped };
}

/**
 * The height of the context city's roadway ribbons (kind 'road') at (e, n), or null off them:
 * what the 1871 teams' wheels and hooves stand on. The walks are left out: where a walk's
 * ribbon crosses a carriageway at a corner it lies a few centimetres above the roadway, and a
 * team reads the roadway it is drawn on, not the crossing walk over it.
 */
export function roadHeightOf(surfaces = [], cellM = 64) {
  const cells = new Map();
  for (const s of surfaces) {
    if (s?.kind !== 'road' || !Array.isArray(s.a) || !Array.isArray(s.b) || !(s.width_m > 0) || !Number.isFinite(s.y)) continue;
    const de = s.b[0] - s.a[0], dn = s.b[1] - s.a[1], length = Math.hypot(de, dn);
    if (!(length > 0)) continue;
    const row = { a: s.a, ue: de / length, un: dn / length, length, half: s.width_m / 2, y: s.y };
    const pad = row.half;
    for (let i = Math.floor((Math.min(s.a[0], s.b[0]) - pad) / cellM); i <= Math.floor((Math.max(s.a[0], s.b[0]) + pad) / cellM); i += 1) {
      for (let j = Math.floor((Math.min(s.a[1], s.b[1]) - pad) / cellM); j <= Math.floor((Math.max(s.a[1], s.b[1]) + pad) / cellM); j += 1) {
        // Only the cells the ribbon passes near (a long diagonal ribbon's box is not filled).
        const ce = (i + .5) * cellM, cn = (j + .5) * cellM;
        const along = Math.min(length, Math.max(0, (ce - s.a[0]) * row.ue + (cn - s.a[1]) * row.un));
        if (Math.hypot(ce - (s.a[0] + row.ue * along), cn - (s.a[1] + row.un * along)) > cellM + pad) continue;
        const key = `${i},${j}`;
        if (!cells.has(key)) cells.set(key, []);
        cells.get(key).push(row);
      }
    }
  }
  return (e, n) => {
    let y = null;
    for (const r of cells.get(`${Math.floor(e / cellM)},${Math.floor(n / cellM)}`) ?? []) {
      const de = e - r.a[0], dn = n - r.a[1];
      const along = de * r.ue + dn * r.un, across = -de * r.un + dn * r.ue;
      if (along < 0 || along > r.length || Math.abs(across) > r.half) continue;
      if (y === null || r.y > y) y = r.y;
    }
    return y;
  };
}
