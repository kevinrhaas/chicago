// Follow one person walking near the Glessner corner, picked on the first frame (T-3744).
const A = (api.humans?.actors ?? []).filter(a => a && Number.isFinite(a.e) && Number.isFinite(a.n));
if (!window.__t3744pick) {
  const near = A.map(a => ({ a, d: Math.hypot(a.e - 1398, a.n + 3215) })).filter(x => x.d < 70).sort((x, y) => x.d - y.d);
  const moving = near.find(x => x.a.moving || x.a.speed > 0.2 || x.a.state === 'walk') ?? near[0];
  window.__t3744pick = moving?.a?.id ?? moving?.a?.personId ?? null;
  window.__t3744actor = moving?.a ?? null;
}
const a = A.find(x => (x.id ?? x.personId) === window.__t3744pick) ?? window.__t3744actor;
return a ? { e: a.e, n: a.n, heading: a.heading } : null;
