// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * street-talk.js — T-3812: the people of the town say short things aloud as you pass them.
 *
 * The owner, 2026-11-27: "Let's do great fire plus street talk", after asking about "adding
 * voices background dialog for the people in 1904". A scene's lines are written in
 * docs/RESEARCH/street-talk-3812/<scene>.txt and built into data/narration/street/<scene>.json
 * (tools/build_street_talk.mjs), published as data/street/<scene>.json. Each line is one clip
 * in its voice, made by the narration workflow (tools/narrate_jaunts.mjs, voices.json `street`)
 * and found in the same narration index, keyed by its words and its voice (`streetKey`).
 *
 *   update(dt)          every frame: now and then, someone near the visitor says a remark
 *   greet(personId)     someone the visitor greeted answers (a greeting fit for the hour)
 *   state               { loaded, speaking, said, last } for the harness
 *
 * Who speaks: an adult of the scene's `people` (their voice, and where they come from), drawn
 * and out of doors within STREET.reach_m of the visitor, not a jaunt's host, and not one who
 * spoke in the last STREET.again_s. Nobody speaks over a jaunt's voice (`busy`), with sound or
 * Narration off (`speech().audible`), or before their clip is known: an unvoiced line is
 * silent, never read by a stand-in. The voice goes through the Narration bus (its level and
 * mute), quieter with distance, and the speaker's jaw follows it (human-mouth.js `say`) as a
 * jaunt host's does. A caption names who said what (`onCaption`), for anyone without sound.
 */
import { textKey, indexLocation, voiceLevel, VOICE } from './narration.js';

export const STREET_SPEAKER = (voice) => `street:${voice}`;
/** The narration index key of a street line: its words' SHA-256 and its voice, so two voices
 *  may say the same words ("Good morning.") and each has its own recording. */
export const streetKey = (textSha, voice) => textSha && `${textSha}@street:${voice}`;

export const STREET = Object.freeze({
  reach_m: 9,           // who may be heard: near enough to overhear
  greet_m: 3.5,         // close in front of you, they may greet you instead of remarking
  gap_s: [16, 34],      // between one remark and the next anywhere about you
  again_s: 150,         // before the same person speaks again unasked
  full_m: 2.5, quiet_m: 12, floor: 0.25,   // the voice's loudness by distance: full, then down to `floor`
});

export const timeOf = (hour) => (!Number.isFinite(hour) ? null : hour >= 5 && hour < 12 ? 'morning' : hour >= 12 && hour < 18 ? 'afternoon' : 'evening');

/** The lines this person may say now: their voice, kind, hour and season, and their origin
 *  where a line names one. Lines nobody has heard lately first. */
export function linesFor(doc, who, kind, { hour = null, season = null, heard = new Set() } = {}) {
  if (!doc || !who) return [];
  const t = timeOf(hour);
  const fit = doc.lines.filter((l) => l.voice === who.voice && l.kind === kind && (!l.time || !t || l.time === t)
    && (!l.season || !season || l.season === season) && (!l.origin || l.origin === who.origin));
  const fresh = fit.filter((l) => !heard.has(l.id));
  return fresh.length ? fresh : fit;
}

/** `people` row 'voice[/origin]'. */
export function personVoice(doc, personId) {
  const row = doc?.people?.[personId];
  if (!row) return null;
  const [voice, origin = null] = String(row).split('/');
  return { voice, origin };
}

/** How loud a voice is at `d` metres: full near, falling to STREET.floor at quiet_m. */
export function gainAt(d) {
  if (!(d > STREET.full_m)) return 1;
  const k = Math.min(1, (d - STREET.full_m) / (STREET.quiet_m - STREET.full_m));
  return 1 - k * (1 - STREET.floor);
}

