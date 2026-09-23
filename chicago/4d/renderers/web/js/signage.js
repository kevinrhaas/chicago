/**
 * signage.js — the signs the town's businesses put out, and what each one says.
 *
 * WHY THIS FILE EXISTS. `docs/ROADMAP.md` K5 (b) asked for signboards on the
 * businesses. T-0039 built the layer: a plank on a bracket, hung off a wall this
 * project had already drawn, on every frontage a rule selected. Every one of
 * those boards was BLANK and every one hung the same way, because L25 and L130
 * read the absence of a recorded WORDING as a reason to paint nothing at all.
 *
 * T-0066 OVERRULES THAT, on the owner's instruction of 2026-08-18: *"you can and
 * should put the name of the location on the sign board. the sign boards should
 * have variation in color and style and signage font and color, some signs may
 * hang from an awning and others may be on the building or painted on the face
 * of the building. you need to add more signage and be period correct and it is
 * fine if they are reconstructions."* So this file now draws
 *
 *  * the NAME on every sign — `sign_text` on the record, which is the same name
 *    the card behind the sign shows, so a visitor who reads a board and then
 *    taps it is not shown two different businesses;
 *  * five MOUNTINGS — `bracket_board`, `awning_board`, `wall_board`,
 *    `post_board` and `facade_painted`, the last of which is not a board at all
 *    but the name straight onto the boards of the building (image 5 of the
 *    owner's brief shows a whole row of painted fronts at the Tremont);
 *  * and a per-sign STYLE — ground colour, letter colour, letterform and panel,
 *    assigned by the generator so that no two signs within 40 m match.
 *
 * T-0130 RE-WORDED ALL OF IT AND THIS FILE LETTERS THE HIERARCHY. A board no
 * longer carries the record's `name` — that is OUR label for a BUILDING, and a
 * signboard carries what the trade lettered. The record now hands over
 * `sign_lines`, each with a ROLE, and the advertisements' own register is drawn
 * from it: the proprietor or firm FIRST AND LARGEST, the trade beneath it, the
 * place last and smallest ("PHILO CARPENTER / Wholesale & Retail Druggist /
 * South Water Street"). Line sizes are relative (`ROLE_WEIGHT`) and the whole
 * block is then fitted to the board, so a long trade line shrinks the type
 * rather than breaking the hierarchy.
 *
 * The record owns all of it. `tools/generate_business_signboards.py` does the
 * choosing and the arithmetic, `tools/check.sh` re-derives its record byte for
 * byte, and this file only draws what that record says.
 *
 * HOW A NAME GETS ONTO A PLANK, in a project with no build step and no font
 * pipeline. The same way the Green Tree's post board got one in T-0082: a
 * CANVAS drawn at load and handed to three as a texture. What is new here is
 * that there are thirty-three of them in ten different colourways, and a layer
 * that is ONE DRAW CALL cannot have thirty-three textures. So the layer paints
 * ONE ATLAS — a grid of cells, one per sign plus one of plain weathered timber —
 * and every triangle it emits carries a `uv` into that atlas. A bracket arm
 * samples the timber cell; a board's face samples its own painted cell; the
 * name is IN the cell, so the lettering costs no triangles at all and the layer
 * is still a single mesh with a single material.
 *
 * WHAT IT WILL AND WILL NOT DO.
 *
 *  * A sign fixed to a building hangs on the same datum as the wall. Its height
 *    is measured from the base of the building's walls, and `buildings.js` puts
 *    that base at the LOWEST terrain sample under the footprint — so this
 *    samples the same 5×5 grid over the same quad. Any other rule and a board on
 *    sloping ground would float off its own wall. A POST is not on the building:
 *    it stands in the street, so it is measured from the ground under itself.
 *    The record says which datum each sign uses (`height_datum`).
 *  * It draws ONE trade device, and only where the shop's own advertisement
 *    names one. Exactly one does: Philo Carpenter's 1835 notice heads itself
 *    "AT THE SIGN OF THE GOLDEN MORTAR", which is a Chicago signboard described
 *    by the man who owned it, so the mortar is PAINTED on his board rather than
 *    the phrase being lettered. That is the opposite case to L25, which stands
 *    untouched: L25 withholds the Wolf Point wolf because that IMAGE was never
 *    described. Every other board is lettering only, and the record decides —
 *    this file draws `sign_device` when it is there and nothing when it is not.
 *  * It is ONE draw call for the whole layer, like the fences.
 *  * It marks itself. Every vertex carries `_confidence` at `reconstructed`,
 *    because the FACT of a sign on these frontages is reconstructed — the
 *    weakest thing deciding that the vertex exists at all — and so, now, are its
 *    wording, its colours and its mounting. So the whole layer disappears when a
 *    visitor hides `reconstructed`, and the town goes back to being mute. That
 *    is the truthful behaviour.
 *  * It answers a pick. A sign belongs to a business with a card behind it, so
 *    clicking it opens the shop — which is what a sign is FOR.
 */

import * as THREE from 'three';

/** attested · inferred · reconstructed, as the confidence view reads them. */
const LEVEL = { attested: 0, documented: 0, inferred: 0.5, reconstructed: 1 };

/**
 * HOW A SIGN IS DRAWN rather than what any shop claimed. The record carries the
 * board's own size, its mounting and the mounting's principal dimensions; these
 * are the small timber that hangs it — strap thickness, the strut under a
 * bracket, the cap over a wall board — the division `enclosures.js` makes
 * between a fence's line (the record's) and a rail's thickness (the renderer's).
 * The bracket numbers are still `generators/archetypes/log_dwelling.py::_sign`'s,
 * the wolf sign's own geometry, so the town has one convention for hanging a
 * board rather than two.
 */
const ARM_T_M = 0.045;
const HANGER_T_M = 0.022;
const HANGER_W_M = 0.018;
const AWNING_T_M = 0.05;
const AWNING_BRACKET_T_M = 0.05;
const WALL_CAP_T_M = 0.05;
const POST_ARM_T_M = 0.09;

