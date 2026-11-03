/**
 * fort-gates.js — Fort Dearborn's gates, hung so a visitor can work them (T-3319).
 *
 * The owner, 2026-11-02: *"you should be able to enter the fort in both 1812 and 1835,
 * be able to walk through the gate ... the gate by default is closed and you can click
 * on interact"*. Until then each stockade was one solid footprint to the walker, so the
 * whole fort was a block a visitor was pushed out of, and its gates were two shut leaves
 * baked into the picket mesh.
 *
 * So for the stockades named in FORT_GATES this layer:
 *
 *   - reads the stockade's own record (footprint, gate_sides, gate_width_m,
 *     gate_offset_m, bastions, picket height) exactly as generators/archetypes/
 *     palisade.py builds it, and hands the walker its WALLS: the curtain with each
 *     gateway cut out, the bastions' returns, and across each gateway a span that blocks
 *     while the gate is shut (walker.js § enclosure). The footprint stays in the array
 *     whole, so nothing grows in the fort and the router and framing read what they did;
 *   - draws each gate's two leaves itself, hinged on the jambs the mesh draws, and the
 *     buildings layer leaves out the baked shut leaves of these records only
 *     (`drawsLeaves`, read in buildings.js) — the `dark` primitive, which on a palisade
 *     is the leaves and nothing else (tools/measure_fort_gates.py reads the same one);
 *   - offers each gate to interact.js as a thing with two states, `closed` (where every
 *     gate starts) and `open`, and one action from each: a swing of the two leaves
 *     inward through 90 degrees.
 *
 * What is ours, and claimed at docs/LIBERTIES.md L-t3319-fort-gate-leaves: the leaves'
 * planking, ledges and brace, that they swing inward, how far and how fast. The sources
 * say "large gates" (Kinzie, of the second fort) and "Main Gate" (Whistler's index no. 7,
 * of the first) and nothing about how they hung.
 */
import * as THREE from 'three';
import { footprintToWorld } from './walker.js';

/** The stockades whose gates a visitor works, and what each gate is called. Only these:
 * every other palisade (the covered way, the gardens) keeps its baked leaves, shut. */
export const FORT_GATES = Object.freeze({
  // 1835 — the second fort's two gates, north and south (Kinzie; Andreas).
  fort_dearborn_palisade: { n: 'North gate', s: 'South gate' },
  // 1812 — the first fort's main gate, through both rows of pickets (Whistler no. 7).
  first_fort_dearborn_pickets_outer: { s: 'Main gate, outer row' },
  first_fort_dearborn_pickets_inner: { s: 'Main gate, inner row' },
});

/** How far a leaf swings from shut, and how long it takes. Ours (the header). */
export const OPEN_DEG = 90;
export const SWING_S = 1.4;
/** Within this far of a gate's middle, on foot, the Interact key offers it. */
export const GATE_REACH_M = 5;
/** Half the curtain's thickness as the walker keeps off it: a picket and its ribband. */
export const WALL_HALF_M = 0.2;

// palisade.py's own constants, so the leaves meet the frame the mesh draws.
const JAMB_M = 0.20;          // _gate(): `jamb`
const HEAD_FRAC = 0.86;       // _gate(): head = picket_height_m * 0.86
const LEAF_FOOT_M = 0.02;     // the shut leaf's foot and head, as _gate() beamed them
const LEAF_HEAD_GAP_M = 0.05;

/** Sawn plank weathered dark: the archetype's GATE_RGBA (0.38, 0.31, 0.24) under the
 * weather a gate takes standing out, in linear colour as the GLB carries its own. */
const LEAF_RGB = [0.25, 0.2, 0.155];

/** One of the record's attributes, its value where it is graded ({ value, confidence }). */
function val(sidecar, name, dflt) {
  const attrs = sidecar?.attributes ?? {};
  const graded = attrs[name];
  const v = graded && typeof graded === 'object' && !Array.isArray(graded) ? graded['value'] : graded;
  return v === undefined || v === null ? dflt : v;
}

