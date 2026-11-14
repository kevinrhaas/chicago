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
const CENSUS_1910 = 'census_1910_chicago_t624_roll241';
/** T-3382: where a child of the house stood on the scene date, from the card's `lived_here`. */
const ON_SCENE_DATE = { yes: 'At home', no: 'Not living here', unknown: 'Not documented' };

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
 * T-3413: a face fitted to a portrait of the person (assets/humans/web/hm08_variation_persons.json's `face`,
 * from tools/fit_portrait_face.py). The card shows the portrait beside a still of the fitted face,
 * the picture's grade, how close the fit came, and what the model cannot show yet. A face with
 * no card block (or none at all) shows nothing.
 */
export function likenessOf(face, assetBase = null) {
  const c = face?.card;
  if (!c?.portrait || !c?.model) return null;
  const url = (p) => { try { return assetBase ? new URL(p, assetBase).href : p; } catch { return p; } };
  const notModelled = (face.not_modelled ?? []).map((t) => String(t).replace(/\s*\(.*\)$/, ''));
  return {
    grade: face.grade ?? 'reconstructed',
    portrait: url(c.portrait),
    model: url(c.model),
    sourceTitle: sourceTitle(c.source_citation ?? '') || c.source_citation || '',
    sourceUrl: c.source_url ?? '',
    fit: Number.isFinite(c.rms_mm) ? `Fitted to ${c.marks ?? 'the'} points marked on the photograph; the model sits within about ${Math.round(c.rms_mm)} mm of them on average.` : '',
    notModelled,
    // T-3478: no photograph of the person is known, so the face is fitted to a stand-in's:
    // someone of their sex, age, heritage and work, named and credited, who is NOT them.
    standIn: c.stand_in ? String(c.stand_in) : '',
  };
}

/**
 * T-3491: how a drawn man looks — complexion, hair, eyes, stature — each in the register's own
 * word and graded, and the stand-in portrait his colouring was matched to, labelled as a
 * stand-in (data/humans/variation/looks/, carried in hm08_variation_persons.json `looks`).
 */
export function looksOf(looks, assetBase = null) {
  if (!looks?.complexion || !looks?.hair) return null;
  const url = (p) => { try { return assetBase ? new URL(p, assetBase).href : p; } catch { return p; } };
  const inches = Number(looks.stature?.inches);
  const feet = Number.isFinite(inches) ? `${Math.floor(inches / 12)} ft ${Math.round(inches % 12)} in` : '';
  const ref = looks.reference ?? null;
  return {
    grade: looks.grade ?? 'reconstructed',
    rows: [['Complexion', looks.complexion.value], ['Hair', [looks.hair.value, ...(looks.hair.facial ?? []).filter(x => !/^(brows|lashes)/.test(x)).map(x => ({
      moustache: 'moustache', moustache_full: 'full moustache', beard_short: 'short beard',
      side_whiskers_short: 'short side whiskers', side_whiskers: 'side whiskers', side_whiskers_full: 'full side whiskers',
    }[x] ?? words(x)))].filter(Boolean).join(', ')],
      ['Eyes', looks.eyes?.value ?? ''], ['Height', feet ? `about ${feet}` : ''],
      // T-3522: what they wear on 14 August (their dress record's own words; reconstructed).
      ['Dress', looks.worn ? `${looks.worn[0].toUpperCase()}${looks.worn.slice(1)}` : '']].filter(([, v]) => v),
    stature: looks.stature ?? null,
    heritage: looks.heritage?.origin && looks.heritage.origin !== 'not found' ? `${looks.heritage.origin.split(' (')[0]} name` : '',
    basis: looks.basis ?? '',
    reference: ref?.image ? { image: url(ref.image), caption: `${ref.title}, ${ref.artist}, ${ref.date}`, url: ref.page_url ?? '', why: ref.why ?? '' } : null,
  };
}

/**
 * The card, from the directory's row and (once it is read) the household record's own entry
 * for this person and the scene's citation join. Every part is optional but the row.
 */
