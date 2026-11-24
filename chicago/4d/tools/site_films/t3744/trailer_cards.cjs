// Render the trailer's title cards as transparent 1920x1080 PNGs in the site's own type.
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright');
const F = 'http://127.0.0.1:8765/site/fonts/';
const css = `
@font-face{font-family:D;font-weight:300;src:url(${F}barlow-semi-condensed-300.woff2)}
@font-face{font-family:D;font-weight:500;src:url(${F}barlow-semi-condensed-500.woff2)}
@font-face{font-family:S;src:url(${F}instrument-serif-400.woff2)}
@font-face{font-family:M;src:url(${F}ibm-plex-mono-400.woff2)}
html,body{margin:0;width:1920px;height:1080px;background:transparent;color:#F2EDE3;overflow:hidden}
.c{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.big{font:300 112px/1 D;letter-spacing:-.02em}
.big em{font:400 1.05em/1 S;font-style:italic;color:#8CF5A8}
.mid{font:300 84px/1.08 D;letter-spacing:-.015em;max-width:1500px}
.mid em{font:400 1.06em/1 S;font-style:italic;color:#8CF5A8}
.k{font:400 26px/1 M;letter-spacing:.34em;text-transform:uppercase;color:#C9C3B6;margin-top:34px}
.lt{position:absolute;left:150px;bottom:130px;text-align:left}
.lt .y{font:300 150px/.9 D;letter-spacing:-.03em;text-shadow:0 4px 40px rgba(0,0,0,.55)}
.lt .p{font:400 26px/1 M;letter-spacing:.34em;text-transform:uppercase;color:#E8E2D4;margin-top:18px;text-shadow:0 2px 16px rgba(0,0,0,.7)}
.lt .p i{display:inline-block;width:12px;height:12px;border-radius:50%;background:#8CF5A8;margin-right:16px;vertical-align:2px}
.logo{font:500 64px/1 D;letter-spacing:.32em}
.logo b{color:#8CF5A8;font-weight:500;margin-left:.2em}
.rule{width:120px;height:2px;background:#8CF5A8;margin:40px auto}
`;
const cards = {
  'c-open': `<div class=c><div class=mid>Four moments in <em>Chicago's life.</em></div></div>`,
  'y-1812': `<div class=lt><div class=y>1812</div><div class=p><i></i>Fort Dearborn</div></div>`,
  'y-1835': `<div class=lt><div class=y>1835</div><div class=p><i></i>The river town</div></div>`,
  'y-1871': `<div class=lt><div class=y>1871</div><div class=p><i></i>Before the fire</div></div>`,
  'y-1904': `<div class=lt><div class=y>1904</div><div class=p><i></i>Prairie Avenue</div></div>`,
  'c-record': `<div class=c><div class=mid>Rebuilt from maps, censuses,<br><em>photographs and newspapers.</em></div></div>`,
  'c-people': `<div class=c><div class=mid>The people <em>the records name.</em></div></div>`,
  'c-meet': `<div class=lt><div class=p><i></i>Walk up. Say hello. Ask for a story.</div></div>`,
  'c-saw': `<div class=c><div class=mid>Stand where <em>they stood.</em></div></div>`,
  'c-title': `<div class=c><div class=big>Walk into <em>Chicago's past.</em></div><div class=rule></div><div class=logo>CHICAGO<b>4D</b></div><div class=k>1812 · 1835 · 1871 · 1904</div><div class=k style="margin-top:22px;color:#8CF5A8">chicago.polecat.live</div></div>`,
};
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  for (const [id, html] of Object.entries(cards)) {
    await p.goto('http://127.0.0.1:8765/site/contact/'); await p.evaluate(([c,h]) => { document.head.innerHTML = '<style>'+c+'</style>'; document.body.className=''; document.body.innerHTML = h; document.documentElement.style.background='transparent'; document.body.style.background='transparent'; }, [css, html]); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(200);
    await p.screenshot({ path: id + '.png', omitBackground: true });
  }
  await b.close();
})();
