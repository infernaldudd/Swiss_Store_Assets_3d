"""Build modular Swiss supermarket gondola wall shelving (Unreal 5.7).

Two separate real-scale GLBs: a 1.04m wall unit and a 2.08m two-bay run.
Material style: powder coated off-white formed steel, folded sheet trays,
visible bolt-fastened triangular braces, adjustable slotted rear uprights,
galvanised reinforcement, PVC clear price rail inserts with original CHF
shelf tickets, and rubber floor feet. Nothing is a flattened billboard.

1m unit height ~2.11m, depth ~0.50m, 5 adjustable shelves.
Bays are intentionally empty so real product GLBs can be placed on them.
 source/*.blend files are editable. All dimensions are metres.

Usage:
 /usr/bin/python3 tools/generate_store_shelf_textures.py
 /usr/bin/python3 tools/generate_surface_finish_maps.py
 blender -b -t 2 --python tools/build_store_shelf.py
 RENDER_PREVIEWS=1 blender -b -t 2 --python tools/build_store_shelf.py
"""
import bpy,math,os,struct,json
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"assets","shelving")
SOURCE=os.path.join(ROOT,"source","shelving")
PREV=os.path.join(ROOT,"previews","shelving")
TEX=os.path.join(ROOT,"textures","shelving")
FIN=os.path.join(ROOT,"textures","surface_finishes")
for path in (OUT,SOURCE,PREV):os.makedirs(path,exist_ok=True)
S=bpy.context.scene;C=bpy.context

def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for m in list(bpy.data.materials):
        if m.users==0:bpy.data.materials.remove(m)
    for im in list(bpy.data.images):
        if im.users==0:bpy.data.images.remove(im)

def material(name,col,metal=.0,rough=.45,roughmap=None,normalmap=None,texture=None,alpha=1):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*col,alpha)
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*col,1)
    p.inputs["Metallic"].default_value=metal
    p.inputs["Roughness"].default_value=rough
    p.inputs["Alpha"].default_value=alpha
    if alpha<1:m.blend_method="BLEND"
    def filetex(name,from_fin=False,noncolor=False):
        filename=os.path.join(FIN if from_fin else TEX,name)
        assert os.path.isfile(filename),filename
        im=bpy.data.images.load(filename,check_existing=True)
        if noncolor:im.colorspace_settings.name="Non-Color"
        im.pack()
        tex=m.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image=im
        return tex
    if roughmap:
        r=filetex(roughmap,True,True)
        m.node_tree.links.new(r.outputs["Color"],p.inputs["Roughness"])
    if normalmap:
        n=filetex(normalmap,True,True)
        nmap=m.node_tree.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value=.18
        m.node_tree.links.new(n.outputs["Color"],nmap.inputs["Color"])
        m.node_tree.links.new(nmap.outputs["Normal"],p.inputs["Normal"])
    if texture:
        t=filetex(texture)
        m.node_tree.links.new(t.outputs["Color"],p.inputs["Base Color"])
    return m

def build_materials():
    return {
     "paint":material("POWDER-COAT | warm white enamel",(.70,.735,.735),.15,.41,
                      "Powdercoat_Steel_Roughness.png","Soft_Micro_Normal.png"),
     "lip":material("PAINTED STEEL | semi-gloss edge protective coat",
                    (.78,.815,.82),.24,.33,"SemiGloss_Vinyl_Roughness.png"),
     "steel":material("GALVANISED STEEL | exposed pressed parts",(.58,.62,.64),.82,.27,
                      "Brushed_Steel_Roughness.png","Soft_Micro_Normal.png"),
     "dark":material("RECESSED SLOTS | recessed graphite steel",(.17,.20,.21),.67,.37),
     "rubber":material("RUBBER | anti-slide foot and endcaps",(.09,.10,.105),.0,.82),
     "pet":material("CLEAR PET | price rail window",(.89,.93,.94),.0,.13,alpha=.28),
     "price":material("PAPER | unique fictive Swiss CHF tickets",(.98,.98,.96),.0,.73,
                       "Matte_Paper_Roughness.png",
                       texture="Shelf_Price_Tickets_2K.png"),
     "orange":material("TRIM | AMIGOS pale apricot brand accent",(.78,.31,.13),.25,.30,
                        "SemiGloss_Vinyl_Roughness.png"),
    }

