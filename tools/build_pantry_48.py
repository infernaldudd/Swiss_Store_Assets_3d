"""Generate 48 fully textured independent glTF binary grocery product stock-batches.

Every distinct product is ONE GLB containing a physical 6–12 identical-unit
retail batch, in separately selectable scene nodes. 48 different products,
not 48 colours of the same cardboard box. Original 2K printed artwork.
Game-ready materials: varnished print, paper fibre, metal foil and lids,
clear plastic, and textured glass. Blender 3.4+.

Run:
 /usr/bin/python3 tools/generate_surface_finish_maps.py
 /usr/bin/python3 tools/generate_pantry_48_art.py
 blender -b -t 2 --python tools/build_pantry_48.py
"""
import bpy,math,os,json,struct,random
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
CAT=json.load(open(os.path.join(ROOT,"catalog","pantry_48.json")))
OUT=os.path.join(ROOT,"assets","pantry_48")
ART=os.path.join(ROOT,"textures","pantry_48")
FIN=os.path.join(ROOT,"textures","surface_finishes")
os.makedirs(OUT,exist_ok=True)
C=bpy.context
S=C.scene
RAD=math.tau
SIZES={
 "pasta_bag":(.127,.063,.229),
 "rice_bag":(.143,.086,.225),
 "paper_box":(.146,.065,.207),
 "standup_pouch":(.132,.071,.225),
 "cereal_box":(.189,.073,.279),
 "paper_sack":(.141,.078,.234),
 "coffee_brick":(.113,.069,.185),
 "valve_pouch":(.141,.080,.227),
 "coffee_tin":(.083,.083,.161),
 "tea_box":(.124,.061,.111),
 "choc_bar":(.170,.022,.095),
 "cookie_box":(.192,.073,.155),
 "flowpack":(.182,.073,.108),
 "glass_jar":(.087,.087,.144),
 "squeeze":(.069,.069,.187),
 "bottle":(.079,.079,.250)}
GRID={
 "pasta_bag":(4,2),"rice_bag":(4,2),"paper_box":(4,2),
 "standup_pouch":(4,2),"cereal_box":(3,2),"paper_sack":(4,2),
 "coffee_brick":(3,3),"valve_pouch":(4,2),"coffee_tin":(3,3),
 "tea_box":(4,3),"choc_bar":(4,3),"cookie_box":(4,2),
 "flowpack":(3,3),"glass_jar":(4,2),"squeeze":(3,3),
 "bottle":(3,3)}
BASE={
 "wheat":(0.75,.53,.24),"tomato":(.65,.21,.14),"gold":(.70,.50,.20),
 "mint":(.29,.51,.37),"cream":(.80,.75,.59),"red":(.65,.21,.23),
 "teal":(.16,.44,.49),"sand":(.62,.47,.30),"rose":(.68,.34,.42),
 "blue":(.30,.49,.67),"yellow":(.83,.68,.25),"brown":(.42,.25,.17),
 "black":(.15,.16,.18),"orange":(.77,.36,.18),"olive":(.31,.42,.19)}

def clear():
 bpy.ops.object.select_all(action="SELECT")
 bpy.ops.object.delete(use_global=False)
 for mat in list(bpy.data.materials):
  if mat.users==0:bpy.data.materials.remove(mat)
 for img in list(bpy.data.images):
  if img.users==0:bpy.data.images.remove(img)

def material(name,c,rough=.45,metal=0,image=None,finish=None,alpha=1.):
 ma=bpy.data.materials.new(name);ma.use_nodes=True
 ma.diffuse_color=(*c,alpha)
 p=ma.node_tree.nodes.get("Principled BSDF")
 p.inputs["Base Color"].default_value=(*c,1.)
 p.inputs["Metallic"].default_value=metal
 p.inputs["Roughness"].default_value=rough
 p.inputs["Alpha"].default_value=alpha
 if alpha<1.:ma.blend_method="BLEND"
 if image or finish:
  for path,output,noncol in (
      (os.path.join(ART,image) if image else None,"Base Color",False),
      (os.path.join(FIN,finish+".png") if finish else None,"Roughness",True)):
   if not path:continue
   assert os.path.isfile(path),path
   img=bpy.data.images.load(path,check_existing=True)
   if noncol:img.colorspace_settings.name="Non-Color"
   img.pack()
   tex=ma.node_tree.nodes.new("ShaderNodeTexImage")
   tex.image=img
   tex.interpolation="Linear"
   ma.node_tree.links.new(tex.outputs["Color"],p.inputs[output])
 return ma

