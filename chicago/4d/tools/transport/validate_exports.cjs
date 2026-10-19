// Optional independent conformance check. Install gltf-validator@2.0.0-dev.3.10
// outside the checkout and set NODE_PATH to its node_modules directory.
const fs = require('node:fs');
const path = require('node:path');
const validator = require('gltf-validator');
const root = path.resolve(__dirname, '../..');

(async () => {
  const reports = {};
  for (const name of ['wagon', 'carriage', 'horse', 'harness']) {
    const directory = path.join(root, 'renderers/web/transport', name);
    const file = fs.readdirSync(directory).find(file => file.endsWith('.glb'));
    reports[name] = await validator.validateBytes(
      new Uint8Array(fs.readFileSync(path.join(directory, file))), { uri: file });
    const { numErrors, numWarnings } = reports[name].issues;
    console.log(`${name}: ${numErrors} errors, ${numWarnings} warnings`);
  }
  if (process.argv[2]) fs.writeFileSync(process.argv[2], JSON.stringify(reports, null, 2) + '\n');
  process.exitCode = Object.values(reports).some(report => report.issues.numErrors) ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 1; });