/**
 * The weathered plank every bracket, post, hood and strap is made of. The
 * archetype's own `SIGN_RGBA`, converted rather than copied: the generator
 * writes glTF `baseColorFactor`, which is LINEAR, at (0.60, 0.54, 0.44), and
 * `THREE.Color.setHex` reads sRGB with `ColorManagement.enabled` on, so the hex
 * that lands on the same linear triple is this one. Copying 0x998a70 straight
 * across would hang a board two stops darker than the wolf sign beside it — the
 * same trap called out in `trees.js`. It is now a colour in the ATLAS rather
 * than the material's own, because the material's colour has to be white for
 * every painted cell to come through unchanged.
 */
const TIMBER_HEX = '#cbc2b1';

/* -------------------------------------------------------------------------- */
/* the atlas                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * ONE CELL PER SIGN, and the size is arithmetic rather than taste. A board 1.1 m
 * wide read from the 3.5 m the release gate stands at fills about 380 px of a
 * 1280-wide viewport, so 512 px of texture across a board is the right order —
 * more is wasted and less is a blurred name. A painted band 4 m wide read from
 * 8 m wants twice that, so a cell wide enough to need it takes two columns.
 */
const TILE_W = 512;
const TILE_H = 256;
const ATLAS_COLS = 8;
const CELL_PAD = 10;
const WIDE_ASPECT = 3.4;   // above this a sign takes two columns

/**
 * The four letterforms, as a canvas can carry them. A browser has no 1830s
 * specimen book in it, so these approximate the period's four working faces with
 * family, weight, horizontal scale and letter-spacing: the SIGNWRITER's roman
 * (a serif, generously spaced, with the drop shade a shop board almost always
 * had), the FAT FACE that is the 1830s display letter (the same serif at its
 * heaviest, widened), the EGYPTIAN slab that arrives beside it (a monospaced
 * slab-serif is the nearest thing a browser ships), and the plain BLOCK letter.
 * The letterform is invented — docs/LIBERTIES.md L158 says so — and what it has
 * to do is be legible from the footway and not be the same on two neighbouring
 * boards.
 */
const FACES = {
  signwriter: {
    family: 'Georgia, "Times New Roman", Times, serif',
    weight: 600, scaleX: 1.0, track: 0.07, shade: true,
  },
  fat_face: {
    family: 'Georgia, "Times New Roman", Times, serif',
    weight: 900, scaleX: 1.24, track: 0.0, shade: false,
  },
  egyptian: {
    family: '"Courier New", Courier, monospace',
    weight: 700, scaleX: 1.06, track: 0.02, shade: false,
  },
  grotesque: {
    family: 'Helvetica, Arial, "Liberation Sans", sans-serif',
    weight: 800, scaleX: 0.88, track: 0.12, shade: false,
  },
};

/** #rrggbb to [r,g,b] 0-255. */
function hexRGB(hex) {
  const h = String(hex || '#000000').replace('#', '');
  return [
    parseInt(h.slice(0, 2), 16) || 0,
    parseInt(h.slice(2, 4), 16) || 0,
    parseInt(h.slice(4, 6), 16) || 0,
  ];
}

/** The same colour lifted or dropped a little — the oval field's second tone. */
function shift(hex, by) {
  const [r, g, b] = hexRGB(hex);
  const f = (v) => Math.max(0, Math.min(255, Math.round(v + by)));
  return `rgb(${f(r)}, ${f(g)}, ${f(b)})`;
}

/** Is this ground dark? Decides which way the oval field and the shade move. */
function isDark(hex) {
  const [r, g, b] = hexRGB(hex);
  return (0.299 * r + 0.587 * g + 0.114 * b) < 128;
}

/** The width one line takes at a size, tracking and horizontal scale included. */
function lineWidth(ctx, str, size, face) {
  ctx.font = `${face.weight} ${size}px ${face.family}`;
  let w = 0;
  for (const ch of str) w += ctx.measureText(ch).width;
  if (str.length > 1) w += face.track * size * (str.length - 1);
  return w * face.scaleX;
}

/**
 * THE PERIOD'S OWN HIERARCHY, as a ratio of type sizes. Both advertisements the
 * wording came off put the proprietor on the top line in the largest letter, the
 * trade beneath it in a second face, and the place last and smallest — so a
 * board that set all three the same size would carry the right words in the
 * wrong voice. The numbers are a signwriter's ordinary step and are invented;
 * what is not invented is the ORDER, which is the advertisements'.
 */
const ROLE_WEIGHT = { name: 1.0, trade: 0.60, place: 0.44 };

/**
 * The wording broken into `n` lines, balanced by length. A shop board carried
 * two or three lines far more often than one, and a trade line the period wrote
 * out in full ("Storage, Forwarding & Commission Merchants") has to break
 * somewhere or take the whole board down with it.
 */
function splitInto(words, n) {
  if (n === 1) return [words.join(' ')];
  if (words.length < n) return null;
  const target = words.join(' ').length / n;
  const lines = [];
  let cur = [];
  for (let i = 0; i < words.length; i += 1) {
    cur.push(words[i]);
    const left = words.length - i - 1;
    const want = n - lines.length - 1;
    if (want > 0 && (cur.join(' ').length >= target || left <= want) && left >= want) {
      lines.push(cur.join(' '));
      cur = [];
    }
  }
  if (cur.length) lines.push(cur.join(' '));
  return lines.length === n ? lines : null;
}

/** One line drawn centred, letter by letter so the tracking is real. */
function drawTracked(ctx, str, cx, cy, size, face) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.scale(face.scaleX, 1);
  ctx.font = `${face.weight} ${size}px ${face.family}`;
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';
  const tr = face.track * size;
  let w = 0;
  for (const ch of str) w += ctx.measureText(ch).width;
  if (str.length > 1) w += tr * (str.length - 1);
  let x = -w / 2;
  for (const ch of str) {
    ctx.fillText(ch, x, 0);
    x += ctx.measureText(ch).width + tr;
  }
  ctx.restore();
}

/**
 * THE GOLDEN MORTAR — the one painted device in this town, and the only image on
 * any board but the wolf. A mortar and pestle: a tapering bowl on a foot, a
 * flared rim, and the pestle standing out of it to the right. Gilt fill with a
 * darker shade under it, which is how a gilder worked a device on a board and is
 * also what keeps it legible on either a dark or a light ground.
 *
 * `s` is the device's height in pixels; (cx, cy) its centre. Nothing here is a
 * record's — the record says a golden mortar was on the board, not how it was
 * drawn — so the outline is deliberately plain: no ornament, no ground line.
 */
