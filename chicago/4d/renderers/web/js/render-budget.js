/** T-2981 — a measured envelope for Full's active Ghost research views.
 * Draws: retained CI maximum8469 ×1.05, rounded up to100 =>8900.
 * T-3535 triangles: published desktop X-RAY 3737315 + the existing defended
 * 18059 margin, rounded up to5000 =>3760000 (was3675000 from T-2981).
 * Receipt: docs/RESEARCH/balanced-shadow-budget-3535/README.md.
 * This measured re-budget changes the allowance, not geometry or submitted work.
 * Normal/Tint, Balanced and Light retain their own existing ceilings; a higher
 * inspection allowance is never reduced. confidence.ghosting supplies the
 * active-view/visible-ghost condition, including hidden-grade restoration.
 */
export function renderBudget(base, detail, ghosting) {
  if (detail !== 'full' || ghosting !== true) return base;
  return { ...base,
    drawCalls: Math.max(base.drawCalls, 8900),
    triangles: Math.max(base.triangles, 3760000),
  };
}
