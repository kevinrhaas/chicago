# SPDX-License-Identifier: GPL-3.0-or-later
"""Original reconstructed near-LOD textile maps; no captured/historical texture.

Pixels generated here are CC0-1.0 original artwork. The 32 mm repeat, 2/1 mm
linen/wool thread periods and micrometre relief are design choices, not evidence
of a resident's garment. No body, skin, hair, rig, source UV or far LOD is changed.
"""
from array import array
import math

SIZE, TILE_M = 128, .032
MATERIALS = {'garment_upper__shirt_linen': 'linen',
             'garment_outer__waistcoat_wool': 'wool',
             'garment_outer__round_jacket': 'wool',
             'garment_lower__highwaist_pantaloons': 'wool'}


JOSEPH = 'dufresne_joseph_1835'


def requested_near(variant, explicit=False):
    """The existing worker loop can opt in ONE named proof variant by data.

    Default recipes carry no switch. A reviewed measurement branch may set
    authoring_studies.woven_cloth_near_v1 on Joseph; no workflow/global default.
    """
    studies = variant.get('authoring_studies', {})
    if not isinstance(studies, dict) or type(explicit) is not bool:
        raise ValueError('invalid near-cloth authoring switch')
    configured = studies.get('woven_cloth_near_v1', False)
    if type(configured) is not bool:
        raise ValueError('near-cloth authoring switch must be boolean')
    enabled = explicit or configured
    if enabled and variant.get('id') != JOSEPH:
        raise ValueError('near-cloth study is Joseph-only; no Otis/Martin/default opt-in')
    return enabled


def relief(kind, u, v):
    """Periodic physical height field; linen interlaces, wool has diagonal wales."""
    if kind == 'linen':
        a, b = 2*math.pi*16*u, 2*math.pi*16*v
        return .000025*(math.cos(a)*(.55+.45*math.cos(b/2))+
                       math.cos(b)*(.55-.45*math.cos(a/2)))/2
    if kind == 'wool':
        return .000020*(.65*math.cos(2*math.pi*32*(u+v))+
                        .25*math.cos(2*math.pi*16*(u-v))+
                        .10*math.cos(2*math.pi*(3*u+5*v)))
    raise ValueError('unknown textile profile')


def map_pixels(kind, channel, color=(1., 1., 1., 1.), roughness=.9, size=SIZE):
    """RGBA float pixels suitable for packed PNG images, with no dependencies."""
    if kind not in ('linen', 'wool') or channel not in ('color', 'orm', 'normal'):
        raise ValueError('unknown textile profile/channel')
    if type(size) is not int or size < 128 or size > 512 or size & (size-1):
        raise ValueError('textile tile must be a power of two from 128 to 512')
    if len(color) != 4 or not all(math.isfinite(c) and 0 <= c <= 1 for c in color) or not .5 <= roughness <= .96:
        raise ValueError('invalid textile color/roughness')
    pixels = array('f')
    for y in range(size):
        for x in range(size):
            u, v = (x+.5)/size, (y+.5)/size
            h = relief(kind, u, v)
            heather = .65*math.sin(2*math.pi*(3*u+5*v))+.35*math.sin(2*math.pi*(13*u-7*v))
            variation = h/.000025
            if channel == 'normal':
                e = .00001
                dx = (relief(kind, u+e, v)-relief(kind, u-e, v))/(2*e*TILE_M)
                dy = (relief(kind, u, v+e)-relief(kind, u, v-e))/(2*e*TILE_M)
                length = math.sqrt(dx*dx+dy*dy+1)
                rgb = ((1-dx/length)/2, (1-dy/length)/2, (1+1/length)/2)
            elif channel == 'orm':
                rgb = (1., max(.5, min(1., roughness+.025*heather-.018*variation)), 0.)
            else:
                strength = .025 if kind == 'linen' else .045
                shade = 1+strength*variation+.025*heather
                rgb = tuple(max(0., min(1., c*shade)) for c in color[:3])
            pixels.extend((*rgb, 1.))
    return pixels


