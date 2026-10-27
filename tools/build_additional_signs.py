"""Additional illuminated Swiss game signage: AMIGOS triple A, single A, and EXIT.

Run:
  blender -b -t 2 --python tools/build_additional_signs.py
  RENDER_PREVIEWS=1 blender -b -t 2 --python tools/build_additional_signs.py

Metres; letter fronts face -Y; +Z is up. Only three NEW GLBs are touched.
"""
import bpy
import json
import math
import os
import struct
import sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(__file__))
import build_store_signs as base

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
PREV = os.path.join(ROOT, "previews")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREV, exist_ok=True)

# Consistent with the first AMIGOS set but with improved shadow gaskets and mounts.
ORANGE = base.FRONTS_AMIGOS[0]
SATIN_ORANGE = base.RETURN_AMIGOS
STEEL = base.STEEL
DARK_STEEL = base.DARK_STEEL
GASKET = base.SCREWS
GREEN_FACE = base.mat("Exit | translucent illuminated green acrylic",
                      (0.018, 0.49, 0.16), metallic=0.0, roughness=0.27, emit=2.2)
GREEN_EDGE = base.mat("Exit | dark green enamel return",
                      (0.018, 0.115, 0.061), metallic=0.31, roughness=0.31)
WHITE_ICON = base.mat("Exit | luminous white diffuser",
                      (0.88, 1.00, 0.91), metallic=0.0, roughness=0.32, emit=2.75)
DARK_FRAME = base.mat("Exit | dark graphite extruded aluminium",
                      (0.065, 0.085, 0.084), metallic=0.81, roughness=0.30)
SOFT_STEEL = base.mat("Exit | satin silver hanging rods",
                      (0.44, 0.48, 0.50), metallic=0.74, roughness=0.27)
EDGE_RUBBER = base.mat("Exit | weatherproof gasket",
                      (0.016, 0.025, 0.019), metallic=0.01, roughness=0.79)
TEXT_WHITE = WHITE_ICON

def cube(name, center, size, material, bevel=0):
    obj = base.cube(name, center, size, material, bevel)
    # Blender 4.0's weighted-normals modifier errors on non-Auto-Smooth meshes.
    for m in list(obj.modifiers):
        if m.type == 'WEIGHTED_NORMAL':
            obj.modifiers.remove(m)
    return obj

def bolt(name, x, y, z, radius=0.015):
    base.cylinder(name + " steel fastener", (x,y,z), radius, .018, STEEL)
    base.cylinder(name + " sealing washer", (x,y+.013,z), radius*1.25, .009, GASKET)

def make_a(z, idx, width=1.00):
    """A three-dimensional orange channel letter with a weather seal behind it."""
    base.mesh_text("A", "AMIGOS | A%02d rear weather gasket" % idx,
                   width+0.018, z, base.FONT_SIGN, GASKET, [GASKET],
                   thickness=0.035, center_x=-0.095, forward_y=-0.112)
    a = base.mesh_text("A", "AMIGOS | A%02d orange acrylic and return" % idx,
                       width, z, base.FONT_SIGN, SATIN_ORANGE, [ORANGE],
                       thickness=0.168, center_x=-0.095, forward_y=-0.231)
    a["emissive_face"] = True
    a["construction"] = "Fabricated orange acrylic-faced aluminium channel letter"
    # A small rear stiffening rib, deliberately hidden behind the letter.
    cube("AMIGOS | A%02d rear brace" % idx, (-0.05,-0.065,z),
         (0.66,0.075,0.052), DARK_STEEL, .010)

def make_wall_support(zlevels, height):
    """Hidden support arms connected to a vertical galvanised wall rail."""
    rail_z = sum(zlevels)/len(zlevels)
    cube("AMIGOS | powdercoated vertical mounting rail",
         (0.615,0.081,rail_z), (0.068,0.102,height), DARK_STEEL, .012)
    for i,z in enumerate(zlevels):
        cube("AMIGOS | A%02d outward support arm"%(i+1),
             (0.395,-0.049,z), (0.425,0.073,0.073), STEEL, .011)
        cube("AMIGOS | A%02d stainless gusset"%(i+1),
             (0.565,-0.018,z-.10), (0.046,0.096,0.19), STEEL, .007)
    for i,z in enumerate((rail_z-height*.39, rail_z, rail_z+height*.39)):
        cube("AMIGOS | facade anchor plate %d" % i,
             (0.632,0.161,z), (0.193,0.024,0.162), DARK_STEEL, .010)
        for k,dx in enumerate((-0.056,0.056)):
            bolt("AMIGOS | anchor %d-%d"%(i,k),0.632+dx,0.139,z)

def build_single():
    make_a(0.00, 1)
    make_wall_support([0.00], 1.06)
    return (1.44, 1.14)

