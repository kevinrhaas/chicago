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
import { narrationScripts, openingScript, textKey, clipFor, clipKey, silentWav, createNarration, NARRATOR, NARRATORS, DEFAULT_NARRATOR, VOICE, voiceLevel } from '../renderers/web/js/narration.js';
import { loadConfig, scriptsFor, voiceFor, plan, voice, synthesize, verify, ROOT } from './narrate_jaunts.mjs';

const sha = s => createHash('sha256').update(s).digest('hex');
const jaunt = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sidecars/1904/jaunts/glessner-household-tour.json'), 'utf8'));

// ---- the scripts -----------------------------------------------------------------------
{
  const scripts = narrationScripts(jaunt);
  assert.deepEqual(scripts.map(s => `${s.part}:${s.id}`),
    ['opening:opening', ...jaunt.stops.map(s => `stop:${s.id}`), ...jaunt.endings.map(e => `ending:${e.id}`)]);
  assert.equal(scripts[1].speaker, 'glessner_john_j', 'a stop is read by its first host');
  assert.equal(scripts[0].speaker, NARRATOR); assert.equal(scripts.at(-1).speaker, NARRATOR);
  assert.equal(scripts[1].text, jaunt.stops[0].text, 'a stop is read as the panel shows it');
  assert.ok(openingScript(jaunt).startsWith('The Glessner Household.\n\nA spring morning'), 'the opening reads its title, not "JAUNT: …"');
  assert.ok(!openingScript(jaunt).includes('JAUNT:'));
  const timed = narrationScripts({ stops: [{ id: 'a', since: 'Four hours later', text: 'Noon.' }, { id: 'b', text: '  ' }] });
  assert.deepEqual(timed, [{ part: 'stop', id: 'a', speaker: NARRATOR, text: 'Four hours later. Noon.' }], 'a since is read with its stop; an empty script is none');
  assert.equal(await textKey('abc'), sha('abc'), 'the app\'s key is SHA-256 of the words');
  assert.equal(await textKey('x', null), null, 'no Web Crypto: no key, no narration');
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
  const scripts = await scriptsFor(config, { only: 'glessner-household-tour' });
  assert.equal(scripts.length, 11, 'the opening and the ending once for each narrator, each stop once (seven stops since T-3590)');
  const first = plan(scripts, config, { version: 1, clips: {} });
  assert.deepEqual(first.todo.map(s => s.id), ['opening', 'john', 'finish'], 'every chosen voice with no clip is voiced');
  assert.deepEqual(first.todo.map(s => s.key.slice(64)), ['~essayist', '', '~essayist']);
  assert.equal(first.skipped.length, 8);
  assert.match(first.skipped.find(s => s.id === 'frances').reason, /needs ELEVENLABS_API_KEY/, 'a voice name needs the key to resolve');
  assert.equal(first.chars, first.todo.reduce((n, s) => n + s.text.length, 0));
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
  assert.equal(calls[0].body.text, scripts[0].text); assert.equal(calls[0].body.model_id, config.model_id);
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

console.log('NARRATION PASS — one script for app and voicer, keyed by its words; only changed words or voices are voiced; the index only grows; the player follows, queues, ducks and stops on mute, and says who is speaking and how loud');
