#!/usr/bin/env node
// T-2899: every Playwright `waitForFunction` passes its options in the THIRD slot.
//
// The signature is `page.waitForFunction(fn, arg, options)`. A call written
// `waitForFunction(fn, { timeout: 30000 })` hands the object to the page function as
// its argument and runs with NO options at all, so the limit is whatever
// `setDefaultTimeout` says. Nothing throws and nothing warns. The smoke's boot wait
// was written that way: it read 30 s and waited the page's 90 s, and on a loaded
// four-core runner desktop boots took 107-170 s and failed "scene reaches ready" with
// zero page errors, three runs in a row (PR #1112). The same slip stood five more
// times in four other tools. This reads every script in the project that calls the function and
// refuses a call whose second argument is an object literal of option keys
// (timeout, polling) with no third argument. Variables in the arg slot are not
// guessed at; the literal is the shape the mistake has taken every time it was made.
//
//   node tools/test_wait_for_function_args.mjs
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const SKIP_DIRS = new Set(['node_modules', '.git', 'tickets', 'site', 'vendor']);
const OPTION_KEYS = new Set(['timeout', 'polling']);

// Blank out comments, string and template-literal bodies and regex literals (keeping
// every newline and every offset), so that only code is searched and a comma or paren
// inside a page function's string never counts. A call quoted in prose is not a call.
export function codeOnly(src) {
  const out = src.split('');
  const blank = (a, b) => { for (let k = a; k < b; k++) if (out[k] !== '\n') out[k] = ' '; };
  let prev = ';';
  for (let i = 0; i < src.length; i++) {
    const c = src[i];
    let end = -1;
    if (c === '/' && src[i + 1] === '/') { end = src.indexOf('\n', i); if (end < 0) end = src.length; blank(i, end); i = end; continue; }
    if (c === '/' && src[i + 1] === '*') { end = src.indexOf('*/', i + 2); end = end < 0 ? src.length : end + 2; blank(i, end); i = end - 1; continue; }
    if (c === '"' || c === "'" || c === '`') end = skipString(src, i);
    else if (c === '/' && regexAllowed(src, i, prev)) end = skipRegex(src, i);
    else { if (!/\s/.test(c)) prev = c; continue; }
    if (end < 0) return out.join('');
    blank(i + 1, end); prev = c; i = end;
  }
  return out.join('');
}

// Split the argument list that opens at `open` (the index of the call's `(`) in code
// already passed through codeOnly. Returns null if it never closes.
export function callArgs(code, open) {
  const args = [];
  let depth = 0, start = open + 1;
  for (let i = open; i < code.length; i++) {
    const c = code[i];
    if ('([{'.includes(c)) depth++;
    else if (')]}'.includes(c)) {
      if (--depth === 0) {
        args.push(code.slice(start, i).trim());
        return args.length === 1 && !args[0] ? [] : args.filter((a, k) => a || k < args.length - 1);
      }
    } else if (c === ',' && depth === 1) { args.push(code.slice(start, i).trim()); start = i + 1; }
  }
  return null;
}

