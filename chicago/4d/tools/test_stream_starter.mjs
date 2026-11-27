/**
 * test_stream_starter.mjs — T-3793..T-3795: cloud play's starter, machine scripts and the launch
 * page's cloud button, against a fake Google (no network, no keys).
 *
 *   node tools/test_stream_starter.mjs
 *
 * Holds: a Firebase ID token is checked by signature, project, expiry, provider and verified
 * address; rights come from Firestore read as the player; a machine is a Spot L4 with Google's
 * own two-hour end, tagged for the firewall, with the session in its metadata; Spot tries each
 * zone and only an admin falls back to on demand; the month's hours count a vanished session at
 * most two hours; the scripts parse, hold no key and gate the stream by the session's token;
 * the launch page's startCloud waits for ready and hands back only an sslip.io link.
 */
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import * as lib from './stream/starter/lib.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const STREAM = path.join(HERE, 'stream');
let passed = 0;
const ok = (cond, what) => { assert.ok(cond, what); passed++; };

// ---- ID tokens ---------------------------------------------------------------------------
const { privateKey, publicKey } = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
const pem = publicKey.export({ type: 'spki', format: 'pem' });
const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
const now = Math.floor(Date.now() / 1000);
const sign = (claims, { kid = 'k1', key = privateKey, alg = 'RS256' } = {}) => {
  const head = b64({ alg, kid, typ: 'JWT' }), body = b64(claims);
  return `${head}.${body}.${crypto.createSign('RSA-SHA256').update(`${head}.${body}`).sign(key).toString('base64url')}`;
};
const good = { aud: 'chicago-61643', iss: 'https://securetoken.google.com/chicago-61643', sub: 'u1', iat: now - 10, exp: now + 3000, email: 'Ann@School.org', email_verified: true, firebase: { sign_in_provider: 'google.com' } };
const certFetch = async (url) => { assert.match(String(url), /securetoken@system/); return { ok: true, json: async () => ({ k1: pem }) }; };
lib.resetCertCache();
const claims = await lib.verifyIdToken(sign(good), { fetchFn: certFetch });
ok(claims.email === 'Ann@School.org', 'a good token passes');
const refuses = async (token, why) => { await assert.rejects(lib.verifyIdToken(token, { fetchFn: certFetch }), undefined, why); passed++; };
await refuses(sign({ ...good, aud: 'other' }), 'another project');
await refuses(sign({ ...good, exp: now - 5 }), 'expired');
await refuses(sign({ ...good, email_verified: false }), 'an unverified address');
await refuses(sign({ ...good, firebase: { sign_in_provider: 'anonymous' } }), 'an email-only sign-in');
await refuses(sign(good, { key: crypto.generateKeyPairSync('rsa', { modulusLength: 2048 }).privateKey }), 'a forged signature');
await refuses(sign(good, { kid: 'nope' }), 'an unknown key');
await refuses(`${b64({ alg: 'none', kid: 'k1' })}.${b64(good)}.`, 'alg none');
await assert.rejects(lib.verifyIdToken('x.y.z', { fetchFn: certFetch }), /not a token/, 'garbage is "not a token" (a 401, not a 500)'); passed++;

// ---- Rights, as the player ---------------------------------------------------------------
const fsFake = ({ cloud = false, admin = false, open = false }) => async (url, init = {}) => {
  assert.equal(init.headers.Authorization, 'Bearer T', 'Firestore is read with the player\'s own token');
  const u = String(url);
  if (u.endsWith(':runQuery')) return { ok: admin, json: async () => [] };
  if (u.includes('/access/')) { assert.ok(u.endsWith('/access/ann%40school.org')); return cloud ? { ok: true, json: async () => ({ fields: { rights: { arrayValue: { values: [{ stringValue: 'cloud' }] } } } }) } : { ok: false, status: 404, json: async () => ({}) }; }
  if (u.endsWith('/launch/cloud')) return { ok: true, json: async () => ({ fields: { ready: { booleanValue: open } } }) };
  throw new Error(u);
};
ok(JSON.stringify(await lib.rightsOf({ token: 'T', email: 'Ann@School.org', fetchFn: fsFake({}) })) === '{"admin":false,"cloud":false,"open":false}', 'a stranger has nothing');
ok((await lib.rightsOf({ token: 'T', email: 'ann@school.org', fetchFn: fsFake({ cloud: true, open: true }) })).cloud, 'a grant gives cloud play');
const adm = await lib.rightsOf({ token: 'T', email: 'ann@school.org', fetchFn: fsFake({ admin: true }) });
ok(adm.admin && adm.cloud && !adm.open, 'an admin has cloud play, even while it is closed');

