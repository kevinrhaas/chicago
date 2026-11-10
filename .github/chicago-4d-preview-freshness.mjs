// Verify the preview actually served after Pages accepted the uploaded artifact.
// This runs AFTER deployment and never changes production or deployment permissions.
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const MODULES = ['walk/js/humans.js', 'walk/js/fabric.js',
  'walk/js/main.js', 'walk/js/parked-transport.js'];

export async function verifyPreview({ origin, previewRoot, timeoutMs = 120000,
  pollMs = 5000, requestMs = 8000 }) {
  if (!(timeoutMs > 0 && timeoutMs <= 120000 && pollMs >= 0 && requestMs > 0)) {
    throw Error('Freshness polling must remain within 120 seconds');
  }
  const base = new URL(origin);
  if (!['http:', 'https:'].includes(base.protocol)) throw Error('HTTP(S) origin required');
  const expectedBuild = JSON.parse(await readFile(resolve(previewRoot, 'build.json'), 'utf8'));
  if (expectedBuild.tier !== 'dev' || !/^[0-9a-f]{7,40}$/.test(expectedBuild.sha ?? '')) {
    throw Error('Generated preview has no valid DEV revision; refusing an unverified success');
  }
  const expectedModules = Object.fromEntries(await Promise.all(MODULES.map(async name =>
    [name, hash(await readFile(resolve(previewRoot, name)))])));
  const started = Date.now(), deadline = started + timeoutMs;
  const attempts = [];
  do {
    const attempt = { at: new Date().toISOString(), build: null, modules: {}, errors: [] };
    const get = async name => {
      const url = new URL(`/4d/dev/${name}`, base);
      url.searchParams.set('verify', `${process.env.GITHUB_RUN_ID ?? 'local'}-${Date.now()}-${attempts.length}`);
      const response = await fetch(url, { cache: 'no-store',
        headers: { 'Cache-Control': 'no-cache', Pragma: 'no-cache' },
        signal: AbortSignal.timeout(Math.max(1, Math.min(requestMs, deadline - Date.now()))) });
      if (!response.ok) throw Error(`${name}: HTTP ${response.status}`);
      return new Uint8Array(await response.arrayBuffer());
    };
    await Promise.all([
      (async () => {
        try { attempt.build = JSON.parse(new TextDecoder().decode(await get('build.json'))); }
        catch (error) { attempt.errors.push(String(error)); }
      })(),
      ...MODULES.map(async name => {
        try { attempt.modules[name] = hash(await get(name)); }
        catch (error) { attempt.errors.push(String(error)); }
      }),
    ]);
    const matches = attempt.errors.length === 0 && attempt.build?.tier === 'dev'
      && attempt.build?.sha === expectedBuild.sha
      && MODULES.every(name => attempt.modules[name] === expectedModules[name]);
    attempts.push(attempt);
    if (matches) return { status: 'PASS_LIVE_DEV_MATCHES_UPLOADED_PREVIEW',
      expectedSHA: expectedBuild.sha, expectedModules, elapsedMs: Date.now() - started, attempts };
    if (Date.now() >= deadline) break;
    await new Promise(done => setTimeout(done, Math.min(pollMs, deadline - Date.now())));
  } while (Date.now() < deadline);
  return { status: 'FAIL_LIVE_DEV_STALE_OR_UNVERIFIED', expectedSHA: expectedBuild.sha,
    expectedModules, elapsedMs: Date.now() - started, attempts };
}

async function main() {
  const args = process.argv.slice(2), options = {};
  for (let i = 0; i < args.length; i += 2) {
    if (!['--origin', '--preview-root', '--out'].includes(args[i]) || !args[i + 1]) {
      throw Error('usage: --origin URL --preview-root GENERATED-DIRECTORY [--out RECEIPT.json]');
    }
    options[args[i]] = args[i + 1];
  }
  if (!options['--origin'] || !options['--preview-root']) throw Error('origin and preview-root required');
  const result = await verifyPreview({ origin: options['--origin'], previewRoot: options['--preview-root'] });
  const body = JSON.stringify(result, null, 2) + '\n';
  if (options['--out']) await writeFile(options['--out'], body, { flag: 'wx' });
  console.log(body);
  if (!result.status.startsWith('PASS_')) {
    console.error('::error::Pages accepted the artifact, but live DEV did not match its build and modules within 120 seconds.');
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(error => { console.error(`::error::DEV freshness verification failed: ${error.message}`); process.exitCode = 1; });
}