/** The _confidence value of one attribute's grade (attested 0, inferred 0.5, reconstructed 1). */
function gradeOf(sidecar, name) {
  const attrs = sidecar?.attributes ?? {};
  const grade = attrs[name] && typeof attrs[name] === 'object' ? attrs[name]['confidence'] : null;
  return { attested: 0, inferred: 0.5, reconstructed: 1 }[grade] ?? 0.5;
}

/**
 * T-3320: is this record a fort's parade, whose ground the yards layer lays as
 * trodden earth feathered into the sward (data/enclosures/*parade_ground.json)?
 * The buildings layer then leaves out the archetype's flat 6 cm slab (its `earth`
 * primitive) and keeps the rest (Fergus's sun-dial).
 */
export function paradeLaidAsGround(record) {
  const kind = record?.sidecar?.attributes?.['kind'];
  return (kind && typeof kind === 'object' ? kind['value'] : kind) === 'parade';
}

/** Does the buildings layer leave this record's baked leaves to this layer? */
export function drawsLeaves(record) {
  return !!record && Object.prototype.hasOwnProperty.call(FORT_GATES, record.id)
    && stockadePlan(record.sidecar).gates.length > 0;
}

/**
 * The stockade as palisade.py builds it, in its footprint frame [u, v] (metres; +u east
 * and +v north at rotation 0): `walls` the curtain and bastion runs as [a, b] segments,
 * and one entry per gate with its middle, the axis along the wall, the inward normal,
 * its half-width and the leaves' foot and head.
 */
export function stockadePlan(sidecar) {
  const fp = sidecar?.footprint;
  const poly = Array.isArray(fp) ? fp : fp?.polygon;
  if (sidecar?.archetype !== 'palisade' || !Array.isArray(poly) || poly.length < 3
      || val(sidecar, 'wall_kind', 'picket_stockade') !== 'picket_stockade') {
    return { w: 0, d: 0, walls: [], gates: [] };
  }
  const us = poly.map((p) => p[0]), vs = poly.map((p) => p[1]);
  const w = Math.max(...us) - Math.min(...us), d = Math.max(...vs) - Math.min(...vs);
  const sides = [].concat(val(sidecar, 'gate_sides', [])).map((s) => String(s).toLowerCase());
  const gw = Number(val(sidecar, 'gate_width_m', 3.6));
  const off = Number(val(sidecar, 'gate_offset_m', 0));
  const height = Number(val(sidecar, 'picket_height_m', 3.7));
  const corners = [].concat(val(sidecar, 'bastion_corners', [])).map((c) => String(c).toLowerCase());
  const L = Number(val(sidecar, 'bastion_length_m', 7.0));
  const P = Number(val(sidecar, 'bastion_projection_m', 3.0));

  // palisade.py _stockade(): each side walked so, its corners at its ends in this order.
  const run = { s: [[0, 0], [w, 0]], e: [[w, 0], [w, d]], n: [[w, d], [0, d]], w: [[0, d], [0, 0]] };
  const cornerAt = { s: ['sw', 'se'], e: ['se', 'ne'], n: ['ne', 'nw'], w: ['nw', 'sw'] };
  // _gate_shift(): gate_offset_m is toward +u (n, s) or +v (e, w); n and w are walked back.
  const shift = (side) => (side === 's' || side === 'e' ? off : -off);
  const lerp = (a, z, t) => [a[0] + (z[0] - a[0]) * t, a[1] + (z[1] - a[1]) * t];
  const walls = [];
  for (const side of ['s', 'e', 'n', 'w']) {
    const [a, z] = run[side];
    const len = Math.hypot(z[0] - a[0], z[1] - a[1]);
    const cuts = [];
    if (sides.includes(side)) {
      const mid = len / 2 + shift(side);
      cuts.push([mid - gw / 2, mid + gw / 2]);
    }
    cornerAt[side].forEach((corner, i) => {
      if (corners.includes(corner)) cuts.push(i === 0 ? [0, L] : [len - L, len]);
    });
    for (const [t0, t1] of keepOutside(len, cuts)) walls.push([lerp(a, z, t0 / len), lerp(a, z, t1 / len)]);
  }
  // _bastion(): out from the wall, along, and back.
  for (const corner of corners) {
    const sx = corner === 'ne' || corner === 'se' ? 1 : -1;
    const sy = corner === 'ne' || corner === 'nw' ? 1 : -1;
    const ox = sx > 0 ? w : 0, oy = sy > 0 ? d : 0;
    const path = [[ox - sx * L, oy], [ox - sx * L, oy + sy * P], [ox + sx * P, oy + sy * P],
      [ox + sx * P, oy - sy * L], [ox, oy - sy * L]];
    for (let i = 1; i < path.length; i += 1) walls.push([path[i - 1], path[i]]);
  }
  // _gate(): the gateway's middle, its run and its inward side.
  const head = height * HEAD_FRAC;
  const gates = sides.map((side) => {
    const ns = side === 'n' || side === 's';
    const centre = ns ? [w / 2 + off, side === 'n' ? d : 0] : [side === 'e' ? w : 0, d / 2 + off];
    const along = ns ? [1, 0] : [0, 1];
    const inward = { s: [0, 1], n: [0, -1], w: [1, 0], e: [-1, 0] }[side];
    return { side, centre, along, inward, half: gw / 2, foot: LEAF_FOOT_M, head: head - LEAF_HEAD_GAP_M };
  });
  return { w, d, walls, gates };
}

