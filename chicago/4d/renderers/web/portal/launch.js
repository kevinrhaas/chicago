/**
 * T-3798: the /4d/ launch page. Four parts, each optional to the others:
 *
 *   years     the page opens on Chicago 4D with no year chosen; choosing a tile sets the hero
 *             (its still, date, marker and words) and the Play button; a second click, Enter or
 *             Play goes. The links are plain hrefs, so the page works without this script.
 *   check     the System check runs by itself on arrival: the town's own device profile
 *             (graphics, cores, memory, the short draw test), a download timing, then one
 *             verdict in plain words (launch-check.js). It never writes the town's cache.
 *   music     one looping bed from the score, off until the player turns it on; the choice
 *             is remembered, and a remembered "on" starts at the first click or key (browsers
 *             allow no sound before one).
 *   account   the same Firebase sign-in the years use, so a player signed in here is signed
 *             in there; no visit is recorded for this page. Rights by sign-in address
 *             (cloud play, admin) come from launch-access.js (T-3797).
 *
 * Settings write the keys the town already reads: the skin (skin.js), the language
 * (chicago.lang), and Scene detail and town sound inside chicago4d.settings.
 */
import { verdictFor, checkRows, DETAIL_WORD } from './launch-check.js';

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const store = {
  get(k, d = null) { try { return localStorage.getItem(k) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
};
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
export const MUSIC_KEY = 'chicago4d.launch.music';
export const MUSIC_VOLUME_KEY = 'chicago4d.launch.musicVolume';
export const MUSIC_ASSET = 'score-bed-1904-places';
const SETTINGS_KEY = 'chicago4d.settings';
const LANG_KEY = 'chicago.lang';

const state = { year: '', reading: null, cloud: { offered: false, ready: false }, waiting: false, account: null, rights: [] };

// ---- Years ---------------------------------------------------------------------------------
// The page opens on Chicago 4D itself, with no year chosen (owner, 2026-11-27: the page should
// not decide a year for the player). Calm by design (same day: "not jumpy and busy"):
//   - with nothing chosen, the backdrop drifts slowly through the four years' stills;
//   - a mouse resting on a tile fades only the backdrop to that year; the words stay put;
//   - choosing a year (click, tap, or keyboard focus) crossfades the hero's words, which sit in
//     space reserved for the longest of them, so nothing below moves;
//   - Play, a click on the chosen year, or a double click goes there; Escape goes back to none.
const tiles = $$('.year-tile');
const stills = $$('.backdrop-still');
const hero = $('.hero-words');
const home = { coord: $('#hero-coord').textContent, state: $('#hero-state').textContent, title: [...$('#hero-year').childNodes].map((n) => n.cloneNode(true)),
  name: $('#hero-name').textContent, lede: $('#hero-lede').textContent };
let chosen = '';
let backdrop = '';
function showStill(year) {
  if (!year || year === backdrop) return;
  backdrop = year;
  const [a, b] = stills;
  const on = a.classList.contains('is-on') ? a : b, off = on === a ? b : a;
  const src = `walk/portal/stills/${year}.webp`;
  off.srcset = `walk/portal/stills/${year}-800.webp 800w, ${src} 1600w`; off.sizes = '100vw'; off.src = src;
  const show = () => { if (backdrop !== year) return; off.classList.add('is-on'); on.classList.remove('is-on'); };
  if (off.complete && off.naturalWidth) show(); else off.addEventListener('load', show, { once: true });
}
function paintPlay(year) {
  const play = $('#play'), label = $('#play-label');
  play.dataset.ready = String(!!year);
  if (year) { const b = document.createElement('b'); b.id = 'play-year'; b.textContent = year; label.replaceChildren('Play ', b); play.href = `${year}/`; }
  else { label.replaceChildren('Choose a year'); play.href = '#years'; }
}
function writeHero(year) {
  const tile = tiles.find((t) => t.dataset.year === year);
  const st = $('#hero-state');
  if (tile) {
    $('#hero-coord').textContent = `DESTINATION ${tile.dataset.index} · ${tile.dataset.date}`;
    st.textContent = tile.dataset.state; st.classList.toggle('nominal', tile.dataset.state === 'LOCK NOMINAL');
    $('#hero-year').replaceChildren(year);
    $('#hero-name').textContent = tile.querySelector('.tile-name').textContent;
    $('#hero-lede').textContent = tile.dataset.lede;
  } else {
    $('#hero-coord').textContent = home.coord;
    st.textContent = home.state; st.classList.add('nominal');
    $('#hero-year').replaceChildren(...home.title.map((n) => n.cloneNode(true)));
    $('#hero-name').textContent = home.name;
    $('#hero-lede').textContent = home.lede;
  }
  document.body.dataset.selected = tile ? year : '';
}
// The words fade out, change, and fade back in; a quick second choice just retargets.
let heroTimer = 0;
function crossfadeHero(year) {
  clearTimeout(heroTimer);
  if (reduced.matches) { writeHero(year); return; }
  hero.classList.add('is-changing');
  heroTimer = setTimeout(() => { writeHero(year); requestAnimationFrame(() => hero.classList.remove('is-changing')); }, 200);
}
function choose(year) {
  if (year === chosen) return;
  chosen = year;
  state.year = year;
  for (const t of tiles) { const on = t.dataset.year === year; t.classList.toggle('is-selected', on); if (on) t.setAttribute('aria-current', 'true'); else t.removeAttribute('aria-current'); }
  paintPlay(year);
  crossfadeHero(year);
  if (year) showStill(year);
}
// A resting mouse previews a year in the backdrop only, after a short pause so a sweep across
// the rail does not flicker; leaving the rail settles back.
let hoverTimer = 0;
const preview = (year) => { clearTimeout(hoverTimer); hoverTimer = setTimeout(() => showStill(year || chosen || backdrop), year ? 140 : 260); };
// With nothing chosen and nothing under the mouse, the backdrop drifts from year to year.
let hovering = false;
let drift = 0;
if (!reduced.matches) {
  setInterval(() => {
    if (chosen || hovering || document.hidden) return;
    drift = (drift + 1) % tiles.length;
    showStill(tiles[drift].dataset.year);
  }, 9000);
}
backdrop = tiles[0]?.dataset.year || '';
function launch(href, year) {
  const veil = $('#launching');
  if (!veil.hidden) return;
  $('#launching-year').textContent = year;
  veil.hidden = false;
  musicFade(0, 500);
  setTimeout(() => location.assign(href), reduced.matches ? 0 : 650);
}
// A tap focuses the tile too, so a focus only chooses when it came from the keyboard
// (:focus-visible), or the first tap would launch.
for (const tile of tiles) {
  tile.addEventListener('click', (e) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
    e.preventDefault();
    if (tile.dataset.year === chosen) launch(tile.getAttribute('href'), tile.dataset.year);
    else choose(tile.dataset.year);
  });
  tile.addEventListener('dblclick', (e) => { e.preventDefault(); launch(tile.getAttribute('href'), tile.dataset.year); });
  tile.addEventListener('focus', () => { if (tile.matches(':focus-visible')) choose(tile.dataset.year); });
  tile.addEventListener('pointerenter', (e) => { if (e.pointerType === 'mouse') { hovering = true; preview(tile.dataset.year); } });
}
$('#year-rail').addEventListener('pointerleave', (e) => { if (e.pointerType === 'mouse') { hovering = false; preview(''); } });
$('#play').addEventListener('click', (e) => {
  if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
  e.preventDefault();
  if (chosen) { launch($('#play').getAttribute('href'), chosen); return; }
  // No year yet: point at the years rather than pick one.
  const rail = $('#year-rail');
  rail.scrollIntoView({ block: 'nearest', behavior: reduced.matches ? 'auto' : 'smooth' });
  rail.classList.remove('is-calling'); void rail.offsetWidth; rail.classList.add('is-calling');
});
addEventListener('keydown', (e) => {
  if (e.key !== 'Escape' || !chosen || document.querySelector('dialog[open]') || !$('#launching').hidden) return;
  document.activeElement?.blur?.();
  choose('');
});
// Back from a year with the browser's Back button: the page comes from the cache, veiled.
addEventListener('pageshow', (e) => { if (e.persisted) $('#launching').hidden = true; });

// ---- Music ---------------------------------------------------------------------------------
let audio = null, audioSrc = null;
const musicOn = () => store.get(MUSIC_KEY) === 'on';
const musicVolume = () => { const v = Number(store.get(MUSIC_VOLUME_KEY, '0.6')); return Number.isFinite(v) ? Math.min(1, Math.max(0, v)) : 0.6; };
async function musicURL() {
  if (audioSrc) return audioSrc;
  const base = new URL('walk/audio/', document.baseURI);
  const catalog = await fetch(new URL('catalog.json', base)).then((r) => r.json());
  const asset = (catalog.assets || []).find((a) => a.id === MUSIC_ASSET);
  if (!asset) throw new Error('no launch music in the catalogue');
  const opus = document.createElement('audio').canPlayType('audio/ogg; codecs="opus"');
  audioSrc = new URL(opus && asset.opus ? asset.opus : asset.aac, base).href;
  return audioSrc;
}
let fadeTimer = 0;
function musicFade(to, ms = 900) {
  if (!audio) return;
  clearInterval(fadeTimer);
  const from = audio.volume, t0 = performance.now();
  fadeTimer = setInterval(() => {
    const k = Math.min(1, (performance.now() - t0) / ms);
    audio.volume = from + (to - from) * k;
    if (k >= 1) { clearInterval(fadeTimer); if (to === 0) audio.pause(); }
  }, 40);
}
async function musicStart() {
  try {
    if (!audio) { audio = new Audio(); audio.loop = true; audio.preload = 'auto'; audio.volume = 0; audio.src = await musicURL(); }
    await audio.play();
    musicFade(musicVolume());
    return true;
  } catch (err) { console.warn('[launch] music', err); return false; }
}
function paintMusic() {
  const on = musicOn();
  $('#music-toggle').setAttribute('aria-pressed', String(on));
  $('#music-state').textContent = on ? 'On' : 'Off';
  $('#set-music').checked = on;
}
async function setMusic(on) {
  store.set(MUSIC_KEY, on ? 'on' : 'off');
  paintMusic();
  if (on) await musicStart(); else musicFade(0, 400);
}
$('#music-toggle').addEventListener('click', () => void setMusic(!musicOn()));
paintMusic();
if (musicOn()) {
  // A remembered "on": try now (some browsers allow it after an earlier visit), else at the first gesture.
  const first = () => { removeEventListener('pointerdown', first, true); removeEventListener('keydown', first, true); if (musicOn() && (!audio || audio.paused)) void musicStart(); };
  void musicStart().then((ok) => { if (!ok) { addEventListener('pointerdown', first, true); addEventListener('keydown', first, true); } });
}
document.addEventListener('visibilitychange', () => { if (!audio || !musicOn()) return; if (document.hidden) audio.pause(); else void audio.play().catch(() => {}); });

// ---- Settings ------------------------------------------------------------------------------
const settingsDialog = $('#settings');
const readTown = () => { try { return JSON.parse(store.get(SETTINGS_KEY, '{}')) || {}; } catch { return {}; } };
const writeTown = (patch) => store.set(SETTINGS_KEY, JSON.stringify({ ...readTown(), ...patch }));
function paintSettings() {
  const town = readTown();
  $('#set-music-volume').value = String(Math.round(musicVolume() * 100));
  $('#set-town-sound').checked = town.soundChosen === true && Number(town.soundMaster) > 0;
  $('#set-detail').value = DETAIL_WORD[town.detail] ? town.detail : '';
  $('#set-lang').value = store.get(LANG_KEY) === 'es' ? 'es' : 'en';
  paintMusic();
}
$('#settings-open').addEventListener('click', () => { paintSettings(); settingsDialog.showModal(); });
$('#set-music').addEventListener('change', (e) => void setMusic(e.target.checked));
$('#set-music-volume').addEventListener('input', (e) => { const v = Number(e.target.value) / 100; store.set(MUSIC_VOLUME_KEY, String(v)); if (audio && !audio.paused) { clearInterval(fadeTimer); audio.volume = v; } });
$('#set-town-sound').addEventListener('change', (e) => writeTown(e.target.checked ? { soundMaster: 0.8, soundChosen: true } : { soundMaster: 0, soundChosen: true }));
$('#set-detail').addEventListener('change', (e) => { const v = e.target.value; const town = readTown(); if (v) town.detail = v; else delete town.detail; store.set(SETTINGS_KEY, JSON.stringify(town)); paintVerdict(); });
$('#set-lang').addEventListener('change', (e) => store.set(LANG_KEY, e.target.value));
for (const d of $$('dialog')) {
  d.addEventListener('click', (e) => { if (e.target === d) d.close(); });
  for (const c of d.querySelectorAll('[data-close]')) c.addEventListener('click', () => d.close());
}

// ---- System check --------------------------------------------------------------------------
const check = $('#check');
const row = (name, words, warn = false) => { const li = check.querySelector(`[data-row="${name}"]`); if (!li) return; li.querySelector('b').textContent = words; li.classList.add('is-read'); li.classList.toggle('warn', warn); };
const segs = [...check.querySelectorAll('.check-meter i')];
function paintMeter(score, grade) {
  const lit = Math.max(1, Math.min(segs.length, Math.round(score / (100 / segs.length))));
  segs.forEach((s, i) => s.classList.toggle('on', i < lit));
  const m = $('#check-meter');
  m.dataset.grade = grade; m.setAttribute('aria-valuenow', String(score)); m.setAttribute('aria-valuetext', `${score} of 100, ${grade}`);
}
async function measureDownload() {
  const c = navigator.connection;
  // Chrome and Edge report a downlink estimate; elsewhere a ~350 KB file is timed.
  if (c && Number.isFinite(c.downlink) && c.downlink > 0) return c.downlink;
  try {
    const t0 = performance.now();
    const r = await fetch(new URL(`walk/audio/wind.mp3?check=${Date.now()}`, document.baseURI), { cache: 'no-store' });
    const bytes = (await r.arrayBuffer()).byteLength;
    const s = (performance.now() - t0) / 1000;
    return bytes > 50000 && s > 0 ? (bytes * 8) / s / 1e6 : NaN;
  } catch { return NaN; }
}
async function runCheck() {
  check.dataset.state = 'running';
  $('#check-phase').textContent = 'SCANNING';
  $('#verdict-title').textContent = 'Checking this computer…';
  $('#verdict-advice').textContent = 'This takes a few seconds and changes nothing.';
  for (const li of check.querySelectorAll('.check-log li')) { li.classList.remove('is-read', 'warn'); li.querySelector('b').textContent = 'reading…'; }
  segs.forEach((s) => s.classList.remove('on'));
  const dp = await import('../js/device-profile.js');
  const touch = matchMedia('(pointer: coarse)').matches || (navigator.maxTouchPoints > 0 && innerWidth < 900);
  await new Promise((r) => requestAnimationFrame(() => setTimeout(r, 250)));
  row('draw', 'running…');
  const [profile, mbps] = await Promise.all([
    dp.profileDevice({ touch, storage: null, search: location.search }),
    measureDownload(),
  ]);
  const { score, grade } = dp.scoreProfile(profile);
  const shared = !touch && dp.sharesSystemMemory(profile.signals?.renderer);
  const rows = checkRows(profile, { mbps, shared });
  const pace = reduced.matches ? 0 : 260;
  const steps = [['gpu', rows.gpu, shared], ['cpu', rows.cpu], ['memory', rows.memory], ['draw', `${score} / 100 · ${grade.label}`, score < 40], ['network', rows.network, Number.isFinite(mbps) && mbps < 5]];
  for (const [name, words, warn] of steps) { row(name, words, !!warn); await new Promise((r) => setTimeout(r, pace)); }
  paintMeter(score, grade.id);
  state.reading = { score, grade: grade.id, detail: profile.choice?.detail || 'full', webgl2: !!profile.signals?.webgl2, software: /software rasteriser/.test(profile.why || ''), touch, mbps };
  check.dataset.state = 'done';
  $('#check-phase').textContent = 'COMPLETE';
  paintVerdict();
}
function paintVerdict() {
  if (!state.reading) return;
  const chosen = DETAIL_WORD[readTown().detail] ? readTown().detail : '';
  const v = verdictFor(state.reading, state.cloud, chosen);
  $('#verdict-title').textContent = v.title;
  $('#verdict-advice').textContent = v.advice;
  check.dataset.verdict = v.kind;
  const chip = $('#hero-verdict'); chip.dataset.state = v.kind; $('#hero-verdict-text').textContent = v.title;
  paintCloud(v.cloud || (!state.cloud.offered && (v.kind === 'lower' || v.kind === 'blocked')));
  // When the check lands on a lower level than the town would pick by itself, it says so;
  // the town already boots at the profile's level, so no setting needs to be written.
  $('#check-apply').hidden = true;
}
$('#check-again').addEventListener('click', () => void runCheck().catch(failCheck));
function failCheck(err) {
  console.warn('[launch] system check', err);
  check.dataset.state = 'done';
  $('#check-phase').textContent = 'NO READING';
  $('#verdict-title').textContent = 'This computer could not be read';
  $('#verdict-advice').textContent = 'You can still play. The town picks its own detail level when it opens.';
}
void runCheck().catch(failCheck);

// ---- Cloud play ----------------------------------------------------------------------------
// Everyone sees the cloud button. With cloud play it starts a machine; without it, it puts the
// player on the waitlist (owner, 2026-11-27), signing them in first if they are not.
function paintCloud(recommended = false) {
  const btn = $('#play-cloud');
  btn.hidden = false;
  btn.dataset.mode = state.cloud.offered ? 'play' : state.waiting ? 'waiting' : 'join';
  btn.querySelector('span').textContent = state.cloud.offered ? 'Play from the cloud' : state.waiting ? 'On the cloud waitlist' : 'Join the cloud waitlist';
  btn.classList.toggle('is-recommended', recommended);
}
const say = (title, advice) => { $('#verdict-title').textContent = title; $('#verdict-advice').textContent = advice; };
let joinAfterSignIn = false;
async function joinWaitlist() {
  const access = await loadAccess();
  const r = access?.joinWaitlist ? await access.joinWaitlist({ account: state.account, config, year: state.year, check: $('#hero-verdict-text').textContent }).catch(() => null) : null;
  if (r?.ok) {
    state.waiting = true; paintCloud();
    say('You are on the cloud waitlist', 'Cloud play runs the town on our machines and streams it to you. When you are let in, this button starts one for you; until then, play here.');
  } else say('Could not join the waitlist', r?.why === 'sign in' ? 'Sign in with Google or an email link first.' : 'Something went wrong. Try again in a moment.');
}
$('#play-cloud').addEventListener('click', async () => {
  const mode = $('#play-cloud').dataset.mode;
  if (mode === 'waiting') { say('You are on the cloud waitlist', 'When you are let in, this button starts a cloud machine for you. Until then, play here.'); return; }
  if (mode === 'join') {
    if (!state.account) { joinAfterSignIn = true; $('#account-note').textContent = 'Sign in to join the cloud play waitlist.'; $('#account-open').click(); return; }
    await joinWaitlist(); return;
  }
  const access = await loadAccess();
  const r = access?.startCloud ? await access.startCloud({ year: state.year, account: state.account, config }).catch(() => null) : null;
  if (r?.ok) return;
  say(r?.title || 'Cloud play is opening soon', r?.message || 'The cloud machines are waiting on Google to approve graphics capacity. This button starts one for you once they are ready.');
});
paintCloud();

// ---- Account -------------------------------------------------------------------------------
const accountDialog = $('#account');
let signIn = null, config = null, accessMod = null;
async function loadSignIn() {
  if (!signIn) [signIn, { SIGN_IN: config }] = await Promise.all([import('../js/sign-in.js'), import('../js/sign-in-config.js')]);
  return signIn;
}
async function loadAccess() {
  if (accessMod !== null) return accessMod;
  try { accessMod = await import('./launch-access.js'); } catch { accessMod = false; }
  return accessMod;
}
const gateModeHere = () => signIn.gateMode({ config, hostname: location.hostname, search: location.search, webdriver: !!navigator.webdriver });
function paintAccount() {
  const a = state.account;
  const label = $('#account-label');
  $('#account-open').classList.toggle('is-in', !!a);
  label.textContent = a ? (a.name || a.email || 'Signed in') : 'Sign in';
  $('#account-who').hidden = !a;
  if (a) $('#account-email').textContent = a.email || 'this device';
  $('#account-rights').textContent = state.rights.length ? `Rights: ${state.rights.map((r) => ({ cloud: 'cloud play', admin: 'admin' }[r] || r)).join(' · ')}` : '';
  $('#admin-open').hidden = !state.rights.includes('admin');
  $('#account-note').hidden = !!a;
}
async function afterSignIn(account) {
  state.account = account || null;
  const access = account ? await loadAccess() : null;
  const r = access?.myRights ? await access.myRights({ account, config }).catch(() => null) : null;
  state.rights = r?.rights ?? [];
  state.cloud = { offered: state.rights.includes('cloud'), ready: !!r?.cloudReady };
  state.waiting = !!r?.waiting;
  paintAccount();
  paintCloud();
  paintVerdict();
  if (joinAfterSignIn && account && !state.cloud.offered && !state.waiting) { joinAfterSignIn = false; await joinWaitlist(); }
  if (state.rights.includes('admin')) access?.mountAdmin?.({ account, config, body: $('#admin-body') });
}
$('#admin-open').addEventListener('click', () => { $('#admin').showModal(); void accessMod?.refreshAdmin?.(); });
// Closing the sheet without signing in drops a waitlist join that was waiting on the sign-in.
accountDialog.addEventListener('close', () => { joinAfterSignIn = false; });
$('#account-open').addEventListener('click', async () => {
  if (!joinAfterSignIn) $('#account-note').textContent = 'One sign-in opens every year.';
  accountDialog.showModal();
  await loadSignIn();
  const mode = gateModeHere();
  const gateEl = $('#gate');
  if (state.account) { gateEl.replaceChildren(); paintAccount(); return; }
  if (mode === 'off' || mode === 'robot') {
    gateEl.replaceChildren();
    $('#account-note').textContent = 'Sign-in is off on this copy of the site. On chicago.polecat.live it opens every year.';
    return;
  }
  if (gateEl.dataset.signin === 'open') return;
  const r = await signIn.signInGate({ year: '', gate: gateEl, config, record: false });
  gateEl.replaceChildren(); delete gateEl.dataset.signin;
  if (r.account) { await afterSignIn(r.account); accountDialog.close(); }
});
$('#account-sign-out').addEventListener('click', async () => {
  await state.account?.signOut?.();
  state.account = null; state.rights = []; state.cloud = { offered: false, ready: false }; state.waiting = false; paintCloud();
  paintAccount(); paintVerdict();
  accountDialog.close();
});
// Who is already signed in on this device (the years' own session), after first paint.
(window.requestIdleCallback || ((f) => setTimeout(f, 1200)))(async () => {
  try {
    await loadSignIn();
    if (gateModeHere() !== 'on') return;
    const r = await signIn.signedInUser(config);
    const u = r?.user;
    if (u && !u.isAnonymous) {
      await afterSignIn({ uid: u.uid, email: u.email || u.providerData?.find((p) => p.email)?.email || '', name: u.displayName || '', method: signIn.methodOf(u),
        idToken: () => u.getIdToken(), signOut: async () => { await r.authMod.signOut(r.auth); } });
    }
  } catch (err) { console.warn('[launch] account', err); }
});
paintAccount();
