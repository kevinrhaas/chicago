/**
 * T-3794 / T-3795: the stream starter's logic, kept apart from the HTTP server so the gate can
 * drive it with a fake Google (tools/test_stream_starter.mjs). No dependencies: Node 20+.
 *
 * Who may start a machine is decided by the same Firestore rules the launch page reads
 * (renderers/web/js/launch-rights.js, docs/SIGN-IN.md): the starter asks Firestore *with the
 * player's own ID token*, so it reads nothing in chicago-61643 beyond what that player could read
 * themself (T-3795 (e)). Its one grant there (the owner's yes, 2026-11-27) is to have IAM sign a
 * one-hour sign-in pass for the player who pressed the button (signInPass, below).
 *
 *   cloud play   access/<email> lists 'cloud', or the player is an admin
 *   admin        the rules let them list access/ (the owner, or a grant naming admin)
 *   open         launch/cloud.ready is true; an admin may start a machine even while it is not
 *
 * A machine is one Spot g2-standard-4 (one NVIDIA L4) from the image family `chicago-stream`
 * (tools/stream/build-image.sh), deleted by Google itself after two hours (maxRunDuration) and
 * by its own idle watch after ten minutes with nobody connected (machine/session.sh).
 */
import crypto from 'node:crypto';

export const FIREBASE_PROJECT = 'chicago-61643';
/** L4 zones, nearest Chicago first. us-central1 (Iowa) had no L4 free at all on 2026-11-27, Spot
 * or on demand, so the starter goes on to Virginia, South Carolina, Oregon and Las Vegas. */
export const ZONES = ['us-central1-a', 'us-central1-b', 'us-central1-c', 'us-east4-a', 'us-east4-c', 'us-east1-b', 'us-east1-c', 'us-east1-d',
  'us-west1-a', 'us-west1-b', 'us-west4-a', 'us-west4-c'];
export const MACHINE_TYPE = 'g2-standard-4';
/** T4 zones, nearest first. When no L4 is free anywhere (2026-11-27: none, and no T4 either, for an
 * hour) the starter tries a T4 on an n1-standard-4: older and slower, still a real GPU, and cheaper
 * (the ledger counts it at the L4's price, so the cap only errs on the safe side). */
export const T4_ZONES = ['us-central1-a', 'us-central1-b', 'us-central1-c', 'us-central1-f', 'us-east4-a', 'us-east4-b', 'us-east4-c',
  'us-east1-c', 'us-east1-d', 'us-west1-a', 'us-west1-b', 'us-west4-a', 'us-west4-b'];
export const GPUS = Object.freeze([
  { gpu: 'l4', machineType: MACHINE_TYPE, zones: ZONES },
  { gpu: 't4', machineType: 'n1-standard-4', accelerator: 'nvidia-tesla-t4', zones: T4_ZONES },
]);
/** The GPUs players may be given, from the starter's GPUS setting: 'l4' by default, because the
 * L4 is the one measured good (2026-11-27). 'l4,t4' lets the older T4 stand in when no L4 is
 * free, once it has been measured too; no code change either way. Never empty: a player always
 * gets a GPU or nothing. */
export const gpusFrom = (setting) => {
  const want = String(setting || 'l4').split(',').map((x) => x.trim());
  const out = GPUS.filter((x) => want.includes(x.gpu));
  return out.length ? out : [GPUS[0]];
};
export const IMAGE_FAMILY = 'chicago-stream';
export const MAX_RUN_SECONDS = 2 * 3600;
export const YEARS = ['1835', '1904', '1812', '1871'];
/** All in, an L4 hour with its streamed bytes costs about $0.71 on Spot and $1.00 on demand
 * (plan, 2026-11-23), rounded up here. The starter stops at 90 % of the $100 budget by its own
 * count, since the budget's alerts can lag by hours. */
export const HOUR_COST = Object.freeze({ spot: 0.75, demand: 1.05 });
export const MONTHLY_BUDGET = 100;
export const SPEND_CAP = MONTHLY_BUDGET * 0.9;

const b64url = (s) => Buffer.from(s.replace(/-/g, '+').replace(/_/g, '/'), 'base64');
export const emailId = (e) => String(e ?? '').trim().toLowerCase();
/** A label value for the player: labels may not hold '@' or '.', and should not hold an address. */
export const playerLabel = (email) => crypto.createHash('sha256').update(emailId(email)).digest('hex').slice(0, 20);
export const monthKey = (d = new Date()) => d.toISOString().slice(0, 7);
export const sslipHost = (ip) => `${String(ip).replace(/\./g, '-')}.sslip.io`;
export const townURL = (year, site = 'https://chicago.polecat.live/4d/') => `${site}${YEARS.includes(String(year)) ? year : '1904'}/`;

