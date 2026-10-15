"""Original reconstructed Glessner vines, shared by Full and Light.

The record owns placement, growth bounds, seed and clearance. Botanical history
is textual evidence; this is a declared July 1904 reconstruction, not a coverage
map traced from later overgrowth. The atlas is generated from these same stems
and original leaf profiles. Full emits curled leaves and attached stems; Light
uses that exact layout on continuous masked panels. No renderer-side planting.
"""
import math, random, json
from pathlib import Path

BOSTON=[(0,0),(-.30,.10),(-.47,.34),(-.58,.53),(-.28,.50),(-.19,.71),(0,1),(.19,.71),(.28,.50),(.58,.53),(.47,.34),(.30,.10)]
VIRGINIA=[(0,0),(-.14,.16),(-.22,.34),(-.26,.51),(-.20,.66),(-.14,.82),(0,1),(.14,.82),(.20,.66),(.26,.51),(.22,.34),(.14,.16)]

def overlaps_rectangle(poly,rect):
    """Clip leaf edges as well as vertices against an opening's clear surround."""
    if max(q[0] for q in poly)<rect[0] or min(q[0] for q in poly)>rect[2] or max(q[1] for q in poly)<rect[1] or min(q[1] for q in poly)>rect[3]:return False
    clipped=list(poly)
    for axis,bound,sign in ((0,rect[0],1),(0,rect[2],-1),(1,rect[1],1),(1,rect[3],-1)):
        result=[]
        for a,b in zip(clipped,clipped[1:]+clipped[:1]):
            da,db=sign*(a[axis]-bound),sign*(b[axis]-bound)
            if da>=0:result.append(a)
            if (da>=0)!=(db>=0):
                t=da/(da-db);result.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(2)))
        clipped=result
        if not clipped:return False
    return len(clipped)>=3


def make_layout(params,spec):
    plants=[]
    for index,plant in enumerate(spec['plants']):
        rng=random.Random(spec["seed"]+index);p=dict(plant);p.update(branches=[],leaves=[])
        u0,z0=p['root_u'],p['root_z'];height=p['height_m'];width=p['width_m']
        margin=spec['bounds']['opening_clearance_m']+.012  # include stem radii
        masks=[(o['u0']-margin,o['z0']-margin,o['u1']+margin,o['z1']+margin)
               for o in params.openings if o['face']==p['face'] and abs(o['at']-p['at'])<.1 and o['kind']!='band']
        p['masks']=masks
        def clear(q):
            u,z=q
            return (u0-width/2<=u<=u0+width/2 and z0-.05<=z<=z0+height and
                    not any(a<=u<=c and b<=z<=d for a,b,c,d in masks))
        def segment(a,b,r):
            # Check the entire segment, not just endpoints crossing an opening.
            if not all(clear((a[0]+(b[0]-a[0])*t/20,a[1]+(b[1]-a[1])*t/20)) for t in range(21)):return False
            p['branches'].append({'a':a,'b':b,'r':r});return True
        def leader(z):return (u0+.055*math.sin((z-z0)*3.2),z)
        def leaf(base,length,angle):
            shape=BOSTON if p['species']=='boston_ivy' else VIRGINIA
            si,co=math.sin(angle),math.cos(angle)
            poly=[(base[0]+length*(x*co+y*si),base[1]+length*(-x*si+y*co)) for x,y in shape]
            if not all(clear(q) for q in poly) or any(overlaps_rectangle(poly,m) for m in masks):return False
            centre=(base[0]+length*.46*si,base[1]+length*.46*co)
            p['leaves'].append({'base':base,'centre':centre,'polygon':poly,'length':length,
                                 'shade':rng.uniform(.78,1.15),'fold':rng.uniform(.006,.014)})
            return True
        def cluster(base,angle):
            petiole=(base[0]+math.sin(angle)*.045,base[1]+math.cos(angle)*.045)
            if not segment(base,petiole,.0014):return
            if p['species']=='boston_ivy':leaf(petiole,rng.uniform(.105,.17),angle)
            else:
                for delta,scale in [(-1.17,.78),(-.59,.95),(0,1),(.59,.95),(1.17,.78)]:
                    leaf(petiole,rng.uniform(.075,.125)*scale,angle+delta)
        segment((u0,z0-.025),(u0,z0),.009)
        for leader_index, (reach, rise) in enumerate(((.06,.97),(-.32,.80),(.30,.73))):
            steps=math.ceil(height*rise/.085);previous=(u0,z0);nodes=[previous]
            phase=rng.uniform(0,6)
            for step in range(1,steps+1):
                t=step/steps
                q=(u0+reach*width*t+.045*math.sin(t*10+phase)*t,
                   z0+(height*rise-.12)*t)
                if not segment(previous,q,(.006 if leader_index else .009)*(1-.55*t)):break
                nodes.append(q);previous=q
            next_branch=rng.randint(3,5)
            for j, origin in enumerate(nodes):
                if j!=next_branch:continue
                next_branch+=rng.randint(3,5)
                side=rng.choice((-1,1));t=j/max(1,steps)
                span=width*rng.uniform(.12,.24)*math.sin(math.pi*min(.92,t))
                n=max(2,math.ceil(span/.10));previous=origin
                rise_branch=rng.uniform(.15,.52)
                for k in range(1,n+1):
                    w=k/n;q=(origin[0]+side*span*w,origin[1]+rise_branch*w+.035*math.sin(w*5))
                    if not segment(previous,q,.0023*(1-.65*w)):break
                    previous=q
                    cluster(q,side*rng.uniform(.35,1.55))
                if rng.random()<.65:cluster(origin,-side*rng.uniform(.3,1.2))
        # Atlas bounds are shared exactly by Full and reduced geometry.
        p['bounds']=(u0-width/2,z0-.05,u0+width/2,z0+height+.03)
        plants.append(p)
    return plants


