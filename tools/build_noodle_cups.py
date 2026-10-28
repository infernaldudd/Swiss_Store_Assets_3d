"""Create 8 game-ready closed noodle cups + 1 opened premium hero cup.

True hollow tapered vessels, paper + plastic composite wall, rolled lip,
printed foil lids and pull tabs, base foot, curved wear and lightly crimped rim.
The open hero cup includes a partially peeled lid, three-dimensional noodles,
broth, vegetables, chili, garnish, and separate editable materials.

Run with blender 4.0+:
 blender -b -t 2 --python tools/build_noodle_cups.py
 RENDER_PREVIEWS=1 blender -b -t 2 --python tools/build_noodle_cups.py

PBR glTF packaged textures included. All geometry is metres; +Z is up.
"""
import bpy, os, math, random, json, struct
from mathutils import Vector,Matrix

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
TEXTURES=os.path.join(ROOT,"textures","noodle_cups")
OUT=os.path.join(ROOT,"assets","noodle_cups")
PREV=os.path.join(ROOT,"previews","noodle_cups")
SOURCE=os.path.join(ROOT,"source")
for folder in (OUT,PREV,SOURCE):os.makedirs(folder,exist_ok=True)
DATA=json.load(open(os.path.join(ROOT,"catalog","noodle_cups.json"),encoding="utf-8"))
PRODUCTS=DATA["products"]

SCENE=bpy.context.scene
C=bpy.context
def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for m in list(bpy.data.materials):
        if m.users==0:bpy.data.materials.remove(m)
    for im in list(bpy.data.images):
        if im.users==0:bpy.data.images.remove(im)

def make_mat(name,color,rough=.40,metal=.0,graphic=None,papermaps=False):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*color,1)
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    if graphic:
        path=os.path.join(TEXTURES,graphic)
        assert os.path.isfile(path),path
        image=bpy.data.images.load(path,check_existing=True)
        image.pack()
        node=m.node_tree.nodes.new("ShaderNodeTexImage")
        node.image=image
        m.node_tree.links.new(node.outputs["Color"],bs.inputs["Base Color"])
    if papermaps:
        p=os.path.join(TEXTURES,"_Shared_Paper_Normal.png")
        r=os.path.join(TEXTURES,"_Shared_Paper_Roughness.png")
        for fname,mode in ((p,"normal"),(r,"roughness")):
            im=bpy.data.images.load(fname,check_existing=True)
            im.colorspace_settings.name="Non-Color"
            im.pack()
            tex=m.node_tree.nodes.new("ShaderNodeTexImage")
            tex.image=im
            if mode=="normal":
                norm=m.node_tree.nodes.new("ShaderNodeNormalMap")
                norm.inputs["Strength"].default_value=.22
                m.node_tree.links.new(tex.outputs["Color"],norm.inputs["Color"])
                m.node_tree.links.new(norm.outputs["Normal"],bs.inputs["Normal"])
            else:
                m.node_tree.links.new(tex.outputs["Color"],bs.inputs["Roughness"])
    return m

def add_mesh(name,verts,faces,mat,uvs=None):
    mesh=bpy.data.meshes.new(name+" geometry")
    mesh.from_pydata(verts,[],faces)
    mesh.materials.append(mat)
    mesh.update()
    if uvs:
        layer=mesh.uv_layers.new(name="UV0")
        assert len(faces)==len(uvs),(name,len(faces),len(uvs))
        for polygon,corners in zip(mesh.polygons,uvs):
            assert len(corners)==len(polygon.loop_indices)
            for li,coord in zip(polygon.loop_indices,corners):
                layer.data[li].uv=coord
    obj=bpy.data.objects.new(name,mesh)
    C.collection.objects.link(obj)
    obj["game_asset"]=True
    return obj

