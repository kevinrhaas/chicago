/**
 * flags.js — the colours on Fort Dearborn's flagstaff, in both forts (T-2124).
 *
 * The owner, 2026-10-05, at the fort in 1835: *"can we have a US flag or
 * whatever the period correct flag staff for the fort would be for the period
 * flying on that flag pole? both 1835 and 1812 ... probably gentle flutter
 * appropriate with the wind speed ... i don't want to lag things up for a
 * flag"*. Both staffs stood bare: the second fort's record argued that a flag
 * was a claim about one forenoon its source declines to make.
 *
 * WHAT IS ON THE RECORD. The staff's record carries `flag` (what pattern) and
 * `flag_flying` (whether it is up on the scene date), each with its own grade
 * and reasoning, and this layer draws exactly what those two say:
 *
 *  - 1835: Andreas has the staff "flaunted, in pleasant weather and on
 *    holidays — a weather-beaten flag". The FLAG is attested, and so is its
 *    wear. The pattern is the law's: under the Flag Act of 4 April 1818 a star
 *    is added on the 4th of July after a state's admission, so the flag of
 *    1 July 1835 is the 24-star flag of 4 July 1822 (Missouri), and the 25th
 *    (Arkansas) waits for 4 July 1836. INFERRED.
 *  - 1812: Whistler's 1808 draught draws the staff, 75 ft; Quaife calls it "a
 *    lofty flagstaff". On 1 August 1812 the law is the Flag Act of 1794: fifteen
 *    stars and FIFTEEN stripes, in force from 1 May 1795 to 4 July 1818. INFERRED.
 *  - That either flag is UP at the scene's hour, how big it is, how its stars
 *    are laid out and which way the wind takes it are RECONSTRUCTED — L390 —
 *    and the confidence view dithers the cloth accordingly.
 *
 * WHAT IT COSTS. One 512 px canvas texture a flag, a 32 x 14 cloth (896
 * triangles), and a three-sided hemp halyard of three short tubes (204
 * triangles, one draw call), and no CPU work a frame beyond adding `dt` to one
 * uniform: the flutter is a vertex-shader travelling wave with its normal
 * taken analytically, so nothing is rebuilt, uploaded or allocated while it
 * moves. The animation clock's hold (`setAnimationHold`) stills it, so every
 * held capture is reproducible. It casts no shadow: a cloth's shadow is a
 * second pass for a smudge on the parade.
 *
 * It degrades rather than throws: a staff the buildings did not draw gets no
 * flag, with the reason on the `problems` list.
 */

import * as THREE from 'three';
import { LEVELS } from './confidence.js';

/**
 * THE PATTERNS — counted from the acts, laid out by us. Rows of stars are the
 * commonest layouts the two counts were flown in (24: four rows of six; 15:
 * five staggered rows of three, the Fort McHenry arrangement); the law fixed
 * the count, not the layout, until 1912, so each layout is reconstructed (L390).
 * `union` is the canton's depth in stripes and its share of the fly.
 */
export const PATTERNS = {
  us_flag_24_star: { stripes: 13, union: { stripes: 7, fly: 0.40 }, rows: [6, 6, 6, 6], stagger: false },
  us_flag_15_star_15_stripe: { stripes: 15, union: { stripes: 8, fly: 0.42 }, rows: [3, 3, 3, 3, 3], stagger: true },
};