def calibration(triangles):
    """Measure actual average UV/metre density; report inherited chart variation."""
    area_m = area_uv = 0.
    densities = []
    for ps, uv in triangles:
        if len(ps) != 3 or len(uv) != 3 or any(len(p) != 3 for p in ps) or any(len(p) != 2 for p in uv) or any(not math.isfinite(x) for p in [*ps, *uv] for x in p):
            raise ValueError('calibration needs finite triangle positions/UVs')
        a, b = ([ps[j][i]-ps[0][i] for i in range(3)] for j in (1, 2))
        physical = math.hypot(a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])/2
        tex = abs((uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-(uv[1][1]-uv[0][1])*(uv[2][0]-uv[0][0]))/2
        if physical <= 1e-18 or tex <= 1e-18:
            raise ValueError('degenerate physical/UV cloth triangle')
        area_m += physical; area_uv += tex
        densities.append(math.sqrt(tex/physical))
    if not densities:
        raise ValueError('no actual cloth triangles to calibrate')
    density = math.sqrt(area_uv/area_m)
    return {'surface_area_m2': area_m, 'uv_area': area_uv, 'uv_per_m_average': density,
            'uv_per_m_range': [min(densities), max(densities)], 'tile_side_m': TILE_M,
            'uv_repeat': 1/(density*TILE_M), 'average_texels_per_m': SIZE/TILE_M,
            'scope': 'area-weighted average; inherited UV stretch remains, not uniform metric density'}


def memory_cost(material_count, profile_count=2):
    """Conservative RGBA8 estimate; separate near GLBs may decode duplicate images."""
    if type(material_count) is not int or material_count not in (3, 4) or profile_count != 2:
        raise ValueError('budget covers the actual three/four-material linen+wool workwear assembly')
    images = 2*material_count+profile_count
    mip_pixels = sum((SIZE >> n)**2 for n in range(SIZE.bit_length()))
    old_shirt_mips = sum((256 >> n)**2 for n in range(9))*4
    per_lod = images*mip_pixels*4
    return {'image_count': images, 'size': [SIZE, SIZE], 'rgba8_base_bytes': images*SIZE*SIZE*4,
            'rgba8_mip_bytes_per_near_lod': per_lod,
            'net_mip_bytes_vs_existing_shirt_per_near_lod': per_lod-old_shirt_mips,
            'net_mip_bytes_both_near_lods': 2*(per_lod-old_shirt_mips),
            'far_lod_increment_bytes': 0, 'scope': 'uncompressed RGBA8 with full mips; excludes geometry, decoder/transient copies and runtime shader costs'}


def apply_near(scene, colors, roughness, variant_id):
    """BPy-only hook: standard portable image nodes on cloned LOD0/1 materials."""
    if variant_id != JOSEPH:
        raise ValueError('near-cloth material hook is Joseph-only')
    import bpy
    groups = {}
    for obj in bpy.data.collections['lod0'].all_objects:
        if obj.type != 'MESH':
            continue
        uv = obj.data.uv_layers.active
        for face in obj.data.polygons:
            material = obj.data.materials[face.material_index]
            if material.name not in MATERIALS or not face.use_smooth:
                continue  # Physical return strips deliberately reuse neighboring UVs.
            if len(face.vertices) != 3 or uv is None:
                raise ValueError('near textile calibration requires triangulated actual UVs')
            groups.setdefault(material.name, []).append((
                [tuple(obj.matrix_world @ obj.data.vertices[i].co) for i in face.vertices],
                [tuple(uv.data[i].uv) for i in face.loop_indices]))
    if not (set(MATERIALS)-{'garment_outer__round_jacket'}) <= set(groups):
        raise ValueError('near textile opt-in requires actual linen/waistcoat/trouser LOD0 garments')
    images, near, receipts = {}, {}, {}
    def texture(kind, channel, color, r):
        key = (kind, channel, tuple(color) if channel == 'color' else r if channel == 'orm' else None)
        if key not in images:
            im = bpy.data.images.new('original_reconstructed_'+kind+'_'+channel+'_'+str(len(images)), width=SIZE, height=SIZE, alpha=False)
            im.colorspace_settings.name = 'sRGB' if channel == 'color' else 'Non-Color'
            im.pixels.foreach_set(map_pixels(kind, channel, color, r))
            im.file_format = 'PNG'; im.pack(); images[key] = im
        return images[key]
    for name, triangles in groups.items():
        kind, metric = MATERIALS[name], calibration(triangles)
        material = bpy.data.materials[name].copy()
        material.name = name+'__woven_near'
        material['chicago4d_cloth_microtexture'] = {
            'version': 1, 'profile': kind, 'source_material': name,
            'grade': 'reconstructed', 'license': 'CC0-1.0',
            'tile_side_m': TILE_M, 'uv_repeat': metric['uv_repeat'],
            'historical_texture': False, 'photo_quality_accepted': False,
            'runtime_weave': 'portable_maps_replace_common_fabric'}
        near[name] = material
        nodes, links = material.node_tree.nodes, material.node_tree.links
        for old in list(nodes):
            if old.type == 'TEX_IMAGE':
                nodes.remove(old)  # Only the clone: omit its replaced shirt checker.
        bsdf = nodes['Principled BSDF']
        # Maps already carry the recipe color and absolute roughness; do not tint twice.
        bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
        bsdf.inputs['Roughness'].default_value = 1
        uv = nodes.new('ShaderNodeTexCoord'); mapping = nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (metric['uv_repeat'], metric['uv_repeat'], 1)
        links.new(uv.outputs['UV'], mapping.inputs['Vector'])
        maps = {}
        for channel in ('color', 'orm', 'normal'):
            node = nodes.new('ShaderNodeTexImage')
            node.image = texture(kind, channel, colors[name], roughness[name])
            node.interpolation, node.extension = 'Linear', 'REPEAT'
            links.new(mapping.outputs['Vector'], node.inputs['Vector']); maps[channel] = node
        links.new(maps['color'].outputs['Color'], bsdf.inputs['Base Color'])
        split = nodes.new('ShaderNodeSeparateColor'); split.mode = 'RGB'
        links.new(maps['orm'].outputs['Color'], split.inputs['Color'])
        links.new(split.outputs['Green'], bsdf.inputs['Roughness'])
        links.new(split.outputs['Blue'], bsdf.inputs['Metallic'])
        normal = nodes.new('ShaderNodeNormalMap'); normal.uv_map = 'UVMap'
        links.new(maps['normal'].outputs['Color'], normal.inputs['Color'])
        links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
        receipts[name] = {'profile': kind, **metric}
    for lod in (0, 1):
        for obj in bpy.data.collections['lod'+str(lod)].all_objects:
            if obj.type == 'MESH':
                for i, material in enumerate(obj.data.materials):
                    if material.name in near:
                        obj.data.materials[i] = near[material.name]
    report = {'version': 1, 'variant': variant_id, 'grade': 'reconstructed', 'license': 'CC0-1.0', 'historical_texture': False,
              'photo_quality_accepted': False, 'lods': [0, 1], 'materials': receipts,
              'normal_convention': 'OpenGL tangent +Y, strength 1', 'thread_period_m': {'linen': .002, 'wool': .001},
              'height_coefficient_m': {'linen': .000025, 'wool': .000020},
              'memory_estimate': memory_cost(len(near), len({MATERIALS[n] for n in near})),
              'actual_packed_images': len(images), 'shared_normals': True,
              'runtime_note': 'marked near material maps replace common fabric weave/heather/rumple/sheens; actual HumanActor and export readback remain required'}
    return report