// A `/` opens a regex after an operator or punctuator, or after a keyword such as
// `return`; after a name, a number or a closing bracket it divides.
function regexAllowed(src, i, prev) {
  if (/[(,=:[!&|?{};+\-*%<>~^]/.test(prev)) return true;
  const word = /([A-Za-z_$][\w$]*)\s*$/.exec(src.slice(Math.max(0, i - 16), i));
  return !!word && /^(return|typeof|case|do|else|in|of|void|yield|await|delete|new|throw)$/.test(word[1]);
}

function skipString(src, i) {
  const q = src[i];
  for (let j = i + 1; j < src.length; j++) {
    if (src[j] === '\\') { j++; continue; }
    if (q === '`' && src[j] === '$' && src[j + 1] === '{') {
      let d = 1; j += 2;
      for (; j < src.length && d > 0; j++) {
        if (src[j] === '`' || src[j] === '"' || src[j] === "'") { j = skipString(src, j); if (j < 0) return -1; continue; }
        if (src[j] === '{') d++; else if (src[j] === '}') d--;
      }
      j--; continue;
    }
    if (src[j] === q) return j;
  }
  return -1;
}

function skipRegex(src, i) {
  let cls = false;
  for (let j = i + 1; j < src.length; j++) {
    const c = src[j];
    if (c === '\\') { j++; continue; }
    if (c === '\n') return -1;
    if (c === '[') cls = true; else if (c === ']') cls = false;
    else if (c === '/' && !cls) return j;
  }
  return -1;
}

// An object literal whose keys are all option names: `{ timeout: 30000 }`, `{polling:250}`.
export function optionsShaped(arg) {
  if (!arg || arg[0] !== '{' || arg[arg.length - 1] !== '}') return false;
  const keys = [...arg.slice(1, -1).matchAll(/(?:^|,)\s*([A-Za-z_$][\w$]*)\s*(?::|,|$)/g)].map((m) => m[1]);
  return keys.length > 0 && keys.every((k) => OPTION_KEYS.has(k));
}

// Every misplaced-options call in one source text, as { line, call }.
export function misplaced(src) {
  const found = [];
  const code = codeOnly(src);
  const re = /\bwaitForFunction\s*\(/g;
  for (let m; (m = re.exec(code));) {
    const open = m.index + m[0].length - 1;
    const args = callArgs(code, open);
    if (!args) continue;
    if (args.length === 2 && optionsShaped(args[1])) {
      found.push({ line: src.slice(0, m.index).split('\n').length, call: `waitForFunction(…, ${src.slice(open).match(/\{[^}]*\}\s*\)/)?.[0] ?? args[1]}` });
    }
  }
  return found;
}

// The scanner must see the mistake before its silence over the tree means anything.
const bad = [
  "await page.waitForFunction(() => window.__chicago4d?.ready === true, { timeout: 30000 });",
  "await page.waitForFunction(() => {\n  const s = 'a, b)'; return /\\)\\s*,/.test(s);\n}, {polling: 250, timeout: 1e4});",
  "page.waitForFunction(`x(${1})`, { timeout })",
];
const good = [
  "await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 30000 });",
  "await page.waitForFunction((t) => t > 1, { threshold: 2 });",
  "await page.waitForFunction(() => ready, {}, { timeout: 120000 });",
  "await page.waitForFunction(() => window.__chicago4d?.ready === true);",
  "const until = (fn, arg = null) => p.waitForFunction(fn, arg, { polling: 250 });",
  "// waitForFunction(fn, { timeout: 1 }) in a comment is prose\nx();",
];
for (const s of bad) assert.equal(misplaced(s).length, 1, `scanner missed: ${s}`);
for (const s of good) assert.equal(misplaced(s).length, 0, `scanner flagged a correct call: ${s}`);

function* scripts(dir) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    if (e.isDirectory()) { if (!SKIP_DIRS.has(e.name)) yield* scripts(join(dir, e.name)); }
    else if (/\.(m?js|cjs)$/.test(e.name)) yield join(dir, e.name);
  }
}

const failures = [];
let files = 0, calls = 0;
for (const file of scripts(ROOT)) {
  const src = readFileSync(file, 'utf8');
  if (!src.includes('waitForFunction')) continue;
  files++;
  calls += (codeOnly(src).match(/\bwaitForFunction\s*\(/g) || []).length;
  for (const f of misplaced(src)) failures.push(`${relative(ROOT, file)}:${f.line}: ${f.call} — options in the arg slot; pass (fn, null, options)`);
}
if (failures.length) {
  console.error(failures.join('\n'));
  console.error(`FAIL: ${failures.length} waitForFunction call(s) pass their options as the page function's argument, so the default timeout applies`);
  process.exit(1);
}
console.log(`ok: ${calls} waitForFunction calls in ${files} scripts pass options in the third slot`);
