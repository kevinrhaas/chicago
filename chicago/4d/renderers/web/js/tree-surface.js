/**
 * T-2015: deterministic, code-authored woody surface atlas. These are render
 * reconstructions, not photographs or botanical evidence. The zone records
 * still decide species, size, colour, phenology and where each plant stands.
 * All sixteen tiles are generated here; no external image/license is needed.
 */
import * as THREE from 'three';

export const TREE_ALPHA_CUTOFF = 0.38;
const TILE = 512;
const GRID = 4;
const SIZE = TILE * GRID;

export function leafFamily(spec) {
  const name = `${spec.speciesId ?? ''} ${spec.common ?? ''}`.toLowerCase();
  if (/quercus|oak/.test(name)) return 0;
  if (/salix|willow/.test(name)) return 1;
  if (/populus|poplar|cottonwood|aspen/.test(name)) return 2;
  if (/fraxinus|ash|carya|hickory|juglans|walnut|locust|robinia|gymnocladus/.test(name)) return 4;
  if (/acer|maple|platanus|sycamore|currant|ribes/.test(name)) return 5;
  if (/tilia|basswood|catalpa|redbud|cercis/.test(name)) return 6;
  return 3;
}

export function treeAtlasUV(tile, u, v) {
  // A transparent gutter keeps a neighbouring tile out of minification/mips.
  const pad = 6 / TILE;
  return [(tile % GRID + pad + u * (1 - 2 * pad)) / GRID,
    1 - (Math.floor(tile / GRID) + pad + (1 - v) * (1 - 2 * pad)) / GRID];
}

function random(seed) {
  let a = seed >>> 0;
  return () => { a = (Math.imul(a, 1664525) + 1013904223) >>> 0; return a / 4294967296; };
}

function leaf(ctx, family, x, y, length, angle, shade, rnd) {
  ctx.save();
  ctx.translate(x, y); ctx.rotate(angle);
  const w = length * [0.39, 0.12, 0.45, 0.30, 0.27, 0.48, 0.47][family];
  const path = new Path2D();
  path.moveTo(0, 0);
  if (family === 0) {
    for (let side = -1; side <= 1; side += 2) {
      if (side === 1) path.lineTo(0, -length);
      for (let i = 1; i <= 10; i++) {
        const t = side === -1 ? i / 10 : 1 - i / 10;
        const lobe = i % 2 ? 1 : 0.54;
        path.lineTo(side * w * Math.sin(Math.PI * t) * lobe, -length * t);
      }
    }
  } else if (family === 2) {
    path.lineTo(-w, -length * 0.28); path.lineTo(0, -length);
    path.lineTo(w, -length * 0.28);
  } else if (family === 5) {
    for (let i = 0; i < 10; i++) {
      const a = -Math.PI / 2 + i * Math.PI / 5;
      const r = (i % 2 ? 0.44 : 0.94) * length * 0.56;
      path.lineTo(Math.cos(a) * r, -length * 0.46 + Math.sin(a) * r);
    }
  } else if (family === 6) {
    path.bezierCurveTo(-w * 1.4, length * 0.03, -w, -length * 0.58, 0, -length);
    path.bezierCurveTo(w, -length * 0.55, w * 1.3, length * 0.04, 0, 0);
  } else {
    path.bezierCurveTo(-w * 0.9, -length * 0.20, -w, -length * 0.63, 0, -length);
    path.bezierCurveTo(w * 0.85, -length * 0.72, w, -length * 0.2, 0, 0);
  }
  path.closePath();
  const grad = ctx.createLinearGradient(-w, -length * 0.5, w, -length * 0.5);
  const value = Math.round(shade);
  grad.addColorStop(0, `rgb(${value * 0.64},${value * 0.69},${value * 0.58})`);
  grad.addColorStop(0.48, `rgb(${value},${value},${value * 0.91})`);
  grad.addColorStop(0.53, `rgb(${value * 0.79},${value * 0.86},${value * 0.71})`);
  grad.addColorStop(1, `rgb(${value * 0.73},${value * 0.81},${value * 0.63})`);
  ctx.fillStyle = grad; ctx.fill(path);
  // The crease and secondary veins remain fine rather than outlining every leaf.
  ctx.save(); ctx.clip(path);
  ctx.strokeStyle = `rgba(231,230,178,${0.18 + rnd() * 0.12})`; ctx.lineWidth = 0.5;
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, -length);
  for (let i = 2; i < 7; i++) {
    const t = i / 8;
    ctx.moveTo(0, -length * t);
    ctx.lineTo(-w * Math.sin(Math.PI * t) * 0.88, -length * (t + 0.16));
    ctx.moveTo(0, -length * t);
    ctx.lineTo(w * Math.sin(Math.PI * t) * 0.88, -length * (t + 0.16));
  }
  ctx.stroke(); ctx.restore(); ctx.restore();
}

