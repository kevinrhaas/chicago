/** T-2981 — a measured envelope for Full's active Ghost research views.
 * Draws: retained CI maximum8469 ×1.05, rounded up to100 =>8900.
 * PR1910 independently qualified the stricter3750000 allowance from this same
 * reading plus5034 reserve. Concurrent T-3535 retains the defended18059 margin:
 * T-3535 triangles: published desktop X-RAY 3737315 + the existing defended
 * 18059 margin, rounded up to5000 =>3760000 (was3675000 from T-2981).
 * Receipt: docs/RESEARCH/balanced-shadow-budget-3535/README.md.
 * Retain that already-adopted3760000 allowance during integration. Both pricing
 * receipts remain valid; this is not a new frame-time guarantee. The allowance
 * changes no geometry or submitted work.
 * T-3556 (2026-11-15), a conscious re-budget: the 1835 townspeople now come out of their
 * doors about the visitor, and the desktop smoke's Full X-RAY stand read 3764962 with two of
 * them out at their far rung (Peck's and Mahoney's bodies, 13836 + 13811 = 27647 triangles,
 * exactly the rise over 3737315). That reading + the same defended 18059 margin, rounded up
 * to 5000 => 3785000. People are core on every device (owner, 2026-11-10), so the
 * allowance moves rather than the town. Receipt: PR #2088.
 * Normal/Tint, Balanced and Light retain their own existing ceilings; a higher
 * inspection allowance is never reduced. confidence.ghosting supplies the
 * active-view/visible-ghost condition, including hidden-grade restoration.
 */
export function renderBudget(base, detail, ghosting) {
  if (detail !== 'full' || ghosting !== true) return base;
  return { ...base,
    drawCalls: Math.max(base.drawCalls, 8900),
    triangles: Math.max(base.triangles, 3785000),
  };
}
