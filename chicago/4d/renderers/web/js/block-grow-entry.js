/**
 * block-grow-entry.js — the Map app's "Watch a block grow" entry (T-3676).
 *
 * A closed section under the map. Opened, it asks the page for the offered blocks
 * (`ctx.actions.blockGrow.blocks()`, read from the loaded 1904 records and nothing else)
 * and lists each with how many of its buildings have a recorded year; Watch this block
 * hands that block to the page, which docks the Navigator and puts the time-lapse bar
 * over the town (block-grow-view.js). Nothing is read until the section opens.
 */
import { t } from './strings/index.js';
import './strings/block-grow.js';

export function mountBlockGrowEntry(el, ctx = {}) {
  const doc = el.ownerDocument;
  if (doc.head && !doc.getElementById('block-grow-style')) {
    const css = doc.createElement('link'); css.id = 'block-grow-style'; css.rel = 'stylesheet';
    css.href = new URL('../css/block-grow.css', import.meta.url).href;
    doc.head.append(css);
  }
  const details = doc.createElement('details'); details.id = 'nav-block-grow';
  const summary = doc.createElement('summary'); summary.textContent = t('blockgrow.title');
  const body = doc.createElement('div'); body.className = 'nav-block-grow';
  details.append(summary, body); el.append(details);
  const p = (key, vars) => { const x = doc.createElement('p'); x.textContent = t(`blockgrow.${key}`, vars); return x; };
  let filled = false;
  details.addEventListener('toggle', async () => {
    if (!details.open || filled) return;
    filled = true;
    body.replaceChildren(p('intro'));
    const actions = ctx.actions?.blockGrow;
    if (!actions?.available) { body.append(p('only1904')); return; }
    const status = p('loading'); status.setAttribute('role', 'status'); body.append(status);
    let blocks = [];
    try { blocks = await actions.blocks(); } catch { status.textContent = t('blockgrow.unavailable'); filled = false; return; }
    status.remove();
    if (!blocks.length) { body.append(p('none')); return; }
    const list = doc.createElement('ul');
    for (const b of blocks) {
      const li = doc.createElement('li');
      const text = doc.createElement('div');
      const name = doc.createElement('strong'); name.textContent = b.title;
      const sub = doc.createElement('span'); sub.textContent = t('blockgrow.counts', { dated: b.dated, undated: b.undated });
      text.append(name, sub);
      const go = doc.createElement('button'); go.type = 'button'; go.textContent = t('blockgrow.start');
      go.dataset.block = b.id;
      go.setAttribute('aria-label', `${t('blockgrow.start')}: ${b.title}`);
      go.addEventListener('click', () => { void actions.open(b.id); });
      li.append(text, go); list.append(li);
    }
    body.append(list);
  });
  return { destroy() { details.remove(); } };
}