/** [0, len] with every cut removed (palisade.py _intervals). */
function keepOutside(len, cuts) {
  let keep = [[0, len]];
  for (const [c0, c1] of [...cuts].sort((x, y) => x[0] - y[0])) {
    const out = [];
    for (const [k0, k1] of keep) {
      if (c1 <= k0 || c0 >= k1) { out.push([k0, k1]); continue; }
      if (c0 > k0) out.push([k0, Math.min(c0, k1)]);
      if (c1 < k1) out.push([Math.max(c1, k0), k1]);
    }
    keep = out;
  }
  return keep.filter(([a, z]) => z - a > 1e-6);
}

/** The leaves' directions at swing fraction `t` (0 shut, 1 open), in the plan frame:
 * each runs from its hinge toward the gateway's middle when shut and turns inward. */
export function leafDirections(gate, t) {
  const a = (OPEN_DEG * Math.PI / 180) * Math.max(0, Math.min(1, t));
  const c = Math.cos(a), s = Math.sin(a);
  return [-1, 1].map((side) => {
    const shut = [-side * gate.along[0], -side * gate.along[1]];
    const dir = [c * shut[0] + s * gate.inward[0], c * shut[1] + s * gate.inward[1]];
    const hinge = [gate.centre[0] + side * gate.half * gate.along[0], gate.centre[1] + side * gate.half * gate.along[1]];
    return { hinge, dir };
  });
}

// ---------------------------------------------------------------- leaf mesh

/** Push a six-faced solid onto pos/nrm as flat triangles: `lo` and `hi` are its four
 * bottom and four top corners [x, y, z], in the same order round. Each face is wound
 * away from the solid's middle, so the normals point out whichever way round the
 * corners were given. */
function solid(pos, nrm, lo, hi) {
  const all = [...lo, ...hi];
  const mid = [0, 1, 2].map((k) => all.reduce((acc, p) => acc + p[k], 0) / all.length);
  const quad = (a, b, c, d) => {
    const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], ad = [d[0] - a[0], d[1] - a[1], d[2] - a[2]];
    let n = [ab[1] * ad[2] - ab[2] * ad[1], ab[2] * ad[0] - ab[0] * ad[2], ab[0] * ad[1] - ab[1] * ad[0]];
    const c0 = [0, 1, 2].map((k) => (a[k] + b[k] + c[k] + d[k]) / 4 - mid[k]);
    let order = [a, b, c, a, c, d];
    if (n[0] * c0[0] + n[1] * c0[1] + n[2] * c0[2] < 0) { n = n.map((x) => -x); order = [a, d, c, a, c, b]; }
    const l = Math.hypot(...n) || 1;
    for (const p of order) { pos.push(...p); nrm.push(n[0] / l, n[1] / l, n[2] / l); }
  };
  for (let i = 0; i < 4; i += 1) {
    const j = (i + 1) % 4;
    quad(lo[i], lo[j], hi[j], hi[i]);
  }
  quad(hi[0], hi[1], hi[2], hi[3]);
  quad(lo[0], lo[3], lo[2], lo[1]);
}

