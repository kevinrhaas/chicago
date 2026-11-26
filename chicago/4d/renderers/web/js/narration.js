/**
 * T-3578 — jaunt narration: a jaunt's opening, each stop and each ending read aloud in the
 * owner's ElevenLabs voices (the owner, 2026-11-13: "I have some voices in eleven labs and I
 * want to begin using those and having them read/play the narration or scripts like the meet
 * the Glessner household").
 *
 * Two halves share this file so they can never disagree about what is spoken:
 *
 *  - `narrationScripts(jaunt)` and `textKey(text)` are pure. tools/narrate_jaunts.mjs reads
 *    them in Node to decide which scripts need voicing; the app reads them to find the clip
 *    for what it shows. A clip is keyed by the SHA-256 of the exact words spoken, so a stop
 *    whose text changed after it was voiced never plays the old recording: it is silent until
 *    the workflow voices the new words.
 *  - `createNarration(...)` is the player: one gesture-primed media element streaming the
 *    clip through Settings › Sound's Narration bus (js/sound.js), ducking music and ambience
 *    while it speaks. It follows the outing: with sound on and Narration up, each stop's
 *    voice starts when you arrive (after the one still speaking finishes).
 *
 * T-3553 — and the person a clip speaks for moves their mouth with it: `voice()` says who is
 * speaking now and how loud (jaunt-hosts.js `speak` gives it to that host's jaw and hand).
 *
 * The clips and their index live with the other recorded audio on the media host
 * (tools/audio-hosting.json; docs/AUDIO.md § Narration). With no index — a local build, an
 * unreachable host, a jaunt not yet voiced — nothing is offered and nothing fails.
 */
// The app's own audio folder, as js/recorded-audio.js names it (not imported: this file stays light and Node-readable).
export const AUDIO_BASE = new URL('../audio/', import.meta.url);

export const NARRATOR = 'narrator';
export const INDEX_PATH = 'narration/index.json';
/** The narrators a visitor chooses between in Settings › Sound (the owner, 2026-11-13: "i have
 *  two narrators, people should be able to select which one they use the essayist is the
 *  default"). The voicer voices every narrator script once for each; data/narration/voices.json
 *  binds each to an ElevenLabs voice, and tools/test_narration.mjs holds the two lists equal.
 *  T-3627: narrators.js carries the same three for Settings, which must not load this player;
 *  this file imports nothing (the voicing workflow checks it out alone), so the test holds
 *  that copy equal to this one too. */
export const NARRATORS = Object.freeze([
  { id: 'essayist', label: 'Cultivated Essayist' },
  { id: 'storyteller', label: 'Midwestern Storyteller' },
]);
export const DEFAULT_NARRATOR = 'essayist';
export const normalNarrator = v => (NARRATORS.some(n => n.id === v) ? v : DEFAULT_NARRATOR);
/** The index key of a script's clip: its words' key, and for the narrator's words, which narrator. */
export const clipKey = (textSha, speaker, narrator = DEFAULT_NARRATOR) =>
  textSha && (speaker === NARRATOR ? `${textSha}~${normalNarrator(narrator)}` : textSha);

/** A jaunt's opening as it is read: the title, then the welcome's paragraphs (without the
 *  "JAUNT: ITS TITLE." its first paragraph leads with, which the title replaces). */
export function openingScript(jaunt) {
  const paragraphs = String(jaunt?.opening?.text ?? '').split(/\n\s*\n/).map(t => t.trim()).filter(Boolean);
  if (paragraphs.length) paragraphs[0] = paragraphs[0].replace(/^(?:JAUNT|PASEO):\s*[^.!?]*[.!?]\s*/, '');
  const body = paragraphs.filter(Boolean).join('\n\n');
  return body ? `${String(jaunt.title ?? '').trim()}.\n\n${body}`.replace(/^\.\n\n/, '') : '';
}

/**
 * T-3755 (the owner, 2026-11-26: "End each scene's narration with an invitation to proceed to
 * the next stop or explore the current location. Vary the language so it does not become
 * repetitive. This may involve some re-recording do what you can to minimize this so we save
 * eleven labs tokens"): every stop closes with one short line of the narrator's, from this one
 * shared set, shown under the stop's words and read straight after its voice. No stop's own
 * words change, so no stop is voiced again: each line here is voiced once (a clip is keyed by
 * its words alone) and every jaunt that uses it plays the same clip.
 *
 * Kinds: `onward` (look around, then go on), `linger` (after a stop that already ends by sending
 * you on, "Walk north to ...": look around here first), `choice` (a stop that asks a choice),
 * `final` (the last stop). Two registers: `young` for ages 8-10 (grades 3-5), `general` for the
 * rest. Each line is [English, Spanish]; a jaunt read in Spanish (jaunt-language.js sets `lang`)
 * takes the Spanish. The words stay in the walk: no keys, no buttons, no build talk, and nothing
 * about where the next stop is (it may be across town, or years away).
 */
