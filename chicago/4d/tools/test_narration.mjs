#!/usr/bin/env node
// T-3578: jaunt narration. The words the app shows are the words voiced (one shared script
// function, keyed by SHA-256); only changed words or voices are sent to ElevenLabs; the index
// only gains clips; and the player follows the outing, queues behind a voice still speaking,
// ducks the other buses, and stops when narration is muted.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { narrationScripts, openingScript, textKey, clipFor, clipKey, silentWav, createNarration, NARRATOR, NARRATORS, DEFAULT_NARRATOR, normalNarrator, VOICE, voiceLevel } from '../renderers/web/js/narration.js';
import { loadConfig, scriptsFor, voiceFor, plan, voice, synthesize, verify, ROOT, spokenWords, sameWords, loadDirection, directionProblems, styleProblems, loadDirectionFile, quota, quotaLine, jauntEntries, jauntIds, takeWithin } from './narrate_jaunts.mjs';

const sha = s => createHash('sha256').update(s).digest('hex');
const jaunt = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sidecars/1904/jaunts/glessner-household-tour.json'), 'utf8'));

// ---- the scripts -----------------------------------------------------------------------
{
  const scripts = narrationScripts(jaunt);
  assert.deepEqual(scripts.map(s => `${s.part}:${s.id}`),
    ['opening:opening', ...jaunt.stops.map(s => `stop:${s.id}`), ...jaunt.endings.map(e => `ending:${e.id}`), ...jaunt.stops.map(s => `onward:${s.id}`)]);
  assert.equal(scripts[1].speaker, 'glessner_john_j', 'a stop is read by its first host');
  assert.equal(scripts[0].speaker, NARRATOR); assert.equal(scripts.at(-1).speaker, NARRATOR);
  assert.equal(scripts[1].text, jaunt.stops[0].text, 'a stop is read as the panel shows it');
  assert.ok(openingScript(jaunt).startsWith('The Glessner Household.\n\nA spring morning'), 'the opening reads its title, not "JAUNT: …"');
  assert.ok(!openingScript(jaunt).includes('JAUNT:'));
  const timed = narrationScripts({ stops: [{ id: 'a', since: 'Four hours later', text: 'Noon.' }, { id: 'b', text: '  ' }] });
  assert.deepEqual(timed.filter(s => s.part !== 'onward'), [{ part: 'stop', id: 'a', speaker: NARRATOR, text: 'Four hours later. Noon.' }], 'a since is read with its stop; an empty script is none');
  assert.deepEqual(timed.filter(s => s.part === 'onward').map(s => s.id), ['a'], 'T-3755: a stop with words closes with a line; an empty one has none');
  assert.equal(await textKey('abc'), sha('abc'), 'the app\'s key is SHA-256 of the words');
  assert.equal(await textKey('x', null), null, 'no Web Crypto: no key, no narration');
}

// ---- T-3755: every stop closes with a varied line sending you on -------------------------
{
  const { onwardLines, sendsOn, ONWARD_LINES } = await import('../renderers/web/js/narration.js');
  const all = Object.values(ONWARD_LINES).flatMap(r => Object.values(r).flat());
  assert.equal(new Set(all.map(l => l[0])).size, all.length, 'no line is in the set twice');
  assert.ok(all.every(l => l.length === 2 && l.every(t => typeof t === 'string' && t.trim() === t && /[.!?]$/.test(t))), 'every line has its English and its Spanish');
  assert.ok(all.every(([en]) => !/\b(?:tap|click|button|menu|screen)\b|\bpress\b(?! on)/i.test(en)), 'the words stay in the walk: no keys or buttons');
  const lines = onwardLines(jaunt), scripts = narrationScripts(jaunt);
  assert.equal(lines.size, jaunt.stops.length, 'every stop of the household tour closes with a line');
  for (const stop of jaunt.stops) {
    const s = scripts.find(x => x.part === 'onward' && x.id === stop.id);
    assert.equal(s.speaker, NARRATOR, 'the narrator reads a closing line, after any host');
    assert.equal(s.text, lines.get(stop.id));
  }
  assert.ok(ONWARD_LINES.general.final.some(l => l[0] === lines.get(jaunt.stops.at(-1).id)), 'the last stop takes a last-stop line');
  // A long jaunt: no line twice until its kind's list has run out, and none twice running.
  const stops = Array.from({ length: 12 }, (_, i) => ({ id: `s${i}`, text: 'A plain stop of facts.', next: i < 11 ? `s${i + 1}` : '$end' }));
  const long = { id: 'long-walk', grade_band: '6-8', stops };
  const got = [...onwardLines(long).values()];
  assert.equal(new Set(got.slice(0, 11)).size, 11, 'eleven onward stops, eleven different lines');
  assert.ok(ONWARD_LINES.general.final.some(l => l[0] === got[11]));
  assert.deepEqual([...onwardLines(long).values()], got, 'the same jaunt always picks the same lines (the voicer and the app agree)');
  const young = [...onwardLines({ ...long, grade_band: '3-5' }).values()];
  assert.ok(young.every(t => Object.values(ONWARD_LINES.young).flat().some(l => l[0] === t)), 'ages 8-10 take the simpler lines');
  const es = [...onwardLines({ ...long, lang: 'es' }).values()];
  assert.ok(es.every((t, i) => all.find(l => l[1] === t)?.[0] === got[i]), 'a jaunt read in Spanish takes the same lines in Spanish');
  assert.ok(sendsOn('The lake is grey. Walk north to the brother\'s house next door.'));
  assert.ok(sendsOn('Mrs. Glessner is in the yard. To find her, walk through the tunnel under the house.'));
  assert.ok(!sendsOn('Quaife doubts the romance, not the rescue.'));
  const sent = onwardLines({ id: 'x', grade_band: '6-8', stops: [{ id: 'a', text: 'Facts. Walk north to the gate.', next: 'b' }, { id: 'b', text: 'More facts.', choices: [{ id: 'c', next: 'd' }], next: 'd' }, { id: 'd', text: 'End.', next: '$end' }] });
  assert.ok(ONWARD_LINES.general.linger.some(l => l[0] === sent.get('a')), 'a stop that already sends you on is told to look round first');
  assert.ok(ONWARD_LINES.general.choice.some(l => l[0] === sent.get('b')), 'a stop asking a choice is told to choose');
}

