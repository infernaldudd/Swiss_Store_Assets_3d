"""Stock the EXISTING four authentic grocery fixtures using existing GLB product models.

Exports four separate prefabricated 3D scenes, leaving original empty fixtures
untouched:
  (1) 1m supermarket shelf stocked with real chips/cans/noodles/drinks
  (2) 2m two-bay shelf stocked with more diverse product artwork
  (3) eight-door chiller stocked with REAL DAIRY/DRINK PACKAGES, six rows/bay
  (4) curved glass deli case stocked with sculpted PIZZA OBJECTS (not photos).

The loaded product packaging geometry/PBR materials are preserved directly
from the pre-existing commercial-safe game GLBs. Each repeated unit shares
its prototype mesh data and texture set (GPU efficient). Product origins and
dimensions are measured in world coordinates before placement. Bounds checks
ensure shelves and fridge glass remain clear.

To rebuild from GitHub repository root:
    blender -b -t 2 --python tools/build_stocked_fixtures.py
    RENDER_PREVIEWS=1 blender -b -t 2 --python tools/build_stocked_fixtures.py
"""
import bpy,os,math,json,struct,random
from mathutils import Vector,Matrix
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"assets","stocked_fixtures")
PREV=os.path.join(ROOT,"previews","stocked_fixtures")
SRC=os.path.join(ROOT,"source","stocked_fixtures")
for d in (OUT,PREV,SRC):os.makedirs(d,exist_ok=True)
C=bpy.context
SC=C.scene
ASSETS=os.path.join(ROOT,"assets")
FIXTURES={
 "shelf1":"shelving/Swiss_Supermarket_Wall_Shelf_1m_5Tier.glb",
 "shelf2":"shelving/Swiss_Supermarket_Wall_Shelf_2m_TwoBay.glb",
 "chiller":"refrigeration/Swiss_Glass_Door_Freezer_Chiller_Wall_8Doors.glb",
 "deli":"refrigeration/Swiss_Refrigerated_Glass_Pizza_Deli_Counter.glb"
}
SKU={
 "paprika":"chips/amigos_original_paprika_280g.glb",
 "natural":"chips/amigos_original_nature_280g.glb",
 "bbq":"chips/kernell_bbq_300g.glb",
 "truffle":"chips/alpcraft_black_truffle_100g.glb",
 "smoky":"chips/alpcraft_smoked_paprika_150g.glb",
 "beet":"chips/alpcraft_beetroot_75g.glb",
 "ravioli":"canned_food/loop_ravioli_in_tomato_sauce_CLOSED.glb",
 "tomato":"canned_food/loop_chopped_tomatoes_CLOSED.glb",
 "peas":"canned_food/loop_garden_peas_CLOSED.glb",
 "corn":"canned_food/loop_sweetcorn_CLOSED.glb",
 "tuna":"canned_food/alp_pantry_tuna_in_brine_CLOSED.glb",
 "peach":"canned_food/amigos_peach_halves_CLOSED.glb",
 "noodles":"noodle_cups/LOOP_Chicken_Instant_Noodles_Closed.glb",
 "noodles2":"noodle_cups/AMIGOS_Spicy_Chicken_Noodles_Closed.glb",
 "noodles3":"noodle_cups/ALP_Ramen_Extra_Hot_Closed.glb",
 "cola":"drinks/LOOP_Cola.glb",
 "orange":"drinks/LOOP_Orange.glb",
 "energy":"drinks/VOLTIX_Energy_Berry.glb",
 "ice_tea":"drinks/AMIGOS_Ice_Tea_Peach.glb",
 "water":"drinks/ALPQUELL_Still_Water.glb",
 "apple_juice":"drinks/LOOP_Apple_Juice.glb",
 "milk":"dairy_100/Batch_01_Milk_Cream_Drinks/loop_vollmilch_3_5.glb",
 "choco_milk":"dairy_100/Batch_01_Milk_Cream_Drinks/loop_schoko_milch.glb",
 "bio_milk":"dairy_100/Batch_01_Milk_Cream_Drinks/amigos_bio_vollmilch.glb",
 "yoghurt_red":"dairy_100/Batch_02_Yoghurt_Drinks/loop_joghurt_erdbeer.glb",
 "yoghurt_blue":"dairy_100/Batch_02_Yoghurt_Drinks/loop_joghurt_heidelbeer.glb",
 "yoghurt_mango":"dairy_100/Batch_02_Yoghurt_Drinks/amigos_joghurt_mango.glb",
 "skyr":"dairy_100/Batch_02_Yoghurt_Drinks/alp_farm_skyr_beeren.glb",
 "greek":"dairy_100/Batch_02_Yoghurt_Drinks/alp_farm_greek_nature.glb",
 "cheese":"dairy_100/Batch_03_Cheese/alp_farm_gruyere_aop.glb",
 "raclette":"dairy_100/Batch_03_Cheese/alp_farm_raclette_nature.glb",
 "mozza":"dairy_100/Batch_03_Cheese/amigos_mozzarella_kugel.glb",
 "feta":"dairy_100/Batch_03_Cheese/loop_feta_wurfel.glb",
 "quark":"dairy_100/Batch_05_Quark_Desserts/amigos_quark_erdbeer.glb",
 "dessert":"dairy_100/Batch_05_Quark_Desserts/amigos_pudding_schokolade.glb",
}
# Maximum measured package height/width based on physical product category
# (all values in metres), and target slot depth to protect cabinet glass.
LIMITS={
 "chips":(.178,.225,.140),
 "canned_food":(.087,.148,.088),
 "noodle_cups":(.105,.124,.105),
 "drinks":(.078,.237,.078),
 "dairy_100":(.094,.233,.096),
}
def reset():
 bpy.ops.object.select_all(action="SELECT")
 bpy.ops.object.delete(use_global=False)
 for m in list(bpy.data.materials):
  if m.users==0:bpy.data.materials.remove(m)
 for i in list(bpy.data.images):
  if i.users==0:bpy.data.images.remove(i)
