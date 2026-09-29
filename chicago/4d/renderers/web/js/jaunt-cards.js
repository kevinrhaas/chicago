/** Use the existing cards; this adapter owns only their outing lifetime and fallback. */
export function createJauntCards({ registry, popup, hud, api, sources, onReturn }) {
  const fallback = document.createElement('section'); fallback.id = 'jaunt-context-card';
  fallback.className = 'jaunt-context-card'; fallback.hidden = true;
  fallback.setAttribute('aria-label', 'Optional historical context');
  const heading = document.createElement('h2'), message = document.createElement('p'), back = document.createElement('button');
  heading.textContent = 'No card yet'; message.textContent = 'This detail is unavailable. Your outing is unchanged.';
  back.type = 'button'; back.textContent = 'Return to outing'; back.addEventListener('click', onReturn);
  fallback.append(heading, message, back); document.body.append(fallback);
  let owned = null;
  function close() {
    const previous = owned; owned = null;
    if (previous === 'source' || previous === 'topic') api.sources?.cancel?.();
    if (previous === 'person') api.people?.close();
    if (previous === 'business') api.businesses?.close();
    popup.close(); hud.setPanel(false); fallback.hidden = true;
  }
  async function open(link, { signal }) {
    if (signal.aborted) return;
    if (document.pointerLockElement) document.exitPointerLock?.();
    owned = link.kind;
    let ok = false;
    try {
      if (link.kind === 'structure') {
        hud.setPanel(false);
        const record = registry.get(link.id);
        ok = !!record && popup.show(record);
      } else if (['person', 'business'].includes(link.kind)) {
        const tab = link.kind === 'person' ? 'people' : 'businesses';
        popup.close(); hud.setPanel(true); hud.selectTab(tab);
        document.getElementById(`${tab}-directory`)?.addEventListener('source-card-close', onReturn, { signal, once: true });
        ok = await api[tab]?.open(link.id, { signal });
      } else if (link.kind === 'source' || link.kind === 'topic') {
        popup.close(); hud.setPanel(true); hud.selectTab('evidence');
        const topic = link.kind === 'source' ? 'sources' : link.id;
        ok = [...document.querySelectorAll('[data-topic]')].some(el => el.dataset.topic === topic);
        if (ok) api.evidenceHub.showTopic(topic);
        if (ok && link.kind === 'source') {
          const view = await sources();
          if (signal.aborted) return;
          ok = await view?.open(link.id, { signal });
        }
      }
    } catch { ok = false; }
    if (signal.aborted) return;
    if (!ok) {
      popup.close(); hud.setPanel(false); fallback.hidden = false; back.focus({ preventScroll: true });
    }
  }
  return { open, close, destroy() { close(); fallback.remove(); } };
}