def build_triple():
    for i,z in enumerate((1.125, 0.0, -1.125), 1):
        make_a(z,i)
    make_wall_support([1.125, 0.0, -1.125], 3.34)
    return (1.44, 3.40)

def poly(name, points, y, depth, material):
    """An actually extruded, planar pictogram, coords as (x,z), CCW front."""
    n=len(points)
    verts=[(x,y-depth/2,z) for x,z in points]
    verts += [(x,y+depth/2,z) for x,z in points]
    faces=[tuple(range(n)), tuple(range(2*n-1,n-1,-1))]
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,n+j,n+i))
    mesh=bpy.data.meshes.new(name+" mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.materials.append(material)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    base.mark_asset(obj)
    return obj

def strip(name, start, end, thickness, material, y=-.147, depth=.012):
    """Rectangular extruded vector stroke between two planar points."""
    dx=end[0]-start[0]
    dz=end[1]-start[1]
    L=math.hypot(dx,dz)
    if L < 0.000001: raise ValueError("degenerate stroke")
    nx, nz = -dz/L*thickness*.5, dx/L*thickness*.5
    return poly(name,[
        (start[0]+nx,start[1]+nz),
        (start[0]-nx,start[1]-nz),
        (end[0]-nx,end[1]-nz),
        (end[0]+nx,end[1]+nz),
    ],y,depth,material)

def circle(name, x,z,r,material, y=-.149):
    points = [(x+math.cos(2*math.pi*i/20)*r,
               z+math.sin(2*math.pi*i/20)*r)
              for i in range(20)]
    return poly(name,points,y,.013,material)

def exit_pictogram():
    # International emergency exit pictogram, modeled entirely as 3D geometry.
    # Door and fleeing person point toward the EXIT arrow (right).
    strip("EXIT | left side doorway",(-.651,-.136),(-.651,.149),.018,WHITE_ICON)
    strip("EXIT | top doorway",(-.651,.149),(-.542,.149),.018,WHITE_ICON)
    circle("EXIT | running person head",-.469,.099,.035,WHITE_ICON)
    # Angled body is constructed with connected trapezoidal white shapes.
    poly("EXIT | running person torso",[
        (-.489,.054),(-.427,.073),(-.363,-.013),(-.414,-.045),
    ],-.148,.014,WHITE_ICON)
    strip("EXIT | reaching forward arm",(-.434,.027),(-.329,.040),.029,WHITE_ICON)
    strip("EXIT | rear arm",(-.469,.022),(-.567,-.033),.025,WHITE_ICON)
    strip("EXIT | forward shin",(-.393,-.027),(-.303,-.126),.035,WHITE_ICON)
    strip("EXIT | planted leg",(-.417,-.030),(-.532,-.133),.038,WHITE_ICON)
    # White filled right-facing directional arrow beneath EXIT label.
    poly("EXIT | directional right arrow", [
        (-.192,-.114),(-.074,-.114),(-.074,-.152),(.031,-.078),
        (-.074,-.004),(-.074,-.043),(-.192,-.043)
    ],-.149,.016,WHITE_ICON)

def build_exit():
    # Suspended/ceiling-mounted dual-faced aluminium emergency wayfinding light.
    # Front and rear acrylic + deliberately closed opaque 3D housing.
    cube("EXIT | aluminium rectangular lightbox housing",
         (0.0,0.00,0.0), (1.565,.105,.483), DARK_FRAME, .021)
    cube("EXIT | front weatherproof gasket", (0,-.065,0),
         (1.504,.011,.419), EDGE_RUBBER, .005)
    cube("EXIT | green acrylic front diffuser", (0,-.080,0),
         (1.480,.019,.395), GREEN_FACE, .008)
    # Rear green diffuser gives a realistic double-faced object at an angle.
    cube("EXIT | rear weatherproof gasket", (0,.065,0),
         (1.504,.011,.419), EDGE_RUBBER, .005)
    cube("EXIT | green acrylic back diffuser", (0,.081,0),
         (1.480,.019,.395), GREEN_FACE, .008)
    # Crisp fitted bead around face instead of a floating overwide border.
    for sign in (-1,1):
        y = -.101 if sign==-1 else .101
        cube("EXIT | top aluminium bezel %s"%sign, (0,y,.207),
             (1.54,.019,.021), DARK_FRAME, .004)
        cube("EXIT | lower aluminium bezel %s"%sign, (0,y,-.207),
             (1.54,.019,.021), DARK_FRAME, .004)
        for x in (-.752,.752):
            cube("EXIT | short edge bezel %s %.2f"%(sign,x), (x,y,0),
                 (.019,.019,.421), DARK_FRAME, .004)
    exit_pictogram()
    # Information occupies the open right half of the sign.
    base.mesh_text("AUSGANG", "EXIT | bright white German title", .615, .086,
                   base.FONT_SECONDARY, GREEN_EDGE, [WHITE_ICON],
                   thickness=.014, center_x=.308, forward_y=-.147)
    base.mesh_text("EXIT", "EXIT | secondary English title", .294, -.095,
                   base.FONT_SECONDARY, GREEN_EDGE, [WHITE_ICON],
                   thickness=.013, center_x=.390, forward_y=-.146)
    # Two machined stainless support rods and slim ceiling plates.
    for idx,x in enumerate((-.51,.51),1):
        base.cylinder("EXIT | ceiling drop rod %d"%idx,
                      (x,.012,.339), .011,.244,SOFT_STEEL,axis='Z')
        base.cylinder("EXIT | lower rod fitting %d"%idx,
                      (x,.012,.232), .026,.022,DARK_FRAME,axis='Z')
        cube("EXIT | flush ceiling anchor plate %d"%idx,
             (x,.012,.483),(.126,.092,.024), DARK_FRAME,.009)
        for j,dx in enumerate((-.039,.039)):
            base.cylinder("EXIT | ceiling bolt %d.%d"%(idx,j),
                          (x+dx,-.034,.480), .011,.014,STEEL,axis='Y')
    for idx,x in enumerate((-.65,.65),1):
        bolt("EXIT | casing screw %d"%idx,x,-.125,-.20, .009)
    return (1.57,0.55)

def add_preview(name, width, height):
    # CPU Cycles, no OpenGL context needed on a headless GitHub Actions runner.
    wall = base.mat("PREVIEW | neutral plaster",(.23,.245,.255),roughness=.9)
    cube("PREVIEW ONLY | wall",(0,.37,.20),(width+1.3,.12,height+.75),wall,.008)
    bpy.ops.object.camera_add(location=(width*.24,-max(width*2.0,5.4),height*.12+.27))
    cam=bpy.context.object
    cam.name="PREVIEW ONLY | camera"
    cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO'
    cam.data.ortho_scale=max(width+1.3,height*1.38)
    bpy.context.scene.camera=cam
    for i,(loc,power,size) in enumerate([
        ((-width*.6,-3.3,2.4),420,3.0),
        ((width*.8,-1.7,.6),230,1.6)
    ]):
        bpy.ops.object.light_add(type="AREA",location=loc)
        l=bpy.context.object
        l.data.energy=power
        l.data.shape='DISK'
        l.data.size=size
        l.rotation_euler=(Vector((0,0,0))-l.location).to_track_quat('-Z','Y').to_euler()
        l.name="PREVIEW ONLY | studio softbox %d"%i
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=20
    scene.render.resolution_x=1024
    scene.render.resolution_y=700 if height>1.9 else 580
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=os.path.join(PREV,name+'.png')
    scene.render.film_transparent=False
    scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.view_transform='AgX'
    scene.render.image_settings.color_depth='8'
    bpy.ops.render.render(write_still=True)
    print("PREVIEW_RENDERED",scene.render.filepath, flush=True)

def validate_glb(path):
    with open(path,"rb") as f:
        magic,version,total=struct.unpack("<4sII",f.read(12))
        chunk_length,ctype=struct.unpack("<I4s",f.read(8))
        obj=json.loads(f.read(chunk_length))
    actual=os.path.getsize(path)
    assert magic==b"glTF" and version==2
    assert total==actual and ctype==b"JSON", (total, actual, ctype)
    assert len(obj.get("meshes",[]))>=5, ("not enough 3D mesh parts",path)
    assert len(obj.get("materials",[]))>=3, ("missing PBR materials",path)
    assert any("emissiveFactor" in m or "KHR_materials_emissive_strength" in m.get("extensions",{})
               for m in obj["materials"]), "no emissive glTF material"
    assert actual>18000, ("suspicious file size",actual)
    print("VALIDATED",os.path.basename(path),"meshes",len(obj["meshes"]),
          "materials",len(obj["materials"]),"bytes",actual, flush=True)

def main():
    variants=[
        ("AMIGOS_TripleA_Projected",build_triple),
        ("AMIGOS_SingleA_Projected",build_single),
        ("EXIT_AUSGANG_Illuminated",build_exit)
    ]
    for name,create in variants:
        base.reset()
        width,height=create()
        base.export_asset(name)
        validate_glb(os.path.join(OUT,name+'.glb'))
        if os.environ.get("RENDER_PREVIEWS")=="1":
            add_preview(name,width,height)
        # Ensure there are no more than three additions, don't touch old four.
    print("COMPLETE: three new valid assets", flush=True)

if __name__=="__main__":
    main()
