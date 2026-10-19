# SPDX-License-Identifier: GPL-3.0-or-later
"""Original CC0 hm08 short04 fitting arithmetic; no MakeHuman program/shader imports."""
import hashlib,json,math,pathlib

def fit(body,config,root):
    relative=pathlib.PurePosixPath(config['directory'])
    if relative.is_absolute() or '..' in relative.parts:raise ValueError('unsafe hair component directory')
    for key in ['roughness','alpha_cutoff']:
        value=config[key]
        if not isinstance(value,(float,int)) or isinstance(value,bool) or not math.isfinite(value) or not 0<=value<=1:
            raise ValueError('hair material setting must be finite within0..1: '+key)
    folder=pathlib.Path(root)/config['directory']
    manifest=(folder/'SOURCE.json').read_bytes()
    if hashlib.sha256(manifest).hexdigest()!=config['source_manifest_sha256']:raise ValueError('hair source manifest hash mismatch')
    source=json.loads(manifest)
    if source['license']!='CC0-1.0':raise ValueError('hair source must be CC0')
    selected=pathlib.PurePosixPath(config['texture'])
    members={row['path']:row for row in source['files']}
    if selected.is_absolute() or '..' in selected.parts or selected.as_posix()!=config['texture'] or config['texture'] not in members:
        raise ValueError('selected hair texture must be a verified safe manifest member')
    if config['texture']!='short04_diffuse_periodic_pad_draft.png':
        raise ValueError('selected hair texture must match the assessed UV derivative')
    for row in source['files']:
        name=pathlib.PurePosixPath(row['path'])
        if name.is_absolute()or'..'in name.parts:raise ValueError('unsafe hair source path')
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('hair source hash mismatch: '+str(name))
    for name in ['short04.obj','short04.mhclo','short04.mhmat']:
        if 'explicitly released as CC0'not in (folder/name).read_text():raise ValueError('missing asset-specific CC0 header')
    if config['uv_transform']!={'source_height':2048,'top_rows':8,'bottom_rows':1}:raise ValueError('unknown unverified hair UV transform')
    rows=[];scales={};uv=[];faces=[];reading=False
    for line in (folder/'short04.mhclo').read_text().splitlines():
        f=line.split()
        if not f or f[0].startswith('#'):continue
        if f[0]=='basemesh'and f[1]!='hm08':raise ValueError('hair basemesh mismatch')
        if f[0]in ['x_scale','y_scale','z_scale']:scales[f[0][0]]=(int(f[1]),int(f[2]),float(f[3]))
        elif f[0]=='verts':reading=True
        elif f[0]=='material':
            if f[1]!='short04.mhmat':raise ValueError('unexpected hair material')
        elif reading:
            if len(f)!=9:raise ValueError('unsupported short04 proxy row')
            rows.append(([int(x)for x in f[:3]],[float(x)for x in f[3:6]],[float(x)for x in f[6:9]]))
    for line in (folder/'short04.obj').read_text().splitlines():
        f=line.split()
        if not f:continue
        if f[0]=='vt':uv.append([float(x)for x in f[1:3]])
        elif f[0]=='f':
            corners=[tuple(int(x)-1 for x in s.split('/')[:2])for s in f[1:]]
            for j in range(1,len(corners)-1):faces.append([corners[0],corners[j],corners[j+1]])
    if len(rows)!=865 or len(faces)!=1050:raise ValueError('unexpected source hair topology')
    points={};skin={}
    for m in body['meshes']:
        for i,p,w in zip(m['source_vertex_indices'],m['positions_m'],m['weights']):
            if i in points and (math.dist(points[i],p)>1e-10 or skin[i]!=w):raise ValueError('body source seam disagreement')
            points[i]=p;skin[i]=w
    required={i for ids,bary,offset in rows for i in ids}|{i for a,b,d in scales.values()for i in [a,b]}
    if required-set(points):raise ValueError('hair references missing body source vertices')
    factor=[abs(points[scales[a][0]][k]-points[scales[a][1]][k])/scales[a][2]for k,a in enumerate('xyz')]
    coords=[];weights=[];negative_rows=0;max_negative_mass=0;max_pruned=0
    for ids,bary,offset in rows:
        total=math.fsum(bary)
        if abs(total-1)>2e-5:raise ValueError('invalid geometric barycentric sum')
        bary=[v/total for v in bary]
        coords.append([math.fsum(w*points[i][k]for w,i in zip(bary,ids))+offset[k]*factor[k]for k in range(3)])
        accum={}
        for w,i in zip(bary,ids):
            for joint,value in skin[i].items():accum[joint]=accum.get(joint,0)+w*value
        negative=math.fsum(-w for w in accum.values()if w<0);negative_rows+=negative>1e-9;max_negative_mass=max(max_negative_mass,negative)
        ordered=sorted(((n,w)for n,w in accum.items()if w>0),key=lambda x:(-x[1],x[0]));max_pruned=max(max_pruned,math.fsum(w for n,w in ordered[4:]));keep=ordered[:4];s=math.fsum(w for n,w in keep)
        if s<=0:raise ValueError('unweighted hair vertex')
        weights.append({n:w/s for n,w in keep})
    split={};p=[];u=[];w=[];t=[]
    for face in faces:
        tri=[]
        for vi,ti in face:
            if (vi,ti)not in split:
                split[vi,ti]=len(p);p.append(coords[vi]);u.append([uv[ti][0],(2048*uv[ti][1]+1)/2057]);w.append(weights[vi])
            tri.append(split[vi,ti])
        t.append(tri)
    if not all(0<=v<=1 for pair in u for v in pair):raise ValueError('hair UV outside human contract')
    report={'source':source,'missing_references':0,'triangles_each_lod':len(t),'vertices_each_lod':len(p),'negative_interpolated_weight_rows':negative_rows,'max_clamped_negative_weight_mass':max_negative_mass,'max_pruned_weight_mass':max_pruned,'UV_transform':config['uv_transform'],'limitations':'Reconstructed shared short hair; period/individual appearance, scalp/ear/collar/deformation, alpha/PBR/export and mip/aniso acceptance open. All LODs preserve source topology pending measured optimization.'}
    return {'positions_m':p,'triangles':t,'uvs':u,'weights':w},folder/config['texture'],report
