"""Read sparse SOURCE asset inputs through an exact frozen Git blob overlay.
Only assets/ byte/metadata reads and recursive listings are redirected. Code and
record IO stays in SOURCE. Every canonical asset read is Git-SHA1 authenticated
against that SOURCE HEAD's tree. No filesystem/source/Git mutation occurs.
"""
from pathlib import Path
import fnmatch,hashlib,json,stat,subprocess
class FrozenAssetOverlay:
 def __init__(self,repo,asset_root,head):
  self.repo=repo;self.logical_root=repo/'chicago/4d/assets';self.actual=asset_root;self.head=head;self.reads={}
  raw=subprocess.check_output(['git','ls-tree','-r','-z',head,'--','chicago/4d/assets'],cwd=repo)
  self.oids={}
  for row in raw.split(b'\0'):
   if not row:continue
   meta,name=row.split(b'\t',1);mode,kind,oid=meta.split()
   if kind==b'blob':self.oids[name.decode().removeprefix('chicago/4d/assets/')]=oid.decode()
 def key(self,p):
  try:return p.relative_to(self.logical_root).as_posix()
  except ValueError:return None
 def install(self):
  self._read=Path.read_bytes;self._stat=Path.stat;self._rglob=Path.rglob
  overlay=self
  def read(p):
   key=overlay.key(p)
   if key is None:return overlay._read(p)
   if key not in overlay.oids:return overlay._read(p)
   actual=overlay.actual/key;raw=overlay._read(actual);oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
   assert oid==overlay.oids[key],('canonical asset input differs from frozen SOURCE Git blob',key,oid,overlay.oids[key])
   overlay.reads['chicago/4d/assets/'+key]={'actual_read_path':str(actual),'git_blob':oid,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()};return raw
  def pstat(p,*a,**kw):
   key=overlay.key(p)
   if key in overlay.oids:return overlay._stat(overlay.actual/key,*a,**kw)
   return overlay._stat(p,*a,**kw)
  def rglob(p,pattern,*a,**kw):
   key=overlay.key(p)
   if key is None:return overlay._rglob(p,pattern,*a,**kw)
   prefix=''if key=='.'else key.rstrip('/')+'/'
   return (overlay.logical_root/name for name in sorted(overlay.oids)if name.startswith(prefix)and fnmatch.fnmatchcase(name[len(prefix):],str(pattern)))
  Path.read_bytes=read;Path.stat=pstat;Path.rglob=rglob
  return self
 def uninstall(self):
  Path.read_bytes=self._read;Path.stat=self._stat;Path.rglob=self._rglob
