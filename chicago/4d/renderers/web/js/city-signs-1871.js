/**
 * city-signs-1871.js — T-3803: the signs over the 1871 shops round the jaunt stops
 * are the firms of October 1871, lettered at runtime.
 *
 * Kevin, 2026-11-27: "the signs above stores must need to be varied and be more
 * specific based on your research of the citizens and people and businesses in
 * 1871". data/context/1871/directory_fronts.json (tools/build_1871_directory_fronts.py)
 * holds the firms Edwards' 1871 directory lists on the faces round the stops, the
 * pre-1909 numbering that puts each on its block face and its place along it, and
 * the trades each street's classified listings carry. Here:
 *
 *  1. PLAN. Every shop front inside the detail rings is matched to the face it
 *     stands on (the street in front of it, the side, the block between two cross
 *     streets) and its place along that face in the direction the numbers run. The
 *     firm whose number falls on it takes it; a front no listed number reaches gets a
 *     trade of that street from the classified directory, never its neighbour's.
 *     An upstairs office (a "room" address, a lawyer, a photographer) at the same
 *     number is lettered between the upper windows.
 *  2. FORM. Each front's signs are chosen per front, as the period views show them
 *     (Carbutt's Lake and Clark Street stereographs, the Lake Street stereoview and
 *     the Library Hall slide in /1871-references): a long name board over the
 *     storefront, a board on the wall between the storefront and the first upper
 *     windows, the name lettered along the cornice frieze, a hanging board at right
 *     angles to the walk on an iron bracket, narrow boards on the iron piers, gilt
 *     letters on the plate glass, the name on the awning's valance. Faces: Roman,
 *     fat face, Egyptian (Clarendon) slab, a Tuscan-ornamented slab, condensed sans;
 *     grounds black, dark green, maroon, cream, white, blue-black; letters gilt,
 *     white, black, cream or vermilion, shaded or not. Every choice is reconstructed
 *     (docs/LIBERTIES.md L-1871-directory-signs).
 *  3. PAINT. The lettering is painted once into canvas atlases, packed cell by cell
 *     (one draw per detail cell), the texel density scaled down until every sign
 *     fits the tier's pages: full 3 x 2048², balanced 2 x 2048², light 1 x 2048 x 1024.
 *     Nothing is shipped but the period faces the 1835 signs already use.
 */
import * as THREE from 'three';

