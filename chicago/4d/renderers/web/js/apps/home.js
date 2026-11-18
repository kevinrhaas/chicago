/**
 * Home (SCR 01): where you are, what is in front of you, the Jaunt in progress,
 * Move and the Confidence view. Its screen is the static #nav-home that navigator.js
 * paints (T-2617); it ships in the boot payload, as DESIGN §14 asks of Home alone.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
import { t } from '../strings/index.js';
import '../strings/moment.js';
const momentPanels = new WeakMap();

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
  },
  unmount(el) {
    const state = momentPanels.get(el);
    if (state) { state.live = false; state.view?.destroy(); }
    el.querySelector('#nav-moment')?.remove(); momentPanels.delete(el);
  },
};
