import bpy,json,sys
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
pts=[o.matrix_world@Vector(c) for o in bpy.context.scene.objects if o.type=='MESH' for c in o.bound_box]
print('BOUNDS',[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)])
for o in bpy.context.scene.objects:
 if o.type=='MESH':print(o.name,list(o.scale),len(o.data.vertices))
