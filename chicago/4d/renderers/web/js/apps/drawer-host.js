/**
 * The drawer's sections, held by Navigator apps (T-2620, NAV-206; DESIGN §14 "App
 * registry": goto, people, businesses, evidence and settings mount inside apps and keep
 * their element ids).
 *
 * The drawer is gone, and its parts are not rebuilt: the one `#panel` element — its head
 * (back, title, close), its section tabs and its scroll column, with every section inside
 * it — moves into whichever app's screen is open, and that app shows only its own
 * sections' tabs. So every id the page, its modules and the smoke read still resolves,
 * every listener stays where it was bound, and `hud.setPanel` / `hud.selectTab` keep
 * their meaning (open a section, close it) through the adapter `install()` gives the HUD.
 *
 *   Jaunts    Go to                       (with Take a Jaunt above it)
 *   Move      Travel
 *   People    People · Businesses         (1835; 1904 has its own People screen)
 *   Guide     Controls · Evidence
 *   Settings  Settings · What's new       (What's new's dot rides the Settings icon)
 *
 * Each redesign is its own ticket (Jaunts/Go to E4, People, Settings T-2656, Evidence →
 * Guide T-2667); this moves the sections as they are.
 */

/** Which app holds each of the drawer's sections. */
export const SECTION_HOME = Object.freeze({
  goto: 'jaunts', travel: 'move', people: 'people', businesses: 'people',
  controls: 'guide', evidence: 'guide', settings: 'settings', whatsnew: 'settings',
});
export const APP_SECTIONS = Object.freeze(Object.entries(SECTION_HOME).reduce((m, [tab, app]) => {
  (m[app] ??= []).push(tab);
  return m;
}, {}));

const panelEl = (doc) => doc.getElementById('panel');

/** The tabs this app shows; the others are left in place but out of sight. */
function paintTabs(doc, appId) {
  const mine = new Set(APP_SECTIONS[appId] ?? []);
  let shown = 0;
  for (const tab of doc.querySelectorAll('.panel-tab[data-tab]')) {
    const here = mine.has(tab.dataset.tab);
    tab.classList.toggle('is-elsewhere', !here);
    if (here && !tab.hidden) shown++;
  }
  // One section needs no tab row of its own: the app's header already names it.
  panelEl(doc)?.classList.toggle('has-one-section', shown < 2);
}

/**
 * The part of an app that holds sections: `shown` moves #panel into this app's screen and
 * opens its section; `hidden` closes it when the app leaves the screen or the device docks.
 */
export function sectionScreen(appId, { lead = null } = {}) {
  return {
    mount(el, ctx) {
      const doc = el.ownerDocument;
      if (lead) {
        const row = lead(doc, ctx);
        if (row) el.append(row);
      }
      void doc;
    },
    shown(el, ctx) {
      const doc = el.ownerDocument;
      const panel = panelEl(doc);
      const hud = ctx.api?.hud;
      if (!panel || !hud) return;
      if (panel.parentElement !== el) el.append(panel);
      paintTabs(doc, appId);
      const mine = (APP_SECTIONS[appId] ?? []).filter((t) => !doc.querySelector(`.panel-tab[data-tab="${t}"]`)?.hidden);
      if (!mine.includes(hud.tab) && mine.length) hud.selectTab(mine[0], { fromHost: true });
      if (!hud.panelOpen()) hud.setPanel(true, { fromHost: true });
    },
    hidden(_el, ctx) {
      const hud = ctx.api?.hud;
      if (hud?.panelOpen()) hud.setPanel(false, { fromHost: true });
    },
  };
}

/**
 * Hand the HUD its adapter, and move What's new's dot onto the Settings icon. Called once
 * main.js has both the HUD and the Navigator.
 */
export function install({ hud, navigator, doc = globalThis.document }) {
  if (!hud || !navigator) return null;
  const appFor = (tab) => SECTION_HOME[tab] ?? null;
  // An app opened for the first time may mount asynchronously (People loads a module): a
  // close that arrives before it has finished must still win, so every open and close
  // is counted, and an open that finishes after a later close is put away again.
  let closes = 0;
  const openApp = (app) => {
    const before = closes;
    void Promise.resolve(navigator.select(app)).then(() => {
      if (before === closes) return;
      if (hud.panelOpen()) hud.setPanel(false, { fromHost: true });
      if (APP_SECTIONS[navigator.app]) navigator.dock();
    });
  };
  const adapter = {
    open(tab) {
      const app = appFor(tab);
      if (app) openApp(app);
    },
    close() {
      closes++;
      if (APP_SECTIONS[navigator.app]) navigator.dock();
    },
    show(tab) {
      const app = appFor(tab);
      if (app && app !== navigator.app) openApp(app);
      else if (app) paintTabs(doc, app);
    },
  };
  hud.setHost(adapter);
  // What's new's dot: the HUD keeps setting #help-dot; it now sits on the Settings icon.
  const dot = doc.getElementById('help-dot');
  const settings = doc.querySelector('#nav-rail [data-app="settings"]');
  if (dot && settings) {
    settings.querySelector('.nav-app-dot')?.remove();
    dot.className = 'nav-app-dot';
    settings.append(dot);
  }
  return adapter;
}
