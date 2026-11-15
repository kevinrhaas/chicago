/**
 * T-3601: the Today window's Google Maps key.
 *
 * The Today window shows Google Street View, today, from where you stand and the way
 * you face. It needs a Maps JavaScript API key from the owner's Google Cloud project
 * (APIs & Services → Credentials → Create credentials → API key, with the Maps
 * JavaScript API enabled). A Maps browser key is public by design, like the Firebase
 * config in sign-in-config.js: what protects it is its restriction to the `hosts`
 * below (Application restrictions → Websites) and a daily quota cap on the API.
 *
 * With `googleMapsKey` empty the window still opens: it names today's spot and the way
 * you face, and links to Google Maps' own Street View there (no key, no cost). Not one
 * byte from Google is fetched until a visitor opens the window.
 *
 * `hosts` is where the key is used. Anywhere else (a local serve, the smoke, a tool's
 * page) the window keeps to the link, so a test never spends the owner's quota. For a
 * local trial, `localStorage['chicago4d.todayKey']` names a key for that browser only.
 */
export const TODAY_VIEW = {
  googleMapsKey: '',
  hosts: ['chicago.polecat.live', 'dev.chicago.polecat.live'],
};
