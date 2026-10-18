#!/usr/bin/env node
// strip_page_comments.mjs — the published walk page ships without its developer notes.
//
//   node tools/strip_page_comments.mjs <site/4d/walk/index.html>   strip in place (publish.sh)
//   node tools/strip_page_comments.mjs --check [site/4d]           assert the shipped form (check.sh)
//   node tools/strip_page_comments.mjs --self-test                 prove each rule on fixtures
//
// WHY. renderers/web/index.html carries about 13 KB of HTML comments: the reasons a
// line is the way it is, written for whoever edits it next. They are the source's
// documentation and they stay there. A visitor downloads none of them usefully, and
// publish.sh ships that page five times over — walk/ and the year doors, which are
// the stamped page plus one <base href> (write_entry_pages.mjs). Those doors are
// deliberately byte-identical, so tools/validate.py's site check (T-0722) refuses
// them once they reach SITE_DUPE_FLOOR (64 KB); on 2026-10-18 the door was 64,208
// bytes and PR #1030's markup put it over. Taking the notes out of the SHIPPED page
// is the honest fix: the floor stays where it is and the doors stay identical.
//
// THE RULES. Only real `<!-- … -->` comments in markup go, and the rest of the page is
// passed through byte for byte:
//   - a placeholder `<!--[A-Z0-9_]+-->` (`<!--BUILD_STAMP-->`) is kept: it is a slot
//     something fills, not a note;
//   - a conditional comment (`<!--[if …]>`, `<![endif]-->`) is kept;
//   - nothing inside <script>, <style>, <textarea>, <pre>, <title>, <noscript> or <xmp>
//     is touched — raw text, whitespace that renders, or code whose `<!--` is not one;
//   - a `<!--` inside a tag (an attribute value) is not a comment and is passed through;
//   - a comment alone on its line(s) takes its line with it, so the page does not ship
//     a column of blank lines in its place. Whitespace on either side of a comment
//     collapses the same with or without it, outside the raw elements above.
//
// WHAT --check ASSERTS on the published tree: walk/index.html carries no developer
// comment; it IS the source with exactly this strip and publish.sh's stamp applied
// (the gate's build stamp and the c4d-releases meta are put back to their source form
// and the rest must match byte for byte), so every script, style and textarea body is
// the source's; every placeholder the source carries survives the strip; and every
// year door is walk/index.html plus its <base>, so the doors carry no notes either.
import { readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const ROOT4D = path.resolve(HERE, '..');

const PLACEHOLDER = /^<!--[A-Z0-9_]+-->$/;
const CONDITIONAL = /^<!--\[if\b|<!\[endif\]-->$/i;
const RAW = new Set(['script', 'style', 'textarea', 'pre', 'title', 'noscript', 'xmp']);

/** The end of the tag that starts at `i` (index of its `>`), honouring quoted attribute values. */
function tagEnd(html, i) {
  let k = i + 1;
  while (k < html.length) {
    const ch = html[k];
    if (ch === '>') return k;
    if (ch === '=') {
      k++;
      while (k < html.length && /\s/.test(html[k])) k++;
      const q = html[k];
      if (q === '"' || q === "'") {
        const close = html.indexOf(q, k + 1);
        if (close < 0) throw new Error(`unterminated attribute value at offset ${k}`);
        k = close + 1;
        continue;
      }
      continue;
    }
    k++;
  }
  throw new Error(`unterminated tag at offset ${i}`);
}

/**
 * The page with its developer comments taken out. Returns the new text, the comments
 * removed and kept, and every raw element's body in document order.
 */
export function stripComments(html) {
  const lower = html.toLowerCase();
  const removed = [];
  const kept = [];
  const raw = [];
  let out = '';
  let i = 0;
  const n = html.length;
  while (i < n) {
    const lt = html.indexOf('<', i);
    if (lt < 0) { out += html.slice(i); break; }
    out += html.slice(i, lt);
    i = lt;
    if (html.startsWith('<!--', i)) {
      // `<!-->` and `<!--->` end at once (the HTML parser's abrupt closing).
      let end;
      if (html.startsWith('<!-->', i)) end = i + 5;
      else if (html.startsWith('<!--->', i)) end = i + 6;
      else {
        const close = html.indexOf('-->', i + 4);
        if (close < 0) throw new Error(`unterminated comment at offset ${i}`);
        end = close + 3;
      }
      const c = html.slice(i, end);
      if (PLACEHOLDER.test(c) || CONDITIONAL.test(c)) { kept.push(c); out += c; i = end; continue; }
      removed.push(c);
      // Alone on its line(s): the line goes too.
      const lineStart = out.lastIndexOf('\n') + 1;
      let j = end;
      while (j < n && (html[j] === ' ' || html[j] === '\t')) j++;
      const restBlank = j >= n || html[j] === '\n' || html[j] === '\r';
      if (restBlank && /^[ \t]*$/.test(out.slice(lineStart))) {
        out = out.slice(0, lineStart);
        if (html.startsWith('\r\n', j)) j += 2;
        else if (j < n) j += 1;
        i = j;
      } else {
        i = end;
      }
      continue;
    }
    if (html.startsWith('<!', i) || html.startsWith('<?', i)) {
      // A doctype, a downlevel `<![endif]-->`, a bogus comment: passed through whole.
      const end = html.indexOf('>', i);
      if (end < 0) throw new Error(`unterminated declaration at offset ${i}`);
      out += html.slice(i, end + 1);
      i = end + 1;
      continue;
    }
    const m = /^<(\/?)([A-Za-z][A-Za-z0-9-]*)/.exec(html.slice(i, i + 64));
    if (!m) { out += '<'; i += 1; continue; }
    const end = tagEnd(html, i);
    out += html.slice(i, end + 1);
    i = end + 1;
    const name = m[2].toLowerCase();
    if (!m[1] && RAW.has(name) && html[end - 1] !== '/') {
      const close = lower.indexOf(`</${name}`, i);
      if (close < 0) throw new Error(`<${name}> at offset ${lt} is never closed`);
      raw.push({ name, body: html.slice(i, close) });
      out += html.slice(i, close);
      i = close;
    }
  }
  return { html: out, removed, kept, raw };
}

const GATE_PLACEHOLDER = '<p class="gate-build" id="gate-build" hidden><!--BUILD_STAMP--></p>';
const RELEASES_PLACEHOLDER = '<meta name="c4d-releases" content="">';

/** The published page with publish.sh's (and deploy.yml's) stamp put back to its source form. */
export function unstamp(html) {
  return html
    .replace(/<p class="gate-build" id="gate-build"[^>]*>.*?<\/p>/s, GATE_PLACEHOLDER)
    .replace(/<meta name="c4d-releases" content="[^"]*">/, RELEASES_PLACEHOLDER);
}

/** Everything wrong with the published walk page and its doors, as sentences. */
export async function problems(site, sourcePath = path.join(ROOT4D, 'renderers/web/index.html')) {
  const bad = [];
  const walkPath = path.join(site, 'walk', 'index.html');
  if (!existsSync(walkPath)) return [`${walkPath} does not exist — run tools/publish.sh first`];
  const source = readFileSync(sourcePath, 'utf8');
  const published = readFileSync(walkPath, 'utf8');
  const fromSource = stripComments(source);
  const shipped = stripComments(published);
  if (shipped.removed.length) {
    bad.push(`walk/index.html ships ${shipped.removed.length} developer comment(s), first: `
      + JSON.stringify(shipped.removed[0].slice(0, 80)));
  }
  for (const ph of source.match(/<!--[A-Z0-9_]+-->/g) || []) {
    if (!fromSource.html.includes(ph)) bad.push(`the strip loses the source's placeholder ${ph}`);
  }
  if (unstamp(published) !== fromSource.html) {
    const a = unstamp(published);
    const b = fromSource.html;
    let k = 0;
    while (k < a.length && a[k] === b[k]) k++;
    bad.push('walk/index.html is not the source with its comments stripped and its stamp applied; '
      + `first difference at offset ${k}: shipped ${JSON.stringify(a.slice(k, k + 60))}, `
      + `expected ${JSON.stringify(b.slice(k, k + 60))}`);
  }
  if (shipped.raw.length !== fromSource.raw.length) {
    bad.push(`walk/index.html has ${shipped.raw.length} script/style/textarea/pre bodies, the source ${fromSource.raw.length}`);
  } else {
    shipped.raw.forEach((r, k) => {
      if (r.name !== fromSource.raw[k].name || r.body !== fromSource.raw[k].body) {
        bad.push(`the ${k + 1}${['st', 'nd', 'rd'][k] || 'th'} raw element (<${r.name}>) is not the source's byte for byte`);
      }
    });
  }
  const { door } = await import('./write_entry_pages.mjs');
  for (const year of readdirSync(site).filter((d) => /^\d{4}$/.test(d)).sort()) {
    const p = path.join(site, year, 'index.html');
    if (!existsSync(p)) continue;
    const html = readFileSync(p, 'utf8');
    if (!html.includes('<base href="../walk/">')) continue; // a planned year's pending page
    if (html !== door(published, '../walk/')) bad.push(`${year}/index.html is not walk/index.html plus its <base>`);
    if (stripComments(html).removed.length) bad.push(`${year}/index.html ships developer comments`);
  }
  return bad;
}

function selfTest() {
  const fail = [];
  const ok = (cond, what) => { if (!cond) fail.push(what); };
  const page = [
    '<!doctype html>',
    '<html><head>',
    '<title>a <!-- not a comment --> title</title>',
    '<!-- a note',
    '     on two lines -->',
    '<meta name="x" content="<!-- in an attribute -->">',
    '<!--[if IE]><p>old</p><![endif]-->',
    '<style>/* <!-- */ .a{} </style>',
    '<script>var s = "<!-- kept -->"; // <!-- also kept\n</script>',
    '</head><body>',
    '  <p>one<!-- inline -->two</p>  <!-- trailing note -->',
    '  <p class="gate-build" id="gate-build" hidden><!--BUILD_STAMP--></p>',
    '<pre>  <!-- shown -->\n</pre><textarea><!-- typed --></textarea>',
    '<noscript><!-- n --></noscript><img alt=don\'t src="x"><!-- after an unquoted apostrophe -->',
    '<!---->',
    '</body></html>',
  ].join('\n');
  const r = stripComments(page);
  ok(!r.html.includes('a note') && !r.html.includes('on two lines'), 'a multi-line note is stripped');
  ok(!r.html.includes('<!-- a note') && r.html.includes('</title>\n<meta name="x"'), 'a note alone on its lines takes its lines with it');
  ok(r.html.includes('content="<!-- in an attribute -->"'), 'a <!-- inside an attribute value is not a comment');
  ok(r.html.includes('<title>a <!-- not a comment --> title</title>'), '<title> is raw text and untouched');
  ok(r.html.includes('<!--[if IE]><p>old</p><![endif]-->'), 'a conditional comment is kept');
  ok(r.html.includes('<style>/* <!-- */ .a{} </style>'), '<style> is untouched');
  ok(r.html.includes('<script>var s = "<!-- kept -->"; // <!-- also kept\n</script>'), '<script> is untouched');
  ok(r.html.includes('<p>onetwo</p>  \n'), 'an inline note goes and leaves its neighbours as they were');
  ok(!r.html.includes('trailing note'), 'a note after markup on its line is stripped');
  ok(r.html.includes('<!--BUILD_STAMP-->'), 'a placeholder survives');
  ok(r.html.includes('<pre>  <!-- shown -->\n</pre>') && r.html.includes('<textarea><!-- typed --></textarea>'), '<pre> and <textarea> are untouched');
  ok(r.html.includes('<noscript><!-- n --></noscript>'), '<noscript> is untouched');
  ok(!r.html.includes('after an unquoted apostrophe'), 'an unquoted attribute value holding a quote does not swallow the page');
  ok(!r.html.includes('<!---->'), 'an empty comment is stripped');
  ok(r.removed.length === 5 && r.kept.length === 2, `5 removed and 2 kept (got ${r.removed.length} and ${r.kept.length})`);
  ok(r.raw.map((x) => x.name).join(',') === 'title,style,script,pre,textarea,noscript', `raw elements in order (got ${r.raw.map((x) => x.name)})`);
  ok(stripComments(r.html).html === r.html, 'the strip is idempotent');
  let threw = false;
  try { stripComments('<p><!-- never closed</p>'); } catch { threw = true; }
  ok(threw, 'an unterminated comment is refused rather than eating the page');
  // The stamp round trip --check leans on.
  const stamped = r.html.replace(GATE_PLACEHOLDER, '<p class="gate-build" id="gate-build">build abc1234 · Oct 18, 2026</p>');
  ok(stamped !== r.html && unstamp(stamped) === r.html, 'unstamp puts the gate stamp back to its source form');
  // The real page: the rules hold on what actually ships.
  const real = readFileSync(path.join(ROOT4D, 'renderers/web/index.html'), 'utf8');
  const rr = stripComments(real);
  ok(rr.removed.length > 0, 'the source page has developer comments to strip');
  ok(rr.html.includes(GATE_PLACEHOLDER), 'the source page\'s gate placeholder survives the strip whole');
  ok(rr.html.includes(RELEASES_PLACEHOLDER), 'the source page\'s release-number meta survives the strip');
  ok(stripComments(rr.html).removed.length === 0, 'the stripped source page carries no comment');
  for (const f of fail) console.error(`FAIL  ${f}`);
  if (!fail.length) console.log(`strip_page_comments self-test: ok (the source page sheds ${rr.removed.length} comments, ${real.length - rr.html.length} bytes)`);
  return fail.length ? 1 : 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  const arg = process.argv[2];
  if (arg === '--self-test') {
    process.exitCode = selfTest();
  } else if (arg === '--check') {
    const site = path.resolve(process.argv[3] || path.join(ROOT4D, '../../site/4d'));
    const bad = await problems(site);
    for (const b of bad) console.error(`FAIL  ${b}`);
    if (bad.length) process.exitCode = 1;
    else {
      const bytes = readFileSync(path.join(site, 'walk', 'index.html')).length;
      console.log(`the published walk page and its doors ship no developer comments (walk/index.html ${bytes.toLocaleString('en-US')} bytes)`);
    }
  } else if (arg && !arg.startsWith('--')) {
    const before = readFileSync(arg, 'utf8');
    const r = stripComments(before);
    writeFileSync(arg, r.html);
    const b = Buffer.byteLength(before);
    const a = Buffer.byteLength(r.html);
    console.log(`strip_page_comments: ${path.basename(path.dirname(arg))}/${path.basename(arg)} ${b.toLocaleString('en-US')} -> `
      + `${a.toLocaleString('en-US')} bytes (${r.removed.length} developer comments out, ${r.kept.length} placeholder(s) kept)`);
  } else {
    console.error('usage: strip_page_comments.mjs <page.html> | --check [site/4d] | --self-test');
    process.exitCode = 2;
  }
}