def tube_mats(item):
    color=item["color"]
    rgb=tuple(int(color[i:i+2],16)/255 for i in (1,3,5))
    return {
      "wrap":make_mat("PRINTED | "+item["id"]+" sleeve",rgb,rough=.77,
                      graphic=item["id"]+"_Wrap.png",papermaps=True),
      "lid":make_mat("FOIL | printed "+item["id"]+" lid",rgb,rough=.29,metal=.25,
                     graphic=item["id"]+"_Lid.png"),
      "inner":make_mat("CUP | cream inner PP lining",(.88,.865,.804),.48,.02),
      "outer":make_mat("CUP | slightly textured white cup bottom",(.88,.861,.803),.82),
      "rim":make_mat("CUP | laminated rolled rim off-white",(.93,.916,.86),.33,.05),
      "foil":make_mat("FOIL | embossed silver underside",(.66,.68,.70),.32,.78),
      "seal":make_mat("LID | transparent bonding edge",(.80,.77,.68),.35,.06),
      "broth":make_mat("OPEN | spicy broth",(.49,.188,.078),.32,.05),
      "noodles":make_mat("OPEN | golden curled noodle cake",(.94,.71,.35),.78,0.0),
      "herb":make_mat("OPEN | spring onion slices",(.14,.45,.18),.7),
      "carrot":make_mat("OPEN | tiny carrot pieces",(.82,.31,.085),.65),
      "corn":make_mat("OPEN | sweetcorn",(.97,.75,.19),.55),
      "chili":make_mat("OPEN | red chili flakes",(.64,.075,.044),.67),
      "cream":make_mat("OPEN | tofu slices",(.91,.84,.67),.7)
    }

def dimes(item):
    height=.109 if item["size"]<=70 else .126
    top=.050 if item["size"]<=70 else .0535
    bottom=.0375 if item["size"]<=70 else .041
    return height,top,bottom

def cylinder_wall(name,height,r_top,r_bot,outer,inner,segments=64):
    # Watertight (as a 2-sided wall) tapered cup, wall thickness 0.9mm,
    # with two subtly differently faceted materials. Top rolled rim separately.
    n=segments; rings=14
    verts=[];faces=[];uvs=[]
    def point(j,k,inside=False):
        f=j/rings
        z=.004+(height-.004)*f
        r=r_bot+(r_top-r_bot)*(f**.98)
        if not inside:r+=.00022*math.sin(k*2.0+f*19)*math.sin(math.pi*f)
        else:r-=.00085
        t=2*math.pi*(k/n-.75)
        # Physical slight ovalisation + paper compression variation.
        r*=1+.0035*math.sin(2*t+1.6)*math.sin(math.pi*f)
        return (r*math.cos(t),r*math.sin(t),z)
    for inside in (False,True):
        for j in range(rings+1):
            for k in range(n+1):
                verts.append(point(j,k,inside))
    layer=(rings+1)*(n+1)
    for inside in (False,True):
        o=layer if inside else 0
        for j in range(rings):
            for k in range(n):
                a=o+j*(n+1)+k
                quad=[a,a+1,a+n+2,a+n+1]
                uv=[(k/n,j/rings),((k+1)/n,j/rings),((k+1)/n,(j+1)/rings),(k/n,(j+1)/rings)]
                if inside:quad.reverse();uv.reverse()
                faces.append(quad);uvs.append(uv)
    for k in range(n):
        # Closed rolled-under paper rim at the top and base edge
        quad=[rings*(n+1)+k, rings*(n+1)+k+1,layer+rings*(n+1)+k+1,layer+rings*(n+1)+k]
        faces.append(quad)
        uvs.append([(k/n,0),((k+1)/n,0),((k+1)/n,1),(k/n,1)])
        quad=[layer+k,layer+k+1,k+1,k]
        faces.append(quad)
        uvs.append([(k/n,0),((k+1)/n,0),((k+1)/n,1),(k/n,1)])
    # Outer and inner are separate editable mesh parts, reducing texture
    # smearing across inside wall. Construct from the same authored geometry.
    nwall=n*rings
    ob=add_mesh(name+" printed tapered sleeve",verts,faces[:nwall],outer,uvs[:nwall])
    # Merge inner wall and narrow edge strips with cream PP lining.
    other=add_mesh(name+" inner liner and wall edges",verts,faces[nwall:],
                   inner,uvs[nwall:])
    for poly in ob.data.polygons:poly.use_smooth=True
    for poly in other.data.polygons:poly.use_smooth=True
    return ob,other