/**
 * HOW BIG, AND WHERE THE WIND IS. Reconstructed (L390), every one.
 *  - THE SIZE IS A POST'S EVERYDAY FLAG, NOT A FORTRESS'S (T-2333, the owner
 *    2026-10-10: "they seem a bit large"). The sizes that survive are the big
 *    ones: Fort McHenry's 1813 storm flag 17 x 25 ft and its garrison flag
 *    30 x 42; the garrison flag the British took at Fort Niagara in 1813 at
 *    least 22 x 28. The Army's regulations, when they first fix sizes (the
 *    revised regulations of 1861, as transcribed), give the garrison flag
 *    20 x 36 ft for great days, the storm flag 10 x 20 for every other day,
 *    and the recruiting flag 4 ft 4 in x 9 ft 9 in. Fort Dearborn was a
 *    one-company post at the end of the supply line, its flag "weather-beaten"
 *    in Andreas, flown "in pleasant weather": the everyday flag, on the small
 *    side of the regulation storm flag and above the recruiting flag. So
 *    6 ft 6 in x 12 ft at both forts, hoist to fly 1 : 1.85, between the 1861
 *    garrison flag's 1 : 1.8 and the later storm flag's 1 : 1.92. The staff's
 *    height does not set it: the first fort's taller staff flew the same issue.
 *    (Was 0.30 of the staff: 15 ft and 22 ft, a fortress's flag on a post.)
 *  - The wind is a July south-westerly — Chicago's prevailing summer wind — at
 *    a breeze that holds the flag out and ripples it rather than cracking it.
 */
const FLY_M = 12 * 0.3048;
const HOIST_TO_FLY = 1 / 1.85;
const WIND_FROM_DEG = 225;
/** The truck and the gap above the head of the flag, metres. */
const TRUCK_GAP_M = 0.18;
/** Cloth resolution: segments along the fly and the hoist. */
const SEG_U = 32;
const SEG_V = 14;
/**
 * THE HALYARD. A hemp line of about 3/4 in, rove through a sheave in the truck:
 * one part made fast to the head and foot of the flag's heading, the other
 * hanging free beside the staff, both belayed to a cleat at shoulder height.
 * Three-sided tubes — at any distance the line is a pixel wide, and a round
 * section would buy nothing but triangles. Reconstructed (L390).
 */
const HALYARD = { radius: 0.011, sides: 3, cleatM: 1.3, color: 0x6f6250 };
/**
 * The wave. Wool bunting is heavy and soft: in a breeze it hangs out in
 * several shallow folds that roll down the fly, sags at the fly end, and never
 * stands out flat or cracks like silk. Crests a fly, crest speed (fly lengths
 * a second), depth, the sag, and a finer ripple riding on the folds.
 */
const WAVE = { crests: 2.3, speed: 0.42, amp: 0.075, droop: 0.16, ripple: 0.22 };

/**
 * THE CLOTH'S COLOURS, worn. Andreas's "weather-beaten" is a reading of the
 * 1835 flag and is applied there in full: madder red gone brick, indigo gone
 * slate, the white yellowed, and the fly end — which snaps and frays first —
 * paler than the hoist. The 1812 flag takes half that wear (reconstructed).
 */
const CLOTH = {
  red: [168, 44, 44],
  white: [236, 230, 212],
  blue: [34, 46, 92],
};
const WEAR = { us_flag_24_star: 1.0, us_flag_15_star_15_stripe: 0.5 };

function valueOf(a) {
  return a && typeof a === 'object' && !Array.isArray(a) ? a.value : a;
}

function gradeOf(a) {
  const c = a && typeof a === 'object' ? a.confidence : null;
  return LEVELS[c] ?? LEVELS.reconstructed;
}

/** The staff records that fly a flag on this scene's date, with what they fly. */
export function flagsFlown(registry) {
  const out = [];
  for (const record of registry.values()) {
    const at = record.sidecar?.attributes ?? {};
    const pattern = valueOf(at.flag);
    if (!pattern || valueOf(at.flag_flying) !== true) continue;
    out.push({
      id: record.id,
      pattern,
      // The cloth is drawn at the worse of its two grades: a flag whose pattern
      // is inferred but whose being up is reconstructed is a reconstruction.
      confidence: Math.max(gradeOf(at.flag), gradeOf(at.flag_flying)),
    });
  }
  return out;
}

/** A five-pointed star, filled, centred at (x, y) with outer radius r. */
function star(ctx, x, y, r) {
  ctx.beginPath();
  for (let i = 0; i < 10; i += 1) {
    const a = -Math.PI / 2 + (i * Math.PI) / 5;
    const rr = i % 2 === 0 ? r : r * 0.382;
    ctx.lineTo(x + rr * Math.cos(a), y + rr * Math.sin(a));
  }
  ctx.closePath();
  ctx.fill();
}

