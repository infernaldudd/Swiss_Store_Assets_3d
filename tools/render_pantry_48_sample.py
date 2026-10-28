"""Render 8 representative REAL modeled pantry packages, one from each category.

Loads the same geometry and PBR 2K art builder used for the delivered GLBs.
The image is a Blender rendered QA of real 3D meshes, not a generic reference
image. Source package prototypes are the same as the SKU model geometry.
"""
import bpy,os,importlib.util,math
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
SRC=os.path.join(ROOT,"tools","build_pantry_48.py")
spec=importlib.util.spec_from_file_location("pantry_build_script",SRC)
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
lib.clear()
C=bpy.context
SC=C.scene
picked=[]
for group_idx,group in enumerate(lib.CAT["categories"]):
  # Chosen styles: pasta bag, rice bag, cereal box, coffee valve bag,
  # wrapped chocolate, glass sauce jar, paper flour sack and oil bottle.
  pick=(0,1,0,1,0,0,0,0)[group_idx]
  p=group["products"][pick]
  old=set(SC.objects)
  lib.build(p)
  new=[o for o in SC.objects if o not in old and o.type=="MESH"]
  assert len(new)>=2,(p["id"],len(new))
  col=group_idx%4
  row=group_idx//4
  x=(col-1.5)*.405
  y=(row-.5)*.54
  for o in new:
    o.location.x+=x
    o.location.y+=y
    o.name=p["id"]+" | "+o.name
  picked.append((p["id"],len(new)))
# Use shallow matte real plinths to catch contact shadows only.
slab=bpy.data.materials.new("PREVIEW | neutral concrete shelf plinth")
slab.diffuse_color=(.36,.39,.41,1)
slab.use_nodes=True
ps=slab.node_tree.nodes.get("Principled BSDF")
ps.inputs["Base Color"].default_value=(.36,.39,.41,1)
ps.inputs["Roughness"].default_value=.68
for i in range(2):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,(i-.5)*.54,-.033))
 o=C.object;o.name="PREVIEW ONLY | separate shallow display platform"
 o.dimensions=(1.78,.44,.063)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(slab)
for pos,power,size in [
 ((-1.55,-1.75,2.6),360,1.8),
 ((1.60,-.75,2.14),290,1.4),
 ((0,1.23,2.10),140,2.1)]:
 bpy.ops.object.light_add(type="AREA",location=pos)
 o=C.object;o.data.energy=power;o.data.size=size
 o.rotation_euler=(Vector((0,0,.16))-o.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.object.camera_add(location=(.64,-2.5,1.3))
cam=C.object
cam.rotation_euler=(Vector((0,0,.12))-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO";cam.data.ortho_scale=2.0
SC.camera=cam
SC.render.engine="CYCLES"
SC.cycles.device="CPU";SC.cycles.samples=20
if hasattr(SC.cycles,"use_denoising"):SC.cycles.use_denoising=False
if hasattr(C.view_layer.cycles,"use_denoising"):
 C.view_layer.cycles.use_denoising=False
SC.world.color=(.20,.21,.22)
SC.view_settings.view_transform="AgX"
SC.render.resolution_x=1450
SC.render.resolution_y=900
SC.render.resolution_percentage=100
SC.render.image_settings.file_format="PNG"
out=os.path.join(ROOT,"previews","pantry_48","Eight_Actual_Package_Shapes_3D.png")
SC.render.filepath=out
bpy.ops.render.render(write_still=True)
print("ACTUAL 3D PACKAGING QA",picked,"render",out,flush=True)
assert os.path.getsize(out)>100000
