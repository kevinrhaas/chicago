/**
 * T-2015 — procedural botanical surfaces for the existing flora archetypes.
 *
 * These are reconstructed leaf shapes, not a new flora census or an archival
 * photograph. The record still owns species, clump width, height and July
 * phenology. This atlas only resolves the old opaque spray plates into stems,
 * leaf margins, veins and small variations in the cuticle. All pixels are
 * generated here, deterministically; there is no downloaded/licensed asset.
 *
 * Two columns (single leaf / leafy shoot), eight botanical families. Ordinary
 * RGBA mipmaps and alpha clipping preserve one opaque, depth-writing draw per
 * archetype. A tile has transparent gutters to prevent adjacent-family bleed.
 */
import * as THREE from 'three';

const TILE = 256;
const FAMILIES = 8;

/** Reconstruction within each recorded taxon's familiar leaf habit. A common
 * oval profile is the explicit fallback, not a fabricated species record. */
export function foliageFamily(id = '') {
  if (/juniperus/.test(id)) return 5;
  if (/quercus/.test(id)) return 4;
  if (/sambucus|fraxinus/.test(id)) return 3;
  if (/salix|spiraea|liatris|allium|asclepias_tuberosa/.test(id)) return 2;
  if (/achillea|artemisia|ambrosia|desmodium|dalea/.test(id)) return 6;
  if (/silphium|plantago|rumex/.test(id)) return 7;
  if (/corylus|vitis|rubus/.test(id)) return 0;
  return 1;
}

function random(seed) {
  let n = seed >>> 0;
  return () => {
    n ^= n << 13; n ^= n >>> 17; n ^= n << 5;
    return (n >>> 0) / 4294967296;
  };
}

function outline(t, family, phase) {
  const base = Math.pow(Math.max(0, Math.sin(Math.PI * t)), family === 7 ? 0.58 : 0.82);
  let edge = 1;
  if (family === 4) edge = 0.72 + 0.28 * Math.cos(t * Math.PI * 10 + 0.3);
  else if (family === 6) edge = 0.55 + 0.45 * Math.cos(t * Math.PI * 14 + 0.2) ** 2;
  else if (family !== 5) edge = 0.96 + 0.04 * Math.sin(t * Math.PI * 52 + phase);
  return base * edge;
}