/** Seeded noise, so the same flag frays the same way on every load. */
function rng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s ^ (s >>> 15), 0x2c1b3c6d) + 0x9e3779b9) >>> 0;
    return s / 0x100000000;
  };
}

/** Draw one flag into a canvas: stripes, canton, stars, then the wear. */
export function paintFlag(patternId, { width = 512, seed = 1835 } = {}) {
  const pat = PATTERNS[patternId];
  if (!pat) throw new Error(`no flag pattern '${patternId}'`);
  const wear = WEAR[patternId] ?? 0.5;
  const w = width;
  const h = Math.round(width * HOIST_TO_FLY);
  const cv = document.createElement('canvas');
  cv.width = w;
  cv.height = h;
  const ctx = cv.getContext('2d');
  const rgb = (c) => `rgb(${c[0]},${c[1]},${c[2]})`;
  const stripeH = h / pat.stripes;
  for (let i = 0; i < pat.stripes; i += 1) {
    ctx.fillStyle = rgb(i % 2 === 0 ? CLOTH.red : CLOTH.white);
    ctx.fillRect(0, Math.floor(i * stripeH), w, Math.ceil(stripeH) + 1);
  }
  const uw = w * pat.union.fly;
  const uh = stripeH * pat.union.stripes;
  ctx.fillStyle = rgb(CLOTH.blue);
  ctx.fillRect(0, 0, uw, uh);
  ctx.fillStyle = rgb(CLOTH.white);
  const rows = pat.rows.length;
  const r = Math.min(uh / rows, uw / Math.max(...pat.rows)) * 0.36;
  // The stars are cut from cotton and sewn on by hand, each a little off its
  // neighbour in place, size and turn — a flag of the period is never a print.
  const sew = rng(seed ^ 0x5eed);
  pat.rows.forEach((n, row) => {
    const y = uh * (row + 0.5) / rows;
    const shift = pat.stagger && row % 2 === 1 ? 0.5 : 0;
    const cols = pat.stagger ? n + 0.5 : n;
    for (let k = 0; k < n; k += 1) {
      const x = uw * (k + 0.5 + (pat.stagger ? shift : 0)) / cols;
      const j = () => (sew() - 0.5) * 2;
      ctx.save();
      ctx.translate(x + j() * r * 0.12, y + j() * r * 0.12);
      ctx.rotate(j() * 0.12);
      star(ctx, 0, 0, r * (1 + j() * 0.06));
      ctx.restore();
    }
  });
  // THE SEAMS. Bunting came in narrow widths, so every stripe is its own strip
  // and the canton its own panel, lapped and stitched: a faint dark line where
  // each strip overlaps the next.
  ctx.strokeStyle = 'rgba(40,24,20,0.28)';
  ctx.lineWidth = Math.max(1, h / 300);
  for (let i = 1; i < pat.stripes; i += 1) {
    const y = Math.round(i * stripeH) + 0.5;
    ctx.beginPath();
    ctx.moveTo(i < pat.union.stripes ? uw : 0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }
  ctx.beginPath();
  ctx.moveTo(uw + 0.5, 0);
  ctx.lineTo(uw + 0.5, uh);
  ctx.lineTo(0, uh + 0.5);
  ctx.stroke();
  // The heading: a strip of heavier canvas down the hoist, where the halyard
  // runs through.
  ctx.fillStyle = 'rgba(214,204,178,0.92)';
  ctx.fillRect(0, 0, Math.max(3, w * 0.018), h);
  // Wool takes dye unevenly and its edges are not knife-cut: soften every
  // boundary by a thread or two before the weave goes on.
  const soft = document.createElement('canvas');
  soft.width = w;
  soft.height = h;
  const sctx = soft.getContext('2d');
  if ('filter' in sctx) sctx.filter = `blur(${(w / 512 * 0.9).toFixed(2)}px)`;
  sctx.drawImage(cv, 0, 0);
  ctx.clearRect(0, 0, w, h);
  ctx.drawImage(soft, 0, 0);
  // THE WEAR. Bleaching toward the fly, a grime of uneven fading over all of
  // it, and a frayed fly edge: three passes of the same seeded noise.
  const img = ctx.getImageData(0, 0, w, h);
  const d = img.data;
  const rand = rng(seed);
  const blot = new Float32Array(16 * 10).map(() => rand());
  const warp = new Float32Array(97).map(() => rand() - 0.5);
  const weft = new Float32Array(89).map(() => rand() - 0.5);
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const u = x / w;
      const gx = Math.min(15, Math.floor(u * 16));
      const gy = Math.min(9, Math.floor((y / h) * 10));
      const b = blot[gy * 16 + gx];
      const bleach = wear * (0.10 + 0.22 * u * u + 0.06 * b);
      const grime = 1 - wear * (0.05 + 0.07 * (1 - b)) * (0.6 + 0.4 * rand());
      // The weave: a plain open weave of worsted, so every row and column of
      // threads catches the light a little differently, with a slub here and
      // there. Multiplied in, so it shows on every colour without moving it.
      const weave = 1 + 0.055 * (warp[x % warp.length] + weft[y % weft.length])
        + 0.035 * (rand() - 0.5) + ((x + y) % 2 === 0 ? 0.018 : -0.018);
      const i = (y * w + x) * 4;
      for (let c = 0; c < 3; c += 1) {
        const v = d[i + c] * grime * weave;
        d[i + c] = Math.max(0, Math.min(255, v + (226 - v) * bleach));
      }
    }
  }
  // The fly edge frays: a ragged band of transparency, deepest mid-hoist.
  // Torn in tongues a few threads wide rather than speckled, so it reads at a
  // distance as a ragged edge and not as noise.
  const fray = w * 0.02 * (0.4 + wear);
  let depth = 0;
  for (let y = 0; y < h; y += 1) {
    if (y % 3 === 0) depth = fray * (0.2 + 0.8 * rand()) * (0.6 + 0.4 * Math.sin((y / h) * Math.PI));
    for (let x = Math.floor(w - depth); x < w; x += 1) d[(y * w + x) * 4 + 3] = 0;
  }
  ctx.putImageData(img, 0, 0);
  return cv;
}

