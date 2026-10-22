/** T-2981 — a measured envelope for Full's active Ghost research views.
 * Draws: retained CI maximum8469 ×1.05, rounded up to100 =>8900.
 * Triangles: paired-parent Xray3656436 + defended18059, rounded up to5000
 * =>3675000. This changes the allowance, not geometry, draw units or work.
 * Normal/Tint, Balanced and Light retain their own existing ceilings; a higher
 * inspection allowance is never reduced. confidence.ghosting supplies the
 * active-view/visible-ghost condition, including hidden-grade restoration.
 */
export function renderBudget(base, detail, ghosting) {
  if (detail !== 'full' || ghosting !== true) return base;
  return { ...base,
    drawCalls: Math.max(base.drawCalls, 8900),
    triangles: Math.max(base.triangles, 3675000),
  };
}