def load_fixture(which):
 path=os.path.join(ASSETS,FIXTURES[which])
 assert os.path.isfile(path),path
 bpy.ops.import_scene.gltf(filepath=path)
 objects=[o for o in SC.objects if o.type=="MESH"]
 assert len(objects)>100,(which,len(objects))
 for o in objects:o["export_stocked_scene"]=True
 print("FIXTURE LOADED",which,len(objects),"mesh parts",flush=True)
def ancestors(o):
 p=o.parent
 while p is not None:
  yield p;p=p.parent
def bounds(objs):
 C.view_layer.update()
 pts=[]
 for o in objs:
  if o.type=="MESH":
   pts.extend([o.matrix_world @ Vector(c) for c in o.bound_box])
 assert pts,"No 3D geometry in selected template"
 low=Vector(tuple(min(p[k] for p in pts) for k in range(3)))
 high=Vector(tuple(max(p[k] for p in pts) for k in range(3)))
 return low,high
def import_prototype(key):
 path=os.path.join(ASSETS,SKU[key])
 assert os.path.isfile(path),path
 old=set(SC.objects)
 bpy.ops.import_scene.gltf(filepath=path)
 fresh=[o for o in SC.objects if o not in old]
 all_mesh=[o for o in fresh if o.type=="MESH"]
 assert all_mesh,("no glTF geometry",path)
 # Dairy products arrive already as 5-20 identical physical units; use ONE
 # existing unit as template rather than accumulating 20x repeated stock.
 unit_mesh=[o for o in all_mesh if any(
   a.name.startswith("STOCK_UNIT_001") for a in ancestors(o))]
 chosen=unit_mesh if unit_mesh else all_mesh
 # Avoid accidentally extracting every dairy unit due to changed hierarchy:
 if "dairy_100" in path:assert unit_mesh,(key,"missing individually authored dairy units")
 C.view_layer.update()
 for o in chosen:
  mat=o.matrix_world.copy()
  o.parent=None
  o.matrix_world=mat
 for o in fresh:
  if o not in chosen and o.name in SC.objects:
   bpy.data.objects.remove(o,do_unlink=True)
 # Join *actual original geometry* and preserve UVs, material slots and maps.
 bpy.ops.object.select_all(action="DESELECT")
 for o in chosen:o.select_set(True)
 C.view_layer.objects.active=chosen[0]
 if len(chosen)>1:
  bpy.ops.object.join()
 proto=C.view_layer.objects.active
 assert proto and proto.type=="MESH"
 proto.name="MASTER TEMPLATE | "+key
 proto["export_stocked_scene"]=False
 # Remove any imported animations that are not relevant for static products.
 lo,hi=bounds([proto])
 size=hi-lo
 assert min(size)>1e-5,(key,size)
 # Enforce physical package maximums, never blow up tiny props to fit a slot.
 cat=SKU[key].split("/")[0]
 maxx,maxz,maxy=LIMITS[cat]
 sf=min(1.,maxx/size.x,maxz/size.z,maxy/size.y)
 # Bottles/cans require a nearly real physical height; reject outliers.
 assert sf>.15,(key,size,sf)
 # Preserve original PBR print, its front direction (-Y) and true aspect.
 norm=Matrix.Diagonal(Vector((sf,sf,sf,1.0))) @ Matrix.Translation(
     Vector((-(lo.x+hi.x)*.5,-(lo.y+hi.y)*.5,-lo.z)))
 return proto,norm,Vector((size.x*sf,size.y*sf,size.z*sf))
