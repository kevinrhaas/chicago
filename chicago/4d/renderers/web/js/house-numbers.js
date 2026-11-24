/**
 * house-numbers.js — each house's street number, over its front door (T-3737).
 *
 * The owner, 2026-11-23: "i noticed there were no street addresses on most of the buildings
 * could you do a sweep of what the street address numbers/plaque would have been on most
 * buildings and then include them accordingly?"
 *
 * WHAT IS DRAWN. data/house_numbers/<scene>.json (tools/place_prairie_1904_house_numbers.py)
 * lists each number, the structure whose front door carries it, the spot on that door (in the
 * structure's own frame), the way the door faces, the figures' height, and the sign-writer's
 * hand it is lettered in (gold leaf or white enamel; Roman, block or sloped; outlined or shaded). 1815's photograph
 * shows light serif figures centred on the door's transom glass, and the Inter Ocean of 1887
 * calls 1612 "the house with the number 1612 over the portals", so every door is given gilt
 * figures on its transom (or its leaf's top rail, without one), each house in its own hand. The file says which are read
 * and which are reconstructed; the liberty is L-prairie-house-numbers-3737.
 *
 * WHAT IT COSTS. Nothing is downloaded but the list (a few KB): each hand's ten figures are
 * drawn once into a 512 x 512 canvas, the atlas (a row a hand), and every number in the district is one quad a figure in
 * ONE mesh with ONE material, so the whole layer is a single draw of a few hundred triangles.
 * The vertex stage folds away every figure farther than REACH_M from the eye, so past a short
 * walk the draw rasterises nothing; the atlas's mipmaps fade a figure out before then. No
 * shadow is cast. Built the same on a phone and a desktop, since it is this small.
 *
 * WHERE. A spot in a structure's frame goes to the world through buildings.js `matrixOf`, the
 * very placement its model is drawn with, so the figures sit on the door the model draws.
 */
import * as THREE from 'three';

/** Figures farther than this from the eye are not drawn (metres). Readable to about 30 m. */
export const REACH_M = 70;
/** The atlas: one strip of the ten figures for each hand, a padded row apiece. */
const ATLAS_W = 512;
const ATLAS_H = 512;
const CELL_W = 48;
const CELL_H = 64;          // the figure's own box in a row
const ROW_H = 80;           // a row: the box and a margin, so mipmaps of one hand do not bleed into the next
const DIGITS = '0123456789';
/** How much of the figures' colour is their own light. Gold leaf and enamel on glass are dull
 *  from the street (the owner, 2026-11-23: "they seem very bright"): a trace, so a figure in a
 *  porch's shade still reads (0.05 lost them in the shade; the first cut's 0.3 glowed). */
export const EMISSIVE = 0.2;
/** A figure's advance is its drawn width, plus this share of the height between figures. */
const TRACK = 0.08;
/** The first cut's one style, for a list that names no hands. */
const PLAIN = { plain: { face: 'serif', weight: 'bold', style: 'normal', fill: '#cfae62', edge: '#2e2312', edge_px: 3 } };

const FACES = {
  serif: "Georgia, 'Times New Roman', Times, serif",
  sans: "'Helvetica Neue', Helvetica, Arial, sans-serif",
};

/**
 * Draw every hand's ten figures once, a row a hand. Returns { canvas, hands: { id: { row, widths } } }
 * (widths: each figure's drawn width as a share of its height).
 */
export function drawAtlas(hands = PLAIN, doc = globalThis.document) {
  const canvas = doc?.createElement?.('canvas');
  if (!canvas) return null;
  canvas.width = ATLAS_W;
  canvas.height = ATLAS_H;
  const g = canvas.getContext('2d');
  if (!g) return null;
  g.clearRect(0, 0, ATLAS_W, ATLAS_H);
  g.textAlign = 'center';
  g.textBaseline = 'alphabetic';
  g.lineJoin = 'round';
  const out = {};
  Object.keys(hands).slice(0, Math.floor(ATLAS_H / ROW_H)).forEach((id, row) => {
    const h = hands[id] ?? {};
    g.font = `${h.style === 'italic' ? 'italic ' : ''}${h.weight || 'bold'} 54px ${FACES[h.face] ?? h.face ?? FACES.serif}`;
    const top = row * ROW_H + (ROW_H - CELL_H) / 2;
    const widths = [];
    for (let i = 0; i < DIGITS.length; i++) {
      const x = i * CELL_W + CELL_W / 2;
      const w = Math.min(CELL_W - 4, (g.measureText(DIGITS[i]).width || CELL_W * 0.6) + (h.edge_px ?? 3) / 2);
      widths.push(w / CELL_H);   // as a share of the figure's height (the box's)
      g.lineWidth = h.edge_px ?? 3;
      g.strokeStyle = h.edge || '#2e2312';
      g.strokeText(DIGITS[i], x, top + 54);
      g.fillStyle = h.fill || '#a88c55';
      g.fillText(DIGITS[i], x, top + 54);
    }
    out[id] = { row, widths };
  });
  return { canvas, hands: out };
}

/**
 * The quads for one number, in the structure's frame: centred on `at`, facing `normal`, each
 * figure `height` tall, in the hand drawn at atlas row `row`. Returns { positions, uvs } (flat
 * arrays, two triangles a figure).
 */
