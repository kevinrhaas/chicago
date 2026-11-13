/**
 * T-3576: THE SIGN-IN GATE. The owner, 2026-11-13: Google sign-in "when you hit one of the
 * time zone years before hitting the download", or "someone could provide an email to get
 * in if they don't have a Google account and then it's ok to let them in with that", with
 * no server; "you should not have to auth to separate years"; and "I would want to be able
 * to know or get a list ... of everyone who has come in".
 *
 * So boot() waits on signInGate() before the scene is fetched. Every way into a year goes
 * through boot() — the Observatory's cards, the /1812/ /1835/ /1904/ doors, ?year= links —
 * so one gate covers them all. The panel sits inside the arrival device in place of its
 * instruments, offering:
 *
 *   - Continue with Google: Firebase Auth, a popup (redirect when the popup is blocked);
 *   - behind a small grey "No Google account? Sign in manually" link (the owner: "we
 *     really want them to auth through Google"), an email: Firebase anonymous sign-in
 *     plus the typed address, unverified for now.
 *     (Verified email later is Firebase's email-link sign-in on the same project.)
 *
 * Firebase keeps the sign-in on the device (IndexedDB) for the whole site, so the next
 * year, and the next visit, pass straight through. Each entry into a year is written to
 * the visitor list (visitor-store.js) and, when Analytics is configured, logged as an
 * `enter_year` event. Neither write holds up the boot.
 *
 * It never locks anyone out by accident. With the gate off (js/sign-in-config.js), on a
 * host the config does not name, or under automation (navigator.webdriver: the smoke, the
 * photo-match and film tools), it returns at once and loads nothing. If the Firebase SDK
 * cannot load or the service cannot be reached, the visitor goes in and the console says
 * why. This is a front door, not a lock: the town's files are public on a static host.
 *
 * `?signin=preview` shows the panel with the gate off (no Firebase at all), for a look at
 * it before the project exists; both choices simply go in.
 */
import { SIGN_IN } from './sign-in-config.js';
import { deviceClass, recordEntry } from './visitor-store.js';

const FIREBASE = 'https://www.gstatic.com/firebasejs/13.3.0/';
export const EMAIL_KEY = 'chicago4d.signin.email';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

/** Is the config complete enough to start Firebase? */
export function configured(firebase = {}) {
  return ['apiKey', 'authDomain', 'projectId', 'appId'].every(key => String(firebase[key] || '').trim());
}

/** Should this page ask? Pure, so the self-test can hold every branch. */
export function gateMode({ config = SIGN_IN, hostname = '', search = '', webdriver = false } = {}) {
  let preview = false;
  try { preview = new URLSearchParams(search).get('signin') === 'preview'; } catch { /* no URL */ }
  const on = !!config.enabled && configured(config.firebase) && (config.hosts || []).includes(hostname);
  if (on && !webdriver) return 'on';
  if (preview) return 'preview';
  return on ? 'robot' : 'off';
}

export function validEmail(value) {
  return EMAIL_RE.test(String(value || '').trim()) && String(value).trim().length <= 254;
}

function read(storage, key) { try { return storage?.getItem(key) || ''; } catch { return ''; } }
function write(storage, key, value) { try { storage?.setItem(key, value); } catch { /* private mode */ } }

function timeout(promise, ms, what) {
  return Promise.race([promise, new Promise((_, reject) => setTimeout(() => reject(new Error(`${what} timed out`)), ms))]);
}

let loading = null;
function loadFirebase(cfg) {
  loading ??= startFirebase(cfg);
  return loading;
}

async function startFirebase(cfg) {
  const [appMod, authMod] = await Promise.all([
    import(`${FIREBASE}firebase-app.js`),
    import(`${FIREBASE}firebase-auth.js`),
  ]);
  const app = appMod.initializeApp({
    apiKey: cfg.apiKey, authDomain: cfg.authDomain, projectId: cfg.projectId, appId: cfg.appId,
    ...(cfg.measurementId ? { measurementId: cfg.measurementId } : {}),
  });
  const auth = authMod.getAuth(app);
  let analytics = null;
  if (cfg.measurementId) {
    // Optional and late: Analytics never holds the door.
    analytics = import(`${FIREBASE}firebase-analytics.js`)
      .then(async mod => (await mod.isSupported().catch(() => false)) ? { mod, a: mod.getAnalytics(app) } : null)
      .catch(() => null);
  }
  return { app, auth, authMod, analytics };
}

function methodOf(user) {
  if (!user) return 'none';
  if (user.isAnonymous) return 'email';
  const provider = user.providerData?.[0]?.providerId || '';
  return provider === 'google.com' ? 'google' : (provider || 'other');
}