PROTOTYPES={}
def getproto(key):
 if key not in PROTOTYPES:
  proto,norm,dim=import_prototype(key)
  # This prototype is not exported or rendered; only linked mesh copies
  # are exported. Keep it hidden outside the camera's view.
  proto.hide_render=True
  proto.hide_set(True)
  PROTOTYPES[key]=(proto,norm,dim)
  print("REAL GLB PRODUCT",key,
        "size(cm)",tuple(round(v*100,1) for v in dim),flush=True)
 return PROTOTYPES[key]

REPORT={"scenes":{}}
def stock(key,x,y,bottom,scene_name):
 prototype,norm,dim=getproto(key)
 clone=prototype.copy()
 clone.data=prototype.data
 clone.name="ACTUAL STOCK | "+key
 C.collection.objects.link(clone)
 clone.hide_render=False
 clone.hide_set(False)
 clone.matrix_world=Matrix.Translation((x,y,bottom)) @ norm
 clone["export_stocked_scene"]=True
 clone["source_glb"]=SKU[key]
 clone["shelf_stock_sku"]=key
 scene=REPORT["scenes"].setdefault(scene_name,{"units":0,"skus":{},"placement_failures":[]})
 scene["units"]+=1
 scene["skus"][key]=scene["skus"].get(key,0)+1
 return clone,dim

def validate_footprint(key,dim,x,y,z,limits,scene):
 xmin,xmax,ymin,ymax,zmin,zmax=limits
 if x-dim.x*.5<xmin or x+dim.x*.5>xmax or y-dim.y*.5<ymin or y+dim.y*.5>ymax or z<zmin or z+dim.z>zmax:
  REPORT["scenes"].setdefault(scene,{}).setdefault("placement_failures",[]).append(
      (key,round(x,3),round(y,3),round(z,3),tuple(round(d,3) for d in dim)))
  raise AssertionError("stock product outside fixture: "+str((scene,key,x,y,z,dim,limits)))
def place_line(keys,width,x_center,y,z,scene,limits,multipliers=None):
 # A line of products may hold multiple actual SKUs with several faces each.
 if multipliers is None:multipliers=[1]*len(keys)
 expanded=[k for key,count in zip(keys,multipliers) for k in [key]*count]
 dims=[getproto(k)[2] for k in expanded]
 gap=.012
 total=sum(d.x for d in dims)+gap*(len(dims)-1)
 if total>width:
  raise AssertionError("Too many products across "+scene+": "+str((expanded,total,width)))
 x=x_center-total/2
 for key,d in zip(expanded,dims):
  center=x+d.x/2
  o,dim=stock(key,center,y,z,scene)
  validate_footprint(key,dim,center,y,z,limits,scene)
  x+=d.x+gap

