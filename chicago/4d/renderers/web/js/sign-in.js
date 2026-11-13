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
 *   - Continue with Google, and Continue with Microsoft (T-3580): Firebase Auth, a popup
 *     (the whole page to the provider and back when the popup is blocked);
 *   - behind a small grey "No Google or Microsoft account? Sign in with email" link (the
 *     owner: "we really want them to auth through Google"): an email and password (sign
 *     in, create an account, reset it), or the email alone — Firebase anonymous sign-in
 *     plus the typed address, unverified for now.
 *   `providers` in js/sign-in-config.js says which of the four the panel offers.
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

/** How a user signed in, in the words the visitor list keeps. */
export function methodOf(user) {
  if (!user) return 'none';
  if (user.isAnonymous) return 'email';
  const provider = user.providerData?.[0]?.providerId || '';
  return METHOD_OF_PROVIDER[provider] || provider || 'other';
}
const METHOD_OF_PROVIDER = { 'google.com': 'google', 'microsoft.com': 'microsoft', password: 'password' };

/** The ways in this config offers, in the panel's order. Google always comes first. */
export function offered(config = SIGN_IN) {
  const known = ['google', 'microsoft', 'password', 'email'];
  const asked = Array.isArray(config.providers) ? config.providers : ['google', 'email'];
  const list = known.filter(p => asked.includes(p));
  return list.length ? list : ['google', 'email'];
}

/** The grey link's words: name the big buttons the visitor does not have. */
export function manualLabel(providers) {
  const big = providers.filter(p => p === 'google' || p === 'microsoft').map(p => (p === 'google' ? 'Google' : 'Microsoft'));
  return big.length ? `No ${big.join(' or ')} account? Sign in with email` : 'Sign in with email';
}

const GOOGLE_G = '<svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M21.6 12.23c0-.68-.06-1.36-.18-2.02H12v3.83h5.4a4.62 4.62 0 0 1-2 3.03v2.5h3.24c1.9-1.75 2.96-4.33 2.96-7.34z"/><path d="M12 22c2.7 0 4.97-.9 6.63-2.43l-3.24-2.5c-.9.6-2.04.96-3.39.96-2.6 0-4.81-1.76-5.6-4.12H3.06v2.58A10 10 0 0 0 12 22z" opacity=".8"/><path d="M6.4 13.9a6 6 0 0 1 0-3.8V7.52H3.06a10 10 0 0 0 0 8.96L6.4 13.9z" opacity=".6"/><path d="M12 5.98c1.47 0 2.79.5 3.83 1.5l2.87-2.87A9.62 9.62 0 0 0 12 2a10 10 0 0 0-8.94 5.52L6.4 10.1C7.19 7.74 9.4 5.98 12 5.98z" opacity=".9"/></svg>';
const MICROSOFT_LOGO = '<svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M3 3h8.5v8.5H3z"/><path d="M12.5 3H21v8.5h-8.5z" opacity=".8"/><path d="M3 12.5h8.5V21H3z" opacity=".8"/><path d="M12.5 12.5H21V21h-8.5z" opacity=".6"/></svg>';

/** The panel, built inside the arrival device. Returns its parts. */
export function buildPanel(doc, { year, providers = ['google', 'email'] }) {
  const has = p => providers.includes(p);
  const manual = has('password') || has('email');
  const el = doc.createElement('section');
  el.id = 'signin';
  el.className = 'signin';
  el.setAttribute('role', 'group');
  el.setAttribute('aria-labelledby', 'signin-title');
  el.innerHTML = `
    <p class="signin-eyebrow"><span>Entry check</span><b></b></p>
    <h2 id="signin-title" class="signin-title" tabindex="-1">Sign in to travel</h2>
    <p class="signin-lede">One sign-in opens every year.</p>
    ${has('google') ? `<button type="button" class="signin-google">${GOOGLE_G}<span>Continue with Google</span></button>` : ''}
    ${has('microsoft') ? `<button type="button" class="signin-microsoft">${MICROSOFT_LOGO}<span>Continue with Microsoft</span></button>` : ''}
    ${manual ? `<button type="button" class="signin-manual" aria-expanded="false" aria-controls="signin-email-form"></button>
    <form id="signin-email-form" class="signin-email" novalidate hidden>
      <label class="visually-hidden" for="signin-email-input">Email</label>
      <input id="signin-email-input" type="email" name="email" inputmode="email" autocomplete="email"
             autocapitalize="off" spellcheck="false" placeholder="you@example.com" required>
      <label class="visually-hidden" for="signin-password-input">Password</label>
      <input id="signin-password-input" type="password" name="password" autocomplete="current-password"
             placeholder="Password" minlength="6">
      <button type="submit" class="signin-enter">Sign in</button>
      <p class="signin-links">
        <button type="button" class="signin-link" data-to="create">New here? Create an account</button>
        <button type="button" class="signin-link" data-to="signin">Have an account? Sign in</button>
        <button type="button" class="signin-link" data-act="reset">Forgot password?</button>
        <button type="button" class="signin-link" data-to="email">Just enter with my email</button>
      </p>
    </form>` : ''}
    <p class="signin-msg" role="status" aria-live="polite"></p>
    <p class="signin-note">We keep your email so we know who has visited.</p>`;
  el.querySelector('.signin-eyebrow b').textContent = year ? String(year) : '';
  const q = sel => el.querySelector(sel);
  if (manual) q('.signin-manual').textContent = manualLabel(providers);
  return {
    el,
    google: q('.signin-google'),
    microsoft: q('.signin-microsoft'),
    manual: q('.signin-manual'),
    form: q('.signin-email'),
    input: q('#signin-email-input'),
    password: q('#signin-password-input'),
    enter: q('.signin-enter'),
    links: [...el.querySelectorAll('.signin-link')],
    msg: q('.signin-msg'),
  };
}

