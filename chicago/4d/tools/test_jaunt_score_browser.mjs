// T-3710: the jaunts' score in a real browser, with real decoding. The 1812 playlist plays,
// a jaunt starts and its opening takes over through the fader, a bed loops past its end
// without stopping, a stop's own cue (the battle's march) takes over, a closing cue plays to
// its end even after the jaunt is over, and then the playlist returns: one media element and
// nonzero audio throughout, no page errors.
//   PW_EXECUTABLE=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome node tools/test_jaunt_score_browser.mjs [--hosted]
// Without --hosted the deliveries come from renderers/web/audio/; with it, from the verified R2 host.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const hosted = process.argv.includes('--hosted');
const catalog = JSON.parse(await fs.readFile(path.join(root, 'renderers/web/audio/catalog.json'), 'utf8'));
const policy = JSON.parse(await fs.readFile(path.join(root, 'tools/audio-hosting.json'), 'utf8'));
if (hosted) for (const a of catalog.assets.filter(a => a.kind === 'music')) for (const k of ['opus', 'aac'])
  a[k] = new URL(`media/${a.delivery[k].sha256}${path.extname(a[k])}`, policy.public_base).href;
let pw; try { pw = await import('playwright'); } catch { pw = await import(path.join(process.env.NODE_PATH, 'playwright/index.mjs')); }
const fixture = `<!doctype html><button id="on">Sound on</button><script type="module">
import {createRecordedAudio} from '/js/recorded-audio.js';
const catalog=${JSON.stringify(catalog)};
window.players=[];window.jaunt=null;
window.sync=()=>engine.sync({active:true,ambienceOn:false,musicOn:true,musicLevel:1,year:'1812',jaunt});
window.peak=()=>{const a=new Float32Array(meter.fftSize);meter.getFloatTimeDomainData(a);return Math.max(...a.map(Math.abs));};
document.getElementById('on').onclick=()=>{
 window.ctx=new AudioContext();ctx.resume();const music=ctx.createGain();window.meter=ctx.createAnalyser();music.connect(meter);meter.connect(ctx.destination);
 window.engine=createRecordedAudio({ctx,ambience:ctx.createGain(),music,base:new URL('/audio/',location.href),
  media:()=>{const a=new Audio();players.push(a);window.player=a;return a;},
  fetcher:(url,opts)=>String(url).endsWith('catalog.json')?Promise.resolve({ok:true,json:async()=>catalog}):fetch(url,opts)});
 sync();setInterval(sync,250);
};
</script>`;
const p = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.https_proxy || process.env.http_proxy;
const u = p ? new URL(p) : null, proxy = u ? { server: u.origin, ...(u.username ? { username: decodeURIComponent(u.username), password: decodeURIComponent(u.password) } : {}) } : undefined;
const browser = await pw.chromium.launch({ proxy, executablePath: process.env.PW_EXECUTABLE ?? '/usr/bin/chromium', headless: true, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
const types = { '.js': 'text/javascript', '.ogg': 'audio/ogg', '.m4a': 'audio/mp4' };
try {
  for (const width of [390, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: width === 390 ? 780 : 800 } }), errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.route(policy.origin + '/**', async route => {
      const name = new URL(route.request().url()).pathname;
      if (name === '/fixture') return route.fulfill({ contentType: 'text/html', body: fixture });
      const file = name.startsWith('/js/') ? path.join(root, 'renderers/web', name) : name.startsWith('/audio/') ? path.join(root, 'renderers/web', name) : null;
      if (!file || file.includes('..')) return route.fulfill({ status: 404 });
      let body; try { body = await fs.readFile(file); } catch { return route.fulfill({ status: 404 }); }
      const headers = { 'Access-Control-Allow-Origin': '*', 'Accept-Ranges': 'bytes' }, contentType = types[path.extname(file)] ?? 'application/octet-stream';
      // Byte ranges as R2 serves them, so the element knows each cue's length and can seek.
      const range = /bytes=(\d+)-(\d*)/.exec(route.request().headers().range ?? '');
      if (!range) return route.fulfill({ contentType, body, headers });
      const start = +range[1], end = range[2] ? Math.min(+range[2], body.length - 1) : body.length - 1;
      return route.fulfill({ status: 206, contentType, body: body.subarray(start, end + 1), headers: { ...headers, 'Content-Range': `bytes ${start}-${end}/${body.length}` } });
    });
    await page.goto(policy.origin + '/fixture'); await page.click('#on');
    const hear = (test, label) => page.waitForFunction(test, null, { timeout: 45000, polling: 100 }).catch(e => { throw Error(`${width}px: ${label}: ${e.message}`); });
    const sounding = '!player.paused&&player.currentTime>0&&peak()>1e-6';
    await hear(`engine.state.track?.includes('Frontier')&&${sounding}`, 'the 1812 playlist');
    await page.evaluate(() => { jaunt = { id: 'battle-of-fort-dearborn', phase: 'opening', stop: 'the-fort', session: 1 }; });
    await hear(`engine.state.score==='score-battle-1-buildup'&&${sounding}`, 'the battle opens on its build');
    await page.evaluate(() => { jaunt = { ...jaunt, phase: 'atStop' }; player.currentTime = player.duration - .5; });
    await page.waitForTimeout(1500);
    assert.equal(await page.evaluate(() => engine.state.score), 'score-battle-1-buildup');
    assert.ok(await page.evaluate(() => !player.paused && player.currentTime < 5 && peak() > 1e-6), 'a bed loops past its end without stopping');
    await page.evaluate(() => { jaunt = { ...jaunt, phase: 'travelling', stop: 'river-mouth' }; });
    await hear(`engine.state.score==='score-battle-2-march'&&${sounding}`, 'setting out for the river mouth takes up the march');
    await page.evaluate(() => { jaunt = { ...jaunt, phase: 'closing', stop: 'ouilmette' }; });
    await hear(`engine.state.score==='score-theme-remembrance'&&${sounding}`, 'the closing cue');
    await page.evaluate(() => { jaunt = null; player.currentTime = player.duration - 2; });
    await page.waitForTimeout(600);
    assert.equal(await page.evaluate(() => engine.state.score), 'score-theme-remembrance', 'the closing plays on after the jaunt ends');
    await hear(`engine.state.track?.includes('Frontier')&&engine.state.score===null&&${sounding}`, 'then the playlist returns');
    assert.equal(await page.evaluate(() => players.length), 1, 'one gesture-unlocked element throughout');
    assert.deepEqual(await page.evaluate(() => engine.state.errors), []); assert.deepEqual(errors, []);
    console.log(`JAUNT SCORE BROWSER PASS ${width}px (${hosted ? 'R2' : 'local'}): playlist, opening, a looping bed, a stop's cue, an uncut closing, the playlist back; one element, nonzero audio`);
    await page.close();
  }
} finally { await browser.close(); }
