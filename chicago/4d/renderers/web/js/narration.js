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
 *  binds each to an ElevenLabs voice, and tools/test_narration.mjs holds the two lists equal. */
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
  if (paragraphs.length) paragraphs[0] = paragraphs[0].replace(/^JAUNT:\s*[^.!?]*[.!?]\s*/, '');
  const body = paragraphs.filter(Boolean).join('\n\n');
  return body ? `${String(jaunt.title ?? '').trim()}.\n\n${body}`.replace(/^\.\n\n/, '') : '';
}

/** Every script of a jaunt, in the order an outing meets them. A stop is read by its first
 *  host (the person waiting there), or by the narrator; its `since` lead is read with it. */
export function narrationScripts(jaunt) {
  const out = [];
  const add = (part, id, speaker, text) => { text = String(text ?? '').trim(); if (text) out.push({ part, id, speaker, text }); };
  add('opening', 'opening', NARRATOR, openingScript(jaunt));
  for (const stop of jaunt?.stops ?? []) {
    add('stop', stop.id, stop.hosts?.[0]?.person ?? NARRATOR, `${stop.since ? `${stop.since}. ` : ''}${stop.text ?? ''}`);
  }
  for (const ending of jaunt?.endings ?? []) add('ending', ending.id, NARRATOR, ending.text);
  return out;
}

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
export function createNarration({ fetcher = globalThis.fetch?.bind(globalThis), base = AUDIO_BASE,
  speech = () => null, wake = async () => {}, duck = () => {}, media = () => new Audio(), narrator = () => DEFAULT_NARRATOR,
  subtle = globalThis.crypto?.subtle, onChange = () => {}, location = null } = {}) {
  let index = null, indexUrl = null, loading = null, failed = false;
  let el = null, routed = null, primed = false, playing = null, queued = null, at = null, error = null;
  const keys = new Map();          // `${jaunt}:${part}:${id}` → { sha, speaker } of the words shown there
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
  /** Look up every script of a jaunt once (per content), then repaint. */
  async function prepare(jaunt) {
    if (!jaunt?.id) return;
    const content = `${jaunt.content_version ?? ''}:${jaunt.stops?.length ?? 0}`;
    if (prepared.get(jaunt.id) === content) return;
    prepared.set(jaunt.id, content);
    const found = await readIndex();
    if (!found) return;
    let any = false;
    for (const script of narrationScripts(jaunt)) {
      const words = { sha: await textKey(script.text, subtle), speaker: script.speaker };
      keys.set(slot(jaunt, script.part, script.id), words);
      any ||= !!clipFor(found, words.sha, words.speaker, narrator());
    }
    if (any) changed();
  }
  const clipAt = key => { const w = keys.get(key); return w ? clipFor(index, w.sha, w.speaker, narrator()) : null; };
  const clip = (jaunt, part, id) => clipAt(slot(jaunt, part, id));

  function element() {
    if (el) return el;
    el = media(); el.preload = 'auto'; el.crossOrigin = 'anonymous';
    el.addEventListener?.('ended', () => finish(true));
    el.addEventListener?.('error', () => { if (playing) { error = 'Narration could not play.'; finish(false); } });
    // Muting Narration or all sound, or leaving the page, ends the voice rather than leaving it speaking silently.
    el.addEventListener?.('timeupdate', () => { if (playing && speech()?.audible === false) stop(); });
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
      node.connect(out.bus); routed = { ctx: out.ctx, node };
    }
    return true;
  }
  function start(key) {
    const c = clipAt(key); if (!c || !route()) return false;
    const a = element(); queued = null; error = null;
    // A clip's file is named from the host's root, as the index's own path is (INDEX_PATH).
    a.src = new URL(c.file, new URL('../', indexUrl)).href;
    playing = key; duck(true); changed();
    const own = key;
    a.play()?.catch?.(e => { if (playing === own) { error = e?.name === 'NotAllowedError' ? 'Tap Listen to hear the narration.' : 'Narration could not play.'; finish(false); } });
    return true;
  }
  function finish(next) {
    playing = null; duck(false);
    const then = next ? queued : null; queued = null;
    if (!(then && start(then))) changed();
  }
  function stop() {
    queued = null;
    if (!playing) return;
    try { el.pause(); el.removeAttribute('src'); el.load?.(); } catch {}
    playing = null; duck(false); changed();
  }
  return {
    prepare, clip, prime,
    get state() { return { index: index ? Object.keys(index.clips).length : failed ? 'unavailable' : 'pending', playing, queued, at, error, primed }; },
    on(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    isPlaying: (jaunt, part, id) => playing === slot(jaunt, part, id),
    /** The part an outing now shows. Arriving at a new one with narration audible plays it,
     *  or queues it behind a voice still speaking. Null (travelling) changes nothing. */
    at(jaunt, part, id) {
      if (!jaunt) { at = null; stop(); return; }
      if (part == null) return;
      const key = slot(jaunt, part, id);
      if (key === at) return;
      at = key;
      if (!clipAt(key) || !speech()?.audible) return;
      if (playing) { if (playing !== key) { queued = key; changed(); } }
      else start(key);
    },
    /** A Listen tap: stop this voice, or start it now (waking sound if it is off). */
    toggle(jaunt, part, id) {
      const key = slot(jaunt, part, id);
      if (playing === key) { stop(); return Promise.resolve(false); }
      prime();
      return Promise.resolve(wake()).then(() => { if (playing) stop(); return start(key); });
    },
    stop,
    end() { at = null; stop(); },
  };
}
