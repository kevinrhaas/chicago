import { t } from './strings/index.js';
import './strings/moment.js';
import './strings/notebook.js';

/** Mounted in the Navigator; only a shutter press allocates a photo. */
export function mountMoment(el, { api, doc = el?.ownerDocument, win = doc?.defaultView } = {}) {
  if (!el || !doc) return null;
  const node = (tag, key) => { const n = doc.createElement(tag); if (key) n.textContent = t(`moment.${key}`); return n; };
  const root = node('section'); root.className = 'moment-tools'; root.setAttribute('aria-label', t('moment.title'));
  const status = node('p'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const controls = node('div'); controls.className = 'moment-actions';
  const button = (key, run) => { const b = node('button', key); b.type = 'button'; b.addEventListener('click', run); controls.append(b); return b; };
  const preview = node('img'); preview.hidden = true; preview.className = 'moment-preview';
  const linkLabel = node('label', 'link');
  const link = node('input'); link.type = 'text'; link.readOnly = true; link.setAttribute('aria-label', t('moment.link'));
  linkLabel.append(link); linkLabel.hidden = true;
  let photo = null, objectURL = null, stopped = false;
  const clearPreview = () => { if (objectURL) win.URL.revokeObjectURL(objectURL); objectURL = null; photo = null; preview.removeAttribute('src'); preview.hidden = true; };
  const capture = button('capture', async () => {
    capture.disabled = true; save.disabled = true; notebook.disabled = true; status.textContent = t('moment.busy');
    try {
      const next = await api.moment.capture();
      if (stopped) return;
      clearPreview(); photo = next;
      objectURL = win.URL.createObjectURL(photo.blob); preview.src = objectURL;
      preview.alt = t('moment.alt', { place: photo.place, year: photo.year }); preview.hidden = false;
      link.value = photo.url; linkLabel.hidden = false;
      status.textContent = t('moment.ready'); capture.textContent = t('moment.retake');
    } catch { status.textContent = t('moment.failed'); }
    finally { capture.disabled = false; save.disabled = !photo; notebook.disabled = !photo; }
  });
  const save = button('download', () => {
    if (!photo || !objectURL) return;
    const a = node('a'); a.href = objectURL; a.download = `4d-chicago-${photo.year}.png`;
    doc.body.append(a); a.click(); a.remove();
  }); save.disabled = true;
  const notebook = button('notebook', async () => {
    if (!photo) return;
    notebook.disabled = true;
    try {
      const { saveNotebookPhoto } = await import('./field-notebook.js');
      const result = await saveNotebookPhoto(photo.blob, { title: photo.title, year: photo.year,
        place: photo.place, sources: photo.sources, link: photo.url });
      status.textContent = result.ok ? t('moment.saved')
        : t(`notebook.error.${result.reason}`, null, t('moment.failed'));
    } catch { status.textContent = t('moment.failed'); }
    finally { notebook.disabled = !photo; }
  }); notebook.disabled = true;
  button('copy', async () => {
    const url = photo?.url ?? api.moment.link();
    if (!url) { status.textContent = t('moment.notReady'); return; }
    link.value = url; linkLabel.hidden = false;
    try { await win.navigator.clipboard.writeText(url); status.textContent = t('moment.copied'); }
    catch { link.focus(); link.select(); status.textContent = t('moment.copyFallback'); }
  });
  root.append(node('h3', 'title'), node('p', 'note'), controls, status, preview, linkLabel); el.append(root);
  return { destroy() { stopped = true; clearPreview(); root.remove(); } };
}