const FACES = {
  roman: { family: '"Old Standard TT", Georgia, "Times New Roman", serif', weight: 700, scaleX: 1, track: 0.06 },
  fat: { family: '"Abril Fatface", Georgia, serif', weight: 400, scaleX: 1, track: 0.03 },
  egyptian: { family: '"Alfa Slab One", Rockwell, "Courier New", serif', weight: 400, scaleX: 0.94, track: 0.04 },
  tuscan: { family: '"Alfa Slab One", Rockwell, "Courier New", serif', weight: 400, scaleX: 0.86, track: 0.06, inline: true },
  condensed: { family: 'Anton, Impact, "Arial Narrow", sans-serif', weight: 400, scaleX: 0.92, track: 0.08 },
};
const TRADE_FACE = { family: '"Old Standard TT", Georgia, serif', weight: 700, scaleX: 1, track: 0.1 };
const ITALIC_FACE = { family: '"Old Standard TT", Georgia, serif', weight: 400, style: 'italic', scaleX: 1, track: 0.02 };
const FACE_KEYS = Object.keys(FACES);
const SIGN_FONTS = [
  ['Old Standard TT', 'sign-old-standard-700.woff2', '700', 'normal'],
  ['Old Standard TT', 'sign-old-standard-400.woff2', '400', 'normal'],
  ['Old Standard TT', 'sign-old-standard-400-italic.woff2', '400', 'italic'],
  ['Abril Fatface', 'sign-abril-fatface-400.woff2', '400', 'normal'],
  ['Alfa Slab One', 'sign-alfa-slab-one-400.woff2', '400', 'normal'],
  ['Anton', 'sign-anton-400.woff2', '400', 'normal'],
];
// Grounds and lettering, as painted boards of the period went (reconstructed).
const BOARDS = [
  { ground: '#141414', letter: 'gilt', shade: '#5a3a10' },
  { ground: '#1d3527', letter: 'gilt', shade: '#0b130d' },
  { ground: '#1d3527', letter: '#f1ead8', shade: '#08100a' },
  { ground: '#4e1a17', letter: 'gilt', shade: '#1e0806' },
  { ground: '#ede4cc', letter: '#1a1a1a', shade: '#8c2a1c' },
  { ground: '#f3efe4', letter: '#141414', shade: null },
  { ground: '#141414', letter: '#f3efe4', shade: '#7a1f17' },
  { ground: '#1b2333', letter: 'gilt', shade: '#0a0d14' },
  { ground: '#e9dfc6', letter: '#7a1a14', shade: '#1a1a1a' },
  { ground: '#2a2522', letter: '#e9dfc6', shade: null },
];
// Lettering straight on a wall or on glass: no ground.
const BARE = [
  { letter: 'gilt', shade: '#2a1a08' }, { letter: '#f3efe4', shade: '#1a1a1a' },
  { letter: '#141414', shade: null }, { letter: '#efe8d6', shade: '#5a1a12' },
];
const TIER = {
  full: { pages: 2, w: 2048, h: 2048, density: 110, secondaries: true },
  balanced: { pages: 2, w: 2048, h: 2048, density: 90, secondaries: true },
  light: { pages: 1, w: 2048, h: 1024, density: 64, secondaries: false },
};

const hash = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return h >>> 0; };

/** The six period faces, loaded before anything is painted; false when any failed. */
async function loadFonts(problems) {
  if (typeof document === 'undefined' || typeof FontFace !== 'function' || !document.fonts) return false;
  const load = Promise.all(SIGN_FONTS.map(async ([family, file, weight, style]) => {
    const face = new FontFace(family, `url(${new URL(`../fonts/${file}`, import.meta.url)})`, { weight, style });
    await face.load();
    document.fonts.add(face);
  }));
  let timer;
  try {
    await Promise.race([load, new Promise((_, no) => { timer = setTimeout(() => no(new Error('timed out')), 8000); })]);
    return true;
  } catch (error) {
    problems.push(`1871 shop signs: the period faces did not load (${error.message}); lettered in fallback faces`);
    return false;
  } finally { clearTimeout(timer); }
}

/** A trade as a board says it: "hats, caps and furs" -> HATS, CAPS & FURS. */
export function tradeWords(trade) {
  if (!trade) return '';
  let t = String(trade).trim();
  const whole = /\(wholesale\)/i.test(t) || /^wholesale\b/i.test(t);
  t = t.replace(/\s*\((wholesale|retail|manufacturers|importers|jobbers)\)/ig, '')
    .replace(/,\s*(retail|wholesale)$/i, '').replace(/^wholesale\s+/i, '');
  t = t.replace(/\band\b/g, '&').replace(/\s+/g, ' ');
  return ((whole ? 'WHOLESALE ' : '') + t).toUpperCase();
}

/** A street's classified trade as a shop board names it ("Saloons" -> SALOON). */
function tradeSign(t) {
  const one = { Saloons: 'SALOON', Restaurants: 'RESTAURANT', Bankers: 'BANKING HOUSE', Banks: 'BANK',
    Trunks: 'TRUNKS', Druggists: 'DRUG STORE', Barbers: 'BARBER SHOP', Bands: 'MUSIC', Dentists: 'DENTIST',
    'Billiard Halls': 'BILLIARDS', Photographers: 'PHOTOGRAPHS', Furriers: 'FURS', Engravers: 'ENGRAVER' };
  return one[t] ?? tradeWords(t);
}

