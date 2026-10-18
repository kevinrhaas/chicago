#!/usr/bin/env node
// T-2644 (NAV-508): Inspect's Sources tab. Every fact grouped by Attested, Inferred and
// Reconstructed with real counts, a Liberties section, human source titles taken from the
// source records' own citations, the full citation folded under each fact, and no source id,
// tier number or tier label in what a visitor reads.
//
// No browser: the pane is an HTML string, read here over fixtures and over the real Glessner
// House sidecar, its authored summary record and its liberties.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildingFacts, factCounts, sourceTitle, sourceTag, sourceYear, resolveSource, sourcesPaneHtml, GRADES, _test }
  from '../renderers/web/js/inspect-sources.js';
import { clean } from '../renderers/web/js/fallback-summary.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const json = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const visible = (html) => html.replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&#39;/g, "'")
  .replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/\s+/g, ' ');
// What is shown before a visitor opens anything: the pane with every <details> body taken out.
const closed = (html) => {
  let out = html;
  for (let i = 0; i < 20; i++) {
    const next = out.replace(/<details\b[^>]*>\s*<summary>((?:(?!<\/summary>)[\s\S])*)<\/summary>(?:(?!<details\b)[\s\S])*?<\/details>/g, '<s-closed>$1</s-closed>');
    if (next === out) break;
    out = next;
  }
  return out;
};

// ---- the title: a prefix of the citation, never a word that is not in it ------------------
{
  assert.equal(sourceTitle('Glessner, John J. The Story of a House. Unpublished typescript booklet, March 1923.'),
    'Glessner, John J. The Story of a House', 'an initial does not end the title');
  assert.equal(sourceTitle('Sanborn Map Company. Insurance Maps of Chicago, Illinois, Volume 3. New York: Sanborn, 1911.'),
    'Sanborn Map Company. Insurance Maps of Chicago, Illinois, Volume 3', 'a short first sentence takes the next');
  assert.equal(sourceTitle('Courtyard, Glessner House, Chicago, IL - 54201692262.jpg Photograph by w_lemay, 2024.'),
    'Courtyard, Glessner House, Chicago, IL', 'cut before a file name or a handle');
  const long = sourceTitle('Detail of Entrance Doorway, House for J. J. Glessner Esq., Chicago Ill., office copy No.23A,1885-1887; microfilm.');
  assert(long.endsWith('…') && long.length <= 81, `a long title is shortened at a word: ${long}`);
  assert.equal(sourceTitle(''), '');
  assert.equal(sourceTitle('data_file_x.json'), '', 'nothing that reads as a title: no title, and none made up');
  assert.deepEqual(_test.sentencesOf('Unknown photographer, ca. 1887. Cornell University.'),
    ['Unknown photographer, ca. 1887', 'Cornell University.'], 'an abbreviation before a number does not split');

  // Every source record in the tree: the title is clean and is the citation's own opening.
  const dir = path.join(ROOT, 'data/sources');
  let n = 0, titled = 0;
  for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.json'))) {
    const rec = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
    const cite = String(rec.citation).replace(/\s+/g, ' ').trim();
    const title = sourceTitle(rec.citation);
    n++;
    if (!title) continue;
    titled++;
    const stem = title.replace(/…$/, '');
    assert(cite.startsWith(stem), `${f}: the title is a prefix of the citation (${title})`);
    assert(clean(stem), `${f}: the title passes the visitor lint (${title})`);
    assert(!stem.includes(rec.id), `${f}: the title is not the id`);
  }
  assert(n > 300 && titled / n > 0.97, `nearly every source has a title from its citation (${titled} of ${n})`);
}