// ---- The machine -------------------------------------------------------------------------
const body = lib.machineBody({ project: 'p', zone: 'us-central1-b', name: 'stream-x', year: '1871', token: 'ab'.repeat(24), player: lib.playerLabel('ann@school.org'), spot: true, machineSA: 'm@p.iam.gserviceaccount.com' });
ok(body.machineType.endsWith('/g2-standard-4') && body.scheduling.provisioningModel === 'SPOT', 'a Spot g2-standard-4');
ok(body.scheduling.maxRunDuration.seconds === '7200' && body.scheduling.instanceTerminationAction === 'DELETE', 'Google itself deletes it after two hours');
ok(body.disks[0].initializeParams.sourceImage === 'projects/p/global/images/family/chicago-stream' && body.disks[0].autoDelete, 'from the image family, its disk going with it');
ok(body.tags.items.includes('chicago-stream') && body.labels.app === 'chicago-stream', 'tagged for the firewall and labelled for the starter');
ok(body.networkInterfaces[0].accessConfigs[0].networkTier === 'STANDARD', 'Standard network tier (the cheaper egress)');
const meta = Object.fromEntries(body.metadata.items.map((m) => [m.key, m.value]));
ok(meta['chicago-url'] === 'https://chicago.polecat.live/4d/1871/' && meta['enable-guest-attributes'] === 'TRUE', 'opens the chosen year');
ok(!/@/.test(body.labels.player) && body.labels.player.length === 20, 'the player label holds no address');
ok(lib.townURL('9999') === 'https://chicago.polecat.live/4d/1904/', 'an unknown year opens 1904');
ok(lib.sslipHost('34.1.2.3') === '34-1-2-3.sslip.io', 'the sslip.io host');

// Spot in each zone, then (admin only) on demand.
const fakeG = (outcomes) => {
  const tried = [];
  return { tried, project: 'p',
    insert: async (zone, b) => { tried.push(`${zone}:${b.scheduling.provisioningModel}`); return { ok: true, body: { name: `op-${tried.length}`, status: 'RUNNING' } }; },
    operation: async () => { const o = outcomes.shift(); return { body: o ? { status: 'DONE', error: { errors: [o] } } : { status: 'DONE' } }; } };
};
const noWait = async () => {};
const stockout = { code: 'ZONE_RESOURCE_POOL_EXHAUSTED', message: 'no L4' };
let g = fakeG([stockout, stockout]);
let r = await lib.startMachine(g, { year: '1904', player: 'x', wait: noWait });
ok(r.ok && r.zone === 'us-central1-c' && r.spot && /^[0-9a-f]{48}$/.test(r.token), `Spot moves on to the next zone (${g.tried})`);
const SPOT_TRIES = lib.GPUS.reduce((n, x) => n + x.zones.length, 0);
const everywhere = () => Array.from({ length: SPOT_TRIES }, () => stockout);
ok(lib.ZONES[0].startsWith('us-central1') && lib.ZONES.every((z) => z.startsWith('us-')), 'L4 zones: Iowa first, then the rest of the US');
g = fakeG(everywhere());
r = await lib.startMachine(g, { year: '1904', player: 'x', wait: noWait });
ok(!r.ok && r.why === 'no capacity' && g.tried.length === SPOT_TRIES && g.tried.every((t) => t.endsWith('SPOT')), 'a player never gets an on-demand machine');
g = fakeG(everywhere());
r = await lib.startMachine(g, { year: '1904', player: 'x', admin: true, wait: noWait });
ok(r.ok && !r.spot && r.gpu === 'l4' && g.tried[SPOT_TRIES] === 'us-central1-a:STANDARD', 'an admin falls back to on demand');
g = fakeG(lib.ZONES.map(() => stockout));
r = await lib.startMachine(g, { year: '1904', player: 'x', wait: noWait });
ok(r.ok && r.spot && r.gpu === 't4' && r.zone === lib.T4_ZONES[0], `no L4 anywhere: a Spot T4 next (${r.gpu} ${r.zone})`);
const t4 = lib.machineBody({ project: 'p', zone: 'us-east4-b', name: 'x', year: '1904', token: 'ab'.repeat(24), player: 'x', gpu: lib.GPUS[1] });
ok(t4.machineType.endsWith('/n1-standard-4') && t4.guestAccelerators[0].acceleratorType === 'zones/us-east4-b/acceleratorTypes/nvidia-tesla-t4' && t4.scheduling.onHostMaintenance === 'TERMINATE' && t4.labels.gpu === 't4', 'a T4 machine carries its accelerator');
ok(!body.guestAccelerators && body.labels.gpu === 'l4', 'an L4 machine has its GPU built in');
g = fakeG([{ code: 'QUOTA_EXCEEDED', message: 'GPUS_ALL_REGIONS' }]);
r = await lib.startMachine(g, { year: '1904', player: 'x', wait: noWait });
ok(!r.ok && r.why === 'quota' && g.tried.length === 1, 'a quota refusal stops at once');
g = fakeG([{ code: 'QUOTA_EXCEEDED', message: "Quota 'NVIDIA_L4_GPUS' exceeded. Limit: 0.0 in region us-east4." }]);
r = await lib.startMachine(g, { year: '1904', player: 'x', wait: noWait });
ok(r.ok && g.tried.length === 2, 'a region\'s own quota only rules out that region');

