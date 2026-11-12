/** T-3532: recorded environment and owner-supplied score. No synthesized hum,
 * drone, ticker or relay. Audio remains opt-in; one shared gesture-owned context.
 * Music streams; environmental loops have a bounded decoded cache. */
import { SOUND_DEFAULTS, normalVolume, soundLevelsFrom } from './settings-app.js';
import { createRecordedAudio } from './recorded-audio.js';

export const curve = v => normalVolume(v, 0) ** 2;
export function mayStartEarly({ nav = globalThis.navigator, transfer = false } = {}) {
  try { const p = nav?.getAutoplayPolicy?.('audiocontext'); if (p) return p === 'allowed'; } catch {}
  return !!transfer;
}
export function createSound({ audio = () => null, unlock = null, early = false,
  settings = () => null, scene = () => '', environment = () => ({}), workEnvironment = () => ({}), journey = null,
  storage = (() => { try { return globalThis.localStorage; } catch { return null; } })(),
  doc = globalThis.document ?? null, recordings = createRecordedAudio,
  every = (fn, ms) => setInterval(fn, ms), cancelEvery = clearInterval } = {}) {
  let ctx = null, master = null, effects = null, bed = null, music = null, recorded = null, disposed = false;
  let levels = {}, active = false;
  const stored = () => { try { return soundLevelsFrom(JSON.parse(storage?.getItem?.('chicago4d.settings') || '{}')); } catch { return SOUND_DEFAULTS; } };
  function sync() {
    if (disposed) return state();
    const s = settings() ?? stored();
    levels = { master: normalVolume(s.soundMaster, SOUND_DEFAULTS.soundMaster),
      effects: normalVolume(s.soundEffects, SOUND_DEFAULTS.soundEffects),
      ambience: normalVolume(s.soundAmbience, SOUND_DEFAULTS.soundAmbience),
      music: normalVolume(s.soundMusic, SOUND_DEFAULTS.soundMusic) };
    const next = audio();
    if (next && next !== ctx) {
      recorded?.dispose();
      for (const node of [master, effects, bed, music]) node?.disconnect();
      ctx?.removeEventListener?.('statechange', sync); ctx = next;
      master = ctx.createGain(); effects = ctx.createGain(); bed = ctx.createGain(); music = ctx.createGain();
      master.gain.value = 0; music.gain.value = 0;
      master.connect(ctx.destination); effects.connect(master); bed.connect(master); music.connect(master);
      recorded = recordings({ ctx, ambience: bed, effects, music, environment, workEnvironment });
      ctx.addEventListener?.('statechange', sync);
    }
    active = !!ctx && ctx.state === 'running' && levels.master > 0 && !doc?.hidden && doc?.visibilityState !== 'hidden';
    if (ctx) {
      master.gain.setTargetAtTime(active ? curve(levels.master) : 0, ctx.currentTime, .08);
      effects.gain.setTargetAtTime(curve(levels.effects), ctx.currentTime, .08);
      bed.gain.setTargetAtTime(curve(levels.ambience), ctx.currentTime, .08);
      const inTown = !journey || ['exploring', 'inspecting', 'on-jaunt', 'touring'].includes(journey.state);
      recorded.sync({ active, ambienceOn: levels.ambience > 0, effectsOn: levels.effects > 0, musicOn: levels.music > 0 && inTown,
        musicLevel: levels.music, year: scene() });
    }
    return state();
  }
  function state() {
    return { context: ctx?.state ?? 'none', levels: { ...levels }, silent: !active, hum: false,
      ambience: active && levels.ambience > 0 ? String(scene()) : null,
      gains: { master: master?.gain.value ?? null, effects: effects?.gain.value ?? null,
        ambience: bed?.gain.value ?? null, music: music?.gain.value ?? null },
      recorded: recorded?.state ?? null };
  }
  doc?.addEventListener?.('visibilitychange', sync);
  const offJourney = journey?.on?.(sync);
  const effectsFrameActive = () => !disposed && active && ctx?.state === 'running'
    && levels.effects > 0 && !doc?.hidden && doc?.visibilityState !== 'hidden'
    && (!journey || ['exploring', 'inspecting', 'on-jaunt', 'touring'].includes(journey.state));
  if (early && mayStartEarly({ transfer: doc?.documentElement?.dataset?.transfer === 'true' }) && stored().soundMaster > 0) unlock?.();
  sync();
  const timer = every(sync, 250);
  return { sync, apply: sync, setting: key => { if (key == null || /^sound/.test(key)) sync(); },
    transportFrame({ active: visible = true } = {}) {
      recorded?.transportFrame?.({ active: visible && effectsFrameActive() });
    },
    workFrame({ active: visible = true } = {}) {
      recorded?.workFrame?.({ active: visible && effectsFrameActive() });
    },
    // Compatibility with arrival callers; no synthetic replacement is played.
    ticker: () => 0, relay: () => false, land: () => false,
    setSpeechActive: on => recorded?.setSpeechActive(on),
    get state() { return state(); },
    get nodes() { return ctx ? { master, effects, ambience: bed, music } : null; },
    dispose() { disposed = true; cancelEvery(timer); offJourney?.(); recorded?.dispose();
      doc?.removeEventListener?.('visibilitychange', sync); ctx?.removeEventListener?.('statechange', sync);
      // Let the environmental fade finish before releasing its destination.
      if (master) master.gain.setTargetAtTime(0, ctx.currentTime, .05);
    },
  };
}
