/**
 * street-surfaces-1871.js — what the 1871 streets are made of, close up (T-3685, T-3807).
 *
 * The context city's streets.glb carries one material per surface, named by the
 * generator (generators/city_1871_emit.py `surface_plan`): `1871_woodblock`
 * (Nicholson end-grain block, where the Board of Public Works' 1871 report puts it
 * and on the principal thoroughfares up to its mileage), `1871_setts` (the boulder
 * pavement of the river streets), `1871_dirt` (every other street) and `1871_plank`
 * (the raised walks and the crossings). Their UVs run along the street (u) and
 * across it from the centreline (v), one unit to two metres, so ruts, block
 * courses and boards follow the street rather than the map grid.
 *
 * Each surface gets a small painted tile, colour plus a height for relief, drawn
 * once per page from a seeded generator. Mipmapping does the distance: within a
 * few metres the tile reads as the surface itself, and past about 150 m it
 * averages to the surface's own tone, which is the cheap far surface. A phone
 * (detail `light`) paints the same tiles at half the resolution.
 *
 * T-3807 (the owner, 2026-11-27: "photo match the best you can to the surrounding
 * street"): the wood block is drawn as the specification describes it (Andreas,
 * History of Chicago vol. 2 pp. 56-57: three-inch pine blocks six inches deep, set
 * on end in rows across the street on inch-board flooring, the inch-wide cells
 * between the rows filled with gravel and tar, the worn surface holding "a coating
 * of fine gravel"; the Board's 1871 report p. 22 for the "completely worn out"
 * Clark and Lake), not as the brick-shaped setts it read as. A second, larger
 * tile (the street's "grime": 24 m along by 8 m across, lanes either side of the
 * line) is multiplied over the roadways in the shader, so the wheel-polished
 * tracks, the dung and wet of the horse paths and the worn-out patches neither
 * repeat every two metres nor cost a full-size texture.
 *
 * Round the jaunt stops (data/context/1871/detail-rings.json) this module also
 * lays, from the floors the walker already stands on and at no cost to the
 * published files: stone-flag walks with stone kerbs in front of the fine stone
 * fronts the photographs show (STONE_FLAG_FRONTAGES), stone crosswalks over the
 * paved streets, a gutter along every kerb, and here and there a stretch of walk
 * standing a step or two above its neighbours with steps up and down between
 * them, Chicago's raised grade (gradeSteps; its floors are handed back so the
 * walker climbs them). Over the South Division's business blocks it lays trodden
 * yard ground, so the backs of lots read as built and used ground rather than
 * lawn; the Court House square keeps its grass.
 *
 * The walks' kerb boards and end risers, and a step at each end of a plank
 * crossing, are built here from `walk_surfaces`. `light` keeps the kerb along the
 * street and the steps, and leaves out the lot-side boards and the end risers.
 *
 * The tones, the flags, the steps and the yard ground are reconstructions
 * (L-1871-street-surfaces, L-1871-street-dress-3807), read against period
 * photographs (LOC stereographs 1s12325, 1s12371, 1s47902; NYPL Carbutt views of
 * Lake and Clark streets), not copied from them.
 */
import * as THREE from 'three';

function rng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6D2B79F5) >>> 0; let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function hashString(text) {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) h = Math.imul(h ^ text.charCodeAt(i), 16777619);
  return h >>> 0;
}
const rgb = (r, g, b, k = 1) => `rgb(${Math.round(Math.min(255, r * k))},${Math.round(Math.min(255, g * k))},${Math.round(Math.min(255, b * k))})`;
const grey = v => { const g = Math.max(0, Math.min(255, Math.round(v))); return `rgb(${g},${g},${g})`; };

/**
 * The order the street layers draw in, as ground decals (Kevin, 2026-11-21: "any
 * intersections of sidewalks or streets is flashy and blinks when you cross it").
 * Where two streets meet, their roadway ribbons lie one on the other at the same
 * height, and so do two walks at a corner; drawn with depth writes, the two faces
 * fought for every pixel and the junction blinked as the eye moved. As 1904's
 * roadways do (street-grid.js ROAD_RENDER_ORDER, T-3389), they now draw after every
 * opaque thing at order 0 without writing depth: overlapping faces of one layer
 * resolve by draw order, the same every frame, and each layer lies over the one
 * below — roadways (dirt, then boulders, then wood block), the gutters, the plank
 * crossings, then the raised walks, the stone flags laid over them and the raised
 * stretches. Keep anything opaque that lies under the streets below 10 (the yard
 * ground is 9.5).
 */
export const STREET_DECAL_ORDER = Object.freeze({ streets: 10, crossings: 10.2, walks: 10.3 });
const ROADWAY_RANK = Object.freeze({ dirt: 0, setts: 0.01, woodblock: 0.02 });
const DRESS_ORDER = Object.freeze({ yard: 9.5, gutters: 10.1, flags: 10.31, raised: 10.32, raisedFlags: 10.33 });

/** Metres one tile covers (square), its roughness and relief. */
export const SURFACES = Object.freeze({
  woodblock: { metres: 2, roughness: 0.92, bump: 0.022 },
  dirt: { metres: 16, roughness: 1, bump: 0.05 },
  setts: { metres: 2, roughness: 0.88, bump: 0.07 },
  plank: { metres: 2.4, roughness: 0.94, bump: 0.025 },
  kerb: { metres: 2, roughness: 0.95, bump: 0.02 },
  flags: { metres: 2.4, roughness: 0.93, bump: 0.025 },
  yard: { metres: 8, roughness: 1, bump: 0.04 },
});

/** The grime tile multiplied over the roadways: metres along and across (centred on the line). */
export const GRIME = Object.freeze({ along: 24, across: 8 });

/**
 * The fine stone fronts the photographs show, whose walks were stone flags with a
 * stone kerb (every other walk round the stops stays plank, "nearly all of pine",
 * Andreas vol. 2 p. 58). Each names its street (the walk ids' prefix) and a box in
 * local east/north metres that holds the centre of the walk on the side meant.
 */
