/**
 * Home (SCR 01): where you are, what is in front of you, the Jaunt in progress,
 * Move and the Confidence view. Its screen is the static #nav-home that navigator.js
 * paints (T-2617); it ships in the boot payload, as DESIGN §14 asks of Home alone.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
import { t } from '../strings/index.js';
import '../strings/moment.js';
import '../strings/photo-hunt.js';
const momentPanels = new WeakMap();
const navigatorVisible = ctx => {
  const level = ctx?.navigator?.level;
  return Number.isFinite(level) ? level > 0 : true;
};

export default {
  id: 'home',
  label: 'Home',
  code: 'SCR 01 · HOME',
  order: 0,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 11 12 4l8 7"/><path d="M6 9.5V20h12V9.5"/><path d="M10 20v-5h4v5"/></svg>',
  panel: 'nav-home',
  mount(el, ctx) {
    const doc = el.ownerDocument;
    const details = doc.createElement('details'); details.id = 'nav-moment';
    const summary = doc.createElement('summary'); summary.textContent = t('moment.title');
    details.append(summary); el.append(details);
    const state = { view: null, loading: false, live: true }; momentPanels.set(el, state);
    details.addEventListener('toggle', async () => {
      if (!details.open || state.view || state.loading) return;
      state.loading = true;
      try {
        const { mountMoment } = await import('../moment-view.js');
        if (state.live) state.view = mountMoment(details, { api: ctx.api });
      } catch {
        const message = doc.createElement('p'); message.setAttribute('role', 'status');
        message.textContent = t('moment.failed'); details.append(message);
      } finally { state.loading = false; }
    });
    const hunt = doc.createElement('details'); hunt.id = 'nav-photo-hunt';
    const huntSummary = doc.createElement('summary'); huntSummary.textContent = t('hunt.title');
    hunt.append(huntSummary); el.append(hunt);
    state.ctx = ctx; state.on = navigatorVisible(ctx); state.hunt = null; state.huntLoading = false;
    hunt.addEventListener('toggle', async () => {
      state.hunt?.setVisible(hunt.open && state.on);
      if (!hunt.open || state.hunt || state.huntLoading) return;
      state.huntLoading = true;
      try {
        const { mountPhotoHunt } = await import('../photo-hunt-view.js');
        if (state.live) {
          state.hunt = mountPhotoHunt(hunt, { context: () => state.ctx });
          state.hunt.setVisible(hunt.open && state.on);
        }
      } catch {
        const message = doc.createElement('p'); message.setAttribute('role', 'status');
        message.textContent = t('hunt.unavailable'); hunt.append(message);
      } finally { state.huntLoading = false; }
    });
    // A challenge link uses the ordinary Home deep link and its existing arrival flow.
    if (new URLSearchParams(doc.defaultView?.location?.search).has('hunt')) hunt.open = true;
  },
  shown(el, ctx) {
    const state = momentPanels.get(el);
    if (state) {
      state.ctx = ctx;
      // A quiet rail selection also calls shown while the Navigator remains docked.
      state.on = navigatorVisible(ctx);
      state.hunt?.setVisible(state.on && !!el.querySelector('#nav-photo-hunt')?.open);
    }
  },
  hidden(el) {
    const state = momentPanels.get(el);
    if (state) { state.on = false; state.hunt?.setVisible(false); }
  },
  unmount(el) {
    const state = momentPanels.get(el);
    if (state) { state.live = false; state.view?.destroy(); state.hunt?.destroy(); }
    el.querySelector('#nav-photo-hunt')?.remove();
    el.querySelector('#nav-moment')?.remove(); momentPanels.delete(el);
  },
};
