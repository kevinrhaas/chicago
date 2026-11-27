/**
 * T-3797: the launch page's side of launch access (the data and rules are
 * ../js/launch-rights.js and docs/SIGN-IN.md). Loaded by launch.js after a sign-in:
 *
 *   myRights({ account, config })   → { rights, admin, waiting, cloudReady }
 *   joinWaitlist({ account, config, year, check })  a player without cloud play asks for it
 *   startCloud({ year, account })   → { ok } or { ok: false, title, message } for the check's
 *                                     verdict line. Until the cloud starter (T-3794) runs and
 *                                     the owner opens launch/cloud, it says what it waits on.
 *   mountAdmin({ account, config, body })  the Admin sheet: cloud play's state, the waitlist
 *                                     (let in, or remove), and people by email with their rights
 *   refreshAdmin()                  reread the list when the sheet opens
 *
 * The rules are the gate; this page only shows what they allow.
 */
import { RIGHT_WORD, emailOk, emailId, myRights as readRights, cloudState, listPeople, grant, revoke, joinWaitlist as join, listWaitlist, letIn, leaveWaitlist } from '../js/launch-rights.js';

const projectOf = (config) => config?.firebase?.projectId || '';
let last = { cloudReady: false, note: '' };

export async function myRights({ account, config }) {
  const projectId = projectOf(config);
  if (!projectId) return { rights: [], admin: false, cloudReady: false };
  const [r, cloud] = await Promise.all([readRights({ projectId, account }), cloudState({ projectId, account })]);
  last = { cloudReady: !!cloud.ready, note: cloud.note || '' };
  return { rights: r.ok ? r.rights : [], admin: !!r.admin, waiting: !!r.waiting, cloudReady: last.cloudReady };
}

export async function joinWaitlist({ account, config, year = '', check = '' }) {
  return join({ projectId: projectOf(config), account, year, check });
}

export async function startCloud() {
  if (!last.cloudReady) {
    return { ok: false, title: 'Cloud play is opening soon',
      message: last.note || 'Your account has cloud play. The cloud machines are waiting on Google to approve graphics capacity; this button starts one for you once they are ready.' };
  }
  // T-3794 replaces this with a call to the cloud starter, which checks the same rights.
  return { ok: false, title: 'Cloud play is not connected yet', message: 'The machines are ready, but this page cannot reach the starter yet.' };
}

// ---- Admin sheet -----------------------------------------------------------------------
const n = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const when = (iso) => { const d = new Date(iso); return Number.isNaN(+d) ? '' : d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }); };
const rightsWords = (rights) => (rights.length ? rights.map((r) => RIGHT_WORD[r] || r).join(' · ') : 'no rights');
const why = (r) => (r.why === 'refused' ? 'Refused. Only the owner can give or take away admin.' : r.why === 'offline' ? 'You look to be offline. Try again.'
  : r.why === 'not an email' ? 'That is not an email address.' : `That did not save (${r.why}).`);