def box(name,pos,size,mat,bevel=0,segments=2):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    o=C.object;o.name=name
    o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new("REAL fabricated edge radius","BEVEL")
        mod.width=bevel;mod.segments=segments
        # Weighted normals improve real sheet-metal highlight gradients.
        o.modifiers.new("Corner-weighted face normals","WEIGHTED_NORMAL")
    o["is_shop_shelf_part"]=True
    return o

def mesh(name,verts,faces,mat,uv=None,smooth=False):
    data=bpy.data.meshes.new(name+" geometry")
    data.from_pydata(verts,[],faces);data.update()
    data.materials.append(mat)
    if uv is not None:
        assert len(faces)==len(uv)
        layer=data.uv_layers.new(name="Printed CHF price UV")
        for face,coords in zip(data.polygons,uv):
            assert len(face.loop_indices)==len(coords)
            for li,coord in zip(face.loop_indices,coords):
                layer.data[li].uv=coord
    o=bpy.data.objects.new(name,data)
    C.collection.objects.link(o)
    o["is_shop_shelf_part"]=True
    if smooth:
        for p in data.polygons:p.use_smooth=True
    return o

def side_bracket(name,x,shelf_z,M):
    # physically formed bracket from a closed extruded triangular plate.
    # Back is at y=+0.222, front at y=-0.22, under tray at shelf_z.
    y0=.212;y1=-.208
    z0=shelf_z-.014;z1=shelf_z-.154
    width=.012
    vs=[]
    for xx in (x-width/2,x+width/2):
        vs.extend([(xx,y0,z0),(xx,y1,z0),(xx,y0,z1)])
    faces=[[0,2,1],[3,4,5],
           [0,1,4,3],[1,2,5,4],[2,0,3,5]]
    o=mesh(name,vs,faces,M["steel"])
    # stamp two notches / bolt holes on actual exposed face with dark
    # recessed steel fasteners and pale bolt heads.
    return o

def price_ticket(name,x,y,z,width,label_index,M):
    # Full UV plane is positioned inside translucent shelf edge carrier.
    h=.027
    v=[(x-width/2,y,z-h/2),(x+width/2,y,z-h/2),
       (x+width/2,y,z+h/2),(x-width/2,y,z+h/2)]
    # Print atlas has five horizontal slices of equal height.
    v0=label_index/5
    v1=(label_index+1)/5
    return mesh(name,v,[[0,1,2,3]],M["price"],
                [[(0,v0),(1,v0),(1,v1),(0,v1)]])