/** Which face of the directory a front stands on, and how far along it. */
function faceOf(faces, fe, fn, out) {
  let best = null;
  for (const f of faces) {
    const [ax, ay] = f.a, [bx, by] = f.b, dx = bx - ax, dy = by - ay, L = Math.hypot(dx, dy);
    const ux = dx / L, uy = dy / L;
    const along = (fe - ax) * ux + (fn - ay) * uy;
    const off = -(fe - ax) * uy + (fn - ay) * ux; // + left of a->b
    if (Math.abs(off) > f.half_m + 9 || Math.abs(off) < f.half_m - 4) continue;
    const side = Math.abs(dx) > Math.abs(dy) ? (fn > ay + uy * along ? 'n' : 's') : (fe > ax + ux * along ? 'e' : 'w');
    if (side !== f.side) continue;
    // The front must look at the street.
    const toStreet = [-uy * Math.sign(off), ux * Math.sign(off)];
    if (out[0] * toStreet[0] + out[1] * toStreet[1] > -0.7) continue;
    const t = (along - f.cross_half_m[0]) / (L - f.cross_half_m[0] - f.cross_half_m[1]);
    if (t < -0.03 || t > 1.03) continue;
    if (!best || Math.abs(off) < Math.abs(best.off)) best = { face: f, t: Math.max(0, Math.min(1, t)), off, ux, uy, L };
  }
  return best;
}

/**
 * The plan: for each shop row in the rings, the firm (or trade) and the signs it
 * carries, with their sizes in metres. `fronts` are buildFronts' own shop frames:
 * { r, w, h, gf, storeys, bays, bw, awning, out:[e,n], centre:[e,n], focus }.
 */
