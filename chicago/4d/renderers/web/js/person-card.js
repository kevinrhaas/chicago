/**
 * person-card.js — one person's own card, opened from a building's People tab (T-3265).
 *
 * The owner, 2026-10-30, on Glessner's People tab: a tap on a person "goes to a full list and
 * there is no way to get back ... it should go to a detailed card on that person and you
 * should be able to go back to the household", and the card "should have their detail and
 * explain who they are, tell their interesting story and explain the sourcing also, like why
 * some are attested and why some are inferred, but focus mostly on the person and their story".
 *
 * So the card leads with the person — name, place in the household, work, the facts of a life
 * the record states (born, age in the scene year, birthplace, the year they came to America) —
 * then their story in the record's own words, and only then How we know: why the grade is
 * what it is, the census line as the enumerator wrote it (with the page itself where the
 * record names its leaf), and the sources by title.
 *
 * NOTHING HERE IS COMPOSED BEYOND THE RECORD. The facts are the record's fields; the
 * birthplace and the year of arrival are read out of the record's own note, where the census
 * readings write them ("born January 1875, in Sweden, came to the United States in 1892"), and
 * a person whose note does not say shows neither. The age is the scene year less the year of
 * birth, "about", because a birthday is not a year. The two sentences every census servant's
 * note ends on — staff changed places, a name hard to read — are about the evidence, not the
 * person, so they move down to How we know rather than close the story.
 *
 * `personModel` is pure (the tests read it); `renderPersonCard` draws a model.
 */

import { sourceTitle } from './inspect-sources.js';

const GRADE_WORD = { attested: 'Attested', inferred: 'Inferred', reconstructed: 'Reconstructed' };
const PLACE = {
  head: 'Head of the household', wife: 'Wife', husband: 'Husband', son: 'Son', daughter: 'Daughter',
  servant: 'Live-in staff', household_member: 'In the household',
};
const NUMBER = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
const BLUE_BOOKS = { chicago_blue_book_1904: '1904', chicago_blue_book_1905: '1905' };
const CENSUS_1900 = 'census_1900_chicago_t623_roll245';

/** Sentences of a note that speak to the evidence rather than the person. */
const ABOUT_THE_EVIDENCE = [
  /\s*Servants changed places often[^.]*\./g,
  /\s*Part of the name is hard to read[^.]*\./g,
];

const ENUMERATED = /^Enumerated on 1 June 1900 [^.]*\.(?=\s|$)/;
const BIRTHPLACE = /\b[Bb]orn (?:\d{1,2} )?(?:[A-Z][a-z]+ )?\d{4}(?: \([^)]*\))?,? in ([A-Z][A-Za-z' ]+(?:, [A-Z][A-Za-z' ]+)?)/;
const ARRIVED = /came to the United States in (\d{4})/;

const words = (s) => String(s ?? '').replace(/_/g, ' ').trim();
const capital = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);
const valueOf = (block) => (block && typeof block === 'object' ? block.value : block);
const gradeOf = (block, fallback) => (block && typeof block === 'object' && block.confidence) || fallback || null;

/** "The Glessner household at 1800 Prairie Avenue" → "The Glessner household". */
export function householdShort(name) {
  const s = String(name ?? '').trim();
  if (!s) return 'This household';
  return s.replace(/\s+at\s+\d.*$/, '') || s;
}

/** A year from a record's date: "1875", "1848-01-01" → 1848. */
function yearOf(v) {
  const m = String(v ?? '').match(/^(\d{4})/);
  return m ? Number(m[1]) : null;
}

/** A born value as a visitor reads it: "1848-01-01" → "1 January 1848". */
function bornWords(v) {
  const s = String(v ?? '');
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return s;
  const month = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
    'September', 'October', 'November', 'December'][Number(m[2]) - 1];
  return month ? `${Number(m[3])} ${month} ${m[1]}` : s;
}

/** The census's page image, where the source is an Internet Archive item and the record names its leaf. */
function leafLink(citation, locator) {
  const url = String(citation?.url ?? '');
  const leaf = String(locator ?? '').match(/\bleaf (n\d+)\b/);
  if (!leaf || !/^https:\/\/archive\.org\/details\/[^/]+$/.test(url)) return null;
  return `${url}/page/${leaf[1]}/mode/1up`;
}

/**
 * The card, from the directory's row and (once it is read) the household record's own entry
 * for this person and the scene's citation join. Every part is optional but the row.
 */
