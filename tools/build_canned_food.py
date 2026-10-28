"""Build 18 closed Swiss-style canned-food products + two opened hero props.

Output: 20 separate textured GLB files (metres, Z-up in Blender).
Models feature pressed steel bodies, double-seamed rolled rims, recessed
embossed lids, easy-open scored tops with attached ring-pulls when applicable,
paper wrap with original 2K UVs, material microdetail, and optional actual
3D contents. Open heroes: ravioli and sweetcorn.

Usage: blender -b -t 2 --python tools/build_canned_food.py
       RENDER_PREVIEWS=1 blender -b -t 2 --python tools/build_canned_food.py
"""
import bpy, math, os, json, struct, random
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
TEX=os.path.join(ROOT,"textures","canned_food")
OUT=os.path.join(ROOT,"assets","canned_food")
PREV=os.path.join(ROOT,"previews","canned_food")
SOURCE=os.path.join(ROOT,"source","canned_food")
for f in (OUT,PREV,SOURCE):os.makedirs(f,exist_ok=True)
DOC=json.load(open(os.path.join(ROOT,"catalog","canned_food.json"),encoding="utf8"))
PRODUCTS=DOC["items"]
SCENE=bpy.context.scene
C=bpy.context

def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for im in list(bpy.data.images):
        if im.users==0:bpy.data.images.remove(im)
    for ma in list(bpy.data.materials):
        if ma.users==0:bpy.data.materials.remove(ma)

def mat(name,color=(.7,.7,.7),metal=0,rough=.5,texture=None,steel=False,paper=False):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    node=m.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value=(*color,1)
    node.inputs["Roughness"].default_value=rough
    node.inputs["Metallic"].default_value=metal
    def image(file,noncolor=False):
        path=os.path.join(TEX,file)
        assert os.path.isfile(path),path
        im=bpy.data.images.load(path,check_existing=True)
        if noncolor:im.colorspace_settings.name="Non-Color"
        im.pack()
        n=m.node_tree.nodes.new("ShaderNodeTexImage")
        n.image=im
        n.interpolation="Linear"
        return n
    if texture:
        tex=image(texture)
        m.node_tree.links.new(tex.outputs["Color"],node.inputs["Base Color"])
    if steel or paper:
        if steel:
            n=image("_Shared_Fine_Metal_Normal.png",True)
            nm=m.node_tree.nodes.new("ShaderNodeNormalMap")
            nm.inputs["Strength"].default_value=.35
            m.node_tree.links.new(n.outputs["Color"],nm.inputs["Color"])
            m.node_tree.links.new(nm.outputs["Normal"],node.inputs["Normal"])
        r=image("_Shared_Steel_Roughness.png" if steel else
                "_Shared_Label_Paper_Roughness.png",True)
        m.node_tree.links.new(r.outputs["Color"],node.inputs["Roughness"])
    return m

def materials(product):
    rgb=tuple(int(product["color"][i:i+2],16)/255 for i in (1,3,5))
    return {
      "label":mat("2K PAPER | "+product["id"],rgb,rough=.69,
                  texture=product["id"]+"_wrap_2K.png",paper=True),
      "tin":mat("TINPLATE | spun brushed steel",(.56,.60,.61),metal=.82,rough=.25,steel=True),
      "lid":mat("TINPLATE | pale aluminium face",(.68,.72,.71),metal=.78,rough=.26,steel=True),
      "seam":mat("METAL | double rolled seams",(.50,.54,.55),metal=.85,rough=.29),
      "score":mat("METAL | scored easy-open groove",(.31,.34,.35),metal=.65,rough=.42),
      "sauce":mat("FOOD | chunky tomato sauce",(.57,.125,.065),rough=.52),
      "pasta":mat("FOOD | soft ravioli dough",(.80,.54,.24),rough=.7),
      "corn":mat("FOOD | sweetcorn kernels",(.92,.69,.14),rough=.48),
      "herb":mat("FOOD | basil",(.10,.35,.11),rough=.62)
    }

def dims(p):
    if p["size"]=="tuna":return .042,.043,.0438
    if p["size"]=="large":return .143,.049,.050
    return .113,.0365,.0373

def new_mesh(name,verts,faces,mat,uvfaces=None):
    me=bpy.data.meshes.new(name+" | geometry")
    me.from_pydata(verts,[],faces)
    me.update()
    me.materials.append(mat)
    if uvfaces is not None:
        assert len(uvfaces)==len(faces),(name,len(uvfaces),len(faces))
        uv=me.uv_layers.new(name="Original label UV")
        for poly,coords in zip(me.polygons,uvfaces):
            assert len(coords)==len(poly.loop_indices)
            for li,point in zip(poly.loop_indices,coords):
                uv.data[li].uv=point
    o=bpy.data.objects.new(name,me)
    C.collection.objects.link(o)
    o["game_asset"]=True
    return o

