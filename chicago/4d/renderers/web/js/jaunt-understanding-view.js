import { t } from './strings/index.js';
import './strings/understanding.js';
import { ANSWER_LIMIT, CHECK_AGES } from './jaunt-understanding.js';

/** Native details, labels and buttons keep the optional check usable with keyboard and
 * screen reader. `draft` belongs to the completed session, never browser or remote storage. */
export function renderUnderstandingCheck(doc, questions, draft) {
  if (questions.length !== 3) return null;
  const node = (tag, text, cls) => {
    const el = doc.createElement(tag);
    if (text != null) el.textContent = text;
    if (cls) el.className = cls;
    return el;
  };
  const button = (key, action) => {
    const el = node('button', t(`understanding.${key}`), 'welcome-link');
    el.type = 'button'; el.addEventListener('click', action); return el;
  };
  const root = node('details', null, 'jaunt-understanding'); root.open = draft.open;
  const summary = node('summary', t('understanding.title'));
  root.append(summary, node('p', t('understanding.intro')), node('p', t('understanding.privacy'), 'jaunt-meta'),
    node('p', t('understanding.age', { age: CHECK_AGES[questions[0].band] }), 'jaunt-meta'));
  root.addEventListener('toggle', () => { draft.open = root.open; });
  const fields = [], reviews = [], compareButtons = [];
  const status = node('p', '', 'jaunt-check-status'); status.setAttribute('role', 'status');
  for (const [i, question] of questions.entries()) {
    const section = node('section', null, 'jaunt-check-question');
    section.append(node('h4', `${question.number}. ${question.prompt}`));
    if (question.place) section.append(node('p', question.place, 'jaunt-meta'));
    section.append(node('p', t('understanding.claim'), 'jaunt-meta'), node('blockquote', question.claim.text));
    const label = node('label', t('understanding.answer', { n: question.number }));
    const field = node('textarea'); field.rows = 3; field.maxLength = ANSWER_LIMIT;
    field.value = draft.answers[i]; field.dataset.checkAnswer = String(i);
    label.append(field); section.append(label); fields.push(field);
    field.addEventListener('input', () => { draft.answers[i] = field.value.slice(0, ANSWER_LIMIT); });
    const review = node('div', null, 'jaunt-check-review'); review.hidden = !draft.reviewed[i];
    review.append(node('p', t('understanding.review')), node('p', t(`understanding.grade.${question.claim.confidence}`)));
    if (question.claim.locator) review.append(node('p', question.claim.locator));
    if (question.claim.reasoning) review.append(node('p', question.claim.reasoning));
    const sources = node('ul');
    for (const ref of question.sources) {
      const item = node('li', ref.citation);
      if (ref.url) {
        const link = node('a', t('understanding.source')); link.href = ref.url;
        link.target = '_blank'; link.rel = 'noopener noreferrer'; item.append(' ', link);
      } else item.append(' ', node('span', t('understanding.unavailable')));
      sources.append(item);
    }
    review.append(sources, button('revise', () => { field.focus(); }));
    const compare = button('compare', () => {
      draft.reviewed[i] = true; review.hidden = false; compare.setAttribute('aria-expanded', 'true');
      status.textContent = field.value.trim() ? t('understanding.review') : t('understanding.empty');
    });
    compare.setAttribute('aria-expanded', String(draft.reviewed[i]));
    compareButtons.push(compare); reviews.push(review); section.append(compare, review); root.append(section);
  }
  const actions = node('div', null, 'jaunt-check-actions');
  actions.append(button('skip', () => { draft.open = false; root.open = false; summary.focus(); }),
    button('again', () => {
      draft.answers.fill(''); draft.reviewed.fill(false);
      fields.forEach(field => { field.value = ''; }); reviews.forEach(review => { review.hidden = true; });
      compareButtons.forEach(button => button.setAttribute('aria-expanded', 'false'));
      status.textContent = t('understanding.reset'); fields[0].focus();
    }));
  root.append(actions, status);
  return root;
}
