/**
 * The viewport in layout pixels, before browser magnification (T-3658).
 * URL-bar and keyboard changes still resize the available space. Pinching only
 * magnifies that space: using the smaller visual viewport directly would shrink
 * the canvas and Navigator a second time while the browser was enlarging them.
 */
export function viewportSize(win = window) {
  const vv = win.visualViewport;
  const scale = Number.isFinite(vv?.scale) && vv.scale > 0 ? vv.scale : 1;
  const dimension = (visual, fallback) => Math.max(1, Math.round(
    Number.isFinite(visual) && visual > 0 ? visual * scale : fallback || 1,
  ));
  return {
    width: dimension(vv?.width, win.innerWidth),
    height: dimension(vv?.height, win.innerHeight),
    scale,
  };
}