// ---- Firebase ID tokens ------------------------------------------------------------------
const CERTS = 'https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com';
let certCache = { at: 0, certs: null };
async function certs(fetchFn) {
  if (certCache.certs && Date.now() - certCache.at < 3600e3) return certCache.certs;
  const r = await fetchFn(CERTS);
  if (!r.ok) throw new Error(`certs ${r.status}`);
  certCache = { at: Date.now(), certs: await r.json() };
  return certCache.certs;
}
export function resetCertCache() { certCache = { at: 0, certs: null }; }

/** Verify a Firebase ID token (RS256, Google's published certificates). → claims, or throws. */
export async function verifyIdToken(token, { projectId = FIREBASE_PROJECT, fetchFn = fetch, now = Date.now() / 1000 } = {}) {
  const parts = String(token || '').split('.');
  if (parts.length !== 3) throw new Error('not a token');
  let head, claims;
  try { head = JSON.parse(b64url(parts[0]).toString('utf8')); claims = JSON.parse(b64url(parts[1]).toString('utf8')); } catch { throw new Error('not a token'); }
  if (head.alg !== 'RS256' || !head.kid) throw new Error('wrong algorithm');
  const cert = (await certs(fetchFn))[head.kid];
  if (!cert) throw new Error('unknown key');
  const ok = crypto.createVerify('RSA-SHA256').update(`${parts[0]}.${parts[1]}`).verify(cert, b64url(parts[2]));
  if (!ok) throw new Error('bad signature');
  if (claims.aud !== projectId || claims.iss !== `https://securetoken.google.com/${projectId}`) throw new Error('wrong project');
  if (!(claims.exp > now) || !(claims.iat <= now + 60) || !claims.sub) throw new Error('expired');
  if (claims.firebase?.sign_in_provider === 'anonymous') throw new Error('email-only sign-in');
  if (!claims.email || claims.email_verified !== true) throw new Error('unverified address');
  return claims;
}

// ---- Rights, read as the player ----------------------------------------------------------
const FS = (p) => `https://firestore.googleapis.com/v1/projects/${p}/databases/(default)/documents`;
export async function rightsOf({ token, email, projectId = FIREBASE_PROJECT, fetchFn = fetch }) {
  const h = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  const [mine, probe, cloud] = await Promise.all([
    fetchFn(`${FS(projectId)}/access/${encodeURIComponent(emailId(email))}`, { headers: h }),
    fetchFn(`${FS(projectId)}:runQuery`, { method: 'POST', headers: h, body: JSON.stringify({ structuredQuery: { from: [{ collectionId: 'access' }], limit: 1 } }) }),
    fetchFn(`${FS(projectId)}/launch/cloud`, { headers: h }),
  ]);
  const admin = probe.ok;
  const had = mine.ok ? ((await mine.json()).fields?.rights?.arrayValue?.values ?? []).map((v) => v.stringValue) : [];
  const open = cloud.ok ? (await cloud.json()).fields?.ready?.booleanValue === true : false;
  return { admin, cloud: admin || had.includes('cloud'), open };
}