def mesh(name,v,faces,ma,uv=None,smooth=False):
 me=bpy.data.meshes.new(name+"_GEO")
 me.from_pydata(v,[],faces);me.update()
 me.materials.append(ma)
 if uv is not None:
  assert len(faces)==len(uv),(name,len(faces),len(uv))
  lay=me.uv_layers.new(name="SKU original 2K print UV0")
  for polygon,tc in zip(me.polygons,uv):
   assert len(polygon.loop_indices)==len(tc),(name,len(polygon.loop_indices),len(tc))
   for loop,coord in zip(polygon.loop_indices,tc):
    lay.data[loop].uv=coord
 ob=bpy.data.objects.new(name,me);C.collection.objects.link(ob)
 for poly in me.polygons:poly.use_smooth=smooth
 return ob

def cube(name,center,dims,ma,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=center)
 ob=C.object
 ob.name=name
 ob.dimensions=dims
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 ob.data.materials.append(ma)
 if bevel:
  b=ob.modifiers.new("Subtle fabrication radius","BEVEL")
  b.width=bevel;b.segments=3
 return ob

def printed_box(name,w,d,h,ink,side,flap,bevel=.002):
 # Six printable faces, front dedicated to central U.26-.74 part of atlas.
 x=w/2;y=d/2
 v=[(-x,-y,0),(x,-y,0),(x,-y,h),(-x,-y,h),
    (-x,y,0),(x,y,0),(x,y,h),(-x,y,h)]
 fs=[[0,1,2,3],[5,4,7,6],[4,0,3,7],[1,5,6,2],[3,2,6,7],[4,5,1,0]]
 uvs=[[(.265,.04),(.735,.04),(.735,.96),(.265,.96)],
      [(.76,.04),(.99,.04),(.99,.96),(.76,.96)],
      [(.02,.04),(.24,.04),(.24,.96),(.02,.96)],
      [(.76,.05),(.99,.05),(.99,.95),(.76,.95)],
      [(.28,.85),(.72,.85),(.72,.97),(.28,.97)],
      [(.28,.03),(.72,.03),(.72,.13),(.28,.13)]]
 ob=mesh(name+" | original 2K full six-face print",v,fs,ink,uvs)
 cube(name+" | folded top heat-sealed tab",(0,0,h+.0015),
       (w-.004,d-.003,.004),flap,.0011)
 # Physically narrow crimp crease and taped opening edges.
 cube(name+" | factory side glue seam",(w/2-.001,y-.005,h*.50),
       (.0016,.009,h*.94),side,.0005)
 cube(name+" | lower crease",(0,-y-.0005,.004),(w-.008,.0018,.005),side,.0005)
 return [ob]

def pouch(name,w,d,h,ink,edge,smooth=True,sealed=True):
 # Physically inflated package: different x-z curvature on both faces,
 # zig-zag edge wrinkles and nonzero depth. U maps to centre-print design.
 nx=12;nz=15
 faces=[];uv=[];v=[]
 for face in (0,1):
  for j in range(nz+1):
   z=h*j/nz
   for i in range(nx+1):
    x=w*(i/nx-.5)
    asym=.006*math.sin(1.2+j*1.55+i*2.35)*math.sin(math.pi*j/nz)
    balloon=math.sin(math.pi*i/nx)*math.sin(math.pi*j/nz)
    y=((-.5 if face==0 else .5)*d+
       (-1 if face==0 else 1)*(d*.08*balloon+asym*.16))
    if sealed and j in (0,1,nz-1,nz):y=(-.5 if face==0 else .5)*(d*.47)
    v.append((x,y,z+.0018*balloon))
   if j:
    for i in range(nx):
     k=face*(nx+1)*(nz+1)+(j-1)*(nx+1)+i
     fs=[k,k+1,k+nx+2,k+nx+1]
     if face:fs=list(reversed(fs))
     faces.append(fs)
     v0=(j-1)/nz;v1=j/nz
     if not face:
      uv.append([(.27+.46*i/nx,v0),(.27+.46*(i+1)/nx,v0),
                 (.27+.46*(i+1)/nx,v1),(.27+.46*i/nx,v1)])
     else:
      uv.append([(.78+.2*i/nx,v0),(.78+.2*(i+1)/nx,v0),
                 (.78+.2*(i+1)/nx,v1),(.78+.2*i/nx,v1)][::-1])
 # Sew left/right/top/bottom together, essential to avoid useless holes.
 count=(nx+1)*(nz+1)
 def idx(face,i,j):return face*count+j*(nx+1)+i
 for i in range(nx):
  for j in (0,nz):
   ff=[idx(0,i,j),idx(0,i+1,j),idx(1,i+1,j),idx(1,i,j)]
   faces.append(ff if j==0 else ff[::-1])
   uv.append([(.02,0),(.22,0),(.22,1),(.02,1)])
 for j in range(nz):
  for i in (0,nx):
   ff=[idx(0,i,j),idx(0,i,j+1),idx(1,i,j+1),idx(1,i)]
   faces.append(ff if i==nx else ff[::-1])
   uv.append([(.02,0),(.22,0),(.22,1),(.02,1)])
 a=mesh(name+" | inflated wrinkled sealed physical bag",v,faces,ink,uv,True)
 for z,sz in ((.006,.012),(h-.006,.012)):
  # Sealed cross-seam is foil material separate from print, with pressed ribs
  cube(name+" | realistic folded end seam",(0,0,z),(w+.002,d*.64,sz),edge,.0017)
  for r in range(13):
   x=-w*.48+r*w*.96/12
   cube(name+" | crimp rib",(x,-d*.33,z),
        (.0012,.0013,sz*.62),edge,.0002)
 cube(name+" | rear central fusion seal",(0,d*.51,h*.5),
      (.005,d*.030,h*.78),edge,.0006)
 return a