// ---- the index -------------------------------------------------------------------------
{
  const k = sha('words');
  const index = { version: 1, clips: { [k]: { text_sha256: k, file: 'narration/f.mp3' }, bad: { text_sha256: 'other', file: 'x.mp3' } } };
  assert.equal(clipFor(index, k).file, 'narration/f.mp3');
  assert.equal(clipFor(index, 'bad'), null, 'an entry must name the words it was made for');
  assert.equal(clipFor(index, sha('changed words')), null, 'changed words have no clip');
  // T-3578: two narrators; the visitor's choice, else the default (the essayist).
  const w = sha('narrated');
  const two = { version: 1, clips: { [`${w}~essayist`]: { text_sha256: w, file: 'narration/e.mp3' }, [`${w}~storyteller`]: { text_sha256: w, file: 'narration/s.mp3' } } };
  assert.equal(DEFAULT_NARRATOR, 'essayist');
  assert.equal(clipFor(two, w, NARRATOR, 'storyteller').file, 'narration/s.mp3', 'the chosen narrator reads');
  assert.equal(clipFor(two, w, NARRATOR).file, 'narration/e.mp3', 'the essayist is the default');
  assert.equal(clipFor({ clips: { [`${w}~essayist`]: two.clips[`${w}~essayist`] } }, w, NARRATOR, 'storyteller').file, 'narration/e.mp3', 'a narrator not yet voiced falls back to the default');
  assert.equal(clipFor(two, w, 'glessner_john_j'), null, 'a person never reads with a narrator\'s clip');
  assert.equal(clipKey(w, NARRATOR, 'nobody'), `${w}~essayist`);
  const real = loadConfig();
  assert.deepEqual(Object.keys(real.narrators), NARRATORS.map(n => n.id), 'voices.json voices every narrator the Settings choice offers');
  assert.deepEqual(Object.values(real.narrators).map(n => n.label), NARRATORS.map(n => n.label));
  // T-3627: Settings offers the narrators from narrators.js, so the boot never loads this player.
  const settingsCopy = await import('../renderers/web/js/narrators.js');
  assert.deepEqual(settingsCopy.NARRATORS, NARRATORS, 'narrators.js offers the narrators narration.js voices');
  assert.equal(settingsCopy.DEFAULT_NARRATOR, DEFAULT_NARRATOR, 'narrators.js defaults to the same narrator');
  for (const v of ['essayist', 'storyteller', 'nobody', undefined]) assert.equal(settingsCopy.normalNarrator(v), normalNarrator(v));
  const html = fs.readFileSync(path.join(ROOT, 'renderers/web/index.html'), 'utf8');
  for (const n of NARRATORS) assert.ok(html.includes(`<option value="${n.id}">${n.label}</option>`), `Settings › Sound offers ${n.label}`);
  for (const v of Object.values(real.voices)) assert.ok(v, 'every Glessner household voice is chosen (owner, 2026-11-13)');
  const wav = silentWav();
  assert.equal(String.fromCharCode(...wav.slice(0, 4)), 'RIFF'); assert.equal(wav.length, 844);
}

// ---- the plan: only what changed ---------------------------------------------------------
{
  const config = { ...loadConfig(), narrators: { essayist: { voice: 'AAAAAAAAAAAAAAAAAAAA', label: 'Cultivated Essayist' }, storyteller: { voice: null, label: 'Midwestern Storyteller' } },
    voices: { glessner_john_j: { voice: 'BBBBBBBBBBBBBBBBBBBB', voice_settings: { style: 0.3 } }, glessner_frances_m: 'Frances Voice' } };
  const every = await scriptsFor(config, { only: 'glessner-household-tour' });
  // T-3755: and each stop's closing line, the narrator's, once for each narrator.
  assert.equal(every.filter(s => s.part === 'onward').length, 14, 'seven closing lines, once for each narrator');
  {
    const twice = [...every, ...every.filter(s => s.part === 'onward').map(s => ({ ...s, jaunt: 'another-jaunt' }))];
    const once = plan(twice, config, { version: 1, clips: {} });
    assert.equal(once.todo.filter(s => s.part === 'onward').length, 7, 'T-3755: a line two jaunts share is voiced once in a run');
    assert.equal(new Set(once.todo.map(s => s.key)).size, once.todo.length, 'no clip is planned twice');
  }
  const scripts = every.filter(s => s.part !== 'onward');
  assert.equal(scripts.length, 11, 'the opening and the ending once for each narrator, each stop once (seven stops since T-3590)');
  const first = plan(scripts, config, { version: 1, clips: {} });
  assert.deepEqual(first.todo.map(s => s.id), ['opening', 'john', 'finish'], 'every chosen voice with no clip is voiced');
  assert.deepEqual(first.todo.map(s => s.key.slice(64)), ['~essayist', '', '~essayist']);
  assert.equal(first.skipped.length, 8);
  assert.match(first.skipped.find(s => s.id === 'frances').reason, /needs ELEVENLABS_API_KEY/, 'a voice name needs the key to resolve');
  assert.equal(first.chars, first.todo.reduce((n, s) => n + s.spoken.length, 0), 'what is sent (the performed words) is what is counted');
  const named = plan(scripts, config, { version: 1, clips: {} }, new Map([['frances voice', 'CCCCCCCCCCCCCCCCCCCC']]));
  assert.equal(named.todo.find(s => s.id === 'frances').voice.params.voice_id, 'CCCCCCCCCCCCCCCCCCCC', 'a name resolves to its id');
  assert.equal(voiceFor(config, 'glessner_john_j').params.voice_settings.style, 0.3, 'a speaker may override the settings');
  // Voice it (with a stand-in ElevenLabs), then plan again: nothing to do.
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'narration-'));
  const calls = [];
  const fake = async (url, init) => {
    calls.push({ url, body: JSON.parse(init.body), key: init.headers['xi-api-key'] });
    return new Response(Buffer.alloc(4000, calls.length), { status: 200 });
  };
  const old = { version: 1, clips: { keep: { text_sha256: 'keep', file: 'narration/old.mp3' } } };
  const { index, made } = await voice(first.todo, old, out, 'test-key', { fetcher: fake, now: () => '2026-11-13T00:00:00Z' });
  assert.equal(calls.length, 3);
  assert.match(calls[0].url, /\/v1\/text-to-speech\/AAAAAAAAAAAAAAAAAAAA\?output_format=mp3_44100_64$/);
  assert.equal(calls[0].body.text, scripts[0].spoken, 'the performance is sent'); assert.equal(calls[0].body.model_id, config.model_id);
  assert.ok(scripts[0].directed && scripts[0].spoken !== scripts[0].text && sameWords(scripts[0].spoken, scripts[0].text), 'performed from its direction, with the same words');
  assert.equal(calls[0].key, 'test-key');
  assert.ok(index.clips.keep, 'the index only gains clips: an older build still finds its own');
  for (const file of made) assert.ok(fs.existsSync(path.join(out, file)));
  const john = index.clips[scripts.find(s => s.id === 'john').text_sha256];
  assert.equal(john.file, `narration/${john.sha256}.mp3`, 'a clip is named by its bytes');
  assert.equal(clipFor(index, await textKey(narrationScripts(jaunt)[1].text), 'glessner_john_j'), john, 'the app finds the clip the tool made');
  assert.equal(clipFor(index, await textKey(narrationScripts(jaunt)[0].text), NARRATOR, 'storyteller').narrator, 'essayist', 'and the essayist\'s opening for a storyteller listener until the storyteller is voiced');
  assert.deepEqual(plan(scripts, config, index).todo, [], 'unchanged words and voices cost nothing');
  const revoiced = plan(scripts, { ...config, narrators: { ...config.narrators, storyteller: { voice: 'DDDDDDDDDDDDDDDDDDDD' } } }, index);
  assert.deepEqual(revoiced.todo.map(s => `${s.id}~${s.narrator}`), ['opening~storyteller', 'finish~storyteller'], 'a newly chosen narrator voices only its own scripts');
  const edited = scripts.map(s => s.id === 'john' ? { ...s, text: s.text + ' Good day.', text_sha256: sha(s.text + ' Good day.'), key: sha(s.text + ' Good day.') } : s);
  assert.deepEqual(plan(edited, config, index).todo.map(s => s.id), ['john'], 'changed words re-voice only that stop');
  const redirected = scripts.map(s => s.id === 'john' ? { ...s, spoken: s.spoken.replace('[chuckles]', '[laughs]'), spoken_sha256: sha(s.spoken.replace('[chuckles]', '[laughs]')) } : s);
  assert.deepEqual(plan(redirected, config, index).todo.map(s => s.id), ['john'], 'a changed direction re-voices only that stop');
  const plainIndex = { ...index, clips: Object.fromEntries(Object.entries(index.clips).map(([k, c]) => [k, { ...c, spoken_sha256: undefined }])) };
  assert.ok(plan(scripts, config, plainIndex).todo.length > 0, 'a clip read from the plain words is re-voiced once its script is directed');
  // Verify reads the public host: the bytes and the index must both be served.
  const served = new Map([...made.map(f => [f, fs.readFileSync(path.join(out, f))]), ['narration/index.json', fs.readFileSync(path.join(out, 'narration/index.json'))]]);
  const host = async url => { const key = new URL(url).pathname.slice(1); return served.has(key) ? new Response(served.get(key)) : new Response('', { status: 404 }); };
  assert.deepEqual(await verify(out, 'https://media.test/', host), []);
  served.delete(made[0]);
  assert.match((await verify(out, 'https://media.test/', host))[0], /HTTP 404/);
  // A busy ElevenLabs is retried; a refusal is reported with its status.
  let n = 0;
  const busy = async () => (++n < 3 ? new Response('busy', { status: 429 }) : new Response(Buffer.alloc(2000), { status: 200 }));
  assert.equal((await synthesize('k', first.todo[0], busy, { wait: async () => {} })).length, 2000);
  await assert.rejects(synthesize('k', first.todo[0], async () => new Response('no', { status: 401 }), { wait: async () => {} }), /HTTP 401/);
}

