import sys
from PIL import Image
import numpy as np
im=np.asarray(Image.open(sys.argv[1]).convert('L'),dtype=float)
x0,x1,y0,y1=map(int,sys.argv[2:6])
prof=im[y0:y1,x0:x1].mean(axis=1)
p=prof-np.convolve(prof,np.ones(15)/15,mode='same')
p=p[8:-8]
F=np.abs(np.fft.rfft(p*np.hanning(len(p)),n=4096))
fr=np.fft.rfftfreq(4096)
m=(fr>1/20)&(fr<1/3)
k=np.argmax(F*m)
print('period px', 1/fr[k], 'len', y1-y0)
