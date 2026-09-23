#!/usr/bin/env node
/**
 * T-0153 — EVERY PLAYWRIGHT TOOL MUST BE POINTABLE AT A BROWSER.
 *
 *   node tools/check_tool_browser.mjs
 *
 * `smoke_renderer.mjs` has always launched with
 *
 *     executablePath: process.env.PW_EXECUTABLE || undefined
 *
 * which is why the release gate runs on any machine that has a Chromium
 * anywhere. Twelve of the other fifteen Playwright tools called a bare
 * `chromium.launch()` and could therefore only use the browser Playwright had
 * installed for itself — so on a runner without that exact build they died
 * before their first frame:
 *
 *     browserType.launch: Executable doesn't exist at
 *       /opt/pw-browsers/chromium_headless_shell-1234/...
 *
 * That is worse than an inconvenience. Almost every one of these is a MEASURING
 * instrument, and the discipline in this repo is that a change is measured
 * before it is claimed. An instrument that cannot start on the machine doing
 * the work turns "measured" quietly into "asserted" — and the tool that could
 * not start was the one T-0013's acceptance is written against.
 *
 * Four tools already had the line and eight more were written after them
 * without it, so this is a pattern that lapsed rather than a decision anyone
 * made. This check exists so it cannot lapse a third time.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SELF = path.basename(fileURLToPath(import.meta.url));
const TOOLS = path.join(path.dirname(fileURLToPath(import.meta.url)));
const files = fs.readdirSync(TOOLS).filter((f) => f.endsWith('.mjs')).sort();

const offenders = [];
let checked = 0;

for (const f of files) {
  // This file quotes `chromium.launch()` in its own prose and would otherwise
  // count itself as a seventeenth browser-launching tool. The match below is
  // deliberately textual rather than syntactic — a tool that only MENTIONS the
  // call still gets asked for the variable, which costs one line and errs the
  // safe way — but counting the checker itself would just be wrong.
  if (f === SELF) continue;
  const src = fs.readFileSync(path.join(TOOLS, f), 'utf8');
  if (!/chromium\s*\.\s*launch\s*\(/.test(src)) continue;
  checked++;
  if (!/PW_EXECUTABLE/.test(src)) offenders.push(f);
}

if (checked === 0) {
  // A rename or a refactor that moved every launch out of tools/ would make
  // this check silently vacuous, which is its own failure mode.
  console.error('   no tool launches a browser — this check has stopped checking anything');
  process.exit(1);
}

if (offenders.length) {
  console.error(`   ${offenders.length} of ${checked} browser-launching tool(s) ignore PW_EXECUTABLE:`);
  for (const f of offenders) console.error(`     tools/${f}`);
  console.error('   add `executablePath: process.env.PW_EXECUTABLE || undefined` to the launch,');
  console.error('   the same way tools/smoke_renderer.mjs does — otherwise the tool can only run');
  console.error('   on a machine carrying the exact browser build Playwright installed for itself.');
  process.exit(1);
}

console.log(`   ${checked} browser-launching tool(s), every one pointable via PW_EXECUTABLE`);
