#!/usr/bin/env python3
"""Build the engine-neutral Chicago 1835 PBR material library.

Every tile is deterministic and seamless.  The script writes aligned base-color,
height, normal, roughness, AO, metallic and Unreal ORM maps plus metadata.
"""

from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage


SIZE = 1024


MATERIALS = [
    dict(id="clapboard_weathered_oak", group="walls", span_m=4.48, confidence="attested/inferred", mean_roughness=.86, kind="clapboard", colors=((126,112,91),(96,91,80)), note="32 exposed clapboard courses at 0.14 m; unpainted weathered timber."),
    dict(id="clapboard_whitewash", group="walls", span_m=4.48, confidence="attested where recorded", mean_roughness=.90, kind="clapboard", colors=((211,207,188),(165,160,143)), note="Chalky lime wash over visible clapboard substrate; not a default finish."),
    dict(id="clapboard_white_lead_paint", group="walls", span_m=4.48, confidence="attested for Sauganash", mean_roughness=.60, kind="clapboard", colors=((226,224,215),(191,188,176)), note="Smooth but aged white lead/oil paint over clapboard."),
    dict(id="clapboard_red_oxide", group="walls", span_m=4.48, confidence="period-inferred; building-level reconstructed", mean_roughness=.85, kind="clapboard", colors=((124,67,53),(85,52,45)), note="Iron-oxide finish over clapboard; do not treat as attested on a named building."),
    dict(id="board_and_batten_weathered", group="walls", span_m=4.272, confidence="reconstructed", mean_roughness=.88, kind="batten", colors=((117,106,88),(82,78,68)), note="12 battens at the committed 0.356 m set-out."),
    dict(id="vertical_sawn_board", group="walls", span_m=4.58, confidence="reconstructed", mean_roughness=.90, kind="vertical", colors=((135,116,88),(89,81,68)), note="20 boards at the committed 0.229 m set-out."),
    dict(id="hewn_log_oak_chinked", group="walls", span_m=4.08, confidence="attested/inferred", mean_roughness=.92, kind="log", colors=((105,82,58),(190,181,154)), note="12 squared log courses at 0.34 m with clay-and-lime chinking."),
    dict(id="sawn_board_weathered", group="timber", span_m=4.00, confidence="inferred", mean_roughness=.94, kind="planks", colors=((118,103,80),(77,72,61)), note="Plain gappy sawn stock; grain detail only where board widths are geometry."),
    dict(id="fresh_sawn_framing", group="timber", span_m=4.00, confidence="inferred", mean_roughness=.84, kind="planks", colors=((177,148,100),(129,105,73)), note="Pale fresh-sawn exposed framing."),
    dict(id="heavy_timber_weathered", group="timber", span_m=4.00, confidence="inferred", mean_roughness=.90, kind="planks", colors=((92,75,55),(57,52,44)), note="Moisture-darkened heavy posts, docks and bridge members."),
    dict(id="wood_shingles_weathered", group="roofs", span_m=4.48, confidence="attested once; otherwise inferred", mean_roughness=.90, kind="shingle", colors=((92,80,67),(57,56,53)), note="Riven timber shingles; 0.14 m exposure is a declared reconstruction outside the attested North Side school."),
    dict(id="roof_boards_weathered", group="roofs", span_m=4.00, confidence="inferred", mean_roughness=.94, kind="roofboards", colors=((100,85,66),(61,58,51)), note="Plain board covering appropriate to rough outbuildings."),
    dict(id="chicago_clay_brick_lime_mortar", group="masonry", span_m=4.20, confidence="fabric attested; module reconstructed", mean_roughness=.90, kind="brick", colors=((132,71,54),(190,178,151)), note="Locally fired red-brown brick with pale lime mortar; brick dimensions are reconstructed, not Chicago-attested."),
    dict(id="limestone_rubble_lime_mortar", group="masonry", span_m=4.00, confidence="reconstructed", mean_roughness=.93, kind="stone", colors=((143,139,126),(190,183,159)), note="Irregular pale Great Lakes rubble masonry; use only where stone fabric is selected."),
    dict(id="cat_and_clay_chimney", group="masonry", span_m=2.04, confidence="reconstructed", mean_roughness=.95, kind="clay", colors=((139,124,96),(194,181,151)), note="Daubed stick-and-clay chimney fabric for log cabins; bounded by chinking and weathered roof tones."),
    dict(id="packed_black_loam", group="ground", span_m=6.00, confidence="attested geology; reconstructed surface", mean_roughness=.96, kind="earth", colors=((73,67,51),(45,44,38)), note="Compacted dark loam for yards and trodden dry ground."),
    dict(id="muddy_rutted_street", group="ground", span_m=8.00, confidence="attested condition; reconstructed wear", mean_roughness=.78, kind="mud", colors=((82,70,58),(44,43,39)), note="Unpaved wagon-and-hoof-worn street with damp ruts; no modern tire marks."),
    dict(id="wet_prairie_muck", group="ground", span_m=6.00, confidence="attested/inferred", mean_roughness=.86, kind="muck", colors=((67,66,46),(34,42,35)), note="Peaty/mucky low wet prairie substrate; vegetation remains a separate layer."),
    dict(id="lake_michigan_dune_sand", group="ground", span_m=6.00, confidence="attested setting; reconstructed grain", mean_roughness=.93, kind="sand", colors=((177,163,129),(129,122,101)), note="Muted gray-tan freshwater beach and low dune sand."),
    dict(id="river_stone_gravel_fill", group="ground", span_m=4.00, confidence="inferred", mean_roughness=.98, kind="gravel", colors=((111,108,98),(63,65,62)), note="Mixed river stone and gravel crib/bridge fill."),
    dict(id="plank_walk_weathered", group="waterfront", span_m=4.00, confidence="attested form; inferred finish", mean_roughness=.94, kind="walk", colors=((118,101,76),(72,67,58)), note="Raised rough-sawn boardwalk/plank crossing above mud."),
    dict(id="dock_timber_tar_darkened", group="waterfront", span_m=4.00, confidence="inferred", mean_roughness=.82, kind="tarwood", colors=((72,61,48),(34,34,31)), note="Heavy waterfront timber darkened by water, grime and limited tar/pitch maintenance."),
    dict(id="wrought_iron_forged", group="props", span_m=1.00, confidence="period-inferred", mean_roughness=.62, kind="iron", colors=((48,47,44),(18,20,20)), note="Hand-forged iron hardware with restrained oxidation; metallic workflow."),
    dict(id="signboard_weathered", group="props", span_m=2.00, confidence="reconstructed", mean_roughness=.85, kind="planks", colors=((155,137,105),(91,82,68)), note="Unlettered weathered sign board. Lettering belongs in the signage atlas."),
    dict(id="blue_painted_shutter", group="props", span_m=2.00, confidence="attested for Sauganash", mean_roughness=.75, kind="planks", colors=((52,89,145),(30,54,92)), note="Aged bright-blue oil-painted timber shutter."),
]


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def fbm(size, seed, octaves=(96, 40, 16, 6), weights=(.48, .27, .16, .09)):
    rng = np.random.default_rng(seed)
    out = np.zeros((size, size), np.float32)
    for sigma, w in zip(octaves, weights):
        a = rng.random((size, size), dtype=np.float32)
        a = ndimage.gaussian_filter(a, sigma=sigma, mode="wrap")
        a = (a - a.min()) / max(float(a.max()-a.min()), 1e-6)
        out += a*w
    return clamp01((out-out.min())/max(float(out.max()-out.min()),1e-6))


