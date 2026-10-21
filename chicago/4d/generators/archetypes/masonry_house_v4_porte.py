"""T-2217: the paired oak carriage doors, from HABS sheet 6.

The sheet supplies the 3-by-6 circular/square fields and paired ring plates.
HABS data p.21 records the heavy straps and latches; the circa-1888 photograph
is a historical cross-check, never a texture or traced asset. Depths, scroll
curves and the unseen boarded backs are bounded reconstructions. See liberty
L-glessner-porte-cochere-2217. Both diagnostic closed and ordinary open poses
use these same members, rotated about their actual hinge axes.
"""
from __future__ import annotations
import math

WOOD, IRON = 6, 10
FRONT, FIELD, BACK, HINGE = -.18, -.215, -.27, -.28
COLS = (.15, .44, .73)
ROWS = (.12, .26, .40, .54, .74, .88)  # from top


def unit(v):
    d=math.sqrt(sum(x*x for x in v)) or 1
    return tuple(x/d for x in v)


class Leaf:
    def __init__(self,b,o,side,angle):
        self.b,self.o,self.side=b,o,side
        self.reduced=not getattr(b,'smooth_rock_faces',True)
        self.conf=max(o['conf'],b.params.detail.get('conf',1.0));self.angle=angle*(1 if side==0 else -1)
        joinery=b.params.detail.get('joinery',{})
        self.cols=tuple(joinery.get('porte_cochere_panel_columns',COLS))
        self.rows=tuple(joinery.get('porte_cochere_panel_rows',ROWS))
        assert list(joinery.get('porte_cochere_panels_per_leaf',[3,6]))==[len(self.cols),len(self.rows)]==[3,6], 'HABS carriage leaves have three columns and six rows'
        self.outer=o['u0']+.055 if side==0 else o['u1']-.055
        self.meeting=(o['u0']+o['u1'])/2+(-.006 if side==0 else .006)
        self.hinge=o['u0']+.085 if side==0 else o['u1']-.085
        self.w=abs(self.meeting-self.outer)
        fg=b.params.detail.get('prairie_frontage',{})
        # T-2976: the leaves hang down to the sunk passage floor (sheet 6 draws them to
        # 1.9 ft under the door datum), clearing it as they swing in over its rise.
        self.bottom=fg['passage_front_z']+.03 if 'passage_front_z' in fg else o['z0']+.02
        self.top=o['z1']-.02;self.h=self.top-self.bottom
        self.member=0

    def local(self,f,t,d):
        return (self.outer+(self.meeting-self.outer)*f,self.top-self.h*t,d)

    def point(self,u,z,d):
        # Glessner's east plane: +x outward, u north, z up.
        x=self.o['at']+d; hx=self.o['at']+HINGE
        co,si=math.cos(self.angle),math.sin(self.angle)
        return (hx+co*(x-hx)-si*(u-self.hinge),
                self.hinge+si*(x-hx)+co*(u-self.hinge),z)

    def vector(self,n):
        co,si=math.cos(self.angle),math.sin(self.angle)
        return (co*n[0]-si*n[1],si*n[0]+co*n[1],n[2])

    def face(self,pts,mat=WOOD,want=(1,0,0),grain='upright'):
        ids=self.b.raw([self.point(*p) for p in pts],self.conf,mat,self.vector(want))
        # Texture coordinates belong to each member before it rotates. Thus
        # opening a leaf rotates its oak grain with it, instead of smearing it.
        uv=getattr(self.b,'roof_uvs',None)
        if ids and uv is not None and mat==WOOD:
            for i in ids:
                x,y,z=self.b.verts[i];hx=self.o['at']+HINGE
                u=self.hinge-math.sin(self.angle)*(x-hx)+math.cos(self.angle)*(y-self.hinge)
                d=HINGE+math.cos(self.angle)*(x-hx)+math.sin(self.angle)*(y-self.hinge)
                axis=max(range(3),key=lambda k:abs(want[k]))
                s,t=(u,z) if axis==0 else ((d,z) if axis==1 else (u,d))
                shift=self.member if grain=='panel' else 0
                uv[i]=(s+.377*shift,t+.911*shift)

    def rect(self,f0,f1,t0,t1,d,mat=WOOD,back=False):
        pts=[self.local(f,t,d) for f,t in [(f0,t1),(f1,t1),(f1,t0),(f0,t0)]]
        self.face(pts,mat,(-1,0,0) if back else (1,0,0))

    def prism(self,poly,d0,d1,mat=IRON,bevel=0):
        pts=[self.local(f,t,d1-bevel) for f,t in poly]
        if bevel:
            cu=sum(p[0] for p in pts)/len(pts);cz=sum(p[1] for p in pts)/len(pts)
            face=[(cu+.93*(p[0]-cu),cz+.93*(p[1]-cz),d1) for p in pts]
            self.face(face,mat)
            for i in range(len(pts)):
                j=(i+1)%len(pts);self.face([pts[i],pts[j],face[j],face[i]],mat)
        else:self.face(pts,mat)
        for p,q in zip(pts,pts[1:]+pts[:1]):
            # Surface normal is chosen geometrically, independent of leaf
            # handedness. The mesh builder fixes winding against this normal.
            centre=(sum(x[0] for x in pts)/len(pts),sum(x[1] for x in pts)/len(pts))
            n=unit((0,(p[0]+q[0])/2-centre[0],(p[1]+q[1])/2-centre[1]))
            self.face([(p[0],p[1],d0),(q[0],q[1],d0),q,p],mat,n)

    def band(self,path,width,depth=FRONT+.008):
        """Flat iron stock in the door plane, including reconstructed curls."""
        q=[self.local(f,t,depth) for f,t in path]
        edges=[]
        for i,p in enumerate(q):
            a,c=q[max(0,i-1)],q[min(len(q)-1,i+1)]
            n=unit((-(c[1]-a[1]),c[0]-a[0]))
            edges.append(((p[0]+n[0]*width/2,p[1]+n[1]*width/2,depth),
                          (p[0]-n[0]*width/2,p[1]-n[1]*width/2,depth)))
        for a,c in zip(edges,edges[1:]):
            self.face([a[0],c[0],c[1],a[1]],IRON)
            if not self.reduced:
                for p,q in [(a[0],c[0]),(c[1],a[1])]:
                    self.face([(p[0],p[1],FRONT),(q[0],q[1],FRONT),q,p],IRON,
                              (0,q[1]-p[1],p[0]-q[0]))

    def tube(self,path,radius,sides=6):
        rings=[]
        closed=math.dist(path[0],path[-1])<1e-8
        for i,p in enumerate(path):
            a,c=(path[-2],path[1]) if closed and i in (0,len(path)-1) else (path[max(0,i-1)],path[min(len(path)-1,i+1)])
            du,dz=c[0]-a[0],c[1]-a[1];length=math.hypot(du,dz) or 1
            rings.append([(p[0]-radius*dz/length*math.cos(t),p[1]+radius*du/length*math.cos(t),p[2]+radius*math.sin(t))
                          for t in [2*math.pi*k/sides for k in range(sides)]])
        for i in range(len(rings)-1):
            for j in range(sides):
                k=(j+1)%sides;quad=[rings[i][j],rings[i+1][j],rings[i+1][k],rings[i][k]]
                m=tuple(sum(q[n] for q in quad)/4 for n in range(3))
                p=tuple((path[i][n]+path[i+1][n])/2 for n in range(3))
                self.face(quad,IRON,(m[2]-p[2],m[0]-p[0],m[1]-p[1]))

        if not closed:
            for i,j,sign in [(0,1,-1),(-1,-2,-1)]:
                v=tuple(sign*(path[j][k]-path[i][k]) for k in range(3))
                self.face(rings[i],IRON,(v[2],v[0],v[1]))

    def panel(self,f,t,fb,tb):
        self.member+=1
        u,z,_=self.local(f,t,FRONT);radius=self.w*.12
        corners=[self.local(x,y,FRONT) for x,y in [(fb[0],tb[0]),(fb[1],tb[0]),(fb[1],tb[1]),(fb[0],tb[1])]]
        lo,hi=min(p[0] for p in corners),max(p[0] for p in corners)
        low,high=min(p[1] for p in corners),max(p[1] for p in corners)
        # Include every cell corner as well as regular circle samples, so the
        # cells tile the front with neither overlapping faces nor tiny gaps.
        count=8 if self.reduced else 64
        angles=sorted(set([round(2*math.pi*k/count,12) for k in range(count)]+
                          [round(math.atan2(q[1]-z,q[0]-u)%(2*math.pi),12) for q in corners]))
        outer=[];rim=[];inner=[]
        half=radius*.695
        for th in angles:
            co,si=math.cos(th),math.sin(th)
            ru=((hi-u) if co>=0 else (u-lo))/max(abs(co),1e-12)
            rz=((high-z) if si>=0 else (z-low))/max(abs(si),1e-12)
            reach=min(ru,rz)
            outer.append((u+reach*co,z+reach*si,FRONT))
            rim.append((u+radius*co,z+radius*si,FRONT))
            reach=half/max(abs(co),abs(si))
            inner.append((u+reach*co,z+reach*si,FIELD))
        for i in range(len(angles)):
            j=(i+1)%len(angles)
            self.face([outer[i],outer[j],rim[j],rim[i]])
            self.face([rim[i],rim[j],inner[j],inner[i]])
        self.face([(u-half,z-half,FIELD),(u+half,z-half,FIELD),(u+half,z+half,FIELD),(u-half,z+half,FIELD)],grain='panel')

    def body(self):
        fcuts=[0]+[(a+b)/2 for a,b in zip(self.cols,self.cols[1:])]+[1]
        tcuts=[0]+[(a+b)/2 for a,b in zip(self.rows,self.rows[1:])]+[1]
        for row,t in enumerate(self.rows):
            for col,f in enumerate(self.cols):self.panel(f,t,fcuts[col:col+2],tcuts[row:row+2])
        # The original views show no reverse. Plain vertical boarding with
        # shallow joints is declared reconstruction, not copied front hardware.
        if self.reduced:
            self.rect(0,1,0,1,BACK,back=True)
        else:
            for i in range(8):
                left=i/8;right=(i+1)/8;gap=.0015/self.w
                self.rect(left+(gap if i else 0),right-(gap if i<7 else 0),0,1,BACK,back=True)
                if i:
                    self.rect(left-gap,left+gap,0,1,BACK+.003,back=True)
                    for f,n in [(left-gap,(0,1,0)),(left+gap,(0,-1,0))]:
                        self.face([self.local(f,0,BACK),self.local(f,1,BACK),self.local(f,1,BACK+.003),self.local(f,0,BACK+.003)],WOOD,n)
        for a,c in [((0,0),(1,0)),((1,0),(1,1)),((1,1),(0,1)),((0,1),(0,0))]:
            p,q=self.local(*a,FRONT),self.local(*c,FRONT)
            centre=self.local(.5,.5,FRONT)
            self.face([(p[0],p[1],BACK),(q[0],q[1],BACK),q,p],WOOD,
                      (0,(p[0]+q[0])/2-centre[0],(p[1]+q[1])/2-centre[1]))

    def stud(self,f,t,r,depth):
        du=r/self.w;dt=r/self.h
        base=[self.local(x,y,depth) for x,y in [(f-du,t),(f,t-dt),(f+du,t),(f,t+dt)]]
        tip=self.local(f,t,depth+.011)
        for p,q in zip(base,base[1:]+base[:1]):self.face([p,q,tip],IRON)

    def hardware(self):
        for t in (.045,.64,.955):
            self.band([(.01,t),(.965,t)],self.h*.019)
            if not self.reduced:
                for f in (.065,.26,.48,.70,.92):
                    self.stud(f,t,.010,FRONT+.008)
        # Scroll outlines are reconstructed around the documented straps, not
        # lifted from the museum scan. The reduced silhouette keeps the straps.
        if not self.reduced:
            for t,sgn in [(.045,1),(.955,-1)]:
                path=[]
                for i in range(34):
                    q=i/33;th=-math.pi/2+2.65*math.pi*q
                    rad=.036*self.h*(1-.90*q)
                    path.append((.915+rad*math.cos(th)/self.w,t+sgn*(.036+rad*math.sin(th)/self.h)))
                self.band(path,.010,FRONT+.011)
        if not self.reduced:
            tail=[]
            for i in range(24):
                q=i/23;th=-math.pi/2+2.6*math.pi*q;rad=.013*self.h*(1-.88*q)
                tail.append((.965+rad*math.cos(th)/self.w,.968+rad*math.sin(th)/self.h))
            self.band(tail,.008,FRONT+.011)
            self.prism([(.005,.608),(.075,.631),(.005,.649)],FRONT+.008,FRONT+.012)
        plate=[(.835,.595),(.845,.585),(.98,.585),(.99,.595),(.99,.702),(.98,.712),(.845,.712),(.835,.702)]
        self.prism(plate,FRONT+.009,FRONT+.017,bevel=0 if self.reduced else .004)
        if not self.reduced:
            for t in (.60,.70):
                path=[]
                for i in range(25):
                    q=i/24;th=math.pi/2+2.5*math.pi*q;rad=.025*self.h*(1-.86*q)
                    path.append((.812+rad*math.cos(th)/self.w,t+rad*math.sin(th)/self.h))
                self.band(path,.009,FRONT+.018)
            for f in (.85,.975):
                for t in (.60,.63,.69):
                    self.stud(f,t,.008,FRONT+.017)
        centre=self.local(.91,.65,FRONT+.033);radius=self.h*.026
        n=10 if self.reduced else 28
        path=[(centre[0]+radius*math.cos(2*math.pi*k/n),centre[1]+radius*math.sin(2*math.pi*k/n),centre[2]) for k in range(n+1)]
        self.tube(path,.007,4 if self.reduced else 8)
        du=.014/self.w;dt=.016/self.h
        self.prism([(.91-du,.617),(.91,.617-dt),(.91+du,.617),(.91,.617+dt)],FRONT+.017,FRONT+.042)
        for t in (.045,.64,.955):
            _,z,_=self.local(.028,t,FRONT)
            u,d=self.hinge,HINGE
            self.tube([(u,z-.047,d),(u,z+.047,d)],.013,4 if self.reduced else 8)
            edge=self.outer+(-.003 if self.side==0 else .003)
            wrap=[(edge,FRONT+.008),(edge,BACK-.008),(self.hinge,BACK-.008)]
            half=self.h*.0095
            for (ua,da),(ub,db) in zip(wrap,wrap[1:]):
                want=(0,-1 if self.side==0 else 1,0) if abs(ua-ub)<1e-9 else (-1,0,0)
                self.face([(ua,z-half,da),(ub,z-half,db),(ub,z+half,db),(ua,z+half,da)],IRON,want)


