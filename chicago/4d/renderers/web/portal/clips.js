(() => {
  // T-2685: each destination card shows a live feed from its year. A card lists a small
  // library of loops filmed in the app itself (tools/portal_clips.mjs); one is picked at
  // random per load and only that one is fetched. The still stays underneath as the poster,
  // and is all a visitor gets with reduced motion, Save-Data, or a video that will not play.
  //
  // The feed is an unstable connection, but mostly a calm one: each card waits a while,
  // then has one short fault (the picture blocks up, tears, flickers or drops to static),
  // then settles again. Calibrating years fault more often than the nominal one, and a card
  // whose hold is slipping (portal.js sets data-hold="drift") breaks up until it recovers.
  // T-3798: the clips sit beside this script, so the launch page (/4d/) and the classic
  // console (/4d/console/) both find them.
  const here = (document.currentScript && document.currentScript.src) || new URL('walk/portal/clips.js', document.baseURI).href;
  const clip = (file) => new URL(`clips/${file}`, here).href;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const saveData = navigator.connection && navigator.connection.saveData;
  if (reduced.matches || saveData) return;
  // One file per clip is fetched: VP9 WebM where it plays, H.264 MP4 otherwise (Safari, iPhone).
  // A file that will not decode falls back to the other format, then to the reel (below).
  const probe = document.createElement('video');
  const exts = [probe.canPlayType('video/webm; codecs="vp9"') && 'webm',
    probe.canPlayType('video/mp4; codecs="avc1.42E01E"') && 'mp4'].filter(Boolean);
  const plates = [...document.querySelectorAll('.era-plate[data-clips]')];
  const rand = (a, b) => a + Math.random() * (b - a);
  const pick = list => list[Math.floor(Math.random() * list.length)];
  const feeds = [];

  plates.forEach(plate => {
    const card = plate.closest('.era');
    const names = plate.dataset.clips.split(',').map(s => s.trim()).filter(Boolean);
    if (!card || !names.length) return;
    const name = pick(names);
    if (!exts.length) { feeds.push(reelFeed(plate, card, name)); return; }
    const video = document.createElement('video');
    video.className = 'era-feed';
    video.muted = true; video.defaultMuted = true; video.loop = true; video.playsInline = true;
    video.setAttribute('muted', ''); video.setAttribute('playsinline', ''); video.setAttribute('aria-hidden', 'true');
    video.preload = 'auto'; video.disablePictureInPicture = true;
    const still = plate.querySelector('img');
    if (still) video.poster = still.currentSrc || still.src;
    video.src = clip(`${name}.${exts[0]}`);
    // Blocky frames are drawn here: the video at a fraction of its size, scaled back up unsmoothed.
    const canvas = document.createElement('canvas');
    canvas.className = 'era-feed-blocks'; canvas.setAttribute('aria-hidden', 'true');
    const ctx = canvas.getContext('2d');
    plate.prepend(canvas); plate.prepend(video);
    plate.dataset.feed = 'tuning';
    plate.dataset.clip = name;
    const feed = { plate, card, video, canvas, ctx, name, fault: null, until: 0, next: 0, visible: true,
      shaky: card.classList.contains('era-calibrating'), ext: 0, tries: 0 };
    feed.next = performance.now() + rand(2500, 7000);
    video.addEventListener('playing', () => { plate.dataset.feed = 'live'; });
    video.addEventListener('error', () => {
      if (feed.reel) return;
      if (++feed.ext < exts.length) { video.src = clip(`${name}.${exts[feed.ext]}`); play(feed); }
      else toReel(feed);
    });
    feeds.push(feed);
  });
  if (!feeds.length) return;

  // The reel: the same clip as a strip of small grey frames in one image, stepped onto a canvas
  // at the clip's 10 fps. An iPhone in Low Power Mode refuses every video, muted or not, and
  // so does a browser set never to autoplay; an image is not a video, so the feed still runs
  // there (Kevin, 2026-11-17: the cards showed stills on his phone). tools/portal_clips.mjs
  // makes `<clip>.reel.webp` beside each clip.
  function reelFeed(plate, card, name) {
    const canvas = document.createElement('canvas');
    canvas.className = 'era-feed-blocks'; canvas.setAttribute('aria-hidden', 'true');
    plate.prepend(canvas);
    const feed = { plate, card, canvas, ctx: canvas.getContext('2d'), name, fault: null, until: 0, next: performance.now() + rand(2500, 7000),
      visible: true, shaky: card.classList.contains('era-calibrating') };
    plate.dataset.feed = 'tuning'; plate.dataset.clip = name;
    toReel(feed);
    return feed;
  }
  function toReel(feed) {
    if (feed.reel || feed.dead) return;
    if (feed.video) { feed.video.pause(); feed.video.removeAttribute('src'); feed.video.load(); feed.video.remove(); feed.video = null; }
    const view = document.createElement('canvas');
    view.className = 'era-feed era-feed-reel'; view.setAttribute('aria-hidden', 'true');
    const img = new Image();
    img.decoding = 'async';
    feed.reel = { img, view, ctx: view.getContext('2d'), frames: 0, fw: 0, fh: 0, shown: -1, t0: performance.now() };
    feed.plate.prepend(view);
    feed.plate.dataset.reel = '';
    img.onload = () => {
      const r = feed.reel; r.fw = img.naturalWidth; r.fh = Math.round(r.fw / 3); r.frames = Math.max(1, Math.floor(img.naturalHeight / r.fh));
      view.width = r.fw; view.height = r.fh;
      stepReel(feed, performance.now());
      feed.plate.dataset.feed = 'live';
    };
    img.onerror = () => { feed.plate.dataset.feed = 'lost'; view.remove(); feed.canvas.remove(); feed.dead = true; };
    img.src = clip(`${feed.name}.reel.webp`);
  }
  function stepReel(feed, now) {
    const r = feed.reel; if (!r.frames) return;
    const k = Math.floor((now - r.t0) / 100) % r.frames;
    if (k === r.shown) return;
    r.shown = k;
    r.ctx.drawImage(r.img, 0, k * r.fh, r.fw, r.fh, 0, 0, r.fw, r.fh);
  }
  const running = feed => !feed.dead && feed.visible && !document.hidden && (feed.reel ? feed.reel.frames > 0 : !feed.video.paused);

  function play(feed) {
    if (feed.dead || feed.reel || !feed.visible || document.hidden) return;
    const p = feed.video.play();
    // Autoplay refused (an iPhone in Low Power Mode, a browser setting): the reel takes over.
    // A play() cut short by our own pause (scrolled away) is not a refusal.
    if (p && p.catch) p.catch(err => { if (err && err.name === 'NotAllowedError') toReel(feed); });
    // Some refusals never answer: a feed that is still not live a while after it was asked to
    // play, with the page in view, goes to the reel too.
    clearTimeout(feed.watch);
    feed.watch = setTimeout(() => {
      if (!feed.reel && feed.visible && !document.hidden && feed.plate.dataset.feed !== 'live') toReel(feed);
    }, 6000);
  }
  const pause = feed => { clearTimeout(feed.watch); if (feed.video) feed.video.pause(); };
  const seen = 'IntersectionObserver' in window && new IntersectionObserver(entries => entries.forEach(entry => {
    const feed = feeds.find(f => f.plate === entry.target); if (!feed) return;
    feed.visible = entry.isIntersecting;
    if (feed.visible) play(feed); else pause(feed);
  }));
  feeds.forEach(feed => { if (seen) seen.observe(feed.plate); play(feed); });
  document.addEventListener('visibilitychange', () => feeds.forEach(f => (document.hidden ? pause(f) : play(f))));
  reduced.addEventListener('change', () => {
    if (reduced.matches) feeds.forEach(f => { pause(f); f.video?.remove(); f.reel?.view.remove(); f.canvas.remove(); f.dead = true; });
  });

  // The faults. Each is short; the calm between them is long.
  const FAULTS = ['blocks', 'blocks', 'tear', 'flicker', 'drop', 'blocks-hard'];
  function begin(feed, now, forced) {
    feed.fault = forced || pick(FAULTS);
    const len = { blocks: rand(500, 1600), 'blocks-hard': rand(300, 800), tear: rand(250, 700), flicker: rand(300, 900), drop: rand(150, 450) }[feed.fault];
    feed.until = now + len;
    feed.block = feed.fault === 'blocks-hard' ? Math.round(rand(14, 24)) : Math.round(rand(5, 11));
    feed.plate.dataset.fault = feed.fault;
  }
  function end(feed, now) {
    feed.fault = null; delete feed.plate.dataset.fault;
    feed.plate.style.removeProperty('--tear'); feed.plate.style.removeProperty('--flick');
    // Mostly calm: 1835 holds nominal and waits longer between faults than the calibrating years.
    feed.next = now + (feed.shaky ? rand(5000, 13000) : rand(8000, 20000));
    // Now and then a fault comes back for a second go straight away, so the rhythm is not regular.
    if (Math.random() < .2) feed.next = now + rand(250, 900);
  }
  function drawBlocks(feed, size) {
    const v = feed.reel ? feed.reel.view : feed.video;
    const vw = feed.reel ? v.width : v.videoWidth, vh = feed.reel ? v.height : v.videoHeight;
    if (feed.reel ? !feed.reel.frames : v.readyState < 2) return;
    const w = feed.plate.clientWidth, h = feed.plate.clientHeight;
    const bw = Math.max(4, Math.round(w / size)), bh = Math.max(2, Math.round(h / size));
    if (feed.canvas.width !== bw || feed.canvas.height !== bh) { feed.canvas.width = bw; feed.canvas.height = bh; }
    // Cover-fit the 3:1 video into the plate's box, as object-fit does for the still.
    const vr = vw / vh, pr = w / h;
    let sw = vw, sh = vh, sx = 0, sy = 0;
    if (vr > pr) { sw = sh * pr; sx = (vw - sw) / 2; } else { sh = sw / pr; sy = (vh - sh) / 2; }
    feed.ctx.imageSmoothingEnabled = true;
    feed.ctx.drawImage(v, sx, sy, sw, sh, 0, 0, bw, bh);
  }
  let last = 0;
  function frame(now) {
    requestAnimationFrame(frame);
    feeds.forEach(feed => { if (feed.reel && running(feed)) stepReel(feed, now); });
    if (now - last < 66) return; // the glitch runs at about 15 fps, like the feed itself
    last = now;
    feeds.forEach(feed => {
      if (!running(feed)) return;
      const slipping = feed.card.dataset.hold === 'drift';
      if (!feed.fault && (now > feed.next || (slipping && Math.random() < .18))) begin(feed, now, slipping ? pick(['blocks-hard', 'tear', 'drop']) : null);
      if (!feed.fault) return;
      if (now > feed.until) { end(feed, now); return; }
      if (feed.fault === 'blocks' || feed.fault === 'blocks-hard') {
        // The block size steps as the link renegotiates, never smoothly.
        if (Math.random() < .3) feed.block = Math.max(3, feed.block + Math.round(rand(-4, 4)));
        drawBlocks(feed, feed.block);
      } else if (feed.fault === 'tear') {
        feed.plate.style.setProperty('--tear', `${Math.round(rand(-14, 14))}px`);
      } else if (feed.fault === 'flicker') {
        feed.plate.style.setProperty('--flick', Math.random() < .5 ? rand(.15, .5).toFixed(2) : '1');
      }
    });
  }
  requestAnimationFrame(frame);
})();