def turned(name,profile,material,segments=64,print_label=False):
    verts=[];faces=[];uv=[]
    for j,(radius,z) in enumerate(profile):
        for k in range(segments+1):
            u=k/segments
            angle=(u-.75)*math.tau
            delta=.00012*math.sin(k*1.2+j*3.0) if print_label else 0
            r=radius+delta
            verts.append((r*math.cos(angle),r*math.sin(angle),z))
    for j in range(len(profile)-1):
        for k in range(segments):
            a=j*(segments+1)+k
            faces.append((a,a+1,a+segments+2,a+segments+1))
            uv.append([(k/segments,j/(len(profile)-1)),
                       ((k+1)/segments,j/(len(profile)-1)),
                       ((k+1)/segments,(j+1)/(len(profile)-1)),
                       (k/segments,(j+1)/(len(profile)-1))])
    obj=new_mesh(name,verts,faces,material,uv)
    for p in obj.data.polygons:p.use_smooth=True
    return obj

def ring(name,major,minor,z,material,n=64,m=10,flatten=1):
    verts=[];faces=[];uv=[]
    for k in range(n):
        t=k*math.tau/n
        for j in range(m):
            a=j*math.tau/m
            r=major+minor*math.cos(a)
            verts.append((r*math.cos(t),r*math.sin(t),
                          z+minor*math.sin(a)*flatten))
    for k in range(n):
        for j in range(m):
            k1=(k+1)%n;j1=(j+1)%m
            faces.append((k*m+j,k1*m+j,k1*m+j1,k*m+j1))
            uv.append([(k/n,j/m),((k+1)/n,j/m),((k+1)/n,(j+1)/m),(k/n,(j+1)/m)])
    o=new_mesh(name,verts,faces,material,uv)
    for p in o.data.polygons:p.use_smooth=True
    return o

def disc(name,r,z,material,n=64,up=True):
    verts=[(0,0,z)]
    for k in range(n):
        a=k*math.tau/n
        verts.append((r*math.cos(a),r*math.sin(a),z))
    faces=[];uv=[]
    for k in range(n):
        j=(k+1)%n
        face=[0,k+1,j+1]
        v=[(.5,.5),(.5+.5*math.cos(k*math.tau/n),.5+.5*math.sin(k*math.tau/n)),
           (.5+.5*math.cos(j*math.tau/n),.5+.5*math.sin(j*math.tau/n))]
        if not up:face.reverse();v.reverse()
        faces.append(face);uv.append(v)
    o=new_mesh(name,verts,faces,material,uv)
    return o

def cylinder(name,r,depth,z,material,n=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=depth,location=(0,0,z))
    o=C.object;o.name=name
    o.data.materials.append(material)
    o["game_asset"]=True
    return o

def metal_shell(p,m,hero):
    h,r,_=dims(p)
    # Rolled tinplate: slightly recessed sidewall, two shoulder tapers.
    turned("TIN | stamped steel structural body",
           [(r-.006,.003),(r-.002,.004),(r,.007),(r,.013),
            (r,h-.012),(r-.002,h-.007)],m["tin"])
    # Separate micron-spaced paper-printed wall, with overlap at back (u~0).
    turned("PRINT | original 2K UV paper wrap",
           [(r+.00055,.016),(r+.00055,h-.016)],m["label"],64,True)
    # Small glued vertical back overlap; positioned behind front at +Y.
    verts=[(-.005,r+.00062,.017),(.002,r+.00062,.017),
           (.002,r+.00062,h-.017),(-.005,r+.00062,h-.017)]
    new_mesh("PAPER | overlapping rear label seam",verts,[[0,1,2,3]],m["label"],
             [[(.002,0),(.016,0),(.016,1),(.002,1)]])
    ring("DOUBLE SEAM | bottom folded edge",r-.0015,.0025,.0055,m["seam"])
    ring("DOUBLE SEAM | top folded edge",r-.0016,.0025,h-.006,m["seam"])
    ring("SHOULDER | lower pressed steel groove",r-.0012,.00075,.014,m["tin"])
    ring("SHOULDER | upper pressed steel groove",r-.0012,.00075,h-.013,m["tin"])
    # Discs are real geometry; bottom has a shallow punched-in base.
    disc("BOTTOM | inset concave base plate",r-.005,.0033,m["tin"],64,False)
    ring("BOTTOM | foot ring",r-.006,.0014,.003,m["seam"])
    if not hero:
        disc("LID | recessed closed disc",r-.0045,h-.007,m["lid"])
        ring("LID | circular etched scoring",r*.76,.00035,h-.0066,m["score"])
        ring("LID | inner punched shoulder",r-.006,.0005,h-.008,m["seam"])
        if p["opening"]=="easy":
            tab(r,h,m)
        else:
            # Classic tin opener lids: pressed circular reinforcing channels.
            ring("CLASSIC LID | concentric pressing",r*.47,.00065,h-.0064,m["seam"])
            ring("CLASSIC LID | inset press marking",r*.23,.00043,h-.0063,m["seam"])
    else:
        ring("OPEN LID | torn inner score outline",r*.76,.0005,h-.0066,m["score"])
        ring("OPEN TOP | inner lip",r-.006,.0006,h-.009,m["seam"])