// ---- Google Cloud, as the starter's own service account ----------------------------------
export function google({ project, fetchFn = fetch, tokenFn }) {
  const getToken = tokenFn || (async () => {
    const r = await fetchFn('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token', { headers: { 'Metadata-Flavor': 'Google' } });
    return (await r.json()).access_token;
  });
  const call = async (url, init = {}) => {
    const r = await fetchFn(url, { ...init, headers: { Authorization: `Bearer ${await getToken()}`, 'Content-Type': 'application/json', ...(init.headers || {}) } });
    const text = await r.text();
    let body = null; try { body = text ? JSON.parse(text) : null; } catch { body = text; }
    return { ok: r.ok, status: r.status, body };
  };
  const C = `https://compute.googleapis.com/compute/v1/projects/${project}`;
  return {
    project, call,
    async machines() {
      const r = await call(`${C}/aggregated/instances?filter=${encodeURIComponent('labels.app=chicago-stream')}`);
      if (!r.ok) throw new Error(`list ${r.status}`);
      return Object.values(r.body?.items ?? {}).flatMap((z) => z.instances ?? []).map((i) => ({
        name: i.name, zone: i.zone.split('/').pop(), status: i.status, labels: i.labels ?? {}, created: i.creationTimestamp,
        ip: i.networkInterfaces?.[0]?.accessConfigs?.[0]?.natIP ?? '',
        token: i.metadata?.items?.find((m) => m.key === 'session-token')?.value ?? '',
      }));
    },
    insert: (zone, body) => call(`${C}/zones/${zone}/instances`, { method: 'POST', body: JSON.stringify(body) }),
    operation: (zone, name) => call(`${C}/zones/${zone}/operations/${name}`),
    remove: (zone, name) => call(`${C}/zones/${zone}/instances/${name}`, { method: 'DELETE' }),
    ready: async (zone, name) => {
      const r = await call(`${C}/zones/${zone}/instances/${name}/getGuestAttributes?queryPath=chicago%2F`);
      return r.ok && (r.body?.queryValue?.items ?? []).some((i) => i.key === 'ready' && i.value === '1');
    },
    // JSON objects in the ledger bucket, written with a generation match so two writers never
    // lose each other's change.
    async object(bucket, path, empty) {
      const r = await call(`https://storage.googleapis.com/storage/v1/b/${bucket}/o/${encodeURIComponent(path)}?alt=json`);
      if (r.status === 404) return { generation: '0', data: empty };
      if (!r.ok) throw new Error(`object ${r.status}`);
      const media = await call(`https://storage.googleapis.com/storage/v1/b/${bucket}/o/${encodeURIComponent(path)}?alt=media&generation=${r.body.generation}`);
      return { generation: r.body.generation, data: media.body };
    },
    async saveObject(bucket, path, generation, data) {
      const r = await call(`https://storage.googleapis.com/upload/storage/v1/b/${bucket}/o?uploadType=media&name=${encodeURIComponent(path)}&ifGenerationMatch=${generation}`, { method: 'POST', body: JSON.stringify(data) });
      return r.ok;
    },
    // The ledger: one object per month, hours/YYYY-MM.json.
    ledger(bucket, month) { return this.object(bucket, `hours/${month}.json`, { month, sessions: {}, stopped: false }); },
    saveLedger(bucket, month, generation, data) { return this.saveObject(bucket, `hours/${month}.json`, generation, data); },
  };
}

/** Machine-hours and dollars this month. A session whose machine is gone ends at the latest when
 * Google's own two-hour limit would have ended it, so a quiet week never runs the count up. */
export function usage(ledger, now = Date.now()) {
  let hours = 0, dollars = 0;
  for (const s of Object.values(ledger?.sessions ?? {})) {
    const start = Date.parse(s.start);
    const end = s.end ? Date.parse(s.end) : Math.min(now, start + MAX_RUN_SECONDS * 1000);
    if (!Number.isFinite(start) || !(end > start)) continue;
    const h = (end - start) / 3600e3;
    hours += h; dollars += h * (s.spot === false ? HOUR_COST.demand : HOUR_COST.spot);
  }
  return { hours, dollars };
}
export const hoursUsed = (ledger, now) => usage(ledger, now).hours;

/** The town a machine opens follows the launch page that asked: the dev preview opens the dev
 * build (so what is being tested is what streams), anything else the site. */
export const DEV_ORIGIN = 'https://dev.chicago.polecat.live';
export const siteFor = (origin, site = 'https://chicago.polecat.live/4d/') => (origin === DEV_ORIGIN ? `${DEV_ORIGIN}/4d/dev/` : site);

// ---- One sign-in (owner, 2026-11-27: "you should have only one sign in for this") ----------
/** A Firebase custom token for the player's own account, signed by the Firebase project's admin
 * account through IAM (the starter holds no key: it may only ask IAM to sign as that account,
 * which the owner granted). The cloud browser signs in with it, so the player is not asked again
 * inside the stream. One hour, the most Firebase allows; the browser's own session lasts after. */
export const CUSTOM_TOKEN_AUD = 'https://identitytoolkit.googleapis.com/google.identity.identitytoolkit.v1.IdentityToolkit';
export function passClaims({ sa, uid, now = Math.floor(Date.now() / 1000) }) {
  return { iss: sa, sub: sa, aud: CUSTOM_TOKEN_AUD, iat: now, exp: now + 3600, uid };
}
export async function signInPass(g, { sa, uid, now }) {
  if (!sa || !uid) return '';
  const r = await g.call(`https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${encodeURIComponent(sa)}:signJwt`,
    { method: 'POST', body: JSON.stringify({ payload: JSON.stringify(passClaims({ sa, uid, now })) }) });
  const jwt = r.ok ? String(r.body?.signedJwt || '') : '';
  return /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(jwt) ? jwt : '';
}

