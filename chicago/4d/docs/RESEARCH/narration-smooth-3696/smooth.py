#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3696: the smooth narration style, applied to direction files (data/narration/direction/).

The owner, 2026-11-19, of the 3rd-grade Glessner Household: "there is not a lot of transition
between topics and also pauses between subjects topics as they speak"; "the parts where they
whisper and laugh could be toned down a bit"; then "that smother narration rule applies for all
the jaunts". docs/AUDIO.md § Narration style says the rule; tools/test_narration.mjs checks every
direction marked "style": "smooth" (no whispering, at most one laugh, a pause every 50 words).

    python3 docs/RESEARCH/narration-smooth-3696/smooth.py --restyle ID...   # an existing direction, in place
    python3 docs/RESEARCH/narration-smooth-3696/smooth.py --draft ID [--tag STOP=TAG ...]
                                                                            # a new direction from the panel's words

--restyle keeps a direction's own reading and only tones it down: a whisper becomes [quietly],
laughs after a script's first are dropped, and a [short pause] goes in at a sentence end wherever
a run passes 50 words without one. --draft writes a plain reading: a lead tag ([measured] unless
--tag gives one), a pause after a stop's opening time-and-place line, at each paragraph, before the
stop's last sentence (its hand-on), and at a sentence end wherever a run passes 42 words. A draft
is a start: read it, then tune tags and pauses by hand. Neither changes a word: test_narration
fails any direction whose words differ from its panel's. The joining lines between subjects are
words, written into the jaunt itself, never here.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIRS = ROOT / 'data/narration/direction'
WORDS_PER_PAUSE = 50          # tools/narrate_jaunts.mjs SMOOTH.words_per_pause
P = '[short pause]'
WHISPER = re.compile(r'\[(?:whispers?|whispering|lowering voice)[^\]]*\]', re.I)
LAUGH = re.compile(r'\[(?:laughs?|laughing|chuckles?|chuckling|giggles?|giggling|snickers?)[^\]]*\]', re.I)
PAUSE = re.compile(r'\[(?:short |long )?pause\]|\.\.\.|…', re.I)
ABBR = r'(?:Mrs|Mr|Dr|St|Capt|Gen|Lt|Col|No|Jr|Sr|Mt|Ft|vs|Co|Bros)'
END = re.compile(r"""[.!?]['"”’]{0,2}(?=\s+[\[A-Z0-9'"“‘(])""")
COMMENT = ("T-3578 format, the smooth style (T-3696; docs/AUDIO.md § Narration style): the same words as the panel "
           "shows, with ElevenLabs v3 audio tags in square brackets and [short pause]/[long pause] and ellipses for "
           "pauses, a pause at each change of subject, no whispering, at most one laugh. Performance only: a tone is a "
           "reading, not evidence of how anyone spoke (L-jaunt-voices-3578). Keyed <part>:<id>.")


def words(text):
    return len(re.findall(r'[\w]+', re.sub(r'\[[^\]]*\]', ' ', text)))


def sentences(text):
    prot = re.sub(r'\b(' + ABBR + r')\.', r'\1<DOT>', text.strip())
    prot = re.sub(r'\b([A-Z])\.(?=\s*[A-Z])', r'\1<DOT>', prot)
    out, start = [], 0
    for m in END.finditer(prot):
        out.append(prot[start:m.end()].strip())
        start = m.end()
    out.append(prot[start:].strip())
    return [x.replace('<DOT>', '.') for x in out if x]


def tidy(text):
    return re.sub(r'[ \t]{2,}', ' ', re.sub(r'\[\s*\]', '', text)).strip()


def tone_down(text):
    text = WHISPER.sub('[quietly]', text)
    seen = [0]

    def keep_first(m):
        seen[0] += 1
        return m.group(0) if seen[0] == 1 else ''
    return tidy(LAUGH.sub(keep_first, text))


def fill_pauses(text):
    """A [short pause] at a sentence end inside any run of more than WORDS_PER_PAUSE words."""
    out = []
    for para in text.split('\n\n'):
        ss, res, run = sentences(para), [], 0
        for s in ss:
            if re.match(r'(?:\[[^\]]*\]\s*)*' + PAUSE.pattern, s, re.I):
                run = 0                                   # it opens with a pause already
            if res and run and run + words(s) > WORDS_PER_PAUSE and not PAUSE.search(res[-1][-16:]):
                res.append(P)
                run = 0
            res.append(s)
            run = 0 if PAUSE.search(s) else run + words(s)
        out.append(' '.join(res))
    return '\n\n'.join(out)


def restyle(text):
    return fill_pauses(tone_down(text))


def draft(text, tag='[measured]', stop=True, every=42):
    out = []
    for pi, para in enumerate(text.split('\n\n')):
        ss, res, run = sentences(para), [], 0
        for i, s in enumerate(ss):
            last = i == len(ss) - 1 and len(ss) > 2
            if i > 0 and ((stop and i == 1 and pi == 0) or last or run + words(s) > every):
                res.append(P)
                run = 0
            res.append(s)
            run += words(s)
        out.append((P + ' ' if pi else '') + ' '.join(res))
    return (tag + ' ' if tag else '') + '\n\n'.join(out)


def write(path, doc):
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--restyle', nargs='+', default=[])
    ap.add_argument('--draft')
    ap.add_argument('--tag', action='append', default=[], help='STOP_ID=[tag] (opening/ending ids too)')
    a = ap.parse_args()
    for jid in a.restyle:
        path = DIRS / f'{jid}.json'
        doc = json.loads(path.read_text())
        scripts = {k: restyle(v) for k, v in doc['scripts'].items()}
        doc = {'$comment': doc.get('$comment', COMMENT), 'version': 1, 'jaunt': jid, 'style': 'smooth', 'scripts': scripts}
        write(path, doc)
        print(f'restyled {path.relative_to(ROOT)}')
    if a.draft:
        tags = dict(t.split('=', 1) for t in a.tag)
        got = json.loads(subprocess.run(['node', str(Path(__file__).with_name('scripts.mjs')), a.draft],
                                        check=True, capture_output=True, text=True).stdout)[a.draft]
        scripts = {}
        for s in got:
            part, sid = s['key'].split(':', 1)
            scripts[s['key']] = draft(s['text'], tags.get(sid, '[measured]'), stop=part == 'stop')
        path = DIRS / f'{a.draft}.json'
        write(path, {'$comment': COMMENT, 'version': 1, 'jaunt': a.draft, 'style': 'smooth', 'scripts': scripts})
        print(f'drafted {path.relative_to(ROOT)}: {len(scripts)} scripts, {sum(map(len, scripts.values()))} characters')


if __name__ == '__main__':
    main()