// ---- what kind of source, true by definition ---------------------------------------------
// "from the time" only where the source's own recorded date is on or before the scene's year;
// otherwise the rung's own meaning (docs/PROVENANCE.md § Evidence tiers).
assert.equal(sourceYear('1963-07-23'), 1963);
assert.equal(sourceYear('1881; accessed 2026-09-02'), 1881, 'the leading clause only');
assert.equal(sourceYear('1885-1887'), 1887, 'a span is as late as its end');
assert.equal(sourceYear('August 1963 (addendum 1985-1986)'), 1963);
assert.equal(sourceYear('undated (probably c. 1900-1930)'), null, 'undated is undated');
assert.equal(sourceYear(undefined), null);
{
  const photo = json('data/sources/habs_glessner_photo_01_nw_1963.json');
  assert.equal(photo.tier, 1, 'the 1963 HABS photograph is first-hand on the ladder');
  assert.equal(sourceTag(photo.tier, photo.date, 1904), 'first-hand', 'and is not "from the time" of a 1904 visit');
  const plate = json('data/sources/inland_architect_1888_02_glessner_exterior.json');
  assert(sourceYear(plate.date) <= 1904, `the 1888 plate is dated by 1904 (${plate.date})`);
  assert.equal(sourceTag(plate.tier, plate.date, 1904), 'from the time', 'the 1888 plate is from the time of a 1904 visit');
  const story = json('data/sources/glessner_story_of_a_house_1923.json');
  assert.equal(sourceTag(story.tier, story.date, 1904), 'a witness remembering', "Glessner's 1923 booklet remembers");
  assert.equal(sourceTag(story.tier, story.date, 1923), 'from the time', 'and is from the time of a 1923 scene');
}
assert.deepEqual([1, 2, 3, 4, 5, 6].map((k) => sourceTag(k, null, 1904)),
  ['first-hand', 'a witness remembering', 'gathered from witnesses', "a historian's account", 'a modern reconstruction', 'a popular map'],
  'an undated source says what its rung is');
assert.equal(sourceTag(1, '1834', null), 'first-hand', 'no scene year, no claim about time');
assert.equal(sourceTag(undefined, null, 1904), '', 'an unknown tier and no date say nothing');