function spray(ctx, family, seed) {
  const rnd = random(seed);
  const leaves = [];
  ctx.strokeStyle = 'rgb(112,108,85)'; ctx.lineCap = 'round';
  function shoot(x, y, angle, length, depth) {
    const bend = (rnd() - 0.5) * 0.45;
    const tx = x + Math.sin(angle + bend) * length;
    const ty = y - Math.cos(angle + bend) * length;
    ctx.lineWidth = depth === 0 ? 2.1 : depth === 1 ? 1.0 : 0.55;
    ctx.beginPath(); ctx.moveTo(x, y);
    ctx.quadraticCurveTo(x + Math.sin(angle) * length * 0.5,
      y - Math.cos(angle) * length * 0.5, tx, ty); ctx.stroke();
    if (depth < 2) {
      const n = depth === 0 ? 8 : 3;
      for (let i = 0; i < n; i++) {
        const t = (i + 0.45 + rnd() * 0.45) / (n + 0.5);
        const sign = i % 2 ? 1 : -1;
        const a = angle + sign * (0.53 + rnd() * 0.75);
        shoot(x + (tx - x) * t, y + (ty - y) * t, a,
          length * (depth ? 0.35 + rnd() * 0.17 : 0.25 + 0.22 * (1 - t)), depth + 1);
      }
    }
    if (depth) {
      const n = depth === 1 ? 5 : 7;
      for (let i = 0; i < n; i++) {
        const t = (i + rnd() * 0.7) / n;
        const bx = x + (tx - x) * t, by = y + (ty - y) * t;
        // Compound leaves retain paired leaflets. Broad leaves have alternate,
        // unequal petioles and individually turned blades, not fern fronds.
        const count = family === 4 ? 2 : 1 + (rnd() < 0.55 ? 1 : 0);
        for (let j = 0; j < count; j++) {
          const sign = family === 4 ? (j ? 1 : -1) : (i + j) % 2 ? 1 : -1;
          const a = family === 4 ? angle + sign * 0.92
            : angle + sign * (0.3 + rnd() * 2.2);
          const px = bx + Math.sin(a) * (3 + rnd() * 4);
          const py = by - Math.cos(a) * (3 + rnd() * 4);
          ctx.lineWidth = 0.45; ctx.beginPath();ctx.moveTo(bx, by);ctx.lineTo(px, py);ctx.stroke();
          leaves.push([px, py, (family === 1 ? 25 : 20) * (0.63 + rnd() * 0.66),
            a, 174 + rnd() * 75]);
        }
      }
    }
    if (depth) leaves.push([tx, ty, 19 + rnd() * 6, angle + (rnd() - 0.5) * 1.3, 211]);
  }
  shoot(251, 472, -0.16, 357, 0);
  leaves.sort((a, b) => b[1] - a[1]);
  for (const [x, y, len, a, shade] of leaves) leaf(ctx, family, x, y, len, a, shade, rnd);
}

/** Keep the covered leaf area as the atlas minifies; ordinary averaged alpha
 * makes fine leaves vanish once each blade occupies less than one pixel. Each
 * family is rescaled independently so a willow cannot inherit an oak's density.
 * This is filtered coverage, never camera-distance dither or a geometry switch.
 */
function foliageMipmaps(source) {
  const levels = [source];
  const base = source.getContext('2d').getImageData(0, 0, SIZE, SIZE).data;
  const coverage = [];
  for (let tile = 0; tile < 14; tile++) {
    let covered = 0;
    const bx = tile % GRID * TILE, by = Math.floor(tile / GRID) * TILE;
    for (let y = 0; y < TILE; y++) for (let x = 0; x < TILE; x++) {
      if (base[((by + y) * SIZE + bx + x) * 4 + 3] >= TREE_ALPHA_CUTOFF * 255) covered++;
    }
    coverage.push(covered / (TILE * TILE));
  }
  for (let size = SIZE / 2; size >= 1; size /= 2) {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = size;
    const ctx = canvas.getContext('2d'); ctx.drawImage(source, 0, 0, size, size);
    const pixels = ctx.getImageData(0, 0, size, size);
    const tileSize = size / GRID;
    if (tileSize >= 2) for (let tile = 0; tile < 14; tile++) {
      const bx = tile % GRID * tileSize, by = Math.floor(tile / GRID) * tileSize;
      const hist = new Uint32Array(256);
      for (let y = 0; y < tileSize; y++) for (let x = 0; x < tileSize; x++) {
        hist[pixels.data[((by + y) * size + bx + x) * 4 + 3]]++;
      }
      const target = coverage[tile] * tileSize * tileSize;
      let sum = 0, threshold = 255;
      for (; threshold > 1 && sum < target; threshold--) sum += hist[threshold];
      const gain = Math.max(1, (TREE_ALPHA_CUTOFF * 255 + 2) / Math.max(1, threshold));
      for (let y = 0; y < tileSize; y++) for (let x = 0; x < tileSize; x++) {
        const at = ((by + y) * size + bx + x) * 4 + 3;
        pixels.data[at] = Math.min(255, pixels.data[at] * gain);
      }
    }
    ctx.putImageData(pixels, 0, 0); levels.push(canvas);
  }
  return levels;
}