/** The instance the starter asks for. */
export function machineBody({ project, zone, name, year, token, player, spot = true, machineSA, site, gpu = GPUS[0], pass = '' }) {
  return {
    name,
    machineType: `zones/${zone}/machineTypes/${gpu.machineType}`,
    ...(gpu.accelerator ? { guestAccelerators: [{ acceleratorType: `zones/${zone}/acceleratorTypes/${gpu.accelerator}`, acceleratorCount: 1 }] } : {}),
    labels: { app: 'chicago-stream', player, year: String(year), gpu: gpu.gpu },
    scheduling: spot
      ? { provisioningModel: 'SPOT', instanceTerminationAction: 'DELETE', maxRunDuration: { seconds: String(MAX_RUN_SECONDS) }, onHostMaintenance: 'TERMINATE', automaticRestart: false }
      : { provisioningModel: 'STANDARD', instanceTerminationAction: 'DELETE', maxRunDuration: { seconds: String(MAX_RUN_SECONDS) }, onHostMaintenance: 'TERMINATE', automaticRestart: false },
    disks: [{ boot: true, autoDelete: true, initializeParams: { sourceImage: `projects/${project}/global/images/family/${IMAGE_FAMILY}`, diskSizeGb: '50', diskType: `zones/${zone}/diskTypes/pd-balanced` } }],
    networkInterfaces: [{ network: 'global/networks/default', accessConfigs: [{ type: 'ONE_TO_ONE_NAT', name: 'External NAT', networkTier: 'STANDARD' }] }],
    tags: { items: ['chicago-stream'] },
    metadata: { items: [
      { key: 'chicago-url', value: townURL(year, site) },
      { key: 'session-token', value: token },
      { key: 'enable-guest-attributes', value: 'TRUE' },
      ...(pass ? [{ key: 'sign-in-pass', value: pass }] : []),
    ] },
    serviceAccounts: machineSA ? [{ email: machineSA, scopes: ['https://www.googleapis.com/auth/cloud-platform'] }] : [],
  };
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---- The availability probe (owner, 2026-11-27: "yes" to a week of tries) ----------------
/** Canada (Montreal, Toronto: as near Chicago as Virginia) is probed before the starter uses it;
 * a zone that does not offer the GPU, or a region with no quota, is logged as such. */
export const PROBE_ZONES = Object.freeze({
  l4: [...ZONES, 'northamerica-northeast2-a', 'northamerica-northeast2-b', 'northamerica-northeast2-c'],
  t4: [...T4_ZONES, 'northamerica-northeast1-a', 'northamerica-northeast1-b', 'northamerica-northeast1-c'],
});
export const PROBE_DAYS = 7;
/** A probe machine: the smallest disk, no address, gone by itself after ten minutes whatever
 * happens to the starter. It is deleted as soon as Google says it exists. */
export function probeBody({ zone, name, gpu, spot }) {
  return {
    name,
    machineType: `zones/${zone}/machineTypes/${gpu.machineType}`,
    ...(gpu.accelerator ? { guestAccelerators: [{ acceleratorType: `zones/${zone}/acceleratorTypes/${gpu.accelerator}`, acceleratorCount: 1 }] } : {}),
    labels: { app: 'chicago-stream-probe', gpu: gpu.gpu },
    scheduling: { provisioningModel: spot ? 'SPOT' : 'STANDARD', instanceTerminationAction: 'DELETE', maxRunDuration: { seconds: '600' }, onHostMaintenance: 'TERMINATE', automaticRestart: false },
    disks: [{ boot: true, autoDelete: true, initializeParams: { sourceImage: 'projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts', diskSizeGb: '10', diskType: `zones/${zone}/diskTypes/pd-standard` } }],
    networkInterfaces: [{ network: 'global/networks/default' }],
  };
}
/** What a refusal means. */
export function refusal(text) {
  const t = String(text || '');
  if (/GPUS_ALL_REGIONS/.test(t)) return 'busy';
  if (/RESOURCE_POOL_EXHAUSTED|does not have enough resources|STOCKOUT/i.test(t)) return 'stockout';
  if (/QUOTA|quota/.test(t)) return 'quota';
  if (/not found|does not exist|not available in|Invalid value|unsupported|not supported/i.test(t)) return 'not offered';
  return 'error';
}
/** One probe: a Spot machine the way the starter looks for one (L4 zones, then T4); only if
 * none, an on-demand one the same way. At most one machine is made, for about a minute.
 * → { spot: {gpu, zone} | null, demand: {gpu, zone} | null | 'not tried', busy, tries } */
export async function probe(g, { wait = sleep } = {}) {
  const tries = [];
  const one = async (gpu, zone, spot) => {
    const name = `probe-${Date.now().toString(36)}-${crypto.randomBytes(2).toString('hex')}`;
    const r = await g.insert(zone, probeBody({ zone, name, gpu, spot }));
    let outcome;
    if (!r.ok) outcome = refusal(`${r.body?.error?.errors?.[0]?.reason || ''} ${r.body?.error?.message || r.status}`);
    else {
      let op = r.body;
      for (let i = 0; i < 40 && op?.status !== 'DONE'; i++) { await wait(1500); op = (await g.operation(zone, op.name)).body; }
      const err = op?.error?.errors?.[0];
      if (err) outcome = refusal(`${err.code} ${err.message}`);
      else if (op?.status !== 'DONE') outcome = 'error';
      else { outcome = 'ok'; await g.remove(zone, name); }
    }
    tries.push({ gpu: gpu.gpu, zone, spot, outcome });
    return outcome;
  };
  const pass = async (spot) => {
    for (const gpu of GPUS) for (const zone of PROBE_ZONES[gpu.gpu]) {
      const o = await one(gpu, zone, spot);
      if (o === 'ok') return { gpu: gpu.gpu, zone };
      if (o === 'busy') return 'busy';
    }
    return null;
  };
  const spot = await pass(true);
  if (spot === 'busy') return { spot: null, demand: 'not tried', busy: true, tries };
  const demand = spot ? 'not tried' : await pass(false);
  if (demand === 'busy') return { spot: null, demand: 'not tried', busy: true, tries };
  return { spot, demand, busy: false, tries };
}
/** The week's log, one short row a probe: when, what was found, and the zones that refused. */
export function probeRow(at, out) {
  const code = (x) => (x && typeof x === 'object' ? `${x.gpu}@${x.zone}` : x || 'none');
  const refused = {};
  for (const t of out.tries) if (t.outcome !== 'ok') (refused[t.outcome] ??= []).push(`${t.gpu}${t.spot ? '' : '!'}@${t.zone}`);
  return { at, spot: code(out.spot), demand: code(out.demand), busy: out.busy, refused };
}
export function probeSummary(log) {
  const rows = log?.rows ?? [];
  const tried = rows.filter((r) => !r.busy);
  const spot = tried.filter((r) => r.spot !== 'none').length;
  const any = tried.filter((r) => r.spot !== 'none' || (r.demand !== 'none' && r.demand !== 'not tried')).length;
  const byZone = {};
  for (const r of tried) for (const k of ['spot', 'demand']) if (r[k] && r[k].includes('@')) byZone[r[k]] = (byZone[r[k]] ?? 0) + 1;
  return { started: log?.started ?? null, until: log?.until ?? null, probes: rows.length, busy: rows.length - tried.length, spot, anyMachine: any, byZone };
}
/** Start a machine: Spot in each L4 zone in turn, then in each T4 zone; on demand (the same order)
 * only for an admin when Spot is refused everywhere. → { ok, zone, name, spot, gpu } or { ok: false, why } */
export async function startMachine(g, { year, player, machineSA, admin, site, gpus = GPUS, pass = '', wait = sleep }) {
  const token = crypto.randomBytes(24).toString('hex');
  const name = `stream-${Date.now().toString(36)}-${crypto.randomBytes(2).toString('hex')}`;
  let last = 'no zone';
  for (const spot of admin ? [true, false] : [true]) {
    for (const gpu of gpus) for (const zone of gpu.zones) {
      const r = await g.insert(zone, machineBody({ project: g.project, zone, name, year, token, player, spot, machineSA, site, gpu, pass }));
      if (!r.ok) { last = r.body?.error?.message || `insert ${r.status}`; if (/GPUS_ALL_REGIONS/.test(last)) return { ok: false, why: 'quota', detail: last }; continue; }
      // The insert is accepted at once; capacity is known only when its operation ends.
      let op = r.body;
      for (let i = 0; i < 40 && op?.status !== 'DONE'; i++) { await wait(1500); op = (await g.operation(zone, op.name)).body; }
      const err = op?.error?.errors?.[0];
      if (!err) return { ok: true, zone, name, spot, token, gpu: gpu.gpu };
      last = `${err.code}: ${err.message}`;
      // The project's one GPU is in use (or not granted): no other zone can help. A region's own
      // quota (say, none yet in Canada) only rules out that region.
      if (/GPUS_ALL_REGIONS/.test(last)) return { ok: false, why: 'quota', detail: last };
    }
  }
  return { ok: false, why: 'no capacity', detail: last };
}
