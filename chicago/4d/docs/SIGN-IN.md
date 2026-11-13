# Sign-in before a year (T-3576)

The owner, 2026-11-13: Google sign-in "when you hit one of the time zone years before
hitting the download", or an email for anyone without a Google account, unverified for
now, with no server; one sign-in for every year; and a list of everyone who has come in,
with some usage numbers.

## How it works

- **Where.** `boot()` in `renderers/web/js/main.js` awaits `signInGate()`
  (`js/sign-in.js`) before the scene is fetched. Every way into a year runs `boot()` —
  the Observatory's cards, the `/1812/` `/1835/` `/1904/` doors and `?year=` links — so
  the one gate stands in front of all of them. The panel takes the arrival device's
  place (`css/signin.css`), in every Appearance, at phone and desktop widths.
- **The ways in** (T-3580; `providers` in `js/sign-in-config.js`, each also switched on
  in the console): **Continue with Google** first, then **Continue with Microsoft**, both
  Firebase popups (a blocked popup falls back to a redirect). Behind a small grey link,
  "No Google or Microsoft account? Sign in with email" (the owner: Google is the way in),
  sits an **email and password** form (sign in, create an account, forgot password) and
  **Just enter with my email**: Firebase anonymous sign-in plus the typed address, not
  verified. The upgrade to verified email-only is Firebase's email-link sign-in.
- **Once.** Firebase keeps the sign-in in the browser for the whole site, so the next
  year and the next visit pass straight through. An email visitor's address is kept in
  `localStorage` (`chicago4d.signin.email`) beside it.
- **The list.** Each entry into a year writes, over Firestore REST
  (`js/visitor-store.js`), `visitors/<uid>` (email, name, method, first and last seen,
  years entered, a count) and one `visits/<id>` row (who, year, device, time). The
  owner reads them at **`/4d/walk/visitors.html`** (sign in with his Google account),
  which also counts entries by year, device and day, and downloads a CSV.
- **Usage.** With `measurementId` set, Firebase Analytics (Google Analytics 4) logs a
  `login` event and an `enter_year` event (year, method, device) beside its own page
  views, sessions, engagement time, countries and devices. No email goes to Analytics.
- **Never a lockout.** Off unless `js/sign-in-config.js` has `enabled: true`, all four
  Firebase values, and the page's host in `hosts`; off under automation
  (`navigator.webdriver`: the smoke, photo-match, films); and if Firebase cannot load
  or answer, the visitor goes in. It is a front door, not a lock: the town's files are
  public on a static host, and the panel says why the email is asked for.
- **Preview.** `?signin=preview` shows the panel with no Firebase at all;
  `visitors.html?demo` draws the visitors page from invented example.com rows.

## Setting up the Firebase project (the owner, once)

1. <https://console.firebase.google.com> → **Create a project** (e.g. `chicago-4d`).
   Leave Google Analytics **on** and pick or create an Analytics account.
2. **Build → Authentication → Get started → Sign-in method**: enable **Google** (pick
   the support email), **Email/Password** (leave "Email link" off until verified
   email-only is built), **Anonymous**, and **Microsoft** (below).
3. **Authentication → Settings → Authorized domains → Add domain**:
   `chicago.polecat.live`.
4. **Build → Firestore Database → Create database**: production mode, location
   `nam5 (us-central)`. Then the **Rules** tab: paste the rules below, put the owner's
   Google address where it says `OWNER_EMAIL`, and **Publish**.
5. **Project settings (gear) → General → Your apps → Web (`</>`)**: register an app
   (nickname `4D Chicago`, no Hosting). Copy `apiKey`, `authDomain`, `projectId`,
   `appId` and `measurementId` from the config it shows into
   `renderers/web/js/sign-in-config.js` and set `enabled: true`. The web config is
   public by design; the rules are what protect the list.

All of it is on Firebase's free Spark plan; nothing needs a card.

### Microsoft

1. Firebase → Authentication → Sign-in method → Add new provider → **Microsoft**; copy the
   callback URL it shows (`https://<project>.firebaseapp.com/__/auth/handler`).
2. **portal.azure.com** (any Microsoft account; a free Azure account if asked) → **App
   registrations → New registration**: name `4D Chicago`; supported account types
   **any organizational directory and personal Microsoft accounts**; redirect URI
   **Web** = the callback URL → Register.
3. Copy the **Application (client) ID** from Overview.
4. **Certificates & secrets → New client secret** (24 months) → copy its **Value**.
5. Paste both into Firebase's Microsoft dialog, enable, Save. The secret expires in 24
   months; renew it before then or Microsoft sign-in stops. A school's IT may block its
   students from consenting to an unverified app; personal accounts always work.

## Firestore rules

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    function isOwner() {
      return request.auth != null
        && request.auth.token.email == 'OWNER_EMAIL'
        && request.auth.token.email_verified == true;
    }
    function visitorFields() {
      return request.resource.data.keys().hasOnly(['email', 'name', 'method', 'firstSeen', 'firstYear', 'lastSeen', 'lastYear', 'lastDevice', 'visits', 'years'])
        && request.resource.data.email is string && request.resource.data.email.size() <= 254
        && request.resource.data.name is string && request.resource.data.name.size() <= 200;
    }
    match /visitors/{uid} {
      allow read, delete: if isOwner();
      allow create, update: if request.auth != null && request.auth.uid == uid && visitorFields();
    }
    match /visits/{id} {
      allow read, delete: if isOwner();
      allow create: if request.auth != null
        && request.resource.data.uid == request.auth.uid
        && request.resource.data.keys().hasOnly(['uid', 'email', 'method', 'year', 'device', 'at'])
        && request.resource.data.email is string && request.resource.data.email.size() <= 254;
    }
  }
}
```

`tools/test_sign_in.mjs` holds the fields `visitor-store.js` writes to the two
`hasOnly` lists above, so a new field cannot ship without its rule.

## Not done (yet)

- **A ping per sign-in.** Firestore cannot send mail by itself; a message per new
  visitor needs a Cloud Function (the Blaze plan) or a scheduled job holding a service
  account key. The visitors page and Analytics' realtime view answer "who came in".
- **Verified email**, by Firebase's email-link sign-in.
- **A sign-out control in the app.** The visitors page has one.
