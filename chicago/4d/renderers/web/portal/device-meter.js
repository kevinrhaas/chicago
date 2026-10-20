// T-2901: the front door's one real instrument. While the Wolf Point aperture opens, the
// machine reads THIS device with the same profile the town boots on (../js/device-profile.js:
// the WebGL2 renderer, cores, memory, texture size, WebGPU and a one-second fill + vertex
// benchmark), scores it 0-100 in five grades, and lights a segment bar that hovers around
// the score. The hover is not decoration: it dips when this page's own frames arrive late.
//
// The front door never writes the town's cached profile (storage: null), so a visit here
// cannot change what the town chooses; it measures afresh each load, during the cold start.
import { profileDevice, scoreProfile, CLASS_LABEL } from '../js/device-profile.js';

const meter = document.getElementById('device-meter');
if (meter) run(meter).catch(err => {
  meter.dataset.state = 'failed';
  meter.querySelector('.dm-read em').textContent = 'NO READING';
  meter.querySelector('.dm-note').textContent = 'This device could not be read.';
  console.warn('[device meter]', err);
});

async function run(root) {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const segs = [...root.querySelectorAll('.dm-bar i')];
  const bar = root.querySelector('.dm-bar');
  const out = root.querySelector('.dm-read output');
  const gradeOut = root.querySelector('.dm-read em');
  const note = root.querySelector('.dm-note');
  const tell = detail => document.dispatchEvent(new CustomEvent('c4d:device', { detail }));
  // The town's own touch test (js/controls/touch.js prefersTouch), so the tier named matches.
  const touch = matchMedia('(pointer: coarse)').matches || (navigator.maxTouchPoints > 0 && innerWidth < 900);

  tell({ phase: 'start' });
  // Let the cold start paint its first frames before the benchmark takes the GPU.
  await new Promise(r => requestAnimationFrame(() => setTimeout(r, 300)));
  const [profile] = await Promise.all([
    profileDevice({ touch, storage: null, search: location.search }),
    new Promise(r => setTimeout(r, reduced.matches ? 0 : 1700)),
  ]);
  const { score, grade } = scoreProfile(profile);
  const s = profile.signals || {};
  const detail = { full: 'Full', balanced: 'Balanced', light: 'Light' }[profile.choice?.detail] || 'Full';
  const software = /software rasteriser/.test(profile.why || '');
  const facts = [
    `Fits ${detail} detail`,
    software ? 'software renderer' : gpuName(s.renderer),
    s.cores ? `${s.cores} cores` : null,
    s.memoryGB ? `${s.memoryGB >= 8 ? '8+' : s.memoryGB} GB` : 'memory not reported',
    s.webgpu?.adapter ? 'WebGPU' : null,
  ].filter(Boolean);
  note.textContent = facts.join(' · ');
  note.title = `${CLASS_LABEL[profile.cls] || profile.cls} device: ${profile.why}${s.renderer ? ` — ${s.renderer}` : ''}`;
  Object.assign(root.dataset, { state: 'ready', score, grade: grade.id, cls: profile.cls, detail: profile.choice?.detail || '' });
  gradeOut.textContent = grade.label;
  bar.setAttribute('aria-valuenow', String(score));
  bar.setAttribute('aria-valuetext', `${score} of 100, ${grade.label}`);
  tell({ phase: 'done', score, grade: grade.label, detail });

  function paint(v) {
    const lit = Math.max(1, Math.min(segs.length, Math.round(v / (100 / segs.length))));
    segs.forEach((seg, i) => { seg.classList.toggle('on', i < lit); seg.classList.toggle('top', i === lit - 1); });
    out.textContent = String(Math.round(v)).padStart(2, '0');
  }
  if (reduced.matches) { paint(score); return; }

  // Frame pacing: the share of the last 40 frames that came late against their median.
  const gaps = [];
  let last = 0;
  (function pace(t) {
    if (last && !document.hidden) { gaps.push(t - last); if (gaps.length > 40) gaps.shift(); }
    last = t; requestAnimationFrame(pace);
  })(performance.now());
  function late() {
    if (gaps.length < 10) return 0;
    const median = [...gaps].sort((a, b) => a - b)[gaps.length >> 1];
    return gaps.filter(g => g > Math.max(median * 1.6, median + 8)).length / gaps.length;
  }

  let value = 0, wobble = 0;
  const timer = setInterval(() => {
    if (document.hidden) return;
    if (reduced.matches) { clearInterval(timer); paint(score); return; }
    wobble = wobble * 0.7 + (Math.random() * 2 - 1) * 1.6;
    const target = Math.max(2, Math.min(100, score - Math.min(18, late() * 40) + wobble));
    value += (target - value) * (value < score * 0.9 ? 0.2 : 0.35);
    paint(value);
  }, 160);
}

// "ANGLE (Apple, ANGLE Metal Renderer: Apple M2, Unspecified Version)" → "Apple M2".
function gpuName(renderer) {
  let s = String(renderer || '');
  const angle = s.match(/^ANGLE \((.*)\)$/);
  if (angle) { const parts = angle[1].split(', '); s = parts[1] || parts[0]; }
  s = s.replace(/^ANGLE Metal Renderer:\s*/, '').replace(/\s*\(0x[0-9a-f]+\)/gi, '')
    .replace(/\s+Direct3D.*$/i, '').replace(/\/PCIe\/SSE2/i, '').trim();
  if (!s) return 'GPU not reported';
  return s.length > 26 ? `${s.slice(0, 25)}…` : s;
}
