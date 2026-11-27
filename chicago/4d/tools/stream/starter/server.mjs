/**
 * T-3794 / T-3795: the stream starter, a Cloud Run service in chicago-stream (deployed by
 * tools/stream/setup.sh). Plain node:http, no dependencies.
 *
 *   POST /start   { year }     a signed-in player with cloud play asks for a machine
 *   GET  /status?name=…        is it ready yet; when it is, the link (only for that player)
 *   POST /stop    { name }     end it now (the player, or an admin)
 *   POST /budget?secret=…      the budget's Pub/Sub push: at 100 % every machine stops and the
 *                              starter refuses until next month or until the owner resumes it
 *   POST /resume               an admin turns the starter back on after a budget stop
 *   POST /probe?secret=…       Cloud Scheduler, hourly for a week: is a GPU machine to be had?
 *   GET  /probe                that week's tally (no names, no addresses)
 *   GET  /health
 *
 * Every player call carries `Authorization: Bearer <Firebase ID token>`.
 */
import http from 'node:http';
import { verifyIdToken, rightsOf, google, usage, startMachine, playerLabel, emailId, monthKey, sslipHost, probe, probeRow, probeSummary, PROBE_DAYS, SPEND_CAP, HOUR_COST, YEARS } from './lib.mjs';

const env = process.env;
const PROJECT = env.GOOGLE_CLOUD_PROJECT || env.PROJECT || 'chicago-stream';
const BUCKET = env.LEDGER_BUCKET || `${PROJECT}-ledger`;
const MACHINE_SA = env.MACHINE_SA || `stream-machine@${PROJECT}.iam.gserviceaccount.com`;
const MAX_MACHINES = Number(env.MAX_MACHINES || 1);
const SITE = env.SITE || 'https://chicago.polecat.live/4d/';
const ORIGINS = (env.ALLOWED_ORIGINS || 'https://chicago.polecat.live,https://dev.chicago.polecat.live').split(',');
const g = google({ project: PROJECT });