export const ONWARD_LINES = Object.freeze({
  general: {
    onward: [
      ['Take your time here. When you are ready, the next stop is waiting.', 'Tómate tu tiempo aquí. Cuando quieras, la siguiente parada te espera.'],
      ['Look around as long as you like, then go on to the next stop.', 'Mira a tu alrededor todo lo que quieras y luego sigue a la siguiente parada.'],
      ['Stay a while, if you want. The story picks up again at the next stop.', 'Quédate un rato, si quieres. La historia sigue en la siguiente parada.'],
      ['There is more to see here, so wander a little before you move on.', 'Aquí hay más que ver, así que recorre un poco el lugar antes de seguir.'],
      ['When you have seen enough, walk on. The next stop will keep.', 'Cuando hayas visto bastante, sigue adelante. La siguiente parada puede esperar.'],
      ['Have a look around. Then, whenever you are ready, we go on.', 'Echa un vistazo. Luego, cuando estés listo, seguimos.'],
      ['Linger here a moment, or press on. The rest of the story is waiting.', 'Quédate aquí un momento, o sigue adelante. El resto de la historia te espera.'],
      ['Explore this place a little. Then on to the next part of the story.', 'Explora un poco este lugar. Luego, a la siguiente parte de la historia.'],
      ['No need to hurry. Look about you, and go on when you are ready.', 'No hay prisa. Mira a tu alrededor y sigue cuando estés listo.'],
      ['Stand here as long as you like. Then on we go, to the next stop.', 'Quédate aquí todo lo que quieras. Luego seguimos a la siguiente parada.'],
      ['Wander, look, listen. When you are done, the next stop is waiting.', 'Pasea, mira, escucha. Cuando termines, la siguiente parada te espera.'],
      ['Take one more look around before you go on.', 'Echa un último vistazo antes de seguir.'],
      ['This place is yours to explore. The story goes on at the next stop.', 'Este lugar es tuyo para explorarlo. La historia sigue en la siguiente parada.'],
      ['See what else you can find here. When you are ready, we will go on.', 'Mira qué más puedes encontrar aquí. Cuando estés listo, seguiremos.'],
      ['Take it all in. When you are ready, the story moves on.', 'Asimílalo todo. Cuando estés listo, la historia sigue.'],
      ['Look closely before you leave. Then on to the next stop.', 'Mira con atención antes de irte. Luego, a la siguiente parada.'],
      ['Spend a little time here. The next stop is ready whenever you are.', 'Pasa un rato aquí. La siguiente parada está lista cuando tú lo estés.'],
      ['Pause here for a while. When you want to go on, the story goes with you.', 'Detente aquí un rato. Cuando quieras seguir, la historia sigue contigo.'],
    ],
    linger: [
      ['But first, take a moment to look around.', 'Pero antes, tómate un momento para mirar a tu alrededor.'],
      ['There is no hurry, though. Look around first, if you like.', 'Aunque no hay prisa. Mira primero a tu alrededor, si quieres.'],
      ['Before you go, have a good look at this place.', 'Antes de irte, mira bien este lugar.'],
      ['Take your time first. This place is worth a second look.', 'Primero, tómate tu tiempo. Este lugar merece una segunda mirada.'],
      ['Linger a little before you go, if you want to.', 'Quédate un poco antes de irte, si quieres.'],
      ['Stay as long as you like before you set off.', 'Quédate todo lo que quieras antes de ponerte en camino.'],
      ['First, though, explore here as much as you wish.', 'Pero primero, explora aquí todo lo que quieras.'],
      ['Whenever you are ready. Look around here first, if you like.', 'Cuando estés listo. Mira primero por aquí, si quieres.'],
    ],
    choice: [
      ['Look around, then choose how the story goes on.', 'Mira a tu alrededor y luego elige cómo sigue la historia.'],
      ['Take your time here. When you are ready, make your choice.', 'Tómate tu tiempo aquí. Cuando estés listo, elige.'],
      ['Think it over, and look about you. The choice is yours.', 'Piénsalo y mira a tu alrededor. La decisión es tuya.'],
      ['Explore a little first, if you like. Then decide.', 'Explora un poco primero, si quieres. Luego decide.'],
    ],
    final: [
      ['That is the last stop. Look around as long as you like before we finish.', 'Esta es la última parada. Mira a tu alrededor todo lo que quieras antes de terminar.'],
      ['This is where the walk ends. Take a last look around, and finish when you are ready.', 'Aquí termina el paseo. Echa un último vistazo y termina cuando estés listo.'],
      ['Our last stop. Stay a while before we close the story.', 'Nuestra última parada. Quédate un rato antes de cerrar la historia.'],
      ['The jaunt ends here. Have one more look around before you go.', 'El paseo termina aquí. Echa otro vistazo antes de irte.'],
      ['That brings us to the end. Linger as long as you like, then we will finish.', 'Con esto llegamos al final. Quédate todo lo que quieras y luego terminaremos.'],
      ['There are no more stops after this one. Take your time here.', 'No hay más paradas después de esta. Tómate tu tiempo aquí.'],
    ],
  },
  young: {
    onward: [
      ['Take a good look around. Then go on to the next stop.', 'Mira bien a tu alrededor. Luego sigue a la siguiente parada.'],
      ['Look around as long as you like. The next stop is waiting.', 'Mira a tu alrededor todo lo que quieras. La siguiente parada te espera.'],
      ['What else can you see here? When you are ready, go on.', '¿Qué más puedes ver aquí? Cuando estés listo, sigue.'],
      ['Have a look around first. Then on we go!', 'Primero echa un vistazo. ¡Luego seguimos!'],
      ['Stay here a little while. Then go on to the next stop.', 'Quédate aquí un ratito. Luego sigue a la siguiente parada.'],
      ['There is a lot to see here. Look around, then go on.', 'Aquí hay mucho que ver. Mira a tu alrededor y luego sigue.'],
      ['Take your time. The next stop will wait for you.', 'Tómate tu tiempo. La siguiente parada te esperará.'],
      ['Look up, look around. Then it is time for the next stop.', 'Mira arriba, mira alrededor. Luego toca la siguiente parada.'],
      ['When you are ready, it is time for the next stop.', 'Cuando estés listo, toca la siguiente parada.'],
      ['Explore a little. Then come along to the next stop.', 'Explora un poco. Luego ven a la siguiente parada.'],
      ['Can you spot something new here? Then go on to the next stop.', '¿Ves algo nuevo aquí? Luego sigue a la siguiente parada.'],
      ['Have a good look. The story goes on at the next stop.', 'Mira bien. La historia sigue en la siguiente parada.'],
    ],
    linger: [
      ['But first, have a look around.', 'Pero primero, echa un vistazo.'],
      ['You can look around here first, if you like.', 'Si quieres, puedes mirar por aquí primero.'],
      ['Take your time. Look around before you go.', 'Tómate tu tiempo. Mira a tu alrededor antes de irte.'],
      ['First, see what else is here.', 'Primero, mira qué más hay aquí.'],
      ['Before you go, look all around you.', 'Antes de irte, mira todo a tu alrededor.'],
      ['There is no rush. Look around first.', 'No hay prisa. Mira primero a tu alrededor.'],
    ],
    choice: [
      ['Look around. Then pick what happens next.', 'Mira a tu alrededor. Luego elige qué pasa después.'],
      ['Take your time, then make your choice.', 'Tómate tu tiempo y luego elige.'],
      ['What will you choose? Look around first, if you like.', '¿Qué vas a elegir? Mira primero a tu alrededor, si quieres.'],
    ],
    final: [
      ['This is our last stop. Take one more look around.', 'Esta es nuestra última parada. Echa otro vistazo.'],
      ['That is the end of our walk. Look around as long as you like.', 'Aquí termina nuestro paseo. Mira a tu alrededor todo lo que quieras.'],
      ['No more stops after this one. Stay as long as you want.', 'No hay más paradas después de esta. Quédate todo lo que quieras.'],
      ['We are at the end. Have one last look before we finish.', 'Llegamos al final. Echa un último vistazo antes de terminar.'],
    ],
  },
});
/** T-3755: a stop's last sentence already sends the visitor on ("Walk north to the brother's
 *  house next door.", "To find her, walk through the tunnel", "Go and meet her."). */