ok(lib.gpusFrom('').length === 1 && lib.gpusFrom('')[0].gpu === 'l4' && lib.gpusFrom('l4,t4').length === 2 && lib.gpusFrom('nonsense')[0].gpu === 'l4', 'players get the measured L4 only unless GPUS=l4,t4; a bad setting never leaves them without an L4');
ok(/GPUS=\$\{GPUS:-l4\}/.test(fs.readFileSync(path.join(STREAM, 'setup.sh'), 'utf8')), 'setup deploys L4 only by default');
g = fakeG(lib.ZONES.map(() => stockout));
r = await lib.startMachine(g, { year: '1904', player: 'x', gpus: lib.gpusFrom('l4'), wait: noWait });
ok(!r.ok && g.tried.length === lib.ZONES.length, 'with the T4 dropped, no L4 means no machine');

// ---- The availability probe ----------------------------------------------------------------
ok(lib.refusal("ZONE_RESOURCE_POOL_EXHAUSTED The zone does not have enough resources") === 'stockout'
  && lib.refusal("QUOTA_EXCEEDED Quota 'GPUS_ALL_REGIONS' exceeded") === 'busy'
  && lib.refusal("QUOTA_EXCEEDED Quota 'NVIDIA_T4_GPUS' exceeded. Limit: 0.0 in region northamerica-northeast1") === 'quota'
  && lib.refusal("Invalid value for field 'resource.machineType': does not exist in zone") === 'not offered', 'refusals read as stockout, busy, quota, not offered');
const probeG = (outcomes) => {
  const made = [], removed = [];
  return { made, removed, project: 'p',
    insert: async (zone, b) => { made.push(`${b.labels.gpu}@${zone}:${b.scheduling.provisioningModel}`); return { ok: true, body: { name: 'op', status: 'RUNNING' } }; },
    operation: async () => { const o = outcomes.shift(); return { body: o ? { status: 'DONE', error: { errors: [o] } } : { status: 'DONE' } }; },
    remove: async (zone, name) => { removed.push(name); return { ok: true }; } };
};
const pb = lib.probeBody({ zone: 'us-east4-a', name: 'probe-x', gpu: lib.GPUS[1], spot: true });
ok(pb.labels.app === 'chicago-stream-probe' && pb.scheduling.maxRunDuration.seconds === '600' && pb.scheduling.instanceTerminationAction === 'DELETE'
  && !pb.networkInterfaces[0].accessConfigs && pb.disks[0].initializeParams.diskSizeGb === '10', 'a probe machine: no address, a small disk, gone by itself in ten minutes');
