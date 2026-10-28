"""Rebuild 12 original beverage assets with actual UV-printed cylindrical labels.

Fix: no 3D text object offset from can, bottle or carton. The printed label
is a physically conforming curved mesh with proper 2048x1024 UVs embedded in
each GLB. 96 radial segments on cans, recessed steel lids, double rolled rims,
punched ring-pull and rivet; label is flush to the metal, not floating.
PET gets proper shrink sleeves; cartons get printed front panel.
All units in metres, Blender +Z up, front toward -Y.

Run:
 /usr/bin/python3 tools/generate_drink_labels.py
 blender -b -t 2 --python tools/build_drinks.py
 RENDER_PREVIEWS=1 blender -b -t 2 --python tools/build_drinks.py
"""
import bpy, math, os, struct, json
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"assets","drinks")
ART=os.path.join(ROOT,"textures","drinks")
FIN=os.path.join(ROOT,"textures","surface_finishes")
PREV=os.path.join(ROOT,"previews","drinks")
os.makedirs(OUT,exist_ok=True)
os.makedirs(PREV,exist_ok=True)
ITEMS=[
 ("LOOP Cola","cola","can",(0.59,0.10,0.08),330),
 ("LOOP Cola Zero","cola zero","can",(0.10,0.10,0.12),330),
 ("LOOP Orange","orange","can",(0.97,0.39,0.08),330),
 ("LOOP Lemon","lemon","can",(0.81,0.84,0.24),330),
 ("AMIGOS Ice Tea Peach","peach iced tea","pet",(0.86,0.46,0.19),500),
 ("AMIGOS Ice Tea Lemon","lemon iced tea","pet",(0.66,0.76,0.26),500),
 ("ALPQUELL Still Water","still water","pet",(0.15,0.51,0.69),500),
 ("ALPQUELL Sparkling Water","sparkling","pet",(0.09,0.44,0.69),500),
 ("VOLTIX Energy Original","energy","can",(0.11,0.69,0.66),250),
 ("VOLTIX Energy Berry","berry energy","can",(0.51,0.21,0.59),250),
 ("LOOP Apple Juice","apple juice","carton",(0.72,0.71,0.25),1000),
 ("AMIGOS Orange Juice","orange juice","carton",(0.94,0.43,0.09),1000),
]
SCENE=bpy.context.scene
C=bpy.context

def material(name,c,metal=0,rough=.4,art=None,alpha=1):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*c,alpha)
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*c,1)
    p.inputs["Metallic"].default_value=metal
    p.inputs["Roughness"].default_value=rough
    p.inputs["Alpha"].default_value=alpha
    if alpha<1:m.blend_method="BLEND"
    if art:
        path=os.path.join(ART,art)
        assert os.path.isfile(path),("Missing UV artwork",path)
        im=bpy.data.images.load(path,check_existing=True)
        im.pack()
        tex=m.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image=im
        tex.interpolation="Linear"
        m.node_tree.links.new(tex.outputs["Color"],p.inputs["Base Color"])
    return m

def apply_finish(mat,roughness_map,normal_strength=0.0):
    """Real material-dependent micro roughness—not uniform glossy plastic."""
    bs=mat.node_tree.nodes.get("Principled BSDF")
    def tex(filename):
        path=os.path.join(FIN,filename+".png")
        assert os.path.isfile(path),path
        im=bpy.data.images.load(path,check_existing=True)
        im.colorspace_settings.name="Non-Color"
        im.pack()
        node=mat.node_tree.nodes.new("ShaderNodeTexImage")
        node.image=im
        node.extension="REPEAT"
        return node
    r=tex(roughness_map)
    mat.node_tree.links.new(r.outputs["Color"],bs.inputs["Roughness"])
    if normal_strength>0:
        bump=tex("Soft_Micro_Normal")
        nm=mat.node_tree.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value=normal_strength
        mat.node_tree.links.new(bump.outputs["Color"],nm.inputs["Color"])
        mat.node_tree.links.new(nm.outputs["Normal"],bs.inputs["Normal"])
    return mat

def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

def mesh(name,vertices,faces,mat,uvs=None,smooth=False):
    me=bpy.data.meshes.new(name+" mesh")
    me.from_pydata(vertices,[],faces)
    me.update()
    me.materials.append(mat)
    if uvs is not None:
        assert len(faces)==len(uvs),(name,len(faces),len(uvs))
        layer=me.uv_layers.new(name="Printed brand artwork UV0")
        for poly,texcoords in zip(me.polygons,uvs):
            assert len(poly.loop_indices)==len(texcoords),(name,len(poly.loop_indices))
            for loop_index,coord in zip(poly.loop_indices,texcoords):
                layer.data[loop_index].uv=coord
    ob=bpy.data.objects.new(name,me)
    C.collection.objects.link(ob)
    if smooth:
        for poly in me.polygons:poly.use_smooth=True
    ob["game_asset"]=True
    return ob