export function planSigns(doc, fronts, detail) {
  const tier = TIER[detail] ?? TIER.full;
  const byFace = new Map();
  const unplaced = [];
  for (const fr of fronts) {
    const hit = faceOf(doc.faces, fr.centre[0], fr.centre[1], fr.out);
    if (!hit) { unplaced.push(fr); continue; }
    // The front's span along the face, as fractions.
    const half = fr.w / 2 / (hit.L - hit.face.cross_half_m[0] - hit.face.cross_half_m[1]);
    fr.face = hit.face; fr.t = hit.t; fr.t0 = hit.t - half; fr.t1 = hit.t + half;
    if (!byFace.has(hit.face.id)) byFace.set(hit.face.id, []);
    byFace.get(hit.face.id).push(fr);
  }
  const firmsByFace = new Map();
  for (const firm of doc.firms) {
    if (!firmsByFace.has(firm.face)) firmsByFace.set(firm.face, []);
    firmsByFace.get(firm.face).push(firm);
  }
  const plans = new Map();
  const census = { fronts: fronts.length, firms: 0, upstairs: 0, trades: 0, unplaced: unplaced.length, signs: 0 };
  const assign = (list, frs, key) => {
    const used = new Set();
    for (const fr of frs) {
      let best = null, bd = Infinity;
      for (const firm of list) {
        if (used.has(firm.id)) continue;
        const d = firm.along < fr.t0 ? fr.t0 - firm.along : firm.along > fr.t1 ? firm.along - fr.t1 : 0;
        const slack = key === 'firm' ? 0.06 : 0.02;
        if (d <= slack && (d < bd || d === bd && Math.abs(firm.along - fr.t) < Math.abs(best.along - fr.t))) { best = firm; bd = d; }
      }
      if (best) { used.add(best.id); fr[key] = best; }
    }
  };
  for (const [fid, frs] of byFace) {
    frs.sort((p, q) => p.t - q.t);
    const firms = firmsByFace.get(fid) ?? [];
    assign(firms.filter(f => f.floor === 'street'), frs, 'firm');
    assign(firms.filter(f => f.floor === 'upstairs'), frs, 'upper');
    // A front no number reaches keeps a trade of its street, never its neighbours'.
    const trades = doc.street_trades?.[frs[0].face.street] ?? [];
    for (let i = 0; i < frs.length; i++) {
      const fr = frs[i];
      if (fr.firm || !trades.length) continue;
      const near = new Set([frs[i - 1], frs[i + 1]].filter(Boolean).map(x => x.firm ? tradeWords(x.firm.trade) : x.tradeOnly));
      let k = hash(fr.r.id) % trades.length;
      for (let n = 0; n < trades.length && near.has(tradeSign(trades[k])); n++) k = (k + 1) % trades.length;
      fr.tradeOnly = tradeSign(trades[k]);
    }
  }
  // Fronts off every listed face (an alley, a cross street the rings reach) keep a
  // trade from the whole list, still never their neighbours'.
  const all = [...new Set(Object.values(doc.street_trades ?? {}).flat())];
  for (const fr of unplaced) if (all.length) fr.tradeOnly = tradeSign(all[hash(fr.r.id) % all.length]);

  for (const fr of fronts) {
    const h0 = hash(String(fr.r.id));
    const pick = (n, salt) => (hash(`${fr.r.id}:${salt}`) % n);
    const name = fr.firm ? fr.firm.name.toUpperCase() : null;
    const trade = fr.firm ? tradeWords(fr.firm.trade) : fr.tradeOnly;
    if (!name && !trade) continue;
    if (fr.firm) census.firms++; else census.trades++;
    const face = FACE_KEYS[pick(FACE_KEYS.length, 'face')];
    const board = BOARDS[pick(BOARDS.length, 'board')];
    const signs = [];
    // A board is as long as its lettering wants, never longer than the front: the
    // painters' boards ran to the words, and the atlas holds no blank board.
    const fit = (full, hM, ls, pad = 0.6) => {
      const total = ls.reduce((a, l) => a + l.size, 0);
      const want = Math.max(...ls.map(l => l.text.length * l.size / total)) * hM * 0.46 + pad;
      return Math.max(Math.min(full, 1.6), Math.min(full, want));
    };
    const add = (kind, wM, hM, spec) => signs.push({ kind, wM: ['fascia', 'band', 'frieze', 'valance', 'upper'].includes(kind) ? fit(wM, hM, spec.lines) : wM, hM, ...spec });
    const lines = name ? [{ text: name, face, size: 1 }, ...(trade ? [{ text: trade, face: 'trade', size: 0.5 }] : [])]
      : [{ text: trade, face, size: 1 }];
    const number = fr.firm ? fr.firm.numbers.join(' & ') : null;
    // The main sign.
    const forms = ['fascia', 'fascia', 'fascia', 'band', 'band'];
    if (fr.storeys >= 3 && fr.w >= 8) forms.push('frieze', 'frieze');
    if (fr.bays >= 3) forms.push('glassmain');
    let main = forms[h0 % forms.length];
    if (main === 'band' && fr.storeys < 2) main = 'fascia';
    if (main === 'fascia') add('fascia', fr.w - 0.4, 0.61, { lines, board, number, framed: true });
    else if (main === 'band') add('band', fr.w - 0.6, Math.min(0.85, fr.bandH), { lines, board: BOARDS[(pick(BOARDS.length, 'band') + 3) % BOARDS.length], framed: true });
    else if (main === 'frieze') add('frieze', fr.w - 0.6, 0.46, { lines: [lines[0]], bare: BARE[pick(BARE.length, 'bare')] });
    else {
      add('fascia', fr.w - 0.4, 0.61, { lines: [{ text: trade || name, face, size: 1 }], board, framed: true });
      if (name) add('glass', Math.min(fr.bw - 0.5, 3.2), 0.5, { lines: [{ text: name, face: 'roman', size: 1 }], bare: BARE[0], arch: true });
    }
    if (tier.secondaries) {
      const s = h0 >>> 8;
      if (main !== 'frieze' && fr.storeys >= 2 && s % 10 < 3) {
        add('hanging', 1.15, 0.62, { lines: [{ text: (fr.firm && trade && trade.length < 22 ? trade : (name ?? trade)), face: FACE_KEYS[(pick(5, 'hang') + 2) % 5], size: 1 }],
          board: BOARDS[(pick(BOARDS.length, 'hang') + 5) % BOARDS.length], framed: true, at: (s >>> 4) % 2 });
      }
      if (fr.bays >= 3 && trade && s % 7 < 2) {
        add('pier', 0.28, 1.5, { lines: [{ text: trade.split(/[,&]/)[0].trim().slice(0, 16), face: 'condensed', size: 1 }],
          board: BOARDS[(pick(BOARDS.length, 'pier') + 1) % BOARDS.length], vertical: true, framed: true });
      }
      if (main !== 'glassmain' && name && fr.bays >= 2 && s % 5 < 2) {
        add('glass', Math.min(fr.bw - 0.5, 3), 0.42, { lines: [{ text: name.length > 22 ? trade : name, face: 'roman', size: 1 }], bare: BARE[0], arch: s % 2 === 0 });
      }
      if (fr.awning && s % 3 === 0) {
        add('valance', fr.w - 0.4, 0.22, { lines: [{ text: name ?? trade, face: 'condensed', size: 1 }], bare: BARE[(pick(4, 'val') % 2) + 1] });
      }
    }
    if (fr.upper && fr.storeys >= 3) {
      add('upper', Math.min(fr.w - 0.8, 9), Math.min(0.7, fr.upperH), { lines: [{ text: fr.upper.name.toUpperCase(), face: FACE_KEYS[(pick(5, 'up') + 1) % 5], size: 1 },
        ...(fr.upper.trade ? [{ text: tradeWords(fr.upper.trade), face: 'trade', size: 0.55 }] : [])],
        board: BOARDS[[4, 5, 6, 0][pick(4, 'upb')]], framed: true });
      census.upstairs++;
    }
    census.signs += signs.length;
    plans.set(fr.r.id, { firm: fr.firm ?? null, upper: fr.upper ?? null, trade, face: fr.face?.id ?? null, signs, focus: fr.focus });
  }
  return { plans, census };
}

