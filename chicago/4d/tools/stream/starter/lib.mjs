/**
 * T-3794 / T-3795: the stream starter's logic, kept apart from the HTTP server so the gate can
 * drive it with a fake Google (tools/test_stream_starter.mjs). No dependencies: Node 20+.
 *
 * Who may start a machine is decided by the same Firestore rules the launch page reads
 * (renderers/web/js/launch-rights.js, docs/SIGN-IN.md): the starter asks Firestore *with the
 * player's own ID token*, so it needs no access to the Firebase project of its own, and nothing
 * here can touch chicago-61643 beyond what that player could read themself (T-3795 (e)).
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
    // The ledger: one JSON object per month in the ledger bucket, written with a generation
    // match so two starts never lose each other's session.
    async ledger(bucket, month) {
      const r = await call(`https://storage.googleapis.com/storage/v1/b/${bucket}/o/${encodeURIComponent(`hours/${month}.json`)}?alt=json`);
      if (r.status === 404) return { generation: '0', data: { month, sessions: {}, stopped: false } };
      if (!r.ok) throw new Error(`ledger ${r.status}`);
      const media = await call(`https://storage.googleapis.com/storage/v1/b/${bucket}/o/${encodeURIComponent(`hours/${month}.json`)}?alt=media&generation=${r.body.generation}`);
      return { generation: r.body.generation, data: media.body };
    },
    async saveLedger(bucket, month, generation, data) {
      const r = await call(`https://storage.googleapis.com/upload/storage/v1/b/${bucket}/o?uploadType=media&name=${encodeURIComponent(`hours/${month}.json`)}&ifGenerationMatch=${generation}`, { method: 'POST', body: JSON.stringify(data) });
      return r.ok;
    },
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

/** The instance the starter asks for. */
export function machineBody({ project, zone, name, year, token, player, spot = true, machineSA, site, gpu = GPUS[0] }) {
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
    ] },
    serviceAccounts: machineSA ? [{ email: machineSA, scopes: ['https://www.googleapis.com/auth/cloud-platform'] }] : [],
  };
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
/** Start a machine: Spot in each L4 zone in turn, then in each T4 zone; on demand (the same order)
 * only for an admin when Spot is refused everywhere. → { ok, zone, name, spot, gpu } or { ok: false, why } */
export async function startMachine(g, { year, player, machineSA, admin, site, wait = sleep }) {
  const token = crypto.randomBytes(24).toString('hex');
  const name = `stream-${Date.now().toString(36)}-${crypto.randomBytes(2).toString('hex')}`;
  let last = 'no zone';
  for (const spot of admin ? [true, false] : [true]) {
    for (const gpu of GPUS) for (const zone of gpu.zones) {
      const r = await g.insert(zone, machineBody({ project: g.project, zone, name, year, token, player, spot, machineSA, site, gpu }));
      if (!r.ok) { last = r.body?.error?.message || `insert ${r.status}`; if (/QUOTA|quota/.test(last)) return { ok: false, why: 'quota', detail: last }; continue; }
      // The insert is accepted at once; capacity is known only when its operation ends.
      let op = r.body;
      for (let i = 0; i < 40 && op?.status !== 'DONE'; i++) { await wait(1500); op = (await g.operation(zone, op.name)).body; }
      const err = op?.error?.errors?.[0];
      if (!err) return { ok: true, zone, name, spot, token, gpu: gpu.gpu };
      last = `${err.code}: ${err.message}`;
      if (/QUOTA/.test(err.code)) return { ok: false, why: 'quota', detail: last };
    }
  }
  return { ok: false, why: 'no capacity', detail: last };
}