def ring(name,r,z,thick,material,segments=64):
    # Mesh torus with 12 radial tube sections; real rolled bead, not shader fake.
    verts=[];faces=[];uvs=[];minor=12
    for i in range(segments):
        t=2*math.pi*i/segments
        for j in range(minor):
            a=2*math.pi*j/minor
            rad=r+thick*math.cos(a)
            verts.append((rad*math.cos(t),rad*math.sin(t),z+thick*math.sin(a)))
    for i in range(segments):
        ii=(i+1)%segments
        for j in range(minor):
            jj=(j+1)%minor
            faces.append([i*minor+j,ii*minor+j,ii*minor+jj,i*minor+jj])
            uvs.append([(i/segments,j/minor),((i+1)/segments,j/minor),
                        ((i+1)/segments,(j+1)/minor),(i/segments,(j+1)/minor)])
    obj=add_mesh(name,verts,faces,material,uvs)
    for p in obj.data.polygons:p.use_smooth=True
    return obj

def disc(name,r,z,material,segments=64,front=True):
    # UV normalised from XY to lid image; room for circular artwork.
    verts=[(0,0,z)]
    for i in range(segments):
        a=i*math.tau/segments
        verts.append((r*math.cos(a),r*math.sin(a),z))
    faces=[];uvs=[]
    for i in range(segments):
        q=(i+1)%segments
        f=[0,i+1,q+1]
        if not front:f.reverse()
        faces.append(f)
        uv=[(.5,.5),(.5+.5*math.cos(i*math.tau/segments),.5+.5*math.sin(i*math.tau/segments)),
            (.5+.5*math.cos(q*math.tau/segments),.5+.5*math.sin(q*math.tau/segments))]
        if not front:uv.reverse()
        uvs.append(uv)
    return add_mesh(name,verts,faces,material,uvs)

def pull_tab(r,z,mat):
    # Overhanging foil tab at -Y, gently bent up at the very tip.
    verts=[
      (-.012,-r+.001,z),(.012,-r+.001,z),
      (-.013,-r-.012,z+.0006),(.013,-r-.012,z+.0006),
      (-.009,-r-.023,z+.0031),(.009,-r-.023,z+.0031)
    ]
    fs=[[0,1,3,2],[2,3,5,4]]
    uv=[[(.31,.26),(.69,.26),(.69,.16),(.31,.16)],
        [(.31,.16),(.69,.16),(.63,.08),(.37,.08)]]
    return add_mesh("Stamped foil pull tab (real bent mesh)",verts,fs,mat,uv)

def bottom(height,rb,mats):
    disc("Recessed closed vessel base",rb-.001,.0045,mats["outer"],48,front=False)
    ring("Foot rollover seam",rb-.002,.0055,.0014,mats["outer"],48)

def build_closed(p,mats):
    h,rt,rb=dimes(p)
    cylinder_wall("Cup",h,rt,rb,mats["wrap"],mats["inner"])
    ring("Embossed rolled paper lip",rt-.0007,h,.0019,mats["rim"])
    ring("Foil heat seal circular weld",rt-.0020,h+.0018,.00065,mats["seal"])
    disc("Printed sealed foil lid",rt-.001,h+.0015,mats["lid"])
    pull_tab(rt,h+.0017,mats["lid"])
    bottom(h,rb,mats)
    return h,rt,rb

