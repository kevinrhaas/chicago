/**
 * T-2094's corridor bands as plain arithmetic over plain records, so the page
 * (streets.js `verge`) and a job-pool worker (flora-ground.js, T-2696) answer
 * the same question with the same code. A worker cannot import streets.js: it
 * imports three, a bare specifier no worker resolves.
 *
 * A record is the four fields `verge` reads of streets.js's prepared street:
 * `bounds` ({e0, e1, n0, n1}, the corridor's padded box), `path` (its control
 * line, [e, n] points), `drawn_width_m` and `corridor_width_m`.
 */

/** The records a worker is sent: those four fields of each prepared street. */
export function vergeRecords(prepared) {
  return prepared.map((r) => ({ bounds: r.bounds, path: r.path,
    drawn_width_m: r.drawn_width_m, corridor_width_m: r.corridor_width_m }));
}

/**
 * Where (e, n) stands in the opened corridors `records`: `{band: 'worked',
 * edgeM: null}` inside a drawn roadway, `{band: 'verge', edgeM}` between it and
 * the corridor's edge (`edgeM` in from that edge, the largest of every corridor
 * reaching it), or null outside every one. The distance to a street is the
 * nearest of its segments, by streets.js `pointSegment`'s own arithmetic.
 */
export function vergeAt(records, e, n) {
  let best = null;
  for (const street of records) {
    const b = street.bounds;
    if (e < b.e0 || e > b.e1 || n < b.n0 || n > b.n1) continue;
    const path = street.path;
    let distance = Infinity;
    for (let i = 1; i < path.length; i++) {
      const a = path[i - 1];
      const c = path[i];
      const dx = c[0] - a[0];
      const dn = c[1] - a[1];
      const len2 = dx * dx + dn * dn || 1e-9;
      const t = Math.max(0, Math.min(1, ((e - a[0]) * dx + (n - a[1]) * dn) / len2));
      const d = Math.hypot(e - (a[0] + dx * t), n - (a[1] + dn * t));
      if (d < distance) distance = d;
    }
    if (distance === Infinity) continue;
    if (distance <= street.drawn_width_m * 0.5) return { band: 'worked', edgeM: null };
    const edgeM = street.corridor_width_m * 0.5 - distance;
    if (edgeM >= 0 && (!best || edgeM > best.edgeM)) best = { band: 'verge', edgeM };
  }
  return best;
}
