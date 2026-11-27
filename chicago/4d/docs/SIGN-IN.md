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
  Firebase values, and the page's host in `hosts` (`chicago.polecat.live` and the dev
  preview's `dev.chicago.polecat.live`); off under automation
  (`navigator.webdriver`: the smoke, photo-match, films); and if Firebase cannot load
  or answer, the visitor goes in. It is a front door, not a lock: the town's files are
  public on a static host, and the panel says why the email is asked for.
- **Sign out.** Settings → About shows "Signed in as …" with a **Sign out** button
  (T-3603, `showAccount` in `js/sign-in.js`). It ends the Firebase session, forgets the
  typed email and reloads, so the gate asks again. The visitors page has its own.
- **Crash reports and Report a bug** (T-3743, `js/bug-report.js`). A small bug key at the
  upper right (Settings › Show › On screen turns it off) opens a sheet: a picture of the
  town, the visitor's words, and the device, graphics, memory, year, settings, place and
  recent errors, saved as `bugs/<id>` under their uid. A page the device killed is filed by
  the next load from its black box (`crash`), a display reset at once (`context`), an
  uncaught error once per message (`error`). Bugs, crashes and resets are also emailed to
  the owner through FormSubmit (automatic ones at most three a device a day). Each row says
  `live`, `dev` or `local`: one Firebase project serves both sites (the owner, 2026-11-24).
  Nothing is sent from any other host or under automation. The owner reads them on
  `visitors.html`, and an email's link opens its report there (`?bug=<id>`).
- **Preview.** `?signin=preview` shows the panel with no Firebase at all;
  `visitors.html?demo` draws the visitors page from invented example.com rows.

## Setting up the Firebase project (the owner, once)

1. <https://console.firebase.google.com> → **Create a project** (e.g. `chicago-4d`).
   Leave Google Analytics **on** and pick or create an Analytics account.
2. **Build → Authentication → Get started → Sign-in method**: enable **Google** (pick
   the support email), **Email/Password** (leave "Email link" off until verified
   email-only is built), **Anonymous**, and **Microsoft** (below).
3. **Authentication → Settings → Authorized domains → Add domain**:
   `chicago.polecat.live` and `dev.chicago.polecat.live` (the dev preview).