def peeled_lid(rt,h,mats):
    # 3D half-peel, curved upward from folded hinge near cup's centre. Outward
    # back-half is embossed with print above and reflective foil on underside.
    seg=32;radial=10
    verts=[];faces=[];uv=[]
    for i in range(radial+1):
        r=(i/radial)*(rt-.001)
        for j in range(seg+1):
            a=math.pi*j/seg
            x=r*math.cos(a)
            y=r*math.sin(a)
            z=h+.002+.032*(y/rt)**1.55+.006*(r/rt)*(math.sin(a*.9)**2)
            # A few uneven creases in the lifted foil sheet.
            z+=.0009*math.sin(a*7+r*240)*math.sin(math.pi*i/radial)
            verts.append((x,y,z))
    stride=seg+1
    for i in range(radial):
        for j in range(seg):
            a=i*stride+j
            f=[a,a+stride,a+stride+1,a+1]
            faces.append(f)
            u=[]
            for index in f:
                x,y,z=verts[index]
                u.append((.5+x/(2*rt),.5+y/(2*rt)))
            uv.append(u)
    add_mesh("Partially peeled printed foil lid | raised in 3D",verts,faces,mats["lid"],uv)
    # Reverse sheet physically separate but copied vertex positions slightly below.
    lo=[(x,y,z-.00028) for x,y,z in verts]
    fs=[list(reversed(f)) for f in faces]
    uv2=[list(reversed(v)) for v in uv]
    add_mesh("Aluminium underside of lifted lid",lo,fs,mats["foil"],uv2)
    # A separate overhanging tip rises continuously from the lifted foil's
    # high back edge, instead of hovering over the opposite side of the cup.
    y0=rt-.001
    z0=h+.002+.032*(y0/rt)**1.55+.006
    v=[(-.012,y0,z0),(.012,y0,z0),
       (-.011,y0+.014,z0+.009),(.011,y0+.014,z0+.009),
       (-.008,y0+.025,z0+.011),(.008,y0+.025,z0+.011)]
    add_mesh("Attached upward lifted foil pull tab",
             v,[[0,1,3,2],[2,3,5,4]],mats["foil"],
             [[(.35,.33),(.65,.33),(.65,.19),(.35,.19)],
              [(.35,.19),(.65,.19),(.61,.08),(.39,.08)]])

def soup_surface(rt,z,mats):
    # 3D dish surface beneath noodles, using a shallow warped disk rather than
    # visible empty flat cup.
    n=64;r=rt*.87
    verts=[(0,0,z)]
    for i in range(n):
        a=i*math.tau/n
        verts.append((r*math.cos(a),r*math.sin(a),z+.0005*math.sin(a*6)))
    faces=[[0,i+1,(i+1)%n+1] for i in range(n)]
    uv=[[(.5,.5),(.5+.5*math.cos(i*math.tau/n),.5+.5*math.sin(i*math.tau/n)),
         (.5+.5*math.cos(((i+1)%n)*math.tau/n),.5+.5*math.sin(((i+1)%n)*math.tau/n))] for i in range(n)]
    add_mesh("Broth surface | floating beneath actual noodles",verts,faces,mats["broth"],uv)

def multi_noodles(mats,rt,h):
    rr=random.Random(14209)
    soup_z=h-.038
    # 42 coils, 42*75 segments*6 vertices each ~19k verts.
    verts=[];faces=[];uv=[]
    sides=6;steps=66
    for noodle in range(44):
        cx=rr.uniform(-rt*.40,rt*.40)
        cy=rr.uniform(-rt*.43,rt*.34)
        path=[]
        frequency=rr.uniform(3.8,5.6)
        theta=rr.uniform(0,math.tau)
        rad=rr.uniform(.007,.017)
        for j in range(steps+1):
            f=j/steps
            angle=theta+f*math.tau*frequency
            r=(rad+.003*math.sin(f*9+noodle))*(.6+.4*math.sin(f*math.pi)**2)
            x=cx+r*math.cos(angle)+.003*math.sin(f*7+noodle*1.4)
            y=cy+r*math.sin(angle)+.003*math.cos(f*10+noodle*.93)
            z=soup_z+.003+rr.uniform(0,.0004)+.006*math.sin(f*math.pi)**2+.0015*math.sin(f*20+noodle)
            if math.hypot(x,y)>rt*.77:
                factor=(rt*.77)/math.hypot(x,y)
                x*=factor;y*=factor
            path.append((x,y,z))
        for j,point in enumerate(path):
            px,py,pz=point
            v=Vector(path[min(j+1,steps)])-Vector(path[max(0,j-1)])
            tangent=v.normalized() if v.length>1e-6 else Vector((1,0,0))
            n1=tangent.cross(Vector((0,0,1)))
            if n1.length<.001:n1=Vector((1,0,0))
            n1.normalize()
            n2=tangent.cross(n1).normalized()
            thickness=.00063*(1+.1*math.sin(noodle+j*.3))
            for k in range(sides):
                q=math.tau*k/sides
                off=n1*(math.cos(q)*thickness)+n2*(math.sin(q)*thickness)
                verts.append((px+off.x,py+off.y,pz+off.z))
        base=noodle*(steps+1)*sides
        for j in range(steps):
            for k in range(sides):
                kk=(k+1)%sides
                f=[base+j*sides+k,base+j*sides+kk,base+(j+1)*sides+kk,base+(j+1)*sides+k]
                faces.append(f)
                uv.append([(j/steps,k/sides),(j/steps,(k+1)/sides),
                           ((j+1)/steps,(k+1)/sides),((j+1)/steps,k/sides)])
    o=add_mesh("OPEN HERO | individually curled noodle strands 3D",verts,faces,mats["noodles"],uv)
    o["noodle_coils"]=44
    for p in o.data.polygons:p.use_smooth=True
    return soup_z