export const STONE_FLAG_FRONTAGES = Object.freeze([
  { id: 'lake_wells_to_state', street: 'lake_street', e: [333, 832], n: [-127, -99],
    basis: 'Lake Street business blocks, both sides: NYPL Carbutt no. 70 "Lake street, East from Clark" (nypl_carbutt_lake_street_east_from_clark_stereo) shows pale paved walks and a pale crosswalk before the stone fronts' },
  { id: 'washington_crosbys', street: 'washington_street', e: [703, 905], n: [-389, -382],
    basis: "Crosby's Opera House front, Washington Street north side: loc_stereo_1s47902_crosbys_opera_house shows a broad jointed stone walk with a stone kerb" },
  { id: 'randolph_sherman_house', street: 'randolph_street', e: [457, 581], n: [-246, -240],
    basis: 'The Sherman House, Randolph Street front: loc_stereo_1s12371_sherman_house' },
  { id: 'clark_sherman_house', street: 'clark_street', e: [565, 573], n: [-253, -113],
    basis: 'The Sherman House, Clark Street front: loc_stereo_1s12371_sherman_house' },
  { id: 'court_house_square_clark', street: 'clark_street', e: [565, 573], n: [-394, -253],
    basis: 'The Court House square walks: loc_stereo_1s12325_court_house shows a flagged walk, stone kerb and stone crosswalk at the corner' },
  { id: 'court_house_square_randolph', street: 'randolph_street', e: [457, 581], n: [-266, -260], basis: 'as court_house_square_clark' },
  { id: 'court_house_square_washington', street: 'washington_street', e: [457, 581], n: [-389, -382], basis: 'as court_house_square_clark' },
  { id: 'court_house_square_lasalle', street: 'lasalle_street', e: [462, 468], n: [-394, -253], basis: 'as court_house_square_clark' },
  { id: 'chamber_of_commerce', street: 'washington_street', e: [457, 520], n: [-405, -399],
    basis: 'The Chamber of Commerce, Washington Street front: nypl_carbutt_140_chamber_of_commerce' },
  { id: 'chamber_of_commerce_lasalle', street: 'lasalle_street', e: [462, 468], n: [-464, -394], basis: 'as chamber_of_commerce' },
  { id: 'state_randolph_to_madison', street: 'state_street', e: [818, 846], n: [-530, -253],
    basis: "State Street's marble fronts, Field, Leiter & Co. at Washington: andreas_1885_v2 (the Field and Leiter plate, p. 563) and nypl_carbutt_booksellers_row_state_street_stereo" },
  { id: 'madison_tribune', street: 'madison_street', e: [703, 832], n: [-543, -537],
    basis: 'The Tribune building, Madison Street front: andreas_1885_v2 (the Tribune plate, p. 492) draws a broad stone walk and crossing' },
  { id: 'dearborn_tribune', street: 'dearborn_street', e: [710, 717], n: [-610, -530], basis: 'as madison_tribune' },
]);

/** The South Division's business blocks, where the backs of lots were yards and sheds, not lawn. */
export const YARD_GROUND = Object.freeze({
  e: [205, 1108], n: [-1000, -14],
  // The Court House square's lawn, inside its four walks, keeps its grass.
  keep: [{ id: 'court_house_square', e: [467, 567], n: [-384, -265] }],
});

const RISER_M = 0.17, TREAD_M = 0.32;

