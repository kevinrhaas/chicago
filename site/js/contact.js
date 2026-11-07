/* Contact page. The form works without JS (it posts to FormSubmit and comes back to
   ?sent=1); with JS it sends over FormSubmit's AJAX endpoint and stays on the page. */
(function () {
  'use strict';
  var root = document.documentElement;
  var TO = 'kevin.haas@polecat.live';

  var toggle = document.getElementById('themeToggle');
  if (toggle) toggle.addEventListener('click', function () {
    var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('chicago.theme', next); } catch (e) {}
  });

  var wrap = document.getElementById('formWrap'), form = document.getElementById('contactForm');
  var status = document.getElementById('formStatus'), btn = document.getElementById('sendBtn'), sent = document.getElementById('sent');
  function done() { wrap.classList.add('done'); if (sent) sent.focus({ preventScroll: false }); }
  if (/[?&]sent=1/.test(location.search)) done();
  if (!form || !window.fetch) return;

  function say(msg, kind) { status.className = 'form-status' + (kind ? ' ' + kind : ''); status.innerHTML = msg; }
  var fallback = function (data) {
    var body = encodeURIComponent((data.message || '') + '\n\n— ' + (data.name || '') + ' <' + (data.email || '') + '>');
    return 'mailto:' + TO + '?subject=' + encodeURIComponent('4D Chicago — ' + (data.topic || 'a message')) + '&body=' + body;
  };

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var data = {};
    new FormData(form).forEach(function (v, k) { data[k] = String(v).trim(); });
    if (data._honey) { done(); return; }                       // a bot filled the hidden field
    if (!data.name || !data.message) { say('Please add your name and a message.', 'err'); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email || '')) { say('Please check your email address — we need it to reply.', 'err'); return; }
    btn.disabled = true; say('Sending…');
    fetch('https://formsubmit.co/ajax/' + TO, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({
        name: data.name, email: data.email, topic: data.topic, message: data.message,
        _subject: '4D Chicago — ' + data.topic + ' — from ' + data.name,
        _replyto: data.email, _template: 'table', _captcha: 'false'
      })
    }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (res.ok && String(res.j.success) === 'true') { form.reset(); done(); return; }
        throw new Error(res.j && res.j.message || 'not sent');
      })
      .catch(function () {
        btn.disabled = false;
        say('That didn’t go through. You can <a href="' + fallback(data) + '" style="text-decoration:underline">send it by email instead</a> — your words are already filled in.', 'err');
      });
  });
})();