const GOOGLE_G = '<svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M21.6 12.23c0-.68-.06-1.36-.18-2.02H12v3.83h5.4a4.62 4.62 0 0 1-2 3.03v2.5h3.24c1.9-1.75 2.96-4.33 2.96-7.34z"/><path d="M12 22c2.7 0 4.97-.9 6.63-2.43l-3.24-2.5c-.9.6-2.04.96-3.39.96-2.6 0-4.81-1.76-5.6-4.12H3.06v2.58A10 10 0 0 0 12 22z" opacity=".8"/><path d="M6.4 13.9a6 6 0 0 1 0-3.8V7.52H3.06a10 10 0 0 0 0 8.96L6.4 13.9z" opacity=".6"/><path d="M12 5.98c1.47 0 2.79.5 3.83 1.5l2.87-2.87A9.62 9.62 0 0 0 12 2a10 10 0 0 0-8.94 5.52L6.4 10.1C7.19 7.74 9.4 5.98 12 5.98z" opacity=".9"/></svg>';

/** The panel, built inside the arrival device. Returns its parts. */
export function buildPanel(doc, { year }) {
  const el = doc.createElement('section');
  el.id = 'signin';
  el.className = 'signin';
  el.setAttribute('role', 'group');
  el.setAttribute('aria-labelledby', 'signin-title');
  el.innerHTML = `
    <p class="signin-eyebrow"><span>Entry check</span><b></b></p>
    <h2 id="signin-title" class="signin-title" tabindex="-1">Sign in to travel</h2>
    <p class="signin-lede">One sign-in opens every year.</p>
    <button type="button" class="signin-google">${GOOGLE_G}<span>Continue with Google</span></button>
    <button type="button" class="signin-manual" aria-expanded="false" aria-controls="signin-email-form">No Google account? Sign in manually</button>
    <form id="signin-email-form" class="signin-email" novalidate hidden>
      <label class="visually-hidden" for="signin-email-input">Email</label>
      <input id="signin-email-input" type="email" name="email" inputmode="email" autocomplete="email"
             autocapitalize="off" spellcheck="false" placeholder="you@example.com" required>
      <button type="submit" class="signin-enter">Enter</button>
    </form>
    <p class="signin-msg" role="status" aria-live="polite"></p>
    <p class="signin-note">We keep your email so we know who has visited.</p>`;
  el.querySelector('.signin-eyebrow b').textContent = year ? String(year) : '';
  return {
    el,
    google: el.querySelector('.signin-google'),
    manual: el.querySelector('.signin-manual'),
    form: el.querySelector('.signin-email'),
    input: el.querySelector('#signin-email-input'),
    enter: el.querySelector('.signin-enter'),
    msg: el.querySelector('.signin-msg'),
  };
}

/**
 * Show the panel and resolve once the visitor is in. `onGoogle()` and `onEmail(email)`
 * resolve to true (go in) or throw an Error whose message is shown on the panel.
 */
function askVisitor({ gate, year, onGoogle, onEmail, storage }) {
  const doc = gate.ownerDocument;
  const card = gate.querySelector('.gate-card') || gate;
  const parts = buildPanel(doc, { year });
  const title = card.querySelector('#gate-title');
  if (title?.nextSibling) card.insertBefore(parts.el, title.nextSibling); else card.appendChild(parts.el);
  parts.input.value = read(storage, EMAIL_KEY);
  gate.dataset.signin = 'open';
  return new Promise(resolve => {
    let busy = false;
    const setBusy = on => {
      busy = on;
      parts.google.disabled = on;
      parts.enter.disabled = on;
      parts.el.toggleAttribute('aria-busy', on);
    };
    const done = how => {
      delete gate.dataset.signin;
      parts.el.remove();
      resolve(how);
    };
    const attempt = async (fn, how) => {
      if (busy) return;
      setBusy(true);
      parts.msg.textContent = '';
      try {
        if (await fn()) { done(how); return; }
      } catch (err) {
        parts.msg.textContent = err?.message || 'That did not work. Try again.';
      }
      setBusy(false);
    };
    parts.google.addEventListener('click', () => attempt(onGoogle, 'google'));
    // The owner, 2026-11-13: "we really want them to auth through Google", so the email
    // box waits behind a small grey link and opens only when asked for.
    parts.manual.addEventListener('click', () => {
      parts.form.hidden = false;
      parts.manual.hidden = true;
      parts.manual.setAttribute('aria-expanded', 'true');
      try { parts.input.focus({ preventScroll: true }); } catch { /* old browser */ }
    });
    parts.form.addEventListener('submit', event => {
      event.preventDefault();
      const email = parts.input.value.trim();
      if (!validEmail(email)) {
        parts.msg.textContent = 'That email does not look right.';
        parts.input.focus();
        return;
      }
      void attempt(() => onEmail(email), 'email');
    });
    // Keys typed here are the visitor's, not the walker's.
    parts.el.addEventListener('keydown', event => event.stopPropagation());
    try { parts.google.focus({ preventScroll: true }); } catch { /* old browser */ }
  });
}

