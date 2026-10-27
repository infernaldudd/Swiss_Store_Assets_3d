"""Photorealistic-ish Swiss sidewalk café A-frame chalkboard, double-sided.

Generates ONE .glb with two independently replaceable chalk surfaces,
weathered oak, hinges, screwed rail joints, support chains and rubber feet.
Authoring units: metres, +Z up. Original café artworks: LOOP LUNCH and AMIGOS OPEN.
Blender 4.0+: blender -b -t 2 --python tools/build_aframe_chalkboard.py
Set RENDER_PREVIEWS=1 for CPU Cycles PNG front/back.
"""
import bpy, math, os, struct, json
from mathutils import Vector, Matrix
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"assets")
PREV=os.path.join(ROOT,"previews")
TEX=os.path.join(ROOT,"textures","aframe")
os.makedirs(OUT,exist_ok=True)
os.makedirs(PREV,exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
C=bpy.context
S=bpy.context.scene

def material(name, color, metal=0.0, rough=.50, imagefile=None):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Metallic"].default_value=metal
    p.inputs["Roughness"].default_value=rough
    if imagefile:
        path=os.path.join(TEX,imagefile)
        assert os.path.isfile(path),("Missing generated texture",path)
        img=bpy.data.images.load(path,check_existing=True)
        img.pack()
        node=m.node_tree.nodes.new("ShaderNodeTexImage")
        node.image=img
        m.node_tree.links.new(node.outputs["Color"],p.inputs["Base Color"])
    return m

OAK=material("Frame | aged oak stained timber - PBR grain",
             (.48,.35,.23),rough=.78,imagefile="Weathered_Oak_Albedo.png")
ENDS=material("Wood | pale end grain",(.42,.30,.19),rough=.8)
BOARD_BACK=material("Board | deep charcoal birch core",(.068,.072,.070),rough=.90)
CHALK_LUNCH=material("Chalk face | editable LOOP LUNCH artwork",
                     (.09,.10,.10),rough=.94,imagefile="Chalk_LUNCH.png")
CHALK_OPEN=material("Chalk face | editable AMIGOS OPEN artwork",
                    (.09,.10,.10),rough=.94,imagefile="Chalk_OPEN.png")
METAL=material("Hardware | scratched satin nickel steel",(.48,.51,.50),metal=.91,rough=.30)
HINGE=material("Hardware | slightly tarnished stainless hinge",(.36,.36,.34),metal=.84,rough=.39)
RUBBER=material("Feet | weathered black anti-slip rubber",(.050,.046,.040),rough=.93)
CONCRETE=material("PREVIEW ONLY | pale city pavement",(.35,.34,.32),rough=.95)

objects=[]
def tag(obj, group):
    obj["export_asset"]=True
    obj["group"]=group
    objects.append(obj)
    return obj

def transform(side):
    # side -1: observer in front (-Y), +1: observer behind (+Y).
    # The top boards are only 0.108 m apart; feet open to 0.58 m.
    theta=side*.225
    return Matrix.Translation((0,side*.17,.575)) @ Matrix.Rotation(theta,4,"X")

def cuboid(name,center,size,mat,bevel=.0,group="wood",base=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob=C.object
    ob.name=name
    ob.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat)
    if bevel>0:
        b=ob.modifiers.new("lightly worn round edges","BEVEL")
        b.width=bevel
        b.segments=3
    T=base if base is not None else Matrix.Identity(4)
    ob.matrix_world=T @ Matrix.Translation(center)
    tag(ob,group)
    return ob

def cylinder(name, xyz, radius, depth, material,axis="Z",vertices=16,group="hardware"):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=xyz)
    o=C.object
    o.name=name
    if axis=="X":o.rotation_euler.y=math.pi*.5
    if axis=="Y":o.rotation_euler.x=math.pi*.5
    o.data.materials.append(material)
    tag(o,group)
    return o

