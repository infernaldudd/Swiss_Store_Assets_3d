"""Build ONE realistic filled, crinkled, sealed 90g SCHWEFEL Paprika chips bag.

Game model: physically curved front and back, side gussets, crimped foil seals,
rear adhesive strip, 2K custom UV artwork, roughness, and foil-normal textures.
All textures are packed in both GLB and .blend source, in metres and +Z up.

blender -b -t 2 --python tools/build_schwefel_bag.py
RENDER_PREVIEWS=1 blender -b -t 2 --python tools/build_schwefel_bag.py
"""
import bpy
import os,math,json,struct
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"assets")
SRC=os.path.join(ROOT,"source")
PREV=os.path.join(ROOT,"previews")
TEX=os.path.join(ROOT,"textures","schwefel_paprika")
for p in (OUT,SRC,PREV):os.makedirs(p,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
S=bpy.context.scene
C=bpy.context

def mat(name,color,metallic=.0,roughness=.35,image=None,normal=None,roughmap=None):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Metallic"].default_value=metallic
    p.inputs["Roughness"].default_value=roughness
    if "Coat Weight" in p.inputs:
        p.inputs["Coat Weight"].default_value=.17
        p.inputs["Coat Roughness"].default_value=.32
    elif "Clearcoat" in p.inputs:
        p.inputs["Clearcoat"].default_value=.17
    def node_for(path,noncolor=False):
        filepath=os.path.join(TEX,path)
        assert os.path.isfile(filepath),(path,"missing generator texture")
        img=bpy.data.images.load(filepath,check_existing=True)
        if noncolor:img.colorspace_settings.name="Non-Color"
        img.pack()
        n=m.node_tree.nodes.new("ShaderNodeTexImage")
        n.image=img
        n.interpolation="Linear"
        n.extension="REPEAT"
        return n
    if image:
        n=node_for(image)
        m.node_tree.links.new(n.outputs["Color"],p.inputs["Base Color"])
    if roughmap:
        n=node_for(roughmap,True)
        m.node_tree.links.new(n.outputs["Color"],p.inputs["Roughness"])
    if normal:
        n=node_for(normal,True)
        nm=m.node_tree.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value=.42
        m.node_tree.links.new(n.outputs["Color"],nm.inputs["Color"])
        m.node_tree.links.new(nm.outputs["Normal"],p.inputs["Normal"])
    return m

NORMAL="Foil_MicroWrinkle_Normal.png"
ROUGH="Foil_Roughness.png"
FRONT=mat("Schwefel | original printed paprika front",(.9,.4,.1),
          metallic=.12,roughness=.27,image="Schwefel_Paprika_Front_2K.png",
          roughmap=ROUGH,normal=NORMAL)
BACK=mat("Schwefel | fictional ingredients reverse",(.9,.4,.12),
         metallic=.12,roughness=.29,image="Schwefel_Paprika_Back_2K.png",
         roughmap=ROUGH,normal=NORMAL)
ORANGE=mat("Thermal seam | dark orange plastic",(.83,.29,.035),metallic=.17,roughness=.34)
CREAM=mat("Crimp reflections | copper-gold thin foil",(.77,.37,.09),metallic=.46,roughness=.3)
FOLD=mat("Rear fin-seal | light metallic orange",(.85,.40,.10),metallic=.37,roughness=.36)

BODY_WIDTH=.173
HALF=BODY_WIDTH*.5
Z0=.016
Z1=.255
BAG_TOTAL_HEIGHT=.275

# For a ~90g Swiss packet. Front of model looks toward world -Y.
def coords(u,v,face):
    # u,v 0..1. Continuous front/back membrane, puffed with nitrogen.
    xx=2*u-1
    z=Z0+(Z1-Z0)*v
    # Slight uneven silhouette at the edges, no simple flat cuboid or symmetric pill.
    x=HALF*xx + .0012*math.sin(8.7*v+xx*1.4)*math.sin(math.pi*u) \
               + .00072*math.sin(29*v+3.8*u)*math.sin(math.pi*u)
    env_x=(max(0,1-abs(xx)**3.6))**.64
    env_z=(max(0,math.sin(math.pi*v)))**.49
    puffy=.0123 + .0265*env_x*env_z
    diagonal=math.sin(22.3*u+13.1*v + math.sin(8.2*v+2*u))
    diag2=math.sin(47*u-35*v+3.1*math.cos(v*17))
    foldstrength=.00035+.00115*(abs(xx)**1.8 + abs(2*v-1)**4)
    wrinkle=foldstrength*diagonal+.0007*diag2 + .00045*math.sin(74*v+12*u)
    # Offset the front and back differently to avoid perfect mirror shapes.
    y=face*puffy + face*wrinkle + (0.00048*math.sin(31*v+11*u))
    z+=.00072*math.sin(17*u+5*v)*math.sin(math.pi*v)
    return (x,y,z)

def make_bag_body():
    # Shared manifold shell, with UV per face to avoid reversed artwork.
    nx,nz=32,48
    verts=[]
    for face in (-1,+1):
        for j in range(nz+1):
            for i in range(nx+1):
                verts.append(coords(i/nx,j/nz,face))
    layer=(nx+1)*(nz+1)
    def k(i,j,back=False):return (layer if back else 0)+j*(nx+1)+i
    faces=[];materials=[];uvpolys=[]
    for back in (False,True):
        for j in range(nz):
            for i in range(nx):
                corners=(k(i,j,back),k(i+1,j,back),k(i+1,j+1,back),k(i,j+1,back))
                if back:
                    corners=tuple(reversed(corners))
                faces.append(corners)
                materials.append(1 if back else 0)
                mapping={}
                for vert in corners:
                    local=vert-layer if back else vert
                    vi,ui=divmod(local,nx+1)
                    mapping[vert]=(1-ui/nx if back else ui/nx,vi/nz)
                uvpolys.append(mapping)
    # 4 edge strips close the pouch; seams near the top/bottom remain real.
    for j in range(nz):
        # Left and right material is original side print, continuous UV.
        corners=(k(0,j),k(0,j+1),k(0,j+1,True),k(0,j,True))
        faces.append(corners); materials.append(2)
        uvpolys.append({corners[0]:(0,j/nz),corners[1]:(0,(j+1)/nz),
                        corners[2]:(1,(j+1)/nz),corners[3]:(1,j/nz)})
        corners=(k(nx,j,True),k(nx,j+1,True),k(nx,j+1),k(nx,j))
        faces.append(corners);materials.append(2)
        uvpolys.append({corners[0]:(0,j/nz),corners[1]:(0,(j+1)/nz),
                        corners[2]:(1,(j+1)/nz),corners[3]:(1,j/nz)})
    for j in (0,nz):
        for i in range(nx):
            corners=(k(i,j,True),k(i+1,j,True),k(i+1,j),k(i,j))
            if j==0: corners=tuple(reversed(corners))
            faces.append(corners);materials.append(2)
            uvpolys.append({vert:(i/nx if m%2==0 else (i+1)/nx, 1 if j==nz else 0)
                            for m,vert in enumerate(corners)})
    mesh=bpy.data.meshes.new("closed foil pouch with UV mapped outer shell")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    for m in (FRONT,BACK,ORANGE):
        mesh.materials.append(m)
    uv=mesh.uv_layers.new(name="UV0 | print both faces")
    for pi,p in enumerate(mesh.polygons):
        p.material_index=materials[pi]
        p.use_smooth=(pi<nx*nz*2)
        mapping=uvpolys[pi]
        for li in p.loop_indices:
            vi=mesh.loops[li].vertex_index
            uv.data[li].uv=mapping[vi]
    o=bpy.data.objects.new("Schwefel Paprika | puffed full foil bag",mesh)
    C.collection.objects.link(o)
    o["asset"]=True
    o["material"]="multilayer printed polymer, not rigid box"
    return o

def strip_crimp(top):
    # Real sealed foil lip, front+back surfaces with 11 regular compression ridges.
    z0=Z1-.0011 if top else .000
    z1=.275 if top else Z0+.0011
    nx=36; nz=30
    verts=[]
    for side in (-1,1):
        for j in range(nz+1):
            v=j/nz; z=z0+(z1-z0)*v
            for i in range(nx+1):
                u=i/nx
                x=(u-.5)*.182
                x+=.0007*math.sin(8*u+v*8)
                # Pressed together at seam, thinly corrugated across horizontal band.
                bump=.00045*math.cos(v*math.pi*21)+.00018*math.sin(u*19)
                y=side*(.0026+bump)
                verts.append((x,y,z))
    layer=(nx+1)*(nz+1)
    def ix(i,j,b):return (layer if b else 0)+j*(nx+1)+i
    fs=[];ms=[];maps=[]
    for back in (False,True):
        for j in range(nz):
            for i in range(nx):
                f=(ix(i,j,back),ix(i+1,j,back),ix(i+1,j+1,back),ix(i,j+1,back))
                if back:f=tuple(reversed(f))
                fs.append(f)
                ms.append(2 if j%5!=0 else 3)
                maps.append([(i/nx,j/nz),((i+1)/nx,j/nz),
                             ((i+1)/nx,(j+1)/nz),(i/nx,(j+1)/nz)][::-1] if back else
                            [(i/nx,j/nz),((i+1)/nx,j/nz),((i+1)/nx,(j+1)/nz),(i/nx,(j+1)/nz)])
    # Stitch seam lip boundary. Thin 5 mm folded fin is a proper 3D volume.
    for i in range(nx):
        for j in (0,nz):
            fs.append((ix(i,j,False),ix(i+1,j,False),ix(i+1,j,True),ix(i,j,True)))
            ms.append(2);maps.append([(0,0),(1,0),(1,1),(0,1)])
    for j in range(nz):
        for i in (0,nx):
            fs.append((ix(i,j,False),ix(i,j+1,False),ix(i,j+1,True),ix(i,j,True)))
            ms.append(2);maps.append([(0,0),(1,0),(1,1),(0,1)])
    mesh=bpy.data.meshes.new("welded ribbed crimp %s"%("top" if top else "bottom"))
    mesh.from_pydata(verts,[],fs)
    for m in (FRONT,BACK,ORANGE,CREAM):mesh.materials.append(m)
    mesh.update()
    ob=bpy.data.objects.new("Heat-sealed foil lip | "+("upper" if top else "lower"),mesh)
    C.collection.objects.link(ob)
    ob["asset"]=True
    ob["crimp_pitch_m"]=round((z1-z0)/11,5)
    # UVs deliberately linear; this object uses solid metal and orange colors.
    layer_uv=mesh.uv_layers.new(name="UV0")
    for poly,coords_uv,materialindex in zip(mesh.polygons,maps,ms):
        poly.material_index=materialindex
        for li,xy in zip(poly.loop_indices,coords_uv):
            layer_uv.data[li].uv=xy

def back_fin():
    # Vertical fin seal fixed to the back face, with narrow folded lip and shadow.
    verts=[]
    seg=40
    for j in range(seg+1):
        v=j/seg
        z=Z0+.007+v*(Z1-Z0-.014)
        for i in range(3):
            x=-.0075+i*.007
            u=.5+x/BODY_WIDTH
            _,surface_y,_=coords(u,.03+.94*v,1)
            y=surface_y+.0015 + (.0007 if i==1 else 0)
            verts.append((x,y,z))
    fs=[]
    for j in range(seg):
        for i in range(2):
            a=j*3+i
            fs.append((a,a+1,a+4,a+3))
    mesh=bpy.data.meshes.new("folded back vertical seam")
    mesh.from_pydata(verts,[],fs)
    mesh.materials.append(FOLD)
    uv=mesh.uv_layers.new(name="UV0")
    for p in mesh.polygons:
        p.use_smooth=True
        for idx,li in enumerate(p.loop_indices):
            vert=mesh.loops[li].vertex_index
            row,colm=divmod(vert,3)
            uv.data[li].uv=(colm/2,row/seg)
    mesh.update()
    o=bpy.data.objects.new("Rear centre-seal | genuine raised foil strip",mesh)
    C.collection.objects.link(o)
    o["asset"]=True

def save_source_and_export():
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SRC,"Schwefel_Paprika_90g.blend"),compress=True)
    bpy.ops.object.select_all(action="DESELECT")
    objs=[o for o in S.objects if o.type=="MESH" and o.get("asset")]
    for o in objs:o.select_set(True)
    C.view_layer.objects.active=objs[0]
    p=os.path.join(OUT,"Schwefel_Paprika_90g.glb")
    bpy.ops.export_scene.gltf(filepath=p,export_format="GLB",use_selection=True,
                              export_yup=True,export_materials="EXPORT",export_apply=True,
                              export_draco_mesh_compression_enable=False)
    with open(p,"rb") as f:
        magic,ver,total=struct.unpack("<4sII",f.read(12))
        n,kind=struct.unpack("<I4s",f.read(8))
        data=json.loads(f.read(n))
    assert magic==b"glTF" and ver==2 and total==os.path.getsize(p)
    assert len(data.get("meshes",[]))>=4
    assert len(data.get("materials",[]))>=4
    assert len(data.get("images",[]))>=4, (len(data.get("images",[])),"missing PBR artwork")
    assert os.path.getsize(p)>250000
    print("GLB VALIDATED",os.path.basename(p),
          "meshes",len(data["meshes"]),"materials",len(data["materials"]),
          "embedded_images",len(data["images"]),"bytes",total,flush=True)
    bpy.ops.object.select_all(action="DESELECT")