export function createTreeAtlas() {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = SIZE;
  const ctx = canvas.getContext('2d');
  for (let tile = 0; tile < 14; tile++) {
    ctx.save(); ctx.translate((tile % GRID) * TILE, Math.floor(tile / GRID) * TILE);
    ctx.beginPath(); ctx.rect(7, 7, TILE - 14, TILE - 14); ctx.clip();
    spray(ctx, tile % 7, 8801 + tile * 7919); ctx.restore();
  }
  // Bark is achromatic so the record's species-specific colour stays in charge.
  const x0 = 2 * TILE, y0 = 3 * TILE;
  ctx.fillStyle = 'rgb(206,203,194)'; ctx.fillRect(x0, y0, TILE, TILE);
  const rnd = random(48231);
  ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, TILE, TILE); ctx.clip();
  for (let i = 0; i < 240; i++) {
    const bx = x0 + rnd() * TILE, phase = rnd() * Math.PI * 2;
    const amplitude = 2 + rnd() * 5;
    ctx.strokeStyle = `rgba(49,42,33,${0.15 + rnd() * 0.45})`;
    ctx.lineWidth = 0.5 + rnd() * 3.5; ctx.beginPath();
    // Periodic at the UV gutter's 6px and 506px boundaries, so two tapered
    // bole segments meet on continuous grain instead of a horizontal seam.
    for (let y = -16; y <= TILE + 16; y += 4) {
      const t = (y - 6) / (TILE - 12) * Math.PI * 2;
      const x = bx + Math.sin(t + phase) * amplitude + Math.sin(t * 3 + phase) * amplitude * 0.35;
      if (y === -16) ctx.moveTo(x, y0 + y); else ctx.lineTo(x, y0 + y);
    }
    ctx.stroke();
  }
  ctx.restore();
  ctx.fillStyle = '#fff'; ctx.fillRect(3 * TILE, 3 * TILE, TILE, TILE);
  const texture = new THREE.CanvasTexture(canvas);
  texture.name = 'procedural-species-leaf-and-bark-atlas';
  texture.mipmaps = foliageMipmaps(canvas);
  texture.generateMipmaps = false;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.anisotropy = 4;
  return texture;
}

/** Colour AND depth use exactly this deformation; cutout shadows cannot lag. */
export function patchTreeWind(material, uWind, { surface = false } = {}) {
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uWind = uWind;
    shader.vertexShader = `attribute float aFlex;\nuniform float uWind;\n`
      + shader.vertexShader.replace('#include <begin_vertex>', `
#include <begin_vertex>
vec3 chiW = (modelMatrix * vec4(transformed, 1.0)).xyz;
float chiS = sin(uWind * 0.85 + chiW.x * 0.055 + chiW.z * 0.041) * 0.62
           + sin(uWind * 1.63 + chiW.x * 0.113 - chiW.z * 0.087) * 0.28;
transformed.x += chiS * aFlex * 0.42;
transformed.z += chiS * aFlex * 0.26;
`);
    if (surface) {
      shader.vertexShader = 'attribute float aLeaf;\nvarying float vTreeLeaf;\n'
        + shader.vertexShader.replace('#include <begin_vertex>',
          '#include <begin_vertex>\nvTreeLeaf = aLeaf;');
      shader.fragmentShader = 'varying float vTreeLeaf;\n' + shader.fragmentShader;
      // T-2110: a leaf card keeps 3.5 % of the bump, and the bump reads the
      // atlas three more times a fragment — 31 % of the trees' frame at the
      // phone's worst stand. So the bump is only computed where it is kept
      // whole, on bark. `aLeaf` is 0 or 1 for a whole card, so the branch is
      // uniform across every triangle and its derivatives stay defined.
      shader.fragmentShader = shader.fragmentShader.replace('#include <normal_fragment_maps>', `
vec3 chiUnrelievedNormal = normal;
if (vTreeLeaf < 0.5) {
#include <normal_fragment_maps>
}
normal = normalize(mix(chiUnrelievedNormal, normal, mix(1.0, 0.035, vTreeLeaf)));
`).replace('#include <roughnessmap_fragment>', `
#include <roughnessmap_fragment>
roughnessFactor *= mix(1.0, 0.82, vTreeLeaf);
`);
      // Thin leaves transmit skylight. This small diffuse term is not emissive
      // bloom; fog, tone mapping and confidence still act on the final surface.
      shader.fragmentShader = shader.fragmentShader.replace('#include <lights_fragment_end>', `
#include <lights_fragment_end>
reflectedLight.indirectDiffuse += diffuseColor.rgb * (0.22 * vTreeLeaf);
`);
    }
  };
  material.customProgramCacheKey = () => `tree-surface-t2015-${surface ? 'lit' : 'depth'}`;
}