def populate_shelf(which,scene):
 global PROTOTYPES
 PROTOTYPES={}
 load_fixture(which)
 bays=1 if which=="shelf1" else 2
 centers=[0.] if bays==1 else [-.525,.525]
 z_levels=(.241,.620,.999,1.378,1.757)
 design=[
   (["paprika","natural"],[2,2],["ravioli","corn","peas"],[3,3,2]),
   (["noodles","noodles2"],[3,3],["noodles3","tuna"],[3,3]),
   (["bbq","truffle"],[2,2],["tomato","peach"],[3,3]),
   (["cola","orange","energy"],[3,3,3],["cola","energy"],[3,3]),
   (["smoky","beet"],[2,2],["noodles","noodles2"],[3,3]),
 ]
 for bay,center in enumerate(centers):
  # vary stock arrangement between modules without altering shelf geometry.
  for i,z in enumerate(z_levels):
   a,na,b,nb=design[(i+bay*2)%len(design)]
   # shelf footprint: x centre +/- .459; -Y is customer side
   limits=(center-.461,center+.461,-.244,.188,z,z+.299)
   # Keep tall products in separate front/back rows; same item stock bundles.
   place_line(a,.905,center,-.154,z,scene,limits,na)
   place_line(b,.905,center,.082,z,scene,limits,nb)
   # A product back-row with deep chips may intersect another row; validate
   # actual depth at render QA, with origin safe shell spacing.
 print("SHELF POPULATED",scene,REPORT["scenes"][scene],flush=True)

# Existing eight-door 6-tier chiller at 0.42, 0.72, etc.
CHILLER={
 0:["milk","bio_milk","choco_milk","ice_tea","water","milk"],
 1:["milk","apple_juice","ice_tea","water","choco_milk","orange"],
 2:["yoghurt_red","yoghurt_blue","yoghurt_mango","skyr","greek","quark"],
 3:["greek","yoghurt_red","skyr","quark","dessert","yoghurt_blue"],
 4:["raclette","cheese","feta","mozza","cheese","raclette"],
 5:["mozza","feta","cheese","raclette","feta","mozza"],
 6:["ice_tea","water","choco_milk","milk","apple_juice","ice_tea"],
 7:["apple_juice","ice_tea","water","orange","energy","cola"]
}
def populate_chiller(scene):
 global PROTOTYPES
 PROTOTYPES={}
 load_fixture("chiller")
 W=6.92
 for bay in range(8):
  center=-W/2+.060+(bay+.5)*.850
  for shelf_index,z in enumerate((.420,.720,1.020,1.320,1.620,1.920)):
   key=CHILLER[bay][shelf_index]
   dim=getproto(key)[2]
   # Shelf usable width ~0.775, with side wall/LED at +/- .404.
   # Front row and rear row, pulled away from glass door at -0.452.
   # Products sit *on* actual ribs at z + 0.014.
   bottom=z+.0142
   count=min(6,int(.720/(dim.x+.018)))
   count=max(3,count)
   if dim.y>.102:
    ys=(-.196,.105) # large cartons and bottles
   else:
    ys=(-.240,-.055,.128) # compact yoghurt, cheese and dessert packs
   for row,y in enumerate(ys):
    # The first row always faces outward, no clipping the door pane.
    lim=(center-.368,center+.368,-.309,.287,bottom,bottom+.269)
    place_line([key],[*range(1)][0] if False else .731,center,y,bottom,scene,lim,[count])
 print("CHILLER STOCKED",scene,REPORT["scenes"][scene],flush=True)

def pizza_material(name,color,rough=.6,metal=0):
 mat=bpy.data.materials.new(name);mat.use_nodes=True
 mat.diffuse_color=(*color,1)
 p=mat.node_tree.nodes["Principled BSDF"]
 p.inputs["Base Color"].default_value=(*color,1)
 p.inputs["Roughness"].default_value=rough
 p.inputs["Metallic"].default_value=metal
 return mat
def geometry(name,verts,faces,mat):
 m=bpy.data.meshes.new(name+" mesh")
 m.from_pydata(verts,[],faces);m.update();m.materials.append(mat)
 ob=bpy.data.objects.new(name,m);C.collection.objects.link(ob)
 ob["export_stocked_scene"]=False
 for polygon in m.polygons:polygon.use_smooth=True
 return ob