let admin = null;
export function mountAdmin({ account, config, body }) {
  const projectId = projectOf(config);
  if (!projectId || !body) return;
  body.querySelector('.admin')?.remove();
  const root = n('div', 'admin');

  const cloud = n('section', 'admin-section');
  cloud.append(n('h3', null, 'Cloud play'));
  const cloudLine = n('p', 'admin-line');
  cloud.append(cloudLine, n('p', 'admin-msg', 'Only people with cloud play can start a machine. Everyone else sees the cloud button as the waitlist.'));

  const waits = n('section', 'admin-section');
  waits.append(n('h3', null, 'Waitlist'));
  const waitList = n('ul', 'admin-people'); waitList.id = 'admin-waitlist';
  const waitMsg = n('p', 'admin-msg'); waitMsg.setAttribute('role', 'status');
  waits.append(n('p', 'admin-msg', 'People who asked for cloud play, oldest first, with the year they chose and what the system check said about their computer.'), waitList, waitMsg);

  const people = n('section', 'admin-section');
  people.append(n('h3', null, 'People'));
  const form = n('form', 'admin-form');
  form.noValidate = true;
  const row1 = n('div', 'admin-row');
  const email = n('input'); email.type = 'email'; email.id = 'admin-email'; email.placeholder = 'name@example.com'; email.autocomplete = 'off'; email.setAttribute('aria-label', 'Email address');
  row1.append(email);
  const row2 = n('div', 'admin-row');
  const boxes = {};
  for (const r of ['cloud', 'admin']) {
    const l = n('label'); const b = n('input'); b.type = 'checkbox'; b.id = `admin-right-${r}`; b.checked = r === 'cloud';
    boxes[r] = b; l.append(b, document.createTextNode(r === 'cloud' ? 'Cloud play' : 'Admin'));
    row2.append(l);
  }
  const note = n('input'); note.type = 'text'; note.id = 'admin-note'; note.maxLength = 200; note.placeholder = 'Note (optional), e.g. tester or teacher'; note.setAttribute('aria-label', 'Note');
  const save = n('button', 'primary', 'Save'); save.type = 'submit'; save.id = 'admin-save';
  const row3 = n('div', 'admin-row'); row3.append(note, save);
  const msg = n('p', 'admin-msg'); msg.setAttribute('role', 'status');
  form.append(row1, row2, row3, msg);
  const list = n('ul', 'admin-people'); list.id = 'admin-people';
  people.append(n('p', 'admin-msg', 'Add someone by the address they sign in with. Their rights are waiting for them the first time they sign in.'), form, list);
  root.append(cloud, waits, people);
  body.append(root);

  const fill = (p) => { email.value = p.email; boxes.cloud.checked = p.rights.includes('cloud'); boxes.admin.checked = p.rights.includes('admin'); note.value = p.note; email.focus(); };
  async function paint() {
    cloudLine.classList.toggle('warn', !last.cloudReady);
    cloudLine.textContent = last.cloudReady ? '> OPEN · players with cloud play can start a machine'
      : '> WAITING · on Google\'s graphics capacity and the cloud starter; the button says "opening soon"';
    waitList.replaceChildren(n('li', 'none', 'Reading…'));
    void listWaitlist({ projectId, account }).then((w) => {
      waitList.replaceChildren();
      if (!w.ok) { waitList.append(n('li', 'none', why(w))); return; }
      if (!w.waiting.length) { waitList.append(n('li', 'none', 'Nobody is waiting.')); return; }
      for (const p of w.waiting) {
        const li = n('li'); li.dataset.email = p.email;
        const meta = n('span', 'meta', [p.name, p.year && `chose ${p.year}`, p.check, p.at && `asked ${when(p.at)}`].filter(Boolean).join(' · '));
        const acts = n('span', 'acts');
        const yes = n('button', 'quiet', 'Let in'); yes.type = 'button';
        yes.addEventListener('click', async () => {
          yes.disabled = true;
          const out = await letIn({ projectId, account, email: p.email });
          waitMsg.textContent = out.ok ? `${p.email} has cloud play now.` : why(out);
          if (out.ok) await paint(); else yes.disabled = false;
        });
        const no = n('button', 'quiet danger', 'Remove'); no.type = 'button';
        no.addEventListener('click', async () => {
          if (no.dataset.armed !== '1') { no.dataset.armed = '1'; no.textContent = 'Confirm'; setTimeout(() => { no.dataset.armed = ''; no.textContent = 'Remove'; }, 4000); return; }
          const out = await leaveWaitlist({ projectId, account, email: p.email });
          waitMsg.textContent = out.ok ? `${p.email} is off the waitlist.` : why(out);
          if (out.ok) await paint();
        });
        acts.append(yes, no);
        li.append(n('span', 'who', p.email), meta, acts);
        waitList.append(li);
      }
    });
    list.replaceChildren(n('li', 'none', 'Reading…'));
    const r = await listPeople({ projectId, account });
    list.replaceChildren();
    if (!r.ok) { list.append(n('li', 'none', why(r))); return; }
    if (!r.people.length) { list.append(n('li', 'none', 'Nobody yet. You are an admin by your own sign-in.')); return; }
    for (const p of r.people) {
      const li = n('li'); li.dataset.email = p.email;
      const meta = n('span', 'meta');
      meta.append(n('span', 'rights', rightsWords(p.rights).toUpperCase()), document.createTextNode([p.note, p.at && `added ${when(p.at)}`, p.by && p.by !== emailId(account.email) && `by ${p.by}`].filter(Boolean).map((s) => ` · ${s}`).join('')));
      const acts = n('span', 'acts');
      const edit = n('button', 'quiet', 'Edit'); edit.type = 'button'; edit.addEventListener('click', () => fill(p));
      const drop = n('button', 'quiet danger', 'Remove'); drop.type = 'button';
      drop.addEventListener('click', async () => {
        if (drop.dataset.armed !== '1') { drop.dataset.armed = '1'; drop.textContent = 'Confirm'; setTimeout(() => { drop.dataset.armed = ''; drop.textContent = 'Remove'; }, 4000); return; }
        const out = await revoke({ projectId, account, email: p.email });
        msg.textContent = out.ok ? `${p.email} has no rights now.` : why(out);
        if (out.ok) await paint();
      });
      acts.append(edit, drop);
      li.append(n('span', 'who', p.email), meta, acts);
      list.append(li);
    }
  }
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!emailOk(email.value)) { msg.textContent = 'That is not an email address.'; email.focus(); return; }
    const rights = Object.entries(boxes).filter(([, b]) => b.checked).map(([r]) => r);
    save.disabled = true; msg.textContent = 'Saving…';
    const out = await grant({ projectId, account, email: email.value, rights, note: note.value });
    save.disabled = false;
    msg.textContent = out.ok ? (rights.length ? `${emailId(email.value)}: ${rightsWords(rights)}.` : `${emailId(email.value)} has no rights now.`) : why(out);
    if (out.ok) { email.value = ''; note.value = ''; boxes.admin.checked = false; boxes.cloud.checked = true; await paint(); }
  });
  admin = { paint };
  void paint();
}
export async function refreshAdmin() { await admin?.paint(); }
