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

  // Season switcher: chips swap the stills of one camera.
  $$('.switcher').forEach(sw => {
    const imgs = $$('.film img', sw), chips = $$('.chip', sw);
    chips.forEach((c, i) => c.addEventListener('click', () => {
      chips.forEach(o => o.setAttribute('aria-pressed', String(o === c)));
      imgs.forEach((im, j) => im.classList.toggle('on', i === j));
    }));
  });
})();
