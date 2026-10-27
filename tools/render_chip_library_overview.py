"""Import and studio-render 9 representative library assets as a shelf display.

This creates ONE optional overview PNG; full 88-entry thumbnails are generated
by tools/make_chip_library_contact_sheets.py with original artwork previews.
"""
import bpy,os,math
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"previews","chips")
os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
S=bpy.context.scene
examples=[
"schwefel_nature_90g",
"schwefel_wave_inferno_120g",
"amigos_budget_paprika_350g",
"loop_naturaplan_nature_140g",
"kernell_chili_200g",
"staxo_original_185g",
"pompo_cheese_110g",
"alpcraft_black_truffle_100g",
"rootix_lentil_nature_90g",
]
def mat(name,base,metal=0,rough=.65):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*base,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*base,1)
    p.inputs["Metallic"].default_value=metal
    p.inputs["Roughness"].default_value=rough
    return m
wood=mat("Preview only | light shelf",(0.63,.58,.51),0,.56)
wall=mat("Preview only | showroom wall",(.31,.33,.35),0,.9)
metal=mat("Preview only | thin metal shelf lip",(.17,.18,.18),.7,.33)
def block(name,center,dims,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    o=bpy.context.object;o.name=name
    o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    return o
block("Only preview backdrop",(0,.23,.41),(1.9,.12,1.27),wall)
for z in (-.025,.41):
    block("Only preview supermarket shelf",(0,.028,z),(1.78,.43,.035),wood)
    block("Only preview front edge strip",(0,-.192,z+.005),(1.78,.015,.047),metal)
for i,asset_id in enumerate(examples):
    file=os.path.join(ROOT,"assets","chips",asset_id+".glb")
    assert os.path.isfile(file),(file,"missing library asset")
    initial=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=file)
    fresh=[obj for obj in bpy.context.scene.objects if obj not in initial]
    assert fresh,asset_id
    x=(-2+i%5)*.325 if i<5 else (-1.5+(i-5))*.325
    z=0.0 if i<5 else .435
    # Importer can add several empties; offset every imported root to avoid
    # reparenting or skewing objects due to glTF container transforms.
    roots=[obj for obj in fresh if obj.parent is None or obj.parent not in fresh]
    for root in roots:
        root.location.x+=x
        root.location.z+=z
        root.rotation_euler.z+=math.radians((i%3-1)*5)
    print("PLACED",asset_id,flush=True)
bpy.ops.object.camera_add(location=(.05,-2.65,.68))
cam=bpy.context.object
cam.rotation_euler=(Vector((0,0,.42))-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO"
cam.data.ortho_scale=2.06
S.camera=cam
for loc,power,size in [
    ((-1.1,-1.5,2.2),630,2.4),
    ((1.35,-.7,1.7),420,1.5),
]:
    bpy.ops.object.light_add(type="AREA",location=loc)
    o=bpy.context.object
    o.data.shape="DISK";o.data.energy=power;o.data.size=size
    o.rotation_euler=(Vector((0,0,.40))-o.location).to_track_quat("-Z","Y").to_euler()
S.world.color=(.18,.18,.18)
S.render.engine="CYCLES"
S.cycles.device="CPU"
S.cycles.samples=10
if hasattr(S.cycles,"use_denoising"):S.cycles.use_denoising=False
if hasattr(bpy.context.view_layer.cycles,"use_denoising"):bpy.context.view_layer.cycles.use_denoising=False
S.render.resolution_x=1300
S.render.resolution_y=820
S.render.resolution_percentage=100
S.render.image_settings.file_format="PNG"
S.render.filepath=os.path.join(OUT,"Preview_9_models_3D.png")
S.view_settings.view_transform="AgX"
bpy.ops.render.render(write_still=True)
print("RENDERED",S.render.filepath,flush=True)