// ---- direction: the same words, performed ----------------------------------------------
{
  assert.deepEqual(spokenWords("[warmly] Good morning... I'm John — 1887!"), ['good', 'morning', 'i', 'm', 'john', '1887']);
  assert.ok(sameWords("Hello! I'm here.", "[cheerfully] Hello... [laughs] I'm — here!"), 'tags, pauses and punctuation are the performance');
  assert.ok(!sameWords('Hello there.', '[cheerfully] Hello over there.'), 'a word added is refused');
  const scripts = [{ jaunt: 'j', part: 'stop', id: 'a', text: 'One two.' }, { jaunt: 'j', part: 'stop', id: 'b', text: 'Three.' }];
  assert.deepEqual(directionProblems(scripts, { j: { 'stop:a': '[sighs] One... two.' } }), []);
  assert.match(directionProblems(scripts, { j: { 'stop:a': 'One two three.' } })[0], /words differ/);
  assert.match(directionProblems(scripts, { j: { 'stop:z': 'Four.' } })[0], /does not have/);
  assert.match(directionProblems([{ jaunt: 'j', part: 'onward', id: 'a', text: 'Go on.' }], { j: { 'onward:a': '[warmly] Go on.' } })[0], /no direction of its own/, 'T-3755: a shared closing line is never directed per jaunt');
  // Every voiced jaunt's direction still matches the words its panel shows. A script edited
  // without its direction fails here: bring the direction along (same words, tags kept).
  const config = loadConfig(), all = await scriptsFor(config);
  const problems = directionProblems(all, Object.fromEntries(jauntIds(config).map(id => [id, loadDirection(id)])));
  assert.deepEqual(problems, [], `data/narration/direction/ is out of step with the jaunts:\n${problems.join('\n')}`);
  assert.equal(config.model_id, 'eleven_v3', 'directions carry v3 audio tags, which only eleven_v3 performs');
  // T-3696: the smooth style. A file marked "style": "smooth" breathes between subjects and keeps
  // laughter and whispering down; every direction written from now on is marked so.
  const twenty = 'one two three four five six seven eight nine ten '.repeat(6);
  assert.deepEqual(styleProblems('j', { scripts: { 'stop:a': `[whispers] ${twenty}` } }), [], 'an unmarked (older) file is not held to it');
  const bad = styleProblems('j', { style: 'smooth', scripts: { 'stop:a': `[whispers] ${twenty} [laughs] [chuckles]` } });
  assert.equal(bad.length, 3, bad.join('; '));
  assert.deepEqual(styleProblems('j', { style: 'smooth', scripts: { 'stop:a': `${twenty.slice(0, 120)} [short pause] ${twenty.slice(120)}... [laughs] done.` } }), []);
  for (const id of jauntIds(config)) {
    const problems = styleProblems(id, loadDirectionFile(id));
    assert.deepEqual(problems, [], `data/narration/direction/${id}.json is marked smooth but:\n${problems.join('\n')}`);
  }
  assert.equal(loadDirectionFile('glessner-household-tour-grades-3-5')?.style, 'smooth', 'the 3rd-grade Glessner Household is performed in the smooth style (owner, 2026-11-19)');
  assert.ok([0, 0.5, 1].includes(config.voice_settings.stability), 'eleven_v3 takes stability 0, 0.5 or 1');
}

// ---- narrators per jaunt (T-3696: Essayist only first, the owner 2026-11-19) ----------------
{
  const cfg = { narrators: { essayist: {}, storyteller: {} }, jaunts: ['a', { id: 'b', narrators: ['essayist'] }, { id: 'c' }] };
  assert.deepEqual(jauntEntries(cfg), [{ id: 'a', narrators: ['essayist', 'storyteller'] }, { id: 'b', narrators: ['essayist'] }, { id: 'c', narrators: ['essayist', 'storyteller'] }]);
  const config = loadConfig(), all = await scriptsFor(config);
  for (const j of jauntEntries(config)) {
    const told = new Set(all.filter(s => s.jaunt === j.id && s.narrator).map(s => s.narrator));
    assert.deepEqual([...told].sort(), [...j.narrators].sort(), `${j.id}: narrator scripts are voiced in exactly its narrators`);
  }
}

