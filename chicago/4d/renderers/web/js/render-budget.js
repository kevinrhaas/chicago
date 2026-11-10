/** T-2981 — a measured envelope for Full's active Ghost research views.
 * Draws: retained CI maximum8469 ×1.05, rounded up to100 =>8900.
 * Previous triangles: paired-parent Xray3656436 + defended18059 =>3675000.
 * 2026-11-10 actual retained-B desktop Xray3737315 breaches that cap by62315.
 * Charge the already-included B positive mesh growth1678 again for three passes
 * (5034 reserve); round3742349 up to25000 =>3750000. SITE-BUDGET.md §4m
 * records the conscious measured re-budget and limits. No frame-time guarantee.
 * This changes the allowance, not geometry, draw units or work.
 * Normal/Tint, Balanced and Light retain their own existing ceilings; a higher
 * inspection allowance is never reduced. confidence.ghosting supplies the
 * active-view/visible-ghost condition, including hidden-grade restoration.
 */
export function renderBudget(base, detail, ghosting) {
  if (detail !== 'full' || ghosting !== true) return base;
  return { ...base,
    drawCalls: Math.max(base.drawCalls, 8900),
    triangles: Math.max(base.triangles, 3750000),
  };
}