def lathe(name,profile,ma,seg=72,uv_band=(0,1)):
 v=[];faces=[];uv=[]
 for j,(r,z) in enumerate(profile):
  for i in range(seg+1):
   u=i/seg
   angle=RAD*(u-.75) # U=.5 on the shopper-facing -Y side
   v.append((r*math.cos(angle),r*math.sin(angle),z))
 for j in range(len(profile)-1):
  for i in range(seg):
   k=j*(seg+1)+i
   faces.append([k,k+1,k+seg+2,k+seg+1])
   uv.append([(uv_band[0]+(uv_band[1]-uv_band[0])*i/seg,j/(len(profile)-1)),
              (uv_band[0]+(uv_band[1]-uv_band[0])*(i+1)/seg,j/(len(profile)-1)),
              (uv_band[0]+(uv_band[1]-uv_band[0])*(i+1)/seg,(j+1)/(len(profile)-1)),
              (uv_band[0]+(uv_band[1]-uv_band[0])*i/seg,(j+1)/(len(profile)-1))])
 return mesh(name,v,faces,ma,uv,True)
def disc(name,r,z,ma,n=64):
 v=[(0,0,z)]
 for i in range(n):
  a=i*RAD/n;v.append((r*math.cos(a),r*math.sin(a),z))
 faces=[[0,i+1,(i+1)%n+1] for i in range(n)]
 return mesh(name,v,faces,ma)
def torus(name,major,minor,z,ma):
 n=56;k=8;v=[];fs=[]
 for aidx in range(n):
  a=RAD*aidx/n
  for bidx in range(k):
   b=RAD*bidx/k;r=major+minor*math.cos(b)
   v.append((r*math.cos(a),r*math.sin(a),z+minor*math.sin(b)))
 for i in range(n):
  for j in range(k):
   fs.append([i*k+j,((i+1)%n)*k+j,((i+1)%n)*k+(j+1)%k,i*k+(j+1)%k])
 return mesh(name,v,fs,ma,smooth=True)