4. **Build → Firestore Database → Create database**: production mode, location
   `nam5 (us-central)`. Then the **Rules** tab: paste the rules below, put the owner's
   Google address where it says `OWNER_EMAIL`, and **Publish**. Since T-3776 a change to
   the rules below is published by the workflow `chicago-4d-firestore-rules.yml` when it
   reaches dev (`tools/publish_firestore_rules.mjs`, with the repository secret
   `FIREBASE_SERVICE_ACCOUNT`); it carries the live owner address across, so the console
   paste is only needed for a brand-new project.
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
    function bugFields(d) {
      return d.keys().hasOnly(['uid', 'email', 'kind', 'comment', 'year', 'site', 'build', 'device', 'gpu', 'place', 'link', 'page', 'env', 'errors', 'steps', 'shot', 'at'])
        && ((request.auth == null && d.uid == '') || (request.auth != null && d.uid == request.auth.uid))
        && d.kind in ['bug', 'crash', 'context', 'error']
        && d.uid is string && d.uid.size() <= 128
        && d.email is string && d.email.size() <= 254
        && d.kind is string && d.kind.size() <= 10
        && d.comment is string && d.comment.size() <= 4000
        && d.year is string && d.year.size() <= 10
        && d.site is string && d.site.size() <= 10
        && d.build is string && d.build.size() <= 80
        && d.device is string && d.device.size() <= 160
        && d.gpu is string && d.gpu.size() <= 200
        && d.place is string && d.place.size() <= 200
        && d.link is string && d.link.size() <= 600
        && d.page is string && d.page.size() <= 300
        && d.env is string && d.env.size() <= 20000
        && d.errors is string && d.errors.size() <= 8000
        && d.steps is string && d.steps.size() <= 20000
        && d.shot is string && d.shot.size() <= 900000
        && d.at is timestamp;
    }
    // T-3776: the visitor reads and deletes their own row too (Settings › About › Delete my
    // saved data, js/student-data.js); every collection that holds a visitor's data lets them.
    function isSelf(uid) {
      return request.auth != null && request.auth.uid == uid;
    }
    match /visitors/{uid} {
      allow read, delete: if isOwner() || isSelf(uid);
      allow create, update: if request.auth != null && request.auth.uid == uid && visitorFields();
    }
    // T-3645: the reader's ages (Settings › Display › Reading age), read and written by
    // the reader alone, so another device opens at the same age.
    match /readers/{uid} {
      allow read, delete: if request.auth != null && request.auth.uid == uid;
      allow create, update: if request.auth != null && request.auth.uid == uid
        && request.resource.data.keys().hasOnly(['ages', 'at'])
        && request.resource.data.ages is list && request.resource.data.ages.size() <= 5;
    }
    match /visits/{id} {
      allow read, delete: if isOwner() || isSelf(resource.data.uid);
      allow create: if request.auth != null
        && request.resource.data.uid == request.auth.uid
        && request.resource.data.keys().hasOnly(['uid', 'email', 'method', 'year', 'device', 'at'])
        && request.resource.data.email is string && request.resource.data.email.size() <= 254;
    }
    // T-3741: the public site's contact page (site/js/contact.js). Anyone may leave a
    // message, signed in or not; only the owner reads or deletes them (visitors.html).
    match /messages/{id} {
      allow read, delete: if isOwner();
      allow create: if request.resource.data.keys().hasOnly(['name', 'email', 'topic', 'message', 'page', 'at'])
        && request.resource.data.name is string && request.resource.data.name.size() > 0 && request.resource.data.name.size() <= 120
        && request.resource.data.email is string && request.resource.data.email.size() <= 200
        && request.resource.data.topic is string && request.resource.data.topic.size() <= 60
        && request.resource.data.message is string && request.resource.data.message.size() > 0 && request.resource.data.message.size() <= 5000
        && request.resource.data.page is string && request.resource.data.page.size() <= 200
        && request.resource.data.at is timestamp;
    }
    // T-3743: crash reports and Report a bug (renderers/web/js/bug-report.js). Anyone in the
    // app may file one under their own uid, or with none when sign-in let them in without
    // one; only the owner reads them all (visitors.html), and a visitor their own (T-3776).
    match /bugs/{id} {
      allow read, delete: if isOwner() || (resource.data.uid != '' && isSelf(resource.data.uid));
      allow create: if bugFields(request.resource.data);
    }
    // T-3644: the visitor's own person (renderers/web/js/visitor-person.js), theirs alone.
    match /people/{uid} {
      allow read, delete: if request.auth != null && request.auth.uid == uid;
      allow create, update: if request.auth != null && request.auth.uid == uid
        && request.resource.data.keys().hasOnly(['person', 'at'])
        && request.resource.data.person is string && request.resource.data.person.size() <= 4000;
    }
    // T-3777: cloud save (renderers/web/js/cloud-save.js): the field notebook, people met and
    // places found, and Settings, under the account's own uid and nobody else's, never from
    // a sign-in with the email alone. `at` is the server's own time.
    match /users/{uid}/{part}/{id} {
      allow read, delete: if isSelf(uid) && part in ['notebook', 'metfound', 'settings'];
      allow create, update: if isSelf(uid) && part in ['notebook', 'metfound', 'settings']
        && request.auth.token.firebase.sign_in_provider != 'anonymous'
        && request.resource.data.keys().hasOnly(['v', 'deleted', 'at'])
        && request.resource.data.v is string && request.resource.data.v.size() <= 800000
        && request.resource.data.deleted is bool
        && request.resource.data.at == request.time;
    }
  }
}
```

`tools/test_bug_report.mjs` holds the fields and lengths `bug-report.js` writes to the
`bugFields` rule above (T-3743). Until that rule is pasted, reports are refused and only the
email copy reaches the owner.

`tools/test_sign_in.mjs` holds the fields `visitor-store.js` writes to the two
`hasOnly` lists above, so a new field cannot ship without its rule; `tools/test_reading_level.mjs`
holds `readers/{uid}` to the fields `reading-level.js` writes (T-3645). Until the
`readers/{uid}` rule is pasted, a reader's ages stay on their device and the console says so once.

**Contact messages (T-3741)** are kept at `messages/<auto id>`: the public site's contact
form writes one per message, unauthenticated, before it asks FormSubmit to email the owner,
so a message survives FormSubmit failing. The owner reads them on the visitors page, newest
first. Until the rule above is pasted the write is refused, the page says the messages are
not readable yet, and the form still sends through FormSubmit (or offers the mailto).
`tools/test_sign_in.mjs` holds `site/js/contact.js`'s write to the `hasOnly` list.

**The visitor's own person (T-3644)** is kept at `people/<uid>`: the choice made on the
Settings card's You tab, as one JSON string, readable and writable by that visitor only.
Until the rule above is pasted into the console the writes are refused and the choice
stays on the device it was made on (the console says so once); nothing else changes.
`tools/test_visitor_person.mjs` holds `visitor-person.js`'s write to the `hasOnly` list.

## Not done (yet)

- **A ping per sign-in.** Firestore cannot send mail by itself; a message per new
  visitor needs a Cloud Function (the Blaze plan) or a scheduled job holding a service
  account key. The visitors page and Analytics' realtime view answer "who came in".
- **Verified email**, by Firebase's email-link sign-in.