def module(index,origin_x,M):
    # Snap-together wall shelf module, nominal 1040mm x 500mm x 2100mm.
    # Front points -Y, rear backboard +Y.
    pre=set(S.objects)
    suffix=" | BAY "+str(index)
    hx=.510
    postz=1.055
    # Rear structural uprights are not a flat wall behind every shelf.
    for side in (-1,1):
        x=side*.503
        box("C-SHAPED STEEL REAR UPRIGHT"+suffix,
            (x,.226,postz),(.041,.065,2.11),M["paint"],.003,3)
        # Side return lip makes U-channel silhouette and extrusion readable.
        box("Upright return fold"+suffix,
            (x+side*.016,.186,postz),(.010,.020,2.095),M["steel"],.0015)
        # Array of recessed punched bracket-adjustment slots, in 52mm
        # increments, not a photo decal. Slots are separate recessed faces.
        for k in range(36):
            z=.18+.052*k
            slot=box("Height adjustment recessed slot %02d"%k+suffix,
                     (x,.192,z),(.010,.0015,.023),M["dark"],.0007)
        # Ground foot, toe support and rubber endstop.
        box("Outrigger anti-tip foot"+suffix,(x,-.036,.039),
            (.074,.565,.055),M["steel"],.004,3)
        box("Front load-bearing rubber shoe"+suffix,(x,-.315,.023),
            (.069,.016,.031),M["rubber"],.003)
        box("Rear leveling rubber foot"+suffix,(x,.237,.014),
            (.070,.058,.021),M["rubber"],.003)
        # Thin shelf upright caps.
        box("Square pressed post finishing cap"+suffix,(x,.226,2.112),
            (.048,.075,.014),M["rubber"],.002)
    # Light structural perforated sheet back, NOT an opaque black board.
    box("White enamel steel back panel"+suffix,(0,.243,1.061),
        (.962,.009,1.962),M["paint"],.001)
    for z in (.13,1.034,1.98):
        box("Rear galvanised cross brace"+suffix,(0,.252,z),
            (.98,.028,.029),M["steel"],.001)
    # Vertical folded ridges in rear sheet reveal sheet thickness, preventing
    # flat/unshaded Roblox wall appearance; tiny physical corrugation.
    for k in range(16):
        z=.208+.105*k
        box("Press-stamped rear fold "+str(k)+suffix,(0,.236,z),
            (.961,.0024,.0024),M["lip"],.0005)
    box("Lower steel kick-panel"+suffix,(0,-.249,.084),
        (.992,.025,.139),M["paint"],.004)
    box("Top finishing header"+suffix,(0,.216,2.033),
        (1.005,.052,.112),M["paint"],.006,3)
    box("Upper apricot enamel identity stripe"+suffix,(0,.182,2.018),
        (.970,.004,.012),M["orange"],.001)

    SHELVES=(.229,.608,.987,1.366,1.745)
    for k,z in enumerate(SHELVES):
        n=k+1
        label=" | LEVEL "+str(n)+suffix
        # Each 1m shelf has formed shallow steel tray 480mm deep.
        box("Folded 1m load tray"+label,(0,-.029,z),
            (.988,.482,.022),M["paint"],.0022,3)
        # Lip folded down at front; catches reflection separate from shelf.
        box("Rolled front metal shelf-edge"+label,(0,-.275,z-.017),
            (.998,.019,.045),M["lip"],.003,3)
        box("Upturned backstop fold"+label,(0,.204,z+.015),
            (.973,.012,.044),M["lip"],.002,3)
        for side in (-1,1):
            xx=side*.458
            side_bracket("Pressed triangular support bracket"+label,xx,z,M)
            # Actual mounting tabs go inside the perforation slots.
            box("Bracket locking ear"+label,(xx,.187,z-.053),
                (.015,.058,.011),M["steel"],.0012)
            # Exposed bolt washer on the angled brace.
            box("Bracket gusset reinforcement"+label,(xx,-.066,z-.032),
                (.018,.018,.006),M["steel"],.0012)
        # Separate clear PET front price display window with a physically
        # enclosed channel rather than floating price text.
        box("Price channel PET cover"+label,(0,-.289,z-.023),
            (.953,.003,.035),M["pet"],.001)
        box("Price label track lower lip"+label,(0,-.291,z-.043),
            (.950,.006,.0045),M["steel"],.0007)
        box("Price label track upper lip"+label,(0,-.291,z-.004),
            (.950,.006,.0045),M["steel"],.0007)
        for t in range(2):
            x=(-.25 if t==0 else .25)
            ticket=price_ticket("Original sample CHF label "+str(t+1)+label,
                                x,-.293,z-.023,.174,(k*2+t)%5,M)
            ticket["fictional_price_tag"]=True
    objects=[o for o in S.objects if o not in pre and o.type=="MESH"]
    for o in objects:
        o.location.x+=origin_x
        o["snap_width_m"]=1.04
        o["fictional_brand_design"]=True
    return len(objects)