export function personModel({ row, person = null, household = null, citations = null, sceneYear = null } = {}) {
  const p = person ?? {};
  const grade = p.grade ?? row?.grade ?? null;
  const relationship = p.relationship ?? row?.relationship ?? '';
  const occupation = valueOf(p.occupation) ?? row?.occupation ?? '';
  const work = occupation && !/^none/.test(String(occupation)) ? capital(words(occupation)) : '';
  const year = Number(sceneYear) || null;
  const householdName = household?.name ?? row?.household_name ?? '';

  // The note, its evidence sentences set aside for How we know.
  let story = String(p.note ?? '').trim();
  const caveats = [];
  for (const re of ABOUT_THE_EVIDENCE) {
    story = story.replace(re, (s) => { caveats.push(s.trim()); return ''; }).trim();
  }
  const bornNote = p.born && typeof p.born === 'object' ? String(p.born.note ?? '') : '';
  const workNote = p.occupation && typeof p.occupation === 'object' ? String(p.occupation.note ?? '') : '';
  // A field's note is the census's own wording for a census reading ("The census gives …",
  // "Written as …"): that is how we know it, not who they were. Any other note is story.
  const fromTheSheet = (s) => /^(The census gives|Written as)\b/.test(s);
  // A census servant's note opens on the enumerator's line ("Enumerated on 1 June 1900 in the
  // house, as a servant (cook); born April 1850, in Ireland, single."). That line is how we
  // know; the story opens instead on the same facts said about the person, and goes on with
  // whatever else the note says (who lived with them, where the family was that day).
  const paragraphs = [];
  let lead = null;
  const sheet = story.match(ENUMERATED);
  if (sheet) {
    story = story.slice(sheet[0].length).trim();
    lead = censusLead({ name: p.name ?? row?.name ?? '', line: sheet[0], work, householdName });
  }
  if (story) paragraphs.push(story);
  for (const n of [bornNote, workNote]) if (n && !fromTheSheet(n) && !story.includes(n)) paragraphs.push(n);
  const sheetNotes = [];
  if (bornNote && fromTheSheet(bornNote)) sheetNotes.push({ text: bornNote, grade: gradeOf(p.born) });
  if (workNote && fromTheSheet(workNote)) sheetNotes.push({ text: workNote, grade: gradeOf(p.occupation) });

  // The facts of a life, each with the grade of the field it is read from.
  const facts = [];
  if (work) facts.push({ label: 'Work', value: work, grade: gradeOf(p.occupation, grade) });
  const born = valueOf(p.born);
  const bornYear = yearOf(born);
  if (born) facts.push({ label: 'Born', value: bornWords(born), grade: gradeOf(p.born, grade) });
  if (bornYear && year && year > bornYear) {
    facts.push({ label: `Age in ${year}`, value: `About ${year - bornYear}`, grade: gradeOf(p.born, grade) });
  }
  const text = [p.note, bornNote].filter(Boolean).join(' ');
  const place = text.match(BIRTHPLACE)?.[1]?.trim();
  if (place) facts.push({ label: 'Born in', value: place, grade: gradeOf(p.born, grade) });
  const arrived = text.match(ARRIVED)?.[1];
  if (arrived) facts.push({ label: 'Came to America', value: arrived, grade: gradeOf(p.born, grade) });

  // How we know.
  const sources = (Array.isArray(p.sources) ? p.sources : []).map((id) => {
    const c = citations?.[id] ?? null;
    // The two Blue Books share a title the shortener cuts before the year, so they say theirs.
    const title = BLUE_BOOKS[id] ? `The Chicago Blue Book, ${BLUE_BOOKS[id]} edition`
      : (c?.citation && sourceTitle(c.citation)) || c?.citation || 'A source not yet joined to this scene';
    return { id, title, url: c?.url || '' };
  });
  const ids = new Set(sources.map((s) => s.id));
  const census = p.census_1900 && typeof p.census_1900 === 'object' ? {
    asWritten: String(p.census_1900.as_enumerated ?? ''),
    relation: String(p.census_1900.relation_as_enumerated ?? ''),
    locator: String(p.census_1900.locator ?? ''),
    date: String(p.census_1900.date ?? ''),
    link: leafLink(citations?.[p.census_1900.source ?? CENSUS_1900], p.census_1900.locator),
    reading: sheet ? sheet[0].trim() : '',
  } : null;
  const book = Object.keys(BLUE_BOOKS).find((id) => ids.has(id));
  const why = whyLine({ grade, census, book: book ? BLUE_BOOKS[book] : null, year, relationship, sources, doubted: caveats.length > 0 });
  const printedAs = p.printed_as ? { text: String(p.printed_as), edition: book ? BLUE_BOOKS[book] : null } : null;

  return {
    id: p.id ?? row?.id ?? null,
    name: p.name ?? row?.name ?? '',
    grade,
    place: PLACE[relationship] ?? capital(words(relationship)),
    household: householdName,
    back: householdShort(householdName),
    facts,
    lead,
    story: paragraphs,
    why,
    census,
    printedAs,
    caveats,
    sheetNotes,
    sources,
    read: !!person,
  };
}