// ---------------------------------------------------------------------------
// Painting.

function fontOf(f, px) { return `${f.style ?? 'normal'} ${f.weight} ${Math.max(4, Math.round(px))}px ${f.family}`; }

function textWidth(ctx, f, px, text) {
  ctx.font = fontOf(f, px);
  return ctx.measureText(text).width * f.scaleX + Math.max(0, text.length - 1) * f.track * px;
}

function giltGradient(ctx, y0, y1) {
  const g = ctx.createLinearGradient(0, y0, 0, y1);
  g.addColorStop(0, '#f6e3a0'); g.addColorStop(0.35, '#d9ac4c'); g.addColorStop(0.55, '#a8761f');
  g.addColorStop(0.8, '#e2b95a'); g.addColorStop(1, '#8a5e18');
  return g;
}

function drawLine(ctx, f, px, text, cx, base, maxW, letter, shade, inline) {
  let size = px;
  let w = textWidth(ctx, f, size, text);
  if (w > maxW) { size *= maxW / w; w = maxW; }
  ctx.font = fontOf(f, size);
  ctx.textBaseline = 'alphabetic';
  const sx = Math.min(f.scaleX, f.scaleX * (maxW / Math.max(1, w)));
  const draw = (dx, dy, fill) => {
    ctx.save();
    ctx.translate(cx - w / 2 + dx, base + dy);
    ctx.scale(sx, 1);
    ctx.fillStyle = fill;
    let x = 0;
    for (const ch of text) {
      ctx.fillText(ch, x, 0);
      x += (ctx.measureText(ch).width + f.track * size / f.scaleX);
    }
    ctx.restore();
  };
  if (shade) draw(size * 0.06, size * 0.05, shade);
  draw(0, 0, letter === 'gilt' ? giltGradient(ctx, base - size * 0.8, base) : letter);
  if (inline) {
    // The Tuscan's inline: a thin light stroke through the letters' middle.
    ctx.save();
    ctx.globalCompositeOperation = 'source-atop';
    ctx.fillStyle = letter === 'gilt' ? 'rgba(255,248,220,.75)' : 'rgba(255,255,255,.55)';
    ctx.fillRect(cx - w / 2, base - size * 0.42, w, Math.max(1, size * 0.07));
    ctx.restore();
  }
}

