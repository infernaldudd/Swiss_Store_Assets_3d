"""Build 100 separate dairy SKU GLBs, each holding 5–20 matching retail units.

Five folders organize the 100 genuinely different products (20 SKUs per
folder), but each exported file is ONE SKU's stock batch, e.g. 12 identical
milk cartons or 8 identical cheese packages. Each unit remains an independently
named instance sharing geometry/material data to minimize file size.

 Blender -b -t 2 --python tools/build_dairy_100.py
"""

import bpy,os,json,math,struct,random
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
ART=os.path.join(ROOT,"textures","dairy_100")
OUT=os.path.join(ROOT,"assets","dairy_100")
PR=os.path.join(ROOT,"previews","dairy_100")
os.makedirs(OUT,exist_ok=True)
os.makedirs(PR,exist_ok=True)
CAT=json.load(open(os.path.join(ROOT,"catalog","dairy_100.json"),encoding="utf8"))
S=bpy.context.scene;C=bpy.context
def reset():
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
 for m in list(bpy.data.materials):
  if m.users==0:bpy.data.materials.remove(m)
 for im in list(bpy.data.images):
  if im.users==0:bpy.data.images.remove(im)
def mat(name,color=(.7,.7,.7),metal=0,rough=.5,texture=None,alpha=1):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,alpha)
 p=m.node_tree.nodes.get("Principled BSDF")
 p.inputs["Base Color"].default_value=(*color,1);p.inputs["Metallic"].default_value=metal
 p.inputs["Roughness"].default_value=rough
 p.inputs["Alpha"].default_value=alpha
 if alpha<1:m.blend_method="BLEND"
 if texture:
  path=os.path.join(ART,texture);assert os.path.isfile(path),path
  img=bpy.data.images.load(path,check_existing=True)
  img.pack()
  n=m.node_tree.nodes.new("ShaderNodeTexImage")
  n.image=img
  m.node_tree.links.new(n.outputs["Color"],p.inputs["Base Color"])
 return m
def modelmesh(name,verts,faces,material,uvs=None,smooth=False):
 me=bpy.data.meshes.new(name+" geo");me.from_pydata(verts,[],faces);me.update()
 me.materials.append(material)
 if uvs is not None:
  assert len(uvs)==len(faces),(name,len(faces),len(uvs))
  layer=me.uv_layers.new(name="Printable art UV")
  for p,coordinates in zip(me.polygons,uvs):
   assert len(p.loop_indices)==len(coordinates),(name,len(p.loop_indices),len(coordinates))
   for li,co in zip(p.loop_indices,coordinates):layer.data[li].uv=co
 if smooth:
  for p in me.polygons:p.use_smooth=True
 obj=bpy.data.objects.new(name,me);C.collection.objects.link(obj)
 obj["dairy_part"]=True
 return obj