function leaf(ctx, base, tip, half, family, rng, tone = 1) {
  const vx = tip[0] - base[0], vy = tip[1] - base[1];
  const length = Math.hypot(vx, vy);
  const phase = rng() * 6.28;
  const curve = (rng() - 0.5) * half * 0.38;
  ctx.save();
  ctx.translate(base[0], base[1]);
  ctx.rotate(Math.atan2(vy, vx));
  ctx.beginPath();
  for (const sign of [1, -1]) {
    for (let i = 0; i <= 48; i++) {
      const t = sign === 1 ? i / 48 : 1 - i / 48;
      const width = half * outline(t, family, phase);
      const y = sign * width + Math.sin(t * Math.PI) * curve;
      if (sign === 1 && i === 0) ctx.moveTo(t * length, y);
      else ctx.lineTo(t * length, y);
    }
  }
  ctx.closePath();
  const gradient = ctx.createLinearGradient(length * 0.3, -half, length * 0.55, half);
  const c = (v) => Math.round(v * tone);
  gradient.addColorStop(0, `rgb(${c(163)},${c(175)},${c(159)})`);
  gradient.addColorStop(0.42, `rgb(${c(215)},${c(222)},${c(204)})`);
  gradient.addColorStop(0.50, `rgb(${c(173)},${c(185)},${c(158)})`);
  gradient.addColorStop(0.58, `rgb(${c(218)},${c(225)},${c(205)})`);
  gradient.addColorStop(1, `rgb(${c(174)},${c(185)},${c(161)})`);
  ctx.fillStyle = gradient;
  ctx.fill();
  ctx.save();
  ctx.clip();
  // Secondary veins join the midrib at an acute angle and diminish toward
  // the margin; the raster is small enough to naturally mip them away.
  ctx.lineWidth = Math.max(0.45, length / 230);
  ctx.strokeStyle = 'rgba(224,231,206,0.34)';
  for (let i = 1; i < 9; i++) {
    const t = i / 10;
    for (const sign of [-1, 1]) {
      const end = Math.min(0.98, t + 0.13);
      const edge = sign * half * outline(end, family, phase) * 0.92;
      ctx.beginPath();
      ctx.moveTo(length * t, Math.sin(t * Math.PI) * curve);
      ctx.quadraticCurveTo(length * (t + 0.10), edge * 0.36,
        length * end, edge + Math.sin(end * Math.PI) * curve);
      ctx.stroke();
    }
  }
  ctx.lineWidth = Math.max(0.6, length / 100);
  ctx.strokeStyle = 'rgba(234,235,205,0.70)';
  ctx.beginPath(); ctx.moveTo(0, 0);
  ctx.quadraticCurveTo(length * 0.50, curve * 1.3, length, 0); ctx.stroke();
  // Subtle mesophyll mottling; neither regular polka dots nor painted holes.
  for (let i = 0; i < 34; i++) {
    const x = rng() * length, y = (rng() * 2 - 1) * half;
    ctx.fillStyle = rng() < 0.5 ? 'rgba(64,87,54,0.055)' : 'rgba(251,249,222,0.07)';
    ctx.beginPath(); ctx.ellipse(x, y, 0.4 + rng() * 1.4,
      0.3 + rng() * 0.8, 0, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore(); ctx.restore();
}

function shoot(ctx, family, rng) {
  const pairs = family === 5 ? 18 : family === 3 ? 7 : 7;
  const woody = family === 5 ? 1.7 : 1.3;
  const stem = (x) => 128 + Math.sin(x * Math.PI) * 11;
  ctx.strokeStyle = 'rgb(130,128,98)';
  ctx.lineWidth = woody;
  ctx.beginPath(); ctx.moveTo(128, 247);
  ctx.bezierCurveTo(138, 169, 140, 79, 128, 12); ctx.stroke();
  for (let i = 0; i < pairs; i++) {
    const t = (i + 0.6) / (pairs + 0.4);
    const y = 228 - t * 184;
    for (const sign of [-1, 1]) {
      const skew = family === 3 || family === 5 ? 0 : sign * 9;
      const base = [stem(t), y + skew];
      const spread = family === 5 ? 48 + rng() * 35 : 68 + rng() * 39;
      const tip = [base[0] + sign * spread, y - (family === 5 ? 26 : 30 + rng() * 21)];
      const half = family === 5 ? 2.5 : family === 2 ? 12 : family === 3 ? 14 : 20 + rng() * 6;
      leaf(ctx, base, tip, half, family, rng, 0.85 + rng() * 0.15);
    }
  }
  if (family !== 5) {
    // A spray represents several internodes, with short side shoots filling
    // its interior. Their smaller leaves keep physical grain instead of
    // increasing one leaf until it fills the old rectangle again.
    for (let i = 0; i < 6; i++) {
      const y = 217 - i * 32;
      const sign = i % 2 ? -1 : 1;
      const base = [128 + sign * (13 + rng() * 16), y];
      const tip = [base[0] + sign * (20 + rng() * 25), y - 48 - rng() * 15];
      leaf(ctx, base, tip, family === 2 ? 8 : 12 + rng() * 7, family, rng,
        0.79 + rng() * 0.17);
    }
  }
  leaf(ctx, [129, 58], [126, 7], family === 5 ? 2.6 : family === 2 ? 10 : 15,
    family, rng, 0.98);
}

export function foliageAtlas() {
  const canvas = document.createElement('canvas');
  canvas.width = TILE * 2; canvas.height = TILE * FAMILIES;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('flora: could not build procedural foliage atlas');
  for (let row = 0; row < FAMILIES; row++) {
    const rng = random(0x183500ab + row * 7141);
    ctx.save(); ctx.translate(0, row * TILE);
    // A needle/willow remains narrow even though the support polygon is broad.
    const half = row === 5 ? 8 : row === 2 ? 50 : 104;
    leaf(ctx, [128, 251], [128, 5], half, row, rng);
    ctx.translate(TILE, 0);
    shoot(ctx, row, rng);
    ctx.restore();
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.name = 'procedural-understory-leaves';
  texture.colorSpace = THREE.NoColorSpace; // relative albedo; species owns hue
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.anisotropy = 4;
  texture.needsUpdate = true;
  return texture;
}