function drawDevice(ctx, cx, cy, s, gold, shade) {
  const r = s * 0.34;              // bowl half-width at the rim
  const foot = cy + s * 0.44;
  const rim = cy - s * 0.06;
  ctx.save();
  ctx.lineJoin = 'round';
  // The pestle first, so the bowl's rim crosses in front of it.
  ctx.save();
  ctx.translate(cx + r * 0.42, rim - s * 0.06);
  ctx.rotate(-0.42);
  ctx.fillStyle = shade;
  ctx.fillRect(-s * 0.075, -s * 0.52, s * 0.15, s * 0.62);
  ctx.fillStyle = gold;
  ctx.fillRect(-s * 0.055, -s * 0.50, s * 0.11, s * 0.58);
  ctx.beginPath();
  ctx.ellipse(0, -s * 0.48, s * 0.105, s * 0.095, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
  // The bowl: rim band, tapering body, and a foot under it.
  ctx.fillStyle = gold;
  ctx.strokeStyle = shade;
  ctx.lineWidth = Math.max(1.5, s * 0.035);
  ctx.beginPath();
  ctx.moveTo(cx - r, rim);
  ctx.lineTo(cx + r, rim);
  ctx.lineTo(cx + r * 0.80, rim + s * 0.13);
  ctx.lineTo(cx + r * 0.42, foot - s * 0.10);
  ctx.lineTo(cx - r * 0.42, foot - s * 0.10);
  ctx.lineTo(cx - r * 0.80, rim + s * 0.13);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.beginPath();
  ctx.rect(cx - r * 0.62, foot - s * 0.11, r * 1.24, s * 0.11);
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

/**
 * One sign's cell: its ground, its panel, its device where it has one, and its
 * wording in the register the record hands over — fitted to the shape of the
 * actual sign so the letters are not stretched when the quad samples it.
 * Returns the sub-rectangle, in pixels, that the sign's face maps to.
 */
function paintCell(ctx, x, y, cellW, sign) {
  const style = sign.style || {};
  const ground = style.ground || TIMBER_HEX;
  const letter = style.letter || '#241a10';
  const face = FACES[style.face] || FACES.signwriter;
  ctx.fillStyle = ground;
  ctx.fillRect(x, y, cellW, TILE_H);

  const cx0 = x + CELL_PAD;
  const cy0 = y + CELL_PAD;
  const cw = cellW - 2 * CELL_PAD;
  const ch = TILE_H - 2 * CELL_PAD;
  const want = Math.max(0.6, (sign.board_w_m || 1) / (sign.board_h_m || 0.5));
  let rw = cw;
  let rh = cw / want;
  if (rh > ch) { rh = ch; rw = ch * want; }
  const rx = cx0 + (cw - rw) / 2;
  const ry = cy0 + (ch - rh) / 2;

  // The panel — a rule, two rules, or an oval field. The cheapest board had
  // none; most had one; a gilt board on green very often had an oval.
  const rule = Math.max(2, rh * 0.026);
  ctx.strokeStyle = letter;
  ctx.lineWidth = rule;
  if (style.panel === 'single_rule') {
    ctx.strokeRect(rx + rh * 0.06, ry + rh * 0.06, rw - rh * 0.12, rh - rh * 0.12);
  } else if (style.panel === 'double_rule') {
    ctx.strokeRect(rx + rh * 0.05, ry + rh * 0.05, rw - rh * 0.10, rh - rh * 0.10);
    ctx.lineWidth = Math.max(1, rule * 0.5);
    ctx.strokeRect(rx + rh * 0.12, ry + rh * 0.12, rw - rh * 0.24, rh - rh * 0.24);
  } else if (style.panel === 'oval') {
    ctx.fillStyle = shift(ground, isDark(ground) ? 16 : -16);
    ctx.beginPath();
    ctx.ellipse(rx + rw / 2, ry + rh / 2, rw / 2 - rh * 0.03, rh / 2 - rh * 0.03,
      0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }

  // THE DEVICE takes the left-hand end of the face and the lettering takes the
  // rest. The record says how much (`share`), because a board's proportions are
  // the record's business; where there is no device the lettering has it all.
  const dev = sign.sign_device || null;
  const devShare = dev ? Math.min(0.45, Math.max(0.1, dev.share ?? 0.3)) : 0;
  const tx = rx + rw * devShare;
  const tw = rw * (1 - devShare);
  if (dev) {
    const s = Math.min(rh * 0.80, rw * devShare * 0.92);
    drawDevice(ctx, rx + (rw * devShare) / 2, ry + rh / 2, s,
      dev.colour || '#d9b036', dev.shade || '#7a5c14');
  }

  // THE WORDING, in the record's own hierarchy. Each line carries a role and a
  // role carries a relative size, so the proprietor reads largest and the place
  // smallest whatever the board turns out to be. A `trade` or `place` line that
  // is long may take TWO rows rather than dragging the whole block down with it,
  // which is why the arrangements are enumerated instead of one being assumed.
  const given = Array.isArray(sign.sign_lines) && sign.sign_lines.length
    ? sign.sign_lines
    : [{ text: String(sign.sign_text || ''), role: 'name' }];
  const src = given
    .map((l) => ({
      words: String(l.text || '').toUpperCase().split(/\s+/).filter(Boolean),
      w: ROLE_WEIGHT[l.role] ?? 1.0,
    }))
    .filter((l) => l.words.length);
  // Every arrangement: each line takes one row, or two where it has the words
  // for it and is not the name (a firm's name stays on its own line — that is
  // the register). At most three source lines, so at most four arrangements.
  const options = [[]];
  for (let i = 0; i < src.length; i += 1) {
    const l = src[i];
    const splits = (l.w < 1.0 && l.words.length >= 3) ? [1, 2] : [1];
    const next = [];
    for (const opt of options) {
      for (const n of splits) {
        const rows = splitInto(l.words, n);
        if (!rows) continue;
        next.push(opt.concat(rows.map((t) => ({ text: t, w: l.w }))));
      }
    }
    options.length = 0;
    options.push(...next);
  }
  const maxW = tw * 0.88;
  const maxH = rh * 0.80;
  let best = null;
  for (const rows of options) {
    if (!rows.length) continue;
    let lo = 4;
    let hi = Math.ceil(rh);
    while (lo < hi) {
      const mid = Math.ceil((lo + hi + 1) / 2);
      const blockH = rows.reduce((a, r) => a + mid * r.w * 1.20, 0);
      const fits = blockH <= maxH
        && rows.every((r) => lineWidth(ctx, r.text, mid * r.w, face) <= maxW);
      if (fits) lo = mid; else hi = mid - 1;
    }
    // Prefer the arrangement that lets the NAME be biggest; on a tie, fewer rows.
    if (!best || lo > best.size || (lo === best.size && rows.length < best.rows.length)) {
      best = { rows, size: lo };
    }
  }
  if (best && best.size >= 4) {
    const heights = best.rows.map((r) => best.size * r.w * 1.20);
    const blockH = heights.reduce((a, b) => a + b, 0);
    const cxText = tx + tw / 2;
    let ly = ry + rh / 2 - blockH / 2;
    for (let i = 0; i < best.rows.length; i += 1) {
      const size = best.size * best.rows[i].w;
      const mid = ly + heights[i] / 2;
      if (face.shade) {
        ctx.fillStyle = isDark(ground) ? 'rgba(0,0,0,0.55)' : 'rgba(0,0,0,0.30)';
        drawTracked(ctx, best.rows[i].text, cxText + size * 0.05, mid + size * 0.06,
          size, face);
      }
      ctx.fillStyle = letter;
      drawTracked(ctx, best.rows[i].text, cxText, mid, size, face);
      ly += heights[i];
    }
  }
  return { rx, ry, rw, rh };
}

/**
 * Lay every sign out on one canvas and hand back the texture plus, for each
 * sign, the uv rectangle its face samples and the uv point its edges take.
 *
 * `null` when there is no document to draw on (a headless parse of this module,
 * or a browser that refuses a 2d context) — the caller then draws plain timber,
 * which is the layer as T-0039 shipped it and is a degradation rather than a
 * failure.
 */
function buildAtlas(signs) {
  if (typeof document === 'undefined') return null;
  const canvas = document.createElement('canvas');
  const cells = [];
  // Cell 0 is plain timber, for every bracket, post, hood and strap in the town.
  let col = 1;
  let row = 0;
  // WIDE CELLS FIRST, and it is packing rather than taste: a two-column cell
  // that will not fit at the end of a row leaves both of those columns empty,
  // and thirteen painted bands laid out in record order cost a whole extra row
  // of a four-megapixel canvas that way. Sorted, the town's signs pack into the
  // area they actually need. `sort` is stable and the record is already in a
  // fixed order, so the layout is as re-derivable as everything else here.
  const order = signs.map((sign, i) => {
    const aspect = Math.max(0.6, (sign.board_w_m || 1) / (sign.board_h_m || 0.5));
    return { sign, i, span: aspect >= WIDE_ASPECT ? 2 : 1 };
  }).sort((a, b) => (b.span - a.span) || (a.i - b.i));
  for (const { sign, span } of order) {
    if (col + span > ATLAS_COLS) { col = 0; row += 1; }
    cells.push({ sign, col, row, span });
    col += span;
  }
  const rows = row + 1;
  canvas.width = ATLAS_COLS * TILE_W;
  canvas.height = rows * TILE_H;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  ctx.fillStyle = TIMBER_HEX;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const W = canvas.width;
  const H = canvas.height;
  const uvOf = (px, py) => [px / W, 1 - py / H];
  const out = { timber: uvOf(TILE_W * 0.5, TILE_H * 0.5), signs: new Map() };
  for (const cell of cells) {
    const x = cell.col * TILE_W;
    const y = cell.row * TILE_H;
    const cellW = cell.span * TILE_W;
    const r = paintCell(ctx, x, y, cellW, cell.sign);
    out.signs.set(cell.sign.structure_id, {
      // The face's rectangle, as (u0, v0) bottom-left to (u1, v1) top-right.
      rect: [r.rx / W, 1 - (r.ry + r.rh) / H, (r.rx + r.rw) / W, 1 - r.ry / H],
      // A point of pure ground colour for the board's four edges, kept well
      // inside the cell so no mip level pulls a neighbour's colour into it.
      solid: uvOf(x + 4, y + 4),
    });
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  texture.needsUpdate = true;
  out.texture = texture;
  out.cells = cells.length;
  out.size = [canvas.width, canvas.height];
  return out;
}

/* -------------------------------------------------------------------------- */
/* the timber                                                                  */
/* -------------------------------------------------------------------------- */

/** (a, b, c) in {-1,1} for each of a box's eight corners, in the face order below. */
const CORNER = [
  [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
  [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],
];
const FACE_TRIS = [
  ['a+', [[1, 5, 6], [1, 6, 2]]],
  ['a-', [[4, 0, 3], [4, 3, 7]]],
  ['b+', [[3, 2, 6], [3, 6, 7]]],
  ['b-', [[0, 4, 5], [0, 5, 1]]],
  ['c+', [[4, 7, 6], [4, 6, 5]]],
  ['c-', [[0, 1, 2], [0, 2, 3]]],
];

/**
 * A solid from eight corners, flat-shaded from its own face normals, every
 * vertex carrying a uv. `uvFor(faceId, cornerIndex)` answers the uv; the default
 * is one point of plain timber, which is what everything but a painted face
 * wants. Deliberately the same shape of helper as the enclosure and frontage
 * layers' — several layers drawing small timber the same way is one thing to
 * reason about, not several.
 *
 * AND IT ORIENTS ITSELF, which the box helpers those layers use do not have to.
 * `FACE_TRIS` fixes a winding in the (a, b, c) corner lattice, so whether a face
 * comes out front- or back-facing depends on the HANDEDNESS of the three axes
 * the caller built its corners on — and this layer has callers on both. The box
 * helper's `b` axis runs INTO the wall; the awning hood's runs OUT of it, and
 * the post's knee brace is a third arrangement again. Rather than make every
 * caller get a sign right, each face is tested against the solid's own centre
 * and flipped — normal and winding together — if it came out facing inward. Two
 * of the five mountings were relying on `side: DoubleSide` and three's
 * back-face normal flip to cancel the error out, which is a coincidence to
 * depend on rather than a rule.
 */
function pushHull(buf, p, level, uvFor) {
  const mid = [0, 0, 0];
  for (const q of p) { mid[0] += q[0] / 8; mid[1] += q[1] / 8; mid[2] += q[2] / 8; }
  for (const [id, tris] of FACE_TRIS) {
    const [i0, i1, i2] = tris[0];
    const ax = p[i1][0] - p[i0][0];
    const ay = p[i1][1] - p[i0][1];
    const az = p[i1][2] - p[i0][2];
    const bx = p[i2][0] - p[i0][0];
    const by = p[i2][1] - p[i0][1];
    const bz = p[i2][2] - p[i0][2];
    let nx = ay * bz - az * by;
    let ny = az * bx - ax * bz;
    let nz = ax * by - ay * bx;
    const len = Math.hypot(nx, ny, nz) || 1;
    nx /= len; ny /= len; nz /= len;
    // Outward is away from the solid's own centre.
    const out = nx * (p[i0][0] - mid[0]) + ny * (p[i0][1] - mid[1])
      + nz * (p[i0][2] - mid[2]);
    const flip = out < 0;
    if (flip) { nx = -nx; ny = -ny; nz = -nz; }
    for (const tri of tris) {
      for (const i of (flip ? [tri[0], tri[2], tri[1]] : tri)) {
        buf.pos.push(p[i][0], p[i][1], p[i][2]);
        buf.nrm.push(nx, ny, nz);
        const uv = uvFor(id, i);
        buf.uv.push(uv[0], uv[1]);
        buf.conf.push(level);
      }
    }
  }
}

/** An axis-aligned-in-its-own-frame box: `u` along its length, world Y up. */
function boxCorners(cx, cy, cz, ux, uz, halfLen, halfW, halfH) {
  const vx = -uz;
  const vz = ux;
  return CORNER.map(([a, b, c]) => [
    cx + ux * a * halfLen + vx * b * halfW,
    cy + c * halfH,
    cz + uz * a * halfLen + vz * b * halfW,
  ]);
}

function pushBox(buf, cx, cy, cz, ux, uz, halfLen, halfW, halfH, level, solid) {
  pushHull(buf, boxCorners(cx, cy, cz, ux, uz, halfLen, halfW, halfH), level,
    () => solid);
}

/**
 * A bar between two points that are not at the same height — the knee under an
 * awning hood and the brace under a post's arm. A box cannot do it: `pushBox`
 * runs its length along a HORIZONTAL unit vector, which is right for everything
 * else in this layer and wrong for the one member whose whole job is to be
 * diagonal. Sheared rather than rotated, which at 45 mm of section is a
 * distinction no eye on the footway can make.
 */
function pushBar(buf, a, b, wx, wz, halfW, halfT, level, solid) {
  const p = CORNER.map(([ca, cb, cc]) => {
    const t = (ca + 1) / 2;
    return [
      a[0] + t * (b[0] - a[0]) + wx * cb * halfW,
      a[1] + t * (b[1] - a[1]) + cc * halfT,
      a[2] + t * (b[2] - a[2]) + wz * cb * halfW,
    ];
  });
  pushHull(buf, p, level, () => solid);
}

/**
 * THE BOARD ITSELF, and the one piece of UV arithmetic worth explaining.
 *
 * A board is pushed with its length along the wall (`wx, wz`), so its "across"
 * axis is `(-wz, wx)`, which for a facade bearing `b` is exactly MINUS the
 * outward normal. The `b-` face is therefore the one that looks at the street
 * and the `b+` face is the one that looks at the wall.
 *
 * WHICH WAY THE NAME RUNS on each. A reader standing off the street face has the
 * board's along-wall axis on their LEFT, so the text runs along MINUS that axis
 * and the u coordinate is mirrored; from behind, it is the other way. Getting
 * this backwards draws a perfectly lit board with the name mirrored on both
 * sides, which is what the first build of the frontage layer's lettering did.
 */
function pushBoard(buf, cx, cy, cz, wx, wz, halfLen, halfT, halfH, level, art) {
  const [u0, v0, u1, v1] = art.rect;
  const uvFor = (id, i) => {
    const [a, , c] = CORNER[i];
    if (id === 'b-') return [u1 - ((a + 1) / 2) * (u1 - u0), v0 + ((c + 1) / 2) * (v1 - v0)];
    if (id === 'b+') return [u0 + ((a + 1) / 2) * (u1 - u0), v0 + ((c + 1) / 2) * (v1 - v0)];
    return art.solid;
  };
  pushHull(buf, boxCorners(cx, cy, cz, wx, wz, halfLen, halfT, halfH), level, uvFor);
}

/**
 * The name painted straight onto the boards of the building: one quad standing
 * `proud` of the wall, and nothing else. Two triangles for a whole sign, which
 * is why this mounting is the cheapest thing in the layer as well as the one the
 * Tremont street scene shows most of.
 */
function pushPaintedBand(buf, cx, cy, cz, wx, wz, ox, oz, halfLen, halfH, level, art) {
  const [u0, v0, u1, v1] = art.rect;
  const P = (s, t) => [cx + wx * s * halfLen, cy + t * halfH, cz + wz * s * halfLen];
  const quad = [P(1, -1), P(-1, -1), P(-1, 1), P(1, 1)];
  const uvs = [[u0, v0], [u1, v0], [u1, v1], [u0, v1]];
  for (const [i, j, k] of [[0, 1, 2], [0, 2, 3]]) {
    for (const idx of [i, j, k]) {
      buf.pos.push(quad[idx][0], quad[idx][1], quad[idx][2]);
      buf.nrm.push(ox, 0, oz);
      buf.uv.push(uvs[idx][0], uvs[idx][1]);
      buf.conf.push(level);
    }
  }
}

/**
 * The base of this building's walls, by the rule `buildings.js` uses: the LOWEST
 * of a 5×5 grid of terrain samples over the footprint. Bilinear over the quad
 * the record carries, which is the footprint's bounding box already turned into
 * local ENU, so nothing here re-does the placement arithmetic the generator did.
 */
function wallBase(quad, terrain) {
  if (!Array.isArray(quad) || quad.length !== 4) return null;
  const [a, b, c, d] = quad;
  let lowest = Infinity;
  const STEPS = 4;
  for (let i = 0; i <= STEPS; i += 1) {
    const s = i / STEPS;
    for (let j = 0; j <= STEPS; j += 1) {
      const t = j / STEPS;
      const e = (a[0] * (1 - s) + b[0] * s) * (1 - t) + (d[0] * (1 - s) + c[0] * s) * t;
      const n = (a[1] * (1 - s) + b[1] * s) * (1 - t) + (d[1] * (1 - s) + c[1] * s) * t;
      const y = terrain.surfaceHeight(e, n);
      if (Number.isFinite(y)) lowest = Math.min(lowest, y);
    }
  }
  return Number.isFinite(lowest) ? lowest : null;
}

/**
 * One sign, whichever way the record hangs it. Returns true if it drew.
 *
 * The frame, for anyone checking the arithmetic against docs/GLB-CONTRACT.md:
 * the record's `facade_bearing_deg` is a compass bearing, so the outward normal
 * is (sin b, cos b) in ENU and the along-wall direction is (cos b, −sin b). The
 * renderer's world is (E, up, −N), which is where every negated north below
 * comes from.
 */
function buildSign(buf, sign, terrain, art, timber, problems) {
  const anchor = sign.anchor_local_enu_m;
  if (!Array.isArray(anchor) || anchor.length !== 2) {
    problems.push(`signage: ${sign.structure_id} carries no anchor — no sign is put up`);
    return false;
  }
  const base = wallBase(sign.ground_quad_local_enu_m, terrain);
  if (base === null) {
    problems.push(`signage: ${sign.structure_id} has no ground under its footprint — `
      + 'no sign is put up');
    return false;
  }
  const level = LEVEL[sign.confidence] ?? 1;
  const b = ((sign.facade_bearing_deg ?? 0) * Math.PI) / 180;
  // Out of the wall, and along it. Both in the renderer's world axes.
  const ox = Math.sin(b);
  const oz = -Math.cos(b);
  const wx = Math.cos(b);
  const wz = Math.sin(b);
  const ax = anchor[0];
  const az = -anchor[1];
  const g = sign.geometry ?? {};
  const bw = sign.board_w_m ?? 0.88;
  const bh = sign.board_h_m ?? 0.50;
  const bt = sign.board_thickness_m ?? 0.05;
  /**
   * WHAT IS PAINTED AND WHAT IS NOT. The record's `style` is the BOARD's paint —
   * its ground, its letters, its panel — so the board's four edges take that
   * ground (`art.solid`) and everything that carries it does not. A bracket
   * arm, an awning hood, a post and a strap are the weathered plank the wolf
   * sign's own bracket is made of, and they sample the atlas's one timber cell.
   * Painting the ironmongery too would be this file inventing on top of a record
   * that already says what is invented.
   */
  const solid = timber;
  const y = base + (sign.arm_height_m ?? 2.55);

  switch (sign.mounting) {
    case 'awning_board': {
      // A HOOD OVER THE DOOR with the board hanging under its outer edge. The
      // hood is a sloped solid rather than a flat one — its outer edge falls,
      // which is what makes it read as an awning and not a shelf — so it is
      // built from eight explicit corners instead of a box.
      const proj = g.awning_projection_m ?? 1.45;
      const fall = g.awning_drop_m ?? 0.34;
      const aw = (g.awning_width_m ?? (bw + 0.9)) / 2;
      const hull = CORNER.map(([ca, cb, cc]) => {
        const outAt = cb < 0 ? 0 : proj;
        const yTop = (cb < 0 ? y : y - fall) + cc * (AWNING_T_M / 2);
        return [
          ax + wx * ca * aw + ox * outAt,
          yTop,
          az + wz * ca * aw + oz * outAt,
        ];
      });
      pushHull(buf, hull, level, () => solid);
      // Two knees carrying it: from the wall, well below the hood, out and up to
      // under its outer edge. Diagonal on purpose — a horizontal strut under a
      // hood reads as a second shelf rather than as the thing holding the first.
      for (const s of [-1, 1]) {
        const offX = wx * s * (aw - 0.10);
        const offZ = wz * s * (aw - 0.10);
        pushBar(buf,
          [ax + offX, y - 0.62, az + offZ],
          [ax + offX + ox * (proj - 0.10), y - fall - AWNING_T_M,
            az + offZ + oz * (proj - 0.10)],
          wx, wz, AWNING_BRACKET_T_M / 2, AWNING_BRACKET_T_M / 2, level, solid);
      }
      // Two straps and the board under the hood's outer edge.
      const drop = g.hanger_drop_m ?? 0.20;
      const hangOut = proj - 0.14;
      const boardY = y - fall - AWNING_T_M / 2 - drop - bh / 2;
      for (const s of [-1, 1]) {
        pushBox(buf,
          ax + ox * hangOut + wx * s * bw * 0.34,
          y - fall - drop / 2,
          az + oz * hangOut + wz * s * bw * 0.34,
          ox, oz, HANGER_T_M, HANGER_W_M, drop / 2, level, solid);
      }
      pushBoard(buf, ax + ox * hangOut, boardY, az + oz * hangOut,
        wx, wz, bw / 2, bt / 2, bh / 2, level, art);
      break;
    }
    case 'wall_board': {
      // FIXED FLAT ON THE FRONT, under a cap that throws the rain off it. The
      // cheapest way to put a name on a building that is not paint.
      const proud = g.proud_m ?? 0.02;
      const cy = y - bh / 2;
      pushBoard(buf, ax + ox * (proud + bt / 2), cy, az + oz * (proud + bt / 2),
        wx, wz, bw / 2, bt / 2, bh / 2, level, art);
      pushBox(buf,
        ax + ox * (proud + bt), y + WALL_CAP_T_M / 2, az + oz * (proud + bt),
        wx, wz, bw / 2 + 0.05, bt, WALL_CAP_T_M / 2, level, solid);
      break;
    }
    case 'post_board': {
      // A POLE AT THE STREET EDGE — the Green Tree's own arrangement (T-0082),
      // which is the one mounting the owner's reference views actually show. It
      // is NOT on the building, so it stands on the ground under ITSELF: a post
      // set to the wall's datum would sink or float wherever the footway falls
      // away from the wall, and this ground is not flat.
      const stand = g.stand_m ?? 1.90;
      const px = ax + ox * stand;
      const pz = az + oz * stand;
      const pg = terrain.surfaceHeight(px, -pz);
      const foot = Number.isFinite(pg) ? pg : base;
      const ph = g.post_height_m ?? 3.5;
      const sq = (g.post_square_m ?? 0.16) / 2;
      const arm = g.arm_m ?? 1.30;
      const drop = g.hanger_drop_m ?? 0.20;
      const armY = foot + ph - POST_ARM_T_M;
      pushBox(buf, px, foot + ph / 2, pz, wx, wz, sq, sq, ph / 2, level, solid);
      pushBox(buf, px + wx * (arm / 2), armY, pz + wz * (arm / 2), wx, wz,
        arm / 2, POST_ARM_T_M / 2, POST_ARM_T_M / 2, level, solid);
      pushBar(buf,
        [px, armY - 0.46, pz],
        [px + wx * 0.46, armY - POST_ARM_T_M / 2, pz + wz * 0.46],
        ox, oz, POST_ARM_T_M * 0.35, POST_ARM_T_M * 0.35, level, solid);
      const hang = arm * 0.55;
      for (const s of [-1, 1]) {
        pushBox(buf,
          px + wx * (hang + s * bw * 0.36), armY - drop / 2,
          pz + wz * (hang + s * bw * 0.36),
          ox, oz, HANGER_T_M, HANGER_W_M, drop / 2, level, solid);
      }
      pushBoard(buf, px + wx * hang, armY - drop - bh / 2, pz + wz * hang,
        wx, wz, bw / 2, bt / 2, bh / 2, level, art);
      break;
    }
    case 'facade_painted': {
      // THE NAME ON THE BUILDING ITSELF. Image 5 of the owner's brief — the
      // Tremont street scene — shows a row of fronts lettered straight onto the
      // boards, and a works or a warehouse announced its firm this way and hung
      // nothing at all over a footway nobody walked.
      const proud = g.proud_m ?? 0.03;
      pushPaintedBand(buf, ax + ox * proud, y - bh / 2, az + oz * proud,
        wx, wz, ox, oz, bw / 2, bh / 2, level, art);
      break;
    }
    default: {
      // THE BRACKET BOARD, unchanged since T-0039 but for its size and its
      // paint: the wolf sign's own arm, strut, straps and plank.
      const arm = g.arm_m ?? 1.15;
      const drop = g.hanger_drop_m ?? 0.20;
      pushBox(buf, ax + ox * (arm / 2), y + ARM_T_M, az + oz * (arm / 2),
        ox, oz, arm / 2, ARM_T_M, ARM_T_M, level, solid);
      // The strut under it, a shorter brace kept slim on purpose: an earlier
      // bracket in this project read as the object with a board attached rather
      // than the other way round. On a shop the board is the point.
      pushBox(buf, ax + ox * 0.30, y - 0.19, az + oz * 0.30,
        ox, oz, 0.30, ARM_T_M * 0.6, ARM_T_M * 0.6, level, solid);
      const hang = arm * 0.72;
      for (const s of [-1, 1]) {
        pushBox(buf,
          ax + ox * hang + wx * s * bw * 0.32,
          y - drop / 2,
          az + oz * hang + wz * s * bw * 0.32,
          ox, oz, HANGER_T_M, HANGER_W_M, drop / 2, level, solid);
      }
      pushBoard(buf, ax + ox * hang, y - drop - bh / 2, az + oz * hang,
        wx, wz, bw / 2, bt / 2, bh / 2, level, art);
      break;
    }
  }
  return true;
}

/* -------------------------------------------------------------------------- */
/* the layer                                                                   */
/* -------------------------------------------------------------------------- */

async function getJSON(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`);
  return res.json();
}

/**
 * @param {object} o dataBase (data/ root) · terrain · confidence · problems
 * @returns {Promise<{group: THREE.Group, records: object[], census: object,
 *                    pickAt: function, dispose: function}>}
 */
export async function createSignage({
  dataBase, terrain, confidence = null, problems = [],
  /**
   * IS THIS BOARD'S BUILDING ACTUALLY STANDING? — T-1126.
   *
   * Every sign in this layer is a function of a wall: the record carries the
   * anchor on the facade, the bearing out of it, and a `height_datum` that says
   * in so many words "the base of this building's walls, as buildings.js sets
   * them". When the wall fails to arrive the arithmetic still works perfectly
   * and hangs the board 2.55 m up over an empty lot, which is a false claim
   * about the town made in the town's own voice.
   *
   * So the layer asks. The default answers no for everything, which is the
   * behaviour every gate and every caller had before this parameter existed —
   * a layer built without a scene behind it draws its whole record.
   */
  hostMissing = () => false,
} = {}) {
  const group = new THREE.Group();
  group.name = 'signage';
  const out = {
    group,
    records: [],
    signs: [],
    spans: [],
    census: { records: 0, boards: 0, lettered: 0, refused: 0, orphaned: 0, mountings: {} },
    pickAt: () => null,
    dispose: () => {},
  };

  if (!dataBase || !terrain) {
    problems.push('signage: no data base or no terrain — no sign is put up');
    return out;
  }
  let index;
  try {
    index = await getJSON(new URL('signage/index.json', dataBase));
  } catch (err) {
    // Degrade to NOTHING drawn plus a recorded problem, never to an invented
    // board: the same contract the enclosure and vegetation layers keep.
    problems.push(`signage: ${err.message} — no signboard is hung`);
    return out;
  }
  const wanted = Array.isArray(index.signage) ? index.signage : [];
  const loaded = await Promise.all(wanted.map(async (s) => {
    if (!s.file) return [s.id, null, 'the manifest gave no file'];
    try {
      return [s.id, await getJSON(new URL(`signage/${s.file}`, dataBase)), null];
    } catch (err) { return [s.id, null, err.message]; }
  }));

  const all = [];
  for (const [id, record, why] of loaded) {
    if (!record) { problems.push(`signage: ${id} — ${why}`); continue; }
    out.records.push(record);
    out.census.records += 1;
    out.census.refused += (record.refused ?? []).length;
    for (const sign of record.signs ?? []) all.push(sign);
  }

  // ONE ATLAS FOR THE WHOLE TOWN, painted before a triangle is emitted, because
  // every triangle needs the uv it hands back.
  const atlas = buildAtlas(all);
  if (!atlas) {
    problems.push('signage: no canvas to paint the signs on — the boards are drawn '
      + 'blank, in plain timber');
  }
  const plain = { rect: [0.02, 0.02, 0.06, 0.06], solid: [0.04, 0.98] };
  const timberUV = atlas?.timber ?? plain.solid;

  const buf = { pos: [], nrm: [], uv: [], conf: [] };
  /**
   * WHICH BUSINESS A TRIANGLE BELONGS TO. The layer is one draw call, so a hit
   * on the mesh knows nothing about which sign it landed on unless each sign
   * banks the half-open range of triangles it emitted. Every sign here has a
   * structure record behind it by construction — the rule that chose it started
   * from one — so unlike the fences there is no unpickable case. The spans are
   * published on the layer as well as used here: the smoke holds every sign to
   * ITS OWN declared reach, which needs to know which triangles are whose.
   */
  const spans = out.spans;
  for (const sign of all) {
    // A board comes down with its building (T-1126). Counted rather than
    // silently dropped: a town short of one signboard is a town short of one
    // BUILDING, and the count is what says so.
    if (hostMissing(sign.structure_id)) {
      out.census.orphaned += 1;
      problems.push(`signage: ${sign.structure_id} drew no geometry — its board is `
        + 'taken down rather than hung on a wall that is not there');
      continue;
    }
    const art = atlas?.signs.get(sign.structure_id) ?? plain;
    const from = buf.pos.length / 9;
    if (!buildSign(buf, sign, terrain, art, timberUV, problems)) continue;
    spans.push({ id: sign.structure_id, from, to: buf.pos.length / 9 });
    out.signs.push(sign);
    out.census.boards += 1;
    if (sign.sign_text) out.census.lettered += 1;
    const m = sign.mounting || 'bracket_board';
    out.census.mountings[m] = (out.census.mountings[m] ?? 0) + 1;
  }
  if (!buf.pos.length) {
    if (out.census.records) {
      problems.push('signage: the records loaded and not one sign was put up');
    }
    return out;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(buf.pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(buf.nrm, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(buf.uv, 2));
  geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(buf.conf, 1));
  geo.computeBoundingSphere();

  const mat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(0xffffff), roughness: 0.85, metalness: 0.0,
    /**
     * DOUBLE-SIDED, and it is the painted band that needs it. A band is one quad
     * wound from the wall's own axes, and a facade bearing this project reads
     * off a placement is right to a tenth of a degree but a footprint whose
     * max-`v` edge faces the other way would draw a sign that simply is not
     * there — with no page error and nothing on screen to debug. Two triangles
     * per band is not worth a winding rule that has to be right thirteen times.
     */
    side: THREE.DoubleSide,
  });
  /**
   * AND ITS SHADOW STAYS THE SIDE IT WAS. three derives `shadowSide` from
   * `side`, and the derivation is not symmetric: a FrontSide material casts from
   * its BACK faces, which is what keeps a solid from striping itself with its
   * own shadow, while a DoubleSide one casts from both and the near face lands
   * in the shadow map at its own depth. This layer was FrontSide until the
   * painted bands arrived and every solid in it is closed, so the side that
   * casts is pinned back to what it has always been.
   */
  mat.shadowSide = THREE.BackSide;
  if (atlas) mat.map = atlas.texture;
  mat.name = 'signboard-timber';
  confidence?.patch(mat);
  /**
   * ITS OWN PROGRAM CACHE KEY, AND WHY THIS LINE IS NOT OPTIONAL. three caches a
   * compiled program under a key ending in `material.customProgramCacheKey()`,
   * whose default is the SOURCE TEXT of `onBeforeCompile` — so every material
   * `confidence.patch()` touches reports the same key, and two patched materials
   * that agree on their other program parameters share one program. The
   * enclosure layer was drawn in solid black by a building's shader that way,
   * with no page error and no warning, on the first build of that layer. This
   * layer is the same shape of material and would walk into the same collision;
   * ticket T-0053 is the general fix.
   */
  mat.customProgramCacheKey = () => 'chicago4d-signboard-timber';

  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = 'signage';
  /**
   * THE ONE PIECE OF FURNITURE THAT STILL CASTS AT `light` — T-0115 measured it
   * and kept it deliberately. A sign is the only thing in this town whose whole
   * function is to be READ from the street, and its shadow is what lifts it off
   * the wall it is bolted to; with the boards not casting, the release gate's
   * own liveness check at the Tremont's footway fell to 0.28 against its 0.30
   * floor. Do not quietly add `signage` to main.js's FURNITURE_LAYERS.
   */
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);
  group.userData.census = out.census;
  if (atlas) out.atlas = { cells: atlas.cells, size: atlas.size };

  const raycaster = new THREE.Raycaster();
  /** The business this sign belongs to, or null. Same ray budget as the fences. */
  out.pickAt = (ndc, camera) => {
    if (!camera) return null;
    raycaster.setFromCamera(ndc ?? new THREE.Vector2(0, 0), camera);
    raycaster.far = Math.max(400, camera.position.y * 4);
    const hits = raycaster.intersectObject(mesh, false);
    if (!hits.length) return null;
    const hit = hits[0];
    const span = spans.find((sp) => hit.faceIndex >= sp.from && hit.faceIndex < sp.to);
    if (!span) return null;
    return { id: span.id, point: hit.point.clone(), distance: hit.distance };
  };

  out.dispose = () => {
    geo.dispose();
    mat.dispose();
    atlas?.texture?.dispose();
  };
  return out;
}
