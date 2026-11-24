# Find skips in a film: a frame whose change from the last is far above (or far below) its neighbours (T-3744).
# python3 skips.py FILM.mp4
import subprocess,sys,numpy as np
f=sys.argv[1]; W,H=160,90
raw=subprocess.run(['ffmpeg','-loglevel','error','-i',f,'-vf',f'scale={W}:{H}','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True).stdout
fr=np.frombuffer(raw,np.uint8).reshape(-1,H,W).astype(np.float32)
d=np.abs(np.diff(fr,axis=0)).mean(axis=(1,2))
med=np.array([np.median(d[max(0,i-6):i+7]) for i in range(len(d))])
print(f, len(fr),'frames')
for i,(x,m) in enumerate(zip(d,med)):
    if x>2.2*m+0.5 or x<0.25*m: print(f'  {i}->{i+1} t={(i+1)/24:.2f}s diff={x:.2f} med={m:.2f}')