def lathe(name,profile,mat,segments=96,uv_v=None):
    v=[];f=[];uv=[]
    for j,(r,z) in enumerate(profile):
        for i in range(segments+1):
            u=i/segments
            a=(u-.75)*math.tau # u=.5 is front-facing (-Y)
            v.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(len(profile)-1):
        v0=j/(len(profile)-1) if uv_v is None else uv_v[j]
        v1=(j+1)/(len(profile)-1) if uv_v is None else uv_v[j+1]
        for i in range(segments):
            k=j*(segments+1)+i
            f.append([k,k+1,k+segments+2,k+segments+1])
            uv.append([(i/segments,v0),((i+1)/segments,v0),
                       ((i+1)/segments,v1),(i/segments,v1)])
    return mesh(name,v,f,mat,uv,True)

def disc(name,r,z,mat,segments=96):
    v=[(0,0,z)]
    for i in range(segments):
        a=i*math.tau/segments
        v.append((r*math.cos(a),r*math.sin(a),z))
    f=[];uv=[]
    for i in range(segments):
        j=(i+1)%segments
        f.append([0,i+1,j+1])
        uv.append([(.5,.5),(.5+.5*math.cos(i*math.tau/segments),.5+.5*math.sin(i*math.tau/segments)),
                   (.5+.5*math.cos(j*math.tau/segments),.5+.5*math.sin(j*math.tau/segments))])
    return mesh(name,v,f,mat,uv)

def ring(name,R,r,z,mat,segments=96,minor=10):
    v=[];faces=[];uv=[]
    for i in range(segments):
        a=i*math.tau/segments
        for j in range(minor):
            b=j*math.tau/minor
            rr=R+r*math.cos(b)
            v.append((rr*math.cos(a),rr*math.sin(a),z+r*math.sin(b)))
    for i in range(segments):
        for j in range(minor):
            ii=(i+1)%segments
            jj=(j+1)%minor
            faces.append([i*minor+j,ii*minor+j,ii*minor+jj,i*minor+jj])
            uv.append([(i/segments,j/minor),((i+1)/segments,j/minor),
                       ((i+1)/segments,(j+1)/minor),(i/segments,(j+1)/minor)])
    return mesh(name,v,faces,mat,uv,True)

def cylinder(name,r,depth,z,mat,segments=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=depth,location=(0,0,z))
    ob=C.object
    ob.name=name
    ob.data.materials.append(mat)
    ob["game_asset"]=True
    return ob

def box(name,pos,dim,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    ob=C.object
    ob.name=name
    ob.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat)
    if bevel:
        mod=ob.modifiers.new("Physical bevel","BEVEL")
        mod.width=bevel
        mod.segments=3
    ob["game_asset"]=True
    return ob

def plane_label(name,w,h,y,z,mat):
    v=[(-w/2,y,z-h/2),(w/2,y,z-h/2),
       (w/2,y,z+h/2),(-w/2,y,z+h/2)]
    return mesh(name,v,[[0,1,2,3]],mat,[[(0,0),(1,0),(1,1),(0,1)]])

def ring_pull(name,top_z,silver,r):
    """Actual pierced aluminium lift tab, horizontal with oval hole."""
    n=32;v=[];f=[];uv=[]
    cx=0;cy=-r*.24
    sx=.010 if r>.03 else .009
    sy=.0077 if r>.03 else .0066
    for level in (0,1):
        for inner in (False,True):
            scale=.49 if inner else 1
            for i in range(n):
                a=i*math.tau/n
                v.append((cx+scale*sx*math.cos(a),cy+scale*sy*math.sin(a),
                          top_z+level*.00085))
    def index(level,inner,i):return level*2*n+(n if inner else 0)+(i%n)
    for i in range(n):
        j=(i+1)%n
        for kind in range(4):
            if kind==0:fi=[index(1,False,i),index(1,False,j),index(1,True,j),index(1,True,i)]
            elif kind==1:fi=[index(0,True,i),index(0,True,j),index(0,False,j),index(0,False,i)]
            elif kind==2:fi=[index(0,False,i),index(0,False,j),index(1,False,j),index(1,False,i)]
            else:fi=[index(1,True,i),index(1,True,j),index(0,True,j),index(0,True,i)]
            f.append(fi)
            uv.append([(0,0),(1,0),(1,1),(0,1)])
    mesh(name+" | pierced tab",v,f,silver,uv)
    cylinder(name+" | hinge rivet",.00225,.0015,top_z+.001,silver,24)

