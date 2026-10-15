"""T-2226: metric joints on plain brick faces and grain along gate members.

These surface reconstructions use the existing original fabric maps. They add
no geometry, directional shadows, historical dirt claims or shared-kit retint.
"""
from __future__ import annotations

FLAT_BRICK=30


def validate(spec):
    f=spec['flat_brick']
    if spec['scene_date']!='1904-07-01' or spec['gate_grain']!='member_axis':
        raise ValueError('Unsupported Glessner surface study')
    if not (0<f['joint_m']<min(f['width_m'],f['course_m']) and 0<f['joint_depth_m']<f['joint_m']):
        raise ValueError('Invalid flat-brick joint dimensions')
    if not (0<f['edge_transition_m']<f['joint_m']/2 and f['columns']>0 and f['rows']>0 and f['rows']%2==0):
        raise ValueError('Brick repeat must close its half-bond courses')
    if f['pixels']!=1024:raise ValueError('Surface study uses the declared 1024-pixel budget')


def flat_brick(b):
    from archetypes.masonry_house_v4_materials import BRICK
    return FLAT_BRICK if b.params.detail.get('surface_finish') else BRICK


def grain_members(b,first,axis,origin):
    """Assign physical metres to each newly emitted wood face's SurfaceUV.

    Oak's long grain is V. Project the member axis onto each side face rather
    than normalising every member to one repeated image. Cut ends keep generic
    oak on a full-rank basis; they do not pretend to be measured end-grain rings.
    """
    if not b.params.detail.get('surface_finish'):return
    from archetypes import masonry_house_v4_detail as d
    axis=d.norm(axis);members=[]
    for face,mat in zip(b.faces[first:],b.mat_index[first:]):
        if mat!=d.WOOD:raise ValueError('Member grain may only map timber')
        pts=[b.verts[i] for i in face];normal=d.norm(d.legacy._normal(pts))
        v=d.sub(axis,tuple(d.dot(axis,normal)*x for x in normal))
        end=d.dot(v,v)<1e-12
        if end:
            guide=min(((1,0,0),(0,1,0),(0,0,1)),key=lambda q:abs(d.dot(q,normal)))
            v=d.sub(guide,tuple(d.dot(guide,normal)*x for x in normal))
        v=d.norm(v);u=d.norm(d.cross(v,normal))
        if min(d.dot(u,u),d.dot(v,v))<.999:raise ValueError('Degenerate wood UV basis')
        for index in face:
            relative=d.sub(b.verts[index],origin)
            b.roof_uvs[index]=(d.dot(relative,u),d.dot(relative,v))
        members.append({'indices':face,'axis':axis,'u':u,'v':v,'end':end})
    if not hasattr(b,'wood_grain_members'):b.wood_grain_members=[]
    b.wood_grain_members.extend(members)


def maps(textures,spec):
    """Original periodic half-bond study; sRGB colour and linear data channels."""
    import numpy as np
    from PIL import Image
    validate(spec);f=spec['flat_brick'];size=f['pixels']
    tile=(f['width_m']*f['columns'],f['course_m']*f['rows'])
    Y,X=np.indices((size,size),dtype=np.float64)
    x=(X+.5)*tile[0]/size;z=(size-Y-.5)*tile[1]/size
    row=np.floor(z/f['course_m']).astype(int);u=x/f['width_m']+.5*(row%2)
    rx=(u%1)*f['width_m'];rz=z%f['course_m']
    distance=np.minimum(np.minimum(rx,f['width_m']-rx),np.minimum(rz,f['course_m']-rz))
    t=np.clip((distance-f['joint_m']/2)/f['edge_transition_m'],0,1);face=t*t*(3-2*t)
    def rgb(name):
        return np.asarray(Image.open(textures/name).convert('RGB').resize((size,size),Image.Resampling.LANCZOS),dtype=float)/255
    def linear(a):return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
    def srgb(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
    def pixels(a):return np.uint8(np.clip(a,0,1)*255+.5)
    # Same existing kiln palette/distribution as the individually modeled bricks.
    rng=np.random.default_rng(f['seed']);pick=rng.random((f['rows'],f['columns']))
    tones=np.array([[.94,.94,.94],[.86,.76,.74],[1,.99,.97],[.66,.58,.56]])
    indices=np.where(pick<.60,0,np.where(pick<.80,1,np.where(pick<.94,2,3)))
    col=np.floor(u).astype(int)%f['columns']
    clay=linear(rgb('court_brick_basecolor.jpg'))*tones[indices[row%f['rows'],col]]
    mortar=linear(rgb('mortar_basecolor.jpg'))
    albedo=srgb(clay*face[...,None]+mortar*(1-face[...,None]))
    relief=face*f['joint_depth_m']
    sx=(np.roll(relief,-1,1)-np.roll(relief,1,1))/(2*tile[0]/size)
    sy=(np.roll(relief,1,0)-np.roll(relief,-1,0))/(2*tile[1]/size)
    grain=rgb('brick_normal.png')*2-1
    normal=np.stack((-sx,-sy,np.ones_like(sx)),axis=-1)
    normal[...,:2]+=grain[...,:2]/np.maximum(.1,grain[...,2,None])*face[...,None]
    normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    rough=rgb('brick_roughness.png')[...,0]*face+rgb('mortar_roughness.png')[...,0]*(1-face)
    return {'basecolor':Image.fromarray(pixels(albedo)),
            'normal':Image.fromarray(pixels(normal*.5+.5)),
            'roughness':Image.fromarray(pixels(rough))}