def tab(r,h,m):
    z=h-.0054
    # Horizontal aluminium ring-pull near the front, an actual hollow oval
    # with inner cutout rather than a solid disk posing as a ring.
    cx,cy=0,-r*.35
    N=32
    verts=[];faces=[];uv=[]
    a,b=.0120,.0086
    for height in (z,z+.00075):
        for which in (0,1):
            for k in range(N):
                t=math.tau*k/N
                radius=1.0 if which==0 else .58
                verts.append((cx+a*radius*math.cos(t),
                              cy+b*radius*math.sin(t),height))
    def idx(layer,which,k):return layer*2*N+which*N+(k%N)
    for k in range(N):
        j=(k+1)%N
        for side in ("top","outer","inner"):
            if side=="top":
                f=[idx(1,0,k),idx(1,0,j),idx(1,1,j),idx(1,1,k)]
            elif side=="outer":
                f=[idx(0,0,k),idx(0,0,j),idx(1,0,j),idx(1,0,k)]
            else:
                f=[idx(1,1,k),idx(1,1,j),idx(0,1,j),idx(0,1,k)]
            faces.append(f)
            uv.append([(k/N,0),(j/N,0),(j/N,1),(k/N,1)])
    new_mesh("EASY OPEN | genuine hollow punched ring-pull",verts,faces,m["lid"],uv)
    # Stamped hinge strip attaches the ring to the rivet.
    strap=[(-.004,cy+b*.38,z+.0002),(.004,cy+b*.38,z+.0002),
           (.004,-r*.013,z+.0007),(-.004,-r*.013,z+.0007)]
    new_mesh("RING-PULL | bending strap",strap,[[0,1,2,3]],m["lid"],
             [[(0,0),(1,0),(1,1),(0,1)]])
    cylinder("RING-PULL | actual hinge rivet",.0023,.0015,z+.0014,m["seam"],16)

def food_sauce(r,h,m,kind):
    # Fill is below the actual rim; a slightly irregular liquid/food surface.
    radius=r*.87
    n=64
    height=h-.0103
    verts=[(0,0,height)]
    for k in range(n):
        a=k*math.tau/n
        verts.append((radius*math.cos(a),radius*math.sin(a),
                      height+.00045*math.sin(8*a)))
    faces=[[0,k+1,(k+1)%n+1] for k in range(n)]
    uv=[[(.5,.5),(.5+.5*math.cos(k*math.tau/n),.5+.5*math.sin(k*math.tau/n)),
        (.5+.5*math.cos(((k+1)%n)*math.tau/n),
         .5+.5*math.sin(((k+1)%n)*math.tau/n))] for k in range(n)]
    new_mesh("OPEN | actual food surface",verts,faces,
             m["sauce"] if kind=="ravioli" else m["corn"],uv)
    return height

def ellipsoids(name,centres,scale,material):
    # Many small garnish kernels consolidated into ONE draw-call-friendly mesh.
    verts=[];faces=[];uv=[]
    lat=6;lon=10
    for index,center in enumerate(centres):
        ox,oy,oz=center
        sx,sy,sz=scale[index] if isinstance(scale,list) else scale
        st=len(verts)
        for j in range(lat+1):
            a=math.pi*j/lat
            for k in range(lon+1):
                b=k*math.tau/lon
                verts.append((ox+sx*math.sin(a)*math.cos(b),
                              oy+sy*math.sin(a)*math.sin(b),
                              oz+sz*math.cos(a)))
        for j in range(lat):
            for k in range(lon):
                i=st+j*(lon+1)+k
                faces.append([i,i+1,i+lon+2,i+lon+1])
                uv.append([(k/lon,j/lat),((k+1)/lon,j/lat),
                           ((k+1)/lon,(j+1)/lat),(k/lon,(j+1)/lat)])
    o=new_mesh(name,verts,faces,material,uv)
    for p in o.data.polygons:p.use_smooth=True