// ---- the quota (T-3696) ----------------------------------------------------------------
{
  const ok = async () => new Response(JSON.stringify({ tier: 'creator', character_count: 40000, character_limit: 100000, next_character_count_reset_unix: 1796083200 }), { status: 200 });
  const q = await quota('k', ok);
  assert.deepEqual(q, { tier: 'creator', used: 40000, limit: 100000, resets: new Date(1796083200 * 1000).toISOString() });
  assert.match(quotaLine(q, 'now'), /40000 of 100000 credits used this period \(60000 left, plan creator, resets /);
  const denied = await quota('k', async () => new Response('no', { status: 401 }));
  assert.equal(denied.error, 'HTTP 401');
  assert.match(quotaLine(denied, 'now'), /not readable/);
  assert.equal((await quota('k', async () => { throw Error('offline'); })).error, 'offline', 'a failed quota read never fails the run');
  const todo = [{ text: 'a'.repeat(400) }, { spoken: 'b'.repeat(500), text: 'b' }, { text: 'c'.repeat(100) }];
  assert.deepEqual(takeWithin(todo, 1000).chars, 1000, 'everything fits');
  const part = takeWithin(todo, 850);
  assert.equal(part.batch.length, 1, 'stops at the first clip that does not fit, keeping the order');
  assert.equal(part.rest.length, 2);
  assert.equal(takeWithin(todo, 0).batch.length, 0, 'no credits left: nothing voiced, nothing fails');
}
{
  // A refusal part way (credits run out) keeps and indexes what was already voiced.
  const config = loadConfig(), all = await scriptsFor(config);
  const names = new Map([...Object.values(config.voices), ...Object.values(config.narrators).map(n => n.voice)].map((v, i) => [v.replace(/\s+/g, ' ').trim().toLowerCase(), `v${String(i).padStart(19, '0')}`]));
  const work = plan(all, config, { version: 1, clips: {} }, names).todo.slice(0, 3);
  assert.equal(work.length, 3);
  {
    let n = 0;
    const out = fs.mkdtempSync(path.join(os.tmpdir(), 'narr-stop-'));
    const twoThenBroke = async () => (++n <= 2 ? new Response(Buffer.alloc(2000 + n), { status: 200 }) : new Response('{"detail":{"status":"quota_exceeded"}}', { status: 401 }));
    const r = await voice(work, { version: 1, clips: {} }, out, 'k', { fetcher: twoThenBroke });
    assert.equal(r.made.length, 2, 'the two voiced clips are kept');
    assert.match(r.stopped.error, /HTTP 401/);
    assert.equal(Object.keys(JSON.parse(fs.readFileSync(path.join(out, 'narration/index.json'), 'utf8')).clips).length, 2, 'and indexed for the upload');
    fs.rmSync(out, { recursive: true, force: true });
  }
}

// ---- the player ------------------------------------------------------------------------
{
  const k = await textKey(narrationScripts(jaunt)[1].text), k2 = await textKey(narrationScripts(jaunt)[2].text);
  const index = { version: 1, clips: { [k]: { text_sha256: k, file: 'narration/a.mp3' }, [k2]: { text_sha256: k2, file: 'narration/b.mp3' } } };
  const fetcher = async () => new Response(JSON.stringify(index));
  class FakeAudio extends EventTarget { constructor() { super(); this.src = ''; this.paused = true; this.plays = []; }
    play() { this.paused = false; this.plays.push(this.src); return Promise.resolve(); } pause() { this.paused = true; }
    removeAttribute(n) { if (n === 'src') this.src = ''; } load() {} }
  let el, audible = true, ducked = [], routedTo = null;
  const ctx = { createMediaElementSource: e => ({ connect: bus => { routedTo = bus; }, disconnect() {} }) };
  globalThis.URL.createObjectURL ??= () => 'blob:silence'; globalThis.URL.revokeObjectURL ??= () => {};
  const n = createNarration({ fetcher, location: Promise.resolve(new URL('https://media.test/narration/index.json')),
    media: () => (el = new FakeAudio()), speech: () => ({ ctx, bus: 'bus', audible }), duck: on => ducked.push(on) });
  let changes = 0; n.on(() => changes++);
  await n.prepare(jaunt);
  assert.ok(n.clip(jaunt, 'stop', 'john')); assert.equal(n.clip(jaunt, 'stop', 'kate'), null, 'an unvoiced stop offers nothing');
  assert.ok(changes > 0, 'finding clips repaints the panel');
  n.at(jaunt, 'stop', 'john');
  assert.equal(el.src, 'https://media.test/narration/a.mp3', 'arriving with narration audible plays the stop');
  assert.equal(routedTo, 'bus', 'through the Narration bus'); assert.deepEqual(ducked, [true]);
  assert.ok(n.isPlaying(jaunt, 'stop', 'john'));
  n.at(jaunt, null); assert.ok(n.isPlaying(jaunt, 'stop', 'john'), 'travelling on does not cut a voice off');
  n.at(jaunt, 'stop', 'frances');
  assert.equal(n.state.queued, `${jaunt.id}:stop:frances`, 'the next stop waits for the voice still speaking');
  el.dispatchEvent(new Event('ended'));
  assert.equal(el.src, 'https://media.test/narration/b.mp3', 'and starts when it ends');
  await n.toggle(jaunt, 'stop', 'frances'); assert.equal(n.state.playing, null, 'Listen again stops it'); assert.equal(ducked.at(-1), false);
  n.at(jaunt, 'stop', 'frances'); assert.equal(n.state.playing, null, 'arriving where you already are does not restart it');
  audible = false; n.at(jaunt, 'stop', 'john'); assert.equal(n.state.playing, null, 'with narration muted nothing starts by itself');
  // T-3735 (the owner, 2026-11-23): a telling for another age, with the very same words, plays
  // nothing unless that telling is voiced itself: never another telling's recording.
  {
    audible = true;
    const other = { ...jaunt, id: `${jaunt.id}-grades-11-12` };
    let asked = [];
    const t = createNarration({ fetcher, location: Promise.resolve(new URL('https://media.test/narration/index.json')),
      media: () => (el = new FakeAudio()), speech: () => ({ ctx, bus: 'bus', audible }),
      voiced: async j => { asked.push(j.id); return j.id === jaunt.id; } });
    await t.prepare(jaunt); await t.prepare(other);
    assert.deepEqual(asked, [jaunt.id, other.id], 'each telling is asked whether it is voiced');
    assert.ok(t.clip(jaunt, 'stop', 'john'), 'the voiced telling keeps its clips');
    for (const s of narrationScripts(other)) assert.equal(t.clip(other, s.part, s.id), null, `${s.part}:${s.id}: an unvoiced telling offers no clip, though its words match`);
    t.at(other, 'opening', 'opening'); t.at(other, 'stop', 'john');
    assert.equal(t.state.playing, null, 'arriving in an unvoiced telling plays nothing');
    assert.equal(t.seconds(other, 'stop', 'john'), null, 'and times no voice');
    assert.equal(await t.toggle(other, 'stop', 'john'), false, 'a Listen tap there plays nothing either');
    // T-3735 (the owner, 2026-11-23): "when you switch tabs to an age that has its own recording,
    // it should start playing that recording": a part shown in a voiced telling's words is read
    // in that telling's voice, at once; one shown in an unvoiced telling's words, in none.
    {
      const younger = { ...jaunt, id: `${jaunt.id}-grades-3-5`, stops: jaunt.stops.map((s, i) => (i === 1 ? { ...s, text: 'Frances says hello.' } : s)) };
      const ks = narrationScripts(younger).find(s => s.part === 'stop' && s.id === younger.stops[1].id);
      const ky = await textKey(ks.text);
      const both = { version: 1, clips: { ...index.clips, [ky]: { text_sha256: ky, file: 'narration/y.mp3' } } };
      const r = createNarration({ fetcher: async () => new Response(JSON.stringify(both)), location: Promise.resolve(new URL('https://media.test/narration/index.json')),
        media: () => (el = new FakeAudio()), speech: () => ({ ctx, bus: 'bus', audible }), voiced: async j => j.id !== other.id });
      audible = true;
      await r.prepare(jaunt);
      const sid = jaunt.stops[1].id;
      r.at(jaunt, 'stop', sid); assert.match(el.src, /b\.mp3$/, 'its own words: its own voice');
      await r.retell(jaunt, 'stop', sid, { jaunt: younger, part: 'stop', id: sid });
      assert.match(el.src, /y\.mp3$/, 'another age with its own recording: that recording plays at once');
      assert.equal(r.state.playing, `${jaunt.id}:stop:${sid}`, 'as this stop (Pause, the meter and the mouths follow it)');
      const plays = el.plays.length;
      await r.retell(jaunt, 'stop', sid, { jaunt: younger, part: 'stop', id: sid });
      assert.equal(el.plays.length, plays, 'the same age again restarts nothing');
      await r.retell(jaunt, 'stop', sid, { jaunt: { ...other }, part: 'stop', id: sid });
      assert.equal(r.state.playing, null, 'an age whose telling is not voiced: the voice stops'); assert.equal(r.clip(jaunt, 'stop', sid), null, 'and offers no Listen');
      await r.retell(jaunt, 'stop', sid, false);
      assert.equal(r.clip(jaunt, 'stop', sid), null, 'words no telling says: no voice');
      await r.retell(jaunt, 'stop', sid, null);
      assert.match(el.src, /b\.mp3$/, 'back to its own age: its own voice again');
      r.stop(); audible = false;
    }
    const u = createNarration({ fetcher, location: Promise.resolve(new URL('https://media.test/narration/index.json')),
      media: () => (el = new FakeAudio()), speech: () => ({ ctx, bus: 'bus', audible }), voiced: () => { throw Error('no catalog'); } });
    await u.prepare(jaunt);
    assert.equal(u.clip(jaunt, 'stop', 'john'), null, 'a telling whose voicing cannot be known stays silent');
    audible = false;
  }
  let woke = 0;
  const m = createNarration({ fetcher, location: Promise.resolve(new URL('https://media.test/narration/index.json')),
    media: () => (el = new FakeAudio()), speech: () => ({ ctx, bus: 'bus', audible }), wake: () => { woke++; audible = true; } });
  await m.prepare(jaunt);
  await m.toggle(jaunt, 'stop', 'john');
  assert.equal(woke, 1, 'a Listen tap wakes sound'); assert.match(el.plays[0], /^blob:/, 'and primes the element inside the tap');
  assert.ok(m.isPlaying(jaunt, 'stop', 'john'));
  audible = false; el.dispatchEvent(new Event('timeupdate'));
  assert.equal(m.state.playing, null, 'muting narration ends the voice');
  // The first Start: the panel names the opening before the index has loaded. The opening
  // still plays once its clip is known, and the first stop's voice waits behind it.
  {
    const k0 = await textKey(narrationScripts(jaunt)[0].text);
    const first = { version: 1, clips: { ...index.clips, [`${k0}~${DEFAULT_NARRATOR}`]: { text_sha256: k0, file: 'narration/o.mp3' } } };
    audible = true;
    const f = createNarration({ fetcher: async () => new Response(JSON.stringify(first)), location: Promise.resolve(new URL('https://media.test/narration/index.json')),
      media: () => (el = new FakeAudio()), speech: () => ({ ctx, bus: 'bus', audible }) });
    let repaint = () => {}; f.on(() => repaint());
    const ready = f.prepare(jaunt);
    f.at(jaunt, 'opening', 'opening');
    assert.equal(f.state.playing, null, 'nothing to play before the index is read');
    repaint = () => f.at(jaunt, 'opening', 'opening');      // what jaunt-panel.js does on a narration change
    await ready;
    assert.equal(f.state.playing, `${jaunt.id}:opening:opening`, 'the opening speaks once its clip is known');
    assert.equal(el.src, 'https://media.test/narration/o.mp3');
    repaint = () => {};
    f.at(jaunt, null); f.at(jaunt, 'stop', 'john');
    assert.equal(f.state.queued, `${jaunt.id}:stop:john`, 'landing at the first stop queues its host behind the opening');
    el.dispatchEvent(new Event('ended'));
    assert.equal(f.state.playing, `${jaunt.id}:stop:john`, 'and John speaks when the narrator finishes');
    f.at(jaunt, 'stop', 'john'); el.dispatchEvent(new Event('ended'));
    f.at(jaunt, 'stop', 'john'); assert.equal(f.state.playing, null, 'a repaint after he finishes does not start him again');
  }
  // A flight shorter than the index's load: the outing has landed at John before any clip is
  // known. The narrator still reads the opening first, and John follows.
  {
    const k0 = await textKey(narrationScripts(jaunt)[0].text);
    const first = { version: 1, clips: { ...index.clips, [`${k0}~${DEFAULT_NARRATOR}`]: { text_sha256: k0, file: 'narration/o.mp3' } } };
    audible = true;
    const g = createNarration({ fetcher: async () => new Response(JSON.stringify(first)), location: Promise.resolve(new URL('https://media.test/narration/index.json')),
      media: () => (el = new FakeAudio()), speech: () => ({ ctx, bus: 'bus', audible }) });
    let shown = ['opening', 'opening']; g.on(() => g.at(jaunt, ...shown));
    const ready = g.prepare(jaunt);
    g.at(jaunt, 'opening', 'opening'); g.at(jaunt, null);
    shown = ['stop', 'john']; g.at(jaunt, 'stop', 'john');
    await ready;
    assert.equal(g.state.playing, `${jaunt.id}:opening:opening`, 'landing before the index loads still plays the opening first');
    assert.equal(g.state.queued, `${jaunt.id}:stop:john`, 'with John after it');
    el.dispatchEvent(new Event('ended'));
    assert.equal(g.state.playing, `${jaunt.id}:stop:john`);
    // Next Stop during the opening passes over it: the opening is not played again later.
    const h = createNarration({ fetcher: async () => new Response(JSON.stringify(first)), location: Promise.resolve(new URL('https://media.test/narration/index.json')),
      media: () => (el = new FakeAudio()), speech: () => ({ ctx, bus: 'bus', audible }) });
    await h.prepare(jaunt);
    h.at(jaunt, 'opening', 'opening'); assert.equal(h.state.playing, `${jaunt.id}:opening:opening`);
    h.stop(); h.at(jaunt, 'stop', 'john');
    assert.equal(h.state.playing, `${jaunt.id}:stop:john`, 'after Next the stop speaks, the opening does not come back');
    h.stop(); assert.equal(h.state.playing, null, 'Next Stop cuts the voice off'); assert.equal(h.state.queued, null);
  }
  // T-3553: who is speaking now and how loud, for their mouth (jaunt-hosts.js `speak`). The
  // level is listened for on the voice itself, before the bus's volume; a stop's voice is its
  // first host's, the opening's the narrator's.
  {
    // The figures the liberty states (L-host-speaks-3553: "0.012 and under is shut, 0.3 is the
    // widest", "about a fiftieth of a second"): a change here is a change to say there.
    assert.deepEqual({ ...VOICE }, { window: 1024, floor: 0.012, full: 0.3, deaf_s: 2 });
    const wave = amp => Uint8Array.from({ length: VOICE.window }, (_, i) => 128 + Math.round(127 * amp * Math.sin(i / 3)));
    const still = new Uint8Array(VOICE.window).fill(128), loud = wave(0.6);
    assert.equal(voiceLevel(still), 0, 'silence is a shut mouth');
    assert.equal(voiceLevel(loud), 1, 'a full voice is a full level');
    const soft = voiceLevel(wave(0.19));   // a root mean square of 0.13: the middle of the recorded voices
    assert(soft > 0.3 && soft < 0.5, `a voice at its middle opens the jaw part of the way (${soft})`);
    assert(voiceLevel(wave(0.1)) < soft && voiceLevel(wave(0.3)) > soft, 'louder is wider');
    assert.equal(voiceLevel(new Uint8Array(0)), 0);
    // "0.012 and under is shut": a hiss at the floor moves nothing, and the level is counted from there.
    const rms = amp => Math.sqrt(wave(amp).reduce((a, x) => a + ((x - 128) / 128) ** 2, 0) / VOICE.window);
    assert(rms(0.016) > 0.008 && rms(0.016) <= VOICE.floor && voiceLevel(wave(0.016)) === 0, `a sound at the floor is a shut mouth (${rms(0.016)})`);
    assert(Math.abs(voiceLevel(wave(0.19)) - (rms(0.19) - VOICE.floor) / (VOICE.full - VOICE.floor)) < 1e-9, 'and a level is what the sound is over the floor');
    const k0 = await textKey(narrationScripts(jaunt)[0].text);
    const withOpening = { version: 1, clips: { ...index.clips, [`${k0}~${DEFAULT_NARRATOR}`]: { text_sha256: k0, file: 'narration/o.mp3' } } };
    const media = () => { el = new FakeAudio(); el.currentTime = 0; return el; };
    const where = Promise.resolve(new URL('https://media.test/narration/index.json'));
    let heard = still, ears = 0, fed = [], cut = 0;
    const hearing = () => ({ createMediaElementSource: () => ({ connect: to => fed.push(to), disconnect() { cut++; } }),
      createAnalyser: () => { ears++; return { fftSize: 0, getByteTimeDomainData: out => out.set(heard) }; } });
    let context = hearing();
    audible = true;
    const v = createNarration({ fetcher: async () => new Response(JSON.stringify(withOpening)), location: where, media, speech: () => ({ ctx: context, bus: 'bus', audible }) });
    await v.prepare(jaunt);
    assert.equal(v.voice(), null, 'nobody speaks before a clip plays');
    // The usual first minute: the narrator's opening plays, John's stop is shown and queued behind it.
    v.at(jaunt, 'opening', 'opening');
    v.at(jaunt, 'stop', 'john');
    assert.deepEqual([v.state.playing, v.state.queued, v.state.at], ['glessner-household-tour:opening:opening', 'glessner-household-tour:stop:john', 'glessner-household-tour:stop:john']);
    heard = loud;
    assert.deepEqual(v.voice(), { speaker: NARRATOR, level: 1 }, 'the voice is the clip that sounds, not the part shown or the one queued: the opening is the narrator\'s');
    assert.equal(ears, 1, 'one ear on the voice');
    assert.deepEqual([fed[0], fed[1].fftSize], ['bus', VOICE.window], 'the voice goes to the bus as before, and to the ear beside it');
    heard = still;
    el.dispatchEvent(new Event('ended'));
    assert.equal(v.state.playing, 'glessner-household-tour:stop:john');
    assert.deepEqual(v.voice(), { speaker: 'glessner_john_j', level: 0 }, 'then the stop\'s voice is its first host\'s; nothing heard of it yet, the level is none');
    assert.deepEqual([ears, fed.length, cut], [1, 2, 0], 'the next clip is heard by the same ear: none is added, nothing re-wired');
    heard = loud;
    assert.deepEqual(v.voice(), { speaker: 'glessner_john_j', level: 1 });
    // Held paused from outside (a media key, a call): nobody's voice, and theirs again when it sounds.
    el.paused = true;
    assert.equal(v.voice(), null, 'a clip that is not sounding is nobody\'s voice');
    assert.equal(v.state.playing, 'glessner-household-tour:stop:john', 'the player still has it');
    el.paused = false;
    assert.equal(v.voice()?.speaker, 'glessner_john_j');
    // A clip whose data stops arriving waits, unpaused and silent: nobody's voice until it plays
    // again (by the element's word, or by its time moving with data in hand).
    el.dispatchEvent(new Event('waiting'));
    assert.deepEqual([v.voice(), el.paused, v.state.playing], [null, false, 'glessner-household-tour:stop:john'], 'a clip waiting for data is nobody\'s voice, and the player still has it');
    el.dispatchEvent(new Event('playing'));
    assert.deepEqual(v.voice(), { speaker: 'glessner_john_j', level: 1 }, 'and theirs again when it plays');
    el.dispatchEvent(new Event('waiting'));
    for (const state of [0, 1, 2]) {
      el.readyState = state; el.dispatchEvent(new Event('timeupdate'));
      assert.equal(v.voice(), null, `time told with no data for the next moment in hand (${state}) is still waiting`);
    }
    el.readyState = 3; el.dispatchEvent(new Event('timeupdate'));
    assert.equal(v.voice()?.speaker, 'glessner_john_j', 'time moving with data for the next moment in hand (3) is playing');
    el.dispatchEvent(new Event('waiting'));
    assert.equal(v.voice(), null);
    el.readyState = 4; el.dispatchEvent(new Event('timeupdate'));
    assert.equal(v.voice()?.speaker, 'glessner_john_j', 'and so is time moving with data enough to play through (4)');
    el.dispatchEvent(new Event('waiting'));
    v.stop(); v.at(jaunt, 'stop', 'frances'); v.toggle(jaunt, 'stop', 'john'); await Promise.resolve(); await Promise.resolve();
    assert.equal(v.voice()?.speaker, 'glessner_john_j', 'a clip begun afresh is not held to the last one\'s wait');
    v.stop();
    assert.equal(v.voice(), null, 'a stopped voice is nobody\'s');
    // The page's sound made anew (another context): the old wiring is cut and a new ear listens.
    context = hearing();
    v.toggle(jaunt, 'stop', 'john'); await new Promise(r => setTimeout(r));
    assert.deepEqual([ears, cut, v.voice()?.speaker], [2, 1, 'glessner_john_j']);
    v.end();
    // An ear that hears nothing at all (every sample at rest) while the clip plays cannot listen:
    // the mouth is shut for the clip's first moments, then the level is not known. What it hears
    // later counts, and each clip is judged afresh.
    heard = still;
    v.toggle(jaunt, 'stop', 'john'); await new Promise(r => setTimeout(r));
    el.currentTime = VOICE.deaf_s - 0.5;
    assert.deepEqual(v.voice(), { speaker: 'glessner_john_j', level: 0 });
    el.currentTime = VOICE.deaf_s + 0.5;
    assert.deepEqual(v.voice(), { speaker: 'glessner_john_j', level: null }, 'an ear that has heard nothing this far in is deaf: the mouth keeps its own run of syllables');
    heard = wave(0.19);
    assert(v.voice().level > 0.3, 'what it hears after all is the level');
    heard = still;
    assert.deepEqual(v.voice(), { speaker: 'glessner_john_j', level: 0 }, 'and a pause in a voice it has heard is a shut mouth, however late');
    v.stop();
    v.toggle(jaunt, 'stop', 'john'); await new Promise(r => setTimeout(r));
    el.currentTime = VOICE.deaf_s + 0.5;
    assert.equal(v.voice().level, null, 'the next clip is judged afresh');
    v.end();
    // A page whose audio has no analyser: the speaker is known, the level is not.
    const deaf = createNarration({ fetcher, location: where, media, speech: () => ({ ctx, bus: 'bus', audible }) });
    await deaf.prepare(jaunt);
    deaf.at(jaunt, 'stop', 'john');
    assert.deepEqual(deaf.voice(), { speaker: 'glessner_john_j', level: null }, 'with no ear the mouth keeps its own run of syllables');
    // ...one whose analyser cannot be made is the same, and so is one whose read throws: the
    // frame that asks is never thrown out of.
    for (const ear of [() => { throw Error('no'); }, () => ({ fftSize: 0, getByteTimeDomainData() { throw Error('no'); } })]) {
      const b = createNarration({ fetcher, location: where, media, speech: () => ({ ctx: { createMediaElementSource: () => ({ connect() {}, disconnect() {} }), createAnalyser: ear }, bus: 'bus', audible }) });
      await b.prepare(jaunt);
      b.at(jaunt, 'stop', 'john');
      assert.deepEqual(b.voice(), { speaker: 'glessner_john_j', level: null });
    }
  }
  const none = createNarration({ fetcher: async () => new Response('', { status: 404 }), location: Promise.resolve(new URL('https://media.test/narration/index.json')) });
  await none.prepare(jaunt);
  assert.equal(none.clip(jaunt, 'stop', 'john'), null); assert.equal(none.state.index, 'unavailable', 'no index: nothing offered, nothing thrown');
}

// ---- T-3755: the player reads a stop's closing line straight after the stop -------------
{
  const scripts = narrationScripts(jaunt);
  const said = (part, id) => scripts.find(s => s.part === part && s.id === id).text;
  const clips = {};
  for (const [part, id] of [['stop', 'john'], ['onward', 'john'], ['stop', 'frances'], ['onward', 'frances']]) {
    const sha = await textKey(said(part, id));
    clips[clipKey(sha, part === 'onward' ? NARRATOR : 'x')] = { text_sha256: sha, file: `narration/${part}-${id}.mp3`, bytes: 8000, output_format: 'mp3_44100_64' };
  }
  class FakeAudio extends EventTarget { constructor() { super(); this.src = ''; this.paused = true; } play() { this.paused = false; return Promise.resolve(); }
    pause() { this.paused = true; } removeAttribute(n) { if (n === 'src') this.src = ''; } load() {} }
  let el;
  const ctx = { createMediaElementSource: () => ({ connect() {}, disconnect() {} }) };
  const p = createNarration({ fetcher: async () => new Response(JSON.stringify({ version: 1, clips })), location: Promise.resolve(new URL('https://media.test/narration/index.json')),
    media: () => (el = new FakeAudio()), speech: () => ({ ctx, bus: 'bus', audible: true }) });
  await p.prepare(jaunt);
  p.at(jaunt, 'stop', 'john');
  assert.equal(el.src, 'https://media.test/narration/stop-john.mp3');
  el.dispatchEvent(new Event('ended'));
  assert.equal(el.src, 'https://media.test/narration/onward-john.mp3', 'the stop heard to its end goes on into its closing line');
  assert.ok(p.isPlaying(jaunt, 'onward', 'john'));
  assert.equal(p.voice().speaker, NARRATOR, 'read by the narrator, so the host\'s mouth stops');
  el.dispatchEvent(new Event('ended'));
  assert.deepEqual(p.position(jaunt, 'stop', 'john'), { done: true }, 'the stop\'s meter stays full after its closing line');
  assert.equal(p.state.playing, null, 'and nothing after it');
  // Moving on while the stop speaks: its closing line is not read at the next stop.
  p.at(jaunt, 'stop', 'frances');
  assert.equal(el.src, 'https://media.test/narration/stop-frances.mp3');
  p.stop(); p.at(jaunt, null);
  assert.equal(p.state.playing, null);
  // A stop whose voice the visitor moved away from (a Listen replay elsewhere) does not trail its line.
  await p.toggle(jaunt, 'stop', 'john');
  assert.equal(el.src, 'https://media.test/narration/stop-john.mp3');
  el.dispatchEvent(new Event('ended'));
  assert.equal(p.state.playing, null, 'heard away from its stop, no closing line follows');
}

// ---- T-3812: street talk -----------------------------------------------------------------
{
  const ST = await import('../renderers/web/js/street-talk.js');
  const B = await import('./build_street_talk.mjs');
  // The built file is the source's: an edit to the lines (or to who speaks) is rebuilt.
  for (const scene of B.SCENES) {
    const { problems, doc } = B.build(scene);
    assert.deepEqual(problems, [], `street talk ${scene}`);
    assert.equal(fs.readFileSync(B.outPath(scene), 'utf8'), B.body(doc), `data/narration/street/${scene}.json is stale: node tools/build_street_talk.mjs`);
    for (const id of Object.keys(loadConfig().voices)) assert.ok(!doc.people[id], `${id} speaks in their own voice, never a stock one`);
    for (const l of doc.lines) assert.ok(l.text.length <= B.MAX_CHARS && !/\[/.test(l.text), `${l.id}: short, plain words`);
  }
  assert.equal(B.voiceOf(B.readTeller('child/m/a9')), null, 'children are not voiced');
  assert.equal(B.voiceOf(B.readTeller('young_lady,child/f/a17')), null);
  assert.equal(B.voiceOf(B.readTeller('cook,maid/f/a45/oirish')), 'cook');
  assert.equal(B.voiceOf(B.readTeller('maid/f/a50')), 'cook', 'an older maid speaks in the older voice');
  assert.equal(B.voiceOf(B.readTeller('maid/f/a21/oirish')), 'maid');
  assert.equal(B.voiceOf(B.readTeller('groom,coachman,manservant/m/a30')), 'manservant');
  assert.equal(B.parseLines('gent greet | Hi.\ngent greet | Hi.').problems.length, 1, 'one voice says the same words once');
  assert.deepEqual(B.parseLines('gent greet | Hi.\nlady greet | Hi.').problems, [], 'two voices may say the same words');
  assert.match(B.parseLines('gent remark | In 1912 we shall see.').problems[0], /after 1904/);
  // Keyed by words AND voice: "Good morning." in two voices is two recordings.
  const k = await textKey('Good morning.');
  assert.notEqual(ST.streetKey(k, 'gent'), ST.streetKey(k, 'lady'));
  // The voicer lists each line once, in its voice, when voices.json lists the scene's street talk.
  const config = { ...loadConfig(), street: ['1904'] };
  const street = (await scriptsFor(config, { only: 'street-1904' }));
  const doc = JSON.parse(fs.readFileSync(B.outPath('1904'), 'utf8'));
  assert.equal(street.length, doc.lines.length);
  assert.ok(street.every(s => s.part === 'street' && s.speaker.startsWith('street:') && s.key.endsWith(`@${s.speaker}`)));
  assert.equal(new Set(street.map(s => s.key)).size, street.length, 'every line its own clip');
  // Picking: their voice, the hour, the season and where they come from.
  const lib = { lines: [
    { id: 'a', voice: 'maid', kind: 'greet', time: 'morning', text: 'Morning.' },
    { id: 'b', voice: 'maid', kind: 'greet', time: 'evening', text: 'Evening.' },
    { id: 'c', voice: 'maid', kind: 'remark', season: 'winter', text: 'Cold.' },
    { id: 'd', voice: 'maid', kind: 'remark', origin: 'irish', text: 'Mayo.' },
    { id: 'e', voice: 'cook', kind: 'remark', text: 'Soup.' }], people: { p1: 'maid/swedish', p2: 'maid/irish' } };
  const maid = ST.personVoice(lib, 'p1'), irish = ST.personVoice(lib, 'p2');
  assert.deepEqual(maid, { voice: 'maid', origin: 'swedish' }); assert.equal(ST.personVoice(lib, 'nobody'), null);
  assert.deepEqual(ST.linesFor(lib, maid, 'greet', { hour: 8 }).map(l => l.id), ['a']);
  assert.deepEqual(ST.linesFor(lib, maid, 'greet', { hour: 21 }).map(l => l.id), ['b']);
  assert.deepEqual(ST.linesFor(lib, maid, 'remark', { season: 'summer' }).map(l => l.id), [], 'winter talk is not had in summer; Mayo is not hers');
  assert.deepEqual(ST.linesFor(lib, irish, 'remark', { season: 'winter' }).map(l => l.id), ['c', 'd']);
  assert.deepEqual(ST.linesFor(lib, irish, 'remark', { season: 'winter', heard: new Set(['c']) }).map(l => l.id), ['d'], 'what was heard waits');
  assert.equal(ST.gainAt(1), 1); assert.ok(ST.gainAt(7) < 1 && ST.gainAt(7) > ST.STREET.floor); assert.equal(ST.gainAt(40), ST.STREET.floor);
  // The player: someone near says a voiced line through the Narration bus, mouth moving; an
  // unvoiced line is silent; nobody speaks over a jaunt's voice or with Narration off.
  {
    const kp = await textKey('Morning.');
    const index = { version: 1, clips: { [ST.streetKey(kp, 'maid')]: { text_sha256: kp, file: 'narration/m.mp3' } } };
    const files = { 'https://data.test/street/1904.json': lib, 'https://media.test/narration/index.json': index };
    const fetcher = async (u) => new Response(JSON.stringify(files[String(u)] ?? null), { status: files[String(u)] ? 200 : 404 });
    class FakeAudio extends EventTarget { constructor() { super(); this.src = ''; this.paused = true; } play() { this.paused = false; return Promise.resolve(); } pause() { this.paused = true; } }
    let el = null, audible = true, busy = false, talk = [], said = [], captions = [];
    const actor = { id: 'p1', personId: 'p1', e: 2, n: 0, actions: { setTalk: (on) => talk.push(on), mouth: { say: (v) => said.push(v), hush: () => said.push('hush') } } };
    const gain = { gain: { value: 1 }, connect() {}, disconnect() {} };
    const ctx = { createMediaElementSource: () => ({ connect() {}, disconnect() {} }), createGain: () => gain };
    const t = ST.createStreetTalk({ scene: '1904', base: new URL('https://data.test/street/'), fetcher, location: Promise.resolve(new URL('https://media.test/narration/index.json')),
      humans: { actors: [actor], get: (id) => (id === 'p1' ? actor : null) }, visitor: () => ({ e: 0, n: 0 }), hour: () => 8, season: () => 'summer',
      speech: () => ({ ctx, bus: 'bus', audible }), busy: () => busy, media: () => (el = new FakeAudio()), random: () => 0, onCaption: (c) => captions.push(c.text) });
    await t.load();
    assert.ok(t.state.loaded);
    t.update(60); // the first remark's wait is over: p1 is 2 m away, so a greeting, the only voiced line
    assert.equal(el?.src, 'https://media.test/narration/m.mp3', 'a voiced line plays from the media host');
    assert.deepEqual(talk, [true]); await Promise.resolve(); assert.deepEqual(captions, ['Morning.'], 'and its words are shown');
    t.update(0.1); assert.ok(said.length >= 1, 'the speaker\'s jaw follows the voice');
    assert.equal(gain.gain.value, 1, 'near: full');
    el.dispatchEvent(new Event('ended')); assert.equal(t.state.speaking, null); assert.equal(said.at(-1), 'hush');
    busy = true; t.update(60); assert.equal(t.state.said, 1, 'nobody speaks over a jaunt\'s voice'); busy = false;
    audible = false; assert.equal(t.greet('p1'), false, 'with Narration off nobody answers aloud'); audible = true;
    assert.equal(t.greet('p1'), true, 'a greeting is answered at once, whenever they last spoke');
  }
}

console.log('NARRATION PASS — one script for app and voicer, keyed by its words; only changed words or voices are voiced; the index only grows; the player follows, queues, ducks and stops on mute, and says who is speaking and how loud');
