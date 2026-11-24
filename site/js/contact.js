/* Contact page (T-3741). Every message is first saved to the project's Firestore
   (`messages`, which only the owner can read, on /4d/walk/visitors.html), then FormSubmit
   is asked to email it on. Either one landing counts as sent; if both fail, the visitor
   gets a mailto with their words filled in. Without JS the form posts to FormSubmit and
   comes back to ?sent=1. The fields written here are held to the rules' hasOnly list in
   chicago/4d/docs/SIGN-IN.md by chicago/4d/tools/test_contact_messages.mjs. */
(function () {
  'use strict';
  var TO = 'kevin.haas@polecat.live';
  // The Firebase web config is public by design (chicago/4d/renderers/web/js/sign-in-config.js);
  // the security rules are what decide who may write and read.
  var PROJECT = 'chicago-61643', KEY = 'AIzaSyBxCJiD-E2s72C5WV8J101WtjCqDxGztDw';
  var STORE = 'https://firestore.googleapis.com/v1/projects/' + PROJECT + '/databases/(default)/documents/messages?key=' + KEY;

  var wrap = document.getElementById('formWrap'), form = document.getElementById('contactForm');
  var status = document.getElementById('formStatus'), btn = document.getElementById('sendBtn'), sent = document.getElementById('sent');
  function done() { wrap.classList.add('done'); if (sent) sent.focus({ preventScroll: false }); }
  if (/[?&]sent=1/.test(location.search)) done();
  if (!form || !window.fetch) return;

  function say(msg, kind) { status.className = 'form-status' + (kind ? ' ' + kind : ''); status.innerHTML = msg; }
  function mailto(data) {
    var body = encodeURIComponent((data.message || '') + '\n\n— ' + (data.name || '') + ' <' + (data.email || '') + '>');
    return 'mailto:' + TO + '?subject=' + encodeURIComponent('4D Chicago — ' + (data.topic || 'a message')) + '&body=' + body;
  }
  function cut(s, n) { return String(s || '').slice(0, n); }

  function save(data) {
    var str = function (v) { return { stringValue: v }; };
    return fetch(STORE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields: {
        name: str(cut(data.name, 120)), email: str(cut(data.email, 200)), topic: str(cut(data.topic, 60)),
        message: str(cut(data.message, 5000)), page: str(cut(location.pathname + location.search, 200)),
        at: { timestampValue: new Date().toISOString() }
      } })
    }).then(function (r) { if (!r.ok) throw new Error('store ' + r.status); return true; });
  }

  function ping(data) {
    return fetch('https://formsubmit.co/ajax/' + TO, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({
        name: data.name, email: data.email, topic: data.topic, message: data.message,
        _subject: '4D Chicago — ' + data.topic + ' — from ' + data.name,
        _replyto: data.email, _template: 'table', _captcha: 'false'
      })
    }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) {
      if (r.ok && String(j.success) === 'true') return true;
      throw new Error(j && j.message || 'not sent');
    }); });
  }

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var data = {};
    new FormData(form).forEach(function (v, k) { data[k] = String(v).trim(); });
    if (data._honey) { done(); return; }                       // a bot filled the hidden field
    if (!data.name || !data.message) { say('Please add your name and a message.', 'err'); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email || '')) { say('Please check your email address: it is how we reply.', 'err'); return; }
    btn.disabled = true; say('Sending…');
    var ok = function () { return true; }, no = function () { return false; };
    // Saved first, so the email can never be the only copy; the email is asked for either way.
    save(data).then(ok, no).then(function (stored) {
      return ping(data).then(ok, no).then(function (mailed) { return stored || mailed; });
    }).then(function (landed) {
      if (landed) { form.reset(); done(); return; }
      btn.disabled = false;
      say('That didn’t go through. You can <a href="' + mailto(data) + '" style="text-decoration:underline">send it by email instead</a>: your words are already filled in.', 'err');
    });
  });
})();