let pg = probeG([stockout, stockout]);
let po = await lib.probe(pg, { wait: noWait });
ok(po.spot?.gpu === 'l4' && po.spot.zone === 'us-central1-c' && po.demand === 'not tried' && pg.removed.length === 1 && pg.made.length === 3, `a free Spot L4 ends the probe, deleted at once (${pg.made})`);
const allSpot = lib.PROBE_ZONES.l4.length + lib.PROBE_ZONES.t4.length;
ok(lib.PROBE_ZONES.l4.some((z) => z.startsWith('northamerica-')) && lib.PROBE_ZONES.t4.some((z) => z.startsWith('northamerica-')), 'Canada is probed');
pg = probeG(Array.from({ length: allSpot }, () => stockout));
po = await lib.probe(pg, { wait: noWait });
ok(po.spot === null && po.demand?.gpu === 'l4' && pg.made[allSpot].endsWith(':STANDARD') && pg.removed.length === 1, 'no Spot anywhere: on demand is tried, and that machine deleted');
pg = probeG([{ code: 'QUOTA_EXCEEDED', message: "Quota 'GPUS_ALL_REGIONS' exceeded" }]);
po = await lib.probe(pg, { wait: noWait });
ok(po.busy && pg.made.length === 1, 'the project\'s GPU in use: the probe stops and says busy');
const row = lib.probeRow('2026-11-28T00:07:00Z', { spot: { gpu: 't4', zone: 'us-east4-b' }, demand: 'not tried', busy: false, tries: [{ gpu: 'l4', zone: 'us-central1-a', spot: true, outcome: 'stockout' }, { gpu: 't4', zone: 'us-east4-b', spot: true, outcome: 'ok' }] });
ok(row.spot === 't4@us-east4-b' && row.refused.stockout[0] === 'l4@us-central1-a', 'a log row names what was found and what refused');
const sum = lib.probeSummary({ rows: [row, { ...row, spot: 'none', demand: 'none' }, { ...row, busy: true, spot: 'none' }] });
ok(sum.probes === 3 && sum.busy === 1 && sum.spot === 1 && sum.anyMachine === 1 && sum.byZone['t4@us-east4-b'] === 1, `the week's tally (${JSON.stringify(sum)})`);

// ---- Hours -------------------------------------------------------------------------------
const t = Date.parse('2026-12-10T12:00:00Z');
const ledger = { sessions: {
  a: { start: '2026-12-10T09:00:00Z', end: '2026-12-10T09:30:00Z' },
  b: { start: '2026-12-01T00:00:00Z' },
  c: { start: '2026-12-10T11:00:00Z' },
} };
ok(Math.abs(lib.hoursUsed(ledger, t) - 3.5) < 1e-9, `hours: 0.5 closed + 2 capped + 1 running = 3.5 (${lib.hoursUsed(ledger, t)})`);
ledger.sessions.c.spot = false;
ok(Math.abs(lib.usage(ledger, t).dollars - (2.5 * 0.75 + 1 * 1.05)) < 1e-9, `dollars count on-demand hours at their own price (${lib.usage(ledger, t).dollars})`);
ok(lib.SPEND_CAP === 90, `the starter stops at 90 % of the $100 budget (${lib.SPEND_CAP})`);

// ---- The scripts -------------------------------------------------------------------------
for (const f of ['setup.sh', 'build-image.sh', 'machine/provision.sh', 'machine/session.sh']) {
  execFileSync('bash', ['-n', path.join(STREAM, f)]);
  passed++;
}
const all = ['setup.sh', 'build-image.sh', 'machine/provision.sh', 'machine/session.sh', 'starter/lib.mjs', 'starter/server.mjs', 'README.md']
  .map((f) => fs.readFileSync(path.join(STREAM, f), 'utf8')).join('\n');
ok(!/BEGIN (RSA )?PRIVATE KEY|"private_key"|AIza[0-9A-Za-z_-]{30}/.test(all), 'no key in tools/stream');
const session = fs.readFileSync(path.join(STREAM, 'machine/session.sh'), 'utf8');
// Caddy reads a first argument starting with / as a path matcher: `redir / 302` sent players to
// "302" (seen on the first test machine, 2026-11-27). Every redir names its matcher.
ok(/redir \* \/ 302/.test(session) && !/redir \/ /.test(session), 'the link sends the player to / (redir names its matcher)');
// The GPU draws and encodes (2026-11-27: Google's driver lacked GL and NVENC, and a stale CDI list
// hid them from the container, so the town was drawn and encoded by the CPU).
const provision = fs.readFileSync(path.join(STREAM, 'machine/provision.sh'), 'utf8');
ok(/libnvidia-gl-\$DRV-server/.test(provision) && /libnvidia-encode-\$DRV-server/.test(provision), 'the image adds the driver\'s graphics and encoder parts');
ok(/nvidia-ctk cdi generate/.test(session) && /--device \/dev\/nvidia-modeset/.test(session) && /DRI_NODE=\/dev\/dri\/renderD128/.test(session), 'the town container gets the GPU to draw and encode');
ok(/SELKIES_ENABLE_CLIPBOARD=false\|locked/.test(session) && /SELKIES_UI_SHOW_SIDEBAR=false\|locked/.test(session) && /SELKIES_FILE_TRANSFERS=none/.test(session), 'the player gets the town only: no clipboard, side panel or file transfer');
ok(/@ok header_regexp session Cookie chicago_stream=\$TOKEN/.test(session) && /respond "This cloud machine belongs to another session\." 403/.test(session), 'the stream answers only the session cookie');
ok(/-p 127\.0\.0\.1:3000:3000/.test(session), 'the streamer listens only behind Caddy');
ok(/\[\[ "\$TOKEN" =~ \^\[0-9a-f\]\{32,\}\$ \]\]/.test(session), 'the token is checked before it goes into the Caddyfile');
ok(/"\$idle" -ge 600/.test(session), 'ten idle minutes end a session');
const server = fs.readFileSync(path.join(STREAM, 'starter/server.mjs'), 'utf8');
ok(/'POST \/probe'[\s\S]*BUDGET_SECRET/.test(server) && /scheduler jobs create http chicago-stream-probe/.test(fs.readFileSync(path.join(STREAM, 'setup.sh'), 'utf8')), 'the probe answers only the scheduler, which setup.sh makes');
ok(/BUDGET_SECRET/.test(server) && /costAmount\) >= Number\(note\.budgetAmount\)/.test(server), 'the budget push stops machines at 100 %');
ok(/usage\(data\)/.test(server) && /SPEND_CAP/.test(server), 'the starter checks the month\'s spending before it starts one');
ok(!/chicago-61643/.test(fs.readFileSync(path.join(STREAM, 'setup.sh'), 'utf8')), 'setup touches nothing in the Firebase project');

