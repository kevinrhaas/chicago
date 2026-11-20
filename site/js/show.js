/* 4D Chicago public site: menu, reveal, films that play when seen, the film player,
   filters and the season switcher. No dependencies. Films are listed in js/films.js. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const saveData = navigator.connection && navigator.connection.saveData;

  // The current page in the menu.
  const page = document.body.dataset.page;
  $$('.menu a').forEach(a => { if (a.getAttribute('href').replace(/\.\.\//g, '').replace(/\/$/, '') === page) a.setAttribute('aria-current', 'page'); });

  // The phone menu.
  const bar = $('#bar'), btn = $('.menu-btn');
  if (bar && btn) {
    btn.addEventListener('click', () => {
      const open = !bar.hasAttribute('data-open');
      bar.toggleAttribute('data-open', open);
      btn.setAttribute('aria-expanded', String(open));
    });
    $$('.menu a').forEach(a => a.addEventListener('click', () => { bar.removeAttribute('data-open'); btn.setAttribute('aria-expanded', 'false'); }));
  }

  // Reveal on scroll.
  const rv = $$('.rv');
  if ('IntersectionObserver' in window && !reduced) {
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { rootMargin: '0px 0px -8% 0px' });
    rv.forEach(el => io.observe(el));
  } else rv.forEach(el => el.classList.add('in'));

  // Films: each [data-film] frame shows its poster, and a muted loop plays while it is on screen.
  const FILMS = window.CHICAGO_FILMS || { files: {} };
  const local = /^(localhost|127\.0\.0\.1)$/.test(location.hostname) || location.protocol === 'file:';
  const base = local && FILMS.localBase ? FILMS.localBase : FILMS.base;
  const srcOf = id => (FILMS.files[id] ? base + FILMS.files[id] : null);
  const frames = $$('[data-film]');
  const start = (el) => {
    if (el._v || reduced || saveData) return;
    const src = srcOf(el.dataset.film);
    if (!src) return;
    const v = document.createElement('video');
    v.muted = true; v.defaultMuted = true; v.loop = true; v.playsInline = true; v.preload = 'auto';
    v.setAttribute('muted', ''); v.setAttribute('playsinline', ''); v.setAttribute('aria-hidden', 'true');
    v.disablePictureInPicture = true;
    v.src = src;
    v.addEventListener('playing', () => el.setAttribute('data-live', ''));
    v.addEventListener('error', () => { v.remove(); el._v = 'dead'; });
    el.append(v);
    el._v = v;
  };
  const play = el => { if (!el._v) start(el); if (el._v && el._v !== 'dead') { const p = el._v.play(); if (p && p.catch) p.catch(() => {}); } };
  const pause = el => { if (el._v && el._v !== 'dead') el._v.pause(); };
  if ('IntersectionObserver' in window) {
    const fo = new IntersectionObserver(es => es.forEach(e => (e.isIntersecting ? play(e.target) : pause(e.target))), { rootMargin: '120px 0px' });
    frames.forEach(el => fo.observe(el));
  }
  document.addEventListener('visibilitychange', () => frames.forEach(el => (document.hidden ? pause(el) : null)));

  // The player: any [data-play] opens its film, with sound and controls.
  const dlg = $('#player');
  if (dlg) {
    const vid = $('video', dlg), title = $('#player-title', dlg);
    $$('[data-play]').forEach(b => b.addEventListener('click', () => {
      const src = srcOf(b.dataset.play) || b.dataset.src;
      if (!src) return;
      vid.src = src; title.textContent = b.dataset.title || '4D Chicago';
      dlg.showModal(); const p = vid.play(); if (p && p.catch) p.catch(() => {});
    }));
    const close = () => { vid.pause(); vid.removeAttribute('src'); vid.load(); if (dlg.open) dlg.close(); };
    $('[data-close]', dlg).addEventListener('click', close);
    dlg.addEventListener('click', e => { if (e.target === dlg) close(); });
    dlg.addEventListener('close', () => { vid.pause(); });
  }

  // Filters: chips with data-filter narrow the [data-tags] items of their group. A group with
  // data-more="N" shows its first N matches and a button for the rest, so a phone is not a long scroll.
  $$('[data-filters]').forEach(group => {
    const items = $$(group.dataset.filters);
    const chips = $$('.chip[data-filter]', group);
    const limit = +group.dataset.more || 0;
    let open = false, f = 'all', btn = null;
    const apply = () => {
      let n = 0;
      items.forEach(it => {
        const match = f === 'all' || (it.dataset.tags || '').split(' ').includes(f);
        it.hidden = !match || Boolean(limit && !open && n >= limit);
        if (match) n++;
      });
      if (btn) { btn.hidden = open || n <= limit; btn.querySelector('span').textContent = `Show all ${n}`; }
    };
    if (limit && items.length > limit) {
      btn = document.createElement('div');
      btn.className = 'more-row';
      btn.innerHTML = '<button class="btn ghost" type="button"><span></span></button>';
      items[items.length - 1].parentElement.after(btn);
      btn.querySelector('button').addEventListener('click', () => { open = true; apply(); });
    }
    chips.forEach(c => c.addEventListener('click', () => {
      chips.forEach(o => o.setAttribute('aria-pressed', String(o === c)));
      f = c.dataset.filter;
      apply();
    }));
    apply();
  });

  // How it's made (home): sources travel the wire through the five stages, each stage lighting as one
  // passes and cycling its pictures. Ported from the first home page; nothing runs off screen.
  (() => {
    const flow = document.getElementById('flow');
    if (!flow || reduced) return;
    const path = document.getElementById('flowPath'), glow = document.getElementById('flowGlow');
    const layer = document.getElementById('packets');
    const stages = [...flow.querySelectorAll('.stage')];
    const STORIES = [
      ['#c9a46a', ['Sanborn map, 1911', 'Footprint traced', 'Attested · 3 sources', 'Model + its sources', 'Prairie Avenue, on screen'], 't-sanborn'],
      ['#7ec8e3', ['1840 census page', 'Names read, line by line', 'Matched to a directory', 'Resident placed on a lot', 'Who lived here']],
      ['#ff3b4f', ['HABS photograph', 'Camera solved', 'Model compared to it', 'Roof rebuilt', 'Matches the photo'], 't-habs'],
      ['#e0a050', ['Robinson atlas, 1886', 'Pinned to the survey grid', 'Lots and addresses graded', 'Ground and roads built', 'Walkable 1904'], 't-plat'],
      ['#9ad17a', ['Wau-Bun, 1856', 'Read scene by scene', 'Inferred · with a note', 'Note on the model', 'In the Kinzie record']],
    ];
    let nodes = [], at = [], len = 0, vertical = false, visible = false, raf = 0, last = 0;
    const packets = [];
    const layout = () => {
      const fr = flow.getBoundingClientRect();
      nodes = stages.map((s) => { const r = s.querySelector('.st-n').getBoundingClientRect(); return [r.left + r.width / 2 - fr.left, r.top + r.height / 2 - fr.top]; });
      vertical = Math.abs(nodes[1][0] - nodes[0][0]) < 4; flow.classList.toggle('v', vertical);
      const first = nodes[0], end = nodes[nodes.length - 1];
      const pts = [vertical ? [first[0], first[1] - 40] : [first[0] - 60, first[1]], ...nodes, vertical ? [end[0], end[1] + 40] : [end[0] + 60, end[1]]];
      const d = 'M' + pts.map((p) => `${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' L');
      path.setAttribute('d', d); glow.setAttribute('d', d);
      len = path.getTotalLength();
      at = []; let acc = 0;
      for (let i = 1; i < pts.length; i++) { acc += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); if (i <= nodes.length) at.push(acc); }
    };
    const spawn = (k, d) => {
      const st = STORIES[k % STORIES.length], el = document.createElement('div');
      el.className = 'packet' + (st[2] ? ' has-img' : ''); el.style.setProperty('--pc', st[0]);
      el.innerHTML = (st[2] ? `<img src="media/flow/${st[2]}.jpg" alt="">` : '<i></i>') + '<span></span>';
      layer.append(el);
      packets.push({ el, label: el.querySelector('span'), story: st[1], d, stage: -2 });
    };
    const frame = (t) => {
      raf = 0; if (!visible) return;
      const dt = last ? Math.min(64, t - last) : 16; last = t;
      const speed = len / 14000;          // a source crosses all five stages in about fourteen seconds
      for (const p of packets) {
        p.d += speed * dt;
        if (p.d < 0) { p.el.style.opacity = 0; continue; }
        if (p.d > len) { p.d = -len * 0.25; p.stage = -2; p.el.style.opacity = 0; continue; }
        const pt = path.getPointAtLength(p.d);
        let s = -1; for (let i = 0; i < at.length; i++) if (p.d >= at[i] - 30) s = i;
        if (s !== p.stage) {
          p.stage = s; p.label.textContent = p.story[Math.max(0, s)];
          if (s >= 0) { const sg = stages[s]; sg.classList.add('lit'); clearTimeout(sg._t); sg._t = setTimeout(() => sg.classList.remove('lit'), 900); }
        }
        p.el.style.opacity = Math.max(0, Math.min(1, p.d / 40, (len - p.d) / 40)).toFixed(2);
        p.el.style.transform = `translate(${pt.x.toFixed(1)}px,${(pt.y + (vertical ? 0 : -30)).toFixed(1)}px) translate(-50%,-50%)`;
      }
      raf = requestAnimationFrame(frame);
    };
    layout();
    for (let k = 0; k < 5; k++) spawn(k, k * len / 5);
    stages.forEach((sg, i) => {
      const ims = [...sg.querySelectorAll('.st-media img')]; if (ims.length < 2) return;
      let n = 0; setTimeout(() => setInterval(() => { if (!visible) return; ims[n].classList.remove('on'); n = (n + 1) % ims.length; ims[n].classList.add('on'); }, 3200), i * 550);
    });
    addEventListener('resize', layout);
    document.fonts?.ready?.then(layout);
    new IntersectionObserver((e) => { visible = e[0].isIntersecting; last = 0; if (visible && !raf) { layout(); raf = requestAnimationFrame(frame); } }, { threshold: 0.05 }).observe(flow);
  })();

  // Season switcher: chips swap the stills of one camera.
  $$('.switcher').forEach(sw => {
    const imgs = $$('.film img', sw), chips = $$('.chip', sw);
    chips.forEach((c, i) => c.addEventListener('click', () => {
      chips.forEach(o => o.setAttribute('aria-pressed', String(o === c)));
      imgs.forEach((im, j) => im.classList.toggle('on', i === j));
    }));
  });
})();