def preview(name, cam_xyz):
    floor=mat("PREVIEW ONLY | polished supermarket tile",(.28,.29,.30),roughness=.72)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,-.015))
    fl=C.object
    fl.name="PREVIEW ONLY | floor"
    fl.dimensions=(.9,.9,.026)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    fl.data.materials.append(floor)
    S.world.color=(.22,.22,.22)
    for loc,energy,size in [
        ((-.45,-.45,.67),165, .66),
        ((.38,.2,.56),130,.6),
        ((.09,-.22,.6),75,.27)
    ]:
        bpy.ops.object.light_add(type="AREA",location=loc)
        o=C.object;o.name="PREVIEW ONLY | softbox"
        o.data.energy=energy
        o.data.shape="DISK";o.data.size=size
        o.rotation_euler=(Vector((0,0,.15))-o.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.object.camera_add(location=cam_xyz)
    cam=C.object;cam.name="PREVIEW ONLY | camera"
    cam.rotation_euler=(Vector((0,0,.143))-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO";cam.data.ortho_scale=.345
    S.camera=cam
    S.render.engine="CYCLES"
    S.cycles.device="CPU"
    S.cycles.samples=22
    if hasattr(S.cycles,"use_denoising"):S.cycles.use_denoising=False
    if hasattr(C.view_layer.cycles,"use_denoising"):C.view_layer.cycles.use_denoising=False
    S.render.resolution_x=780; S.render.resolution_y=1120; S.render.resolution_percentage=100
    S.render.image_settings.file_format="PNG"
    S.render.filepath=os.path.join(PREV,"Schwefel_Paprika_90g_"+name+".png")
    S.view_settings.view_transform="AgX"
    bpy.ops.render.render(write_still=True)
    print("PREVIEW RENDERED",S.render.filepath,flush=True)
    bpy.data.objects.remove(fl,do_unlink=True)
    bpy.data.objects.remove(cam,do_unlink=True)
    for o in list(S.objects):
        if o.type=="LIGHT":bpy.data.objects.remove(o,do_unlink=True)

def main():
    make_bag_body()
    strip_crimp(True)
    strip_crimp(False)
    back_fin()
    save_source_and_export()
    if os.environ.get("RENDER_PREVIEWS")=="1":
        preview("Front",(.30,-.60,.30))
        preview("Back",(-.24,.66,.31))
    print("COMPLETED SCHWEFEL PAPRIKA 90g single chips packet",flush=True)

if __name__=="__main__":main()
