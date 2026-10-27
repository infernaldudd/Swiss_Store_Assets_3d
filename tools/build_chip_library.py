"""Produce 88 independently importable low/mid-poly Swiss fictional chip products.

Blender 4.0 system packages are supported. Includes realistically pillow-inflated
foil bags with fused crimp seals and a separate cylindrical stacked-chips family.

This tool only ADDS files in assets/chips/ and does not change earlier assets.
Run: blender -b -t 2 --python tools/build_chip_library.py
See catalog/chip_collection.json for all variants.
"""
import bpy, math, json, os, struct
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
CATALOG=json.load(open(os.path.join(ROOT,"catalog/chip_collection.json"),encoding="utf-8"))
ITEMS=CATALOG["entries"]
TEXTURES=os.path.join(ROOT,"textures","chips")
OUT=os.path.join(ROOT,"assets","chips")
os.makedirs(OUT,exist_ok=True)
S=bpy.context.scene
C=bpy.context

def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # Avoid accumulating image data across many independent export passes.
    for m in list(bpy.data.materials):
        if m.users==0:bpy.data.materials.remove(m)
    for img in list(bpy.data.images):
        if img.users==0:bpy.data.images.remove(img)

def create_mat(name,base,metal=.05,rough=.38,image=None,normal=False,roughness=False):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*base,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*base,1)
    bs.inputs["Metallic"].default_value=metal
    bs.inputs["Roughness"].default_value=rough
    if image:
        image_path=os.path.join(TEXTURES,image)
        assert os.path.isfile(image_path),image_path
        image_data=bpy.data.images.load(image_path,check_existing=True)
        tex=m.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image=image_data
        tex.extension="REPEAT"
        if normal or roughness:
            image_data.colorspace_settings.name="Non-Color"
            if normal:
                n=m.node_tree.nodes.new("ShaderNodeNormalMap")
                n.inputs["Strength"].default_value=.35
                m.node_tree.links.new(tex.outputs["Color"],n.inputs["Color"])
                m.node_tree.links.new(n.outputs["Normal"],bs.inputs["Normal"])
            if roughness:
                m.node_tree.links.new(tex.outputs["Color"],bs.inputs["Roughness"])
        else:
            m.node_tree.links.new(tex.outputs["Color"],bs.inputs["Base Color"])
    return m

def get_mats(item):
    a=item["accent"]
    rgb=tuple(int(a[k:k+2],16)/255 for k in (1,3,5))
    # Name matters in the glTF and for straightforward Unreal re-assignment.
    front=create_mat("PRINT | "+item["id"]+" front",rgb,image=item["id"]+"_front.jpg",metal=.085,rough=.31)
    back=create_mat("PRINT | "+item["id"]+" back",rgb,image=item["id"]+"_back.jpg",metal=.10,rough=.36)
    # Shared independent microdetail maps give true non-flat foil highlights.
    for printed in (front,back):
        p=printed.node_tree.nodes.get("Principled BSDF")
        n=printed.node_tree.nodes.new("ShaderNodeTexImage")
        n.image=bpy.data.images.load(os.path.join(TEXTURES,"_shared_foil_normal.png"),check_existing=True)
        n.image.colorspace_settings.name="Non-Color"
        normalmap=printed.node_tree.nodes.new("ShaderNodeNormalMap")
        normalmap.inputs["Strength"].default_value=.32
        printed.node_tree.links.new(n.outputs["Color"],normalmap.inputs["Color"])
        printed.node_tree.links.new(normalmap.outputs["Normal"],p.inputs["Normal"])
        rough=printed.node_tree.nodes.new("ShaderNodeTexImage")
        rough.image=bpy.data.images.load(os.path.join(TEXTURES,"_shared_foil_rough.png"),check_existing=True)
        rough.image.colorspace_settings.name="Non-Color"
        printed.node_tree.links.new(rough.outputs["Color"],p.inputs["Roughness"])
    weld=create_mat("Sealed foil | crimped branded edge",rgb,metal=.22,rough=.35)
    metallic=create_mat("Highlights | aluminium plated edges",(.61,.62,.58),metal=.77,rough=.3)
    cap=create_mat("Canister | smoked coloured polymer top",(.075,.078,.075),metal=.18,rough=.31)
    return front,back,weld,metallic,cap

