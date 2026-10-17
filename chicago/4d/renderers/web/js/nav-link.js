/**
 * T-2621 — Navigator deep links and the Back button (design doc §14 "Deep links").
 *
 *   /1904/?nav=jaunts                       opens Jaunts after landing
 *   /1904/?nav=map                          opens the Map
 *   /1904/?nav=inspect:glessner_house&tab=design
 *                                           opens Inspect on that building (its Design tab
 *                                           once the dossier lands, T-2638)
 *
 * A teacher can share any screen this way. The link is read once, and acted on only
 * after the landing (main.js); an app the rail does not have, or an id or tab that is
 * not well formed, is dropped quietly — a stale link opens the town, never an error.
 *
 * Back closes the Navigator before it leaves the page: while the device is open or an
 * app other than Home is showing, one history entry is held for it; Back pops that entry
 * and closes the app (to Home, docked), and the next Back leaves as it always did.
 * Closing the device by hand gives the entry back, so Back never has to be pressed twice
 * for nothing.
 */

const APP = /^[a-z][a-z0-9-]{0,31}$/;
const ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$/;
const TAB = /^[a-z][a-z0-9-]{0,31}$/;

/** `{ app, id, tab }` from a location's search string, or null when there is no usable link. */
export function parseNavLink(search = '') {
  let params;
  try { params = new URLSearchParams(search); } catch { return null; }
  const raw = params.get('nav');
  if (!raw) return null;
  const [app, id = null, ...rest] = raw.split(':');
  if (!APP.test(app) || rest.length) return null;
  const tab = params.get('tab');
  return {
    app,
    id: id && ID.test(id) ? id : null,
    tab: tab && TAB.test(tab) ? tab : null,
  };
}

/** Whether the device holds a screen Back should close. */
export const navHoldsBack = (s) => !!s && (s.level > 0 || (!!s.app && s.app !== 'home'));

/**
 * Hold one history entry while the Navigator is open, and close it on Back.
 * `nav` is the device's api (onChange, closeApp); `win` the window.
 */
export function createNavHistory({ nav, win = globalThis } = {}) {
  if (!nav?.onChange || !win?.history?.pushState) return null;
  let held = false;      // our entry is on top of the history
  let skip = 0;          // popstates we caused ourselves, to be ignored
  let closing = false;   // closing because of Back, so do not give the entry back again
  const off = nav.onChange((state) => {
    if (navHoldsBack(state) && !held) {
      try {
        win.history.pushState({ ...(win.history.state ?? {}), c4dNavigator: true }, '', win.location?.href);
        held = true;
      } catch { /* a sandboxed frame may refuse; Back then leaves, as before */ }
    } else if (!navHoldsBack(state) && held && !closing) {
      held = false;
      skip += 1;
      win.history.back();
    }
  });
  const onPop = () => {
    if (skip > 0) { skip -= 1; return; }
    if (!held) return;
    held = false;
    closing = true;
    try { nav.closeApp(); } finally { closing = false; }
  };
  win.addEventListener?.('popstate', onPop);
  return {
    get held() { return held; },
    stop() { off?.(); win.removeEventListener?.('popstate', onPop); },
  };
}