const GOOGLE_ERRORS = {
  'auth/popup-closed-by-user': 'Google sign-in was closed. Try again, or use your email.',
  'auth/cancelled-popup-request': 'Google sign-in was closed. Try again, or use your email.',
  'auth/user-cancelled': 'Google sign-in was cancelled. Try again, or use your email.',
  'auth/network-request-failed': 'No connection to Google just now. Use your email instead.',
};

/**
 * The gate. Resolves `{ how }` once the visitor may enter: 'off', 'robot', 'preview',
 * 'returning', 'google', 'email' or 'fail-open'. Never rejects.
 */
export async function signInGate({
  year,
  gate = globalThis.document?.getElementById('gate'),
  config = SIGN_IN,
  loc = globalThis.location,
  nav = globalThis.navigator,
  storage = (() => { try { return globalThis.localStorage; } catch { return null; } })(),
  win = globalThis,
} = {}) {
  const mode = gateMode({ config, hostname: loc?.hostname, search: loc?.search, webdriver: !!nav?.webdriver });
  if (mode === 'off' || mode === 'robot' || !gate) return { how: mode === 'robot' ? 'robot' : 'off' };
  if (mode === 'preview') {
    const how = await askVisitor({ gate, year, storage,
      onGoogle: async () => true,
      onEmail: async email => { write(storage, EMAIL_KEY, email); return true; } });
    return { how: 'preview', chose: how };
  }

  let fb;
  try {
    fb = await timeout(loadFirebase(config.firebase), 12000, 'Firebase');
    // Back from a redirect sign-in (the popup was blocked): settle it before reading the user.
    await timeout(fb.authMod.getRedirectResult(fb.auth).catch(() => null), 8000, 'redirect result').catch(() => null);
    await timeout(fb.auth.authStateReady(), 8000, 'sign-in state');
  } catch (err) {
    loading = null;
    console.warn('[4D Chicago] sign-in: letting the visitor in, Firebase did not start', err);
    return { how: 'fail-open' };
  }

  const { auth, authMod } = fb;
  const device = deviceClass(win);
  const enter = (user, email) => {
    const method = methodOf(user);
    if (user) {
      void user.getIdToken().then(idToken => recordEntry({
        projectId: config.firebase.projectId, idToken,
        uid: user.uid, email: email || user.email || '', name: user.displayName || '',
        method, year: String(year || ''), device,
      })).catch(err => console.warn('[4D Chicago] sign-in: visit not recorded', err));
    }
    void fb.analytics?.then(an => {
      if (!an) return;
      an.mod.logEvent(an.a, 'enter_year', { year: String(year || ''), method, device });
    }).catch(() => {});
  };

  const current = auth.currentUser;
  const storedEmail = read(storage, EMAIL_KEY);
  if (current && (!current.isAnonymous || storedEmail)) {
    enter(current, current.isAnonymous ? storedEmail : '');
    return { how: 'returning' };
  }

  let typed = '';
  const logLogin = method => void fb.analytics?.then(an => an && an.mod.logEvent(an.a, 'login', { method })).catch(() => {});
  const how = await askVisitor({
    gate, year, storage,
    onGoogle: async () => {
      const provider = new authMod.GoogleAuthProvider();
      provider.setCustomParameters({ prompt: 'select_account' });
      try {
        await authMod.signInWithPopup(auth, provider);
        return true;
      } catch (err) {
        const code = err?.code || '';
        if (code === 'auth/popup-blocked' || code === 'auth/operation-not-supported-in-this-environment') {
          // The page leaves for Google and comes back signed in; the next boot passes.
          await authMod.signInWithRedirect(auth, provider);
          return false;
        }
        console.warn('[4D Chicago] sign-in: Google', code, err);
        throw new Error(GOOGLE_ERRORS[code] || 'Google sign-in did not work here. Use your email instead.');
      }
    },
    onEmail: async email => {
      typed = email;
      write(storage, EMAIL_KEY, email);
      try {
        if (!auth.currentUser) await timeout(authMod.signInAnonymously(auth), 10000, 'email sign-in');
      } catch (err) {
        // The email is the visitor's ticket in; a Firebase hiccup is not their problem.
        console.warn('[4D Chicago] sign-in: letting the visitor in, email not recorded', err);
      }
      return true;
    },
  });
  logLogin(how);
  enter(auth.currentUser, how === 'email' ? typed : '');
  return { how };
}

/** For the console and the visitors page: who is signed in on this device, and a way out. */
export async function signedInUser(config = SIGN_IN) {
  if (!configured(config.firebase)) return null;
  const fb = await loadFirebase(config.firebase);
  await fb.auth.authStateReady();
  return { user: fb.auth.currentUser, auth: fb.auth, authMod: fb.authMod };
}
