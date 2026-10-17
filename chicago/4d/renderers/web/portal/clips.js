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
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const saveData = navigator.connection && navigator.connection.saveData;
  if (reduced.matches || saveData) return;
  // One file per clip is fetched: VP9 WebM where it plays, H.264 MP4 otherwise (Safari, iPhone).
  const probe = document.createElement('video');
  const ext = probe.canPlayType('video/webm; codecs="vp9"') ? 'webm'
    : probe.canPlayType('video/mp4; codecs="avc1.42E01E"') ? 'mp4' : '';
  if (!ext) return;
  const plates = [...document.querySelectorAll('.era-plate[data-clips]')];
  const rand = (a, b) => a + Math.random() * (b - a);
  const pick = list => list[Math.floor(Math.random() * list.length)];
  const feeds = [];

  plates.forEach(plate => {
    const card = plate.closest('.era');
    const names = plate.dataset.clips.split(',').map(s => s.trim()).filter(Boolean);
    if (!card || !names.length) return;
    const name = pick(names);
    const video = document.createElement('video');
    video.className = 'era-feed';
    video.muted = true; video.defaultMuted = true; video.loop = true; video.playsInline = true;
    video.setAttribute('muted', ''); video.setAttribute('playsinline', ''); video.setAttribute('aria-hidden', 'true');
    video.preload = 'auto'; video.disablePictureInPicture = true;
    const still = plate.querySelector('img');
    if (still) video.poster = still.currentSrc || still.src;
    video.src = `walk/portal/clips/${name}.${ext}`;
    // Blocky frames are drawn here: the video at a fraction of its size, scaled back up unsmoothed.
    const canvas = document.createElement('canvas');
    canvas.className = 'era-feed-blocks'; canvas.setAttribute('aria-hidden', 'true');
    const ctx = canvas.getContext('2d');
    plate.prepend(canvas); plate.prepend(video);
    plate.dataset.feed = 'tuning';
    plate.dataset.clip = name;
    const feed = { plate, card, video, canvas, ctx, name, fault: null, until: 0, next: 0, visible: true,
      shaky: card.classList.contains('era-calibrating') };
    feed.next = performance.now() + rand(2500, 7000);
    video.addEventListener('playing', () => { plate.dataset.feed = 'live'; });
    video.addEventListener('error', () => { plate.dataset.feed = 'lost'; video.remove(); canvas.remove(); feed.dead = true; });
    feeds.push(feed);
  });
  if (!feeds.length) return;

  function play(feed) {
    if (feed.dead || !feed.visible || document.hidden) return;
    const p = feed.video.play();
    // Autoplay refused (an iPhone in Low Power Mode, a browser setting): the still stays.
    // A play() cut short by our own pause (scrolled away) is not a refusal.
    if (p && p.catch) p.catch(err => { if (err && err.name === 'NotAllowedError') feed.plate.dataset.feed = 'still'; });
  }
  const seen = 'IntersectionObserver' in window && new IntersectionObserver(entries => entries.forEach(entry => {
    const feed = feeds.find(f => f.plate === entry.target); if (!feed) return;
    feed.visible = entry.isIntersecting;
    if (feed.visible) play(feed); else feed.video.pause();
  }));
  feeds.forEach(feed => { if (seen) seen.observe(feed.plate); play(feed); });
  document.addEventListener('visibilitychange', () => feeds.forEach(f => (document.hidden ? f.video.pause() : play(f))));
  reduced.addEventListener('change', () => { if (reduced.matches) feeds.forEach(f => { f.video.pause(); f.video.remove(); f.canvas.remove(); f.dead = true; }); });

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
    const v = feed.video; if (v.readyState < 2) return;
    const w = feed.plate.clientWidth, h = feed.plate.clientHeight;
    const bw = Math.max(4, Math.round(w / size)), bh = Math.max(2, Math.round(h / size));
    if (feed.canvas.width !== bw || feed.canvas.height !== bh) { feed.canvas.width = bw; feed.canvas.height = bh; }
    // Cover-fit the 3:1 video into the plate's box, as object-fit does for the still.
    const vr = v.videoWidth / v.videoHeight, pr = w / h;
    let sw = v.videoWidth, sh = v.videoHeight, sx = 0, sy = 0;
    if (vr > pr) { sw = sh * pr; sx = (v.videoWidth - sw) / 2; } else { sh = sw / pr; sy = (v.videoHeight - sh) / 2; }
    feed.ctx.imageSmoothingEnabled = true;
    feed.ctx.drawImage(v, sx, sy, sw, sh, 0, 0, bw, bh);
  }
  let last = 0;
  function frame(now) {
    requestAnimationFrame(frame);
    if (now - last < 66) return; // the glitch runs at about 15 fps, like the feed itself
    last = now;
    feeds.forEach(feed => {
      if (feed.dead || !feed.visible || feed.video.paused) return;
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
