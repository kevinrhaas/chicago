/**
 * T-3576: the sign-in gate's switch and its Firebase project.
 *
 * The gate stays OFF until `enabled` is true AND the four Firebase values below are
 * filled in. With it off the app is exactly as before: no panel, and not one Firebase
 * byte is fetched (js/sign-in.js imports the SDK only when the gate is on).
 *
 * These values come from the Firebase console (Project settings → Your apps → Web app
 * → SDK setup and configuration → Config). A Firebase web config is public by design:
 * it names the project, it does not unlock it. What protects the visitor list is the
 * Firestore security rules in docs/SIGN-IN.md, which only the owner's Google account
 * can read through.
 *
 * `hosts` is where the gate runs: the site and its dev preview (served from
 * dev.chicago.polecat.live since 2026-11-13). Anywhere else (a local serve, the smoke, a
 * tool's Playwright page) it stays off, so the gate never blocks a test or a film. Each
 * host must also be on Firebase's Authentication → Settings → Authorized domains.
 */
export const SIGN_IN = {
  enabled: true,
  hosts: ['chicago.polecat.live', 'dev.chicago.polecat.live'],
  // The ways in, each switched on in the Firebase console too (Authentication → Sign-in
  // method): 'google' and 'microsoft' are the big buttons; 'password' (email and password)
  // and 'email' (the email alone, Firebase's Anonymous provider) wait behind the grey link.
  providers: ['google', 'microsoft', 'password', 'email'],
  // T-3776: the one switch for Stage 1's cloud features (cloud save, classes, shared routes,
  // follow the teacher; T-3777..T-3780). Every one checks cloudFeaturesOn() in
  // js/student-data.js before it writes. The owner switched it on, 2026-11-27 ("Turn on the
  // cloud features"); docs/STUDENT-DATA.md says what each feature keeps, and a school gets the
  // agreement (docs/STUDENT-DATA-AGREEMENT.md) before its classes use them.
  cloudFeatures: true,
  firebase: {
    apiKey: 'AIzaSyBxCJiD-E2s72C5WV8J101WtjCqDxGztDw',
    authDomain: 'chicago-61643.firebaseapp.com',
    projectId: 'chicago-61643',
    appId: '1:317737441172:web:8c54d8aaa876cdd424e181',
    // Optional: Google Analytics for the usage numbers. Empty skips Analytics.
    measurementId: 'G-L7XSC6H69J',
  },
};