export function numberQuads(number, at, normal, height, widths, row = 0) {
  const n = new THREE.Vector3(...normal).normalize();
  const up = new THREE.Vector3(0, 1, 0);
  // Facing the door from the street (looking along -n), the reader's right.
  const right = new THREE.Vector3().crossVectors(n.clone().negate(), up).normalize();
  const figs = String(number).split('').filter((c) => DIGITS.includes(c));
  const adv = figs.map((c) => (widths[DIGITS.indexOf(c)] + TRACK) * height);
  const total = adv.reduce((a, b) => a + b, 0) - TRACK * height;
  const positions = [], uvs = [];
  let s = -total / 2;
  const c = new THREE.Vector3(...at);
  // the canvas's top row is the texture's top (flipY): v counts up from the atlas's foot
  const top = row * ROW_H + (ROW_H - CELL_H) / 2;
  const v0 = 1 - (top + CELL_H) / ATLAS_H;
  const v1 = 1 - top / ATLAS_H;
  for (let i = 0; i < figs.length; i++) {
    const k = DIGITS.indexOf(figs[i]);
    const w = widths[k] * height;
    // the cell is CELL_W wide and the glyph is centred in it: take the glyph's own width
    const u0 = (k * CELL_W + CELL_W / 2 - (w / height) * CELL_H / 2) / ATLAS_W;
    const u1 = (k * CELL_W + CELL_W / 2 + (w / height) * CELL_H / 2) / ATLAS_W;
    const a = c.clone().addScaledVector(right, s).addScaledVector(up, -height / 2);
    const b = a.clone().addScaledVector(right, w);
    const d = a.clone().addScaledVector(up, height);
    const e = b.clone().addScaledVector(up, height);
    for (const [p, uv] of [[a, [u0, v0]], [b, [u1, v0]], [e, [u1, v1]], [a, [u0, v0]], [e, [u1, v1]], [d, [u0, v1]]]) {
      positions.push(p.x, p.y, p.z);
      uvs.push(uv[0], uv[1]);
    }
    s += adv[i];
  }
  return { positions, uvs };
}

/** Fold away a figure past `reach` metres from the eye, in the vertex stage. */
function withReach(material, reach) {
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uNumberReach = { value: reach };
    shader.vertexShader = shader.vertexShader
      .replace('void main() {', 'uniform float uNumberReach;\nvoid main() {')
      .replace('#include <project_vertex>', `#include <project_vertex>
  if (distance((modelMatrix * vec4(transformed, 1.0)).xyz, cameraPosition) > uNumberReach) gl_Position = vec4(0.0, 0.0, 2.0, 1.0);`);
  };
  material.customProgramCacheKey = () => `house-numbers-reach-${reach}`;
  return material;
}

async function getJSON(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return res.json();
}

/**
 * @param {object} o dataBase (data/ root, or null when the scene does not list the layer) ·
 *   sceneId · buildings (buildings.js: `matrixOf`) · problems · doc (a list already in hand)
 * @returns {Promise<{group: THREE.Group, census: object, doc: object|null}>}
 */
export async function createHouseNumbers({ dataBase = null, sceneId = '', buildings = null, problems = [], doc = null, document: dom } = {}) {
  const group = new THREE.Group();
  group.name = 'house-numbers';
  const census = { numbers: 0, figures: 0, placed: 0, unplaced: [], triangles: 0, draws: 0, hands: {} };
  const out = { group, census, doc: null, mesh: null };
  if ((!dataBase && !doc) || !buildings?.matrixOf) return out;
  try {
    doc = doc ?? await getJSON(new URL(`house_numbers/${sceneId}.json`, dataBase));
  } catch (err) {
    problems.push(`house numbers not loaded — ${err.message}`);
    return out;
  }
  out.doc = doc;
  const atlas = drawAtlas(doc.hands ?? PLAIN, dom);
  if (!atlas) {
    problems.push('house numbers: no canvas to draw the figures on');
    return out;
  }
  const positions = [], uvs = [], normals = [];
  const v = new THREE.Vector3();
  const nm = new THREE.Matrix3();
  for (const row of doc.numbers ?? []) {
    census.numbers++;
    const m = buildings.matrixOf(row.structure);
    if (!m) { census.unplaced.push(row.structure); continue; }
    const hand = atlas.hands[row.hand] ?? Object.values(atlas.hands)[0];
    const q = numberQuads(row.number, row.at, row.normal, row.height_m, hand.widths, hand.row);
    nm.getNormalMatrix(m);
    const wn = new THREE.Vector3(...row.normal).applyMatrix3(nm).normalize();
    for (let i = 0; i < q.positions.length; i += 3) {
      v.set(q.positions[i], q.positions[i + 1], q.positions[i + 2]).applyMatrix4(m);
      positions.push(v.x, v.y, v.z);
      normals.push(wn.x, wn.y, wn.z);
    }
    uvs.push(...q.uvs);
    census.figures += q.positions.length / 18;
    census.placed++;
    census.hands[row.hand ?? 'plain'] = (census.hands[row.hand ?? 'plain'] ?? 0) + 1;
  }
  if (!positions.length) return out;
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geometry.computeBoundingSphere();
  const texture = new THREE.CanvasTexture(atlas.canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  const material = withReach(new THREE.MeshStandardMaterial({
    map: texture, alphaTest: 0.5, roughness: 0.55, metalness: 0.0, side: THREE.FrontSide,
    // Gold leaf on glass is lit by the street, not by itself: only a trace of its own light.
    emissive: 0xffffff, emissiveMap: texture, emissiveIntensity: EMISSIVE,
    polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1,
  }), REACH_M);
  material.name = 'house_number_gilt';
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = 'house-numbers';
  mesh.castShadow = false;
  mesh.receiveShadow = true;
  mesh.matrixAutoUpdate = false;
  group.add(mesh);
  out.mesh = mesh;
  census.triangles = positions.length / 9;
  census.draws = 1;
  return out;
}