def draw_atlas(plants,path):
    from PIL import Image,ImageDraw
    tile=1024;im=Image.new('RGBA',(tile*4,tile*2),(54,87,30,0));draw=ImageDraw.Draw(im)
    for index,p in enumerate(plants):
        x0,y0,x1,y1=p['bounds'];col,row=index%4,index//4
        def px(q):return (col*tile+8+(q[0]-x0)/(x1-x0)*(tile-16),row*tile+tile-8-(q[1]-y0)/(y1-y0)*(tile-16))
        for branch in p['branches']:
            width=max(1,round(branch['r']*2/(x1-x0)*(tile-16)))
            draw.line([px(branch['a']),px(branch['b'])],fill=(94,76,49,255),width=width)
        for leaf in p['leaves']:
            shade=leaf['shade'];colour=tuple(round(c*shade) for c in (54,88,31))+(255,)
            # Small inward teeth retain the independently drawn leaf envelope.
            # No photograph is sampled, traced or embedded.
            outline=[];centre=leaf['centre'];poly=leaf['polygon']
            for a,b in zip(poly,poly[1:]+poly[:1]):
                outline.append(a)
                for t,inset in ((.32,0),(.48,.016),(.64,0)):
                    q=(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))
                    dx,dy=centre[0]-q[0],centre[1]-q[1];length=math.hypot(dx,dy) or 1
                    outline.append((q[0]+dx/length*leaf['length']*inset,q[1]+dy/length*leaf['length']*inset))
            draw.polygon([px(q) for q in outline],fill=colour)
            draw.line([px(leaf['base']),px(leaf['polygon'][6])],fill=(89,113,54,255),width=1)
            for edge in [2,4,8,10]:
                draw.line([px(leaf['centre']),px(leaf['polygon'][edge])],fill=(70,99,39,255),width=1)
    im.save(path,format="PNG")


from collections import defaultdict

def validate_spec(spec,params):
    plants=spec['plants']
    if not 1<=len(plants)<=8 or len({p['id'] for p in plants})!=len(plants):
        raise ValueError('Vine atlas needs one to eight uniquely named plants')
    if spec['scene_date']!='1904-07-01' or spec['bounds']['opening_clearance_m']<.20:
        raise ValueError('Glessner vines require the July1904 bounds and opening clearance')
    for p in plants:
        if p['species'] not in ('boston_ivy','virginia_creeper') or p['face'] not in ('east','west','north','south'):
            raise ValueError('Unsupported vine species or wall face')
        if not all(math.isfinite(p[k]) for k in ('at','root_u','root_z','width_m','height_m')):
            raise ValueError('Non-finite planting dimensions')
        if not (0<p['width_m']<=6 and 0<p['height_m']<=6):
            raise ValueError('Vine growth exceeds its restrained wall envelope')
        normal_limit=params.width_m if p['face'] in ('east','west') else params.depth_m
        along_limit=params.depth_m if p['face'] in ('east','west') else params.width_m
        if not (-.35<=p['at']<=normal_limit+.01 and 0<=p['root_u']<=along_limit):
            raise ValueError('Vine root lies outside the house envelope')

def frame(p):
    axis=0 if p['face'] in ('east','west') else 1
    return axis,1-axis,1 if p['face'] in ('east','north') else -1