/** An axis-aligned box in the leaf's frame. */
function box(pos, nrm, x0, x1, y0, y1, z0, z1) {
  solid(pos, nrm,
    [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]],
    [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]]);
}

/**
 * One leaf in its hinge's frame: it runs along +x from the hinge (x = 0) to `len`, its
 * boards from `foot` to `head` in y, and its ledges and brace on the `back` side in z
 * (+1 or -1, the side that faces the fort). Boards butted with a hairline between them,
 * two ledges and a brace rising from the hinge's foot to the free end — the ledged and
 * braced door every carpenter hangs where a leaf must not sag. About 100 triangles.
 */
export function leafGeometry({ len, foot, head, back = 1 }) {
  const pos = [], nrm = [];
  const T = 0.07;                                   // the boards' thickness
  const boards = Math.max(3, Math.round(len / 0.28));
  const pitch = len / boards;
  for (let i = 0; i < boards; i += 1) {
    box(pos, nrm, i * pitch + 0.004, (i + 1) * pitch - 0.004, foot, head, -T / 2, T / 2);
  }
  const zb = [back * T / 2, back * (T / 2 + 0.045)].sort((a, b) => a - b);
  const ledgeH = 0.16;
  const yLow = foot + 0.32, yHigh = head - 0.42 - ledgeH;
  box(pos, nrm, 0.06, len - 0.06, yLow, yLow + ledgeH, zb[0], zb[1]);
  box(pos, nrm, 0.06, len - 0.06, yHigh, yHigh + ledgeH, zb[0], zb[1]);
  // The brace: from the hinge end's lower ledge up to the free end's upper one, a board
  // 0.14 m wide laid flat on the back between them.
  const a = [0.12, yLow + ledgeH], b = [len - 0.12, yHigh];
  const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
  const px = (-dy / l) * 0.07, py = (dx / l) * 0.07;
  const q = [[a[0] - px, a[1] - py], [b[0] - px, b[1] - py], [b[0] + px, b[1] + py], [a[0] + px, a[1] + py]];
  solid(pos, nrm, q.map(([x, y]) => [x, y, zb[0]]), q.map(([x, y]) => [x, y, zb[1]]));

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  geo.computeBoundingSphere();
  return geo;
}

// ---------------------------------------------------------------- the layer

/**
 * @param {object} o
 * @param {Map} o.registry              scene-loader's records
 * @param {object} o.buildings          the buildings layer (matrixOf)
 * @param {Array} o.footprints          walker.js footprints — the stockades' entries get `walls`
 * @param {object} [o.confidence]       createConfidenceView
 * @param {string[]} [o.problems]
 */
