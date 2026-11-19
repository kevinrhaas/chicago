import { t } from './strings/index.js';
import './strings/investigation.js';
import { CASE_LIMITS, investigationNote, saveInvestigation } from './jaunt-investigation.js';
import { fieldNotebook } from './field-notebook.js';

/** Native disclosure, form controls and text-only readings. No markup comes from a
 * student's answer, and the only storage write is the Save button's action. */
export function renderInvestigation(doc, model, draft, notebook = fieldNotebook) {
  if (!model || !draft) return null;
  const node = (tag, text, cls) => {
    const el = doc.createElement(tag);
    if (text != null) el.textContent = text;
    if (cls) el.className = cls;
    return el;
  };
  const button = (key, action) => {
    const el = node('button', t(`investigation.${key}`), 'welcome-link');
    el.type = 'button'; el.addEventListener('click', action); return el;
  };
  const root = node('details', null, 'jaunt-investigation'); root.open = draft.open;
  const summary = node('summary', t('investigation.title'));
  root.append(summary, node('p', model.intro ?? t('investigation.intro')), node('p', t('investigation.privacy'), 'jaunt-meta'),
    node('h4', model.question));
  root.addEventListener('toggle', () => { draft.open = root.open; });
  for (const reading of model.readings) {
    const card = node('section', null, 'jaunt-investigation-reading');
    card.append(node('h5', reading.title), node('p', model.reading ?? t('investigation.reading'), 'jaunt-meta'), node('p', reading.locator));
    for (const claim of reading.claims) {
      card.append(node('h6', t(`investigation.evidence.${claim.id}`)),
        node('p', model.grades?.[claim.confidence] ?? t(`investigation.grade.${claim.confidence}`), 'jaunt-meta'), node('blockquote', claim.text));
      if (claim.reasoning) card.append(node('p', claim.reasoning));
    }
    const sources = node('ul');
    for (const source of new Map(reading.claims.flatMap(c => c.sources).map(s => [s.id, s])).values())
      sources.append(node('li', source.title));
    card.append(sources); root.append(card);
  }
  const choiceSet = node('fieldset'); choiceSet.append(node('legend', t('investigation.evidence')));
  const choices = [];
  const changed = () => { draft.status = ''; status.textContent = ''; paintSave(); };
  for (const claim of model.claims) {
    const label = node('label', null, 'jaunt-investigation-choice');
    const input = node('input'); input.type = 'checkbox'; input.value = claim.id;
    input.checked = draft.selected.includes(claim.id); choices.push(input);
    input.addEventListener('change', () => {
      draft.selected = choices.filter(c => c.checked).map(c => c.value); changed();
    });
    label.append(input, node('span', t(`investigation.evidence.${claim.id}`))); choiceSet.append(label);
  }
  root.append(choiceSet);
  const fields = {};
  for (const key of ['claim', 'uncertainty']) {
    const label = node('label', t(`investigation.${key}`));
    const field = node('textarea'); field.rows = key === 'claim' ? 4 : 3;
    field.maxLength = CASE_LIMITS[key]; field.value = draft[key]; field.dataset.investigationField = key;
    field.addEventListener('input', () => { draft[key] = field.value.slice(0, CASE_LIMITS[key]); changed(); });
    fields[key] = field; label.append(field); root.append(label);
  }
  const review = node('div', null, 'jaunt-investigation-review'); review.hidden = !draft.reviewed;
  review.append(node('p', t('investigation.review')));
  for (const claim of model.claims)
    review.append(node('h5', t(`investigation.evidence.${claim.id}`)), node('p', t(`investigation.review.${claim.id}`)));
  review.append(node('p', model.liberties ?? t('investigation.review.liberties')), button('revise', () => fields.claim.focus()));
  const compare = button('compare', () => {
    draft.reviewed = true; review.hidden = false; compare.setAttribute('aria-expanded', 'true');
    status.textContent = t('investigation.review');
  });
  compare.setAttribute('aria-expanded', String(draft.reviewed)); root.append(compare, review);
  const status = node('p', draft.status ? t(`investigation.status.${draft.status}`) : '', 'jaunt-investigation-status');
  status.setAttribute('role', 'status'); status.setAttribute('aria-atomic', 'true');
  const save = button('save', () => {
    const result = saveInvestigation(model, draft, notebook);
    draft.status = result.ok ? (result.duplicate ? 'duplicate' : 'saved') : result.reason;
    status.textContent = t(`investigation.status.${draft.status}`);
    if (!result.ok && fields[result.reason]) fields[result.reason].focus();
    else if (result.reason === 'evidence') choices[0]?.focus();
    paintSave();
  });
  function paintSave() {
    const note = investigationNote(model, draft);
    save.textContent = t(draft.savedSignature && note.signature !== draft.savedSignature
      ? 'investigation.save.revised' : 'investigation.save');
  }
  paintSave();
  const actions = node('div', null, 'jaunt-investigation-actions');
  actions.append(save, button('skip', () => { draft.open = false; root.open = false; summary.focus(); }));
  root.append(actions, status);
  return root;
}