const ENTER_WORDS = { signin: 'Sign in', create: 'Create account', email: 'Enter' };

/**
 * Show the panel and resolve once the visitor is in. Each handler resolves to true (go
 * in), to a string (say it, stay on the panel), or throws an Error whose message is shown.
 *   handlers.google(), handlers.microsoft(), handlers.password(email, password, create),
 *   handlers.reset(email), handlers.email(email)
 */
function askVisitor({ gate, year, providers, handlers, storage }) {
  const doc = gate.ownerDocument;
  const card = gate.querySelector('.gate-card') || gate;
  const parts = buildPanel(doc, { year, providers });
  const title = card.querySelector('#gate-title');
  if (title?.nextSibling) card.insertBefore(parts.el, title.nextSibling); else card.appendChild(parts.el);
  if (parts.input) parts.input.value = read(storage, EMAIL_KEY);
  gate.dataset.signin = 'open';
  // The manual form's mode: sign in or create with a password, or the email alone.
  let mode = providers.includes('password') ? 'signin' : 'email';
  const paintMode = () => {
    if (!parts.form) return;
    parts.form.dataset.mode = mode;
    parts.password.hidden = mode === 'email';
    parts.password.autocomplete = mode === 'create' ? 'new-password' : 'current-password';
    parts.enter.textContent = ENTER_WORDS[mode];
    for (const link of parts.links) {
      const to = link.dataset.to;
      const act = link.dataset.act;
      let show = false;
      if (to === 'create') show = mode === 'signin';
      else if (to === 'signin') show = mode !== 'signin' && providers.includes('password');
      else if (to === 'email') show = mode !== 'email' && providers.includes('email');
      else if (act === 'reset') show = mode === 'signin';
      link.hidden = !show;
    }
  };
  paintMode();
  return new Promise(resolve => {
    let busy = false;
    const buttons = () => [parts.google, parts.microsoft, parts.enter, ...parts.links].filter(Boolean);
    const setBusy = on => {
      busy = on;
      for (const b of buttons()) b.disabled = on;
      parts.el.toggleAttribute('aria-busy', on);
    };
    const say = (text, ok = false) => {
      parts.msg.textContent = text || '';
      parts.msg.classList.toggle('signin-msg-ok', !!ok);
    };
    const done = how => {
      delete gate.dataset.signin;
      parts.el.remove();
      resolve(how);
    };
    const attempt = async (fn, how) => {
      if (busy) return;
      setBusy(true);
      say('');
      try {
        const result = await fn();
        if (result === true) { done(how); return; }
        if (typeof result === 'string') say(result, true);
      } catch (err) {
        say(err?.message || 'That did not work. Try again.');
      }
      setBusy(false);
    };
    parts.google?.addEventListener('click', () => attempt(handlers.google, 'google'));
    parts.microsoft?.addEventListener('click', () => attempt(handlers.microsoft, 'microsoft'));
    if (parts.form) {
      // The owner, 2026-11-13: "we really want them to auth through Google", so the email
      // ways wait behind a small grey link and open only when asked for.
      parts.manual.addEventListener('click', () => {
        parts.form.hidden = false;
        parts.manual.hidden = true;
        parts.manual.setAttribute('aria-expanded', 'true');
        try { parts.input.focus({ preventScroll: true }); } catch { /* old browser */ }
      });
      for (const link of parts.links) {
        link.addEventListener('click', () => {
          if (link.dataset.to) { mode = link.dataset.to; say(''); paintMode(); return; }
          const email = parts.input.value.trim();
          if (!validEmail(email)) { say('Type your email first, then tap Forgot password.'); parts.input.focus(); return; }
          void attempt(() => handlers.reset(email), 'reset');
        });
      }
      parts.form.addEventListener('submit', event => {
        event.preventDefault();
        const email = parts.input.value.trim();
        if (!validEmail(email)) { say('That email does not look right.'); parts.input.focus(); return; }
        if (mode === 'email') { void attempt(() => handlers.email(email), 'email'); return; }
        const password = parts.password.value;
        if (password.length < 6) { say('Use a password of at least 6 characters.'); parts.password.focus(); return; }
        void attempt(() => handlers.password(email, password, mode === 'create'), 'password');
      });
    }
    // Keys typed here are the visitor's, not the walker's.
    parts.el.addEventListener('keydown', event => event.stopPropagation());
    try { (parts.google || parts.microsoft || parts.manual)?.focus({ preventScroll: true }); } catch { /* old browser */ }
  });
}

