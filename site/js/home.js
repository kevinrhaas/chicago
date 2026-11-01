/* chicago.polecat.live — front-door motion. Classic script, no deps.
   Everything here is enhancement: the page reads whole without it. */
(function () {
  'use strict';
  var root = document.documentElement;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var saveData = navigator.connection && navigator.connection.saveData;
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
  function quietPlay(v) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }

  /* ---- theme (chicago.theme) --------------------------------------------- */
  var toggle = document.getElementById('themeToggle');
  if (toggle) toggle.addEventListener('click', function () {
    var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('chicago.theme', next); } catch (e) {}
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', next === 'light' ? '#f5f2ea' : '#07090f');
  });

  /* ---- nav, progress, Prairie parallax ------------------------------------ */
  var nav = document.getElementById('nav'), bar = document.querySelector('.progress');
  var pImg = document.getElementById('prairieImg'), ticking = false;
  function onScroll() {
    if (ticking) return; ticking = true;
    requestAnimationFrame(function () {
      ticking = false;
      var y = window.scrollY || 0, vh = window.innerHeight;
      if (nav) nav.classList.toggle('scrolled', y > vh * 0.6);
      if (bar) bar.style.setProperty('--sp', (y / Math.max(1, document.documentElement.scrollHeight - vh)).toFixed(4));
      if (pImg && !reduce) {
        var r = pImg.parentNode.getBoundingClientRect();
        if (r.bottom > 0 && r.top < vh) pImg.style.setProperty('--py', ((r.top + r.height / 2 - vh / 2) * -0.08).toFixed(1) + 'px');
      }
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();

  /* ---- reveal + counters ------------------------------------------------------ */
  function countUp(el) {
    var to = +el.getAttribute('data-count'); if (reduce || !to) return;
    var t0 = null;
    (function step(t) { if (t0 === null) t0 = t; var k = clamp((t - t0) / 1400, 0, 1);
      el.textContent = Math.round(to * (1 - Math.pow(1 - k, 4))); if (k < 1) requestAnimationFrame(step); })(performance.now());
  }
  var reveals = [].slice.call(document.querySelectorAll('.reveal, .timeline'));
  if (!('IntersectionObserver' in window)) reveals.forEach(function (e) { e.classList.add('in'); });
  else {
    var io = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) {
        if (!en.isIntersecting) return;
        en.target.classList.add('in');
        [].forEach.call(en.target.querySelectorAll('[data-count]'), countUp);
        io.unobserve(en.target);
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(function (e) { io.observe(e); });
  }

  /* ---- card spotlight ------------------------------------------------------------ */
  [].forEach.call(document.querySelectorAll('.acard'), function (c) {
    c.addEventListener('pointermove', function (ev) {
      var r = c.getBoundingClientRect();
      c.style.setProperty('--mx', (ev.clientX - r.left) + 'px'); c.style.setProperty('--my', (ev.clientY - r.top) + 'px');
    });
  });

  /* ---- the record: tabs over three screens from the app ------------------------------ */
  var CAPS = [
    'Glessner House, 1904: still standing, built 1887 — with the archival photograph the record cites.',
    'The Sauganash Hotel, 1835: who lived there, and its 30 facts graded — over the confidence view of the town.',
    'Fort Dearborn, 1812: the commanding officer’s barracks, 14 facts — 4 attested, 6 inferred, 4 reconstructed.'
  ];
  var tabs = [].slice.call(document.querySelectorAll('.shot-tabs button'));
  var imgs = [].slice.call(document.querySelectorAll('.shot-frame img'));
  var cap = document.getElementById('shotCap'), shotIdx = 0, auto = null;
  function show(i) {
    shotIdx = i;
    tabs.forEach(function (t, k) { t.setAttribute('aria-selected', k === i ? 'true' : 'false'); });
    imgs.forEach(function (im, k) { im.classList.toggle('on', k === i); });
    if (cap) cap.textContent = CAPS[i];
  }
  tabs.forEach(function (t, k) { t.addEventListener('click', function () { show(k); if (auto) { clearInterval(auto); auto = null; } }); });
  if (tabs.length && !reduce) auto = setInterval(function () { show((shotIdx + 1) % tabs.length); }, 6000);

  /* ---- hero film: plays while on screen ------------------------------------------------- */
  var hero = document.getElementById('heroVideo');
  if (hero) {
    if (reduce || saveData) hero.removeAttribute('autoplay');
    else if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (e) { if (e[0].isIntersecting) quietPlay(hero); else hero.pause(); }, { threshold: 0.1 }).observe(hero);
      document.addEventListener('visibilitychange', function () { if (document.hidden) hero.pause(); });
    } else quietPlay(hero);
  }

  /* ---- the film player: any of the four films, switchable in place ---------------------- */
  var dlg = document.getElementById('film'), film = document.getElementById('filmVideo');
  var close = document.getElementById('closeFilm'), title = document.getElementById('filmTitle');
  var walk = document.getElementById('filmWalk');
  var FILMS = {
    'chicago-walk': ['4D Chicago · 1904, 1835 and 1812', '4d/'],
    'chicago-1812': ['4D Chicago · Fort Dearborn, 14 August 1812', '4d/1812/'],
    'chicago-1835': ['4D Chicago · the river town, 1 July 1835', '4d/1835/'],
    'chicago-1904': ['4D Chicago · Prairie Avenue, 1 July 1904', '4d/1904/']
  };
  var current = '';
  function load(name, play) {
    if (!FILMS[name]) return;
    if (name !== current) {
      current = name;
      film.pause();
      var v = name === 'chicago-walk' ? '?v=2' : '';   // the combined cut was re-cut newest-first
      film.innerHTML = '<source src="media/' + name + '.webm' + v + '" type="video/webm"><source src="media/' + name + '.mp4' + v + '" type="video/mp4">';
      film.poster = 'media/' + name + '.jpg' + v;
      film.load();
    }
    if (title) title.textContent = FILMS[name][0];
    if (walk) walk.href = FILMS[name][1];
    [].forEach.call(dlg.querySelectorAll('[data-tab]'), function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-tab') === name ? 'true' : 'false'); });
    if (play) quietPlay(film);
  }
  if (dlg && film) {
    [].forEach.call(document.querySelectorAll('[data-film]'), function (btn) {
      btn.addEventListener('click', function () {
        var name = btn.getAttribute('data-film');
        if (typeof dlg.showModal !== 'function') { location.href = 'media/' + name + '.mp4'; return; }   // very old browsers
        dlg.showModal();
        if (hero) hero.pause();
        load(name, true);
      });
    });
    [].forEach.call(dlg.querySelectorAll('[data-tab]'), function (b) {
      b.addEventListener('click', function () { load(b.getAttribute('data-tab'), true); });
    });
    close.addEventListener('click', function () { dlg.close(); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('close', function () { film.pause(); if (hero && !reduce && !saveData) quietPlay(hero); });
  }
})();
