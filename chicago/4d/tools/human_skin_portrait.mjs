#!/usr/bin/env node
// T-3400: portraits of a portable human with and without renderers/web/js/human-skin.js.
//   node tools/human_skin_portrait.mjs <out-dir> [asset] [query…]
// Serves chicago/4d on a loopback port, opens tools/human_skin_portrait.html (never
// published) and writes <asset>-before.png / <asset>-after.png. A page or shader error exits 1.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [out = '.', asset = 'anonymous_working_driver_1904', extra = ''] = process.argv.slice(2);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.glb': 'model/gltf-binary', '.wasm': 'application/wasm' };
const server = createServer(async (req, res) => {
  const file = path.join(root, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
  let body;
  try { body = await readFile(file); } catch { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'content-type': types[path.extname(file)] ?? 'application/octet-stream' }).end(body);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: Number(process.env.W ?? 900), height: Number(process.env.H ?? 900) } });
const errors = [];
page.on('pageerror', e => errors.push(String(e)));
page.on('console', m => { if (process.env.DEBUG) console.log('console:', m.type(), m.text().slice(0, 300)); if (m.type() === 'error' || /THREE\.WebGLProgram/.test(m.text())) errors.push(m.text()); });
for (const skin of ['0', '1']) {
  await page.goto(`http://127.0.0.1:${port}/tools/human_skin_portrait.html?asset=${asset}&skin=${skin}&${extra}`);
  await page.waitForFunction(() => window.ready, null, { timeout: 240000 }).catch(e => { console.error(errors.join('\n')); throw e; });
  const tag = (process.env.TAG ?? '') + (skin === '1' ? 'after' : 'before');
  await page.screenshot({ path: path.join(out, `${asset}-${tag}.png`) });
  console.log(skin, JSON.stringify(await page.evaluate(() => ({ ready: window.ready, dressed: window.dressed }))));
}
await browser.close(); server.close();
if (errors.length) { console.error(errors.join('\n')); process.exit(1); }
