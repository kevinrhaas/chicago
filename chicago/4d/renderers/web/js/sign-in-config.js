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
  enabled: false,
  hosts: ['chicago.polecat.live'],
  firebase: {
    apiKey: '',
    authDomain: '',
    projectId: '',
    appId: '',
    // Optional: Google Analytics for the usage numbers. Empty skips Analytics.
    measurementId: '',
  },
};
