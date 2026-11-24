const c = api.jauntStage.snapshot().cast.filter(a => !a.hidden && a.drawn !== false && Math.abs(a.e - 1141) < 9);
let hx = 0, hy = 0; for (const a of c) { if (!Number.isFinite(a.heading)) continue; const r = a.heading * Math.PI / 180; hx += Math.sin(r); hy += Math.cos(r); }
const L = Math.hypot(hx, hy), fx = L > 1e-3 ? hx / L : 0, fy = L > 1e-3 ? hy / L : -1;
if (!c.length) return null;
const along = c.map(a => a.e * fx + a.n * fy).sort((x, y) => x - y);
const q = p => along[Math.min(along.length - 1, Math.max(0, Math.round(p * (along.length - 1))))];
const tail = q(0.02), head = q(0.98);
let ce = 0, cn = 0; for (const a of c) { ce += a.e; cn += a.n; } ce /= c.length; cn /= c.length;
const mid = ce * fx + cn * fy;
const sm = (a, b, x) => { const t = Math.max(0, Math.min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const w = sm(0.58, 1.0, u);
const sD = 0.02 + 0.96 * sm(0, 0.62, u) ;
const s = sD * (1 - w) + 0.55 * w;
const at = tail + (head - tail) * s;
const e = ce + (at - mid) * fx, n = cn + (at - mid) * fy;
return { e, n, heading: Math.atan2(fx, fy) * 180 / Math.PI,
  offset: { back: -2 + 20 * w, side: -7 * (1 - w) - 1.5 * w, alt: 1.9 + 22 * w }, look_h: 1.3 * (1 - w) };