function paintSign(ctx, s, x, y, w, h) {
  ctx.save();
  ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  const bare = !!s.bare;
  const letter = bare ? s.bare.letter : s.board.letter;
  const shade = bare ? s.bare.shade : s.board.shade;
  if (!bare) {
    ctx.fillStyle = s.board.ground; ctx.fillRect(x, y, w, h);
    if (s.framed) {
      const m = Math.max(1, Math.min(w, h) * 0.07);
      ctx.strokeStyle = letter === 'gilt' ? '#b88a2e' : shade ?? letter;
      ctx.globalAlpha = 0.75; ctx.lineWidth = Math.max(1, m * 0.35);
      ctx.strokeRect(x + m, y + m, w - 2 * m, h - 2 * m);
      ctx.globalAlpha = 1;
    }
  }
  const pad = Math.min(w, h) * (bare ? 0.05 : 0.16);
  if (s.vertical) {
    // A pier board: the trade reads up the board.
    ctx.translate(x + w / 2, y + h / 2); ctx.rotate(-Math.PI / 2);
    const L = s.lines[0], f = FACES[L.face] ?? FACES.condensed;
    drawLine(ctx, f, w * 0.72, L.text, 0, w * 0.27, h - pad * 2, letter, shade, f.inline);
    ctx.restore();
    return;
  }
  const total = s.lines.reduce((a, l) => a + l.size, 0);
  const innerH = h - pad * 2;
  let yy = y + pad;
  for (const L of s.lines) {
    const f = L.face === 'trade' ? (s.lines[0].face === 'roman' ? ITALIC_FACE : TRADE_FACE) : FACES[L.face] ?? FACES.roman;
    const lh = innerH * L.size / total;
    const px = lh * (f === FACES.condensed ? 0.95 : 0.82);
    const base = yy + lh * 0.5 + px * 0.36;
    if (s.arch && L === s.lines[0]) {
      // Gilt letters set on an arc across the glass.
      let tw = textWidth(ctx, f, px, L.text);
      const size = px * Math.min(1, (w - pad * 2) / tw);
      tw = textWidth(ctx, f, size, L.text);
      const R = tw * 1.2;
      ctx.font = fontOf(f, size);
      let arc = -tw / 2;
      for (const ch of L.text) {
        const cw = ctx.measureText(ch).width * f.scaleX + f.track * size;
        ctx.save();
        ctx.translate(x + w / 2, base + R - size * 0.15);
        ctx.rotate((arc + cw / 2) / R);
        ctx.translate(0, -R);
        ctx.scale(f.scaleX, 1);
        if (shade) { ctx.fillStyle = shade; ctx.fillText(ch, -cw / 2 / f.scaleX + size * 0.05, size * 0.04); }
        ctx.fillStyle = letter === 'gilt' ? giltGradient(ctx, -size * 0.8, 0) : letter;
        ctx.fillText(ch, -cw / 2 / f.scaleX, 0);
        ctx.restore();
        arc += cw;
      }
    } else {
      drawLine(ctx, f, px, L.text, x + w / 2, base, w - pad * 2 - (s.number ? h * 1.1 : 0), letter, shade, f.inline);
    }
    yy += lh;
  }
  if (s.number) {
    // The street number at each end of the board, as the Lake Street boards carry it.
    const f = FACES.roman, px = h * 0.3;
    for (const cx of [x + h * 0.55, x + w - h * 0.55]) drawLine(ctx, f, px, s.number, cx, y + h * 0.62, h * 0.95, letter, null, false);
  }
  ctx.restore();
}

