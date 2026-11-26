/**
 * Settings › Display › Language (gap analysis item 15: Spanish). Built here, not in index.html:
 * the page is copied to every year's door and sits at validate.py's 64 KiB duplicate floor
 * (T-0722), so it carries none of this row's bytes. Choosing reloads the page in that language
 * (js/strings/index.js § chooseLanguage).
 *
 * T-3757 (Kevin, 2026-11-26): "Warn users in both languages that changing the language will
 * restart the application." The row says so under the menu, in English and Spanish at once, and
 * a new choice asks once, in both, before the page restarts: a stray tap costs nothing.
 */
import { LANG, LANGUAGES, chooseLanguage } from './strings/index.js';

/** The warning, in both languages whichever is in force: the visitor may read only the other. */
export const RESTART_WORDS = Object.freeze({
  note: 'Changing the language restarts the app. · Cambiar el idioma reinicia la aplicación.',
  ask: (label) => `Restart in ${label}? Anything not saved is lost. · ¿Reiniciar en ${label}? Lo que no esté guardado se pierde.`,
  go: 'Restart · Reiniciar',
  stay: 'Cancel · Cancelar',
});

export function languageRow(after, { choose = chooseLanguage } = {}) {
  if (!after || document.getElementById('s-language')) return null;
  const row = document.createElement('label');
  row.className = 'field row';
  row.id = 'row-language';
  const name = document.createElement('span');
  // Each language names itself, and the row's name is in both while either is in force, so a
  // visitor who cannot read the language in force can still find the way back.
  name.textContent = 'Language · Idioma';
  name.setAttribute('translate', 'no');
  const sel = document.createElement('select');
  sel.id = 's-language';
  sel.setAttribute('translate', 'no');
  for (const [code, label] of LANGUAGES) {
    const opt = document.createElement('option');
    opt.value = code;
    opt.textContent = label;
    opt.lang = code;
    sel.append(opt);
  }
  sel.value = LANG;
  row.append(name, sel);

  // The standing note, and the question a new choice asks (hidden until then).
  const note = document.createElement('p');
  note.className = 'legend-note language-note';
  note.id = 'language-restart-note';
  note.setAttribute('translate', 'no');
  note.textContent = RESTART_WORDS.note;
  sel.setAttribute('aria-describedby', note.id);
  const ask = document.createElement('div');
  ask.className = 'language-ask';
  ask.id = 'language-restart-ask';
  ask.setAttribute('translate', 'no');
  ask.setAttribute('role', 'alertdialog');
  ask.hidden = true;
  const question = document.createElement('p');
  question.className = 'legend-note language-ask-text';
  question.id = 'language-restart-question';
  ask.setAttribute('aria-labelledby', question.id);
  const go = document.createElement('button');
  go.type = 'button'; go.className = 'setting-button language-ask-go'; go.textContent = RESTART_WORDS.go;
  const stay = document.createElement('button');
  stay.type = 'button'; stay.className = 'setting-button language-ask-stay'; stay.textContent = RESTART_WORDS.stay;
  const actions = document.createElement('span');
  actions.className = 'pack-settings-actions';
  actions.append(go, stay);
  ask.append(question, actions);

  let wanted = null;
  const close = () => { ask.hidden = true; wanted = null; note.hidden = false; };
  sel.addEventListener('change', () => {
    if (sel.value === LANG) { close(); return; }
    wanted = sel.value;
    const label = LANGUAGES.find(([code]) => code === wanted)?.[1] ?? wanted;
    question.textContent = RESTART_WORDS.ask(label);
    note.hidden = true;
    ask.hidden = false;
    go.focus();
  });
  go.addEventListener('click', () => { const code = wanted; close(); if (code) choose(code); });
  stay.addEventListener('click', () => { sel.value = LANG; close(); sel.focus(); });
  ask.addEventListener('keydown', (e) => { if (e.key === 'Escape') { e.stopPropagation(); stay.click(); } });

  after.after(row);
  row.after(note, ask);
  return row;
}
