// chicago-4d-dev-redirect.mjs: point the old /4d/dev/ preview at its own site.
//
//   node .github/chicago-4d-dev-redirect.mjs [site]
//
// Since 2026-11-13 the dev preview is a separate GitHub Pages site,
// https://dev.chicago.polecat.live/4d/dev/, deployed by kevinrhaas/chicago-dev. It
// used to be folded into this site's artifact, and production plus the preview plus
// the landing films and older viewers had reached GitHub's 1 GB per site.
//
// Old links (tickets, evidence, bookmarks, the home-screen app) still point at
// chicago.polecat.live/4d/dev/…. GitHub Pages has no server redirects, so this
// writes small pages that send the visitor on with the rest of the path, query and
// hash kept:
//
//   site/4d/dev/index.html          /4d/dev/
//   site/4d/dev/<door>/index.html   /4d/dev/1835/ and the other front doors
//   site/4d/dev/walk/index.html     /4d/dev/walk/
//   site/404.html                   any other /4d/dev/… path (only when the site has
//                                   no 404 page of its own); other misses get a plain
//                                   not-found page
//   site/4d/dev/sw.js               a service worker that unregisters itself, so a
//                                   phone that installed the old preview stops serving
//                                   it from its cache
import { mkdir, readdir, writeFile, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';

export const TARGET = 'https://dev.chicago.polecat.live';
export const MARKER = 'data-c4d-dev-moved';

const script = `(function(){var l=location;if(!/^\\/4d\\/dev(\\/|$)/.test(l.pathname))return;`
  + `l.replace(${JSON.stringify(TARGET)}+l.pathname+l.search+l.hash)})();`;

export function redirectPage(path) {
  return `<!doctype html>
<html lang="en" ${MARKER}>
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex,nofollow">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The dev preview has moved</title>
<script>${script}</script>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:32rem;margin:15vh auto;padding:0 16px;color:#e8e6df;background:#14161a}a{color:#7dd3fc}</style>
</head>
<body>
<p>The 4D Chicago dev preview has moved to its own address:</p>
<p><a href="${TARGET}${path}">${TARGET.replace('https://', '')}${path}</a></p>
<p>Production is still at <a href="/4d/">chicago.polecat.live/4d/</a>.</p>
</body>
</html>
`;
}

export const notFoundPage = `<!doctype html>
<html lang="en" ${MARKER}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Not found</title>
<script>${script}</script>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:32rem;margin:15vh auto;padding:0 16px;color:#e8e6df;background:#14161a}a{color:#7dd3fc}</style>
</head>
<body>
<p>There is no page at this address.</p>
<p><a href="/">chicago.polecat.live</a> · <a href="/4d/">4D Chicago</a></p>
</body>
</html>
`;

export const retiringWorker = `// The dev preview moved to ${TARGET}/4d/dev/ (2026-11-13).
// A browser that installed the old preview's service worker here checks this file
// for updates; this version clears that worker's caches and unregisters it.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) await caches.delete(key);
    await self.registration.unregister();
    for (const client of await self.clients.matchAll({ type: 'window' })) client.navigate(client.url);
  })());
});
`;

export async function writeRedirects(site = 'site') {
  const app = join(site, '4d');
  const out = join(app, 'dev');
  // The front doors are the numeric year directories publish.sh writes (1812, 1835,
  // 1880, 1904); walk/ is the app page itself.
  const doors = existsSync(app)
    ? (await readdir(app)).filter(name => /^\d{4}$/.test(name)) : [];
  const written = [];
  for (const rel of ['', ...doors, 'walk']) {
    const dir = rel ? join(out, rel) : out;
    await mkdir(dir, { recursive: true });
    await writeFile(join(dir, 'index.html'), redirectPage(`/4d/dev/${rel ? `${rel}/` : ''}`));
    written.push(`/4d/dev/${rel ? `${rel}/` : ''}`);
  }
  await writeFile(join(out, 'sw.js'), retiringWorker);
  const notFound = join(site, '404.html');
  if (!existsSync(notFound)) {
    await writeFile(notFound, notFoundPage);
    written.push('/404.html');
  }
  return written;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const site = process.argv[2] || 'site';
  if (!existsSync(site) || !(await stat(site)).isDirectory()) {
    console.error(`usage: node .github/chicago-4d-dev-redirect.mjs [site]: ${site} is not a directory`);
    process.exit(2);
  }
  const written = await writeRedirects(site);
  console.log(`dev-redirect: ${written.length} page(s) point at ${TARGET}: ${written.join(' ')}`);
}
