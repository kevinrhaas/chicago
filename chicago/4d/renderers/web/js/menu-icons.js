/** T-2120: the arrival menu's line icons — engraved-plate shapes, one stroke, currentColor.
 *  Jaunt types, travel modes, quick starts and the three arrival choices draw from here. */
const P = {
  // Shared person actions: simple strokes remain clear at the phone's 18 px size.
  greet: '<circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M17 5l2-2M18 9h3M17 13l2 2"/>',
  chat: '<path d="M4 4h16v12H9l-5 4z"/><path d="M8 8h8M8 12h5"/>',
  enter: '<path d="M13 3h7v18h-7M3 12h12M10 7l5 5-5 5"/>',
  garden: '<path d="M12 21V11M12 15C5 15 3 11 3 6c6 0 9 3 9 9M12 11c0-5 3-8 9-8 0 5-3 8-9 8"/>',
  food: '<path d="M3 12h18a9 9 0 0 1-18 0zM8 21h8M8 8V3M12 8V3M16 8V3"/>',
  // jaunt families (catalog `primary_family`)
  'Wayfinding': '<circle cx="12" cy="12" r="8.5"/><path d="M12 5.5l2.4 6.5-2.4 6.5-2.4-6.5z"/><path d="M12 2v1.5M12 20.5V22M2 12h1.5M20.5 12H22"/>',
  'Provisions': '<path d="M7.5 3.5h9c1.6 2.8 1.6 14.2 0 17h-9c-1.6-2.8-1.6-14.2 0-17z"/><path d="M6.4 8.5h11.2M6.4 15.5h11.2"/>',
  'Neighbors': '<path d="M3.5 11.5L12 5l8.5 6.5"/><path d="M5.5 10v10h13V10"/><path d="M10.5 20v-5h3v5"/><path d="M15.5 7.2V4h2v4.8"/>',
  'Livelihood': '<path d="M3.5 7.5h12c.3 2.4 2.2 3.4 5 3.4v1.4c-3 .1-4.8 1-5.3 3.2H9.6c-.3-3-2.5-4.9-6.1-5.4z"/><path d="M9.5 15.5v2.5M14.5 15.5v2.5M6.5 20.5h11"/>',
  'News & Knowledge': '<path d="M20 3.5C13 4.5 9 9.5 8 17"/><path d="M20 3.5c-.6 6.2-5 11.4-12 13.5"/><path d="M8 17l-2.5 3.5"/><path d="M12.5 20.5h7"/>',
  // travel modes (travel-settings PACES)
  walk: '<path d="M8.5 3.5h4v9l4.6 2.3c1.6.8 2.4 1.9 2.4 3.2v1.5h-14V16l3-3z"/><path d="M5.5 17.5h14"/>',
  wagon: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="1.6"/><path d="M12 4v6.4M12 13.6V20M4 12h6.4M13.6 12H20M6.3 6.3l4.6 4.6M13.1 13.1l4.6 4.6M17.7 6.3l-4.6 4.6M10.9 13.1l-4.6 4.6"/>',
  horse: '<path d="M7 20.5V11a5 5 0 0 1 10 0v9.5" stroke-width="2.6"/><path d="M5.5 20.5h3M15.5 20.5h3"/>',
  fly: '<path d="M2.5 12.5c3-3.2 6.3-3.2 9.5 0 3.2-3.2 6.5-3.2 9.5 0"/><path d="M7 17.5c1.6-1.5 3.4-1.5 5 0"/>',
  instantly: '<path d="M13.5 2.5L6 13.5h5.5l-1 8 7.5-11h-5.5z"/>',
  // quick starts
  aerial: '<path d="M4.5 8c1.8-1.8 3.7-1.8 5.5 0 1.8-1.8 3.7-1.8 5.5 0"/><path d="M2.5 20.5h19M4 20.5v-4l2.5-2.5 2.5 2.5v4M11 20.5v-6l2.5-2.5 2.5 2.5v6M18 20.5v-3l1.5-1.5"/>',
  fort: '<path d="M7.5 20.5v-9h9v9"/><path d="M6 11.5l6-4.5 6 4.5"/><path d="M12 7V2.5l3.5 1.2L12 5"/><path d="M2.5 20.5h19M3.5 20.5v-5M5.5 20.5v-5M18.5 20.5v-5M20.5 20.5v-5"/>',
  forks: '<path d="M12 21.5v-8.5C12 9 8 6.5 3.5 3.5M12 13c0-4 4-6.5 8.5-9.5" stroke-width="2.4"/>',
  street: '<path d="M2.5 20.5h19"/><path d="M3.5 20.5V10l3-3 3 3v10.5M9.5 20.5V8h5v12.5M14.5 20.5v-9l3-3 3 3v9"/><path d="M11 20.5v-3h2v3"/>',
  wharf: '<path d="M3 14.5h18l-3 4.5H6z"/><path d="M9.5 14.5v-11M15 14.5V5.5"/><path d="M9.5 4.5l-4.5 8h4.5M15 6.5l4.5 6.5H15"/>',
  // T-3436: 1904's viewpoints, each its own glyph instead of the one eye.
  arch: '<path d="M2.5 20.5h19"/><path d="M4 20.5V11a8 8 0 0 1 16 0v9.5"/><path d="M8.5 20.5V12.5a3.5 3.5 0 0 1 7 0v8"/>',
  mansion: '<path d="M2.5 20.5h19"/><path d="M4.5 20.5v-10h15v10"/><path d="M3.5 10.5L6 6.5h12l2.5 4"/><path d="M9.5 6.5V3.5h5v3"/><path d="M10.5 20.5v-4h3v4"/><path d="M7 13h2M15 13h2"/>',
  mansard: '<path d="M2.5 20.5h19"/><path d="M5 20.5v-9h14v9"/><path d="M4 11.5l1.8-5h12.4l1.8 5"/><path d="M8.5 9v-2.5M12 9v-2.5M15.5 9v-2.5"/><path d="M8 14.5h2v2.5H8zM14 14.5h2v2.5h-2z"/>',
  church: '<path d="M12 2.5V6M10.3 4.1h3.4"/><path d="M9 11l3-5 3 5"/><path d="M9 11v9.5h6V11"/><path d="M15 13.5h5v7h-5M9 13.5H4v7h5"/><path d="M11 20.5v-2.5a1 1 0 0 1 2 0v2.5"/>',
  ghost: '<path d="M6 20.5V10a6 6 0 0 1 12 0v10.5l-2-1.5-2 1.5-2-1.5-2 1.5-2-1.5z"/><circle cx="10" cy="10.5" r=".9"/><circle cx="14" cy="10.5" r=".9"/>',
  door: '<path d="M3.5 20.5h17"/><path d="M6.5 20.5V8a5.5 5.5 0 0 1 11 0v12.5"/><path d="M12 20.5V9"/><circle cx="10.3" cy="14.5" r=".7"/>',
  gate: '<path d="M4 20.5V5M20 20.5V5"/><path d="M4 8.5c3 1.5 13 1.5 16 0M4 17.5h16M8 9.5v8M12 9.8v7.7M16 9.5v8"/>',
  court: '<path d="M3.5 20.5V3.5h17v17z"/><path d="M8.5 20.5v-12h12"/><path d="M13 13h3v3h-3z"/>',
  stable: '<path d="M3.5 20.5V10L12 4.5l8.5 5.5v10.5"/><path d="M8.5 20.5v-6.5h7v6.5"/><path d="M8.5 14l7 6.5M15.5 14l-7 6.5"/><path d="M10.5 9h3"/>',
  wall: '<path d="M3 5.5h18v13H3z"/><path d="M3 9.8h18M3 14.2h18M9 5.5v4.3M15 5.5v4.3M6 9.8v4.4M12 9.8v4.4M18 9.8v4.4M9 14.2v4.3M15 14.2v4.3"/>',
  corner: '<path d="M2.5 9h6.5V2.5M15 2.5V9h6.5M2.5 15h6.5v6.5M15 21.5V15h6.5"/>',
  view: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
  // the arrival's three choices
  jaunts: '<circle cx="5.5" cy="18.5" r="2"/><path d="M7.5 18.5h4.5a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h7.5"/><path d="M16.5 10V2.5l4 1.8-4 1.8"/>',
  start: '<path d="M12 21.5s-6.5-6.4-6.5-11.5a6.5 6.5 0 0 1 13 0c0 5.1-6.5 11.5-6.5 11.5z"/><circle cx="12" cy="10" r="2.4"/>',
  explore: '<circle cx="12" cy="12" r="8.5"/><path d="M15.8 8.2l-2 5.6-5.6 2 2-5.6z"/>',
  back: '<path d="M14.5 5.5L8 12l6.5 6.5"/>',
  more: '<path d="M6.5 9.5L12 15l5.5-5.5"/>',
  play: '<path d="M8 5.5v13l10-6.5z"/>',
  search: '<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5.5 5.5"/>',
  // T-2561: keep a year on this device, and the year kept
  keep: '<path d="M12 3.5v11"/><path d="M7.5 10.5l4.5 4.5 4.5-4.5"/><path d="M4.5 15.5v4h15v-4"/>',
  kept: '<path d="M4.5 15.5v4h15v-4"/><path d="M7.5 9l3 3 6-6.5"/>',
  // T-3432: the jaunt's welcome page, its last stop and its finish
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3.5 2"/>',
  day: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M18.7 5.3l-1.8 1.8M7.1 16.9l-1.8 1.8"/>',
  night: '<path d="M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z"/>',
  story: '<path d="M12 6.5c-2.5-1.6-5.5-2-8.5-1.5v13c3-.5 6-.1 8.5 1.5 2.5-1.6 5.5-2 8.5-1.5V5c-3-.5-6-.1-8.5 1.5z"/><path d="M12 6.5v13"/>',
  finish: '<path d="M5.5 21.5V3.5"/><path d="M5.5 4h13l-3 4 3 4h-13"/>',
  close: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
  done: '<circle cx="12" cy="12" r="8.5"/><path d="M8 12.3l2.8 2.8L16.3 9"/>',
};
export function iconSvg(name, size = 20) {
  const body = P[name] || P.view;
  return `<svg class="menu-icon" viewBox="0 0 24 24" width="${size}" height="${size}" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">${body}</svg>`;
}
export function icon(name, size) {
  const t = document.createElement('template'); t.innerHTML = iconSvg(name, size); return t.content.firstChild;
}
/** A jaunt's type: its catalog family, with the colour slot styles key on. */
export const FAMILIES = ['Wayfinding', 'Provisions', 'Neighbors', 'Livelihood', 'News & Knowledge'];
export const familySlot = family => {
  const i = FAMILIES.indexOf(family); return i < 0 ? 'other' : ['way', 'prov', 'neigh', 'live', 'news'][i];
};
