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
 * `hosts` is where the gate runs. Anywhere else (a local serve, the smoke, a tool's
 * Playwright page) it stays off, so the gate never blocks a test or a film.
 */
export const SIGN_IN = {
  enabled: true,
  hosts: ['chicago.polecat.live'],
  // The ways in, each switched on in the Firebase console too (Authentication → Sign-in
  // method): 'google' and 'microsoft' are the big buttons; 'password' (email and password)
  // and 'email' (the email alone, Firebase's Anonymous provider) wait behind the grey link.
  providers: ['google', 'microsoft', 'password', 'email'],
  firebase: {
    apiKey: 'AIzaSyBxCJiD-E2s72C5WV8J101WtjCqDxGztDw',
    authDomain: 'chicago-61643.firebaseapp.com',
    projectId: 'chicago-61643',
    appId: '1:317737441172:web:8c54d8aaa876cdd424e181',
    // Optional: Google Analytics for the usage numbers. Empty skips Analytics.
    measurementId: 'G-L7XSC6H69J',
  },
};