class Surface:
    """Index actual outward masonry triangles in wall-local u/z coordinates."""
    def __init__(self,b,p):
        self.axis,self.along,self.sign=frame(p);self.at=p['at'];self.cells=defaultdict(list);self.fallback=0
        lo,z0,hi,z1=p['bounds'];axis,along,sign=self.axis,self.along,self.sign
        for face,material in zip(b.faces,b.mat_index):
            if material not in (0,1,2,9,12,13,14,15,16,17,18,24):continue
            points=[b.verts[i] for i in face]
            if any(not -.06<sign*(q[axis]-self.at)<.22 for q in points):continue
            a,c,e=points[0],points[1],points[2]
            nx=(c[1]-a[1])*(e[2]-a[2])-(c[2]-a[2])*(e[1]-a[1])
            ny=(c[2]-a[2])*(e[0]-a[0])-(c[0]-a[0])*(e[2]-a[2])
            if (nx if axis==0 else ny)*sign<=1e-12:continue
            for j in range(1,len(points)-1):
                tri=[(q[along],q[2],sign*(q[axis]-self.at)) for q in (points[0],points[j],points[j+1])]
                u0,u1=min(q[0] for q in tri),max(q[0] for q in tri)
                v0,v1=min(q[1] for q in tri),max(q[1] for q in tri)
                if u1<lo or u0>hi or v1<z0 or v0>z1:continue
                for x in range(math.floor(max(lo,u0)/.2),math.floor(min(hi,u1)/.2)+1):
                    for y in range(math.floor(max(z0,v0)/.2),math.floor(min(z1,v1)/.2)+1):self.cells[x,y].append(tri)
    def depth(self,q):
        x,y=q;hits=[]
        for a,b,c in self.cells.get((math.floor(x/.2),math.floor(y/.2)),[]):
            den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-12:continue
            u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
            v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
            if min(u,v,1-u-v)>-1e-7:hits.append(u*a[2]+v*b[2]+(1-u-v)*c[2])
        return max(hits) if hits else self.fallback
    def point(self,q,d):
        p=[0.,0.,q[1]];p[self.axis]=self.at+self.sign*d;p[self.along]=q[0];return tuple(p)

    def peak(self,coords):
        """Height over an entire leaf/panel, including interior stone crowns."""
        lo,hi=min(q[0] for q in coords),max(q[0] for q in coords)
        z0,z1=min(q[1] for q in coords),max(q[1] for q in coords)
        heights=[self.depth(q) for q in coords]
        for x in range(math.floor(lo/.2),math.floor(hi/.2)+1):
            for y in range(math.floor(z0/.2),math.floor(z1/.2)+1):
                for tri in self.cells.get((x,y),[]):
                    if max(q[0] for q in tri)>=lo and min(q[0] for q in tri)<=hi and max(q[1] for q in tri)>=z0 and min(q[1] for q in tri)<=z1:
                        heights.append(max(q[2] for q in tri))
        return max(heights)