def mesh_object(name,verts,faces,mat_ids,mats,uvcoords):
    me=bpy.data.meshes.new(name+" mesh")
    me.from_pydata(verts,[],faces)
    me.update()
    for m in mats:me.materials.append(m)
    uv=me.uv_layers.new(name="UV | original artwork")
    assert len(faces)==len(mat_ids)==len(uvcoords)
    for poly,mi,coords in zip(me.polygons,mat_ids,uvcoords):
        poly.material_index=mi
        if len(coords)!=len(poly.loop_indices):
            raise ValueError((name,len(coords),len(poly.loop_indices)))
        for li,xy in zip(poly.loop_indices,coords):
            uv.data[li].uv=xy
        poly.use_smooth=True
    o=bpy.data.objects.new(name,me)
    C.collection.objects.link(o)
    o["chips_collection"]=True
    return o

def dims(item):
    g=item["weight_g"]
    form=item["shape"]
    if form=="can":
        return .081,.250
    scale=.70+math.sqrt(g/90)*.29
    w=(.160*scale)* (1.09 if form=="tortilla" else 1)
    h=(.258*scale)* (1.08 if form=="tortilla" else 1)
    return round(w,4),round(h,4)

def bag_body(item,mats):
    w,h=dims(item)
    nx,nz=22,32
    half=w/2
    # Folded cap zones at each end are physically distinct from the gas-filled bag.
    zbase=.015
    active_h=h-.030
    def point(i,j,side):
        u=i/nx;v=j/nz
        a=2*u-1
        x=a*half+.00067*math.sin(29*v+5*u)*(1-abs(a))
        z=zbase+v*active_h + .0007*math.sin(14*u+v*16)*math.sin(math.pi*v)
        env=max(0,1-abs(a)**3.8)**.68 * max(0,math.sin(math.pi*v))**.57
        bulge=.004 + .029*env
        # narrow diagonal micro-folds plus edge wrinkles in actual mesh geometry
        crease=.0010*math.sin(15*u+19*v+.8*math.sin(v*18))*(.12+.88*abs(a)**2)
        crease+=.00035*math.sin(47*u-63*v)
        y=side*(bulge+crease)
        return (x,y,z)
    verts=[]
    layer=(nx+1)*(nz+1)
    for side in (-1,1):
        for j in range(nz+1):
            for i in range(nx+1):
                verts.append(point(i,j,side))
    def ix(i,j,b):return (layer if b else 0)+j*(nx+1)+i
    faces=[];ids=[];maps=[]
    for back in (False,True):
        for j in range(nz):
            for i in range(nx):
                face=[ix(i,j,back),ix(i+1,j,back),ix(i+1,j+1,back),ix(i,j+1,back)]
                coords=[(i/nx,j/nz),((i+1)/nx,j/nz),((i+1)/nx,(j+1)/nz),(i/nx,(j+1)/nz)]
                if back:
                    face.reverse()
                    coords=[(1-u,v) for u,v in reversed(coords)]
                faces.append(face)
                maps.append(coords)
                ids.append(1 if back else 0)
    # Side-gusset closure has its own geometry and a foil seam material.
    for j in range(nz):
        for i in (0,nx):
            c=[ix(i,j,False),ix(i,j+1,False),ix(i,j+1,True),ix(i,j,True)]
            if i==nx:c.reverse()
            faces.append(c);ids.append(2)
            maps.append([(0,j/nz),(0,(j+1)/nz),(1,(j+1)/nz),(1,j/nz)] if i==0 else [(1,j/nz),(1,(j+1)/nz),(0,(j+1)/nz),(0,j/nz)])
    for j in (0,nz):
        for i in range(nx):
            c=[ix(i,j,False),ix(i+1,j,False),ix(i+1,j,True),ix(i,j,True)]
            if j==0:c.reverse()
            faces.append(c);ids.append(2)
            maps.append([(i/nx,0),((i+1)/nx,0),((i+1)/nx,1),(i/nx,1)])
    body=mesh_object("Foil packaging | 3D crumpled body",verts,faces,ids,mats,maps)
    body["weight_g"]=item["weight_g"]
    body["made_for"]="Helvetia / GundeliTheftAuto7"