const SENDS_ON = /^(?:["'‘“¡]*)(?:(?:to|then|now|next|first|so|and|para|luego|ahora)\b[^,.!?]{0,60},\s*)?(?:walk|step|go|keep|look|take|follow|cross|head|turn|come|find|meet|stand|listen|watch|wait|climb|pick|ride|put|sit|join|hear|see|try|let's|let us|carry|run|board|enter|visit|ask|read|light|hold|pass|leave|stay|choose|decide|camina|ve|sigue|mira|toma|cruza|entra|ven|vamos|busca|escucha|espera|sube|pasa|acompaña|quédate|elige|decide)\b/i;
export function sendsOn(text) {
  const sentences = String(text ?? '').trim().split(/(?<=[.!?]['"’”]?)\s+/).filter(Boolean);
  return SENDS_ON.test(sentences.at(-1) ?? '');
}
/** T-3755: which stops a jaunt can end on (no stop of its own comes after them), as jaunts.js isFinalStop reads it. */
function finalStops(jaunt) {
  const stops = jaunt?.stops ?? [], ids = new Set(stops.map(s => s.id));
  const ends = next => next == null || !ids.has(next);
  return new Set(stops.filter(s => (s.choices?.length && s.choices.some(c => c.next)
    ? s.choices.every(c => ends(c.next ?? s.next)) : ends(s.next))).map(s => s.id));
}
const fnv = s => { let h = 0x811c9dc5; for (const c of String(s)) { h ^= c.codePointAt(0); h = Math.imul(h, 0x01000193) >>> 0; } return h; };
/** T-3755: each stop's closing line, by stop id. Each kind walks its own list from a start set by
 *  the jaunt's id, so neighbouring stops never share a line and no line comes twice in a jaunt
 *  until its list has run out. Pure: the voicer and the app pick the same line. */
export function onwardLines(jaunt, lang = jaunt?.lang) {
  const register = ONWARD_LINES[jaunt?.grade_band === '3-5' ? 'young' : 'general'], es = lang === 'es';
  const last = finalStops(jaunt), used = {}, out = new Map();
  for (const stop of jaunt?.stops ?? []) {
    if (!String(stop.text ?? '').trim()) continue;
    const kind = last.has(stop.id) ? 'final' : stop.choices?.length ? 'choice' : sendsOn(stop.text) ? 'linger' : 'onward';
    const list = register[kind], n = used[kind] = (used[kind] ?? -1) + 1;
    out.set(stop.id, list[(fnv(`${jaunt.id}:${kind}`) + n) % list.length][es ? 1 : 0]);
  }
  return out;
}

/** Every script of a jaunt, in the order an outing meets them. A stop is read by its first
 *  host (the person waiting there), or by the narrator; its `since` lead is read with it.
 *  T-3755: each stop's closing line (`onward`, the narrator's) follows the endings, so the
 *  parts a jaunt already had keep their places; the player reads it straight after its stop. */
export function narrationScripts(jaunt) {
  const out = [];
  const add = (part, id, speaker, text) => { text = String(text ?? '').trim(); if (text) out.push({ part, id, speaker, text }); };
  add('opening', 'opening', NARRATOR, openingScript(jaunt));
  for (const stop of jaunt?.stops ?? []) {
    add('stop', stop.id, stop.hosts?.[0]?.person ?? NARRATOR, `${stop.since ? `${stop.since}. ` : ''}${stop.text ?? ''}`);
  }
  for (const ending of jaunt?.endings ?? []) add('ending', ending.id, NARRATOR, ending.text);
  for (const [id, text] of onwardLines(jaunt)) add('onward', id, NARRATOR, text);
  return out;
}
/** T-3755: the closing line that follows a stop's voice: `${jaunt}:stop:${id}` → `${jaunt}:onward:${id}`. */
const onwardSlot = key => (typeof key === 'string' && key.includes(':stop:') ? key.replace(':stop:', ':onward:') : null);

const hex = buffer => [...new Uint8Array(buffer)].map(b => b.toString(16).padStart(2, '0')).join('');
/** The clip key for some spoken words: SHA-256 of their UTF-8 bytes, as hex. Null where the
 *  page has no Web Crypto (an insecure origin), which simply offers no narration. */
export async function textKey(text, subtle = globalThis.crypto?.subtle) {
  if (!subtle) return null;
  return hex(await subtle.digest('SHA-256', new TextEncoder().encode(String(text))));
}

/** The index's clip for these words in this speaker's voice, or null. A narrator script takes
 *  the chosen narrator, else the default one. Only an entry that names these words' key is
 *  returned: changed words never play the old recording. */
export function clipFor(index, textSha, speaker = null, narrator = DEFAULT_NARRATOR) {
  if (!textSha) return null;
  const keys = speaker === NARRATOR ? [clipKey(textSha, speaker, narrator), clipKey(textSha, speaker, DEFAULT_NARRATOR)] : [textSha];
  for (const key of keys) {
    const clip = index?.clips?.[key];
    if (clip && clip.text_sha256 === textSha && typeof clip.file === 'string') return clip;
  }
  return null;
}

/**
 * T-3553: how loud a voice is now, for the mouth of the person it speaks for. `window`: the
 * samples listened to (about a fiftieth of a second, so a low voice's own beat does not show
 * in it); a level under `floor` (the root mean square of the samples, of 1) is a shut mouth
 * and one at `full` a jaw as far open as a voice turns it (human-mouth.js `say_deg`). Ours,
 * set on the household tour's first two voices as they were recorded (John and Frances
 * Glessner, in windows of this length, counting only those over the floor: the middle of
 * John's is 0.13 and of Frances's 0.12, nine tenths of each lie under 0.20 and ninety-nine
 * in a hundred under 0.27), so that a syllable opens the jaw about as far as the talk without
 * a voice does and only the loudest opens it wide. `deaf_s`: an ear that has heard nothing
 * at all this long into a clip is taken to be unable to listen (the level is then not known).
 */
export const VOICE = Object.freeze({ window: 1024, floor: 0.012, full: 0.3, deaf_s: 2 });
/** A window of a voice's samples (bytes, 128 at rest) as a level, 0..1. */
export function voiceLevel(samples) {
  let sum = 0;
  for (let i = 0; i < samples.length; i++) { const x = (samples[i] - 128) / 128; sum += x * x; }
  const rms = Math.sqrt(sum / Math.max(1, samples.length));
  return Math.min(1, Math.max(0, (rms - VOICE.floor) / (VOICE.full - VOICE.floor)));
}

/** A 1/10 s silent WAV: played inside a tap, it lets the element speak later without one
 *  (WebKit, so iPhone Chrome, counts a media element as allowed once it has played in a gesture). */
export function silentWav(rate = 8000, samples = 800) {
  const bytes = new Uint8Array(44 + samples), v = new DataView(bytes.buffer);
  const text = (at, s) => [...s].forEach((c, i) => { bytes[at + i] = c.charCodeAt(0); });
  text(0, 'RIFF'); v.setUint32(4, 36 + samples, true); text(8, 'WAVE'); text(12, 'fmt ');
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, rate, true); v.setUint32(28, rate, true); v.setUint16(32, 1, true); v.setUint16(34, 8, true);
  text(36, 'data'); v.setUint32(40, samples, true); bytes.fill(128, 44);
  return bytes;
}

/** Where the narration index is: beside the hosted media when the published catalogue names
 *  its host, else beside the app's own audio (a local build, or a test's fixture). */
export async function indexLocation({ fetcher, base = AUDIO_BASE } = {}) {
  try {
    const r = await fetcher(new URL('catalog.json', base));
    const host = r.ok ? (await r.json())?.hosting?.public_base : null;
    if (typeof host === 'string' && /^https:\/\//.test(host)) return new URL(INDEX_PATH, host);
  } catch { /* fall through to the local copy */ }
  return new URL(INDEX_PATH, base);
}

/**
 * The player. `speech()` is js/sound.js's `{ ctx, bus, audible }` (null until the page's first
 * gesture); `wake()` is called inside a Listen tap to make sure sound is on and loaded, and
 * resolves once it is; `duck(on)` lowers music and ambience while a voice speaks.
 */
/** T-3619: a clip's length in seconds from the narration index: its bytes at its constant bitrate
 *  (`mp3_44100_64` is 64 kbit/s), else about 15 characters a second, else null. */
export function clipSeconds(clip) {
  if (!clip) return null;
  const kbps = Number(/^mp3_\d+_(\d+)$/.exec(clip.output_format ?? '')?.[1]);
  if (kbps > 0 && clip.bytes > 0) return clip.bytes / (kbps * 125);
  return clip.chars > 0 ? clip.chars / 15 : null;
}

/**
 * T-3735 (the owner, 2026-11-23: "if they are on 11-13 ... and you do not have narration for
 * that then don't play that other wrong narration unless you have the correct one"): `voiced(jaunt)`
 * says (or resolves to) whether this telling itself is read aloud: the catalog's `narrated`,
 * from data/narration/voices.json. A clip is found by its words alone, and the tellings of one
 * jaunt for other ages share words (the title and opening, a stop left as it was), so without
 * this a telling nobody voiced spoke with another telling's recording. A telling that is not
 * voiced, or one whose answer cannot be had, offers no Listen key and plays nothing; its words
 * and its music go on as before.
 */
export function createNarration({ fetcher = globalThis.fetch?.bind(globalThis), base = AUDIO_BASE,
  speech = () => null, wake = async () => {}, duck = () => {}, media = () => new Audio(), narrator = () => DEFAULT_NARRATOR,
  subtle = globalThis.crypto?.subtle, onChange = () => {}, location = null, voiced = () => true } = {}) {
  let index = null, indexUrl = null, loading = null, failed = false;
  let el = null, routed = null, primed = false, playing = null, queued = null, at = null, error = null, starved = false;
  let heard = false;               // the part `at` names has been played or queued once
  let paused = false;              // T-3671: the visitor paused the voice speaking (WCAG 1.4.2); it keeps its place
  let ended = null;                // the last clip that played to its end
  let opening = null;              // an outing's opening it showed that has not been heard yet
  const keys = new Map();          // `${jaunt}:${part}:${id}` → { sha, speaker } of the words shown there
  const retold = new Map();        // T-3735: slot → the other telling whose words it shows now ('none': no voice)
  const pending = new Set();       // T-3735: slots whose words are being looked up again (no voice until known)
  const serials = new Map(); let serial = 0;
  const prepared = new Map();      // jaunt id → the content it was prepared for
  const listeners = new Set([onChange]);
  const changed = () => { for (const fn of listeners) { try { fn(); } catch { /* a listener's own problem */ } } };
  const slot = (jaunt, part, id) => `${jaunt?.id}:${part}:${id}`;

  async function readIndex() {
    if (index || failed) return index;
    loading ??= (async () => {
      try {
        indexUrl = await (location ?? indexLocation({ fetcher, base }));
        const r = await fetcher(indexUrl, { cache: 'no-cache' });
        if (!r.ok) throw Error(`HTTP ${r.status}`);
        const value = await r.json();
        if (value?.version !== 1 || typeof value.clips !== 'object') throw Error('unknown narration index');
        index = value;
      } catch { failed = true; }
      loading = null; return index;
    })();
    return loading;
  }
  /** Look up every script of a jaunt once (per content), then repaint. Every caller waits
   *  for the same lookup (the flight to the start waits on it to know the opening's length). */
  function prepare(jaunt) {
    if (!jaunt?.id) return Promise.resolve();
    const content = `${jaunt.content_version ?? ''}:${jaunt.stops?.length ?? 0}`;
    const had = prepared.get(jaunt.id);
    if (had?.content === content) return had.done;
    const done = lookUp(jaunt);
    prepared.set(jaunt.id, { content, done });
    return done;
  }
  async function lookUp(jaunt) {
    const found = await readIndex();
    if (!found) return;
    let own = false;
    try { own = (await voiced(jaunt)) === true; } catch { own = false; }
    if (!own) return;   // T-3735: never another telling's voice
    let any = false;
    for (const script of narrationScripts(jaunt)) {
      const words = { sha: await textKey(script.text, subtle), speaker: script.speaker };
      if (retold.has(slot(jaunt, script.part, script.id))) continue;   // T-3735: an age tab chose its words
      keys.set(slot(jaunt, script.part, script.id), words);
      any ||= !!clipFor(found, words.sha, words.speaker, narrator());
    }
    if (any) changed();
  }
  const clipAt = key => { if (pending.has(key)) return null; const w = keys.get(key); return w ? clipFor(index, w.sha, w.speaker, narrator()) : null; };
  /**
   * T-3735 (the owner, 2026-11-23: "when you switch tabs to an age that has its own recording,
   * it should start playing that recording"): a part of the jaunt being walked now shows the
   * words of `from`, another telling's part ({ jaunt, part, id }); `null` gives it back its
   * own words, and `false` shows words no telling has a voice for. The part is then voiced by
   * that telling's recording where that telling is voiced (`voiced`), and by none where it is
   * not. When the words it is voiced by change, a voice reading the old ones stops, and the
   * new one starts if the visitor is at that part with narration audible, as on arriving.
   */
  function retell(jaunt, part, id, from = null) {
    if (!jaunt?.id) return Promise.resolve();
    const key = slot(jaunt, part, id);
    const sign = from === false ? 'none' : from?.jaunt?.id ? `${from.jaunt.id}:${from.part}:${from.id}` : '';
    if ((retold.get(key) ?? '') === sign) return Promise.resolve();
    if (sign) retold.set(key, sign); else retold.delete(key);
    pending.add(key);
    const mine = ++serial; serials.set(key, mine);
    return (async () => {
      let words = null;
      try {
        const source = from === false ? null : from?.jaunt?.id ? from : { jaunt, part, id };
        if (source && await readIndex() && (await voiced(source.jaunt)) === true) {
          const script = narrationScripts(source.jaunt).find(s => s.part === source.part && s.id === source.id);
          if (script) words = { sha: await textKey(script.text, subtle), speaker: script.speaker };
        }
      } catch { words = null; }
      if (serials.get(key) !== mine) return;
      pending.delete(key);
      const before = keys.get(key)?.sha ?? null;
      if (words) keys.set(key, words); else keys.delete(key);
      if ((words?.sha ?? null) !== before) {
        if (queued === key) queued = null;
        if (playing === key) stop();
        if (at === key) heard = false;
      }
      if (at === key && !heard && clipAt(key) && speech()?.audible) {
        heard = true;
        if (!playing) start(key); else if (playing !== key) queued = key;
      }
      changed();
    })();
  }
  const clip = (jaunt, part, id) => clipAt(slot(jaunt, part, id));

  function element() {
    if (el) return el;
    el = media(); el.preload = 'auto'; el.crossOrigin = 'anonymous';
    // T-3755: a stop's closing line ending leaves the stop's own voice the one heard to its end (the meter).
    el.addEventListener?.('ended', () => { const was = playing; if (!was?.includes(':onward:')) ended = was; finish(true, was); });
    el.addEventListener?.('error', () => { if (playing) { error = 'Narration could not play.'; finish(false); } });
    // Muting Narration or all sound, or leaving the page, ends the voice rather than leaving it speaking silently.
    el.addEventListener?.('timeupdate', () => { if (playing && speech()?.audible === false) stop(); if (starved && el.readyState >= 3) starved = false; });
    // T-3553: a clip whose data stops arriving waits, unpaused and silent (`voice()`).
    el.addEventListener?.('waiting', () => { starved = true; });
    el.addEventListener?.('playing', () => { starved = false; });
    return el;
  }
  /** Call inside a trusted tap: the element plays a moment of silence, so a later stop's voice may start unprompted. */
  function prime() {
    const a = element();
    if (primed || playing) return;
    primed = true;
    try {
      const url = URL.createObjectURL(new Blob([silentWav()], { type: 'audio/wav' }));
      a.src = url;
      const done = () => { try { URL.revokeObjectURL(url); } catch {} };
      a.play()?.then?.(() => { if (!playing) a.pause(); done(); }, done);
    } catch { /* a page without Blob URLs still plays clips from a tap */ }
  }
  function route() {
    const out = speech(); if (!out?.ctx || !out.bus) return false;
    if (routed?.ctx !== out.ctx) {
      try { routed?.node.disconnect(); } catch {}
      const node = out.ctx.createMediaElementSource(element());
      node.connect(out.bus);
      // T-3553: and an ear on the voice before the bus's volume, for the speaker's mouth
      // (`voice()`). It feeds nothing; a page whose audio has no analyser simply has none.
      let ear = null;
      try { if (typeof out.ctx.createAnalyser === 'function') { ear = out.ctx.createAnalyser(); ear.fftSize = VOICE.window; node.connect(ear); } } catch { ear = null; }
      routed = { ctx: out.ctx, node, ear, samples: ear ? new Uint8Array(VOICE.window) : null, heard: false };
    }
    return true;
  }
  function start(key) {
    const c = clipAt(key); if (!c || !route()) return false;
    if (key === opening) opening = null;
    const a = element(); queued = null; error = null;
    // A clip's file is named from the host's root, as the index's own path is (INDEX_PATH).
    a.src = new URL(c.file, new URL('../', indexUrl)).href;
    playing = key; paused = false; if (ended === key) ended = null; duck(true); changed();
    routed.heard = false;   // the ear has heard nothing of this clip yet (`voice()`)
    starved = false;
    const own = key;
    a.play()?.catch?.(e => { if (playing === own) { error = e?.name === 'NotAllowedError' ? 'Tap Listen to hear the narration.' : 'Narration could not play.'; finish(false); } });
    return true;
  }
  function finish(next, was = null) {
    playing = null; paused = false; duck(false);
    let then = next ? queued : null; queued = null;
    // T-3755: a stop's voice heard to its end, with the visitor still there, goes on into its closing line.
    if (next && !then && was && at === was && clipAt(onwardSlot(was))) then = onwardSlot(was);
    if (!(then && start(then))) changed();
  }
  function stop() {
    queued = null;
    if (!playing) return;
    try { el.pause(); el.removeAttribute('src'); el.load?.(); } catch {}
    playing = null; paused = false; duck(false); changed();
  }
  /** T-3671 (WCAG 1.4.2): hold the voice where it is, or let it go on from there. A held voice
   *  is still the part's own (`isPlaying`), so the closing scene waits for it, and nobody's
   *  mouth moves (`voice()` reads a paused element as silence). */
  function pause() {
    if (!playing || paused) return false;
    try { el.pause(); } catch {}
    paused = true; duck(false); changed(); return true;
  }
  function resume() {
    if (!playing || !paused) return false;
    paused = false; duck(true); changed();
    const own = playing;
    try { el.play()?.catch?.(() => { if (playing === own) { paused = true; duck(false); changed(); } }); } catch {}
    return true;
  }
  return {
    prepare, clip, prime, retell,
    get state() { return { index: index ? Object.keys(index.clips).length : failed ? 'unavailable' : 'pending', playing, paused, queued, at, error, primed }; },
    pause, resume,
    /** T-3671: whether a voice of this jaunt is speaking (or held), and held: for the panel's Pause key. */
    speaking: jaunt => !!playing && !!jaunt?.id && playing.startsWith(`${jaunt.id}:`),
    get paused() { return !!playing && paused; },
    on(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    isPlaying: (jaunt, part, id) => playing === slot(jaunt, part, id),
    /** The owner, 2026-11-16: how far this part's voice has spoken, for the stop's meter:
     *  { t, d } seconds while it plays, { done: true } once it has played to its end, else null. */
    position(jaunt, part, id) {
      const key = slot(jaunt, part, id);
      if (playing === key && el) {
        const d = Number.isFinite(el.duration) && el.duration > 0 ? el.duration : clipSeconds(clipAt(key));
        return { t: el.currentTime || 0, d };
      }
      return ended === key ? { done: true } : null;
    },
    /** The owner, 2026-11-16: the closing scene waits for its ending's voice to finish. */
    ended: (jaunt, part, id) => ended === slot(jaunt, part, id),
    /** How long this part's voice will speak if it plays now (sound on, Narration up, a clip
     *  for its words), in seconds; null when nothing would be heard. */
    seconds(jaunt, part, id) {
      const c = clip(jaunt, part, id);
      return c && speech()?.audible ? clipSeconds(c) : null;
    },
    /**
     * T-3553: who is speaking now, and how loud: { speaker, level } while a clip sounds, else
     * null. `speaker` is the person the clip speaks for (a stop's first host) or NARRATOR;
     * `level` is 0..1 (VOICE), or null where the page cannot listen to the clip (no analyser,
     * one that throws, or one that has heard nothing at all `deaf_s` into a clip that is
     * playing), so the mouth keeps its own run of syllables. A clip held paused (a media key,
     * a call, a play the browser refused), or waiting for data that has stopped arriving, is
     * nobody's voice until it sounds again.
     */
    voice() {
      if (!playing || el?.paused || starved) return null;
      const speaker = keys.get(playing)?.speaker ?? NARRATOR;
      if (!routed?.ear) return { speaker, level: null };
      try {
        routed.ear.getByteTimeDomainData(routed.samples);
        // An ear that listens reads something other than rest within the clip's first moments.
        if (!routed.heard && !(routed.heard = routed.samples.some(x => x !== 128))) return { speaker, level: el?.currentTime > VOICE.deaf_s ? null : 0 };
        return { speaker, level: voiceLevel(routed.samples) };
      } catch { return { speaker, level: null }; }
    },
    /** The part an outing now shows. Arriving at a new one with narration audible plays it,
     *  or queues it behind a voice still speaking. Null (travelling) changes nothing. */
    at(jaunt, part, id) {
      if (!jaunt) { at = null; opening = null; stop(); return; }
      if (part == null) return;
      const key = slot(jaunt, part, id);
      if (key === at && heard) return;
      if (key !== at) { at = key; heard = false; }
      if (part === 'opening') opening = key;
      else if (opening && !opening.startsWith(`${jaunt.id}:`)) opening = null;
      // Not decided yet when the clip is still being looked up (a jaunt's first Start: the index
      // loads while the flight begins) or sound has not woken: the repaint that follows asks again.
      if (!clipAt(key) || !speech()?.audible) return;
      heard = true;
      // The owner (2026-11-13): the narrator reads the title and Background, then the first host
      // speaks. A flight shorter than the index's load lands before the opening could start, so
      // the first stop plays the unheard opening first and its own voice after it.
      const first = part === 'stop' && opening && clipAt(opening) ? opening : null;
      if (playing) { if (playing !== key) { queued = key; changed(); } }
      else if (first && start(first)) { queued = key; changed(); }
      else start(key);
    },
    /** A Listen tap: stop this voice, or start it now (waking sound if it is off). */
    toggle(jaunt, part, id) {
      const key = slot(jaunt, part, id);
      if (playing === key) { stop(); return Promise.resolve(false); }
      prime();
      return Promise.resolve(wake()).then(() => { if (playing) stop(); return start(key); });
    },
    /** Stop the voice; the visitor moving on (Next, Previous, End) also passes over an unheard opening. */
    stop() { opening = null; stop(); },
    end() { at = null; opening = null; stop(); },
  };
}
