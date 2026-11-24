#!/usr/bin/env python3
"""hero.py FILMS_DIR OUT.mp4 — the home page's background: a silent montage, dissolve to dissolve,
whose last shot dissolves back into its first so the loop never jumps (T-3744)."""
import os, subprocess, sys
films, out = sys.argv[1:3]
W, H, FPS, X = 1600, 900, 24, 1.0
S = [('1904-prairie-walk', 1.0, 6.0), ('1812-fort-fly', 0.2, 5.5), ('1904-people-cards', 1.0, 5.5),
     ('1812-column', 3.0, 5.5), ('1835-forks-fly', 1.0, 5.0), ('1904-prairie-walk', 60.0, 6.0),
     ('1871-clark-street', 0.3, 5.5), ('1871-fire-night', 1.0, 5.0), ('1904-prairie-walk', 84.5, 6.5)]
args = ['ffmpeg', '-v', 'error', '-y']
for f, ss, ln in S: args += ['-ss', str(ss), '-t', str(ln), '-i', os.path.join(films, f + '.mp4')]
fc = ''.join(f'[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration={ln},trim=duration={ln},setpts=PTS-STARTPTS[v{i}];' for i, (_, _, ln) in enumerate(S))
# the first shot again, to dissolve the end into the start
fc += f'[v0]split[v0a][v0b];'
cur, t = '[v0a]', S[0][2]
for i in range(1, len(S)):
    t -= X; fc += f'{cur}[v{i}]xfade=transition=fade:duration={X}:offset={t:.3f}[x{i}];'; cur = f'[x{i}]'; t += S[i][2]
# loop seam: the montage's tail dissolves into the head of shot 0; the film then starts X in
t -= X; fc += f'{cur}[v0b]xfade=transition=fade:duration={X}:offset={t:.3f},trim=start={X},setpts=PTS-STARTPTS,trim=duration={t - X + X:.3f}[o]'
args += ['-filter_complex', fc, '-map', '[o]', '-an', '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', '27', '-preset', 'slow', '-movflags', '+faststart', out]
subprocess.check_call(args)
print(out, subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',out]).decode().strip(), os.path.getsize(out))
