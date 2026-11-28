import { t } from './strings/index.js';
import './strings/understanding.js';
import { ANSWER_LIMIT, CHECK_AGES, answerQuestion, shortCitation } from './jaunt-understanding.js';
import { fieldNotebook, LIMITS } from './field-notebook.js';

/** Native details, labels and buttons keep the optional check usable with keyboard and
 * screen reader. `draft` belongs to the completed session, never browser or remote storage,
 * until the student chooses Save to my notebook (T-3778: a reflection a student may then
 * hand in to their teacher from the notebook). */
export function reflectionEntry(questions, draft, { title = '', year = '' } = {}) {
  const lines = questions.map((q, i) => `${q.number}. ${q.ask?.stem ?? q.prompt}\n${t('understanding.heard')}: ${q.heard ?? q.claim.text}\n${
    draft.solved[i] && q.ask ? `${t('understanding.answerIs', { answer: q.ask.options.find(o => o.id === q.ask.answer)?.label ?? '' })}\n` : ''}${
    t('understanding.answer', { n: q.number, prompt: q.prompt })}\n${draft.answers[i]?.trim() || '—'}`);
  return { kind: 'note', topic: 'reflection', title: t('understanding.saveTitle', { title }), year: String(year ?? ''),
    text: lines.join('\n\n').slice(0, LIMITS.noteChars) };
}
export function renderUnderstandingCheck(doc, questions, draft, { title = '', year = '', notebook = fieldNotebook } = {}) {
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
  const fields = [], reviews = [], compareButtons = [], section_paints = [];
  const status = node('p', '', 'jaunt-check-status'); status.setAttribute('role', 'status');
  for (const [i, question] of questions.entries()) {
    const section = node('section', null, 'jaunt-check-question');
    const ask = question.ask;
    const heading = node('h4', `${question.number}. ${ask?.stem ?? question.prompt}`);
    heading.id = `jaunt-check-q-${i}-${Math.random().toString(36).slice(2, 8)}`;
    section.append(heading);
    // A 'where' question does not print its own answer above the claim.
    if (question.place && ask?.kind !== 'where') section.append(node('p', question.place, 'jaunt-meta'));
    // The line you heard on the walk; the record behind it waits in the review below.
    section.append(node('p', t('understanding.heard'), 'jaunt-meta'), node('blockquote', question.heard ?? question.claim.text));
    // T-3670: the guide's question, one answer, as many tries as you like, no score.
    let paintChoices = () => {};
    if (ask) {
      const group = node('div', null, 'jaunt-check-choices');
      group.setAttribute('role', 'group'); group.setAttribute('aria-labelledby', heading.id);
      const feedback = node('p', '', 'jaunt-check-feedback');
      feedback.setAttribute('role', 'status'); feedback.setAttribute('aria-live', 'polite');
      const reveal = button('reveal', () => {
        draft.solved[i] = true; draft.chosen[i] = ask.answer; paintChoices();
        feedback.textContent = t('understanding.revealed'); showReview(); choiceButtons.find(b => b.dataset.option === ask.answer)?.focus();
      });
      reveal.classList.add('jaunt-check-reveal');
      const choiceButtons = ask.options.map(option => {
        const b = node('button', option.label, 'jaunt-check-choice'); b.type = 'button'; b.dataset.option = option.id;
        b.addEventListener('click', () => {
          const result = answerQuestion(question, draft, i, option.id);
          feedback.textContent = result.right ? t(`understanding.right.${ask.kind}`, null, t('understanding.right')) : t('understanding.wrong');
          paintChoices();
          if (result.right) { showReview(); if (draft.solved.every(Boolean)) status.textContent = t('understanding.done'); }
        });
        return b;
      });
      paintChoices = () => {
        for (const b of choiceButtons) {
          const isAnswer = b.dataset.option === ask.answer;
          const tried = draft.chosen[i] === b.dataset.option;
          b.disabled = draft.solved[i];
          b.setAttribute('aria-pressed', String(tried));
          b.classList.toggle('is-right', draft.solved[i] && isAnswer);
          b.classList.toggle('is-wrong', !draft.solved[i] && tried && !isAnswer);
        }
        reveal.hidden = draft.solved[i] || draft.tries[i] < 2;
      };
      group.append(...choiceButtons);
      section.append(group, feedback, reveal);
      if (draft.solved[i]) feedback.textContent = t('understanding.answerIs', { answer: ask.options.find(o => o.id === ask.answer)?.label ?? '' });
      paintChoices();
    }
    const label = node('label', t('understanding.answer', { n: question.number, prompt: question.prompt }));
    const field = node('textarea'); field.rows = 3; field.maxLength = ANSWER_LIMIT;
    field.value = draft.answers[i]; field.dataset.checkAnswer = String(i);
    label.append(field); section.append(label); fields.push(field);
    field.addEventListener('input', () => { draft.answers[i] = field.value.slice(0, ANSWER_LIMIT); });
    const review = node('div', null, 'jaunt-check-review'); review.hidden = !draft.reviewed[i];
    // Plain words first: what kind of claim it is, where we read it, where in that record.
    review.append(node('p', t('understanding.review')),
      node('p', t(`understanding.choice.${question.claim.confidence}`, null, t(`understanding.grade.${question.claim.confidence}`))));
    if (question.place && ask?.kind === 'where') review.append(node('p', question.place, 'jaunt-meta'));
    if (question.speaker && ask?.kind === 'who') review.append(node('p', question.speaker, 'jaunt-meta'));
    review.append(node('h5', t('understanding.claim')), node('blockquote', question.claim.text), node('h5', t('understanding.from')));
    const sources = node('ul');
    for (const ref of question.sources) {
      const item = node('li', shortCitation(ref.citation));
      if (ref.url) {
        const link = node('a', t('understanding.source')); link.href = ref.url;
        link.target = '_blank'; link.rel = 'noopener noreferrer'; item.append(' ', link);
      } else item.append(' ', node('span', t('understanding.unavailable')));
      sources.append(item);
    }
    review.append(sources);
    if (question.claim.locator) review.append(node('p', t('understanding.locator', { locator: question.claim.locator })));
    if (question.claim.reasoning) review.append(node('p', question.claim.reasoning));
    review.append(button('revise', () => { field.focus(); }));
    function showReview() { draft.reviewed[i] = true; review.hidden = false; compare.setAttribute('aria-expanded', 'true'); }
    const compare = button('compare', () => {
      showReview();
      status.textContent = field.value.trim() || draft.solved[i] ? t('understanding.review') : t('understanding.empty');
    });
    compare.setAttribute('aria-expanded', String(draft.reviewed[i]));
    section_paints.push(() => paintChoices());
    compareButtons.push(compare); reviews.push(review); section.append(compare, review); root.append(section);
  }
  const actions = node('div', null, 'jaunt-check-actions');
  actions.append(button('skip', () => { draft.open = false; root.open = false; summary.focus(); }),
    button('again', () => {
      draft.answers.fill(''); draft.reviewed.fill(false);
      draft.chosen.fill(null); draft.tries.fill(0); draft.solved.fill(false);
      section_paints.forEach(paint => paint());
      root.querySelectorAll?.('.jaunt-check-feedback').forEach(p => { p.textContent = ''; });
      fields.forEach(field => { field.value = ''; }); reviews.forEach(review => { review.hidden = true; });
      compareButtons.forEach(button => button.setAttribute('aria-expanded', 'false'));
      status.textContent = t('understanding.reset'); fields[0].focus();
    }));
  // T-3778: the student's own choice; once saved, a later Save changes the same entry.
  const save = button('save', () => {
    const entry = reflectionEntry(questions, draft, { title, year });
    const r = draft.savedId && notebook.read().entries.some(e => e.id === draft.savedId)
      ? notebook.update(draft.savedId, entry.text) : notebook.add(entry);
    if (r.ok && r.entry?.id) draft.savedId = r.entry.id;
    status.textContent = r.ok ? t('understanding.saved') : t('understanding.saveFailed');
  });
  actions.append(save);
  root.append(actions, status);
  return root;
}