export function personModel({ row, person = null, household = null, citations = null, sceneYear = null, face = null, looks = null, assetBase = null, told = null } = {}) {
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
  // T-3521 (the owner, 2026-11-08, of John Kinzie's 1812 card: "the story text style deviates
  // from the style we had before, this is really technical and not interesting, do a sweep of
  // everyone so that we have good correct stories for each"): a person's story is written for
  // a reader in the scene's stories file (data/residents_<scene>/stories.json, `told`). The
  // record's own notes, which are the researchers' working words, move to How we know, folded
  // under "The research notes". Without a written story a census servant keeps the lead said
  // from the enumerator's line, and a reconstructed life its reconstructed history; the notes
  // are the story only where nothing else is written yet.
  const notes = [];
  const toldParas = (Array.isArray(told) ? told : told ? String(told).split(/\n\s*\n/) : []).map((t) => String(t).trim()).filter(Boolean);
  if (toldParas.length) {
    lead = null;
    if (story) notes.push(story);
    for (const n of [bornNote, workNote]) if (n && !fromTheSheet(n) && !story.includes(n)) notes.push(n);
    paragraphs.push(...toldParas);
  } else if (lead || (p.history && Array.isArray(p.history.paragraphs) && p.history.paragraphs.length)) {
    if (story) notes.push(story);
    for (const n of [bornNote, workNote]) if (n && !fromTheSheet(n) && !story.includes(n)) notes.push(n);
    if (lead) { const extra = roleLine(work); if (extra) paragraphs.push(extra); }
  } else {
    if (story) paragraphs.push(story);
    for (const n of [bornNote, workNote]) if (n && !fromTheSheet(n) && !story.includes(n)) paragraphs.push(n);
  }
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
  // T-3382: a child of the house carded for the years they lived in it, which need not
  // include the scene date. The years are the card's, as the listings and censuses give them.
  const lived = p.lived_here ?? row?.lived_here ?? null;
  if (lived?.years) facts.push({ label: 'Lived here', value: String(lived.years).replace(/([\ds])-(\d|about)/g, '$1\u2013$2'), grade });
  if (lived?.on_scene_date && ON_SCENE_DATE[lived.on_scene_date]) {
    facts.push({ label: year ? `In ${year}` : 'On the scene date', value: ON_SCENE_DATE[lived.on_scene_date], grade });
  }
  const ownCard = p.own_card ?? row?.own_card ?? null;
  // T-3507..T-3509: a card's own graded facts (a Native card's name basis, band, gens, its 15th),
  // a reconstructed history kept apart from the story, and a named man's own portrait.
  for (const f of Array.isArray(p.card_facts) ? p.card_facts : []) {
    if (f?.label && f?.value && !facts.some((x) => x.label === f.label)) facts.push({ label: String(f.label), value: String(f.value), grade: f.grade ?? grade });
  }
  const assetUrl = (q) => { try { return assetBase ? new URL(q, assetBase).href : q; } catch { return q; } };
  const hist = p.history && Array.isArray(p.history.paragraphs) && p.history.paragraphs.length ? {
    title: String(p.history.title ?? 'A reconstructed history'), grade: p.history.grade ?? 'reconstructed',
    caveat: String(p.history.caveat ?? ''), paragraphs: p.history.paragraphs.map(String) } : null;
  // T-3521: with no written story, a reconstructed history IS the story, told under Their
  // story with its reconstructed mark rather than in a second section beneath technical notes.
  const historyIsStory = !!hist && !toldParas.length && !lead;
  // A story about someone no source tells the life of says so beside it.
  const storyMark = historyIsStory ? { grade: hist.grade, text: hist.caveat || 'No source tells this life: every particular of it is ours.' }
    : (toldParas.length && grade === 'reconstructed') ? { grade: 'reconstructed', text: 'No source names this person: the life told here is reconstructed from the record of the town.' }
      : null;
  const fifteenth = p.on_15_august?.value ? { value: String(p.on_15_august.value), grade: p.on_15_august.grade ?? grade, note: String(p.on_15_august.note ?? '') } : null;
  const nameBasis = p.name_basis?.note ? { grade: p.name_basis.grade ?? grade, text: String(p.name_basis.note) } : null;
  const portrait = p.portrait?.image ? { image: assetUrl(p.portrait.image), caption: String(p.portrait.caption ?? ''), why: String(p.portrait.why ?? ''),
    grade: p.portrait.grade ?? 'attested' } : null;

  // How we know.
  const sources = (Array.isArray(p.sources) ? p.sources : []).map((id) => {
    const c = citations?.[id] ?? null;
    // The two Blue Books share a title the shortener cuts before the year, so they say theirs.
    const title = BLUE_BOOKS[id] ? `The Chicago Blue Book, ${BLUE_BOOKS[id]} edition`
      : (c?.citation && sourceTitle(c.citation)) || c?.citation || 'A source not yet joined to this scene';
    return { id, title, url: c?.url || '' };
  });
  const ids = new Set(sources.map((s) => s.id));
  // The 1900 census line where there is one, else the 1910 line a child is carded from (T-3382).
  const line = [[p.census_1900, CENSUS_1900], [p.census_1910, CENSUS_1910]].find(([c]) => c && typeof c === 'object');
  const census = line ? {
    asWritten: String(line[0].as_enumerated ?? ''),
    relation: String(line[0].relation_as_enumerated ?? ''),
    locator: String(line[0].locator ?? ''),
    date: String(line[0].date ?? ''),
    year: yearOf(line[0].date) ?? (line[1] === CENSUS_1910 ? 1910 : 1900),
    link: leafLink(citations?.[line[0].source ?? line[1]], line[0].locator),
    reading: sheet ? sheet[0].trim() : '',
  } : null;
  const book = Object.keys(BLUE_BOOKS).find((id) => ids.has(id));
  const why = whyLine({ grade, census, book: book ? BLUE_BOOKS[book] : null, year, relationship, sources, doubted: caveats.length > 0, lived });
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
    story: historyIsStory ? hist.paragraphs.slice() : paragraphs,
    storyMark,
    historyIsStory,
    told: toldParas.length > 0,
    notes,
    why,
    census,
    printedAs,
    caveats,
    sheetNotes,
    sources,
    ownCard,
    likeness: likenessOf(face, assetBase),
    looks: looksOf(looks, assetBase),
    history: hist,
    fifteenth,
    nameBasis,
    portrait,
    portraitResearch: p.portrait_research?.note ? String(p.portrait_research.note) : null,
    individualCards: (Array.isArray(p.individual_cards) ? p.individual_cards : []).map(id => ({
      id, name: household?.persons?.find(person => person.id === id)?.name ?? 'Family member',
    })),
    away: lived?.on_scene_date === 'no',
    // T-3531: whether the record has them in town on the scene's day at all ('absent' for
    // Sauganash, who came to Chicago on 16 August 1812), and the day they came if it says.
    present: row?.present ?? null,
    came: String(row?.household_name ?? household?.name ?? '').match(/\bwho came to Chicago on (\d{1,2} [A-Z][a-z]+ \d{4})/)?.[1] ?? null,
    read: !!person,
  };
}