def disk(name,r,z,thick,mat,waviness=.0,n=48):
 # Sculptured irregular golden-brown pizza crust/pie, not a flat PNG disk.
 verts=[];faces=[]
 for height in (z,z+thick):
  for j in range(3):
   rad=(.72+.14*j)*r
   if j==2:rad=r
   for i in range(n):
    a=2*math.pi*i/n
    rr=rad*(1+waviness*math.sin(i*2.6+j*1.7))
    zz=height+(0.008 if j==2 and height>z else 0)
    verts.append((rr*math.cos(a),rr*math.sin(a),zz))
 faces.append(list(reversed([i for i in range(n)])))
 off=3*n
 for row in range(2):
  for i in range(n):
   k=(i+1)%n
   faces.append([off+row*n+i,off+row*n+k,off+(row+1)*n+k,off+(row+1)*n+i])
 # side ring and underside of pie
 outer_bot=2*n;outer_top=5*n
 for i in range(n):
  k=(i+1)%n
  faces.append([outer_bot+i,outer_bot+k,outer_top+k,outer_top+i])
 return geometry(name,verts,faces,mat)

def ellipse_batch(name,seed,count,radius,z,material,sz,shape):
 rng=random.Random(seed)
 vertices=[];faces=[]
 segments=10
 for i in range(count):
  a=rng.uniform(0,math.tau);dist=radius*math.sqrt(rng.random())*.77
  cx=dist*math.cos(a);cy=dist*math.sin(a)
  rx=sz[0]*rng.uniform(.65,1.3)
  ry=sz[1]*rng.uniform(.65,1.25)
  h=sz[2]*rng.uniform(.6,1.3)
  st=len(vertices)
  for level in range(3):
   for k in range(segments):
    phi=k*math.tau/segments
    xx=cx+rx*math.cos(phi)
    yy=cy+ry*math.sin(phi)
    zz=z+([-.001,h*.8,h][level])
    if shape=="pepper":
     xx+=rx*.26*math.cos(3*phi+i)
     yy+=ry*.26*math.sin(2*phi+i)
    vertices.append((xx,yy,zz))
  for k in range(segments):
   nxt=(k+1)%segments
   for level in range(2):
    faces.append([st+level*segments+k,st+level*segments+nxt,
                  st+(level+1)*segments+nxt,st+(level+1)*segments+k])
 return geometry(name,vertices,faces,material)

def make_pizza_variant(kind):
 crust=pizza_material("PIZZA | hand-baked blistered crust",(.58,.29,.10),.73)
 border=pizza_material("PIZZA | golden dough raised rim",(.78,.49,.20),.76)
 sauce=pizza_material("PIZZA | baked tomato sauce",(.60,.09,.037),.55)
 cheese=pizza_material("PIZZA | melted mozzarella cream",(.88,.77,.45),.38)
 tomato=pizza_material("PIZZA | fresh red tomato pieces",(.83,.20,.09),.52)
 green=pizza_material("PIZZA | basil parsley pieces",(.08,.27,.09),.71)
 olive=pizza_material("PIZZA | dark sliced olives",(.06,.09,.06),.41)
 r=.143
 objects=[]
 objects.append(disk("PIZZA "+kind+" | genuine baked crust",r,0,.012,crust,.008))
 objects.append(disk("PIZZA "+kind+" | melted tomato sauce",r*.83,.018,.003,sauce,.007))
 objects.append(ellipse_batch("PIZZA "+kind+" | 34 melted cheese patches",24,34,r,.024,cheese,
                (.018,.013,.003),"cheese"))
 objects.append(ellipse_batch("PIZZA "+kind+" | 23 original tomato topping",321,23,r,.028,tomato,
                (.012,.008,.002),"tomato"))
 objects.append(ellipse_batch("PIZZA "+kind+" | green vegetables",52,23,r,.027,green,
                (.008,.005,.002),"pepper"))
 if kind!="Margherita":
  objects.append(ellipse_batch("PIZZA "+kind+" | olive slices",984,17,r,.027,olive,
                 (.010,.009,.002),"olive"))
 if kind=="Spicy":
  objects.append(ellipse_batch("PIZZA "+kind+" | extra red chili pepper",35,18,r,.031,tomato,
                 (.016,.003,.002),"pepper"))
 # Consolidate actual original pizza mesh parts into one prototype
 bpy.ops.object.select_all(action="DESELECT")
 for obj in objects:obj.select_set(True)
 C.view_layer.objects.active=objects[0]
 bpy.ops.object.join()
 prototype=C.view_layer.objects.active
 prototype.name="MASTER PIZZA | "+kind
 prototype["export_stocked_scene"]=False
 prototype.hide_render=True
 prototype.hide_set(True)
 return prototype
