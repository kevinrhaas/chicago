// SPDX-License-Identifier: GPL-3.0-or-later
// Run from any cwd; project root derives from this installed file.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {chromium} = require('playwright');
const project = path.resolve(__dirname, '../..');
const output = process.argv[2];
const clipName=process.argv[3]||'walk';
if(!['idle','walk','trot'].includes(clipName))throw Error('Unsupported clip');
if (!output) throw Error('Usage: node tools/transport/measure_head_fit.cjs RECEIPT.json [idle|walk|trot]');
const server = http.createServer((request, response) => {
  const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
  const file = path.resolve(project, '.' + pathname);
  if (!file.startsWith(project + path.sep)) { response.writeHead(403); response.end(); return; }
  fs.readFile(file, (error, bytes) => {
    if (error) { response.writeHead(404); response.end(); return; }
    response.setHeader('Content-Type', file.endsWith('.html') ? 'text/html' : file.endsWith('.js') ? 'text/javascript' : file.endsWith('.json') ? 'application/json' : 'application/octet-stream');
    response.end(bytes);
  });
});
(async () => {
  let browser;
  const errors = [];
  try {
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const launch = {headless:true, args:['--no-sandbox','--disable-dev-shm-usage']};
    if (process.env.PW_EXECUTABLE) launch.executablePath = process.env.PW_EXECUTABLE;
    browser = await chromium.launch(launch);
    const page = await browser.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => errors.push(request.url()));
    await page.goto(`http://127.0.0.1:${server.address().port}/tools/transport/head-fit/index.html?clip=${encodeURIComponent(clipName)}`);
    const receipt = await page.evaluate(() => window.measurement);
    receipt.browser_errors = errors;
    fs.writeFileSync(output, JSON.stringify(receipt, null, 2) + '\n');
    if (!receipt.passed || receipt.rows.length !== 21 || errors.length) throw Error('Head fit/boundary contract failed; preserve receipt');
    console.log(`PASS 21poses,5straps,564triangles; minimum ${Math.min(...receipt.rows.map(row=>row.triangle_distance.unsigned_minimum_m))}m; no containment/continuous-time claim`);
  } finally {
    await browser?.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