// ---- facts, counts and the pane over a fixture --------------------------------------------
{
  const sidecar = {
    documented_range: { from: '1887-12-01', to: '1946-08-31', confidence: 'attested', sources: ['src_a'] },
    placement: { position_confidence: 'inferred', position_sources: ['src_b'], position_note: 'Read off the 1911 map.' },
    footprint: { confidence: 'attested', sources: ['src_a'], note: 'From data/research/x.json § footprint (T-1731).' },
    attributes: {
      roof_covering: { value: 'terracotta tile', confidence: 'attested', sources: ['src_a', 'src_b'] },
      brick_tint: { value: [0.36, 0.14, 0.1], confidence: 'reconstructed', sources: [], note: 'Chosen to match the photographs.' },
      present_status: { value: 'Still standing', confidence: 'attested', sources: [] },
      odd: { value: 'x', confidence: 'documented', sources: [] },
    },
    citations: [
      { source_id: 'src_a', citation: 'Historic American Buildings Survey. John J. Glessner House, 1800 S. Prairie Avenue.', tier: 4, tier_label: 'later scholarship', url: 'https://example.org/a' },
      { source_id: 'src_b', citation: 'Sanborn Map Company. Insurance Maps of Chicago, Illinois, Vol. 3 (1911), sheet 28.', tier: 1, tier_label: 'period/eyewitness' },
    ],
  };
  const summary = {
    status: { text: 'Still standing', today: 'A house museum', grade: 'attested', sources: ['src_c'] },
    built: { year: 1887, grade: 'attested', sources: ['src_a'] },
    key: [{ label: 'Architect', value: 'H. H. Richardson', grade: 'attested', sources: ['src_a'] }],
    residents: [{ name: 'John J. Glessner', role: 'Farm-machine executive', grade: 'attested', sources: ['src_c'] }],
    lookFor: [], notable: [{ text: 'A fact.', grade: 'inferred', sources: [], note: 'Worked out from the plan.' }], story: [],
  };
  const docSources = { src_c: { citation: 'Glessner House, Glessner Family (biographies). Read 16 October 2026.', tier: 4, type: 'website' } };
  const sourceDates = { src_a: '1963', src_b: '1888' };

  const facts = buildingFacts(sidecar, summary);
  assert.deepEqual(facts.slice(0, 5).map((f) => f.label), ['Today', 'Built', 'Architect', 'John J. Glessner', 'Notable fact'],
    'the front page\'s facts first, in its order');
  assert.deepEqual(facts.slice(5).map((f) => f.label), ['Stood here', 'Where it stood', 'Its outline', 'Roof covering', 'Brick tint', 'Today', 'Odd'],
    'then the record\'s claims: whether it stood, where, its outline, each attribute; renamed terms used');
  const n = factCounts(facts);
  assert.deepEqual(n, { attested: 8, inferred: 2, reconstructed: 1, other: 1, total: 12 });

  const html = sourcesPaneHtml({ sidecar, summary, docSources, liberties: [
    { id: 'L-1', title: 'courtyard roof junction', fields: [{ label: 'Decision', text: 'The **apex** is ours.' }, { label: 'Ticket', text: 'T-2016' }] },
    { id: 'L-2', title: 'The west gable', fields: [{ label: 'Decision', text: 'See `data/x.json`.' }] },
  ], questions: null, dossier: 'https://example.org/dossier.md', sourceDates, sceneYear: '1904' });
  const text = visible(html);
  assert.match(text, /^\s*12 facts\. 8 Attested, 2 Inferred, 1 Reconstructed\. Tap any one to see its sources\./, 'the header counts every fact, by grade');
  const groups = [...html.matchAll(/<section class="src-grade" data-grade="(\w+)">/g)].map((m) => m[1]);
  assert.deepEqual(groups, [...GRADES, 'other'], 'three groups in ladder order, and the off-scale one said to be a fault');
  assert.match(text, /1 carry no grade on our scale\. That is a fault in our record\./);
  const count = (g) => Number(html.match(new RegExp(`data-grade="${g}">\\s*<h3[^>]*>[\\s\\S]*?<span class="src-count">(\\d+)<`))?.[1]);
  assert.deepEqual(GRADES.map(count), [8, 2, 1], 'each group heads its own count');
  assert.equal((html.match(/<details class="src-fact"/g) ?? []).length, 12, 'every fact is a row');
  assert.match(text, /Historic American Buildings Survey\. John J\. Glessner House, 1800 S\. Prairie… a historian's account/, 'a human title and what kind of source it is (dated 1963, after 1904)');
  assert.match(text, /Sanborn Map Company\. Insurance Maps of Chicago, Illinois, Vol\. 3 \(1911\), sheet… from the time/, 'dated 1888, by the scene year');
  assert.match(text, /Glessner House, Glessner Family \(biographies\) a historian's account/, 'a summary-only source resolves through the compiled summaries');
  assert(!/\btier\b|later scholarship|period\/eyewitness/.test(text), 'no tier number or tier label');
  assert(!/src_[abc]/.test(text), 'no source id');
  assert.match(html, /<details class="src-cites"><summary>The full citations<\/summary>/, 'the full citation is folded under the fact');
  assert.match(text, /Why Read off the 1911 map\./, 'a clean reason is shown in the record\'s words');
  assert.match(text, /The reasoning for this one is written for researchers\. It is in the full record\./, 'an unclean one is pointed to, not shown');
  assert(!/T-1731|data\/research/.test(text), 'and its path and ticket never show');
  assert.match(text, /No source is named, though this grade needs one\. That is a fault in our record\./, 'an unsourced attested fact says it is a fault');
  assert.match(text, /Liberties 2 Our list of the choices we made without a source, and why\./, 'Liberties, counted, with its plain line');
  assert.match(text, /Courtyard roof junction Decision The apex is ours\./, 'a liberty by name, its visitor-facing part folded under it');
  assert(!/T-2016|L-1|L-2|data\/x\.json/.test(text), 'no liberty id, ticket or path');
  assert.match(text, /The west gable The full entry is written for researchers\./);
  assert.match(text, /Read the research dossier ↗/);
  assert.match(html, /data-insp-full/, 'a way to the full record');
  assert(!/<details[^>]*\bopen\b/.test(html), 'every row starts folded');
  assert(!/src-why|src-titles|cites/.test(closed(html)), 'before a tap, only the labels and values show');

  assert.match(visible(sourcesPaneHtml({ sidecar, liberties: null })), /Our list of liberties could not be read just now\./,
    'a list that did not load is said, never shown as empty');
  assert.match(visible(sourcesPaneHtml({ sidecar, liberties: [] })), /No liberties are written down for this building\. That does not mean none were taken\./);
  assert.equal(resolveSource('src_c', new Map(), docSources).tier, 4);
  assert.equal(resolveSource('nope', new Map(), docSources), null);
  assert.equal(_test.keyWords('frame_ft'), 'Frame (ft)');
  assert.equal(_test.valueWords({ length_ft: 1 }), '', 'a structured value is left off');
}

// ---- Glessner House, from the real tree ----------------------------------------------------
{
  const sidecar = json('data/sidecars/1904/glessner_house.json');
  const summary = json('data/summaries/glessner_house.json');
  const libs = json('data/liberties.json').liberties.filter((l) => l.subjects?.includes('glessner_house'));
  const dateOf = (id) => { try { return json(`data/sources/${id}.json`).date ?? null; } catch { return null; } };
  const ids0 = new Set([...sidecar.citations.map((c) => c.source_id), ...buildingFacts(sidecar, summary).flatMap((f) => f.sources)]);
  const sourceDates = Object.fromEntries([...ids0].map((id) => [id, dateOf(id)]).filter(([, d]) => d));
  const html = sourcesPaneHtml({ sidecar, summary, docSources: null, liberties: libs, questions: [], dossier: null, sourceDates, sceneYear: 1904 });
  const facts = buildingFacts(sidecar, summary);
  const n = factCounts(facts);
  const claims = 3 + Object.keys(sidecar.attributes).length;
  const front = 2 + ['key', 'residents', 'lookFor', 'notable', 'story'].reduce((k, f) => k + summary[f].length, 0);
  assert.equal(n.total, claims + front, 'every front-page fact and every claim on the record');
  assert(n.attested > 0 && n.inferred > 0 && n.reconstructed > 0);
  const text = visible(html);
  assert.match(text, new RegExp(`^\\s*${n.total} facts\\. ${n.attested} Attested, ${n.inferred} Inferred, ${n.reconstructed} Reconstructed\\.`));
  assert.match(text, new RegExp(`Liberties ${libs.length} `), 'every liberty recorded against the house');
  const ids = new Set([...sidecar.citations.map((c) => c.source_id), ...facts.flatMap((f) => f.sources)]);
  for (const id of ids) assert(!text.includes(id), `no source id: ${id}`);
  assert(!/\btier \d|period\/eyewitness|near-primary|later scholarship|compiled secondary/.test(text), 'no tier label');
  const shut = visible(closed(html));
  assert(!/[A-Za-z0-9]_[A-Za-z0-9]|\.json\b|\bdata\/|\bT-\d{3,}/.test(shut), `nothing id-shaped before a tap: ${shut.match(/\S*_\S*|\S*\.json|\bT-\d+/)?.[0]}`);
  // Each source tag is true by definition: "from the time" exactly where the date allows it.
  const tierOf = new Map(sidecar.citations.map((c) => [c.source_id, c.tier]));
  const expected = facts.flatMap((f) => f.sources.filter((id) => tierOf.has(id)).map((id) => sourceTag(tierOf.get(id), sourceDates[id], 1904)));
  const fromTime = expected.filter((w) => w === 'from the time').length;
  assert(fromTime > 0 && fromTime < expected.length, `some of Glessner's sources are from the time and some are not (${fromTime} of ${expected.length})`);
  assert.equal((html.match(/<span class="src-when">from the time<\/span>/g) ?? []).length, fromTime, 'and the pane says it of exactly those');
  assert(!/written later/.test(text));
  for (const term of ['Attested', 'Inferred', 'Reconstructed', 'Liberties']) assert(text.includes(term), `the locked term ${term}`);
}

console.log('test_nav_sources: OK');