def add_vines(b,params,reduced=False):
    spec=params.detail.get('vines')
    if not spec:return {'plants':[], 'added_faces':0, 'reduced':reduced}
    validate_spec(spec,params)
    plants=make_layout(params,spec);before=len(b.faces);stats=[];emitted_tubes=set()
    def tube(a,c,r,normal):
        key=(tuple(sorted((tuple(round(x,9) for x in a),tuple(round(x,9) for x in c)))),round(r,9))
        if key in emitted_tubes:return
        emitted_tubes.add(key)
        v=[c[k]-a[k] for k in range(3)];length=math.sqrt(sum(x*x for x in v))
        if length<1e-7:return
        v=[x/length for x in v]
        side=(v[1]*normal[2]-v[2]*normal[1],v[2]*normal[0]-v[0]*normal[2],v[0]*normal[1]-v[1]*normal[0])
        size=math.sqrt(sum(x*x for x in side))
        if size<1e-7:
            normal=(0,0,1);side=(v[1],-v[0],0);size=math.sqrt(sum(x*x for x in side))
        side=[x/size for x in side]
        up=(v[1]*side[2]-v[2]*side[1],v[2]*side[0]-v[0]*side[2],v[0]*side[1]-v[1]*side[0])
        rings=[[tuple(q[k]+r*(math.cos(i*math.pi/2)*side[k]+math.sin(i*math.pi/2)*up[k]) for k in range(3)) for i in range(4)] for q in (a,c)]
        for i in range(4):b.raw([rings[0][i],rings[0][(i+1)%4],rings[1][(i+1)%4],rings[1][i]],1.,6)
    for index,p in enumerate(plants):
        surface=Surface(b,p);axis,along,sign=frame(p);normal=tuple(sign if k==axis else 0 for k in range(3))
        lo,z0,hi,z1=p['bounds'];col,row=index%4,index//4
        def uv(q):return ((col+(8+(q[0]-lo)/(hi-lo)*1008)/1024)/4,1-(row+(1016-(q[1]-z0)/(z1-z0)*1008)/1024)/2)
        def raw(points,coords,normals=None):
            # UV overrides use the builder's existing indexed surface-UV path.
            a,c,e=points[:3]
            cross=((c[1]-a[1])*(e[2]-a[2])-(c[2]-a[2])*(e[1]-a[1]),(c[2]-a[2])*(e[0]-a[0])-(c[0]-a[0])*(e[2]-a[2]),(c[0]-a[0])*(e[1]-a[1])-(c[1]-a[1])*(e[0]-a[0]))
            if sum(cross[k]*normal[k] for k in range(3))<0:
                points=list(reversed(points));coords=list(reversed(coords))
                if normals is not None:normals=list(reversed(normals))
            indices=b.raw(points,1.,29)
            for vertex,coord in zip(indices,coords):b.roof_uvs[vertex]=uv(coord)
            if normals is not None:
                # The existing explicit corner-normal path preserves UV seams.
                # A curved leaf is one surface, not twelve hard triangular facets.
                for vertex,n in zip(indices,normals):b.rock_normals[vertex]=n
        if reduced:
            # Shared grid vertices keep adjacent atlas panels continuous.
            cell_depth={}
            for ix in range(2):
                for iz in range(2):
                    cell_depth[ix,iz]=surface.peak([(lo+(hi-lo)*u/2,z0+(z1-z0)*v/2)
                        for u,v in ((ix,iz),(ix+1,iz+1))])+.032
            node_depth={(x,y):max(cell_depth[i,j] for i in range(2) for j in range(2)
                        if i<=x<=i+1 and j<=y<=j+1) for x in range(3) for y in range(3)}
            for ix in range(2):
                for iz in range(2):
                    indices=[(ix,iz),(ix+1,iz),(ix+1,iz+1),(ix,iz+1)]
                    coords=[(lo+(hi-lo)*u/2,z0+(z1-z0)*v/2) for u,v in indices]
                    raw([surface.point(q,node_depth[key]) for q,key in zip(coords,indices)],coords)
        else:
            for branch in p['branches']:
                a,c=branch['a'],branch['b'];r=branch['r']
                tube(surface.point(a,surface.depth(a)+r),surface.point(c,surface.depth(c)+r),r,normal)
            # All leaflets of a compound leaf share one petiole junction. Different
            # stone supports must not create nested tubes from the same base:
            # near-identical ends coincided on K01's 1 mm measurement grid.
            junction_depth={}
            for leaf in p['leaves']:
                base=leaf['base']
                junction_depth[base]=max(junction_depth.get(base,0),surface.peak(leaf['polygon'])+.022)
            for leaf in p['leaves']:
                coords=leaf['polygon'];depth=junction_depth[leaf['base']]
                centre=surface.point(leaf['centre'],depth+leaf['fold']);points=[surface.point(q,depth) for q in coords]
                face_normals=[]
                for a,c in zip(points,points[1:]+points[:1]):
                    u=[a[k]-centre[k] for k in range(3)];v=[c[k]-centre[k] for k in range(3)]
                    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                    length=math.sqrt(sum(x*x for x in n))
                    direction=1 if sum(n[k]*normal[k] for k in range(3))>=0 else -1
                    face_normals.append(tuple(direction*x/length for x in n))
                edge_normals=[]
                for j in range(len(points)):
                    n=tuple(face_normals[j-1][k]+face_normals[j][k] for k in range(3))
                    length=math.sqrt(sum(x*x for x in n));edge_normals.append(tuple(x/length for x in n))
                for j in range(len(points)):
                    raw([centre,points[j],points[(j+1)%len(points)]],
                        [leaf['centre'],coords[j],coords[(j+1)%len(coords)]],
                        [normal,edge_normals[j],edge_normals[(j+1)%len(points)]])
                base=leaf['base'];tube(surface.point(base,surface.depth(base)+.002),surface.point(base,depth),.0012,normal)
        stats.append({'id':p['id'],'leaves':len(p['leaves']),'branches':len(p['branches']),'surface_cells':len(surface.cells)})
    return {'plants':stats,'added_faces':len(b.faces)-before,'reduced':reduced}