/** What the visitor reads for each Firebase error code. */
export const AUTH_ERRORS = {
  'auth/popup-closed-by-user': 'Sign-in was closed. Try again, or use another way.',
  'auth/cancelled-popup-request': 'Sign-in was closed. Try again, or use another way.',
  'auth/user-cancelled': 'Sign-in was cancelled. Try again, or use another way.',
  'auth/network-request-failed': 'No connection just now. Try again in a moment.',
  'auth/account-exists-with-different-credential': 'That email has signed in here another way. Use the same way as last time.',
  'auth/operation-not-allowed': 'That way of signing in is not switched on yet. Use another way.',
  'auth/invalid-credential': 'That email and password do not match. Try again, or reset your password.',
  'auth/invalid-login-credentials': 'That email and password do not match. Try again, or reset your password.',
  'auth/wrong-password': 'That email and password do not match. Try again, or reset your password.',
  'auth/user-not-found': 'That email and password do not match. Try again, or create an account.',
  'auth/email-already-in-use': 'That email already has an account. Sign in instead.',
  'auth/weak-password': 'Use a password of at least 6 characters.',
  'auth/invalid-email': 'That email does not look right.',
  'auth/too-many-requests': 'Too many tries. Wait a minute, or reset your password.',
};
const said = (err, fallback) => new Error(AUTH_ERRORS[err?.code] || fallback);

/**
 * The gate. Resolves `{ how }` once the visitor may enter: 'off', 'robot', 'preview',
 * 'returning', 'google', 'microsoft', 'password', 'email' or 'fail-open'. Never rejects.
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
  const providers = offered(config);
  if (mode === 'preview') {
    const how = await askVisitor({ gate, year, storage, providers, handlers: {
      google: async () => true,
      microsoft: async () => true,
      password: async email => { write(storage, EMAIL_KEY, email); return true; },
      reset: async () => 'If that email has an account, a reset link is on its way.',
      email: async email => { write(storage, EMAIL_KEY, email); return true; },
    } });
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
      const name = user.displayName || user.providerData?.[0]?.displayName || '';
      const known = user.email || user.providerData?.find(p => p.email)?.email || '';
      void user.getIdToken().then(idToken => recordEntry({
        projectId: config.firebase.projectId, idToken,
        uid: user.uid, email: email || known, name,
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

  // Google and Microsoft: a popup, or the whole page to the provider and back when the
  // browser blocks the popup (the next boot then passes as 'returning').
  const popup = async (provider, who) => {
    try {
      await authMod.signInWithPopup(auth, provider);
      return true;
    } catch (err) {
      const code = err?.code || '';
      if (code === 'auth/popup-blocked' || code === 'auth/operation-not-supported-in-this-environment') {
        await authMod.signInWithRedirect(auth, provider);
        return false;
      }
      console.warn(`[4D Chicago] sign-in: ${who}`, code, err);
      throw said(err, `${who} sign-in did not work here. Try another way.`);
    }
  };

  let typed = '';
  const logLogin = method => void fb.analytics?.then(an => an && an.mod.logEvent(an.a, 'login', { method })).catch(() => {});
  const how = await askVisitor({
    gate, year, storage, providers, handlers: {
      google: () => {
        const provider = new authMod.GoogleAuthProvider();
        provider.setCustomParameters({ prompt: 'select_account' });
        return popup(provider, 'Google');
      },
      microsoft: () => {
        const provider = new authMod.OAuthProvider('microsoft.com');
        provider.setCustomParameters({ prompt: 'select_account' });
        return popup(provider, 'Microsoft');
      },
      password: async (email, password, create) => {
        write(storage, EMAIL_KEY, email);
        try {
          if (create) await authMod.createUserWithEmailAndPassword(auth, email, password);
          else await authMod.signInWithEmailAndPassword(auth, email, password);
          return true;
        } catch (err) {
          console.warn('[4D Chicago] sign-in: password', err?.code, err);
          throw said(err, 'That did not work. Try again, or use another way.');
        }
      },
      reset: async email => {
        try { await authMod.sendPasswordResetEmail(auth, email); } catch (err) {
          if (err?.code === 'auth/invalid-email' || err?.code === 'auth/too-many-requests') throw said(err, '');
          // Anything else: say the same as success, so the panel never tells who has an account.
        }
        return 'If that email has an account, a reset link is on its way.';
      },
      email: async email => {
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