def hero_food(p,m):
    h,r,_=dims(p)
    z=food_sauce(r,h,m,p["food"])
    rr=random.Random(2468 if p["food"]=="ravioli" else 6281)
    if p["food"]=="ravioli":
        # Distinct filled pillow shapes with pinched, subtly beveled edges.
        for i in range(9):
            a=rr.random()*math.tau
            rad=math.sqrt(rr.random())*r*.55
            x=rad*math.cos(a);y=rad*math.sin(a)
            bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z+.0048))
            o=C.object;o.name="RAVIOLI | hand-pinched pasta pillow"
            o.dimensions=(.017,.014,.006)
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
            o.rotation_euler.z=rr.random()*math.tau
            o.data.materials.append(m["pasta"]);o["game_asset"]=True
            bev=o.modifiers.new("Pasta rounded edge","BEVEL")
            bev.width=.0025;bev.segments=3
        herb=[(rr.uniform(-r*.55,r*.55),rr.uniform(-r*.5,r*.5),z+.008)
              for i in range(19)]
        ellipsoids("RAVIOLI | real 3D basil topping",herb,(.003,.0017,.0008),m["herb"])
    else:
        pts=[];scales=[]
        for i in range(185):
            a=rr.uniform(0,math.tau)
            dist=math.sqrt(rr.random())*r*.67
            x=dist*math.cos(a);y=dist*math.sin(a)
            zval=z+.002+rr.random()*.009
            pts.append((x,y,zval))
            scales.append((rr.uniform(.0013,.0023),
                           rr.uniform(.0020,.0030),
                           rr.uniform(.0015,.0021)))
        ellipsoids("CORN | 185 separate actual 3D kernels, merged for draw calls",
                   pts,scales,m["corn"])
        leaves=[(rr.uniform(-r*.62,r*.62),rr.uniform(-r*.62,r*.62),z+.009)
                for i in range(14)]
        ellipsoids("CORN | scattered green herbs",leaves,(.003,.0011,.0006),m["herb"])

def peeled_hero_lid(p,m):
    h,r,_=dims(p)
    # Half-circle peeled back from centre, retaining a metal attachment edge.
    radial=12;segments=40
    verts=[];faces=[];uv=[]
    radius=r*.76
    for i in range(radial+1):
        rad=i/radial*radius
        for k in range(segments+1):
            a=k/segments*math.pi # back +Y
            x=rad*math.cos(a); y=rad*math.sin(a)
            z=h-.006+(.043 if p["food"]=="corn" else .047)*(y/r)**1.42
            z+=.00075*math.sin(a*9+i*.6)*math.sin(math.pi*i/radial)
            verts.append((x,y,z))
    for i in range(radial):
        for k in range(segments):
            a=i*(segments+1)+k
            face=[a,a+segments+1,a+segments+2,a+1]
            faces.append(face)
            coords=[(.5+verts[j][0]/(2*r),.5+verts[j][1]/(2*r)) for j in face]
            uv.append(coords)
    new_mesh("OPEN HERO | peeled silver half-lid bent upwards",
             verts,faces,m["lid"],uv)
    back=[(x,y,z-.0003) for x,y,z in verts]
    new_mesh("OPEN HERO | foil underside of physically peeled lid",
             back,[list(reversed(f)) for f in faces],m["tin"],
             [list(reversed(v)) for v in uv])
    # A stamped ring-pull is integrated at a position on the elevated lid.
    x,y=0,r*.46
    zz=h-.006+.047*(y/r)**1.42+.003
    # Low polygon oval extruded loop following tilted tab.
    n=30;v=[];f=[];uv=[]
    for sc in (1,.58):
        for k in range(n):
            a=k*math.tau/n
            v.append((x+.010*sc*math.cos(a),y+.0065*sc*math.sin(a),
                      zz+.0016*math.sin(a)))
    for k in range(n):
        j=(k+1)%n
        f.append([k,j,n+j,n+k])
        uv.append([(k/n,0),(j/n,0),(j/n,1),(k/n,1)])
    new_mesh("OPEN HERO | pull-tab attached to peeled lid",v,f,m["seam"],uv)