def can(p,label,metal,lid):
    name,flavor,form,color,ml=p
    h=.116 if ml==330 else .134
    r=.0327 if ml==330 else .0267
    # Subtle real-world shoulder roll into ends: cylindrical, round body.
    lathe("CAN | spun aluminium below print",[(r*.88,.003),(r*.94,.004),
          (r,.009),(r,h-.010),(r*.93,h-.004)],metal)
    # Logo/flavour/weight are *in* the curved 2K image, not floating objects.
    lathe("CAN | TRUE CYLINDRICAL UV-PRINTED BRAND INK",
          [(r+.00008,.009),(r+.00008,h-.009)],label,96)
    disc("CAN | recessed machined bottom",r*.89,.0038,metal)
    disc("CAN | stamped aluminium lid",r*.85,h-.0059,lid)
    ring("CAN | bottom double folded seam",r*.93,.00165,.005,metal)
    ring("CAN | rolled top seam",r*.91,.0019,h-.0037,metal)
    ring("CAN | easy-open scored lid outline",r*.65,.00055,h-.00545,metal)
    ring_pull("CAN | ring-pull",h-.0051,lid,r)

def pet(p,label,metal,lid):
    name,flavor,form,color,ml=p
    h=.212;r=.033
    resin=apply_finish(material("PET | clear tinted polymer",(.78,.88,.91),metal=0,rough=.18,alpha=.78),"PET_Bottle_Roughness",.10)
    juice=material("PET | contained beverage",tuple(min(.99,.27+c*.65) for c in color),0,.15)
    lathe("PET | injection stretch blown transparent bottle",[
        (.019,.002),(.027,.004),(.031,.012),(.033,.031),
        (.033,.135),(.030,.155),(.024,.171),(.015,.186),(.014,.194)],resin,96)
    # The coloured fluid is slightly inside the transparent skin.
    lathe("PET | beverage within bottle",[
        (.027,.006),(.031,.015),(.031,.038),(.031,.139),(.029,.149)],juice,72)
    # Conforming shrink-sleeve wraps round the circumference, not 3D text.
    lathe("PET | REAL CURVED UV-PRINTED 2K SHRINK SLEEVE",[
        (.03312,.051),(.03312,.133)],label,96)
    for i in range(6):
        z=.017+i*.005
        ring("PET | tactile lower blow-mould grip",r-.0005,.00045,z,resin,72)
    cap=material("PET | opaque capped closure",(.85,.88,.84),.04,.38)
    cylinder("PET | tamper evident ring",.0157,.006,.191,cap,48)
    cylinder("PET | ribbed injection-moulded cap",.0175,.016,.204,cap,64)
    for i in range(24):
        a=i*math.tau/24
        ob=box("PET | individual cap grip rib",
               (.0175*math.cos(a),.0175*math.sin(a),.204),
               (.0013,.0014,.010),cap,.00025)
        ob.rotation_euler.z=a

def carton(p,label,metal,lid):
    name,flavor,form,color,ml=p
    h=.236;w=.070;depth=.070
    paper=material("CARTON | laminated board",(.82,.79,.68),.01,.67)
    box("CARTON | rounded upright multilayer body",(0,0,.097),
        (w,depth,.188),paper,.0016)
    # The artwork is physically in contact with the front plane, not
    # free-standing 3D font geometry offset several millimetres away.
    plane_label("CARTON | true UV-printed front face",w-.002,.183,-depth/2-.00017,.097,label)
    verts=[(-w/2,-depth/2,.191),(w/2,-depth/2,.191),
           (w/2,depth/2,.191),(-w/2,depth/2,.191),
           (-w/2,0,.228),(w/2,0,.228)]
    faces=[[0,1,5,4],[3,2,5,4],[0,4,3],[1,2,5]]
    mesh("CARTON | folded gable roof with actual slopes",verts,faces,paper)
    box("CARTON | compressed factory heat seal",(0,0,.232),
        (w+.002,.005,.009),paper,.001)
    cap=material("CARTON | screw closure",(.92,.92,.85),.03,.42)
    cylinder("CARTON | pouring spout",.009,.006,.212,cap,36)
    cylinder("CARTON | screw cap",.013,.010,.221,cap,36)

def build(p):
    name,flavor,form,color,ml=p
    ink=material("UV PRINT | "+name,color,.38 if form=="can" else .02,
                 .29 if form=="can" else .57,
                 art=name.replace(" ","_")+"_wrap_2K.png")
    apply_finish(ink,"Glossy_Laminated_Print_Roughness" if form=="can" else ("SemiGloss_Vinyl_Roughness" if form=="pet" else "Matte_Paper_Roughness"),.13 if form=="can" else 0)
    aluminum=apply_finish(material("METAL | brushed aluminium",(.66,.69,.70),.85,.27),"Brushed_Steel_Roughness",.13)
    lid=apply_finish(material("LID | satin silver press",(.74,.76,.76),.72,.34),"Foil_Lid_Roughness",.08)
    if form=="can": can(p,ink,aluminum,lid)
    elif form=="pet":pet(p,ink,aluminum,lid)
    else:carton(p,ink,aluminum,lid)
    assert not any(o.type=="FONT" or
                   any(token in o.name.lower() for token in (
                       "product branding","flavour typography",
                       "volume","front logo","drink type","juice flavour",
                       "carton nominal","product title"))
                   for o in SCENE.objects),name+" still contains floating text"

