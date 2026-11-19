#!/usr/bin/env python3
"""Verify the full-city 1871 context's geographic and walk-support contracts."""
from __future__ import annotations
import collections
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generators"))
import city_1871_emit as recipe


def main():
    doc=json.loads((ROOT/"data/context/1871.json").read_text())
    plan=json.loads((ROOT/"data/context/1871/plan.json").read_text())
    stamp=json.loads((ROOT/"data/context/1871/generated-assets.json").read_text())
    meta=json.loads((recipe.EPOCH/"heightfield.json").read_text())
    raw=(recipe.EPOCH/"heightfield.bin").read_bytes()
    values=struct.unpack("<"+str(len(raw)//2)+"h",raw)
    fails=[]
    def check(ok,message):
        if not ok:fails.append(message)
    def height(e,n):
        x=(e-meta["origin_e"])/meta["cell_m"];y=(n-meta["origin_n"])/meta["cell_m"]
        i,j=math.floor(x),math.floor(y);fx,fy=x-i,y-j;c=meta["cols"]
        if not (0<=i<c-1 and 0<=j<meta["rows"]-1):return -999
        h=lambda di,dj:values[(j+dj)*c+i+di]*meta["scale"]
        return (h(0,0)*(1-fx)+h(1,0)*fx)*(1-fy)+(h(0,1)*(1-fx)+h(1,1)*fx)*fy
    check(doc["kind"]=="city_context_1871" and doc["target_date"]=="1871-10-08","wrong temporal selection")
    check(doc["inputs_sha256"]==recipe.inputs_sha()==stamp["inputs_sha256"]==meta["inputs_sha256"],"stale recipe/plan/field")
    for rel,entry in stamp["files"].items():
        p=ROOT/rel
        check(p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==entry["sha256"],f"generated output drift: {rel}")
    check(len(values)==meta["cols"]*meta["rows"],"field dimensions disagree")
    check(meta["skirt"]["margin_m"]>=20000,"city horizon has no 20km skirt")
    check(meta["mesh_max_interpolation_error_m"]<=.03,"ground triangles exceed 30mm field agreement")
    check(meta["cell_m"]<=10,"navigation field is too coarse for the refined bank trace")
    check(meta["reconstruction"]["horizontal_map_rms_m"]==plan["map_control"]["rms_m"],"terrain has stale training residual metadata")
    check(meta["reconstruction"]["held_out_rmse_m"]==plan["map_control"]["held_out_rms_m"],"terrain has stale reserved-check accuracy metadata")
    check(len(doc["buildings"])>=25000,"city context has shrunk to a neighborhood")
    check(len({b["kit"] for b in doc["buildings"]})==16,"one or more period kit families is absent")
    check(set(b["id"] for b in doc["bridges"])==set(b["id"] for b in plan["bridges"]),"mapped bridge inventory was dropped")
    bridge_sources={b["id"]:b for b in plan["bridges"]}
    for bridge in doc["bridges"]:
        source=bridge_sources[bridge["id"]]
        check(bridge.get("reported_historical_length_m")==source.get("reported_length_m"),f"bridge reported length was invented or altered: {bridge['id']}")
        check(bridge.get("sources")==source.get("sources",["mitchell_1870_chicago_map"]),f"bridge source list differs from its evidence: {bridge['id']}")
        if source.get("axis_points"):
            check(math.dist(bridge["center"],source["point"])<=.008,f"confirmed bridge point was moved: {bridge['id']}")
            check(bridge.get("alignment")=="source_point_and_axis",f"confirmed bridge axis was ignored: {bridge['id']}")
        else:
            check(bridge.get("alignment")=="mapped_road_river_intersection" and bridge["context_offset_m"]<=source.get("max_alignment_offset_m",35),f"bridge used an undeclared displaced crossing: {bridge['id']}")
    city=recipe.City(plan)
    # The drawn named streets (mapped arterials and the platted core), as the
    # visitor sees them: no lot may stand in their carriageway or walks.
    named_index=recipe.SpatialLines([{"points":[s["a"],s["b"]],"width_m":s["width_m"],"walk_m":s["walk_m"]} for s in doc["streets"] if s["alignment"]!="reconstructed_grid"])
    collision=collections.defaultdict(list);overlaps=[];unsupported=[];forbidden=[];mapped_intrusions=[]
    for b in doc["buildings"]:
        # A lot facing east or west has its frontage along v (T-3684).
        u,v=recipe.uv(b["e"],b["n"]);w,d=recipe.extents(b)
        corners=recipe.corners(b["e"],b["n"],b["width_m"],b["depth_m"],b["bearing_deg"])
        if min(height(*p) for p in corners)<b["base_m"]-.015:unsupported.append(b["id"])
        if any(not named_index.clear(p,1.98) for p in corners):mapped_intrusions.append(b["id"])
        if any(not recipe.inside(p,city.boundary) or city.park(p) or any(recipe.inside(p,x["polygon"]) for x in city.exclusions) for p in corners):forbidden.append(b["id"])
        ix,iy=math.floor(u/100),math.floor(v/100)
        for x in range(ix-1,ix+2):
            for y in range(iy-1,iy+2):
                for old,ou,ov,ow,od in collision[x,y]:
                    if abs(u-ou)<(w+ow)/2-.025 and abs(v-ov)<(d+od)/2-.025:overlaps.append((b["id"],old))
        collision[ix,iy].append((b["id"],u,v,w,d))
    check(not unsupported,f"{len(unsupported)} building footprints lack field support: {unsupported[:5]}")
    check(not forbidden,f"{len(forbidden)} buildings cross water/park/burn/city exclusion: {forbidden[:5]}")
    check(not overlaps,f"{len(overlaps)} generic buildings overlap: {overlaps[:5]}")
    check(not mapped_intrusions,f"{len(mapped_intrusions)} buildings intrude into mapped arterial corridors: {mapped_intrusions[:5]}")
    mapped={r["id"]:r for r in plan["streets"]}
    names=json.loads((ROOT/"data/context/1871/street_names_1871.json").read_text())
    sources_dir=ROOT/"data/sources"
    for key,base in names["bases"].items():
        check(all((sources_dir/f"{x}.json").exists() for x in base["sources"]),f"street-name basis cites a missing source: {key}")
    easing=doc.get("arterial_easing",{});splines={};deviations=[]
    for street in doc["streets"]:
        name=street.get("name")
        check(not name or "reconstructed" not in name.lower(),f"street carries a placeholder name: {street['street_id']}")
        check(street.get("name_basis") in names["bases"] or street.get("name_basis")=="reconstructed",f"street name has no declared basis: {street['street_id']}")
        check(bool(name)==(street.get("name_basis") not in ("reconstructed","unread")),f"street name and its basis disagree: {street['street_id']}")
        if street.get("alignment")!="mapped_arterial":continue
        # Arterials run on a spline through their traced points; only an end
        # eased onto the street it continues (declared in arterial_easing)
        # may leave that spline, by no more than its declared shift.
        source=mapped.get(street.get("trace_id"))
        check(source is not None,f"mapped road has no plan trace: {street['street_id']}")
        if not source:continue
        check(street.get("source_name")==source["name"],f"mapped road source name differs from its trace: {street['street_id']}")
        if street["trace_id"] not in splines:splines[street["trace_id"]]=recipe.catmull(source["points"])
        for p in (street["a"],street["b"]):
            off=recipe.distance(p,splines[street["trace_id"]]);allowed=.015
            for e,n,shift in easing.get(street["street_id"],[]):
                check(shift<=70,f"arterial eased too far: {street['street_id']}")
                if math.dist(p,(e,n))<=310+shift:allowed=max(allowed,shift+.015)
            if off>allowed:deviations.append((round(off,3),street["street_id"]))
    check(not deviations,f"named roads were moved off their mapped traces: {sorted(deviations)[-5:]}")
    # Curving streets are smooth: within one street's run no vertex turns
    # more than 10 degrees, unless it is a street corner (60 degrees or more,
    # or a fillet's arc drawn in sub-metre steps).
    runs=collections.defaultdict(list)
    for street in doc["streets"]:runs[street["run"]].append(street)
    kinks=[]
    for segs in runs.values():
        if segs[0]["alignment"]=="reconstructed_grid":continue
        for x,y in zip(segs,segs[1:]):
            if x["b"]!=y["a"]:continue
            turn=recipe.turning(x["a"],x["b"],y["b"])
            if 10.5<turn<60 and min(math.dist(x["a"],x["b"]),math.dist(y["a"],y["b"]))>=1:kinks.append((x["street_id"],x["b"],round(turn,1)))
    check(not kinks,f"{len(kinks)} street kinks over 10 degrees: {kinks[:5]}")
    check(all(len(j)==4 and j[2]!=j[3] for j in doc.get("junctions",[])) and len(doc.get("junctions",[]))>=300,"named street junctions are missing")
    # Inspect both visible edges, independently of the generator's centerline
    # clipping. A walk overhanging a riverbank by metres must fail even if a
    # runtime floor callback would keep the visitor on the floating planks.
    surfaces=doc.get("walk_surfaces",[])
    # One road floor per drawn segment; walks are cut where they cross another
    # street's carriageway (T-3684), so a segment has zero or more walk pieces.
    roads_ids=[x["id"][:-5] for x in surfaces if x["kind"]=="road"]
    check(len(roads_ids)==len(set(roads_ids))==len(doc["streets"]),"road ribbons lack exact floor descriptors")
    road_set=set(roads_ids)
    check(all(x["id"].split("_walk_")[0] in road_set for x in surfaces if x["kind"]=="walk"),"walk ribbon belongs to no road")
    # T-3685: a plank crossing belongs to the walk line of a drawn segment and
    # lies only on a dirt street; paved streets were crossed on their paving.
    crossing_ids=[x["id"].rsplit("_x",1)[0] for x in surfaces if x["kind"]=="crossing"]
    check(bool(crossing_ids) and all(x in road_set for x in crossing_ids),"plank crossings are missing or belong to no road")
    check(doc["surface_heights_m"]["road"]<doc["surface_heights_m"]["crossing"]<doc["surface_heights_m"]["walk"]
          and doc["surface_heights_m"]["walk"]-doc["surface_heights_m"]["road"]<=.35,"raised walks are not a step above the road and its crossings")
    # T-3685: what each street is made of, and the report that bounds it.
    paving=json.loads((ROOT/doc["paving"]["rules"]).read_text())
    check((ROOT/"data/sources"/(paving["source"]+".json")).exists(),"street paving cites an unresolved source")
    check(doc["paving"]["liberty"] in (ROOT/"docs/LIBERTIES.md").read_text(),"street surfaces carry no recorded liberty")
    pairs={("woodblock","report_1871"),("woodblock","principal_thoroughfare"),("setts","river_street"),("dirt","unpaved")}
    check(all((x.get("surface"),x.get("surface_basis")) in pairs for x in doc["streets"]),"a street surface has no declared basis")
    check(any(x["surface_basis"]=="report_1871" for x in doc["streets"]),"no street is paved where the 1871 report puts its wood block")
    # Pieces are budgeted block by block in their own division; a drawn segment
    # may join blocks across a division line, so the city total is the check.
    drawn=collections.Counter()
    for x in doc["streets"]:drawn[x["surface"]]+=math.dist(x["a"],x["b"])
    for kind,key in (("woodblock","woodblock_lineal_ft"),("setts","boulder_lineal_ft")):
        allowed=sum(v for k,v in paving["totals"][key].items() if k!="locator")*.3048
        check(drawn[kind]<=allowed+1,f"more {kind} drawn ({drawn[kind]:.0f} m) than the report's {allowed:.0f} m")
        for div,kinds in doc["paving"]["lengths_m"].items():
            check(kinds.get(kind,0)<=paving["totals"][key].get(div,0)*.3048+1,f"more {kind} budgeted in the {div} division than the report's figure")
    street_bins=collections.defaultdict(list)
    for x in doc["streets"]:
        h=x["width_m"]/2
        for i in range(math.floor((min(x["a"][0],x["b"][0])-h)/100),math.floor((max(x["a"][0],x["b"][0])+h)/100)+1):
            for j in range(math.floor((min(x["a"][1],x["b"][1])-h)/100),math.floor((max(x["a"][1],x["b"][1])+h)/100)+1):street_bins[i,j].append(x)
    for x in surfaces:
        if x["kind"]=="crossing":
            m=((x["a"][0]+x["b"][0])/2,(x["a"][1]+x["b"][1])/2)
            under=[s for s in street_bins[math.floor(m[0]/100),math.floor(m[1]/100)] if recipe.segdist(m,s["a"],s["b"])<=s["width_m"]/2]
            check(bool(under) and any(s["surface"]=="dirt" for s in under),f"plank crossing not over a dirt street: {x['id']}")
    surface_bins=collections.defaultdict(list);unsupported_walks=[]
    for surface in surfaces:
        a,b=surface["a"],surface["b"];width=surface["width_m"]
        dx,dn=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dn)
        check(length>0 and surface["y"]==doc["surface_heights_m"][surface["kind"]],f"invalid floor ribbon: {surface['id']}")
        for x in range(math.floor((min(a[0],b[0])-width/2-.003)/250),math.floor((max(a[0],b[0])+width/2+.003)/250)+1):
            for y in range(math.floor((min(a[1],b[1])-width/2-.003)/250),math.floor((max(a[1],b[1])+width/2+.003)/250)+1):surface_bins[x,y].append(surface)
        if surface["kind"]=="walk":
            count=max(1,math.ceil(length/4));worst=0.
            for i in range(count+1):
                for side in (-1,1):
                    e=a[0]+dx*i/count-side*dn/length*width/2
                    n=a[1]+dn*i/count+side*dx/length*width/2
                    worst=max(worst,surface["y"]-height(e,n))
            if worst>.35:unsupported_walks.append((surface["id"],round(worst,3)))
    check(not unsupported_walks,f"sidewalk edges overhang unsupported banks: {unsupported_walks[:8]}")
    def floor_covers(surface,e,n,y):
        a,b=surface["a"],surface["b"];dx,dn=b[0]-a[0],b[1]-a[1];length2=dx*dx+dn*dn
        along=((e-a[0])*dx+(n-a[1])*dn)/length2
        across=abs((e-a[0])*dn-(n-a[1])*dx)/math.sqrt(length2)
        return -.002/math.sqrt(length2)<=along<=1+.002/math.sqrt(length2) and across<=surface["width_m"]/2+.002 and abs(y-surface["y"])<.001
    blob=(ROOT/"data/context/1871/streets.glb").read_bytes()
    js_len=struct.unpack_from("<I",blob,12)[0];road_gltf=json.loads(blob[20:20+js_len]);bin_start=28+js_len
    bad_floor_vertices=0;floor_vertices=0
    for node in road_gltf["nodes"]:
        layer=node.get("extras",{}).get("layer")
        if layer=="saturday_fire_clearance":
            for primitive in road_gltf["meshes"][node["mesh"]]["primitives"]:
                accessor=road_gltf["accessors"][primitive["attributes"]["POSITION"]]
                view=road_gltf["bufferViews"][accessor["bufferView"]];offset=bin_start+view.get("byteOffset",0)+accessor.get("byteOffset",0)
                for i in range(accessor["count"]):
                    e,y,z=struct.unpack_from("<fff",blob,offset+12*i)
                    check(height(e,-z)>=recipe.GRADE-.015,"fire-clearance overlay paints solid ground across water or an unsupported bank")
        if layer not in ("streets","walks","crossings"):continue
        kind={"streets":"road","walks":"walk","crossings":"crossing"}[layer]
        for primitive in road_gltf["meshes"][node["mesh"]]["primitives"]:
            accessor=road_gltf["accessors"][primitive["attributes"]["POSITION"]]
            view=road_gltf["bufferViews"][accessor["bufferView"]];offset=bin_start+view.get("byteOffset",0)+accessor.get("byteOffset",0)
            for i in range(accessor["count"]):
                e,y,z=struct.unpack_from("<fff",blob,offset+12*i);n=-z;floor_vertices+=1
                if not any(surface["kind"]==kind and floor_covers(surface,e,n,y) for surface in surface_bins[math.floor(e/250),math.floor(n/250)]):bad_floor_vertices+=1
    check(floor_vertices>0 and not bad_floor_vertices,f"{bad_floor_vertices} visible road/walk vertices lack matching runtime floors")
    bridges=[d for d in doc["walk_decks"] if d.get("kind")=="bridge"]
    quays=[d for d in doc["walk_decks"] if d.get("kind")=="quay"]
    check(len(bridges)==len(doc["bridges"]) and len(bridges)+len(quays)==len(doc["walk_decks"]),"walk decks have missing or unknown kinds")
    check(bool(quays),"no quays have declared walk surfaces")
    for d in bridges:
        check(len(d["pts"])==4 and d["y"]==recipe.DECK_Y,f"invalid bridge deck: {d['id']}")
        gaps=[d["y"]-height(*p) for p in d["pts"]+d["axis_endpoints"]]
        check(max(gaps)<=.35,f"unwalkable bridge approach {d['id']}: {max(gaps):.3f}m step")
        midpoint=[sum(p[k] for p in d["axis_endpoints"])/2 for k in (0,1)]
        check(height(*midpoint)<0,f"bridge has no water below center: {d['id']}")
    for d in quays:
        check(len(d["pts"])==4 and d["y"]==recipe.WALK_Y,f"invalid quay deck: {d['id']}")
        a,b=d["land_edge"]
        edge=[(a[0]+(b[0]-a[0])*i/36,a[1]+(b[1]-a[1])*i/36) for i in range(37)]
        check(max(abs(d["y"]-height(*p)) for p in edge)<=.35,f"quay outer edge does not meet supported land: {d['id']}")
        path=d["access_path"]
        check(len(path)>=3 and height(*path[0])>=d["y"]-.35,f"quay access starts off land: {d['id']}")
        check(recipe.inside(path[-1],d["pts"]),f"quay access does not enter its deck: {d['id']}")
        floors=[]
        for a,b in zip(path,path[1:]):
            count=max(1,math.ceil(math.dist(a,b)/.2))
            for i in range(count+1):
                p=(a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count)
                ground=height(*p)
                floors.append(d["y"] if recipe.inside(p,d["pts"]) else ground)
        check(max(abs(b-a) for a,b in zip(floors,floors[1:]))<=.35,f"quay access has an unsafe step or floor gap: {d['id']}")
        # Access must not run through a generic warehouse to reach the dock.
        for p in path:
            u,v=recipe.uv(*p);ix,iy=math.floor(u/100),math.floor(v/100)
            blocked=any(abs(u-ou)<ow/2 and abs(v-ov)<od/2
                        for x in range(ix-1,ix+2) for y in range(iy-1,iy+2)
                        for _,ou,ov,ow,od in collision[x,y])
            check(not blocked,f"quay access enters a building: {d['id']}")
    # Check the actual portable visible mesh, not a second copy of the recipe:
    # every rendered quay-floor vertex must belong to a declared walk polygon.
    blob=(ROOT/"data/context/1871/bridges.glb").read_bytes()
    js_len=struct.unpack_from("<I",blob,12)[0];gltf=json.loads(blob[20:20+js_len]);bin_start=28+js_len
    visible=[];visible_triangles=[]
    for node in gltf["nodes"]:
        if node.get("extras",{}).get("layer")!="quays":continue
        for primitive in gltf["meshes"][node["mesh"]]["primitives"]:
            acc=gltf["accessors"][primitive["attributes"]["POSITION"]];view=gltf["bufferViews"][acc["bufferView"]]
            offset=bin_start+view.get("byteOffset",0)+acc.get("byteOffset",0)
            vertices=[struct.unpack_from("<fff",blob,offset+12*i) for i in range(acc["count"])]
            visible.extend(vertices)
            ia=gltf["accessors"][primitive["indices"]];iv=gltf["bufferViews"][ia["bufferView"]]
            io=bin_start+iv.get("byteOffset",0)+ia.get("byteOffset",0)
            fmt="I" if ia["componentType"]==5125 else "H"
            indices=struct.unpack_from("<"+str(ia["count"])+fmt,blob,io)
            check(len(indices)%3==0,"quay floor has incomplete triangle indices")
            for i in range(0,len(indices),3):
                tri=[vertices[k] for k in indices[i:i+3]]
                a,b,c=tri
                upward=(b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2])
                check(upward>0,"quay floor triangle is degenerate or faces down")
                visible_triangles.append(tuple(sorted(tri)))
    f32=lambda p:struct.unpack("<fff",struct.pack("<fff",*p))
    declared=[f32((e,d["y"],-n)) for d in quays for e,n in d["pts"]]
    check(collections.Counter(visible)==collections.Counter(declared),"visible quay mesh and declared walk floors disagree")
    expected_triangles=[]
    for d in quays:
        vertices=[f32((e,d["y"],-n)) for e,n in d["pts"]]
        expected_triangles.extend(tuple(sorted(vertices[k] for k in triangle)) for triangle in ((0,1,2),(0,2,3)))
    check(collections.Counter(visible_triangles)==collections.Counter(expected_triangles),"rendered quay triangles leave a walk-surface gap or extra floor")
    check(any(n.get("extras",{}).get("layer")=="quay_piles" for n in gltf["nodes"]),"quay platforms have no generated timber support")
    for name in ("terrain","water"):
        p=ROOT/f"assets/gltf/{name}__e1871_prefire.glb";raw=p.read_bytes()
        check(struct.unpack_from("<III",raw)==(0x46546c67,2,len(raw)),f"invalid GLB container: {name}")
        size,kind=struct.unpack_from("<II",raw,12);gltf=json.loads(raw[20:20+size]);node=gltf["nodes"][0]
        check(node["name"]==f"{name}__e1871_prefire" and node["extras"]["terrain_epoch"]=="e1871_prefire",f"terrain GLB identity failed: {name}")
        check(gltf["asset"]["extras"]["inputs_sha256"]==doc["inputs_sha256"],f"GLB is stale: {name}")
        check(all("_CONFIDENCE" in p["attributes"] for m in gltf["meshes"] for p in m["primitives"]),f"missing confidence channel: {name}")
    if fails:
        print("\n".join("FAIL "+x for x in fails));return 1
    print(f"1871 context PASS: {len(doc['buildings']):,} footprints, 16 kits, {len(bridges)} walkable bridges, {len(quays)} supported quay bays; visible floor agreement, safe bank access, field support, exclusion masks, non-overlap, 30mm mesh agreement, provenance and every generated hash verified")
    return 0


if __name__=="__main__":raise SystemExit(main())