/** T-3531: why Find and Follow are greyed on this card: said from the record, never a guess. */
export function notFoundWhy(m) {
  if (m.present === 'absent') return m.came ? `Not in town today: came to Chicago on ${m.came}` : 'Not in town today';
  if (m.present === 'uncertain') return 'Not in town now: where they were that day is not known';
  return 'Not out in town at this hour or season';
}

/** T-3573: under Find and Follow for someone at home now. */
export const AT_HOME_LINE = 'At home now: they come out to meet you';

/**
 * T-3521: a line on what the work meant in a house like this one, for a census servant whose
 * card has no story written yet. It is about the work, said generally ("A cook in a house
 * like this …"), never a claim about the person; a work it does not know says nothing.
 */
const ROLE_LINES = [
  [/^cook/i, 'A cook in a Prairie Avenue house ran the kitchen below stairs: the coal range lit before dawn, three meals for the family and the staff, and the dinners the street was known for.'],
  [/^(second |head |chamber|house|parlo(u)?r|lady'?s )?(maid|servant|housemaid|domestic)/i, 'A maid in a house like this was up first and to bed last: grates cleaned and fires laid, rooms dusted and beds made, hot water carried up the back stairs before the family woke.'],
  [/^waitress/i, 'A waitress laid the table, served each course and cleared it, and kept the silver and the china in the butler\'s pantry between meals.'],
  [/^laundress/i, 'A laundress spent her week in the basement laundry: Monday washing in the copper, then starching, drying and ironing until the family\'s linen went back upstairs.'],
  [/^(nurse|nursemaid|governess)/i, 'A nurse kept the children: their nursery, their meals, their walks along the avenue and the lake, and their bedtimes.'],
  [/^(coachman|driver|hostler|groom|stableman)/i, 'A coachman lived over or beside the stable at the back of the lot, kept the horses and the carriages, and drove the family wherever they went.'],
  [/^(butler|footman|houseman|man servant|manservant|valet)/i, 'A butler ran the household staff, kept the wine and the silver, answered the door and announced every caller.'],
  [/^(seamstress|dressmaker)/i, 'A seamstress kept the family\'s clothes in repair and made new ones in a sewing room upstairs.'],
  [/^(helper|laborer|labourer|gardener|porter|janitor|furnace)/i, 'A helper did the heavy work of the place: coal and ashes, the walks and the yard, and whatever the house and stable needed carried.'],
];
export function roleLine(work) {
  const w = String(work ?? '').trim();
  if (!w) return '';
  return ROLE_LINES.find(([re]) => re.test(w))?.[1] ?? '';
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
function whyLine({ grade, census, book, year, relationship, sources, doubted, lived = null }) {
  if (lived) return livedWhy({ grade, census, year, lived });
  const gap = census && year ? year - (yearOf(census.date) ?? year) : 0;
  const before = gap > 0 ? `${NUMBER[gap] ?? gap} year${gap === 1 ? '' : 's'} before this scene` : 'before this scene';
  if (grade === 'attested') {
    const lead = book
      ? `The ${book} Blue Book, Chicago's society register, lists ${relationship === 'head' ? 'this household' : 'them'} at this house.`
      : `${sources.length > 1 ? 'The sources below say' : 'The source below says'} so directly: they lived in this house.`;
    return { grade, title: 'Attested: a source says so', text: census ? `${lead} The ${census.year ?? 1900} census found them here too.` : lead };
  }
  if (grade === 'inferred') {
    if (census && !book && (census.year ?? 1900) <= (year ?? 1900)) {
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

/** T-3382: the grade of a child carded for the years they lived here. */
function livedWhy({ grade, census, year, lived }) {
  const when = year ?? 'the scene year';
  const on = lived.on_scene_date;
  const then = on === 'no' ? ` They were not living here in ${when}.`
    : on === 'unknown' ? ` No record we read says whether they were here in ${when}.` : '';
  if (grade === 'attested') {
    return { grade, title: 'Attested: a source says so',
      text: `The sources below place them in this house as a child of the family${lived.years ? `, ${String(lived.years).replace(/([\ds])-(\d|about)/g, '$1\u2013$2')}` : ''}.${then}` };
  }
  if (grade === 'inferred') {
    // T-3590: someone the 1900 census found here who was gone by the scene (Kate Ryan, the
    // Glessners' summer cook) is known from that census line, like the staff who stayed.
    const gap = census && year ? year - (yearOf(census.date) ?? year) : 0;
    if (census && gap > 0 && on === 'no') {
      return { grade, title: 'Inferred: worked out from clues',
        text: `The 1900 census lists them in this house on 1 June 1900, ${NUMBER[gap] ?? gap} year${gap === 1 ? '' : 's'} before this scene.${then}` };
    }
    const later = census && census.year > (Number(year) || 0)
      ? `The ${census.year} census lists them in this house${on === 'yes' ? `; their age and the family's listings put them at home in ${when}, which no record of that year states` : ''}.`
      : 'No source prints the relationship outright; it is read from the listings below.';
    return { grade, title: 'Inferred: worked out from clues', text: `${later}${then}` };
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
export function renderPersonCard(doc, m, { dot = () => doc.createTextNode(''), onFind = null, onFollow = null, inTown = null, atHome = null } = {}) {
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
  // T-3531 (the owner, 2026-11-09: "if somebody is looked for and you try to find them and
  // they cant be found because they are not in the area you should not be able to select the
  // find this person or follow and where those buttons are you should know they cant be found
  // or followed"): Find and Follow are live only for someone placed in town now. Anyone else
  // keeps both keys, greyed, with the reason under them.
  const canFind = typeof onFind === 'function', canFollow = typeof onFollow === 'function';
  if ((canFind || canFollow) && !m.away) {
    const here = typeof inTown === 'function' ? !!inTown(m.id) : canFind;
    if (canFind) {
      const find = el(doc, 'button', 'nav-tile insp-person-find', 'Find this person');
      find.type = 'button'; find.dataset.personFind = m.id;
      if (here) find.addEventListener('click', () => onFind(m.id));
      else { find.disabled = true; find.setAttribute?.('aria-disabled', 'true'); }
      card.append(find);
    }
    // T-3404: someone placed in town now (Hans Johnson on his round) can be walked alongside.
    if (canFollow && typeof inTown === 'function') {
      const follow = el(doc, 'button', 'nav-tile insp-person-follow', 'Follow');
      follow.type = 'button'; follow.dataset.personFollow = m.id;
      // Its own: Inspect's pane carries data-person, and a click let up to it reopens the card.
      if (here) follow.addEventListener('click', (e) => { e?.stopPropagation?.(); onFollow(m.id); });
      else { follow.disabled = true; follow.setAttribute?.('aria-disabled', 'true'); }
      card.append(follow);
    }
    if (!here) card.append(el(doc, 'p', 'nav-k insp-person-unfound', notFoundWhy(m)));
    // T-3573: at home now: Find or Follow goes to their door, and out they come on a walk.
    else if (typeof atHome === 'function' && atHome(m.id)) card.append(el(doc, 'p', 'nav-k insp-person-unfound insp-person-home', AT_HOME_LINE));
  }
  if (m.ownCard) {
    // T-3382: a grown child with a house of their own in the scene year has a card there too.
    const own = el(doc, 'button', 'nav-tile insp-person-link insp-person-own', 'Their own household');
    own.type = 'button'; own.dataset.person = m.ownCard; card.append(own);
  }


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
    if (m.storyMark) {
      sec.dataset.grade = m.storyMark.grade;
      const c = el(doc, 'p', 'insp-person-note insp-person-mark', m.storyMark.text);
      c.prepend(dot(doc, m.storyMark.grade), ' ');
      sec.append(c);
    }
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

  if (m.history && !m.historyIsStory) {
    const H = m.history;
    const sec = el(doc, 'section', 'insp-sec insp-person-history');
    sec.dataset.grade = H.grade;
    const h = el(doc, 'h3', 'insp-h', H.title);
    sec.append(h);
    if (H.caveat) { const c = el(doc, 'p', 'insp-person-note', H.caveat); c.prepend(dot(doc, H.grade), ' '); sec.append(c); }
    for (const t of H.paragraphs) sec.append(el(doc, 'p', 'insp-summary', t));
    card.append(sec);
  }

  if (m.fifteenth) {
    const F = m.fifteenth;
    const sec = el(doc, 'section', 'insp-sec insp-person-fifteenth');
    sec.dataset.grade = F.grade;
    sec.append(el(doc, 'h3', 'insp-h', '15 August 1812'));
    const v = el(doc, 'p', 'insp-person-why-title', F.value);
    v.prepend(dot(doc, F.grade));
    sec.append(v);
    if (F.note) sec.append(el(doc, 'p', 'insp-person-note', F.note));
    card.append(sec);
  }

  if (m.portraitResearch && !m.portrait && !m.likeness) {
    const sec = el(doc, 'section', 'insp-sec insp-person-portrait-research');
    sec.append(el(doc, 'h3', 'insp-h', 'Likeness'), el(doc, 'p', 'insp-person-note', m.portraitResearch));
    card.append(sec);
  }
  if (m.individualCards?.length) {
    const sec = el(doc, 'section', 'insp-sec');
    sec.append(el(doc, 'h3', 'insp-h', 'Individual family members'));
    for (const { id, name } of m.individualCards) {
      const button = el(doc, 'button', 'nav-tile insp-person-link', name);
      button.type = 'button'; button.dataset.person = id; sec.append(button);
    }
    card.append(sec);
  }

  if (m.portrait && !m.likeness) {
    const P = m.portrait;
    const sec = el(doc, 'section', 'insp-sec insp-person-likeness insp-person-portrait');
    sec.dataset.grade = P.grade;
    sec.append(el(doc, 'h3', 'insp-h', 'Likeness'));
    const fig = el(doc, 'figure', 'insp-person-face');
    const img = el(doc, 'img');
    img.src = P.image; img.alt = `${m.name}: ${P.caption}`; img.loading = 'lazy'; img.decoding = 'async'; img.width = 360; img.height = 480;
    fig.append(img, el(doc, 'figcaption', 'nav-k', P.caption));
    sec.append(fig);
    if (P.why) sec.append(el(doc, 'p', 'insp-person-note', P.why));
    card.append(sec);
  }

  if (m.likeness) {
    const L = m.likeness;
    const sec = el(doc, 'section', 'insp-sec insp-person-likeness');
    sec.dataset.grade = L.grade;
    sec.append(el(doc, 'h3', 'insp-h', 'Likeness'));
    const pair = el(doc, 'div', 'insp-person-pair');
    const photo = L.standIn ? ['Stand-in, not them', `A stand-in's photograph, not ${m.name}`] : ['Photograph', `${m.name}, photograph`];
    for (const [src, cap, alt] of [[L.portrait, photo[0], photo[1]], [L.model, 'Model', `${m.name}, the model's face`]]) {
      const fig = el(doc, 'figure', 'insp-person-face');
      const img = el(doc, 'img');
      img.src = src; img.alt = alt; img.loading = 'lazy'; img.decoding = 'async'; img.width = 360; img.height = 480;
      fig.append(img, el(doc, 'figcaption', 'nav-k', cap));
      pair.append(fig);
    }
    sec.append(pair);
    const g = el(doc, 'p', 'insp-person-why-title', L.standIn ? `Face ${String(GRADE_WORD[L.grade] ?? L.grade).toLowerCase()} after a stand-in` : `Face ${String(GRADE_WORD[L.grade] ?? L.grade).toLowerCase()} by the photograph`);
    g.prepend(dot(doc, L.grade));
    if (L.standIn) { g.after(el(doc, 'p', 'insp-person-note', L.standIn)); }
    sec.append(g);
    if (L.fit) sec.append(el(doc, 'p', 'insp-person-note', L.fit));
    if (L.notModelled.length) sec.append(el(doc, 'p', 'insp-person-note', `Not on the model yet: ${L.notModelled.join(', ')}.`));
    if (L.sourceTitle) {
      const p = el(doc, 'p', 'insp-person-note');
      if (L.sourceUrl) { const a = el(doc, 'a', null, L.sourceTitle); a.href = L.sourceUrl; a.target = '_blank'; a.rel = 'noopener'; p.append(a); }
      else p.append(L.sourceTitle);
      sec.append(p);
    }
    card.append(sec);
  }

  if (m.looks) {
    const L = m.looks;
    const sec = el(doc, 'section', 'insp-sec insp-person-looks');
    sec.dataset.grade = L.grade;
    sec.append(el(doc, 'h3', 'insp-h', 'Looks'));
    const dl = el(doc, 'dl', 'insp-key');
    for (const [k, v] of L.rows) {
      const row = el(doc, 'div', 'insp-key-row');
      row.append(el(doc, 'dt', null, k), el(doc, 'dd', null, v));
      dl.append(row);
    }
    sec.append(dl);
    const g = el(doc, 'p', 'insp-person-why-title', `${GRADE_WORD[L.grade] ?? L.grade}${L.heritage ? ` \u00b7 ${L.heritage}` : ''}`);
    g.prepend(dot(doc, L.grade));
    sec.append(g);
    // T-3521: the working notes on how the look was drawn (readings, source lines, liberty
    // numbers) fold under the grade, as the story's research notes fold under How we know.
    if (L.basis || L.stature?.basis) {
      const fold = el(doc, 'details', 'insp-person-notes');
      fold.append(el(doc, 'summary', 'nav-k', 'How the look was drawn'));
      if (L.basis) fold.append(el(doc, 'p', 'insp-person-note', L.basis));
      if (L.stature?.basis) {
        const s = el(doc, 'p', 'insp-person-note', `Height: ${L.stature.basis}`);
        if (L.stature.grade && L.stature.grade !== L.grade) s.prepend(dot(doc, L.stature.grade));
        fold.append(s);
      }
      sec.append(fold);
    }
    if (L.reference) {
      const fig = el(doc, 'figure', 'insp-person-face insp-person-standin');
      const img = el(doc, 'img');
      img.src = L.reference.image; img.alt = `Stand-in portrait: ${L.reference.caption}`; img.loading = 'lazy'; img.decoding = 'async'; img.width = 360; img.height = 480;
      const cap = el(doc, 'figcaption', 'nav-k');
      if (L.reference.url) { const a = el(doc, 'a', null, `Stand-in: ${L.reference.caption}`); a.href = L.reference.url; a.target = '_blank'; a.rel = 'noopener'; cap.append(a); }
      else cap.append(`Stand-in: ${L.reference.caption}`);
      fig.append(img, cap);
      sec.append(fig);
      if (L.reference.why) sec.append(el(doc, 'p', 'insp-person-note', L.reference.why));
    }
    card.append(sec);
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
    box.append(el(doc, 'span', 'nav-k', `The ${m.census.year ?? 1900} census, as written`));
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
  if (m.nameBasis) {
    const p = el(doc, 'p', 'insp-person-note', `Name: ${m.nameBasis.text}`);
    p.prepend(dot(doc, m.nameBasis.grade), ' ');
    how.append(p);
  }
  for (const c of m.caveats) how.append(el(doc, 'p', 'insp-person-note', c));
  if (m.notes?.length) {
    // T-3521: the record's own notes, in the researchers' words, a tap away.
    const det = el(doc, 'details', 'insp-person-notes');
    det.append(el(doc, 'summary', 'nav-k', 'The research notes'));
    for (const t of m.notes) det.append(el(doc, 'p', 'insp-person-note', t));
    how.append(det);
  }
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