export function createFortGates({ registry, buildings, footprints = [], confidence = null, problems = [] }) {
  const group = new THREE.Group();
  group.name = 'fort-gates';
  const material = new THREE.MeshStandardMaterial({
    color: new THREE.Color().setRGB(...LEAF_RGB), roughness: 0.9, metalness: 0,
  });
  if (confidence?.patch) confidence.patch(material);
  const gates = [];

  for (const id of Object.keys(FORT_GATES)) {
    const record = registry.get(id);
    if (!record) continue;                            // not in this year's scene
    const plan = stockadePlan(record.sidecar);
    const m = buildings?.matrixOf?.(id);
    const obstacle = footprints.find((f) => f.id === id);
    if (!m || !obstacle || !plan.gates.length) {
      problems.push(`${id}: a fort gate to hang, but ${!m ? 'its stockade was not drawn' : !obstacle ? 'it has no footprint' : 'its record names no gate'} — the fort stays shut`);
      continue;
    }
    const toWorld = footprintToWorld(record.sidecar.placement);
    const conf = gradeOf(record.sidecar, 'gate_sides');
    // The walls: the curtain and bastions always, each gateway's span while it is shut.
    const walls = plan.walls.map(([a, b]) => ({ a: toWorld(a), b: toWorld(b), half: WALL_HALF_M }));
    obstacle.walls = walls;
    footprints.wallsVersion = (footprints.wallsVersion ?? 0) + 1;   // walker.js re-reads

    const holder = new THREE.Group();
    holder.name = `fort-gates:${id}`;
    holder.matrixAutoUpdate = false;
    holder.matrix.copy(m);
    group.add(holder);

    for (const gate of plan.gates) {
      const name = FORT_GATES[id][gate.side];
      if (!name) continue;
      // The leaves, each on a pivot at its hinge. Plan (x, y) is glTF (x, -z), so a plan
      // direction at angle phi from +x is a turn of phi about +y.
      const leaves = leafDirections(gate, 0).map(({ hinge, dir }) => {
        const pivot = new THREE.Object3D();
        pivot.position.set(hinge[0], 0, -hinge[1]);
        // The fort's side of the leaf: +z of the pivot is the plan direction turned
        // clockwise; the ledges go on whichever of +z and -z faces the inward normal.
        const cw = [dir[1], -dir[0]];
        const back = cw[0] * gate.inward[0] + cw[1] * gate.inward[1] >= 0 ? 1 : -1;
        const geo = leafGeometry({ len: gate.half - 0.004, foot: gate.foot, head: gate.head, back });
        const n = geo.getAttribute('position').count;
        geo.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(n).fill(conf), 1));
        const mesh = new THREE.Mesh(geo, material);
        mesh.name = `fort-gate-leaf:${id}:${gate.side}`;
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData.structure_id = id;
        pivot.add(mesh);
        holder.add(pivot);
        return pivot;
      });
      holder.updateMatrixWorld(true);

      const thing = {
        id: `${id}:${gate.side}`,
        kind: 'gate',
        structureId: id,
        name,
        states: ['closed', 'open'],
        state: 'closed',
        at: toWorld(gate.centre),
        reach: GATE_REACH_M,
        swing: 0,
        actions: {
          closed: [{ id: 'open', label: 'Open gate', to: 'open',
            steps: [{ label: 'Opening', seconds: SWING_S, run: (t) => setSwing(t) }] }],
          open: [{ id: 'close', label: 'Close gate', to: 'closed',
            steps: [{ label: 'Closing', seconds: SWING_S, run: (t) => setSwing(1 - t) }] }],
        },
      };
      function setSwing(t) {
        thing.swing = t;
        // Eased so the leaf starts and stops like a weight on a hinge, not a wiper.
        const eased = t * t * (3 - 2 * t);
        leafDirections(gate, eased).forEach(({ dir }, i) => {
          leaves[i].rotation.y = Math.atan2(dir[1], dir[0]);
        });
        holder.updateMatrixWorld(true);
      }
      setSwing(0);
      // The gateway's span stands across the way unless the gate is open and still.
      walls.push({ a: toWorld([gate.centre[0] - gate.half * gate.along[0], gate.centre[1] - gate.half * gate.along[1]]),
        b: toWorld([gate.centre[0] + gate.half * gate.along[0], gate.centre[1] + gate.half * gate.along[1]]),
        half: 0.06, gate: thing.id, blocks: () => !(thing.state === 'open' && !thing.running) });
      // And open, each leaf is a board standing out from its jamb.
      for (const { hinge, dir } of leafDirections(gate, 1)) {
        const len = gate.half;
        walls.push({ a: toWorld(hinge), b: toWorld([hinge[0] + dir[0] * len, hinge[1] + dir[1] * len]),
          half: 0.06, gate: thing.id, blocks: () => thing.state === 'open' && !thing.running });
      }
      gates.push(thing);
    }
  }

  return {
    group,
    gates,
    dispose() {
      group.traverse((o) => { if (o.isMesh) o.geometry.dispose(); });
      material.dispose();
    },
  };
}