/** Paint one surface: { color, height } canvases of px × px, covering SURFACES[kind].metres. */
export function paintSurface(kind, px = 512, doc = globalThis.document) {
  const color = doc.createElement('canvas'), height = doc.createElement('canvas');
  color.width = color.height = height.width = height.height = px;
  const c = color.getContext('2d'), h = height.getContext('2d');
  const R = rng(kind.length * 7919 + kind.charCodeAt(0) * 31);
  const s = px / SURFACES[kind].metres; // pixels per metre
  const area = (px / 512) ** 2;          // counts scale with the tile's pixels
  const blots = (ctx, n, size, tone, alpha) => {
    for (let i = 0; i < n; i++) {
      const x = R() * px, y = R() * px, r = size * (0.4 + R());
      ctx.fillStyle = typeof tone === 'function' ? tone() : tone; ctx.globalAlpha = alpha * (0.4 + R() * 0.6);
      ctx.beginPath(); ctx.ellipse(x, y, r, r * (0.5 + R()), R() * Math.PI, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
  };
  h.fillStyle = grey(128); h.fillRect(0, 0, px, px);
  // Every mark that crosses an edge is drawn again on the far side, so the tile repeats without a seam.
  const wrapped = (x, y, r, draw) => {
    for (const dx of [0, -px, px]) for (const dy of [0, -px, px]) {
      if (x + dx + r < 0 || x + dx - r > px || y + dy + r < 0 || y + dy - r > px) continue;
      draw(x + dx, y + dy);
    }
  };
  const blotsWrapped = (ctx, n, size, tone, alpha, stretch = 1) => {
    for (let i = 0; i < n; i++) {
      const x = R() * px, y = R() * px, r = size * (0.4 + R()), t = typeof tone === 'function' ? tone() : tone;
      const a = alpha * (0.4 + R() * 0.6), ry = r * (0.5 + R() * 0.5) / stretch, rot = (R() - 0.5) * 0.4;
      wrapped(x, y, r, (X, Y) => { ctx.fillStyle = t; ctx.globalAlpha = a; ctx.beginPath(); ctx.ellipse(X, Y, r, ry, rot, 0, Math.PI * 2); ctx.fill(); });
    }
    ctx.globalAlpha = 1;
  };
  if (kind === 'woodblock') {
    // Nicholson pavement: rows of three-inch pine blocks set on end ACROSS the street
    // (x runs along it), each row a course 0.1 m wide of which the inch-wide cell
    // between rows is gravel rammed in hot tar; the blocks in a row 6 to 12 inches
    // long, butted. Weathered pine is grey-brown; the tops are worn round and hold
    // a skin of fine gravel; the cells show dark tar and pale grit.
    c.fillStyle = rgb(88, 80, 66); c.fillRect(0, 0, px, px);
    h.fillStyle = grey(70); h.fillRect(0, 0, px, px);
    blotsWrapped(c, Math.round(9000 * area), 0.009 * s, () => R() < 0.6 ? rgb(150, 140, 120) : rgb(56, 50, 42), 0.6); // gravel and tar in the cells
    const courses = Math.round(SURFACES[kind].metres / 0.1), course = px / courses, cell = course * 0.24;
    const pine = [[152, 126, 94], [142, 122, 96], [158, 130, 96], [134, 118, 98], [148, 128, 102], [126, 106, 84]];
    for (let k = 0; k < courses; k++) {
      const x = k * course + cell / 2, w = course - cell, lens = [];
      let total = 0;
      while (total < px) { const l = (0.15 + R() * 0.15) * s; lens.push(l); total += l; }
      const scale = px / total; let y = R() * 0.3 * s; // blocks fill the course exactly, then wrap
      for (const l0 of lens) {
        const l = l0 * scale, [pr, pg, pb] = pine[Math.floor(R() * pine.length)], tone = 0.86 + R() * 0.24;
        const butt = Math.max(1, px / 400), ringX = x + w * (R() * 1.6 - 0.3), ringY = y + l * (R() * 1.4 - 0.2), rings = 3 + Math.floor(R() * 4);
        const hi = 175 + R() * 50, crack = R() < 0.4;
        for (const Y of [y, y - px]) {
          c.fillStyle = rgb(pr, pg, pb, tone); c.fillRect(x, Y, w, l);
          c.fillStyle = rgb(70, 60, 48); c.globalAlpha = 0.45; c.fillRect(x, Y, w, butt); c.globalAlpha = 1; // the butt joint, closed up
          // the worn crown: lighter and grittier in the middle of the block, darker at its arrises
          c.fillStyle = rgb(pr + 18, pg + 16, pb + 14, tone); c.globalAlpha = 0.45;
          c.fillRect(x + w * 0.2, Y + butt + l * 0.18, w * 0.6, l * 0.64 - butt); c.globalAlpha = 1;
          c.save(); c.beginPath(); c.rect(x, Y + butt, w, l - butt); c.clip();
          c.strokeStyle = rgb(pr - 34, pg - 30, pb - 24, tone); c.lineWidth = Math.max(1, px / 700);
          const ry = ringY + (Y - y);
          for (let r = 1; r <= rings; r++) { c.globalAlpha = 0.22; c.beginPath(); c.arc(ringX, ry, r * 0.012 * s, 0, Math.PI * 2); c.stroke(); }
          if (crack) { // a check opened along the grain
            c.globalAlpha = 0.5; c.strokeStyle = rgb(48, 40, 32); c.beginPath();
            c.moveTo(ringX, ry); c.lineTo(x + w * R(), Y + butt + (l - butt) * (R() < 0.5 ? 0 : 1)); c.stroke();
          }
          c.restore(); c.globalAlpha = 1;
          h.fillStyle = grey(hi - 30); h.fillRect(x, Y + butt, w, l - butt);
          h.fillStyle = grey(hi); h.fillRect(x + w * 0.18, Y + butt + l * 0.15, w * 0.64, l * 0.7 - butt);
        }
        y += l;
      }
    }
    blotsWrapped(c, Math.round(3000 * area), 0.012 * s, rgb(156, 148, 132), 0.35); // the gravel skin on the tops
    blotsWrapped(c, Math.round(50 * area), 0.05 * s, rgb(34, 30, 26), 0.3);         // tar bled from the cells
    blotsWrapped(c, 20, 0.3 * s, rgb(90, 80, 64), 0.14, 2);                          // dried mud filmed over
  } else if (kind === 'dirt') {
    // Packed earth; across (y) the tile spans 16 m centred on the street's line.
    c.fillStyle = rgb(118, 98, 70); c.fillRect(0, 0, px, px);
    blotsWrapped(c, 5000, 0.05 * s, () => rgb(124 + R() * 30, 104 + R() * 24, 74 + R() * 18), 0.3);
    blotsWrapped(c, 40, 1.2 * s, rgb(92, 76, 54), 0.1, 3);  // damp ground and dried puddles, long with the street
    blotsWrapped(c, 400, 0.12 * s, rgb(78, 64, 46), 0.12, 1.5); // hoof marks and droppings, mostly mid-lane
    const mid = px / 2;
    for (const lane of [-4.6, -2.6, -0.95, 0.95, 2.6, 4.6]) { // wheel ruts, about 1.65 m gauge a lane
      const y0 = mid + lane * s, phase = R() * Math.PI * 2;
      for (let x = 0; x < px; x += 2) {
        const wob = Math.sin((x / px) * Math.PI * 4 + phase) * 0.06 * s; // two whole waves: seamless along
        c.globalAlpha = 0.45; c.fillStyle = rgb(80, 64, 46); c.fillRect(x, y0 + wob - 0.07 * s, 2, 0.14 * s);
        c.globalAlpha = 0.25; c.fillStyle = rgb(146, 126, 96); c.fillRect(x, y0 + wob + 0.08 * s, 2, 0.06 * s); // the rut's lip
        h.fillStyle = grey(70); h.fillRect(x, y0 + wob - 0.08 * s, 2, 0.16 * s);
      }
      c.globalAlpha = 1;
    }
    blotsWrapped(h, 1600, 0.06 * s, () => grey(100 + R() * 70), 0.5);
    // T-3807: dung down the middle of each lane (between its ruts) and wet where it lay.
    for (const lane of [-3.6, 0, 3.6]) {
      for (let i = 0; i < 90; i++) {
        const x = R() * px, y = mid + (lane + (R() - 0.5) * 0.9) * s;
        const heap = R() < 0.35;
        wrapped(x, y, 0.4 * s, (X, Y) => {
          c.globalAlpha = heap ? 0.8 : 0.3; c.fillStyle = heap ? rgb(62, 48, 28) : rgb(84, 70, 46);
          const r = (heap ? 0.06 : 0.12 + R() * 0.2) * s;
          c.beginPath(); c.ellipse(X, Y, r, r * 0.7, R(), 0, Math.PI * 2); c.fill();
        });
      }
      c.globalAlpha = 1;
    }
  } else if (kind === 'setts') {
    // Boulder pavement: rounded field stones of mixed sizes and colours set close in
    // sand, the joints full of dirt and muck rather than open ("soft and marly
    // stone" among them, Andreas vol. 2 p. 56).
    c.fillStyle = rgb(84, 72, 56); c.fillRect(0, 0, px, px);
    h.fillStyle = grey(50); h.fillRect(0, 0, px, px);
    const stones = [[118, 114, 106], [132, 122, 104], [104, 100, 96], [126, 110, 92], [140, 134, 122], [98, 92, 84]];
    const n = Math.round(SURFACES[kind].metres / 0.16), step = px / n;
    for (let row = 0; row < n; row++) {
      for (let col = 0; col < n; col++) {
        const x = (col + (row % 2) * 0.5 + (R() - 0.5) * 0.35) * step, y = (row + (R() - 0.5) * 0.35) * step;
        const r = step * (0.36 + R() * 0.2), k = 0.78 + R() * 0.35, [sr, sg, sb] = stones[Math.floor(R() * stones.length)];
        const rx = r * (0.8 + R() * 0.3), ry = r * (0.75 + R() * 0.3), rot = R() * Math.PI;
        wrapped(x, y, r * 1.3, (X, Y) => {
          c.fillStyle = rgb(sr, sg, sb, k); c.beginPath(); c.ellipse(X, Y, rx, ry, rot, 0, Math.PI * 2); c.fill();
          c.fillStyle = rgb(sr + 34, sg + 32, sb + 30, k); c.globalAlpha = 0.35; // the worn top
          c.beginPath(); c.ellipse(X - rx * 0.15, Y - ry * 0.15, rx * 0.5, ry * 0.45, rot, 0, Math.PI * 2); c.fill(); c.globalAlpha = 1;
          const g = h.createRadialGradient(X, Y, 0, X, Y, r);
          g.addColorStop(0, grey(225)); g.addColorStop(0.7, grey(165)); g.addColorStop(1, grey(60));
          h.fillStyle = g; h.beginPath(); h.ellipse(X, Y, rx, ry, rot, 0, Math.PI * 2); h.fill();
        });
      }
    }
    blotsWrapped(c, Math.round(400 * area), 0.05 * s, rgb(88, 74, 54), 0.3); // sand and muck over the stones
  } else if (kind === 'plank') {
    // Boards laid across the walk: their long side runs across (y), joints along (x).
    const board = 0.24 * s;
    for (let x = 0; x < px; x += board) {
      const k = 0.78 + R() * 0.35;
      c.fillStyle = rgb(132, 110, 82, k); c.fillRect(x, 0, board, px);
      c.strokeStyle = rgb(88, 74, 58, k); c.globalAlpha = 0.25; c.lineWidth = 1;
      for (let g = 0; g < 7; g++) {
        const gx = x + R() * board;
        c.beginPath(); c.moveTo(gx, 0); c.bezierCurveTo(gx + 2, px / 3, gx - 2, px * 2 / 3, gx + 1, px); c.stroke();
      }
      c.globalAlpha = 1;
      c.fillStyle = rgb(40, 33, 26); c.fillRect(x, 0, Math.max(1, px / 340), px); // the gap between boards
      h.fillStyle = grey(40); h.fillRect(x, 0, Math.max(1, px / 300), px);
      c.fillStyle = rgb(50, 44, 38);
      for (const ny of [0.15, 0.85]) { c.fillRect(x + board * 0.3, px * ny, 2, 2); c.fillRect(x + board * 0.7, px * ny, 2, 2); }
    }
    blots(c, 300, 0.05 * s, rgb(96, 84, 66), 0.2);
  } else if (kind === 'flags') {
    // Stone flags: big sawn slabs of the buff-grey Lemont and Joliet limestone the
    // fronts are built of, laid in courses along the walk (x), each course one or
    // two slabs across; mortar-dark joints, worn and stained.
    c.fillStyle = rgb(78, 74, 66); c.fillRect(0, 0, px, px);
    h.fillStyle = grey(50); h.fillRect(0, 0, px, px);
    const joint = Math.max(1.5, 0.01 * s);
    let x = 0; const lens = []; let total = 0;
    while (total < px) { const l = (1.0 + R() * 0.8) * s; lens.push(l); total += l; }
    const scale = px / total;
    for (const l0 of lens) {
      const l = l0 * scale, cuts = R() < 0.35 ? [0, (0.35 + R() * 0.3) * px, px] : [0, px];
      const shift = R() * px;
      for (let i = 0; i + 1 < cuts.length; i++) {
        const k = 0.86 + R() * 0.2, warm = (R() - 0.4) * 14, y0 = cuts[i] + shift, y1 = cuts[i + 1] + shift;
        for (const off of [0, -px]) {
          const Y0 = y0 + off + joint / 2, Y1 = y1 + off - joint / 2;
          c.fillStyle = rgb(188 + warm, 172 + warm * 0.6, 142, k); c.fillRect(x + joint / 2, Y0, l - joint, Y1 - Y0);
          c.fillStyle = rgb(120, 114, 100); c.globalAlpha = 0.18; // the arrises worn and dirty
          c.fillRect(x + joint / 2, Y0, l - joint, 0.04 * s); c.fillRect(x + joint / 2, Y1 - 0.04 * s, l - joint, 0.04 * s);
          c.globalAlpha = 1;
          h.fillStyle = grey(175); h.fillRect(x + joint / 2, Y0, l - joint, Y1 - Y0);
        }
        if (R() < 0.18) { // a cracked slab
          const cy = y0 + (y1 - y0) * (0.2 + R() * 0.6);
          c.strokeStyle = rgb(70, 66, 58); c.globalAlpha = 0.7; c.lineWidth = Math.max(1, px / 600);
          for (const off of [0, -px]) { c.beginPath(); c.moveTo(x + l * 0.1, cy + off); c.lineTo(x + l * 0.5, cy + off + (R() - 0.5) * 0.2 * s); c.lineTo(x + l * 0.9, cy + off + (R() - 0.5) * 0.3 * s); c.stroke(); }
          c.globalAlpha = 1;
        }
      }
      x += l;
    }
    blotsWrapped(c, Math.round(2600 * area), 0.01 * s, () => R() < 0.5 ? rgb(196, 188, 170) : rgb(130, 124, 110), 0.25); // the stone's grain
    blotsWrapped(c, 26, 0.25 * s, rgb(110, 100, 84), 0.12, 1.5);  // trodden dirt and wet
    blotsWrapped(c, 8, 0.12 * s, rgb(70, 64, 56), 0.2);           // spills and tobacco
  } else if (kind === 'yard') {
    // Trodden yard ground behind the fronts: earth, cinders and ash, wood chips and
    // straw, worn bare; a little grass only along the fences, which no tile knows.
    c.fillStyle = rgb(100, 86, 66); c.fillRect(0, 0, px, px);
    blotsWrapped(c, 26, 0.9 * s, () => R() < 0.5 ? rgb(84, 74, 60) : rgb(118, 102, 78), 0.25, 1.3);
    blotsWrapped(c, Math.round(5000 * area), 0.03 * s, () => rgb(92 + R() * 40, 80 + R() * 32, 62 + R() * 24), 0.35);
    blotsWrapped(c, Math.round(900 * area), 0.025 * s, () => R() < 0.6 ? rgb(52, 50, 48) : rgb(150, 146, 140), 0.45); // cinders and ash
    blotsWrapped(c, Math.round(160 * area), 0.04 * s, rgb(156, 132, 92), 0.5, 3); // chips and straw
    blotsWrapped(c, Math.round(40 * area), 0.08 * s, rgb(84, 96, 58), 0.3);       // a weed
    blotsWrapped(h, Math.round(1400 * area), 0.05 * s, () => grey(90 + R() * 80), 0.5);
  } else { // kerb: a weathered edge board, its grain along (x)
    c.fillStyle = rgb(92, 76, 56); c.fillRect(0, 0, px, px);
    c.strokeStyle = rgb(64, 52, 38); c.globalAlpha = 0.3; c.lineWidth = 1;
    for (let g = 0; g < 40; g++) { const gy = R() * px; c.beginPath(); c.moveTo(0, gy); c.bezierCurveTo(px / 3, gy + 3, px * 2 / 3, gy - 3, px, gy); c.stroke(); }
    c.globalAlpha = 1;
    blots(c, 200, 0.05 * s, rgb(60, 48, 34), 0.3);
  }
  return { color, height };
}

/**
 * The street's grime, a colour multiplier (mid-grey is 1): W = 3 × px along (24 m),
 * H = px across (8 m, the street's line at its middle), so a lane runs 2 m either
 * side of the line and again 6 m out. Wheel tracks polished pale, the horse path
 * down each lane stained with dung and wet, straw, a few worn-out patches mended
 * with muck (the Board, 1871: Clark and Lake "completely worn out in many places").
 */
export function paintGrime(px = 256, doc = globalThis.document) {
  const W = px * 3, H = px, s = px / GRIME.across;
  const canvas = doc.createElement('canvas'); canvas.width = W; canvas.height = H;
  const c = canvas.getContext('2d'), R = rng(3807);
  const area = (px / 256) ** 2;
  c.fillStyle = grey(128); c.fillRect(0, 0, W, H);
  const wrapped = (x, y, r, draw) => {
    for (const dx of [0, -W, W]) for (const dy of [0, -H, H]) {
      if (x + dx + r < 0 || x + dx - r > W || y + dy + r < 0 || y + dy - r > H) continue;
      draw(x + dx, y + dy);
    }
  };
  const blot = (x, y, rx, ry, tone, alpha, rot = 0) => wrapped(x, y, Math.max(rx, ry), (X, Y) => {
    c.globalAlpha = alpha; c.fillStyle = tone; c.beginPath(); c.ellipse(X, Y, rx, ry, rot, 0, Math.PI * 2); c.fill();
  });
  for (let i = 0; i < 90 * area; i++) blot(R() * W, R() * H, (1 + R() * 2) * s, (0.5 + R()) * s, grey(116 + R() * 26), 0.25);
  const lanes = [2, 6]; // across, in metres from the tile's edge (the line is at 4)
  for (const lane of lanes) {
    for (const side of [-0.78, 0.78]) { // the wheel tracks: polished, with grit at their lips
      const y0 = (lane + side) * s, phase = R() * Math.PI * 2;
      for (let x = 0; x < W; x += 2) {
        const wob = Math.sin((x / W) * Math.PI * 6 + phase) * 0.1 * s;
        c.globalAlpha = 0.3; c.fillStyle = rgb(158, 154, 146); c.fillRect(x, y0 + wob - 0.12 * s, 2, 0.24 * s);
      }
    }
    for (let i = 0; i < 70 * area; i++) { // dung and wet down the horse path
      const x = R() * W, y = (lane + (R() - 0.5) * 0.9) * s;
      blot(x, y, (0.12 + R() * 0.35) * s, (0.08 + R() * 0.15) * s, R() < 0.65 ? rgb(96, 74, 42) : rgb(94, 90, 82), 0.4 + R() * 0.3, (R() - 0.5) * 0.5);
    }
    for (let i = 0; i < 26 * area; i++) { // droppings, in little heaps
      const x = R() * W, y = (lane + (R() - 0.5) * 0.6) * s;
      for (let j = 0; j < 3 + R() * 5; j++) blot(x + (R() - 0.5) * 0.18 * s, y + (R() - 0.5) * 0.14 * s, 0.035 * s, 0.03 * s, rgb(58, 46, 28), 0.85);
    }
  }
  for (let i = 0; i < 120 * area; i++) { // straw
    const x = R() * W, y = R() * H, a = R() * Math.PI, l = (0.08 + R() * 0.16) * s;
    wrapped(x, y, l, (X, Y) => { c.globalAlpha = 0.55; c.strokeStyle = rgb(196, 174, 112); c.lineWidth = Math.max(1, s * 0.012);
      c.beginPath(); c.moveTo(X, Y); c.lineTo(X + Math.cos(a) * l, Y + Math.sin(a) * l); c.stroke(); });
  }
  for (let i = 0; i < 4; i++) { // worn-out patches mended with muck
    const x = R() * W, y = R() * H;
    for (let j = 0; j < 7; j++) blot(x + (R() - 0.5) * 0.9 * s, y + (R() - 0.5) * 0.6 * s, (0.2 + R() * 0.3) * s, (0.15 + R() * 0.2) * s, rgb(86, 70, 50), 0.6);
  }
  c.globalAlpha = 1;
  return canvas;
}

/**
 * Multiply the grime tile over a dressed material's colour in its fragment shader,
 * at its own scale: the grime's UV is the map's UV (in map tiles) scaled to grime
 * tiles. Chains whatever hook the material already carries (the confidence view).
 */
function addGrime(material, grime, scale, offset) {
  const prior = material.onBeforeCompile;
  const uniforms = { uGrimeMap: { value: grime }, uGrimeScale: { value: new THREE.Vector2(...scale) },
    uGrimeOffset: { value: new THREE.Vector2(...offset) } };
  material.onBeforeCompile = function streetGrime(shader, renderer) {
    if (typeof prior === 'function') prior.call(this, shader, renderer);
    Object.assign(shader.uniforms, uniforms);
    shader.fragmentShader = 'uniform sampler2D uGrimeMap;\nuniform vec2 uGrimeScale;\nuniform vec2 uGrimeOffset;\n'
      + shader.fragmentShader.replace('#include <map_fragment>',
        '#include <map_fragment>\n#ifdef USE_MAP\n\tdiffuseColor.rgb *= texture2D( uGrimeMap, vMapUv * uGrimeScale + uGrimeOffset ).rgb * 2.0;\n#endif');
  };
  material.userData.streetGrime = true;
  material.needsUpdate = true;
}

/** The painted tile for one surface, as map + bump textures (cached per call site). */
function tileTextures(kind, px, anisotropy, made, textures) {
  if (made.has(kind)) return made.get(kind);
  const { color, height } = paintSurface(kind, px);
  const map = new THREE.CanvasTexture(color), bump = new THREE.CanvasTexture(height);
  const repeat = 2 / SURFACES[kind].metres; // UVs: one unit to two metres
  for (const t of [map, bump]) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = anisotropy;
    t.repeat.set(repeat, repeat);
    // across-street v is centred on the line: the dirt tile's ruts sit either side of it
    if (kind === 'dirt') t.offset.set(0, 0.5);
  }
  map.colorSpace = THREE.SRGBColorSpace;
  textures.push(map, bump);
  made.set(kind, { map, bump });
  return made.get(kind);
}

function dress(material, kind, tile) {
  material.map = tile.map; material.bumpMap = tile.bump; material.bumpScale = SURFACES[kind].bump;
  material.color?.setRGB(1, 1, 1);
  if ('roughness' in material) material.roughness = SURFACES[kind].roughness;
  material.needsUpdate = true;
}

/** The grime's UV transform for a roadway tile: the map's UV is in map tiles, its v centred as the map's offset says. */
function grimeTransform(kind) {
  const m = SURFACES[kind].metres, sx = m / GRIME.along, sy = m / GRIME.across;
  const mapOffsetV = kind === 'dirt' ? 0.5 : 0;
  return [[sx, sy], [0, 0.5 - mapOffsetV * sy]];
}

/** Distance from (e, n) to the nearest detail ring's point or line. */
function ringDistance(rings, e, n) {
  let best = Infinity;
  for (const ring of rings ?? []) {
    const p = ring.points ?? [];
    if (p.length === 1) best = Math.min(best, Math.hypot(e - p[0][0], n - p[0][1]));
    for (let i = 0; i + 1 < p.length; i++) best = Math.min(best, segmentDistance([e, n], p[i], p[i + 1]));
  }
  return best;
}
function segmentDistance(q, a, b) {
  const de = b[0] - a[0], dn = b[1] - a[1], L2 = de * de + dn * dn;
  const t = L2 > 0 ? Math.max(0, Math.min(1, ((q[0] - a[0]) * de + (q[1] - a[1]) * dn) / L2)) : 0;
  return Math.hypot(q[0] - a[0] - t * de, q[1] - a[1] - t * dn);
}
const streetOf = id => /^(.*?)__/.exec(id ?? '')?.[1] ?? '';
const midpoint = w => [(w.a[0] + w.b[0]) / 2, (w.a[1] + w.b[1]) / 2];

/** The stone-flag frontage a walk lies in, or null. */
export function flagFrontage(w) {
  if (w.kind !== 'walk') return null;
  const [e, n] = midpoint(w), street = streetOf(w.id);
  return STONE_FLAG_FRONTAGES.find(f => street.startsWith(f.street) && e >= f.e[0] && e <= f.e[1] && n >= f.n[0] && n <= f.n[1]) ?? null;
}

/** Collects quads into one indexed geometry. */
function quadSink() {
  const pos = [], nrm = [], uv = [];
  return {
    pos, nrm, uv,
    vertical(a, b, y0, y1, along = 0) { // a vertical face from a to b, facing its right-hand side
      const de = b[0] - a[0], dn = b[1] - a[1], L = Math.hypot(de, dn);
      if (L < 0.01 || y1 - y0 < 0.005) return;
      const nx = dn / L, nz = de / L; // right of a→b in map e/n is (dn, -de); glTF z = -n
      for (const [p, y] of [[a, y0], [b, y0], [b, y1], [a, y1]]) { pos.push(p[0], y, -p[1]); nrm.push(nx, 0, nz); }
      uv.push(along / 2, y0 / 2, (along + L) / 2, y0 / 2, (along + L) / 2, y1 / 2, along / 2, y1 / 2);
    },
    flat(a, b, width, y, u0 = 0, v0 = 0) { // a horizontal ribbon from a to b on its centreline, facing up
      const de = b[0] - a[0], dn = b[1] - a[1], L = Math.hypot(de, dn);
      if (L < 0.01) return;
      const ox = -dn / L * width / 2, on = de / L * width / 2;
      for (const p of [[a[0] + ox, a[1] + on], [a[0] - ox, a[1] - on], [b[0] - ox, b[1] - on], [b[0] + ox, b[1] + on]]) {
        pos.push(p[0], y, -p[1]); nrm.push(0, 1, 0);
      }
      uv.push(u0 / 2, (v0 - width / 2) / 2, u0 / 2, (v0 + width / 2) / 2, (u0 + L) / 2, (v0 + width / 2) / 2, (u0 + L) / 2, (v0 - width / 2) / 2);
    },
    rect(e0, e1, n0, n1, y) { // an axis box on the ground, facing up, UVs in map metres
      for (const [e, n] of [[e0, n0], [e1, n0], [e1, n1], [e0, n1]]) { pos.push(e, y, -n); nrm.push(0, 1, 0); uv.push(e / 2, n / 2); }
    },
    get quads() { return pos.length / 12; },
  };
}
function sinkGeometry(sink, { upward = false } = {}) {
  if (!sink.pos.length) return null;
  const count = sink.pos.length / 3, index = new Uint32Array(count / 4 * 6);
  for (let q = 0, k = 0; q < count; q += 4) {
    // Upward faces wound to face +y whichever way their corners turn.
    let flip = false;
    if (upward) {
      const p = sink.pos, i = q * 3;
      const ax = p[i + 3] - p[i], az = p[i + 5] - p[i + 2], bx = p[i + 6] - p[i], bz = p[i + 8] - p[i + 2];
      flip = az * bx - ax * bz <= 0;
    }
    index.set(flip ? [q, q + 2, q + 1, q, q + 3, q + 2] : [q, q + 1, q + 2, q, q + 2, q + 3], k); k += 6;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(sink.pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(sink.nrm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(sink.uv, 2));
  g.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(count).fill(1), 1));
  g.setIndex(new THREE.BufferAttribute(index, 1));
  g.computeBoundingBox(); g.computeBoundingSphere();
  return g;
}

/**
 * Dress the context city's street materials in place and build the walks' edges,
 * and round the jaunt stops (`rings`, detail-rings.json's list) the flags, stone
 * crossings, gutters, raised stretches and the business blocks' yard ground.
 * Returns { textures, materials, meshes, floors, census } for the caller to own and
 * dispose; `floors` are the raised stretches' and their steps' ribbons
 * ({ a, b, width_m, y }), for the floor index the walker stands on.
 */
export function dressStreetSurfaces(meshes, { walkSurfaces = [], heights = {}, detail = 'full',
  anisotropy = 4, confidence = null, rings = null, streets = [] } = {}) {
  const made = new Map(), textures = [], materials = [], out = [];
  const px = detail === 'light' ? 256 : 512;
  const dressed = new Set();
  let grime = null; // painted on first need, as the tiles are (no canvas before a paved street)
  const grimeTexture = () => {
    if (grime) return grime;
    grime = new THREE.CanvasTexture(paintGrime(px / 2));
    grime.wrapS = grime.wrapT = THREE.RepeatWrapping; grime.anisotropy = anisotropy;
    grime.colorSpace = THREE.NoColorSpace; // a multiplier, read as data
    textures.push(grime);
    return grime;
  };
  let decals = 0;
  for (const mesh of meshes) {
    const material = mesh.material, kind = String(material?.name ?? '').replace(/^1871_/, '');
    if (!SURFACES[kind]) continue;
    const layers = mesh.userData?.layers ?? [];
    if (layers.length && layers.every(l => STREET_DECAL_ORDER[l] != null)) {
      // one layer a batch (city-context.js splits them); a roadway ranks by its surface
      mesh.renderOrder = Math.max(...layers.map(l => STREET_DECAL_ORDER[l])) + (layers.includes('streets') ? (ROADWAY_RANK[kind] ?? 0) : 0);
      material.depthWrite = false;
      decals++;
    }
    if (dressed.has(material)) continue;
    dress(material, kind, tileTextures(kind, px, anisotropy, made, textures));
    if (kind === 'woodblock' || kind === 'setts') addGrime(material, grimeTexture(), ...grimeTransform(kind));
    dressed.add(material);
  }
  const road = heights.road ?? 3.23, ground = heights.ground ?? 3.2, walkY = heights.walk ?? 3.38;
  const light = detail === 'light';
  const radius = Number(rings?.radius_m?.full) || 200;
  const ringList = rings?.rings ?? [];
  const nearStop = (e, n) => ringList.length > 0 && ringDistance(ringList, e, n) <= radius;

  // Which crossings cross a paved street round the stops: those are stone.
  const paved = (streets ?? []).filter(r => !Array.isArray(r) && (r.surface === 'woodblock' || r.surface === 'setts')
    && Array.isArray(r.a) && Array.isArray(r.b) && ringList.length
    && Math.min(ringDistance(ringList, ...r.a), ringDistance(ringList, ...r.b), ringDistance(ringList, (r.a[0] + r.b[0]) / 2, (r.a[1] + r.b[1]) / 2)) <= radius + 150);
  const crossesPaved = w => {
    const m = midpoint(w), own = streetOf(w.id);
    return paved.some(r => r.street_id !== own && segmentDistance(m, r.a, r.b) <= r.width_m / 2 + 0.5);
  };

  const stoneSurfaces = [], plankSurfaces = [], flagWalks = [], stoneCrossings = [], ringWalks = [];
  for (const w of walkSurfaces) {
    if (w.kind !== 'walk' && w.kind !== 'crossing') continue;
    const [e, n] = midpoint(w);
    const near = nearStop(e, n);
    if (w.kind === 'walk') {
      if (near) ringWalks.push(w);
      if (near && flagFrontage(w)) { flagWalks.push(w); stoneSurfaces.push(w); continue; }
    } else if (near && crossesPaved(w)) { stoneCrossings.push(w); stoneSurfaces.push(w); continue; }
    plankSurfaces.push(w);
  }
  // The generator lays crossings only over the dirt streets. Over a paved street round the
  // stops, where a walk stops at the cross street and the same side's walk picks up beyond
  // it, a stone crosswalk is laid on the walk's line, a little proud of the blocks.
  const floors = [];
  const sideOf = w => /_walk_(-?1)(?:_\d+)?$/.exec(w.id ?? '')?.[1];
  const bySide = new Map();
  for (const w of walkSurfaces) {
    if (w.kind !== 'walk' || !sideOf(w)) continue;
    const key = `${streetOf(w.id)}:${sideOf(w)}`;
    if (!bySide.has(key)) bySide.set(key, []);
    bySide.get(key).push(w);
  }
  const crossingY = road + 0.05;
  for (const w of ringWalks) {
    const L = Math.hypot(w.b[0] - w.a[0], w.b[1] - w.a[1]); if (!(L > 1)) continue;
    const ue = (w.b[0] - w.a[0]) / L, un = (w.b[1] - w.a[1]) / L;
    let best = null;
    for (const v of bySide.get(`${streetOf(w.id)}:${sideOf(w)}`) ?? []) {
      if (v === w) continue;
      const de = v.a[0] - w.b[0], dn = v.a[1] - w.b[1], d = Math.hypot(de, dn);
      if (d < 6 || d > 34 || (de * ue + dn * un) / d < 0.97) continue;
      if (!best || d < best.d) best = { v, d };
    }
    if (!best) continue;
    const x = { id: `${w.id}__stone_x`, kind: 'crossing', a: w.b, b: best.v.a, width_m: 2.4, y: +crossingY.toFixed(3) };
    if (!crossesPaved(x)) continue;
    stoneCrossings.push(x); stoneSurfaces.push(x);
    floors.push({ a: x.a, b: x.b, width_m: x.width_m, y: x.y });
  }

  // tiles and materials are made only for what is laid (a city with no stops paints no canvas)
  const flagTile = () => tileTextures('flags', px, anisotropy, made, textures);
  const newMaterial = (name, kind, tile, tint = 1, roughness = null) => {
    const material = new THREE.MeshStandardMaterial({ name });
    dress(material, kind, tile);
    material.color.setRGB(tint, tint, tint);
    if (roughness != null) material.roughness = roughness;
    confidence?.patch?.(material);
    materials.push(material);
    return material;
  };
  const addMesh = (geometry, material, name, { order = null, layers, upward = false } = {}) => {
    if (!geometry) return 0;
    if (order != null) { material.depthWrite = false; material.polygonOffset = true; material.polygonOffsetFactor = -1; material.polygonOffsetUnits = -2; }
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = `context:1871:infrastructure:${name}:${material.name}`;
    mesh.receiveShadow = true;
    if (order != null) mesh.renderOrder = order;
    const quads = geometry.getAttribute('position').count / 4;
    mesh.userData = { layer: 'infrastructure', layers, confidence: 'reconstructed',
      liberty: layers.includes('walk_edges') ? 'L-1871-street-surfaces' : 'L-1871-street-dress-3807', triangles: quads * 2 };
    out.push(mesh);
    return quads;
  };

  // The plank walks' kerb boards and crossing steps, as T-3685 built them.
  let quads = 0;
  const plankEdges = walkEdgeGeometry(plankSurfaces, { road, ground, walk: walkY, light });
  if (plankEdges) {
    const material = newMaterial('1871_kerb', 'kerb', tileTextures('kerb', px, anisotropy, made, textures));
    quads += addMesh(plankEdges, material, 'walk_edges', { layers: ['walk_edges'] });
  }
  // The stone walks' kerbstones and the stone crossings' steps.
  const stoneEdgeSink = quadSink();
  walkEdgeGeometry(stoneSurfaces, { road, ground, walk: walkY, light, sink: stoneEdgeSink });
  const plankEdgeSink = quadSink(); // the raised stretches' faces on plank walks
  // The flags laid over the plank walks and crossings they replace.
  const flagSink = quadSink();
  for (const w of flagWalks) flagSink.flat(w.a, w.b, w.width_m, w.y + 0.004);
  for (const w of stoneCrossings) {
    flagSink.flat(w.a, w.b, w.width_m, w.y + 0.004);
    if (!/__stone_x$/.test(w.id)) continue;
    // the laid crosswalk's two long edges, from the blocks up to its top
    const L = Math.hypot(w.b[0] - w.a[0], w.b[1] - w.a[1]), ue = (w.b[0] - w.a[0]) / L, un = (w.b[1] - w.a[1]) / L, o = w.width_m / 2;
    const side = (p, k) => [p[0] - un * k, p[1] + ue * k];
    stoneEdgeSink.vertical(side(w.b, o), side(w.a, o), road - 0.02, w.y);
    stoneEdgeSink.vertical(side(w.a, -o), side(w.b, -o), road - 0.02, w.y);
  }
  // A gutter along every kerb round the stops, on the roadway's edge.
  const gutterSink = quadSink();
  for (const w of ringWalks) {
    const side = walkStreetSide(w); if (!side) continue;
    const L = Math.hypot(w.b[0] - w.a[0], w.b[1] - w.a[1]); if (!(L > 1)) continue;
    const ue = (w.b[0] - w.a[0]) / L, un = (w.b[1] - w.a[1]) / L, o = side * (w.width_m / 2 + 0.3);
    const shift = p => [p[0] - un * o, p[1] + ue * o];
    gutterSink.flat(shift(w.a), shift(w.b), 0.6, road + 0.006, 0, 7.2);
  }
  // Chicago's raised grade: here and there a stretch of walk a step or two above its neighbours.
  const raisedSink = quadSink(), raisedFlagSink = quadSink();
  let pieces = 0;
  for (const w of ringWalks) {
    const flagged = flagWalks.includes(w);
    pieces += gradeSteps(w, { road, ground, top: flagged ? raisedFlagSink : raisedSink,
      faces: flagged ? stoneEdgeSink : plankEdgeSink, floors });
  }
  const flagQuads = flagSink.quads ? addMesh(sinkGeometry(flagSink, { upward: true }), newMaterial('1871_flags', 'flags', flagTile()),
    'flags', { order: DRESS_ORDER.flags, layers: ['flags'] }) : 0;
  const kerbstoneQuads = stoneEdgeSink.quads ? addMesh(sinkGeometry(stoneEdgeSink),
    newMaterial('1871_kerbstone', 'flags', flagTile(), 0.74, 0.88), 'kerbstones', { layers: ['kerbstones'] }) : 0;
  let raisedQuads = 0;
  if (plankEdgeSink.quads) {
    const material = newMaterial('1871_kerb_raised', 'kerb', tileTextures('kerb', px, anisotropy, made, textures));
    raisedQuads += addMesh(sinkGeometry(plankEdgeSink), material, 'raised_faces', { layers: ['raised_walks'] });
  }
  if (raisedSink.quads) {
    const material = newMaterial('1871_plank_raised', 'plank', tileTextures('plank', px, anisotropy, made, textures));
    raisedQuads += addMesh(sinkGeometry(raisedSink, { upward: true }), material, 'raised_walks', { order: DRESS_ORDER.raised, layers: ['raised_walks'] });
  }
  if (raisedFlagSink.quads) {
    const material = newMaterial('1871_flags_raised', 'flags', flagTile());
    raisedQuads += addMesh(sinkGeometry(raisedFlagSink, { upward: true }), material, 'raised_flags', { order: DRESS_ORDER.raisedFlags, layers: ['raised_walks'] });
  }
  const gutterQuads = gutterSink.quads ? addMesh(sinkGeometry(gutterSink, { upward: true }),
    newMaterial('1871_gutter', 'dirt', tileTextures('dirt', px, anisotropy, made, textures), 0.62, 0.55),
    'gutters', { order: DRESS_ORDER.gutters, layers: ['gutters'] }) : 0;
  // The business blocks' yard ground, under the streets, round the square's lawn.
  let yardQuads = 0;
  if (ringList.length) {
    const yardSink = quadSink(), Y = ground + 0.012, [e0, e1] = YARD_GROUND.e, [n0, n1] = YARD_GROUND.n;
    const hole = YARD_GROUND.keep[0];
    yardSink.rect(e0, e1, n0, hole.n[0], Y); yardSink.rect(e0, e1, hole.n[1], n1, Y);
    yardSink.rect(e0, hole.e[0], hole.n[0], hole.n[1], Y); yardSink.rect(hole.e[1], e1, hole.n[0], hole.n[1], Y);
    const material = newMaterial('1871_yard', 'yard', tileTextures('yard', px, anisotropy, made, textures));
    yardQuads = addMesh(sinkGeometry(yardSink, { upward: true }), material, 'yard_ground', { order: DRESS_ORDER.yard, layers: ['yard_ground'] });
  }
  return { textures, materials, meshes: out, floors, census: { detail, dressed: dressed.size, decals, edgeQuads: quads, tilePx: px,
    flagWalks: flagWalks.length, stoneCrossings: stoneCrossings.length, flagQuads, kerbstoneQuads, gutterQuads,
    raisedPieces: pieces, raisedQuads, floorRibbons: floors.length, yardQuads, ringWalks: ringWalks.length } };
}

/** Which side of a walk the street is on: 1 left of a→b, -1 right, from its id's `_walk_<side>`; null when unknown. */
function walkStreetSide(w) {
  const s = /_walk_(-?1)(?:_\d+)?$/.exec(w.id ?? '')?.[1];
  // The generator's side of the centreline (-1 right, 1 left of the street's run,
  // which runs the same way as the walk): a right-hand walk has the street on its left.
  return s === '-1' ? 1 : s === '1' ? -1 : null;
}

/**
 * Raise stretches of one walk a riser or two (0.17 m each) above the rest, with a
 * step at each end: the walk is cut into frontages 7 to 22 m long from a seed of its
 * id (its first and last 3 m always stay at the walk's own height, where it meets
 * the corner and the crossing), and about one frontage in four stands up, never two
 * side by side. Pushes the tops to `top`, the risers and side faces to `faces`, and
 * each level's floor ribbon to `floors`. Returns the number of raised stretches.
 */
export function gradeSteps(w, { road = 3.23, ground = 3.2, top, faces, floors }) {
  const L = Math.hypot(w.b[0] - w.a[0], w.b[1] - w.a[1]);
  if (!(L >= 20)) return 0;
  const side = walkStreetSide(w);
  if (!side) return 0;
  const R = rng(hashString(w.id ?? `${w.a}`));
  const ue = (w.b[0] - w.a[0]) / L, un = (w.b[1] - w.a[1]) / L, half = w.width_m / 2;
  const at = (s, o = 0) => [w.a[0] + ue * s - un * o, w.a[1] + un * s + ue * o]; // o > 0: left of a→b
  let s = 3, raisedBefore = false, count = 0;
  while (s < L - 3) {
    let s1 = Math.min(s + 7 + R() * 15, L - 3);
    if (L - 3 - s1 < 5) s1 = L - 3;
    const raise = !raisedBefore && R() < 0.26 && s1 - s >= 5;
    const steps = R() < 0.7 ? 1 : 2;
    if (raise) {
      count++;
      for (let j = 1; j <= steps; j++) {
        const a = s + (j - 1) * TREAD_M, b = s1 - (j - 1) * TREAD_M, y0 = w.y + (j - 1) * RISER_M, y1 = w.y + j * RISER_M;
        floors?.push({ a: at(a), b: at(b), width_m: w.width_m, y: +y1.toFixed(3) });
        // its street face from the roadway (the first level) and its lot face from the ground, just proud of the kerb
        const streetO = side * (half + 0.012), lotO = -side * (half + 0.012);
        const base = j === 1;
        if (side > 0) { faces.vertical(at(b, streetO), at(a, streetO), base ? road - 0.02 : y0, y1, a); faces.vertical(at(a, lotO), at(b, lotO), base ? ground - 0.02 : y0, y1, a); }
        else { faces.vertical(at(a, streetO), at(b, streetO), base ? road - 0.02 : y0, y1, a); faces.vertical(at(b, lotO), at(a, lotO), base ? ground - 0.02 : y0, y1, a); }
        // the risers at both ends
        faces.vertical(at(a, half), at(a, -half), y0, y1, 0); faces.vertical(at(b, -half), at(b, half), y0, y1, 0);
        // the treads: the whole top on the highest level, else the two step treads
        if (j === steps) top.flat(at(a), at(b), w.width_m, y1 + 0.002, a);
        else { top.flat(at(a), at(a + TREAD_M), w.width_m, y1 + 0.002, a); top.flat(at(b - TREAD_M), at(b), w.width_m, y1 + 0.002, b - TREAD_M); }
      }
    }
    raisedBefore = raise;
    s = s1;
  }
  return count;
}

/**
 * The vertical faces of the raised walks and the steps at the crossings, from the
 * floor ribbons: a kerb board along each walk's street side (from the roadway up to
 * the walk), and — above `light` — its lot-side board (from the ground) and its end
 * risers; and at each end of a crossing, a step half way between the two. With a
 * `sink`, the faces are added to it and nothing is returned.
 */
export function walkEdgeGeometry(surfaces, { road = 3.23, ground = 3.2, walk = 3.38, light = false, sink = null } = {}) {
  const S = sink ?? quadSink();
  for (const w of surfaces) {
    if (w.kind !== 'walk' && w.kind !== 'crossing') continue;
    const [a, b] = [w.a, w.b], de = b[0] - a[0], dn = b[1] - a[1], L = Math.hypot(de, dn);
    if (!(L > 0.01)) continue;
    const ue = de / L, un = dn / L, half = w.width_m / 2;
    const side = (p, o) => [p[0] - un * o, p[1] + ue * o]; // o > 0: left of a→b
    if (w.kind === 'walk') {
      const la = side(a, half), lb = side(b, half), ra = side(a, -half), rb = side(b, -half);
      const streetLeft = walkStreetSide(w) === 1;
      // Kerb toward the street, from the roadway; lot side from the ground.
      if (streetLeft) S.vertical(lb, la, road - 0.02, w.y); else S.vertical(ra, rb, road - 0.02, w.y);
      if (!light) {
        if (streetLeft) S.vertical(ra, rb, ground - 0.02, w.y); else S.vertical(lb, la, ground - 0.02, w.y);
        S.vertical(la, ra, road - 0.02, w.y); S.vertical(rb, lb, road - 0.02, w.y); // end risers
      }
    } else {
      // A step at each end, 0.35 m out from the walk and half way down.
      const yStep = (w.y + walk) / 2;
      const d = Math.min(0.35, L / 4);
      for (const [p, dir] of [[a, 1], [b, -1]]) {
        const q = [p[0] + ue * d * dir, p[1] + un * d * dir];
        S.flat(p, q, w.width_m, yStep);
        const l = side(q, half), r = side(q, -half);
        if (dir > 0) S.vertical(r, l, w.y - 0.01, yStep); else S.vertical(l, r, w.y - 0.01, yStep);
      }
    }
  }
  return sink ? null : sinkGeometry(S);
}