// ---- The launch page's cloud button ------------------------------------------------------
const { startCloud } = await import('../renderers/web/portal/launch-access.js');
const account = { idToken: async () => 'T' };
r = await startCloud({ year: '1904', account, config: {} });
ok(!r.ok && /opening soon/.test(r.title), 'no starter configured: opening soon');
let polls = 0;
const starter = async (url, init) => {
  assert.equal(init.headers.Authorization, 'Bearer T');
  if (String(url).endsWith('/start')) { assert.equal(JSON.parse(init.body).year, '1835'); return { status: 200, json: async () => ({ ok: true, name: 'stream-1', status: 'STARTING' }) }; }
  polls++;
  return { status: 200, json: async () => (polls < 3 ? { ok: true, status: 'RUNNING', ready: false } : { ok: true, status: 'RUNNING', ready: true, link: `https://34-1-2-3.sslip.io/?k=${'ab'.repeat(24)}` }) };
};
const seen = [];
r = await startCloud({ year: '1835', account, config: { streamStarter: 'https://s.run.app/' }, fetchFn: starter, wait: noWait, progress: (s, st) => seen.push(st) });
ok(r.ok && r.link.startsWith('https://34-1-2-3.sslip.io/?k=') && polls === 3 && seen.length === 3, 'it waits for ready and hands back the link');
ok(r.gpu === 'l4' && /L4 GRAPHICS · FULL DETAIL/.test(r.machine), `the player is told what machine they got (${r.machine})`);
r = await startCloud({ year: '1835', account, config: { streamStarter: 'https://s.run.app' }, wait: noWait,
  fetchFn: async (url) => (String(url).endsWith('/start') ? { status: 200, json: async () => ({ ok: true, name: 'n', gpu: 't4' }) } : { status: 200, json: async () => ({ ok: true, ready: true, gpu: 't4', link: `https://34-1-2-3.sslip.io/?k=${'ab'.repeat(24)}` }) }) });
ok(r.ok && /T4 GRAPHICS · AN OLDER CARD/.test(r.machine), 'a T4 is named as the older card');
ok(/CLOUD MACHINE READY · \$\{r\.machine/.test(fs.readFileSync(path.join(STREAM, '../../renderers/web/portal/launch.js'), 'utf8')), 'the launch page shows it before the stream opens');
r = await startCloud({ year: '1835', account, config: { streamStarter: 'https://s.run.app' }, wait: noWait,
  fetchFn: async (url) => (String(url).endsWith('/start') ? { status: 200, json: async () => ({ ok: true, name: 'n' }) } : { status: 200, json: async () => ({ ok: true, ready: true, link: 'https://evil.example/' }) }) });
ok(!r.ok, 'a link that is not an sslip.io stream is never followed');
r = await startCloud({ year: '1835', account, config: { streamStarter: 'https://s.run.app' }, fetchFn: async () => ({ status: 429, json: async () => ({ ok: false, why: 'busy', message: 'All 1 cloud machine is in use.' }) }) });
ok(!r.ok && r.title === 'Every cloud machine is in use', 'busy is said plainly');

console.log(`PASS stream starter: ${passed} checks (tokens, rights as the player, the machine, zones and on demand, hours and dollars, scripts, the cloud button)`);