def round_container(p,ink,M):
 form=p["form"];w,d,h=SIZES[form];r=w*.48
 if form in ("glass_jar","coffee_tin"):
  glass=form=="glass_jar"
  body=material("actual tinted glass cylinder" if glass else "lacquered metal tin",
      (.72,.80,.78) if glass else (.47,.5,.51),.12 if glass else .27,
      0 if glass else .67,alpha=.25 if glass else 1.)
  if glass:
   content=material("real jar content | "+p["name"],BASE[p["palette"]],.32,.0)
   lathe("FOOD CONTENT | filling inside glass",[(r*.77,.006),
      (r*.84,.011),(r*.84,h*.76),(r*.79,h*.80)],content,56)
  lathe("CONTAINER | shaped cylindrical body",
      [(r*.86,.004),(r*.94,.009),(r,h*.15),
       (r,h*.84),(r*.93,h*.92),(r*.83,h*.94)],body)
  lathe("LABEL | 2K printed cylindrical wrap",[(r+.00035,.021),
      (r+.00035,h*.80)],ink,72)
  top=h*.935
  disc("LID | actual cap pressed top",r*.925,top+.004,M["metal"])
  torus("LID | rolled cap rim",r*.94,.002,top,M["metal"])
  for i in range(36):
   a=i*RAD/36
   ob=cube("LID | tiny rib knurl",((r*.948)*math.cos(a),
        (r*.948)*math.sin(a),top-.006),(.0015,.0015,.012),M["metal"],.0003)
  disc("BOTTOM | closed sealed base",r*.83,.003,M["metal"])
 elif form=="squeeze":
  plastic=material("SQUEEZE | coloured semi-gloss polymer",BASE[p["palette"]],.21)
  lathe("SQUEEZE | tapered flexible body",[(r*.66,.017),(r*.90,.037),
      (r,.11),(r*.78,h-.018),(r*.67,h-.005)],plastic)
  lathe("SQUEEZE | true conforming printed label",[(r*.91,.044),
      (r*.98,.105),(r*.78,h-.029)],ink)
  lathe("SQUEEZE | flip-top cap",[(r*.68,.001),(r*.69,.019)],M["polymer"])
  disc("SQUEEZE | lid disc",r*.69,.001,M["polymer"])
  cube("SQUEEZE | moulded hinge edge",(0,-r*.66,.013),
       (.013,.005,.013),M["polymer"],.001)
 elif form=="bottle":
  r=w*.43
  water=material("BOTTLE | amber/green transparent food-safe body",
     (.48,.62,.51),.15,0,alpha=.33)
  fill=material("BOTTLE | content shade",BASE[p["palette"]],.25,0)
  lathe("BOTTLE | physically shaped vessel",
       [(r*.73,.005),(r*.96,.012),(r,.035),
        (r,h*.72),(r*.80,h*.80),(r*.44,h*.86),(r*.39,h-.016)],water)
  lathe("BOTTLE | liquid volume inside",
       [(r*.65,.007),(r*.83,.017),(r*.86,.05),(r*.83,h*.63)],fill,56)
  lathe("BOTTLE | cylindrical ink paper label",
       [(r+.0005,.058),(r+.0005,h*.68)],ink)
  lathe("BOTTLE | tamper closure",[(r*.42,h-.019),
       (r*.42,h-.002)],M["metal"])
  disc("BOTTLE | opaque screw cap lid",r*.43,h-.001,M["metal"])
  torus("BOTTLE | raised embossed glass lip",r*.41,.0018,h-.020,M["glass"])
 else:raise AssertionError(form)

def build(p):
 form=p["form"]
 w,d,h=SIZES[form]
 finish=("Matte_Paper_Roughness" if form in
 ("paper_box","cereal_box","tea_box","cookie_box","paper_sack")
 else "Flex_Foil_Roughness" if form in
 ("pasta_bag","rice_bag","standup_pouch","coffee_brick","valve_pouch","choc_bar","flowpack")
 else "Glossy_Laminated_Print_Roughness")
 ink=material("ORIGINAL 2K BRAND INK | "+p["id"],BASE[p["palette"]],
      .31,.10 if form in ("choc_bar","coffee_brick","valve_pouch") else .015,
      image=p["id"]+"_2K.jpg",finish=finish)
 M={
  "metal":material("PBR | stamped satin cap / foil metallic rim",(.59,.64,.66),.29,.78,finish="Brushed_Steel_Roughness"),
  "foil":material("PBR | asymmetric laminated foil crimp",(.74,.71,.63),.27,.33,finish="Flex_Foil_Roughness"),
  "paper":material("PBR | fibrous folded paper and carton edge",(.83,.82,.73),.73,.0,finish="Matte_Paper_Roughness"),
  "polymer":material("PBR | moulded food-pack closure",(.84,.84,.80),.23,.02,finish="SemiGloss_Vinyl_Roughness"),
  "glass":material("PBR | restrained food-grade glass highlights",(.79,.90,.91),.16,.0,alpha=.22)}
 if form in ("paper_box","cereal_box","tea_box","cookie_box"):
  printed_box("FOLDED CARTON",w,d,h,ink,M["paper"],M["paper"])
 elif form in ("pasta_bag","rice_bag","standup_pouch","coffee_brick",
             "valve_pouch","paper_sack","choc_bar","flowpack"):
  pouch("PACKED PRODUCT",w,d,h,ink,M["paper"] if form=="paper_sack" else M["foil"])
  if form=="valve_pouch":
   # actual one-way coffee valve, not a floating printed disc
   r=.008
   lathe("COFFEE | extruded one-way aromalock valve",
         [(r,.0),(r,h*.055)],M["polymer"],36)
   disc("COFFEE | vent cap",r,h*.055,M["metal"],36)
  if form=="choc_bar":
   for k in range(6):
    x=-w*.42+k*w*.168
    cube("CHOCOLATE | fine pressed foil panel rib",
         (x,-d*.51,h*.50),(.0013,.0010,h*.79),M["foil"],.0003)
 elif form in ("glass_jar","squeeze","bottle","coffee_tin"):
  round_container(p,ink,M)
 else:raise AssertionError("Unimplemented packaging "+form)
 return [o for o in S.objects if o.type=="MESH"]

