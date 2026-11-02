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

  /* ---- photo-matched pairs: filter by year ---------------------------------------- */
  var eraBtns = [].slice.call(document.querySelectorAll('.era-tabs button'));
  var matches = [].slice.call(document.querySelectorAll('.match'));
  eraBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      var era = b.getAttribute('data-era');
      eraBtns.forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      matches.forEach(function (m) { m.classList.toggle('hide', era !== 'all' && m.getAttribute('data-era') !== era); m.classList.add('in'); });
    });
  });

  /* ---- how it's made: sources travel the five stages ---------------------------------- */
  (function () {
    var flow = document.getElementById('flow'); if (!flow || reduce) return;
    var path = document.getElementById('flowPath'), glow = document.getElementById('flowGlow');
    var layer = document.getElementById('packets');
    var stages = [].slice.call(flow.querySelectorAll('.stage'));
    var STORIES = [
      ['#c9a46a', ['Sanborn map, 1911', 'Footprint traced', 'Attested · 3 sources', 'glTF + sidecar', 'Prairie Avenue, on screen']],
      ['#7ec8e3', ['1840 census page', 'Names read, line by line', 'Matched to a directory', 'Resident placed on a lot', '“Who lived here”']],
      ['#ff3b4f', ['HABS photograph', 'Camera solved', 'Model compared to it', 'Roof re-baked', 'Matches the photo'], 't-habs'],
      ['#e0a050', ['Robinson atlas, 1886', 'Pinned to the survey grid', 'Lots & addresses graded', 'Terrain + roads built', 'Walkable 1904'], 't-plat'],
      ['#9ad17a', ['Wau-Bun, 1856', 'Read scene by scene', 'Inferred · with a note', 'Note in the sidecar', 'In the Kinzie record']]
    ];
    var nodes = [], len = 0, vertical = false, packets = [], visible = false, raf = 0, last = 0;
    function layout() {
      var fr = flow.getBoundingClientRect();
      nodes = stages.map(function (s) { var r = s.querySelector('.st-n').getBoundingClientRect(); return [r.left + r.width / 2 - fr.left, r.top + r.height / 2 - fr.top]; });
      vertical = Math.abs(nodes[1][0] - nodes[0][0]) < 4; flow.classList.toggle('v', vertical);
      var first = nodes[0], lastN = nodes[nodes.length - 1];
      var pre = vertical ? [first[0], first[1] - 40] : [first[0] - 60, first[1]];
      var post = vertical ? [lastN[0], lastN[1] + 40] : [lastN[0] + 60, lastN[1]];
      var pts = [pre].concat(nodes, [post]);
      var d = 'M' + pts.map(function (p) { return p[0].toFixed(1) + ' ' + p[1].toFixed(1); }).join(' L');
      path.setAttribute('d', d); glow.setAttribute('d', d);
      len = path.getTotalLength();
      // the length along the path at which each stage sits
      var acc = 0; nodes.at = [];
      for (var i = 1; i < pts.length; i++) { acc += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); if (i <= nodes.length) nodes.at.push(acc); }
    }
    function spawn(k, delay) {
      var st = STORIES[k % STORIES.length], el = document.createElement('div');
      el.className = 'packet' + (st[2] ? ' has-img' : ''); el.style.setProperty('--pc', st[0]);
      el.innerHTML = (st[2] ? '<img src="media/flow/' + st[2] + '.jpg" alt="">' : '<i></i>') + '<span></span>';
      layer.appendChild(el);
      packets.push({ el: el, label: el.querySelector('span'), story: st[1], d: delay, stage: -1 });
    }
    function frame(t) {
      raf = 0; if (!visible) return;
      var dt = last ? Math.min(64, t - last) : 16; last = t;
      var speed = len / 14000;   // a source crosses all five stages in about fourteen seconds
      packets.forEach(function (p) {
        p.d += speed * dt;
        if (p.d < 0) { p.el.style.opacity = 0; return; }
        if (p.d > len) { p.d = -len * 0.25; p.stage = -1; p.el.style.opacity = 0; return; }
        var pt = path.getPointAtLength(p.d);
        var s = -1; for (var i = 0; i < nodes.at.length; i++) if (p.d >= nodes.at[i] - 30) s = i;
        if (s !== p.stage) {
          p.stage = s; p.label.textContent = p.story[Math.max(0, s)];
          if (s >= 0) { var sg = stages[s]; sg.classList.add('lit'); clearTimeout(sg._t); sg._t = setTimeout(function () { sg.classList.remove('lit'); }, 900); }
        }
        var edge = Math.min(1, p.d / 40, (len - p.d) / 40);
        p.el.style.opacity = edge.toFixed(2);
        p.el.style.transform = 'translate(' + pt.x.toFixed(1) + 'px,' + (pt.y + (vertical ? 0 : -30)).toFixed(1) + 'px) translate(-50%, -50%)';
      });
      raf = requestAnimationFrame(frame);
    }
    layout();
    for (var k = 0; k < 5; k++) spawn(k, k * len / 5);
    stages.forEach(function (sg, i) {
      var ims = [].slice.call(sg.querySelectorAll('.st-media img')); if (ims.length < 2) return;
      var at = 0; setTimeout(function () { setInterval(function () { if (!visible) return; ims[at].classList.remove('on'); at = (at + 1) % ims.length; ims[at].classList.add('on'); }, 3200); }, i * 550);
    });
    window.addEventListener('resize', layout);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(layout);
    new IntersectionObserver(function (e) { visible = e[0].isIntersecting; last = 0; if (visible && !raf) { layout(); raf = requestAnimationFrame(frame); } }, { threshold: 0.05 }).observe(flow);
  })();

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