def build(b,o,angle_deg=None):
    assert o['axis']=='x' and o['sign']==1,'Porte-cochere belongs to the east plane'
    angle=math.radians(b.params.detail.get('porte_cochere_open_deg',82) if angle_deg is None else angle_deg)
    for side in range(2):
        leaf=Leaf(b,o,side,angle);leaf.body();leaf.hardware()
    # Fixed oak linings fill the two side clearances behind the stone jambs.
    # A back-edge hinge lets the whole leaf swing clear of these linings.
    fixed=Leaf(b,o,0,0)
    fixed.bottom=b.params.detail.get('prairie_frontage',{}).get('passage_front_z',o['z0'])-.002
    fixed.top=o['z1']+.001;fixed.h=fixed.top-fixed.bottom
    for ua,ub in [(o['u0'],o['u0']+.05),(o['u1']-.05,o['u1'])]:
        fa=(ua-fixed.outer)/fixed.w;fb=(ub-fixed.outer)/fixed.w
        fixed.prism([(fa,0),(fb,0),(fb,1),(fa,1)],BACK-.015,FRONT+.01,WOOD)
        fixed.rect(fa,fb,0,1,BACK-.015,back=True)
    for side in (0,1):
        leaf=Leaf(b,o,side,0)
        ua,ub=(o['u0']+.025,leaf.hinge+.010) if side==0 else (leaf.hinge-.010,o['u1']-.025)
        fa,fb=(ua-fixed.outer)/fixed.w,(ub-fixed.outer)/fixed.w
        for t in (.045,.64,.955):
            z=leaf.local(0,t,FRONT)[1]
            ta,tb=(fixed.top-z-.025)/fixed.h,(fixed.top-z+.025)/fixed.h
            fixed.prism([(fa,ta),(fb,ta),(fb,tb),(fa,tb)],HINGE-.018,BACK-.011,IRON)