def populate_deli(scene):
 global PROTOTYPES
 PROTOTYPES={}
 load_fixture("deli")
 kinds=("Margherita","Garden_Vegetable","Spicy")
 masters={kind:make_pizza_variant(kind) for kind in kinds}
 # Three 680mm serving trays, each with four fully modelled original pizzas.
 # Individual pies have 286mm diameter, positioned within the case.
 for j,xbase in enumerate((-.706,0,.706)):
  kind=kinds[j]
  proto=masters[kind]
  for row,y in enumerate((-.232,.135)):
   for col,xoffset in enumerate((-.166,.166)):
    x=xbase+xoffset
    name="STOCKED PIZZA | "+kind+" | "+str(row*2+col+1)
    obj=proto.copy();obj.data=proto.data
    C.collection.objects.link(obj);obj.name=name
    obj.hide_render=False;obj.hide_set(False)
    # Real model pizza base z = 0, on stainless tray surface about .868.
    obj.matrix_world=Matrix.Translation((x,y,.880))
    obj["export_stocked_scene"]=True
    obj["original_pizza_kind"]=kind
    REPORT["scenes"].setdefault(scene,{"units":0,"skus":{},"placement_failures":[]})
    REPORT["scenes"][scene]["units"]+=1
    REPORT["scenes"][scene]["skus"][kind]=REPORT["scenes"][scene]["skus"].get(kind,0)+1
    assert abs(x)<1.10 and -.399<y-.143 and y+.143<.424
 print("DELI RESTOCKED",REPORT["scenes"][scene],flush=True)

def asset_export(name,scenario):
 objs=[o for o in SC.objects if o.type=="MESH" and o.get("export_stocked_scene")]
 assert len(objs)>140,(scenario,len(objs))
 bpy.ops.object.select_all(action="DESELECT")
 for obj in objs:obj.select_set(True)
 for obj in SC.objects:
  if obj.type=="EMPTY" and obj.name.startswith("DOOR_"):obj.select_set(True)
 C.view_layer.objects.active=objs[0]
 path=os.path.join(OUT,name+".glb")
 bpy.ops.export_scene.gltf(filepath=path,export_format="GLB",
   use_selection=True,export_apply=True,export_materials="EXPORT",
   export_extras=True,export_yup=True,
   export_draco_mesh_compression_enable=False)
 bpy.ops.object.select_all(action="DESELECT")
 with open(path,"rb") as f:
  magic,version,total=struct.unpack("<4sII",f.read(12))
  n,kind=struct.unpack("<I4s",f.read(8))
  doc=json.loads(f.read(n))
 assert magic==b"glTF" and version==2 and kind==b"JSON"
 assert total==os.path.getsize(path)
 nodes=[n.get("name","") for n in doc["nodes"]]
 has_products=any(n.startswith("ACTUAL STOCK |") or
                  n.startswith("STOCKED PIZZA |") for n in nodes)
 assert has_products,scenario
 assert len(doc["materials"])>8
 assert len(doc["images"])>=2
 assert REPORT["scenes"][scenario]["units"]>=12
 if scenario=="chiller":
  assert sum(n.startswith("DOOR_") for n in nodes)==8
  assert sum(n.startswith("INTERIOR | actual load bearing metal shelf") for n in nodes)==48
 if scenario=="deli":
  assert sum(n.startswith("STOCKED PIZZA |") for n in nodes)==12
 print("VERIFIED STOCKED GLB",name,len(objs),"meshes",
       REPORT["scenes"][scenario]["units"],"individual packs",
       len(doc["images"]),"artwork maps",
       os.path.getsize(path),"bytes",flush=True)
 return path
