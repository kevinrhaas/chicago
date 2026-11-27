/**
 * publish_firestore_rules.mjs — publish docs/SIGN-IN.md's Firestore rules to the live
 * project (T-3776).
 *
 *   node tools/publish_firestore_rules.mjs --dry-run     print the rules it would publish
 *   FIREBASE_SERVICE_ACCOUNT='{…json…}' node tools/publish_firestore_rules.mjs [--project id]
 *
 * The owner, 2026-11-26: "you can push directly to firestore", with the service account
 * kept as the repository secret FIREBASE_SERVICE_ACCOUNT. Until then the rules were pasted
 * into the Firebase console by hand (docs/SIGN-IN.md, setup step 4); the workflow
 * chicago-4d-firestore-rules.yml now runs this instead.
 *
 * The rules in the doc say `OWNER_EMAIL` where the owner's address goes, and the address is
 * never committed. So this reads the LIVE ruleset first and carries its owner address
 * across (the one `request.auth.token.email == '…'` in isOwner()), masked in the log. It
 * refuses, and publishes nothing, when:
 *   - the live rules have no owner address to carry (and OWNER_EMAIL is not set);
 *   - the live rules match a collection the doc's rules do not (someone added it in the
 *     console; publishing would drop it) — add it to the doc first, or pass --force;
 *   - Firebase's own compiler rejects the new source.
 * Publishing is two calls: create a ruleset from the source, then point the
 * `cloud.firestore` release at it, which is exactly what the console's Publish does.
 */
import { readFileSync } from 'node:fs';
import { createSign } from 'node:crypto';

const args = process.argv.slice(2);
const flag = (name) => args.includes(name);
const opt = (name, fallback) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : fallback; };
const DRY = flag('--dry-run');
const FORCE = flag('--force');
const PROJECT = opt('--project', process.env.FIREBASE_PROJECT_ID || 'chicago-61643');
const PLACEHOLDER = 'OWNER_EMAIL';
const RULES_API = 'https://firebaserules.googleapis.com/v1';

/** The rules block of docs/SIGN-IN.md: the fenced block that starts `rules_version`. */
export function rulesFromDoc(doc) {
  const blocks = [...doc.matchAll(/```[a-z]*\n([\s\S]*?)```/g)].map((m) => m[1]);
  const rules = blocks.filter((b) => b.trimStart().startsWith("rules_version = '2';"));
  if (rules.length !== 1) throw new Error(`docs/SIGN-IN.md holds ${rules.length} rules blocks, not 1`);
  if (!rules[0].includes(`'${PLACEHOLDER}'`)) throw new Error(`the rules block has no '${PLACEHOLDER}' to fill`);
  return rules[0];
}