def crimp(item,mats,upper):
    w,h=dims(item)
    # Compression ridges are part of the actual 3D silhouette.
    z0=h-.016 if upper else 0
    z1=h if upper else .016
    nx,nz=22,11
    verts=[];fs=[];ids=[];maps=[]
    for side in (-1,1):
        for j in range(nz+1):
            v=j/nz;z=z0+(z1-z0)*v
            for i in range(nx+1):
                u=i/nx
                x=(u-.5)*(w+.012)+.0004*math.sin(9*u+v*11)
                y=side*(.0027+.0006*math.cos(v*math.pi*nz*2))
                verts.append((x,y,z))
    stride=(nx+1)*(nz+1)
    def ix(i,j,back):return (stride if back else 0)+j*(nx+1)+i
    for back in (False,True):
        for j in range(nz):
            for i in range(nx):
                f=[ix(i,j,back),ix(i+1,j,back),ix(i+1,j+1,back),ix(i,j+1,back)]
                uv=[(i/nx,j/nz),((i+1)/nx,j/nz),((i+1)/nx,(j+1)/nz),(i/nx,(j+1)/nz)]
                if back:f.reverse();uv.reverse()
                fs.append(f);maps.append(uv);ids.append(3 if j%3==0 else 2)
    for i in range(nx):
        for j in (0,nz):
            fs.append([ix(i,j,False),ix(i+1,j,False),ix(i+1,j,True),ix(i,j,True)])
            ids.append(2);maps.append([(0,0),(1,0),(1,1),(0,1)])
    for j in range(nz):
        for i in (0,nx):
            fs.append([ix(i,j,False),ix(i,j+1,False),ix(i,j+1,True),ix(i,j,True)])
            ids.append(2);maps.append([(0,0),(1,0),(1,1),(0,1)])
    mesh_object("Heat sealed crimp | "+("top" if upper else "bottom"),verts,fs,ids,mats,maps)

def center_fin(item,mats):
    w,h=dims(item)
    z0=.018;z1=h-.018
    verts=[];faces=[];ids=[];uv=[]
    seg=24
    for j in range(seg+1):
        v=j/seg
        for k,x in enumerate((-.005,0,.005)):
            y=.010+.027*max(0,math.sin(math.pi*v))**.55+.0017+.00065*math.sin(v*18+k)
            verts.append((x,y,z0+v*(z1-z0)))
    for j in range(seg):
        for k in range(2):
            faces.append([j*3+k,j*3+k+1,(j+1)*3+k+1,(j+1)*3+k])
            ids.append(3)
            uv.append([(k/2,j/seg),((k+1)/2,j/seg),((k+1)/2,(j+1)/seg),(k/2,(j+1)/seg)])
    mesh_object("Reinforced rear fin fold",verts,faces,ids,mats,uv)