def face(name,side,material,tf):
    # UV-exact thin face with correct left-to-right reading on both sides.
    width,height=.548,.849
    ymin=(-1 if side<0 else 1)*.028
    z=.022
    verts=[
        (-width/2,ymin,z-height/2),
        (width/2,ymin,z-height/2),
        (width/2,ymin,z+height/2),
        (-width/2,ymin,z+height/2)]
    mesh=bpy.data.meshes.new(name+" mesh")
    inds=(0,1,2,3) if side<0 else (3,2,1,0)
    mesh.from_pydata(verts,[],[inds])
    mesh.materials.append(material)
    mesh.update()
    uv=mesh.uv_layers.new(name="Artwork UV: freely replace image texture")
    # panel coordinate and UV relation mirror for opposite-facing sheet.
    lookup=[(0,0),(1,0),(1,1),(0,1)]
    for loop in mesh.polygons[0].loop_indices:
        vertex_i=mesh.loops[loop].vertex_index
        u,v=lookup[vertex_i]
        if side>0:u=1-u
        uv.data[loop].uv=(u,v)
    obj=bpy.data.objects.new(name,mesh)
    C.collection.objects.link(obj)
    obj.matrix_world=tf
    tag(obj,"face_lunch" if side<0 else "face_open")
    obj["replace_texture_with"] = "Any vertical 1024 x 1408 PNG; use original Artwork UV"
    obj["matte"] = True
    return obj

def screws(side,tf):
    for x in (-.306,.306):
        for z in (-.505,.497):
            P=tf @ Vector((x,side*.031,z))
            cylinder("Countersunk wood screw",P,.007,.007,METAL,axis="Y",vertices=12,group="small_hardware")

def build_side(side):
    T=transform(side)
    side_name="FRONT | LOOP LUNCH" if side<0 else "BACK | AMIGOS OPEN"
    # The original standing frame is made of rectangular, mitred wood stock.
    for x in (-.307,.307):
        cuboid(side_name+" | continuous oak leg", (x,0,-.001),
               (.052,.052,1.100),OAK,.005,"wood",T)
        # End-grain cap near scuffed ground and black slip sleeves.
        cuboid(side_name+" | end-grain face",(x,0,-.550),(.052,.053,.009),
               ENDS,.001,"wood",T)
        cuboid(side_name+" | booted anti-slip toe",(x,0,-.548),(.057,.059,.052),
               RUBBER,.007,"rubber",T)
    for z in (-.508,.508):
        cuboid(side_name+" | transverse oak rail",(0,0,z),
               (.654,.047,.058),OAK,.004,"wood",T)
    # Core is only 16 mm, exactly inset between the surface-facing timber rail.
    cuboid(side_name+" | inset actual 3D slate panel",
           (0,0,.022),(.562,.017,.862),BOARD_BACK,.0015,"board_back",T)
    face(side_name+" | replaceable chalk decal",side,
         CHALK_LUNCH if side<0 else CHALK_OPEN,T)
    screws(side,T)
    # Extra small retaining corners, where staples/wood screws are often visible.
    for x in (-.283,.283):
        for z in (-.439,.448):
            P=T @ Vector((x,side*.022,z))
            cylinder(side_name+" | recessed attachment bolt",P,.0045,.006,
                     HINGE,axis="Y",vertices=12,group="small_hardware")

for side in (-1,1):
    build_side(side)

# Hinges are integrated into BOTH upper frames, not floating ornament.
for x in (-.296,.296):
    cylinder("Top pivot through-bolt", (x,0,1.105),.013,.097,METAL,"X",24,"hinges")
    cylinder("Top hinge sleeve", (x,0,1.105),.020,.071,HINGE,"X",24,"hinges")
    for sy in (-.057,.057):
        cuboid("Foldable hinge's wall plate",(x,sy,1.073),
               (.068,.052,.014),HINGE,.003,"hinges")
    for dx in (-.050,.050):
        cylinder("Hinge pivot locknut",(x+dx,0,1.105),.019,.014,METAL,"X",18,"hinges")

# Two physically suspended link chains constrain the side opening.
# A catenary drop of ~45 mm gives the correct loose metal-chain silhouette.
for ix,x in enumerate((-.310,.310)):
    for i in range(17):
        f=i/16
        y=(f-.5)*.444
        # Catenary-like curve, lowest at the centre.
        z=.356-.045*(1-(2*f-1)**2)
        # Flattened ovals link into each other with alternating ring orientation.
        bpy.ops.mesh.primitive_torus_add(major_segments=12,minor_segments=7,
                                        location=(x,y,z),
                                        rotation=((math.pi*.5 if i%2 else 0),math.pi*.5,0),
                                        major_radius=.0153,minor_radius=.0029)
        o=C.object
        o.name="Support chain %d - oval link %02d"%(ix+1,i)
        o.scale=(.82,1.04,.77)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        o.data.materials.append(HINGE)
        tag(o,"chain")
    for y in (-.228,.228):
        cylinder("Chain connection anchor", (x,y,.364),.012,.037,METAL,
                 "X",16,"hinges")

# One engraved-style brand on the side is represented by chalk graphics only.
# Do not add extra geometry or photograph into the asset.