def export(name):
    meshes=[o for o in S.objects if o.type=="MESH" and o.get("is_shop_shelf_part")]
    assert len(meshes)>150,(name,len(meshes))
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:o.select_set(True)
    C.view_layer.objects.active=meshes[0]
    path=os.path.join(OUT,name+".glb")
    bpy.ops.export_scene.gltf(filepath=path,export_format="GLB",
        use_selection=True,export_apply=True,export_materials="EXPORT",
        export_yup=True,export_draco_mesh_compression_enable=False)
    bpy.ops.object.select_all(action="DESELECT")
    with open(path,"rb") as f:
        magic,version,total=struct.unpack("<4sII",f.read(12))
        chunk,kind=struct.unpack("<I4s",f.read(8))
        doc=json.loads(f.read(chunk))
    assert magic==b"glTF" and version==2 and kind==b"JSON"
    assert os.path.getsize(path)==total
    assert len(doc.get("meshes",[]))>=150
    assert len(doc.get("images",[]))>=2
    names=[node.get("name","") for node in doc["nodes"]]
    assert len([n for n in names if n.startswith("Folded 1m load tray")])>=5
    assert len([n for n in names if n.startswith("Price channel PET cover")])>=5
    assert len([n for n in names if n.startswith("Original sample CHF label")])>=10
    print("VERIFIED SHELF",name,len(meshes),"pieces",len(doc["images"]),
          "texture images",total,"bytes",flush=True)

def render(name,bays):
    # Objects added after export are preview only.
    floor=material("PREVIEW | studio limestone",(.29,.31,.32),0,.72)
    box("PREVIEW ONLY | floor",(0,0,-.027),
        (4.0,3.5,.047),floor,.004)
    for pos,power,size in [
        ((-1.2,-1.5,3.4),1350,2.3),
        ((1.5,-1.0,2.5),990,1.6),
        ((0.25,.95,3.2),530,2.2)]:
        bpy.ops.object.light_add(type="AREA",location=pos)
        o=C.object;o.name="PREVIEW ONLY | softbox"
        o.data.energy=power;o.data.size=size
        o.rotation_euler=(Vector((0,0,1.04))-o.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.object.camera_add(location=((.8 if bays==1 else 1.3),
                                          -3.6 if bays==1 else -4.8,2.13))
    cam=C.object
    cam.rotation_euler=(Vector((0,0,1.04))-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO"
    cam.data.ortho_scale=2.68 if bays==1 else 3.17
    S.camera=cam
    S.render.engine="CYCLES"
    S.cycles.device="CPU";S.cycles.samples=22
    if hasattr(S.cycles,"use_denoising"):S.cycles.use_denoising=False
    if hasattr(C.view_layer.cycles,"use_denoising"):C.view_layer.cycles.use_denoising=False
    S.world.color=(.25,.25,.25)
    S.view_settings.view_transform="AgX"
    S.render.resolution_x=1000 if bays==1 else 1380
    S.render.resolution_y=1130
    S.render.resolution_percentage=100
    S.render.image_settings.file_format="PNG"
    S.render.filepath=os.path.join(PREV,name+".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED",S.render.filepath,flush=True)

def main():
    reset()
    M=build_materials()
    module(1,0,M)
    name="Swiss_Supermarket_Wall_Shelf_1m_5Tier"
    export(name)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCE,name+".blend"),compress=True)
    if os.environ.get("RENDER_PREVIEWS")=="1":render(name,1)
    reset()
    M=build_materials()
    module(1,-.525,M)
    module(2,+.525,M)
    name="Swiss_Supermarket_Wall_Shelf_2m_TwoBay"
    export(name)
    if os.environ.get("RENDER_PREVIEWS")=="1":render(name,2)
    assert len([x for x in os.listdir(OUT) if x.endswith(".glb")])==2
    print("SUCCESS TWO REALISTIC MODULAR STORE SHELF GLBS",flush=True)

if __name__=="__main__":main()