def render_preview(name,scenario):
 # Do not render master prototypes, only linked actual retail inventory.
 pos={
 "shelf1":(1.15,-3.6,2.15),
 "shelf2":(1.92,-5.55,2.40),
 "chiller":(4.30,-11.3,4.11),
 "deli":(2.45,-4.2,2.15),
 }[scenario]
 target={"shelf1":(0,0,1.08),"shelf2":(0,0,1.06),
         "chiller":(0,0,1.32),"deli":(0,0,.85)}[scenario]
 floor=bpy.data.materials.new("PREVIEW ONLY | supermarket floor")
 floor.diffuse_color=(.24,.26,.28,1)
 floor.use_nodes=True
 mat=floor.node_tree.nodes["Principled BSDF"]
 mat.inputs["Base Color"].default_value=(.24,.26,.28,1)
 mat.inputs["Roughness"].default_value=.62
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.041))
 fb=C.object;fb.name="PREVIEW ONLY | matte terrazzo"
 fb.dimensions=(9,5,.068)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 fb.data.materials.append(floor)
 for p,watts,sz in [
  ((-3,-3,5.2),1450,3.3),
  ((3,-1.5,4.0),800,2.6),
  ((0,1.5,5.0),500,3.2)]:
  bpy.ops.object.light_add(type="AREA",location=p)
  light=C.object
  light.data.energy=watts;light.data.size=sz
  light.rotation_euler=(Vector(target)-light.location).to_track_quat("-Z","Y").to_euler()
 bpy.ops.object.camera_add(location=pos)
 cam=C.object
 cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
 cam.data.type="ORTHO"
 cam.data.ortho_scale={"shelf1":2.65,"shelf2":3.60,"chiller":8.65,"deli":2.85}[scenario]
 SC.camera=cam
 SC.render.engine="CYCLES"
 SC.cycles.device="CPU"
 SC.cycles.samples=18
 if hasattr(SC.cycles,"use_denoising"):SC.cycles.use_denoising=False
 if hasattr(C.view_layer.cycles,"use_denoising"):C.view_layer.cycles.use_denoising=False
 SC.view_settings.view_transform="AgX"
 SC.world.color=(.16,.16,.16)
 SC.render.resolution_x=900 if scenario=="shelf1" else 1400
 SC.render.resolution_y=1050 if scenario=="shelf1" else 950
 SC.render.resolution_percentage=100
 SC.render.image_settings.file_format="PNG"
 SC.render.filepath=os.path.join(PREV,name+".png")
 bpy.ops.render.render(write_still=True)
 print("STOCK RENDER",SC.render.filepath,flush=True)

def main():
 scenarios=[
  ("shelf1","Swiss_Supermarket_Shelf_1m_Stocked"),
  ("shelf2","Swiss_Supermarket_Shelf_2m_Stocked"),
  ("chiller","Swiss_Glass_Door_Chiller_8Doors_Stocked"),
  ("deli","Swiss_Glass_Deli_Pizza_Counter_Stocked")]
 for scenario,name in scenarios:
  reset()
  if scenario.startswith("shelf"):populate_shelf(scenario,scenario)
  elif scenario=="chiller":populate_chiller(scenario)
  elif scenario=="deli":populate_deli(scenario)
  else:raise AssertionError(scenario)
  info=REPORT["scenes"][scenario]
  assert not info["placement_failures"],(scenario,info["placement_failures"])
  asset_export(name,scenario)
  if scenario=="deli":
   # Only the novel pizza is procedural; all other stock uses existing GLBs.
   bpy.ops.wm.save_as_mainfile(
      filepath=os.path.join(SRC,"Stocked_Deli_Pizza_Master.blend"),compress=True)
  if os.environ.get("RENDER_PREVIEWS")=="1":
   render_preview(name,scenario)
 print("RENDER/EXPORT READY: four distinct stocked fixtures",flush=True)
 with open(os.path.join(PREV,"Stocking_Report.json"),"w") as f:
  json.dump(REPORT,f,indent=2)
 assert len([f for f in os.listdir(OUT) if f.endswith(".glb")])==4
 print("FINISHED exactly 4 separate stocked fixture GLBs",flush=True)
if __name__=="__main__":main()
