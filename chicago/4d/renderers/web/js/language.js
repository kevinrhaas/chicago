/**
 * Settings › Display › Language (gap analysis item 15: Spanish). Built here, not in index.html:
 * the page is copied to every year's door and sits at validate.py's 64 KiB duplicate floor
 * (T-0722), so it carries none of this row's bytes. Choosing reloads the page in that language
 * (js/strings/index.js § chooseLanguage).
 */
import { LANG, LANGUAGES, chooseLanguage } from './strings/index.js';

export function languageRow(after) {
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
  sel.addEventListener('change', () => chooseLanguage(sel.value));
  row.append(name, sel);
  after.after(row);
  return row;
}