def validate(path):
    with open(path,"rb") as f:
        magic,version,total=struct.unpack("<4sII",f.read(12))
        n,kind=struct.unpack("<I4s",f.read(8))
        info=json.loads(f.read(n))
    assert magic==b"glTF" and version==2 and kind==b"JSON"
    assert total==os.path.getsize(path)
    assert len(info.get("meshes",[]))>=4
    assert len(info.get("materials",[]))>=3
    assert len(info.get("images",[]))>=1
    assert any("UV-PRINTED" in node.get("name","") or "UV-printed" in node.get("name","")
               for node in info["nodes"])
    assert any("TEXCOORD_0" in prim.get("attributes",{}) for mesh in info["meshes"]
               for prim in mesh["primitives"])
    assert not any("Product branding" in node.get("name","") or
                   "Flavour typography" in node.get("name","") or
                   "Front logo" in node.get("name","")
                   for node in info["nodes"])
    print("VALIDATED UV-WRAPPED BEVERAGE",os.path.basename(path),
          len(info["meshes"]),"meshes",len(info["images"]),"textures",
          total,"bytes",flush=True)

def export(name):
    bpy.ops.object.select_all(action="DESELECT")
    objs=[o for o in SCENE.objects if o.type=="MESH" and o.get("game_asset")]
    assert objs
    for o in objs:o.select_set(True)
    C.view_layer.objects.active=objs[0]
    path=os.path.join(OUT,name.replace(" ","_")+".glb")
    bpy.ops.export_scene.gltf(filepath=path,export_format="GLB",
        use_selection=True,export_yup=True,export_apply=True,
        export_materials="EXPORT",export_draco_mesh_compression_enable=False)
    bpy.ops.object.select_all(action="DESELECT")
    validate(path)

def preview(name):
    """Optional isolated QA render. Shelf backdrop is not in the exported GLB."""
    floor=material("PREVIEW ONLY | light terrazzo",(.43,.46,.47),.05,.66)
    box("PREVIEW ONLY | store shelf",(0,0,-.019),(.5,.5,.028),floor,.002)
    for loc,power,size in [
         ((-.22,-.28,.35),42,.34),
         ((.16,.13,.36),31,.26)]:
        bpy.ops.object.light_add(type="AREA",location=loc)
        obj=C.object;obj.name="PREVIEW ONLY | area light"
        obj.data.energy=power;obj.data.size=size
        obj.rotation_euler=(Vector((0,0,.063))-obj.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.object.camera_add(location=(.16,-.31,.19))
    cam=C.object;cam.name="PREVIEW ONLY | camera"
    cam.rotation_euler=(Vector((0,0,.060))-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO"
    cam.data.ortho_scale=.180
    SCENE.camera=cam
    SCENE.world.color=(.25,.25,.25)
    SCENE.render.engine="CYCLES"
    SCENE.cycles.device="CPU"
    SCENE.cycles.samples=22
    # Ubuntu's Blender package does not include OpenImageDenoiser.
    # Avoid a preview-only crash after the GLB export already passed.
    if hasattr(SCENE.cycles,"use_denoising"):
        SCENE.cycles.use_denoising=False
    if hasattr(C.view_layer.cycles,"use_denoising"):
        C.view_layer.cycles.use_denoising=False
    SCENE.render.resolution_x=800
    SCENE.render.resolution_y=950
    SCENE.render.resolution_percentage=100
    SCENE.render.image_settings.file_format="PNG"
    SCENE.render.filepath=os.path.join(PREV,name.replace(" ","_")+"_Curved_Labels.png")
    SCENE.view_settings.view_transform="AgX"
    bpy.ops.render.render(write_still=True)
    print("RENDERED DRINK",SCENE.render.filepath,flush=True)

def main():
    for i,p in enumerate(ITEMS):
        clear()
        build(p)
        export(p[0])
        if os.environ.get("RENDER_PREVIEWS")=="1" and p[0] in (
             "VOLTIX Energy Berry","VOLTIX Energy Original","LOOP Cola",
             "AMIGOS Ice Tea Peach"):
            preview(p[0])
        print("DRINK DONE",i+1,"/",len(ITEMS),p[0],flush=True)
    assert len([x for x in os.listdir(OUT) if x.endswith(".glb")])==12
    print("SUCCESS: 12 textured, mechanically shaped drinks, no floating text",flush=True)

if __name__=="__main__":main()