def garnish(soup_z,rt,mats):
    rr=random.Random(72609)
    # Three compact garnish mesh groups for batch-friendly draw calls.
    for which,material,num in [
        ("herb",mats["herb"],64),
        ("carrot",mats["carrot"],22),
        ("corn",mats["corn"],23),
        ("chili",mats["chili"],27),
        ("cream",mats["cream"],9)
    ]:
        verts=[];faces=[];uv=[]
        for i in range(num):
            t=rr.random()*math.tau
            r=rr.uniform(.004,rt*.67)
            x,y=r*math.cos(t),r*math.sin(t)
            z=soup_z+.006+rr.random()*.009
            a=rr.uniform(0,math.tau)
            sx=.0012 if which in ("herb","chili") else .0022
            sy=.0018 if which in ("herb","chili") else .0025
            if which=="cream":sx=.004;sy=.002
            q=[(x-sx,y-sy,z),(x+sx,y-sy,z+.001),(x+sx,y+sy,z),(x-sx,y+sy,z-.0006)]
            c=len(verts);verts.extend(q);faces.append([c,c+1,c+2,c+3])
            uv.append([(0,0),(1,0),(1,1),(0,1)])
        add_mesh("OPEN HERO | garnish "+which,verts,faces,material,uv)

def open_hero(p,mats):
    h,rt,rb=dimes(p)
    cylinder_wall("Opened cup",h,rt,rb,mats["wrap"],mats["inner"])
    ring("Exposed rolled cup lip",rt-.0007,h,.0019,mats["rim"])
    ring("Foil heat seam under peeled lid",rt-.0020,h+.0014,.00055,mats["seal"])
    bottom(h,rb,mats)
    soup_surface(rt,h-.040,mats)
    soup_z=multi_noodles(mats,rt,h)
    garnish(soup_z,rt,mats)
    peeled_lid(rt,h,mats)
    return h,rt,rb

def validate(path,expected_images=4):
    with open(path,"rb") as f:
        magic,ver,total=struct.unpack("<4sII",f.read(12))
        n,fmt=struct.unpack("<I4s",f.read(8))
        doc=json.loads(f.read(n))
    assert magic==b"glTF" and ver==2 and fmt==b"JSON"
    assert total==os.path.getsize(path)
    assert len(doc.get("meshes",[]))>=6
    assert len(doc.get("materials",[]))>=4
    assert len(doc.get("images",[]))>=expected_images
    assert any("TEXCOORD_0" in p.get("attributes",{}) for m in doc["meshes"] for p in m.get("primitives",[]))
    assert total>40000
    print("VALIDATED",os.path.basename(path),"meshes",len(doc["meshes"]),
          "images",len(doc["images"]),"bytes",total,flush=True)