def grain(size, seed, vertical=False):
    n = fbm(size, seed, (72, 18, 5), (.48,.32,.20))
    axis = np.linspace(0, 2*math.pi*38, size, endpoint=False)
    bands = np.sin(axis + ndimage.gaussian_filter(n, 22, mode="wrap")*14)
    g = .55*n + .45*(bands*.5+.5)
    return g.T if vertical else g


def palette(a, c0, c1):
    a = clamp01(a)[...,None]
    return np.array(c0,dtype=np.float32)*(1-a)+np.array(c1,dtype=np.float32)*a


def board_surface(size, seed, vertical=True, boards=16, battens=False):
    yy,xx=np.indices((size,size))
    coord=xx if vertical else yy
    width=size/boards
    frac=(coord%width)/width
    seam=np.exp(-((np.minimum(frac,1-frac))/0.035)**2)
    bevel=np.sin(frac*math.pi)
    h=.55+.10*bevel-.20*seam+.11*(grain(size,seed,vertical=not vertical)-.5)
    if battens:
        bat=np.exp(-((np.minimum(frac,1-frac))/0.10)**4)
        h += .28*bat
    return clamp01(h), seam


def clapboard(size, seed):
    yy,xx=np.indices((size,size))
    courses=32
    ch=size/courses
    frac=(yy%ch)/ch
    overlap=np.exp(-((frac)/.09)**2)
    h=.42+.34*frac-.27*overlap+.08*(grain(size,seed)-.5)
    # Staggered butt joints, kept subtle because much course rhythm is geometry.
    joints=np.zeros((size,size),np.float32)
    for row in range(courses):
        off=(row%2)*size//4
        for j in range(4):
            x=(off+j*size//2)%size
            y0=int(row*ch); y1=int((row+1)*ch)
            joints[y0:y1,max(0,x-1):min(size,x+2)]=1
    h-=ndimage.gaussian_filter(joints,1.1,mode="wrap")*.10
    return clamp01(h), clamp01(overlap+joints*.4)


def logwall(size, seed):
    yy,xx=np.indices((size,size)); courses=12; ch=size/courses
    frac=(yy%ch)/ch
    chink=(frac<.16)|(frac>.92)
    rounded=np.sin(np.clip((frac-.12)/.80,0,1)*math.pi)
    h=.35+.38*rounded+.08*(grain(size,seed)-.5)
    h=np.where(chink,.46+.04*fbm(size,seed+4,(20,7),(.65,.35)),h)
    return clamp01(h),chink.astype(np.float32)


def shingles(size, seed):
    yy,xx=np.indices((size,size)); rows=32; rh=size/rows; cols=16; cw=size/cols
    r=(yy//rh).astype(int); fx=((xx+(r%2)*cw/2)%cw)/cw; fy=(yy%rh)/rh
    seamx=np.exp(-((np.minimum(fx,1-fx))/.04)**2)
    seamy=np.exp(-(fy/.07)**2)
    h=.36+.30*fy-.23*seamy-.14*seamx+.10*(grain(size,seed)-.5)
    return clamp01(h),clamp01(seamx+seamy)


def brick(size, seed):
    yy,xx=np.indices((size,size)); rows=48; rh=size/rows; cols=20; cw=size/cols
    r=(yy//rh).astype(int); fx=((xx+(r%2)*cw/2)%cw)/cw; fy=(yy%rh)/rh
    mortar=(np.minimum(fx,1-fx)<.055)|(np.minimum(fy,1-fy)<.14)
    n=fbm(size,seed,(34,9,3),(.55,.3,.15))
    h=.57+.12*(n-.5); h[mortar]=.30+.04*n[mortar]
    return clamp01(h),mortar.astype(np.float32)


def stone(size, seed):
    rng=np.random.default_rng(seed); seeds=np.zeros((size,size),bool)
    for _ in range(150):
        seeds[rng.integers(0,size),rng.integers(0,size)]=1
    # Solve the Voronoi field on a 3x3 tiling and crop the centre.  A plain EDT
    # does not know that opposite image edges are neighbours and leaves a seam.
    tiled=np.tile(seeds,(3,3))
    _,inds=ndimage.distance_transform_edt(~tiled,return_indices=True)
    labels=(inds[0]%size)*size+(inds[1]%size)
    labels=labels[size:2*size,size:2*size]
    edge=(labels!=np.roll(labels,1,0))|(labels!=np.roll(labels,1,1))
    mortar=ndimage.binary_dilation(edge,iterations=3)
    n=fbm(size,seed+1,(42,12,4),(.55,.3,.15))
    h=.56+.20*(n-.5); h[mortar]=.27+.05*n[mortar]
    return clamp01(h),mortar.astype(np.float32)


def ground(size, seed, mode):
    n=fbm(size,seed,(110,36,11,3),(.42,.3,.19,.09)); micro=fbm(size,seed+1,(8,2),(.7,.3))
    h=.36+.38*n+.10*(micro-.5); mask=np.zeros_like(h)
    yy,xx=np.indices((size,size))
    if mode=="mud":
        for x in (int(size*.30),int(size*.66)):
            wob=26*np.sin(yy/78)+14*np.sin(yy/31)
            d=np.minimum(abs(xx-(x+wob)),size-abs(xx-(x+wob)))
            rut=np.exp(-(d/18)**2); h-=.32*rut; mask=np.maximum(mask,rut)
        rng=np.random.default_rng(seed+9)
        for _ in range(22):
            cx,cy=rng.integers(0,size,2); rx=rng.integers(8,19); ry=rng.integers(13,27)
            dx=np.minimum(abs(xx-cx),size-abs(xx-cx)); dy=np.minimum(abs(yy-cy),size-abs(yy-cy))
            hoof=np.exp(-((dx/rx)**4+(dy/ry)**4)); h-=.14*hoof; mask=np.maximum(mask,hoof)
    elif mode=="muck":
        mask=clamp01((fbm(size,seed+8,(70,20),(.7,.3))-.52)*4)
        h-=mask*.12
    elif mode=="sand":
        ripple=(np.sin(2*math.pi*(12*xx/size + .35*np.sin(2*math.pi*3*yy/size)))*.5+.5)
        h=.46+.24*n+.08*ripple; mask=ripple
    return clamp01(h),clamp01(mask)


def gravel(size, seed):
    rng=np.random.default_rng(seed); yy,xx=np.indices((size,size)); h=.36+.15*fbm(size,seed,(34,9),(.7,.3)); mask=np.zeros_like(h)
    for _ in range(260):
        cx,cy=rng.integers(0,size,2); r=float(rng.integers(3,14));
        dx=np.minimum(abs(xx-cx),size-abs(xx-cx)); dy=np.minimum(abs(yy-cy),size-abs(yy-cy))
        rock=clamp01(1-np.sqrt(dx*dx+dy*dy)/r); h=np.maximum(h,.48+.42*rock); mask=np.maximum(mask,rock)
    return clamp01(h),mask


def surface(spec, seed):
    k=spec["kind"]
    if k=="clapboard": h,m=clapboard(SIZE,seed)
    elif k=="batten": h,m=board_surface(SIZE,seed,True,12,True)
    elif k=="vertical": h,m=board_surface(SIZE,seed,True,20)
    elif k=="log": h,m=logwall(SIZE,seed)
    elif k in ("planks","roofboards","walk","tarwood"): h,m=board_surface(SIZE,seed,k not in ("roofboards","walk"),14 if k!="walk" else 11)
    elif k=="shingle": h,m=shingles(SIZE,seed)
    elif k=="brick": h,m=brick(SIZE,seed)
    elif k=="stone": h,m=stone(SIZE,seed)
    elif k=="clay": h,m=ground(SIZE,seed,"earth")
    elif k in ("earth","mud","muck","sand"): h,m=ground(SIZE,seed,k)
    elif k=="gravel": h,m=gravel(SIZE,seed)
    elif k=="iron": h,m=ground(SIZE,seed,"earth"); h=.43+.15*(h-.5); m=clamp01((.52-fbm(SIZE,seed+8,(28,6),(.7,.3)))*3)
    else: raise ValueError(k)

    n=fbm(SIZE,seed+40,(80,24,7,2),(.45,.30,.17,.08))
    if k in ("clapboard","batten","vertical","planks","roofboards","walk","tarwood","shingle","log"):
        g=grain(SIZE,seed+12,vertical=k in ("clapboard","shingle","log","roofboards","walk"))
        color=palette(.25*n+.75*g,*spec["colors"])
    else:
        color=palette(.25+.65*n,*spec["colors"])

    if k=="log":
        chink=m>.5; color[chink]=palette(n,*((185,176,150),(211,201,172)))[chink]
    elif k in ("brick","stone"):
        mort=m>.5; mortar=palette(n,(171,163,140),(208,199,172)); color[mort]=mortar[mort]
    elif k=="clay":
        color=palette(.35+.5*n,*spec["colors"])
    elif k=="mud":
        damp=clamp01(m*.72+(fbm(SIZE,seed+16,(90,25),(.7,.3))-.62)*2)
        color*=1-.20*damp[...,None]
    elif k=="muck":
        color*=1-.16*m[...,None]
    elif k=="sand":
        color*=.93+.09*m[...,None]
    elif k=="gravel":
        color=palette(.2+.65*n,(99,99,94),(151,145,130)); color*=.86+.18*m[...,None]
    elif k=="tarwood":
        color*=.72+.20*n[...,None]
    elif k=="iron":
        rust=np.array([89,55,38],np.float32); color=color*(1-m[...,None]*.42)+rust*m[...,None]*.42

    rough=clamp01(spec["mean_roughness"] + (n-.5)*.16)
    if k in ("mud","muck","tarwood"): rough=clamp01(rough-m*.30)
    if k=="iron": rough=clamp01(rough+m*.18)
    metallic=np.ones_like(h) if k=="iron" else np.zeros_like(h)
    return h,color,rough,metallic


def maps_from_height(h, strength=5.0):
    gx=(np.roll(h,-1,1)-np.roll(h,1,1))*.5*strength
    gy=(np.roll(h,-1,0)-np.roll(h,1,0))*.5*strength
    z=np.ones_like(h)
    normal=np.stack((-gx,-gy,z),axis=-1); normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    gl=(normal*.5+.5)
    dx=gl.copy(); dx[...,1]=1-dx[...,1]
    local=ndimage.gaussian_filter(h,7,mode="wrap")-h
    ao=clamp01(1-np.maximum(local,0)*2.4)
    return gl,dx,ao


def periodic_component(a):
    """Moisan periodic-plus-smooth decomposition, channel by channel."""
    h,w=a.shape[:2]
    yy=np.arange(h)[:,None]; xx=np.arange(w)[None,:]
    denom=2*np.cos(2*np.pi*xx/w)+2*np.cos(2*np.pi*yy/h)-4
    denom[0,0]=1
    out=np.empty_like(a,dtype=np.float32)
    channels=1 if a.ndim==2 else a.shape[2]
    src=a[...,None] if a.ndim==2 else a
    for c in range(channels):
        u=src[...,c].astype(np.float32); v=np.zeros((h,w),np.float32)
        d=u[0,:]-u[-1,:]; v[0,:]+=d; v[-1,:]-=d
        d=u[:,0]-u[:,-1]; v[:,0]+=d; v[:,-1]-=d
        sh=np.fft.fft2(v)/denom; sh[0,0]=0
        out[...,c] if a.ndim==3 else out
        if a.ndim==3: out[...,c]=u-np.fft.ifft2(sh).real
        else: out=u-np.fft.ifft2(sh).real
    return out


def ai_mud_maps(source_path, procedural_height, mean_roughness):
    """Turn the generated flat-lit mud study into a periodic, aligned PBR set."""
    im=Image.open(source_path).convert("RGB").resize((SIZE,SIZE),Image.Resampling.LANCZOS)
    color=periodic_component(np.asarray(im,dtype=np.float32)/255.0)
    lo,hi=np.percentile(color,(.5,99.5)); color=clamp01((color-lo)/max(float(hi-lo),1e-6))
    # Keep the study's hue but constrain it to the material sheet's dark loam range.
    target=np.array([.31,.27,.23],np.float32); mean=color.mean(axis=(0,1))
    color=clamp01((color-mean)*.58+target)
    lum=.2126*color[...,0]+.7152*color[...,1]+.0722*color[...,2]
    lum=periodic_component(lum)
    detail=lum-ndimage.gaussian_filter(lum,10,mode="wrap")
    h=clamp01(.58*procedural_height+.42*clamp01(.5+(lum-lum.mean())*1.7+detail*1.8))
    damp=clamp01((lum.mean()-lum)*4.2)
    rough=clamp01(mean_roughness+(lum-lum.mean())*.72-damp*.16)
    metal=np.zeros_like(h)
    return h,color*255.0,rough,metal


def _atomic_png(path, image):
    """Encode in memory, then replace atomically so interrupted writes cannot survive."""
    buf = io.BytesIO()
    image.save(buf, format="PNG", compress_level=6)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(path)


def as_u8(a):
    return np.clip(a*255+0.5,0,255).astype(np.uint8)


def save8(path,a):
    _atomic_png(path, Image.fromarray(as_u8(a)))


def save16(path,a):
    _atomic_png(path, Image.fromarray(np.clip(a*65535+0.5,0,65535).astype(np.uint16)))


def valid_material_dir(d, material_id):
    suffixes=("basecolor","normal_gl","normal_dx","roughness","height16","ao","metallic","orm")
    try:
        for suffix in suffixes:
            with Image.open(d/f"{material_id}_{suffix}.png") as im:
                im.verify()
        return (d/"material.json").is_file()
    except Exception:
        return False


def build(out: Path, mud_source: Path | None = None):
    out.mkdir(parents=True,exist_ok=True); manifest=[]
    for i,spec in enumerate(MATERIALS):
        d=out/spec["group"]/spec["id"]; d.mkdir(parents=True,exist_ok=True)
        data={**spec,"resolution_px":SIZE,"px_per_m":round(SIZE/spec["span_m"],2),"color_space":{"basecolor":"sRGB","normal_gl":"linear","normal_dx":"linear","roughness":"linear","height16":"linear 16-bit","ao":"linear","metallic":"linear","orm":"linear; R=AO G=Roughness B=Metallic"},"seamless":True,"generator_seed":18350701+i*97}
        if spec["kind"]=="mud" and mud_source is not None:
            data["generation_method"]="AI-generated flat-lit color study, made periodic; procedural/aligned PBR derivation"
        else:
            data["generation_method"]="deterministic procedural synthesis"
        if not valid_material_dir(d,spec["id"]):
            h,color,rough,metal=surface(spec,18350701+i*97); ngl,ndx,ao=maps_from_height(h,5.5 if spec["kind"] not in ("earth","mud","muck","sand") else 3.2)
            if spec["kind"]=="mud" and mud_source is not None:
                h,color,rough,metal=ai_mud_maps(mud_source,h,spec["mean_roughness"])
                ngl,ndx,ao=maps_from_height(h,3.8)
            save8(d/f'{spec["id"]}_basecolor.png',color/255.0)
            save8(d/f'{spec["id"]}_normal_gl.png',ngl)
            save8(d/f'{spec["id"]}_normal_dx.png',ndx)
            save8(d/f'{spec["id"]}_roughness.png',rough)
            save16(d/f'{spec["id"]}_height16.png',h)
            save8(d/f'{spec["id"]}_ao.png',ao)
            save8(d/f'{spec["id"]}_metallic.png',metal)
            orm=np.stack((as_u8(ao),as_u8(rough),as_u8(metal)),axis=-1)
            _atomic_png(d/f'{spec["id"]}_orm.png',Image.fromarray(orm))
        (d/"material.json").write_text(json.dumps(data,indent=2)+"\n")
        manifest.append(data)
    (out/"manifest.json").write_text(json.dumps({"library":"Chicago 1835 PBR Materials","version":"1.0.0","materials":manifest},indent=2)+"\n")
    make_contact_sheet(out,manifest)


def make_contact_sheet(out, manifest):
    thumb=220; label=52; cols=5; rows=math.ceil(len(manifest)/cols)
    sheet=Image.new("RGB",(cols*thumb,rows*(thumb+label)),(26,27,25)); draw=ImageDraw.Draw(sheet); font=ImageFont.load_default()
    for i,m in enumerate(manifest):
        p=out/m["group"]/m["id"]/f'{m["id"]}_basecolor.png'; im=Image.open(p).convert("RGB").resize((thumb,thumb),Image.Resampling.LANCZOS)
        x=(i%cols)*thumb; y=(i//cols)*(thumb+label); sheet.paste(im,(x,y));
        draw.text((x+7,y+thumb+7),m["id"].replace("_"," "),font=font,fill=(235,232,220))
        draw.text((x+7,y+thumb+24),f'{m["span_m"]:.2f} m tile · {m["confidence"][:26]}',font=font,fill=(166,169,157))
    sheet.save(out/"contact_sheet.jpg",quality=91,optimize=True)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,required=True); ap.add_argument("--mud-source",type=Path); a=ap.parse_args(); build(a.out,a.mud_source)


if __name__=="__main__": main()