export function createStreetTalk({ scene, base, fetcher = globalThis.fetch?.bind(globalThis), humans = null,
  visitor = () => null, hour = () => null, season = () => null, speech = () => null, busy = () => false,
  host = () => false, onCaption = () => {}, media = () => new Audio(), random = Math.random,
  subtle = globalThis.crypto?.subtle, location = null, audioBase } = {}) {
  let doc = null, index = null, indexUrl = null, loading = null, failed = false;
  const keys = new Map();         // line id → clip key
  const spoke = new Map();        // person id → clock when they last spoke
  const heard = new Set();        // line ids heard this visit (lines repeat only once all are heard)
  let clock = 0, next = STREET.gap_s[0] * 0.5, el = null, routed = null, speaking = null, said = 0, last = null;

  function load() {
    if (doc || failed) return Promise.resolve(doc);
    loading ??= (async () => {
      try {
        const r = await fetcher(new URL(`${scene}.json`, base));
        if (!r.ok) throw Error(`HTTP ${r.status}`);
        const d = await r.json();
        // No narration index (offline, a host refusing) leaves every line unvoiced, so silent.
        try {
          indexUrl = await (location ?? indexLocation({ fetcher, ...(audioBase ? { base: audioBase } : {}) }));
          const ir = await fetcher(indexUrl, { cache: 'no-cache' });
          index = ir.ok ? await ir.json() : null;
        } catch { index = null; }
        for (const l of d.lines) keys.set(l.id, streetKey(await textKey(l.text, subtle), l.voice));
        doc = d;
      } catch { failed = true; }
      loading = null; return doc;
    })();
    return loading;
  }
  const clipOf = (line) => { const c = index?.clips?.[keys.get(line.id)]; return c && typeof c.file === 'string' ? c : null; };

  function element() {
    if (el) return el;
    el = media(); el.preload = 'auto'; el.crossOrigin = 'anonymous';
    el.addEventListener?.('ended', () => finish());
    el.addEventListener?.('error', () => finish());
    return el;
  }
  function route() {
    const out = speech(); if (!out?.ctx || !out.bus) return false;
    if (routed?.ctx !== out.ctx) {
      try { routed?.node.disconnect(); } catch {}
      const node = out.ctx.createMediaElementSource(element());
      const gain = out.ctx.createGain(); node.connect(gain); gain.connect(out.bus);
      let ear = null;
      try { if (typeof out.ctx.createAnalyser === 'function') { ear = out.ctx.createAnalyser(); ear.fftSize = VOICE.window; node.connect(ear); } } catch { ear = null; }
      routed = { ctx: out.ctx, node, gain, ear, samples: ear ? new Uint8Array(VOICE.window) : null };
    }
    return true;
  }
  function hush(s = speaking) {
    const a = s?.actor; if (!a || a.disposed) return;
    a.actions?.setTalk?.(false);
    const mouth = a.actions?.mouth; if (mouth?.hush) mouth.hush(); else mouth?.say?.(null);
  }
  function finish() { if (!speaking) return; hush(); speaking = null; }
  function stop() { if (!speaking) return; try { el.pause(); } catch {} finish(); }

  const dist = (a, v) => Math.hypot(a.e - v.e, a.n - v.n);
  function candidate(actor) {
    const id = actor?.personId ?? actor?.id;
    if (!actor || actor.disposed || actor.indoors || actor.jauntHost || host(id) || actor.root?.visible === false) return null;
    const who = personVoice(doc, id); if (!who) return null;
    return { id, actor, who };
  }

  function say(c, kind) {
    const out = speech(); if (!out?.audible || !route()) return false;
    const lines = linesFor(doc, c.who, kind, { hour: hour(), season: season(), heard }).filter(clipOf);
    if (!lines.length) return false;
    const line = lines[Math.floor(random() * lines.length) % lines.length], clip = clipOf(line);
    const a = element();
    stop();
    a.src = new URL(clip.file, new URL('../', indexUrl)).href;
    const v = visitor(); routed.gain.gain.value = v ? gainAt(dist(c.actor, v)) : 1;
    speaking = { ...c, line }; said++; last = { person: c.id, line: line.id, kind };
    heard.add(line.id); if (heard.size > doc.lines.length * 0.8) heard.clear();
    spoke.set(c.id, clock);
    c.actor.actions?.setTalk?.(true);
    // The caption shows what is heard: a clip the page may not play yet (no tap so far) shows nothing.
    const own = speaking, shown = () => { if (speaking === own) onCaption({ personId: c.id, actor: c.actor, text: line.text, kind }); };
    const p = a.play();
    if (p?.then) p.then(shown, () => { if (speaking === own) finish(); }); else shown();
    return true;
  }

  return {
    load,
    get state() { return { loaded: !!doc, failed, speaking: speaking ? { person: speaking.id, line: speaking.line.id } : null, said, last }; },
    /** Someone the visitor greeted answers. Loads the lines the first time (a tap). */
    greet(personId) {
      const go = () => {
        const actor = humans?.get?.(personId); const c = candidate(actor);
        if (!c || busy()) return false;
        return say(c, 'greet');
      };
      if (doc) return go();
      void load().then(go);
      return false;
    },
    update(dt = 0) {
      clock += dt;
      if (speaking) {
        const v = visitor(), a = speaking.actor;
        if (!a || a.disposed || busy() || speech()?.audible === false) { stop(); return; }
        if (v && routed) routed.gain.gain.value = gainAt(dist(a, v));
        let level = null;
        if (routed?.ear && el && !el.paused) { routed.ear.getByteTimeDomainData(routed.samples); level = voiceLevel(routed.samples); }
        a.actions?.mouth?.say?.(level);
        return;
      }
      if (clock < next) return;
      next = clock + STREET.gap_s[0] + random() * (STREET.gap_s[1] - STREET.gap_s[0]);
      if (!doc) { void load(); return; }
      const v = visitor(); if (!v || busy() || !speech()?.audible) return;
      const near = [];
      for (const actor of humans?.actors ?? []) {
        if (!actor || !(dist(actor, v) <= STREET.reach_m)) continue;
        const c = candidate(actor);
        if (!c || clock - (spoke.get(c.id) ?? -Infinity) < STREET.again_s) continue;
        near.push({ ...c, d: dist(actor, v) });
      }
      if (!near.length) return;
      const c = near[Math.floor(random() * near.length) % near.length];
      say(c, c.d <= STREET.greet_m && random() < 0.5 ? 'greet' : 'remark');
    },
    stop,
    dispose() { stop(); try { routed?.node.disconnect(); routed?.gain.disconnect(); } catch {} routed = null; },
  };
}
