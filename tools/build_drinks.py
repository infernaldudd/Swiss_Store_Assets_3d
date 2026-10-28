"""Produce a first collection of original fictional Swiss grocery drinks.
Creates 12 different 3D beverage GLBs with fitted printed labels and PBR
materials: cans, PET bottles, and gable-top juice cartons.
Usage: blender -b -t 2 --python tools/build_drinks.py
"""
import bpy,math,os,struct,json
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"assets","drinks")
os.makedirs(OUT,exist_ok=True)
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
def material(name,c,metal=0,rough=.4):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 p=m.node_tree.nodes.get("Principled BSDF")
 p.inputs["Base Color"].default_value=(*c,1);p.inputs["Metallic"].default_value=metal;p.inputs["Roughness"].default_value=rough
 return m
def clear():
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
def mesh(name,verts,faces,mat,uvs=None):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();m.materials.append(mat)
 if uvs:
  u=m.uv_layers.new(name="Artwork UV")
  for p,coords in zip(m.polygons,uvs):
   for li,point in zip(p.loop_indices,coords):u.data[li].uv=point
 o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);return o
def lathe(name,profile,mat,seg=48):
 v=[];f=[];uv=[]
 for r,z in profile:
  for i in range(seg+1):
   a=math.tau*i/seg;v.append((r*math.cos(a),r*math.sin(a),z))
 for j in range(len(profile)-1):
  for i in range(seg):
   k=j*(seg+1)+i
   f.append((k,k+1,k+seg+2,k+seg+1))
   uv.append(((i/seg,j/(len(profile)-1)),((i+1)/seg,j/(len(profile)-1)),((i+1)/seg,(j+1)/(len(profile)-1)),(i/seg,(j+1)/(len(profile)-1))))
 return mesh(name,v,f,mat,uv)
def cylinder(name,r,depth,z,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=depth,location=(0,0,z))
 o=bpy.context.object;o.name=name;o.data.materials.append(mat);return o
def torus(name,R,r,z,mat):
 bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=8,location=(0,0,z),major_radius=R,minor_radius=r)
 o=bpy.context.object;o.name=name;o.data.materials.append(mat);return o
def box(name,pos,dim,mat,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
 o=bpy.context.object;o.name=name;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:
  b=o.modifiers.new("Rounded manufacturing edges","BEVEL");b.width=bevel;b.segments=3
 return o
def text(name,word,width,z,y,mat):
 data=bpy.data.curves.new(name,"FONT");data.body=word;data.align_x="CENTER";data.align_y="BOTTOM_BASELINE";data.extrude=.00012
 o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o)
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.context.view_layer.update()
 if o.dimensions.x>0:o.scale=(width/o.dimensions.x,)*3
 o.rotation_euler.x=math.pi/2;o.location=(0,y,z)
 bpy.ops.object.convert(target="MESH");o=bpy.context.object;o.data.materials.append(mat);o.select_set(False);return o
def cup(name,flavor,form,col,vol):
 dark=material("Label | "+name,col,.06,.31)
 silver=material("Brushed aluminium",(0.67,.69,.70),.82,.26)
 white=material("Printed white lettering",(.97,.96,.90),.02,.38)
 if form=="can":
  h=.115 if vol==330 else .097;r=.033 if vol==330 else .029
  lathe("Pressed aluminium body",[(r*.94,.004),(r,.009),(r,h-.009),(r*.90,h-.004)],dark)
  cylinder("Lower can base",r*.93,.003,.004,silver)
  cylinder("Recessed upper can lid",r*.90,.003,h-.004,silver)
  torus("Double seamed aluminium rolled rim",r*.92,.002,h-.003,silver)
  box("Opening ring tab",(-.004,0,h-.001),(.025,.012,.0017),silver,.002)
  text("Product branding",name.split()[0],r*1.55,h*.68,-r-.001,white)
  text("Flavour typography",flavor.upper(),r*1.62,h*.42,-r-.001,white)
  text("Volume",str(vol)+" ml",r*1.3,h*.22,-r-.001,white)
 elif form=="pet":
  h=.211;r=.033
  pet=material("PET | semi transparent tint",tuple(min(1,c*.5+.33) for c in col),.0,.14)
  lathe("Blow-moulded PET bottle",[(.019,.002),(.027,.004),(.031,.012),(.033,.031),(.033,.135),(.030,.155),(.024,.171),(.015,.186),(.014,.194)],pet)
  label=lathe("Sleeve printed label",[(.0333,.052),(.0333,.127)],dark)
  for i in range(7):
   z=.017+i*.005
   torus("PET lower grip ridges",.0326,.0006,z,pet)
  cap=material("Injection moulded plastic cap",(.86,.87,.84),.05,.33)
  cylinder("Tamper evident neck ring",.016,.006,.191,cap)
  cylinder("Ribbed cap",.018,.018,.204,cap)
  for i in range(18):
   a=math.tau*i/18
   ob=box("Cap anti-slip grip rib",(.018*math.cos(a),.018*math.sin(a),.203),(.0016,.0018,.012),cap,.0003)
   ob.rotation_euler.z=a
  text("Front logo",name.split()[0],r*1.52,.103,-r-.003,white)
  text("Drink type",flavor.upper(),r*1.65,.080,-r-.003,white)
 elif form=="carton":
  h=.195
  paper=material("Laminated carton | "+name,col,.01,.64)
  box("Liquid container cardboard carton",(0,0,.096),(.070,.070,.188),paper,.0025)
  # Inclined folded shoulders produce familiar gable top.
  verts=[(-.035,-.035,.190),(.035,-.035,.190),(.035,.035,.190),(-.035,.035,.190),
   (-.035,0,.231),(.035,0,.231)]
  faces=[(0,1,5,4),(3,2,5,4),(0,4,3),(1,2,5)]
  mesh("Carton folded sealed gable roof",verts,faces,paper)
  box("Folded top longitudinal seal",(0,0,.233),(.072,.004,.008),paper,.001)
  cap=material("Opaque carton spout",(.95,.95,.90),.05,.35)
  cylinder("Pour spout",.011,.006,.208,cap)
  cylinder("Screw opening cap",.014,.010,.216,cap)
  text("Product title",name.split()[0],.050,.139,-.036,white)
  text("Juice flavour",flavor.upper(),.062,.089,-.036,white)
  text("Carton nominal volume","1 L",.035,.037,-.036,white)
 return h
def export(name):
 bpy.ops.object.select_all(action="DESELECT")
 objs=[o for o in bpy.context.scene.objects if o.type=="MESH"]
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0]
 path=os.path.join(OUT,name+".glb")
 bpy.ops.export_scene.gltf(filepath=path,export_format="GLB",use_selection=True,export_yup=True,export_apply=True,export_materials="EXPORT",export_draco_mesh_compression_enable=False)
 with open(path,"rb") as f:
  magic,version,total=struct.unpack("<4sII",f.read(12))
  chunk,typ=struct.unpack("<I4s",f.read(8));data=json.loads(f.read(chunk))
 assert magic==b"glTF" and version==2 and total==os.path.getsize(path)
 assert len(data.get("meshes",[]))>=3
 assert len(data.get("materials",[]))>=2
 print("VALIDATED",name,total,"bytes",flush=True)
def main():
 for i,(name,flavor,form,col,vol) in enumerate(ITEMS):
  clear();cup(name,flavor,form,col,vol)
  slug=name.replace(" ","_")
  export(slug)
 assert len([x for x in os.listdir(OUT) if x.endswith(".glb")])==len(ITEMS)
 print("SUCCESS",len(ITEMS),"beverage assets",flush=True)
if __name__=="__main__":main()
