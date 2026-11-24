#!/usr/bin/env python3
"""cut.py FILMS_DIR CARDS_DIR MUSIC OUT.mp4 — the 4D Chicago trailer (T-3744).

Each segment is cut to 1920x1080/24 with its card laid over it, faded from and to black where it
says so; the segments are joined and the complete main title theme laid under them."""
import json, os, subprocess, sys
films, cards, music, out = sys.argv[1:5]
W, H, FPS = 1920, 1080, 24
# (source film or None for black, start in source, length, card, card in, card out, fade in, fade out)
T = [
 (None,                 0,   3.6, 'c-open',   0.5, 3.0, 0,   0),
 ('1812-fort-fly',      0.5, 6.9, 'y-1812',   0.8, 6.0, 0.8, 0.5),
 ('1835-forks-fly',     0.5, 6.0, 'y-1835',   0.6, 5.2, 0.5, 0.5),
 ('1871-downtown-fly',  0.5, 6.0, 'y-1871',   0.6, 5.2, 0.5, 0.5),
 ('1904-prairie-walk',  0.5, 8.5, 'y-1904',   0.8, 7.4, 0.5, 0.7),
 (None,                 0,   3.0, 'c-record', 0.3, 2.6, 0,   0),
 ('1904-people-cards',  0.0, 5.8, 'c-meet',   0.8, 5.0, 0.6, 0.4),
 ('1904-host',          0.5, 3.9, None,       0,   0,   0.3, 0.5),
 (None,                 0,   1.4, 'c-saw',    0.1, 1.3, 0,   0),
 ('1812-column',        2.0, 4.0, None,       0,   0,   0,   0),
 ('1812-burning-wide',  1.0, 3.0, None,       0,   0,   0,   0),
 ('1871-fire-night',    1.0, 3.0, None,       0,   0,   0,   0),
 ('1904-prairie-walk', 62.0, 3.0, None,       0,   0,   0,   0),
 ('1812-column',       16.2, 3.0, None,       0,   0,   0,   0),
 ('1904-prairie-walk', -7.5, 5.8, None,       0,   0,   0,   0.8),
]
total = sum(t[2] for t in T)
DUR = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',music]))
TITLE = DUR - total
T.append((None, 0, TITLE, 'c-title', 0.4, TITLE - 1.6, 0, 1.4))
os.makedirs('seg', exist_ok=True)
segs = []
for i, (src, ss, ln, card, cin, cout, fin, fout) in enumerate(T):
    seg = f'seg/{i:02d}.mp4'
    args = ['ffmpeg', '-v', 'error', '-y']
    if src:
        f = os.path.join(films, src + '.mp4')
        d = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
        start = ss if ss >= 0 else d + ss
        args += ['-ss', f'{start:.3f}', '-t', f'{ln:.3f}', '-i', f]
        v = f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1,tpad=stop_mode=clone:stop_duration={ln:.3f},trim=duration={ln:.3f}'
    else:
        args += ['-f', 'lavfi', '-t', f'{ln:.3f}', '-i', f'color=c=0x070d18:s={W}x{H}:r={FPS}']
        v = '[0:v]setsar=1'
    if fin: v += f',fade=t=in:st=0:d={fin}'
    if fout: v += f',fade=t=out:st={ln - fout:.3f}:d={fout}'
    v += '[base]'
    if card:
        args += ['-loop', '1', '-t', f'{ln:.3f}', '-i', os.path.join(cards, card + '.png')]
        fc = f'{v};[1:v]format=rgba,fade=t=in:st={cin}:d=0.6:alpha=1,fade=t=out:st={cout}:d=0.5:alpha=1[c];[base][c]overlay=0:0:shortest=1,format=yuv420p[o]'
    else:
        fc = f'{v};[base]format=yuv420p[o]'
    args += ['-filter_complex', fc, '-map', '[o]', '-t', f'{ln:.3f}', '-r', str(FPS), '-c:v', 'libx264', '-crf', '16', '-preset', 'fast', seg]
    subprocess.check_call(args); segs.append(seg)
open('seg/list.txt', 'w').write(''.join(f"file '{os.path.basename(s)}'\n" for s in segs))
subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'seg/list.txt', '-i', music,
    '-filter_complex', f'[1:a]afade=t=out:st={DUR - 2.0:.2f}:d=2[a]', '-map', '0:v', '-map', '[a]',
    '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', '22', '-preset', 'slow',
    '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', '-shortest', out])
print(out, total + TITLE, os.path.getsize(out))