/**
 * The census line said about the person: where the enumerator found them, the work, where they
 * were born and when they came. Every clause is a field of that line; one it lacks is left out.
 */
export function censusLead({ name, line, work, householdName }) {
  const where = line.match(/^Enumerated on 1 June 1900 (in [^,;]+?)(?:,| as\b|;)/)?.[1] ?? '';
  const address = String(householdName ?? '').match(/\bat (\d.*)$/)?.[1] ?? '';
  const born = line.match(/\bborn ((?:[A-Z][a-z]+ )?\d{4})/)?.[1] ?? '';
  const bornYear = yearOf(born.match(/\d{4}/)?.[0]);
  const place = line.match(BIRTHPLACE)?.[1]?.trim() ?? '';
  const came = Number(line.match(ARRIVED)?.[1]) || null;
  const status = line.match(/,\s*(single|married|widowed|divorced)\.?\s*$/)?.[1] ?? '';
  const first = String(name).split(/\s+/)[0];
  const called = first && !first.endsWith('.') ? first : name;
  const job = work && !/^(Wife|Son|Daughter|Head|Servant)$/i.test(work)
    ? `, working as ${/^[aeiou]/i.test(work) ? 'an' : 'a'} ${work.toLowerCase()}` : '';
  const at = where ? ` living ${where}${address && /\bhouse$/.test(where) ? ` at ${address}` : ''}` : '';
  const out = [`On 1 June 1900 the census taker found ${name}${at}${job}.`];
  if (place || born) {
    const from = [place ? `in ${place}` : '', born ? `in ${born}` : ''].filter(Boolean).join(' ');
    out.push(came
      ? `Born ${from}, ${called} came to the United States in ${came}${bornYear && came > bornYear ? `, at about ${came - bornYear}` : ''}.`
      : `${called} was born ${from}.`);
  }
  if (status) out.push(`${capital(status)} at the time.`);
  return out.join(' ');
}

/** Why the grade is what it is, in a sentence or two a visitor can follow. */
function whyLine({ grade, census, book, year, relationship, sources, doubted }) {
  const gap = census && year ? year - (yearOf(census.date) ?? year) : 0;
  const before = gap > 0 ? `${NUMBER[gap] ?? gap} year${gap === 1 ? '' : 's'} before this scene` : 'before this scene';
  if (grade === 'attested') {
    const lead = book
      ? `The ${book} Blue Book, Chicago's society register, lists ${relationship === 'head' ? 'this household' : 'them'} at this house.`
      : `${sources.length > 1 ? 'The sources below say' : 'The source below says'} so directly: they lived in this house.`;
    return { grade, title: 'Attested: a source says so', text: census ? `${lead} The 1900 census found them here too.` : lead };
  }
  if (grade === 'inferred') {
    if (census && !book) {
      return { grade, title: 'Inferred: worked out from clues',
        text: `The 1900 census lists them in this house on 1 June 1900, ${before}. The Blue Book, which places the family, never prints servants or young children, so the census is the nearest record that names them.${doubted ? '' : ` No record we read says they were still here in ${year ?? 'the scene year'}.`}` };
    }
    return { grade, title: 'Inferred: worked out from clues',
      text: 'No source states this outright for the scene date; it is reasoned from what the sources do say, as their story above explains.' };
  }
  if (grade === 'reconstructed') {
    return { grade, title: 'Reconstructed: built so the street makes sense',
      text: 'No source names this person here; our model of the town placed them, and says so.' };
  }
  return null;
}