/**
 * Pack and paint every planned sign. Cells are packed in turn so a cell's signs share
 * a page (one draw a cell); the density is scaled down until all fit the tier.
 * Writes each sign's `uv` [u0, vTop, u1, vBottom] and `page`.
 */
export async function paintSigns(plans, cellOf, detail, problems = []) {
  const tier = TIER[detail] ?? TIER.full;
  await loadFonts(problems);
  const cells = new Map();
  for (const [rowId, plan] of plans) {
    const key = cellOf(rowId);
    if (!cells.has(key)) cells.set(key, []);
    for (const s of plan.signs) cells.get(key).push({ s, focus: plan.focus });
  }
  const order = [...cells.keys()].sort();
  let density = tier.density;
  let placed;
  for (let tries = 0; tries < 12; tries++) {
    placed = pack(order, cells, tier, density);
    if (placed) break;
    density *= 0.86;
  }
  if (!placed) { problems.push('1871 shop signs: the signs did not fit the atlas'); return { pages: [], density: 0 }; }
  const pages = [];
  for (let p = 0; p < placed.pages; p++) {
    const canvas = document.createElement('canvas');
    canvas.width = tier.w; canvas.height = tier.h;
    pages.push(canvas);
  }
  const ctxs = pages.map(c => c.getContext('2d'));
  for (const it of placed.items) {
    paintSign(ctxs[it.page], it.s, it.x, it.y, it.w, it.h);
    // Inset half a texel so mips never bleed a neighbour in.
    it.s.page = it.page;
    it.s.uv = [(it.x + 0.5) / tier.w, 1 - (it.y + 0.5) / tier.h, (it.x + it.w - 0.5) / tier.w, 1 - (it.y + it.h - 0.5) / tier.h];
  }
  const textures = pages.map(canvas => {
    const t = new THREE.CanvasTexture(canvas);
    t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; t.generateMipmaps = true;
    t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter;
    t.needsUpdate = true;
    return t;
  });
  return { textures, density: Math.round(density), pages: pages.length, bytes: pages.length * tier.w * tier.h * 4 * 4 / 3 };
}

function pack(order, cells, tier, density) {
  const items = [];
  let page = 0, x = 0, y = 0, row = 0;
  const gap = 4;
  for (const key of order) {
    const list = cells.get(key).map(({ s, focus }) => {
      // The stops themselves get the sharpest lettering.
      const d = density * (focus ? 1.25 : 0.7) * (s.kind === 'pier' || s.kind === 'hanging' ? 0.9 : 1);
      const w = Math.max(8, Math.round(s.wM * d)), h = Math.max(6, Math.round(s.hM * d));
      return { s, w: Math.min(w, tier.w - gap), h };
    }).sort((a, b) => b.h - a.h);
    const area = list.reduce((a, it) => a + (it.w + gap) * (it.h + gap), 0);
    // A cell starts a fresh page when it plainly will not fit what is left of this one.
    const left = (tier.h - y - row) * tier.w + (tier.w - x) * row;
    if (area > left && (x > 0 || y > 0) && area < tier.w * tier.h * 0.9) { page++; x = 0; y = 0; row = 0; }
    for (const it of list) {
      if (x + it.w > tier.w) { x = 0; y += row + gap; row = 0; }
      if (y + it.h > tier.h) { page++; x = 0; y = 0; row = 0; }
      if (page >= tier.pages) return null;
      items.push({ ...it, page, x, y });
      x += it.w + gap; row = Math.max(row, it.h);
    }
  }
  return { items, pages: page + 1 };
}