def canister(item,mats):
    w,h=dims(item)
    radius=w/2
    n=32
    rings=18
    verts=[];faces=[];ids=[];uv=[]
    z0=.009;z1=h-.010
    for j in range(rings+1):
        t=j/rings
        z=z0+(z1-z0)*t
        for k in range(n+1):
            theta=2*math.pi*k/n
            rr=radius+.00025*math.sin(theta*9+z*71)
            verts.append((rr*math.cos(theta),rr*math.sin(theta),z))
    for j in range(rings):
        for k in range(n):
            face=[j*(n+1)+k,j*(n+1)+k+1,(j+1)*(n+1)+k+1,(j+1)*(n+1)+k]
            # Front covers -Y, rear covers +Y.
            front = k>=n//2
            u0=(k-n/2)/(n/2) if front else k/(n/2)
            u1=(k+1-n/2)/(n/2) if front else (k+1)/(n/2)
            faces.append(face)
            ids.append(0 if front else 1)
            uv.append([(u0,j/rings),(u1,j/rings),(u1,(j+1)/rings),(u0,(j+1)/rings)])
    o=mesh_object("Stacked chips | printable cylindrical tube",verts,faces,ids,mats,uv)
    o["packaging"]="Paper laminate spiral-wound tube with plastic lid"
    for label,z,r,mat_index in [
        ("Bottom rolled aluminium seam",.004,radius+.0015,3),
        ("Top rolled aluminium seam",h-.008,radius+.0015,3),
        ("Removable polymer lid",h-.003,radius+.003,4),
    ]:
        verts=[];faces=[];ids=[];uv=[]
        for zz,rad in ((z-.003,r),(z+.003,r)):
            for k in range(n):
                t=math.tau*k/n
                verts.append((rad*math.cos(t),rad*math.sin(t),zz))
        for k in range(n):
            kn=(k+1)%n
            faces.append([k,kn,n+kn,n+k]);ids.append(mat_index)
            uv.append([(k/n,0),(kn/n,0),(kn/n,1),(k/n,1)])
        faces.append(list(range(n,2*n)))
        ids.append(mat_index)
        uv.append([(0,0)]*n)
        mesh_object(label,verts,faces,ids,mats,uv)

def build(item):
    reset()
    mats=get_mats(item)
    if item["shape"]=="can":
        canister(item,mats)
    else:
        bag_body(item,mats)
        crimp(item,mats,True)
        crimp(item,mats,False)
        center_fin(item,mats)
    bpy.ops.object.select_all(action="DESELECT")
    meshes=[o for o in S.objects if o.type=="MESH"]
    assert len(meshes)==4,("expect 4 mesh objects",item["id"],len(meshes))
    for o in meshes:o.select_set(True)
    C.view_layer.objects.active=meshes[0]
    path=os.path.join(OUT,item["id"]+".glb")
    bpy.ops.export_scene.gltf(filepath=path,export_format="GLB",
                              use_selection=True,export_materials="EXPORT",
                              export_yup=True,export_apply=True,
                              export_draco_mesh_compression_enable=False)
    # Validate each exported GLB binary, mesh count, UV material slots and images.
    with open(path,"rb") as f:
        magic,version,length=struct.unpack("<4sII",f.read(12))
        chunksize,ctype=struct.unpack("<I4s",f.read(8))
        jsondata=json.loads(f.read(chunksize))
    actual=os.path.getsize(path)
    assert magic==b"glTF" and version==2 and length==actual
    assert ctype==b"JSON"
    assert len(jsondata.get("meshes",[]))>=4
    assert len(jsondata.get("materials",[]))>=4
    assert len(jsondata.get("images",[]))>=2
    assert all(any(p.get("attributes",{}).get("TEXCOORD_0") is not None for p in m.get("primitives",[]))
               for m in jsondata["meshes"][:1])
    assert actual>16000
    if item["shape"]=="can":
        assert "cylindrical" in jsondata["nodes"][0].get("name","").lower() or len(jsondata["meshes"])>=4
    return actual

def main():
    assert len(ITEMS)==88,len(ITEMS)
    assert len(set(item["id"] for item in ITEMS))==len(ITEMS)
    bytes_total=0
    for i,item in enumerate(ITEMS):
        amount=build(item)
        bytes_total+=amount
        if i%8==0 or i==len(ITEMS)-1:
            print("BUILT",i+1,"/",len(ITEMS),item["id"],"bytes",amount,flush=True)
    import glob
    paths=glob.glob(os.path.join(OUT,"*.glb"))
    assert len(paths)==len(ITEMS),(len(paths),len(ITEMS))
    print("SUCCESS",len(paths),"distinct GLB files, total bytes",bytes_total,flush=True)
if __name__=="__main__":main()