def box(name,loc,dims,material,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
 obj=C.object;obj.name=name;obj.dimensions=dims
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 obj.data.materials.append(material);obj["dairy_part"]=True
 if bevel:
  m=obj.modifiers.new("Real manufacture edge radius","BEVEL")
  m.width=bevel;m.segments=3
  obj.modifiers.new("Weighted face normals","WEIGHTED_NORMAL")
 return obj
def circle(name,r,depth,z,material,n=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=depth,location=(0,0,z))
 o=C.object;o.name=name;o.data.materials.append(material);o["dairy_part"]=True
 for p in o.data.polygons:p.use_smooth=True
 return o
def lathe(name,profile,material,n=48):
 verts=[];faces=[];UV=[]
 for radius,z in profile:
  for k in range(n+1):
   u=k/n;a=(u-.75)*math.tau
   verts.append((radius*math.cos(a),radius*math.sin(a),z))
 for j in range(len(profile)-1):
  for k in range(n):
   a=j*(n+1)+k
   faces.append((a,a+1,a+n+2,a+n+1))
   UV.append([(k/n,j/(len(profile)-1)),((k+1)/n,j/(len(profile)-1)),
              ((k+1)/n,(j+1)/(len(profile)-1)),(k/n,(j+1)/(len(profile)-1))])
 return modelmesh(name,verts,faces,material,UV,True)
def circle_ring(name,R,r,z,material,n=48,m=8):
 verts=[];faces=[];UV=[]
 for i in range(n):
  a=i*math.tau/n
  for j in range(m):
   b=j*math.tau/m;rr=R+r*math.cos(b)
   verts.append((rr*math.cos(a),rr*math.sin(a),z+r*math.sin(b)))
 for i in range(n):
  for j in range(m):
   k=(i+1)%n;t=(j+1)%m
   faces.append((i*m+j,k*m+j,k*m+t,i*m+t))
   UV.append([(i/n,j/m),((i+1)/n,j/m),((i+1)/n,(j+1)/m),(i/n,(j+1)/m)])
 return modelmesh(name,verts,faces,material,UV,True)
def plane_front(name,w,h,y,zc,material):
 # A raised paper-print/sleeve facet; front looks toward -Y.
 vs=[(-w/2,y,zc-h/2),(w/2,y,zc-h/2),(w/2,y,zc+h/2),(-w/2,y,zc+h/2)]
 return modelmesh(name,vs,[[0,1,2,3]],material,[[(0,0),(1,0),(1,1),(0,1)]])
def plane_top(name,w,depth,z,material):
 vs=[(-w/2,-depth/2,z),(w/2,-depth/2,z),
     (w/2,depth/2,z),(-w/2,depth/2,z)]
 return modelmesh(name,vs,[[0,1,2,3]],material,[[(0,0),(1,0),(1,1),(0,1)]])
def carton(p,m,metal):
 # Full 1-litre gable-top brick with scored shoulders and sealed folded ridge.
 h=.234 if p["net"]>=900 else .156
 w=.071 if p["net"]>=900 else .055
 dep=.071 if p["net"]>=900 else .049
 body_h=h-.040
 box("Laminated paperboard main liquid carton",(0,0,body_h/2),(w,dep,body_h),m["container"],.0016)
 y=-dep/2-.00065
 plane_front("UV-printed front label "+p["id"],w-.003,body_h-.006,y,body_h/2,m["print"])
 # Four genuinely angled folded gable roof facets + ridge. A 6-vertex
 # shoulder piece is not just a square or false bump map.
 vs=[(-w/2,-dep/2,body_h),(w/2,-dep/2,body_h),
     (w/2,dep/2,body_h),(-w/2,dep/2,body_h),
     (-w/2,0,h-.006),(w/2,0,h-.006)]
 fs=[[0,1,5,4],[3,2,5,4],[0,4,3],[1,2,5]]
 modelmesh("Folded inward gable top",vs,fs,m["container"])
 box("Factory pinch-sealed top ridge",(0,0,h-.004),(w+.001,.004,.009),m["container"],.0007)
 # Lightweight circular opening, tamper band, and screw cap.
 cap=metal["cap"]
 circle("Moulded pouring spout",.010,.004,h-.027,cap,32)
 circle("Threaded pouring cap",.013,.010,h-.020,cap,32)
 circle_ring("Cap anti-leak collar",.012,.001,h-.027,cap,32)
 return h
def bottle(p,m,metal):
 h=.232 if p["net"]>600 else .188
 r=.037 if p["net"]>600 else .031
 shoulder=h-.046
 plastic=m["plastic"]
 lathe("Blow moulded bottle body",[
  (r*.47,.002),(r*.76,.004),(r*.94,.012),(r,.030),(r,shoulder-.025),
  (r*.97,shoulder),(r*.81,shoulder+.010),(r*.48,h-.027),
  (r*.40,h-.022)],plastic)
 for i in range(5):
  circle_ring("Embossed bottle grip rib "+str(i),r-.0007,.00052,.018+i*.006,plastic,36)
 rlab=r+.0009
 lathe("360-degree printed shrink sleeve",[(rlab,.051),(rlab,shoulder-.016)],m["print"])
 circle("Tamper proof neck safety ring",r*.52,.004,h-.021,metal["cap"])
 circle("Closure cap with recessed disc",r*.52,.020,h-.012,metal["cap"])
 for i in range(18):
  a=math.tau*i/18
  o=box("Cap grip tooth",((r*.53)*math.cos(a),(r*.53)*math.sin(a),h-.010),
        (.001,.0014,.012),metal["cap"],.00025)
  o.rotation_euler.z=a
 return h
def cup(p,m,metal,tub=False):
 # Yoghurt pot: small taper with a rolled lip, heat-sealed circular foil.
 h=.077 if tub else (.080 if p["net"]>=200 else .071)
 rtop=.048 if tub else .043
 rbottom=.039 if tub else .032
 lathe("Injection moulded tapered pot",[
  (rbottom*.95,.003),(rbottom,.005),(rbottom+.002,.018),
  (rtop-.001,h-.008),(rtop,h-.005)],m["container"])
 rlabel=rtop-.005
 lathe("Original 360 printed sleeve",
       [(rbottom+.0008,.010),(rtop-.0001,h-.013)],m["print"])
 circle_ring("Proper moulded rim rollover",rtop-.0015,.002,h-.006,metal["white"])
 circle("Heat-sealed printed top foil",rtop-.001,.001,h-.004,metal["foil"])
 circle_ring("Foil stamped rim",rtop-.002,.0006,h-.004,metal["steel"])
 # Genuine foil pull tab, not a flat circle painted on the lid.
 v=[(-.010,rtop-.004,h-.003),(.010,rtop-.004,h-.003),
    (-.007,rtop+.013,h+.002),(.007,rtop+.013,h+.002)]
 modelmesh("Liftable corner pull tab",v,[[0,1,3,2]],metal["foil"],
           [[(.18,.18),(.82,.18),(.8,.05),(.2,.05)]])
 return h
def wedge(p,m,metal):
 # Vacuum-pack aged Swiss cheese wedge: actual triangular prism plus top seal.
 # Geometry differs by SKU size to avoid every cheese being the same wedge.
 a=.068 if p["net"]>180 else .060;b=.040 if p["net"]>180 else .036
 h=.033
 v=[(-a/2,-b/2,.008),(a/2,-b/2,.008),(0,b/2,.008),
    (-a/2,-b/2,h),(a/2,-b/2,h),(0,b/2,h)]
 fs=[[0,2,1],[3,4,5],[0,1,4,3],[1,2,5,4],[2,0,3,5]]
 modelmesh("True triangular artisan cheese wedge",v,fs,m["cheese"])
 box("Transparent thermoformed vacuum wrap",(0,0,h/2+.005),
     (a+.012,b+.014,h+.016),metal["film"],.004)
 plane_front("Premium printed strip label",a*.88,.024,-b/2-.0071,.024,m["print"])
 return h+.013
def tray(p,m,metal):
 w=.105 if p["net"]>=180 else .087
 dep=.077 if p["net"]>=180 else .066
 h=.026
 box("Deep vacuum formed food tray",(0,0,.014),(w,dep,.028),metal["white"],.004)
 box("Visible cheese or cream insert",(0,0,.020),(w-.009,dep-.009,.020),m["cheese"],.003)
 box("Thin transparent cling film",(0,0,.030),(w+.003,dep+.003,.0011),metal["film"],.001)
 plane_top("Printed upper foil label",w*.87,dep*.87,.032,m["print"])
 plane_front("Front product information band",w*.90,.018,-dep/2-.0015,.013,m["print"])
 return h+.008
def pouch(p,m,metal):
 w=.100;h=.166
 # Printed flexible grated-cheese bag with volume and crimped upper edge.
 n=20;steps=22
 vs=[];fs=[];uvs=[]
 for side in (-1,1):
  for j in range(steps+1):
   v=j/steps
   for k in range(n+1):
    u=k/n
    x=w*(u-.5);z=.006+v*(h-.017)
    env=max(0,math.sin(math.pi*u)*math.sin(math.pi*v))
    y=side*(.0025+.011*env)+side*.0008*math.sin(u*18+v*16)
    vs.append((x,y,z))
 layer=(steps+1)*(n+1)
 for side in (0,1):
  for j in range(steps):
   for k in range(n):
    a=side*layer+j*(n+1)+k
    f=[a,a+1,a+n+2,a+n+1]
    u=[(k/n,j/steps),((k+1)/n,j/steps),((k+1)/n,(j+1)/steps),(k/n,(j+1)/steps)]
    if side:f.reverse();u.reverse()
    fs.append(f);uvs.append(u)
 modelmesh("Gas-filled flexible grated-cheese pouch",vs,fs,m["print"],uvs,True)
 box("Heat sealed bottom edge",(0,0,.007),(w+.002,.006,.013),metal["foil"],.001)
 box("Heat crimped top edge",(0,0,h-.004),(w+.002,.006,.014),metal["foil"],.001)
 for j in range(11):
  z=h-.010+j*.0012
  box("Physical top crimp ridge "+str(j),(0,-.0033,z),(w+.001,.001,.00035),metal["steel"])
 return h
def round_cheese(p,m,metal):
 r=.056 if p["net"]>=200 else .045
 h=.040
 circle("Soft ripened round cheese wheel",r,h,.023,m["cheese"])
 circle("Printed circular wheel top",r*.89,.0006,.044,m["print"])
 circle_ring("Round paper wrapped perimeter",r-.001,.002,.041,metal["paper"])
 lathe("Branded sideboard wrapping",[(r+.0005,.009),(r+.0005,.036)],m["print"])
 return .047
def butter(p,m,metal):
 w=.108 if p["net"]>=200 else .082
 d=.051 if p["net"]>=200 else .048
 h=.034
 box("Actual chamfered chilled butter block",(0,0,.019),(w-.006,d-.006,.031),m["cheese"],.002)
 box("Gold foil and printed sleeve",(0,0,.019),(w,d,h),metal["paper"],.0018)
 plane_front("Printed front paper wrapper",w-.004,h-.004,-d/2-.0009,.019,m["print"])
 plane_top("Top ingredient brand panel",w-.004,d-.006,.0363,m["print"])
 # folded butter-wrapper creases
 for k in range(3):
  x=-w/2+.006+k*(w-.012)/2
  box("Genuine folded wrapper seam "+str(k),(x,0,.037),(.0006,d-.002,.0007),metal["foil"])
 return h+.007
def spray(p,m,metal):
 h=.220;r=.029
 lathe("Pressurised cream aerosol curved aluminium body",[
  (r*.8,.003),(r,.009),(r,.18),(r*.85,.192),(r*.48,.201)],metal["steel"])
 lathe("Printed full-wrap aerosol artwork",[(r+.0006,.018),(r+.0006,.169)],m["print"])
 circle("Push dispenser nozzle",.012,.010,.204,metal["white"])
 circle("Clear protective nozzle cap",.022,.023,.210,metal["film"])
 circle_ring("Aerosol rolled base",r-.002,.002,.005,metal["steel"])
 return h
def can(p,m,metal):
 h=.116;r=.036
 lathe("Spun steel condensed-milk can",[(r-.004,.004),(r,.009),(r,h-.008),(r-.004,h-.004)],metal["steel"])
 lathe("Paper label on steel can",[(r+.0006,.016),(r+.0006,h-.016)],m["print"])
 for z in (.006,h-.006):
  circle_ring("Seamed steel tin rim",r-.002,.002,z,metal["steel"])
 circle("Recessed tin lid",r-.004,.002,h-.006,metal["steel"])
 circle("Steel base",r-.004,.002,.005,metal["steel"])
 return h
def one_product(p,batch_i,k):
 def hue(h):return tuple(int(h[j:j+2],16)/255 for j in (1,3,5))
 color=hue(p["color"])
 named=p["id"]
 root=bpy.data.objects.new("SKU %02d | %s | %s"%(k+1,p["brand"],p["name"]),None)
 C.collection.objects.link(root)
 root.empty_display_type="CUBE";root.empty_display_size=.021
 root["sku_id"]=named;root["brand"]=p["brand"];root["product_name"]=p["name"]
 root["net_content"]=p["net"];root["package_shape"]=p["shape"]
 root["fictional_game_prop"]=True
 # 5 columns x 4 rows. Spacing is generous so meshes do not overlap.
 root.location=((k%5-2)*.19,(k//5-1.5)*.21,0)
 cream=mat(named+" | soft contents",(.94,.85,.60),rough=.75)
 m={"print":mat("ARTWORK | "+named,color,rough=.60,texture=named+".jpg"),
    "container":mat("PRIMARY PACKAGE | "+named,tuple(min(.99,c*.60+.36) for c in color),rough=.45),
    "plastic":mat("Tinted PET | "+named,tuple(min(.99,c*.22+.64) for c in color),rough=.16,alpha=.83),
    "cheese":cream}
 # Unique, separate reusable materials for each SKU in the emitted GLB.
 metal={"steel":mat("CLEAN | folded tinplate "+named,(.74,.77,.76),metal=.84,rough=.26),
        "foil":mat("ALUMINIUM | print-seal "+named,tuple(min(.98,c*.22+.63) for c in color),metal=.33,rough=.31),
        "white":mat("RIGID POLYPROPYLENE | "+named,(.87,.87,.81),rough=.44),
        "paper":mat("MULTILAYER WRAPPER | "+named,tuple(min(.99,c*.54+.32) for c in color),rough=.65),
        "film":mat("TRANSLUCENT VACUUM FILM | "+named,(.89,.94,.95),rough=.18,alpha=.32),
        "cap":mat("Moulded screw cap | "+named,tuple(min(.99,c*.62+.3) for c in color),rough=.30)}
 prior=set(S.objects)
 shape=p["shape"]
 fn={"carton":carton,"bottle":bottle,"cup":lambda p,m,metal:cup(p,m,metal,False),
     "tub":lambda p,m,metal:cup(p,m,metal,True),
     "wedge":wedge,"tray":tray,"pouch":pouch,"round":round_cheese,
     "brick":butter,"spray":spray,"can":can}[shape]
 height=fn(p,m,metal)
 new=[o for o in S.objects if o not in prior and o.type=="MESH"]
 assert len(new)>=2,(named,len(new))
 # Parent transforms (with identity parent inverse) make it possible to
 # select and reposition any one SKU independently without affecting others.
 for o in new:
  o.parent=root
  o["product_id"]=named
 root["physical_height_m"]=round(height,4)
 return root,len(new)

# (columns, rows, horizontal pitch, depth pitch). These correspond to
# case/shelf stock groups, never mixed products. Front labels face -Y.
STOCK_LAYOUTS={
 "carton":(4,3,.084,.082),  # 12 separate one-litre milk cartons
 "bottle":(3,3,.086,.086),  # 9 separate dairy-drink bottles
 "cup":(4,4,.094,.091),     # 16 individually sealed yoghurt pots
 "tub":(4,3,.105,.102),     # 12 quark/soft cheese tubs
 "wedge":(4,2,.084,.060),   # 8 separately vacuum-sealed cheese wedges
 "tray":(5,2,.117,.087),    # 10 independent cheese trays
 "pouch":(4,3,.109,.033),   # 12 vertical grated-cheese bags
 "round":(4,2,.119,.119),   # 8 round cheese packs
 "brick":(4,3,.114,.060),   # 12 foil-wrapped butter packs
 "spray":(3,2,.075,.075),   # 6 cream aerosol cans
 "can":(4,3,.084,.083),     # 12 milk tins
}
def export_product_stock_batch(p,batch):
    """Export a single SKU as a group of actual duplicate packaged units.

    Units have separate transforms and hierarchy nodes (not one stretched
    mesh). All 5–20 stock packages refer to the same distinct product.
    A copy of each prototype mesh is linked rather than rebuilding 20
    textures and shapes, so the game-ready GLB can share geometry buffers.
    """
    reset()
    root,parts=one_product(p,batch["batch_number"],p["slot"]-1)
    root.name="PRODUCT BATCH | "+p["id"]
    root.location=(0,0,0)
    original=[o for o in S.objects if o.type=="MESH" and o.parent==root]
    assert len(original)==parts and parts>=2,(p["id"],parts,len(original))
    count=int(p["stock_units_per_glb"])
    cols,rows,dx,dy=STOCK_LAYOUTS[p["shape"]]
    assert count==cols*rows,(p["id"],count,cols,rows)
    assert 5<=count<=20
    root["batch_unit_count"]=count
    root["batch_contains_single_sku"]=True
    root["product_sku_id"]=p["id"]
    root["is_retail_stock_batch"]=True
    # Make all unit parents first at the origin, so re-parenting doesn't
    # disturb Blender's existing product-space vertex coordinates.
    parents=[]
    for i in range(count):
        group=bpy.data.objects.new("STOCK_UNIT_%03d | %s"%(i+1,p["id"]),None)
        C.collection.objects.link(group)
        group.parent=root
        group.empty_display_type="PLAIN_AXES"
        group.empty_display_size=.010
        group["unit_index"]=i+1
        group["sku_id"]=p["id"]
        parents.append(group)
    # Unit 001 owns the prototype meshes.
    for ob in original:
        ob.parent=parents[0]
    # Later unit meshes reuse the SAME mesh datablocks and image materials.
    # Modifiers are still independent on object copies where present.
    for group in parents[1:]:
        for ob in original:
            clone=ob.copy()
            clone.name=ob.name+" | "+group.name.split(" | ")[0]
            clone.data=ob.data
            C.collection.objects.link(clone)
            clone.parent=group
            clone["unit_index"]=group["unit_index"]
    # Now arrange units in an evenly spaced, shelf-ready multipack.
    for i,group in enumerate(parents):
        col=i%cols
        row=i//cols
        group.location=((col-(cols-1)/2)*dx,(row-(rows-1)/2)*dy,0)
    C.view_layer.update()
    exported_parts=[o for o in S.objects if o.type=="MESH"]
    assert len(exported_parts)==parts*count,(
        p["id"],len(exported_parts),parts,count)
    # Explicit select only this SKU hierarchy, never another SKU.
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for group in parents:group.select_set(True)
    for ob in exported_parts:ob.select_set(True)
    C.view_layer.objects.active=root
    destination=os.path.join(OUT,"Batch_%02d_%s"%(batch["batch_number"],batch["name"]))
    os.makedirs(destination,exist_ok=True)
    filepath=os.path.join(destination,p["id"]+".glb")
    bpy.ops.export_scene.gltf(filepath=filepath,export_format="GLB",
        use_selection=True,export_materials="EXPORT",export_extras=True,
        export_yup=True,export_apply=True,
        export_draco_mesh_compression_enable=False)
    with open(filepath,"rb") as stream:
        magic,version,total=struct.unpack("<4sII",stream.read(12))
        chunk,typecode=struct.unpack("<I4s",stream.read(8))
        gltf=json.loads(stream.read(chunk))
    assert magic==b"glTF" and version==2 and typecode==b"JSON"
    assert total==os.path.getsize(filepath)
    assert len(gltf.get("meshes",[]))>=2
    assert len(gltf.get("images",[]))>=1
    exported_units=[n for n in gltf["nodes"] if
        n.get("name","").startswith("STOCK_UNIT_")]
    assert len(exported_units)==count,(
        p["id"],len(exported_units),"expected stock units",count)
    assert all(p["id"] in n.get("name","") for n in exported_units)
    assert any(p["id"] in n.get("name","") for n in gltf["nodes"])
    # Each stock unit should actually have at least two child mesh parts.
    idx_map={i:n for i,n in enumerate(gltf["nodes"])}
    for unit in exported_units:
        child_ids=unit.get("children",[])
        assert len(child_ids)>=2,(p["id"],unit["name"],len(child_ids))
        assert sum("mesh" in idx_map[i] for i in child_ids)>=2,(p["id"],unit["name"])
    print("VALIDATED STOCK GLB",p["id"],count,"physical units",
          parts,"mesh parts per unit",
          len(gltf["meshes"]),"gltf meshes",
          len(gltf["images"]),"label textures",total,"bytes",flush=True)

def main():
    assert len(CAT["batches"])==5 and CAT["count"]==100
    for batch in CAT["batches"]:
        assert len(batch["products"])==20
        for p in batch["products"]:
            export_product_stock_batch(p,batch)
        print("FINISHED 20 distinct retail stock GLBs in",batch["name"],flush=True)
    import glob
    files=glob.glob(os.path.join(OUT,"Batch_*","*.glb"))
    assert len(files)==100,(len(files),"expected 100 product batch GLBs")
    print("SUCCESS: 100 DISTINCT DAIRY PRODUCTS; ONE GLB PER SKU;",
          "EACH GLB CONTAINS 5–20 IDENTICAL PHYSICAL RETAIL PACKAGES",flush=True)
if __name__=="__main__":main()
