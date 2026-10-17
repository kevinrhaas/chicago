/**
 * Settings (SCR 10): display, comfort, performance, machine skin, units, sound,
 * About & What's new. Pinned to the foot.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
export default {
  id: 'settings',
  label: 'Settings',
  code: 'SCR 10 · SETTINGS',
  order: 100,
  pin: 'bottom',
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h10M18 7h2M4 12h2M10 12h10M4 17h8M16 17h4"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="12" r="2"/><circle cx="14" cy="17" r="2"/></svg>',
  // What's new's unread dot shows here (§06).
  badge: (ctx) => !!ctx.whatsNewUnread,
  // Stub until the Settings app lands: the drawer's Settings section.
  launch: (ctx) => ctx.actions?.openSection?.('settings'),
};