def export(p,hero):
    mats=tube_mats(p)
    d=open_hero(p,mats) if hero else build_closed(p,mats)
    name=p["id"]+("_OPEN_HERO" if hero else "_Closed")
    meshes=[o for o in SCENE.objects if o.get("game_asset") and o.type=="MESH"]
    assert len(meshes)>=6
    for o in meshes:
        o["brand"]=p["brand"]
        o["flavour"]=p["flavor"]
        o["fictional_product"]=True
        o["dimensions_m"]=str([round(d[1]*2,3),round(d[1]*2,3),round(d[0],3)])
    if hero:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCE,name+".blend"),compress=True)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in meshes:ob.select_set(True)
    C.view_layer.objects.active=meshes[0]
    path=os.path.join(OUT,name+".glb")
    bpy.ops.export_scene.gltf(filepath=path,export_format="GLB",use_selection=True,
                              export_materials="EXPORT",export_apply=True,
                              export_yup=True,export_draco_mesh_compression_enable=False)
    bpy.ops.object.select_all(action="DESELECT")
    validate(path)
    return d

def preview(name,camera_xyz):
    env=make_mat("PREVIEW ONLY | supermarket background",(.33,.37,.36),.93,0)
    tabletop=make_mat("PREVIEW ONLY | pale laminated shelf",(.59,.62,.61),.53,.02)
    def box(name,center,size,material):
        bpy.ops.mesh.primitive_cube_add(size=1,location=center)
        obj=C.object;obj.name=name
        obj.dimensions=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        obj.data.materials.append(material)
    box("PREVIEW ONLY | shelf",(0,0,-.014),(.70,.68,.024),tabletop)
    box("PREVIEW ONLY | wall",(0,.23,.29),(.74,.06,.68),env)
    for loc,power,sz in [
        ((-.35,-.40,.47),95,.55),
        ((.26,-.17,.51),75,.39)]:
        bpy.ops.object.light_add(type="AREA",location=loc)
        a=C.object;a.name="PREVIEW ONLY | softbox"
        a.data.energy=power;a.data.size=sz
        a.rotation_euler=(Vector((0,0,.07))-a.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.object.camera_add(location=camera_xyz)
    cam=C.object;cam.name="PREVIEW ONLY | camera"
    cam.rotation_euler=(Vector((0,0,.073))-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO";cam.data.ortho_scale=.215
    SCENE.camera=cam
    SCENE.world.color=(.20,.20,.20)
    SCENE.render.engine="CYCLES";SCENE.cycles.device="CPU"
    SCENE.cycles.samples=28
    if hasattr(SCENE.cycles,"use_denoising"):SCENE.cycles.use_denoising=False
    if hasattr(C.view_layer.cycles,"use_denoising"):C.view_layer.cycles.use_denoising=False
    SCENE.render.resolution_x=850;SCENE.render.resolution_y=1010
    SCENE.render.resolution_percentage=100
    SCENE.render.image_settings.file_format="PNG"
    SCENE.render.filepath=os.path.join(PREV,name+".png")
    SCENE.view_settings.view_transform="AgX"
    bpy.ops.render.render(write_still=True)
    print("RENDER",SCENE.render.filepath,flush=True)

def main():
    assert len(PRODUCTS)==8,len(PRODUCTS)
    for i,p in enumerate(PRODUCTS):
        reset()
        export(p,False)
        if os.environ.get("RENDER_PREVIEWS")=="1" and i in (0,3,7):
            preview(p["id"]+"_Closed",(0.18,-.33,.19))
        print("CLOSED",i+1,"/",len(PRODUCTS),p["id"],flush=True)
    p=PRODUCTS[-1]
    reset()
    export(p,True)
    if os.environ.get("RENDER_PREVIEWS")=="1":
        preview(p["id"]+"_OPEN_HERO",(.14,-.23,.26))
    files=[x for x in os.listdir(OUT) if x.endswith(".glb")]
    assert len(files)==9,(len(files),files)
    print("SUCCESS: 8 closed cups + 1 opened noodles hero cup",flush=True)

if __name__=="__main__":main()
