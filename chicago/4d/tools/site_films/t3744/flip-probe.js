// T-3744: log every person within 25 m of (1398, -3215) who turns or moves more than a walk allows in one
// 24 fps frame, while the camera circles them in the air (run as an eval job of site_films.mjs).
const T = window.__probeT ?? '16:30';
api.timeOfDay.set(T); for (let i = 0; i < 4; i++) api.step();
const C = { e: 1398, n: -3215 };
const wrap = d => Math.abs(((d % 360) + 540) % 360 - 180);
const out = [], prev = new Map(), seen = new Set();
window.__film.freeze();
const N = 24 * 24;
for (let k = 0; k < N; k++) {
  window.__film.advance(1000 / 24);
  const ang = (k / N) * Math.PI * 1.2 - 0.6, R = 6 + 3 * Math.sin(k / N * Math.PI);
  const e = C.e + R * Math.sin(ang), n = C.n - R * Math.cos(ang);
  api.setFly(true);
  api.walker.teleport({ local_e: e, local_n: n, yaw_deg: (Math.atan2(C.e - e, C.n - n) * 180 / Math.PI + 360) % 360, pitch_deg: 0, altitude_m: 1.7 });
  api.step();
  for (const a of (api.humans?.actors ?? [])) {
    if (!a || !Number.isFinite(a.e) || Math.hypot(a.e - C.e, a.n - C.n) > 25) continue;
    const id = String(a.personId ?? a.id);
    seen.add(id);
    const rec = { h: +a.heading?.toFixed?.(1), ry: +((a.root?.rotation?.y ?? 0) * 180 / Math.PI).toFixed(1), vis: !!a.root?.visible,
      e: +a.e.toFixed(2), n: +a.n.toFixed(2), st: a.state, lod: a.lod ?? a.currentLod ?? null, path: !!a.path, inR: !!a.inRange,
      mode: a.__mode ?? null, ch: a.root?.children?.length ?? 0 };
    const pv = prev.get(id);
    if (pv) {
      const dh = wrap(rec.h - pv.h), dry = wrap(rec.ry - pv.ry), dp = Math.hypot(rec.e - pv.e, rec.n - pv.n);
      if (dh > 12 || dry > 12 || dp > 0.4 || rec.vis !== pv.vis || rec.lod !== pv.lod || rec.ch !== pv.ch)
        out.push({ k, id, dh: +dh.toFixed(1), dry: +dry.toFixed(1), dp: +dp.toFixed(2), from: pv, to: rec });
    }
    prev.set(id, rec);
  }
}
window.__film.release();
return { time: api.timeOfDay.current.hhmm, actors: [...seen], events: out.slice(0, 300), total: out.length };