def join_groups():
    # Fewer engine draw calls. Chalk faces are intentionally separate editable meshes.
    for group in ("wood","rubber","board_back","small_hardware","hinges","chain"):
        objs=[o for o in list(C.scene.objects) if o.get("group")==group]
        if len(objs)<2:continue
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:o.select_set(True)
        C.view_layer.objects.active=objs[0]
        bpy.ops.object.convert(target="MESH")
        bpy.ops.object.join()
        merged=C.object
        merged.name="Cafe A-Frame | "+group.replace("_"," ")
        merged["export_asset"]=True
        merged["group"]=group
        print("JOINED",group,len(objs), flush=True)
    bpy.ops.object.select_all(action="DESELECT")

join_groups()

def export():
    bpy.ops.object.select_all(action="DESELECT")
    sign_objs=[o for o in C.scene.objects if o.type=="MESH" and o.get("export_asset")]
    assert len(sign_objs)>=8,(len(sign_objs),[o.name for o in sign_objs])
    for o in sign_objs:o.select_set(True)
    C.view_layer.objects.active=sign_objs[0]
    path=os.path.join(OUT,"Swiss_AFrame_Cafe_Chalkboard.glb")
    bpy.ops.export_scene.gltf(filepath=path,export_format="GLB",
                              use_selection=True,export_apply=True,
                              export_materials="EXPORT",export_yup=True)
    bpy.ops.object.select_all(action="DESELECT")
    with open(path,"rb") as f:
        magic,version,length=struct.unpack("<4sII",f.read(12))
        size,typ=struct.unpack("<I4s",f.read(8))
        data=json.loads(f.read(size))
    assert magic==b"glTF" and version==2 and length==os.path.getsize(path)
    mats=data.get("materials",[])
    names=[m["name"] for m in mats]
    assert len(data.get("meshes",[]))>=8,("Insufficient geometrical parts",len(data.get("meshes",[])))
    assert all(any(x in n for n in names) for x in ["chalk","oak","Hardware","Feet"])
    assert len(data.get("images",[]))>=3, ("not all original textures embedded",data.get("images"))
    assert os.path.getsize(path)>=300_000
    print("VALIDATED",os.path.basename(path),"meshes",len(data["meshes"]),
          "materials",len(mats),"embedded_images",len(data["images"]),
          "bytes",os.path.getsize(path),flush=True)

def preview(scene_label, cam_pos):
    # Preview-only ground, environment and photographic studio lighting.
    ground=cuboid("PREVIEW ONLY | textured pavement",(0,0,-.046),
                  (4.0,4.0,.09),CONCRETE,.0,"preview")
    ground["export_asset"]=False
    S.world.color=(.30,.30,.30)
    for i,(pos,power,size) in enumerate([
        ((-2.7,-2.8,4.1),360,3.2),((2.2,1.4,3.8),320,2.8)]):
        bpy.ops.object.light_add(type="AREA",location=pos)
        obj=C.object
        obj.name="PREVIEW ONLY | area light"
        obj.data.energy=power
        obj.data.shape="DISK"
        obj.data.size=size
        obj.rotation_euler=(Vector((0,0,.52))-obj.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.object.camera_add(location=cam_pos)
    camera=C.object
    camera.name="PREVIEW ONLY | camera"
    target=Vector((0,0,.57))
    camera.rotation_euler=(target-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.type="ORTHO"
    camera.data.ortho_scale=1.78
    S.camera=camera
    S.render.engine="CYCLES"
    S.cycles.device="CPU"
    S.cycles.samples=28
    if hasattr(S.cycles,"use_denoising"):S.cycles.use_denoising=False
    if hasattr(C.view_layer.cycles,"use_denoising"):C.view_layer.cycles.use_denoising=False
    S.render.resolution_x=900
    S.render.resolution_y=1030
    S.render.resolution_percentage=100
    S.render.image_settings.file_format="PNG"
    S.render.filepath=os.path.join(PREV,"Swiss_AFrame_Cafe_Chalkboard_"+scene_label+".png")
    S.view_settings.view_transform="AgX"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", S.render.filepath,flush=True)
    bpy.data.objects.remove(camera,do_unlink=True)
    for o in list(C.scene.objects):
        if o.type=="LIGHT":bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.objects.remove(ground,do_unlink=True)

def main():
    export()
    if os.environ.get("RENDER_PREVIEWS")=="1":
        preview("Front_LUNCH",(1.72,-2.5,1.58))
        preview("Back_OPEN",(-1.72,2.5,1.55))
    print("DONE: 1 independently textured double-sided sign",flush=True)

if __name__=="__main__":main()