const send = (res, origin, status, body) => {
  const h = { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', Vary: 'Origin' };
  if (ORIGINS.includes(origin)) Object.assign(h, { 'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Headers': 'Authorization, Content-Type', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS' });
  res.writeHead(status, h); res.end(JSON.stringify(body));
};
const readBody = (req) => new Promise((resolve) => { let s = ''; req.on('data', (c) => { s += c; if (s.length > 1e5) req.destroy(); }); req.on('end', () => { try { resolve(s ? JSON.parse(s) : {}); } catch { resolve({}); } }); });

/** Read-modify-write the month's ledger, retrying a lost race. */
async function withLedger(fn) {
  const month = monthKey();
  for (let i = 0; i < 5; i++) {
    const { generation, data } = await g.ledger(BUCKET, month);
    const next = fn(structuredClone(data));
    if (!next) return data;
    if (await g.saveLedger(BUCKET, month, generation, next)) return next;
  }
  throw new Error('ledger busy');
}
/** Delete stopped machines and close the ledger's sessions whose machine is gone. */
async function sweep() {
  const all = await g.machines();
  for (const m of all) if (m.status === 'TERMINATED' || m.status === 'STOPPED') await g.remove(m.zone, m.name);
  const live = new Set(all.filter((m) => m.status !== 'TERMINATED' && m.status !== 'STOPPED').map((m) => m.name));
  await withLedger((d) => {
    let changed = false;
    for (const [name, s] of Object.entries(d.sessions ?? {})) {
      if (!s.end && !live.has(name)) { s.end = new Date(Math.min(Date.now(), Date.parse(s.start) + 7200e3)).toISOString(); changed = true; }
    }
    return changed ? d : null;
  });
  return all.filter((m) => live.has(m.name));
}

async function player(req) {
  const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  const claims = await verifyIdToken(token);
  const rights = await rightsOf({ token, email: claims.email });
  return { token, email: emailId(claims.email), label: playerLabel(claims.email), ...rights };
}
const describe = async (m) => {
  const ready = m.status === 'RUNNING' && m.ip ? await g.ready(m.zone, m.name) : false;
  return { name: m.name, year: m.labels.year, status: m.status, ready, link: ready ? `https://${sslipHost(m.ip)}/?k=${m.token}` : '' };
};

const routes = {
  'GET /health': async () => [200, { ok: true }],
  'POST /start': async (req) => {
    const p = await player(req);
    if (!p.cloud) return [403, { ok: false, why: 'no cloud play' }];
    if (!p.open && !p.admin) return [409, { ok: false, why: 'closed' }];
    const body = await readBody(req);
    const year = YEARS.includes(String(body.year)) ? String(body.year) : '1904';
    const { data } = await g.ledger(BUCKET, monthKey());
    if (data.stopped) return [503, { ok: false, why: 'budget', message: 'Cloud play has stopped for this month: the spending limit was reached.' }];
    const used = usage(data);
    // A new session may run two hours: start one only if that still fits under the cap.
    if (used.dollars + 2 * HOUR_COST.spot > SPEND_CAP) return [503, { ok: false, why: 'hours', message: `This month's cloud hours are used ($${used.dollars.toFixed(0)} of $${SPEND_CAP}).` }];
    const live = await sweep();
    const mine = live.find((m) => m.labels.player === p.label);
    if (mine) return [200, { ok: true, already: true, ...(await describe(mine)) }];
    if (live.length >= MAX_MACHINES) return [429, { ok: false, why: 'busy', message: `All ${MAX_MACHINES} cloud machine${MAX_MACHINES === 1 ? ' is' : 's are'} in use. Try again in a few minutes.` }];
    const t0 = Date.now();
    const out = await startMachine(g, { year, player: p.label, machineSA: MACHINE_SA, admin: p.admin, site: SITE });
    if (!out.ok) return [503, { ok: false, why: out.why, message: out.why === 'quota' ? 'Google has not given this project the graphics capacity yet.' : 'Google has no free graphics machine anywhere in the US just now. Try again later.' }];
    await withLedger((d) => { d.sessions ??= {}; d.sessions[out.name] = { start: new Date(t0).toISOString(), year, spot: out.spot, gpu: out.gpu, by: p.admin ? 'admin' : 'player' }; return d; });
    return [200, { ok: true, name: out.name, year, status: 'STARTING', ready: false, spot: out.spot, gpu: out.gpu, spentThisMonth: Number(used.dollars.toFixed(2)) }];
  },
  'GET /status': async (req, url) => {
    const p = await player(req);
    const m = (await g.machines()).find((x) => x.name === url.searchParams.get('name'));
    if (!m || (m.labels.player !== p.label && !p.admin)) return [404, { ok: false, why: 'gone' }];
    return [200, { ok: true, ...(await describe(m)) }];
  },
  'POST /stop': async (req) => {
    const p = await player(req);
    const { name } = await readBody(req);
    const m = (await g.machines()).find((x) => x.name === name);
    if (!m || (m.labels.player !== p.label && !p.admin)) return [404, { ok: false, why: 'gone' }];
    await g.remove(m.zone, m.name);
    await withLedger((d) => { const s = d.sessions?.[m.name]; if (!s || s.end) return null; s.end = new Date().toISOString(); return d; });
    return [200, { ok: true }];
  },
  'POST /budget': async (req, url) => {
    if (!env.BUDGET_SECRET || url.searchParams.get('secret') !== env.BUDGET_SECRET) return [403, { ok: false }];
    const body = await readBody(req);
    let note = {};
    try { note = JSON.parse(Buffer.from(body.message?.data || '', 'base64').toString('utf8')); } catch { /* not a budget note */ }
    if (!(Number(note.costAmount) >= Number(note.budgetAmount) && Number(note.budgetAmount) > 0)) return [200, { ok: true, stopped: false }];
    for (const m of await g.machines()) await g.remove(m.zone, m.name);
    await withLedger((d) => { d.stopped = true; d.stoppedAt = new Date().toISOString(); d.stoppedCost = Number(note.costAmount); return d; });
    return [200, { ok: true, stopped: true }];
  },
  'POST /probe': async (req, url) => {
    if (!env.BUDGET_SECRET || url.searchParams.get('secret') !== env.BUDGET_SECRET) return [403, { ok: false }];
    const now = new Date();
    const { data: log } = await g.object(BUCKET, 'probe/log.json', { rows: [] });
    if (log.until && now.toISOString() > log.until) return [200, { ok: true, done: true }];
    const { data } = await g.ledger(BUCKET, monthKey());
    if (data.stopped) return [200, { ok: true, skipped: 'budget' }];
    // A player's machine holds the project's one GPU: count the hour as busy, try nothing.
    const live = (await g.machines()).filter((m) => m.status !== 'TERMINATED' && m.status !== 'STOPPED');
    const out = live.length ? { spot: null, demand: 'not tried', busy: true, tries: [] } : await probe(g);
    const row = probeRow(now.toISOString(), out);
    for (let i = 0; i < 5; i++) {
      const { generation, data: cur } = await g.object(BUCKET, 'probe/log.json', { rows: [] });
      cur.started ??= now.toISOString();
      cur.until ??= new Date(now.getTime() + PROBE_DAYS * 86400e3).toISOString();
      cur.rows = [...(cur.rows ?? []), row];
      if (await g.saveObject(BUCKET, 'probe/log.json', generation, cur)) break;
    }
    return [200, { ok: true, ...row }];
  },
  'GET /probe': async () => {
    const { data: log } = await g.object(BUCKET, 'probe/log.json', { rows: [] });
    return [200, { ok: true, ...probeSummary(log), last: (log.rows ?? []).slice(-6) }];
  },
  'POST /resume': async (req) => {
    const p = await player(req);
    if (!p.admin) return [403, { ok: false, why: 'admin only' }];
    await withLedger((d) => { if (!d.stopped) return null; d.stopped = false; d.resumedAt = new Date().toISOString(); return d; });
    return [200, { ok: true }];
  },
};

http.createServer(async (req, res) => {
  const origin = req.headers.origin || '';
  const url = new URL(req.url, 'http://x');
  if (req.method === 'OPTIONS') return send(res, origin, 204, {});
  const route = routes[`${req.method} ${url.pathname}`];
  if (!route) return send(res, origin, 404, { ok: false, why: 'no such call' });
  try {
    const [status, body] = await route(req, url);
    send(res, origin, status, body);
  } catch (err) {
    const auth = /token|signature|expired|project|algorithm|key|unverified|email-only/.test(err.message);
    console.error(JSON.stringify({ severity: auth ? 'WARNING' : 'ERROR', message: err.message, path: url.pathname }));
    send(res, origin, auth ? 401 : 500, { ok: false, why: auth ? 'sign in' : 'failed' });
  }
}).listen(Number(env.PORT || 8080));