/** The collections a ruleset matches at the top level of documents. */
export const collectionsOf = (source) =>
  [...new Set([...source.matchAll(/match \/([A-Za-z0-9_-]+)\/\{/g)].map((m) => m[1]).filter((c) => c !== 'databases'))].sort();

/** The owner address in a live ruleset's isOwner(), or null. */
export function ownerEmailOf(source) {
  const found = [...source.matchAll(/request\.auth\.token\.email\s*==\s*'([^']+)'/g)].map((m) => m[1]);
  const unique = [...new Set(found)].filter((e) => e !== PLACEHOLDER);
  return unique.length === 1 ? unique[0] : null;
}

function serviceAccount() {
  const raw = process.env.FIREBASE_SERVICE_ACCOUNT?.trim();
  if (!raw) throw new Error('FIREBASE_SERVICE_ACCOUNT is not set');
  const text = raw.startsWith('{') ? raw : Buffer.from(raw, 'base64').toString('utf8');
  const account = JSON.parse(text);
  if (!account.client_email || !account.private_key) throw new Error('FIREBASE_SERVICE_ACCOUNT is not a service-account key');
  return account;
}

async function accessToken(account) {
  const now = Math.floor(Date.now() / 1000);
  const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
  const head = b64({ alg: 'RS256', typ: 'JWT' });
  const claim = b64({
    iss: account.client_email, aud: account.token_uri || 'https://oauth2.googleapis.com/token',
    scope: 'https://www.googleapis.com/auth/firebase https://www.googleapis.com/auth/cloud-platform',
    iat: now, exp: now + 600,
  });
  const signer = createSign('RSA-SHA256');
  signer.update(`${head}.${claim}`);
  const jwt = `${head}.${claim}.${signer.sign(account.private_key).toString('base64url')}`;
  const res = await fetch(account.token_uri || 'https://oauth2.googleapis.com/token', {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer', assertion: jwt }),
  });
  const body = await res.json();
  if (!res.ok || !body.access_token) throw new Error(`token refused: ${res.status} ${body.error ?? ''} ${body.error_description ?? ''}`);
  return body.access_token;
}

async function api(token, method, path, payload) {
  const res = await fetch(`${RULES_API}/${path}`, {
    method, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: payload ? JSON.stringify(payload) : undefined,
  });
  const text = await res.text();
  let body = {};
  try { body = JSON.parse(text); } catch { body = { raw: text }; }
  if (!res.ok) throw new Error(`${method} ${path}: ${res.status} ${body.error?.message ?? text.slice(0, 300)}`);
  return body;
}

async function main() {
  const doc = readFileSync(new URL('../docs/SIGN-IN.md', import.meta.url), 'utf8');
  const template = rulesFromDoc(doc);
  const wanted = collectionsOf(template);
  if (DRY) {
    console.log(template);
    console.log(`dry run: ${wanted.length} collections (${wanted.join(', ')}); nothing published`);
    return;
  }

  const account = serviceAccount();
  if (account.project_id && account.project_id !== PROJECT) {
    throw new Error(`the key is for project ${account.project_id}, not ${PROJECT}`);
  }
  const token = await accessToken(account);

  const release = await api(token, 'GET', `projects/${PROJECT}/releases/cloud.firestore`);
  const live = await api(token, 'GET', release.rulesetName);
  const liveSource = (live.source?.files ?? []).map((f) => f.content).join('\n');
  const owner = process.env.OWNER_EMAIL?.trim() || ownerEmailOf(liveSource);
  if (!owner) throw new Error('the live rules hold no single owner address to carry across, and OWNER_EMAIL is not set');
  if (process.env.GITHUB_ACTIONS) console.log(`::add-mask::${owner}`);

  const dropped = collectionsOf(liveSource).filter((c) => !wanted.includes(c));
  if (dropped.length && !FORCE) {
    throw new Error(`the live rules match ${dropped.join(', ')}, which docs/SIGN-IN.md does not; add them to the doc first (or --force)`);
  }

  const content = template.replaceAll(`'${PLACEHOLDER}'`, `'${owner}'`);
  if (content === liveSource) {
    console.log(`Firestore rules for ${PROJECT} are already the doc's (${release.rulesetName}); nothing to publish`);
    return;
  }
  const ruleset = await api(token, 'POST', `projects/${PROJECT}/rulesets`, {
    source: { files: [{ name: 'firestore.rules', content }] },
  });
  await api(token, 'PATCH', `projects/${PROJECT}/releases/cloud.firestore`, {
    release: { name: `projects/${PROJECT}/releases/cloud.firestore`, rulesetName: ruleset.name },
  });
  const check = await api(token, 'GET', `projects/${PROJECT}/releases/cloud.firestore`);
  if (check.rulesetName !== ruleset.name) throw new Error(`the release still points at ${check.rulesetName}`);
  console.log(`published Firestore rules for ${PROJECT}: ${ruleset.name} (was ${release.rulesetName}); `
    + `${wanted.length} collections: ${wanted.join(', ')}`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => {
    // Never echo the key or the owner address; the messages above carry neither.
    console.error(`publish_firestore_rules: ${err.message}`);
    process.exit(1);
  });
}