def export_one(p,hero=False):
    reset()
    m=materials(p)
    metal_shell(p,m,hero)
    if hero:
        hero_food(p,m)
        peeled_hero_lid(p,m)
    name=p["id"]+("_OPEN_HERO" if hero else "_CLOSED")
    meshes=[o for o in SCENE.objects if o.type=="MESH" and o.get("game_asset")]
    for o in meshes:
        o["fictional_food_prop"]=True
        o["brand"]=p["brand"]
        o["variant"]=p["flavour"]
        o["weight_g"]=p["weight_g"]
    if hero:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCE,name+".blend"),compress=True)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in meshes:ob.select_set(True)
    C.view_layer.objects.active=meshes[0]
    path=os.path.join(OUT,name+".glb")
    bpy.ops.export_scene.gltf(filepath=path,export_format="GLB",
        use_selection=True,export_materials="EXPORT",export_yup=True,
        export_apply=True,export_draco_mesh_compression_enable=False)
    bpy.ops.object.select_all(action="DESELECT")
    with open(path,"rb") as f:
        magic,version,length=struct.unpack("<4sII",f.read(12))
        n,chunk=struct.unpack("<I4s",f.read(8))
        data=json.loads(f.read(n))
    assert magic==b"glTF" and version==2 and chunk==b"JSON"
    assert os.path.getsize(path)==length
    assert len(data.get("meshes",[]))>=8,len(data.get("meshes",[]))
    assert len(data.get("images",[]))>=3,len(data.get("images",[]))
    assert len(data.get("materials",[]))>=5
    assert any("TEXCOORD_0" in prim.get("attributes",{})
               for me in data["meshes"] for prim in me.get("primitives",[]))
    assert length>200000
    print("VALIDATED",name,"meshes",len(data["meshes"]),
          "images",len(data["images"]),"bytes",length,flush=True)

def render(name,position):
    # Lights, stage and camera are purely for previews: they never enter GLBs.
    background=mat("PREVIEW ONLY | pale shop tile",(.48,.50,.48),rough=.79)
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.011))
    floor=C.object;floor.name="PREVIEW ONLY | supermarket shelf"
    floor.dimensions=(.52,.48,.019)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    floor.data.materials.append(background)
    for pos,energy,size in [
        ((-.35,-.29,.37),105,.48),
        ((.26,.15,.42),85,.38)]:
        bpy.ops.object.light_add(type="AREA",location=pos)
        o=C.object;o.name="PREVIEW ONLY | area light"
        o.data.energy=energy;o.data.size=size
        o.rotation_euler=(Vector((0,0,.07))-o.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.object.camera_add(location=position)
    cam=C.object
    cam.rotation_euler=(Vector((0,0,.059))-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO"
    cam.data.ortho_scale=.190
    SCENE.camera=cam
    SCENE.world.color=(.22,.22,.22)
    SCENE.render.engine="CYCLES"
    SCENE.cycles.device="CPU"
    SCENE.cycles.samples=24
    if hasattr(SCENE.cycles,"use_denoising"):SCENE.cycles.use_denoising=False
    if hasattr(C.view_layer.cycles,"use_denoising"):C.view_layer.cycles.use_denoising=False
    SCENE.render.resolution_x=750
    SCENE.render.resolution_y=970
    SCENE.render.resolution_percentage=100
    SCENE.render.image_settings.file_format="PNG"
    SCENE.render.filepath=os.path.join(PREV,name+".png")
    SCENE.view_settings.view_transform="AgX"
    bpy.ops.render.render(write_still=True)
    print("RENDERED",SCENE.render.filepath,flush=True)

def main():
    assert len(PRODUCTS)==18
    for i,p in enumerate(PRODUCTS):
        export_one(p,False)
        if os.environ.get("RENDER_PREVIEWS")=="1" and i in (0,2,14):
            render(p["id"]+"_CLOSED",(.16,-.26,.20))
        if p["id"] in DOC["opened_hero_ids"]:
            export_one(p,True)
            if os.environ.get("RENDER_PREVIEWS")=="1":
                render(p["id"]+"_OPEN_HERO",(.16,-.26,.26))
        print("COMPLETED PRODUCT",i+1,"/",len(PRODUCTS),p["id"],flush=True)
    exports=[x for x in os.listdir(OUT) if x.endswith(".glb")]
    assert len(exports)==20,(len(exports),exports)
    print("SUCCESS: 18 closed tins, 2 opened food hero assets",flush=True)
if __name__=="__main__":main()
