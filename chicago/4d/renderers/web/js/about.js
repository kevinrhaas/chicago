/**
 * Settings › About (T-2629, NAV-305; DESIGN §01 LOW finding and §386): which build this
 * is, and on a dev build the DEV mark the preview carries.
 *
 * On a phone the dev chrome stood on the town: the dev preview's banner and its DEV pill
 * (#__dev, #__devpill, which .github/chicago-4d-dev-preview.mjs injects into the dev tree
 * only) covered the HUD's top row, and the arrival card carried the build stamp
 * (#gate-build). On phones those are not drawn (walk.css, under the Navigator's phone
 * width), and this row says the same things where a visitor who wants them looks:
 * the build stamp everywhere (production's `build <sha> · <when>`, the preview's
 * `DEV PREVIEW · dev@<sha> · <when>`), and the DEV mark with "not production" and a way
 * to production on a dev build. A desktop keeps its banner, pill and stamp as they were.
 *
 * Painted when the Settings section opens, so it reads the page as it is then.
 */
import { t as str } from './strings/index.js';
import './strings/hud.js';

/** A dev build: the preview's own pill is on the page, or the page is served from /4d/dev/. */
export function isDevBuild(doc = globalThis.document, loc = globalThis.location) {
  if (doc?.getElementById?.('__devpill') || doc?.getElementById?.('__dev')) return true;
  return /\/4d\/dev\//.test(loc?.pathname ?? '');
}

/** The build stamp the page was published with, or `build <version>` before publish. */
export function buildStamp(doc = globalThis.document, version = '') {
  const text = doc?.getElementById?.('gate-build')?.textContent?.trim() ?? '';
  return text || (version ? `build ${version}` : str('hud.about.unpublished'));
}

/** Fill #s-about from the page. Returns what it showed. */
export function paintAbout({ doc = globalThis.document, loc = globalThis.location, version = '' } = {}) {
  const build = doc?.getElementById?.('s-about-build');
  if (!build) return null;
  const dev = isDevBuild(doc, loc);
  build.textContent = buildStamp(doc, version);
  const mark = doc.getElementById('s-about-dev');
  const note = doc.getElementById('s-about-dev-note');
  if (mark) mark.hidden = !dev;
  if (note) note.hidden = !dev;
  return { dev, build: build.textContent };
}
