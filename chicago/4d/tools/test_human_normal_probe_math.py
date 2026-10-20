import copy,json,math,random,struct,unittest
from pathlib import Path
from human_normal_probe_math import *
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
def frame(A=math.pi/2,B=math.pi/2,yaw=0):return ((0,0,1),(math.cos(yaw),math.sin(yaw),0),(-math.sin(yaw),math.cos(yaw),0),A,B)
def probes(f,rounded=False):return {name:tuple(f32(x)for x in decode(f,code))if rounded else decode(f,code)for name,code in PROBES.items()}
class Adapter:
 def __init__(self,fail_final=False):
  self.frames=[frame(),frame(yaw=.4)];self.codes=[(32767,0)]*4;self.calls=[];self.updates=0;self.fail_final=fail_final
 def read_codes(self):return self.codes[:]
 def invariant_digest(self):return 'EXPLICIT ANALYTIC MOCK invariant'
 def write_codes(self,codes):self.codes=list(codes);self.calls.append(list(codes))
 def update(self):self.updates+=1
 def read_normals(self):
  points=[]
  for fan,f in enumerate(self.frames):
   codes=self.codes[2*fan:2*fan+2];average=tuple(int(sum(code[a]for code in codes)/len(codes))for a in [0,1]);value=decode(f,average)
   if self.fail_final and self.updates==6:value=(0,1,0)
   points.extend([value,value])
  return points
class Tests(unittest.TestCase):
 def test_counterexample_recovered_without_ordinary_beta_snap(self):
  f=frame();r,errors=recover(probes(f));target=(math.cos(.01),math.sin(.01),0);code=inverse(r,target)
  self.assertNotEqual(code[1],0);self.assertLess(distance(decode(f,code),target),1e-3);self.assertGreater(distance(decode(f,(32767,0)),target),.009)
 def test_seeded_frames_signed_branches_and_float32_probe_outputs(self):
  rng=random.Random(8127);maximum=0;count=0
  for _ in range(1000):
   f=frame(rng.uniform(.08,math.pi-.08),rng.uniform(.08,2*math.pi),rng.uniform(-math.pi,math.pi));r,residual=recover(probes(f,True))
   for _ in range(10):
    target=unit((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)),tolerance=10);code=inverse(r,target);error=distance(decode(f,code),target);maximum=max(maximum,error);count+=1;self.assertLess(error,1e-3)
 def test_max_beta_quarter_above_pi_over_two_works(self):
  f=frame(B=2*math.pi);r,_=recover(probes(f));self.assertAlmostEqual(r[4],2*math.pi);self.assertGreater(8192/S*2*math.pi,math.pi/2)
 def test_degenerate_or_corrupt_probes_fail_closed(self):
  for f in [frame(A=0),frame(A=math.pi),frame(A=1e-6),frame(B=0),frame(A=.0142,B=.0142)]:
   with self.assertRaises(Refused):recover(probes(f))
  for key,value in [('zero',(0,0,0)),('alpha',(float('nan'),0,0)),('negative_beta',(1,0,0))]:
   p=probes(frame());p[key]=value
   with self.assertRaises(Refused):recover(p)
 def test_full_probe_uniformity_coherence_and_success(self):
  a=Adapter();target=(math.cos(.01),math.sin(.01),0);r=prototype_transaction(a,[0,0,1,1],[10]*4,[target]*4)
  self.assertLess(r['maximum_target_delta'],1e-3);self.assertLess(r['maximum_seam_spread'],1e-3)
  for call in a.calls[:5]:self.assertEqual(len(set(call)),1)
  self.assertEqual(a.codes[0],a.codes[1]);self.assertEqual(a.codes[2],a.codes[3]);self.assertNotEqual(a.codes[0],a.codes[2])
 def test_failure_restores_original_codes(self):
  a=Adapter(fail_final=True);original=a.read_codes();target=(math.cos(.01),math.sin(.01),0)
  with self.assertRaises(Refused):prototype_transaction(a,[0,0,1,1],[10]*4,[target]*4)
  self.assertEqual(a.read_codes(),original);self.assertEqual(a.updates,7)
 def test_incoherent_target_and_malformed_codes_refuse(self):
  p=probes(frame());
  with self.assertRaises(Refused):recover_group_codes([0,0],[p,p],[(1,0,0),(0,1,0)])
  for code in [(True,0),(-32768,0),(0,32768)]:
   with self.assertRaises(Refused):decode(frame(),code)
if __name__=='__main__':unittest.main()