/**
 * The vertex edit: a travelling wave down the fly, growing from nothing at
 * the hoist (it is lashed to the staff) to full at the fly end, a slower
 * second wave across it so the cloth does not move as one sheet, and a little
 * droop. Position and normal are computed from the same function, so the light
 * follows the folds. `uv.x` is 0 at the hoist.
 */
function flutter(material, uniforms) {
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    const head = `uniform float uFlagTime;
uniform float uFlagFly;
uniform float uFlagHoist;
vec3 chiFlag( vec2 st ) {
  float u = st.x, v = st.y;
  float grow = pow( u, 1.25 );
  float k = 6.2831853 * ${WAVE.crests.toFixed(3)};
  float ph = k * u - 6.2831853 * ${WAVE.speed.toFixed(3)} * uFlagTime;
  float z = ${WAVE.amp.toFixed(3)} * uFlagFly * grow
          * ( sin( ph ) + 0.35 * sin( 1.7 * ph + 2.3 * v + 0.6 * uFlagTime )
            + ${WAVE.ripple.toFixed(3)} * sin( 3.1 * ph - 4.0 * v + 1.3 * uFlagTime ) );
  // The fly end sags under its own weight, the foot more than the head, and
  // the sag rocks a little as the folds pass.
  float droop = ${WAVE.droop.toFixed(3)} * uFlagHoist * u * u
              * ( 0.75 + 0.25 * ( 1.0 - v ) ) * ( 1.0 + 0.15 * sin( ph ) );
  float pull = 0.04 * uFlagFly * grow * ( 1.0 - cos( ph ) );
  return vec3( -pull, -droop, z );
}
`;
    shader.vertexShader = head + shader.vertexShader
      .replace('#include <beginnormal_vertex>', `
  vec2 chiSt = uv;
  float chiE = 0.01;
  vec3 chiP0 = chiFlag( chiSt );
  vec3 chiDu = vec3( uFlagFly * chiE, 0.0, 0.0 ) + chiFlag( chiSt + vec2( chiE, 0.0 ) ) - chiP0;
  vec3 chiDv = vec3( 0.0, uFlagHoist * chiE, 0.0 ) + chiFlag( chiSt + vec2( 0.0, chiE ) ) - chiP0;
  vec3 objectNormal = normalize( cross( chiDu, chiDv ) );
  #ifdef USE_TANGENT
    vec3 objectTangent = vec3( tangent.xyz );
  #endif`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
  transformed += chiP0;`);
  };
  material.needsUpdate = true;
}

/**
 * The halyard, in the holder's frame: the staff's axis is x = z = 0, the
 * flag's head is at (radius, 0, 0) and the wind blows toward +x. One part runs
 * from the truck to the head of the heading and on from its foot down to the
 * cleat; the other hangs free from the truck to the cleat. Each long run bows
 * a little downwind, as a line does that is belayed but not bar-taut.
 */
function halyard({ hoist, radius, staffH, material }) {
  const truck = new THREE.Vector3(radius * 0.8, TRUCK_GAP_M * 0.55, 0);
  const cleat = new THREE.Vector3(radius * 1.15, -(staffH - TRUCK_GAP_M) + HALYARD.cleatM, 0);
  const run = (a, b, bow, zOff, segs) => {
    const pts = [];
    for (let i = 0; i <= segs; i += 1) {
      const t = i / segs;
      const p = a.clone().lerp(b, t);
      p.x += bow * 4 * t * (1 - t);
      p.z += zOff * Math.sin(Math.PI * Math.min(1, t * 6)) ;
      pts.push(p);
    }
    return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), segs, HALYARD.radius, HALYARD.sides, false);
  };
  const head = new THREE.Vector3(radius, 0, 0);
  const foot = new THREE.Vector3(radius, -hoist, 0);
  const lower = foot.distanceTo(cleat);
  const parts = [
    run(truck, head, 0.01, 0, 2),
    run(foot, cleat, Math.min(0.35, lower * 0.012), 0, 14),
    run(truck, cleat, Math.min(0.30, staffH * 0.008), HALYARD.radius * 3, 18),
  ];
  // One mesh, one draw call: the three tubes' triangles concatenated.
  const pos = [];
  const nor = [];
  for (const geo of parts) {
    const g = geo.toNonIndexed();
    pos.push(...g.getAttribute('position').array);
    nor.push(...g.getAttribute('normal').array);
    g.dispose();
    geo.dispose();
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  geo.setAttribute('_confidence',
    new THREE.BufferAttribute(new Float32Array(pos.length / 3).fill(LEVELS.reconstructed), 1));
  const m = new THREE.Mesh(geo, material);
  m.name = 'halyard';
  m.castShadow = false;
  return m;
}

/**
 * Hang a flag on every staff the scene's records fly one from.
 *
 * @param {object} o
 * @param {Map} o.registry          scene-loader's records
 * @param {object} o.buildings      createBuildings — for where each staff stands
 * @param {object} [o.confidence]   createConfidenceView — the cloth dithers by grade
 * @param {string[]} [o.problems]
 */
export function createFlags({ registry, buildings, confidence = null, problems = [] }) {
  const group = new THREE.Group();
  group.name = 'flags';
  const uniforms = { uFlagTime: { value: 0 } };
  const drawn = [];
  const bounds = buildings?.instanceBounds?.() ?? {};
  const ropeMat = new THREE.MeshStandardMaterial({ color: HALYARD.color, roughness: 1, metalness: 0 });
  if (confidence?.patch) confidence.patch(ropeMat);

  for (const flag of flagsFlown(registry)) {
    const m = buildings?.matrixOf?.(flag.id);
    const box = bounds[flag.id];
    if (!m || !box) {
      problems.push(`${flag.id}: flies a flag, but its staff was not drawn — no flag hung`);
      continue;
    }
    if (!PATTERNS[flag.pattern]) {
      problems.push(`${flag.id}: flag pattern '${flag.pattern}' is not one this layer knows`);
      continue;
    }
    // The staff's axis and head, from the mesh the buildings actually drew.
    const axis = new THREE.Vector3((box.min[0] + box.max[0]) / 2, box.max[1],
      (box.min[2] + box.max[2]) / 2).applyMatrix4(m);
    const foot = new THREE.Vector3((box.min[0] + box.max[0]) / 2, box.min[1],
      (box.min[2] + box.max[2]) / 2).applyMatrix4(m);
    const staffH = axis.y - foot.y;
    const radius = Math.max(0.04, Math.min(box.max[0] - box.min[0], box.max[2] - box.min[2]) / 2 * 0.6);
    const fly = FLY_M;
    const hoist = fly * HOIST_TO_FLY;

    const tex = new THREE.CanvasTexture(paintFlag(flag.pattern, { seed: flag.id.length * 7919 }));
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 4;
    // Wool is matte with a soft sheen at grazing light, never a gloss: the
    // physical material's sheen lobe is that, and it costs nothing a frame.
    const mat = new THREE.MeshPhysicalMaterial({
      map: tex, side: THREE.DoubleSide, roughness: 1, metalness: 0,
      sheen: 0.5, sheenRoughness: 0.85, sheenColor: new THREE.Color(0.9, 0.86, 0.78),
      alphaTest: 0.5,
    });
    const flagUniforms = { ...uniforms, uFlagFly: { value: fly }, uFlagHoist: { value: hoist } };
    flutter(mat, flagUniforms);
    if (confidence?.patch) confidence.patch(mat);

    // The cloth in its own frame: hoist edge on x = 0, fly along +x, the
    // head of the flag at y = 0 and the foot at -hoist.
    const geo = new THREE.PlaneGeometry(fly, hoist, SEG_U, SEG_V);
    geo.translate(fly / 2, -hoist / 2, 0);
    const n = geo.getAttribute('position').count;
    geo.setAttribute('_confidence',
      new THREE.BufferAttribute(new Float32Array(n).fill(flag.confidence), 1));

    const mesh = new THREE.Mesh(geo, mat);
    mesh.name = `flag:${flag.id}`;
    mesh.castShadow = false;
    mesh.receiveShadow = true;
    mesh.frustumCulled = true;
    geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(fly / 2, -hoist / 2, 0), fly);
    // Downwind: the fly streams toward the bearing the wind blows TO. A
    // compass bearing b is world (sin b, 0, -cos b); the cloth's +x is turned
    // onto it about the staff.
    const to = (WIND_FROM_DEG + 180) * Math.PI / 180;
    const holder = new THREE.Group();
    holder.position.set(axis.x, axis.y - TRUCK_GAP_M, axis.z);
    holder.rotation.y = Math.atan2(-Math.cos(to), Math.sin(to)) * -1;
    mesh.position.x = radius;
    holder.add(mesh);
    holder.add(halyard({ fly, hoist, radius, staffH, material: ropeMat }));
    group.add(holder);
    drawn.push({ id: flag.id, pattern: flag.pattern, fly_m: Number(fly.toFixed(2)),
      hoist_m: Number(hoist.toFixed(2)), confidence: flag.confidence });
  }

  return {
    group,
    drawn,
    /** Advance the cloth. `dt` is 0 while the animation clock is held. */
    update(dt) {
      if (drawn.length) uniforms.uFlagTime.value += dt || 0;
    },
    dispose() {
      group.traverse((o) => {
        if (o.isMesh) { o.geometry.dispose(); o.material.map?.dispose(); o.material.dispose(); }
      });
    },
  };
}