function el(doc, tag, cls, text) {
  const n = doc.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

/** Draw a model. `dot(doc, grade)` is Inspect's grade dot. */
export function renderPersonCard(doc, m, { dot = () => doc.createTextNode('') } = {}) {
  const card = el(doc, 'article', 'insp-person-card');
  card.dataset.personId = m.id ?? '';
  const back = el(doc, 'button', 'insp-person-back');
  back.type = 'button';
  back.dataset.personBack = '';
  back.setAttribute('aria-label', `Back to ${m.back}`);
  back.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 5-7 7 7 7"/></svg>';
  back.append(el(doc, 'span', null, m.back));
  card.append(back);

  const head = el(doc, 'header', 'insp-person-head');
  const name = el(doc, 'h2', 'insp-name insp-person-name', m.name);
  head.append(name);
  const chips = el(doc, 'ul', 'insp-chips');
  const chip = (text, grade) => { const li = el(doc, 'li', 'insp-chip', text); if (grade) li.append(dot(doc, grade)); chips.append(li); };
  if (m.grade) chip(GRADE_WORD[m.grade] ?? m.grade, m.grade);
  if (m.place) chip(m.place);
  head.append(chips);
  if (m.household) head.append(el(doc, 'p', 'insp-address insp-person-hh', m.household));
  card.append(head);

  if (m.facts.length) {
    const dl = el(doc, 'dl', 'insp-key');
    for (const f of m.facts) {
      const row = el(doc, 'div', 'insp-key-row');
      const dd = el(doc, 'dd', null, f.value);
      dd.append(dot(doc, f.grade));
      row.append(el(doc, 'dt', null, f.label), dd);
      dl.append(row);
    }
    card.append(dl);
  }

  if (m.lead || m.story.length) {
    const sec = el(doc, 'section', 'insp-sec insp-person-story');
    sec.append(el(doc, 'h3', 'insp-h', 'Their story'));
    if (m.lead) {
      const p = el(doc, 'p', 'insp-summary', m.lead);
      p.dataset.composed = ''; // said from the census line below, clause by clause
      sec.append(p);
    }
    for (const t of m.story) sec.append(el(doc, 'p', 'insp-summary', t));
    card.append(sec);
  } else if (!m.read) {
    card.append(el(doc, 'p', 'nav-sub insp-person-wait', 'Reading the household record…'));
  } else {
    card.append(el(doc, 'p', 'nav-sub', 'The record says no more about them yet than the listing below.'));
  }

  const how = el(doc, 'section', 'insp-sec insp-person-how');
  how.append(el(doc, 'h3', 'insp-h', 'How we know'));
  if (m.why) {
    const box = el(doc, 'div', 'insp-person-why');
    box.dataset.grade = m.why.grade;
    const t = el(doc, 'p', 'insp-person-why-title', m.why.title);
    t.prepend(dot(doc, m.why.grade));
    box.append(t, el(doc, 'p', 'insp-person-why-text', m.why.text));
    how.append(box);
  }
  if (m.census) {
    const box = el(doc, 'div', 'insp-person-census');
    box.append(el(doc, 'span', 'nav-k', 'The 1900 census, as written'));
    box.append(el(doc, 'p', 'insp-person-as', `“${m.census.asWritten}”${m.census.relation ? ` · ${m.census.relation}` : ''}`));
    if (m.census.locator) box.append(el(doc, 'p', 'nav-sub', m.census.locator));
    if (m.census.reading) box.append(el(doc, 'p', 'insp-person-reading', m.census.reading));
    if (m.census.link) {
      const a = el(doc, 'a', 'insp-person-leaf', 'See the census page');
      a.href = m.census.link;
      a.target = '_blank';
      a.rel = 'noopener';
      box.append(a);
    }
    how.append(box);
  }
  if (m.printedAs) {
    how.append(el(doc, 'p', 'insp-person-note',
      `Printed in the ${m.printedAs.edition ? `${m.printedAs.edition} ` : ''}Blue Book as “${m.printedAs.text}”.`));
  }
  for (const n of m.sheetNotes) {
    const p = el(doc, 'p', 'insp-person-note', n.text);
    p.prepend(dot(doc, n.grade), ' ');
    how.append(p);
  }
  for (const c of m.caveats) how.append(el(doc, 'p', 'insp-person-note', c));
  if (m.sources.length) {
    const ul = el(doc, 'ul', 'insp-person-sources');
    for (const s of m.sources) {
      const li = el(doc, 'li');
      if (s.url) {
        const a = el(doc, 'a', null, s.title);
        a.href = s.url;
        a.target = '_blank';
        a.rel = 'noopener';
        li.append(a);
      } else li.append(el(doc, 'span', null, s.title));
      ul.append(li);
    }
    how.append(el(doc, 'span', 'nav-k', m.sources.length === 1 ? 'Source' : `${m.sources.length} sources`), ul);
  }
  card.append(how);
  return card;
}