def export_stock(p,group):
 clear()
 parts=build(p)
 assert len(parts)>=2,(p["id"],len(parts))
 root=bpy.data.objects.new("SKU BATCH | "+p["id"],None)
 C.collection.objects.link(root)
 root["SKU"]=p["id"]
 root["fictional_brand"]=p["brand"]
 root["stock_units"]=p["units_per_glb"]
 root["package_type"]=p["form"]
 qty=p["units_per_glb"]
 cols,rows=GRID[p["form"]]
 assert cols*rows==qty and 5<=qty<=20,(p["id"],qty,cols,rows)
 w,d,h=SIZES[p["form"]]
 # Separate instance hierarchy while reusing actual geometric mesh data.
 for i in range(qty):
  g=bpy.data.objects.new("RETAIL_UNIT_%03d | "%(i+1)+p["id"],None)
  C.collection.objects.link(g)
  g.parent=root;g["SKU"]=p["id"];g["unit_index"]=i+1
  g.location=((i%cols-(cols-1)/2)*(w+.013),
              (i//cols-(rows-1)/2)*(d+.014),0)
  for part in parts:
   if i==0:obj=part
   else:
    obj=part.copy()
    obj.data=part.data
    C.collection.objects.link(obj)
   obj.parent=g
   if i>0:obj.name=part.name+" | "+str(i+1)
 C.view_layer.update()
 bpy.ops.object.select_all(action="DESELECT")
 root.select_set(True)
 for o in S.objects:
  if o.parent is root or o.type=="MESH":o.select_set(True)
 C.view_layer.objects.active=root
 dst=os.path.join(OUT,group["folder"])
 os.makedirs(dst,exist_ok=True)
 path=os.path.join(dst,p["id"]+".glb")
 bpy.ops.export_scene.gltf(filepath=path,export_format="GLB",
     use_selection=True,export_apply=True,export_extras=True,
     export_materials="EXPORT",export_yup=True,
     export_draco_mesh_compression_enable=False)
 with open(path,"rb") as stream:
  magic,ver,total=struct.unpack("<4sII",stream.read(12))
  n,typ=struct.unpack("<I4s",stream.read(8))
  data=json.loads(stream.read(n))
 assert magic==b"glTF" and ver==2 and typ==b"JSON"
 assert total==os.path.getsize(path)
 assert len(data.get("images",[]))>=2
 assert len(data.get("materials",[]))>=2
 assert len(data.get("meshes",[]))>=2
 units=[node for node in data["nodes"] if node.get("name","").startswith("RETAIL_UNIT_")]
 assert len(units)==qty,(p["id"],len(units),qty)
 assert all(p["id"] in n["name"] and len(n.get("children",[]))>=2 for n in units)
 textures=sum(1 for m in data.get("materials",[])
              if m.get("pbrMetallicRoughness",{}).get("baseColorTexture"))
 assert textures>=1,p["id"]
 print("VALIDATED PANTRY STOCK",p["id"],qty,"pieces",
       len(data["meshes"]),"geometry",len(data["images"]),"PBR images",
       round(total/1e6,2),"MB",flush=True)

def main():
 allsku=[p for g in CAT["categories"] for p in g["products"]]
 assert len(allsku)==48 and len({p["id"] for p in allsku})==48
 for group in CAT["categories"]:
  for p in group["products"]:export_stock(p,group)
 import glob
 files=glob.glob(os.path.join(OUT,"*","*.glb"))
 assert len(files)==48,(len(files),"expected 48 separate product GLBs")
 print("COMPLETE: 48 DISTINCT SKUs, 48 GLBs and",
       sum(p["units_per_glb"] for p in allsku),
       "real separate stock unit objects",flush=True)

if __name__=="__main__":main()
