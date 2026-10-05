/** T-2120: the arrival menu's line icons — engraved-plate shapes, one stroke, currentColor.
 *  Jaunt types, travel modes, quick starts and the three arrival choices draw from here. */
const P = {
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
  view: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
  // the arrival's three choices
  jaunts: '<circle cx="5.5" cy="18.5" r="2"/><path d="M7.5 18.5h4.5a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h7.5"/><path d="M16.5 10V2.5l4 1.8-4 1.8"/>',
  start: '<path d="M12 21.5s-6.5-6.4-6.5-11.5a6.5 6.5 0 0 1 13 0c0 5.1-6.5 11.5-6.5 11.5z"/><circle cx="12" cy="10" r="2.4"/>',
  explore: '<circle cx="12" cy="12" r="8.5"/><path d="M15.8 8.2l-2 5.6-5.6 2 2-5.6z"/>',
  back: '<path d="M14.5 5.5L8 12l6.5 6.5"/>',
  more: '<path d="M6.5 9.5L12 15l5.5-5.5"/>',
  play: '<path d="M8 5.5v13l10-6.5z"/>',
  search: '<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5.5 5.5"/>',
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
