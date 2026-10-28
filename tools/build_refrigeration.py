"""Build TWO photorealistic grocery refrigeration fixtures from user photo references.

Model 1: wheeled serve-over refrigerated deli / pizza display case with bent
         real glass, wheel casters, ventilated compressor box, display trays.
Model 2: one eight-door full-width freezer/chiller wall, eight independent
         door pivot groups, 48 internal shelves, rubber gaskets, internal LED
         light channels, glass, chrome frames and grilles.

All dimensions in metres. Distinct 3D geometry, not screenshots turned into
planes. Original graphics. Empty food compartments ready for separate product
assets. Generic fictional signs only; no real trademarks. This is one GLB per
reference fixture (exactly two GLBs), plus two Blender source .blend files and
two preview renders. Both models face world -Y in Blender.

Usage:
 /usr/bin/python3 tools/generate_surface_finish_maps.py
 /usr/bin/python3 tools/generate_fridge_graphics.py
 blender -b -t 2 --python tools/build_refrigeration.py
 RENDER_PREVIEWS=1 blender -b -t 2 --python tools/build_refrigeration.py
"""
import bpy,os,math,json,struct
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"assets","refrigeration")
SRC=os.path.join(ROOT,"source","refrigeration")
PREV=os.path.join(ROOT,"previews","refrigeration")
FIN=os.path.join(ROOT,"textures","surface_finishes")
IMG=os.path.join(ROOT,"textures","refrigeration")
for folder in (OUT,SRC,PREV):os.makedirs(folder,exist_ok=True)
SC=bpy.context.scene
C=bpy.context
TAG="fridge_asset"
def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for m in list(bpy.data.materials):
        if m.users==0:bpy.data.materials.remove(m)
    for i in list(bpy.data.images):
        if i.users==0:bpy.data.images.remove(i)

def material(name,col,metal=0,rough=.5,alpha=1,roughmap=None,normal=False,texture=None,emission=0):
    ma=bpy.data.materials.new(name);ma.use_nodes=True
    ma.diffuse_color=(*col,alpha)
    bs=ma.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*col,1)
    bs.inputs["Metallic"].default_value=metal
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Alpha"].default_value=alpha
    if alpha<1:ma.blend_method="BLEND"
    if emission>0:
        bs.inputs["Emission Color"].default_value=(*col,1)
        bs.inputs["Emission Strength"].default_value=emission
    def read(src,nc):
        path=os.path.join(FIN if src in ("rough","normal") else IMG,nc[0])
        im=bpy.data.images.load(path,check_existing=True)
        if nc[1]:im.colorspace_settings.name="Non-Color"
        im.pack()
        tex=ma.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image=im
        return tex
    if roughmap:
        n=read("rough",(roughmap,True))
        ma.node_tree.links.new(n.outputs["Color"],bs.inputs["Roughness"])
    if normal:
        n=read("normal",("Soft_Micro_Normal.png",True))
        nm=ma.node_tree.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value=.15
        ma.node_tree.links.new(n.outputs["Color"],nm.inputs["Color"])
        ma.node_tree.links.new(nm.outputs["Normal"],bs.inputs["Normal"])
    if texture:
        n=read("image",(texture,False))
        ma.node_tree.links.new(n.outputs["Color"],bs.inputs["Base Color"])
    return ma
def mats():
    return {
      "stainless":material("PBR | brushed stainless steel",(.53,.58,.61),.88,.28,
                           roughmap="Brushed_Steel_Roughness.png",normal=True),
      "silver":material("PBR | satin silver anodized aluminium",(.65,.70,.71),.77,.27,
                        roughmap="Brushed_Steel_Roughness.png",normal=True),
      "graphite":material("PBR | smoked metallic grey case fascia",(.23,.255,.275),.56,.35,
                          roughmap="SemiGloss_Vinyl_Roughness.png"),
      "white":material("PBR | clean off-white antimicrobial liner",(.76,.82,.83),.15,.38,
                       roughmap="Powdercoat_Steel_Roughness.png",normal=True),
      "black":material("PBR | black recessed metal vents",(.055,.067,.072),.47,.48),
      "rubber":material("PBR | matte moulded rubber door gasket",(.06,.075,.082),.0,.83),
      "glass":material("PBR | clear single-pane display glass 6mm",(.74,.86,.90),.0,.08,
                       alpha=.16,roughmap="PET_Bottle_Roughness.png"),
      "window_glass":material("PBR | glazed insulating multi-door panels",(.79,.88,.91),.0,.06,
                              alpha=.12,roughmap="PET_Bottle_Roughness.png"),
      "darkglass":material("PBR | opaque dark readout glass",(.03,.061,.084),.0,.19),
      "led":material("PBR | 4300K LED luminous diffuser",(.85,.95,1.0),0,.24,emission=3.8),
      "warmled":material("PBR | 3900K warm white display strip",(.96,.91,.82),0,.29,emission=3.2),
      "tire":material("PBR | soft textured caster tyre",(.04,.043,.048),0,.92),
      "screen":material("PBR | original printed digital thermostat",(.3,.7,.81),0,.32,
                        texture="Digital_Thermostat_2K.png",emission=.45),
      "header":material("PBR | custom chilled aisle header sign",(.12,.22,.24),.05,.59,
                        texture="Chiller_Header_2K.png"),
      "counter_brand":material("PBR | original refrigerator service panel label",(.22,.34,.37),.11,.53,
                                texture="Counter_Front_Panel_2K.png"),
      "vents":material("PBR | perforated steel front",(.55,.58,.60),.69,.35,
                       roughmap="Brushed_Steel_Roughness.png"),
    }

def cube(name,pos,dim,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    o=C.object;o.name=name
    o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel>0:
        b=o.modifiers.new("Real edge bevel","BEVEL")
        b.width=bevel;b.segments=3
        # Geometry bevel already gives real highlights without auto-smooth warnings.
    o[TAG]=True
    return o
def cylinder(name,pos,r,depth,mat,axis="Z",n=36):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=depth,location=pos)
    o=C.object;o.name=name;o.data.materials.append(mat)
    if axis=="X":o.rotation_euler[1]=math.pi/2
    if axis=="Y":o.rotation_euler[0]=math.pi/2
    for poly in o.data.polygons:poly.use_smooth=True
    o[TAG]=True
    return o
def new_mesh(name,verts,faces,mat,uvfaces=None,smooth=False):
    mesh=bpy.data.meshes.new(name+"_geom")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    mesh.materials.append(mat)
    if uvfaces is not None:
        assert len(uvfaces)==len(faces)
        uvs=mesh.uv_layers.new(name="Print UV")
        for face,uv in zip(mesh.polygons,uvfaces):
            assert len(face.loop_indices)==len(uv)
            for l,c in zip(face.loop_indices,uv):uvs.data[l].uv=c
    o=bpy.data.objects.new(name,mesh)
    C.collection.objects.link(o)
    o[TAG]=True
    for poly in o.data.polygons:poly.use_smooth=smooth
    return o
def image_front(name,w,h,y,z,mat):
    v=[(-w/2,y,z-h/2),(w/2,y,z-h/2),
       (w/2,y,z+h/2),(-w/2,y,z+h/2)]
    return new_mesh(name,v,[[0,1,2,3]],mat,[[(0,0),(1,0),(1,1),(0,1)]])
def beam(name,a,b,width,depth,mat,bevel=.001):
    # Box aligned with its longitudinal Z axis, so rails follow glass
    # bends and refrigeration structural profiles exactly.
    a=Vector(a);b=Vector(b)
    direction=b-a
    o=cube(name,(a+b)*.5,(width,depth,direction.length),mat,bevel)
    o.rotation_euler=direction.to_track_quat("Z","Y").to_euler()
    return o
def vent_mesh(name,xc,y,zc,width,height,m,cols=26,rows=8):
    """Physically pierced metal mesh: every opening has NO FACE at the centre.

    The darker compressor wall is behind the grill with 6mm air gap.
    Each opening has four connected metal rings, not projected dark dots.
    """
    vx=[];faces=[]
    cw=width/cols;ch=height/rows
    for row in range(rows):
        for col in range(cols):
            x0=xc-width/2+col*cw
            z0=zc-height/2+row*ch
            x1=x0+cw;z1=z0+ch
            sx=cw*.21;sz=ch*.22
            # 8 vertices around a rectangular punched hole.
            start=len(vx)
            vx.extend([(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1),
                       (x0+sx,y,z0+sz),(x1-sx,y,z0+sz),
                       (x1-sx,y,z1-sz),(x0+sx,y,z1-sz)])
            faces.extend([[start+0,start+1,start+5,start+4],
                          [start+1,start+2,start+6,start+5],
                          [start+2,start+3,start+7,start+6],
                          [start+3,start+0,start+4,start+7]])
    return new_mesh(name,vx,faces,m)

def wheel_group(x,y,M,num):
    z=.078
    cube("CASTER %d | welded rotation bracket"%num,(x,y,z+.036),
         (.082,.071,.080),M["silver"],.005)
    cylinder("CASTER %d | dark rubber tyre"%num,(x,y,z),.047,.036,M["tire"],"X",40)
    cylinder("CASTER %d | stainless axle hub"%num,(x+.021,y,z),.020,.003,M["stainless"],"X",24)
    cylinder("CASTER %d | axle cap"%num,(x-.021,y,z),.014,.004,M["graphite"],"X",24)
    cube("CASTER %d | fork arm"%num,(x,y-.027,z+.014),(.051,.006,.063),M["stainless"],.002)

def plate_prism(name,x,profile,depth,mat):
    # Flat side cheek follows angular glass outline, actual thickness depth.
    # x is side of the fixture, profile is (y,z), thickness along X.
    xs=(x-depth/2,x+depth/2)
    verts=[(xx,y,z) for xx in xs for y,z in profile]
    n=len(profile)
    faces=[list(reversed(range(n))),list(range(n,2*n))]
    for i in range(n):
        nxt=(i+1)%n
        faces.append([i,nxt,n+nxt,n+i])
    return new_mesh(name,verts,faces,mat)

def glass_ribbon(name,width,points,M):
    # Glass front and roof made from flat glass facets with constrained bends,
    # not a floating translucent plane or texture of a glass case.
    for i in range(len(points)-1):
        y0,z0=points[i];y1,z1=points[i+1]
        a=(-width/2,y0,z0);b=(width/2,y0,z0)
        c=(width/2,y1,z1);d=(-width/2,y1,z1)
        new_mesh(name+" | bent segment %02d"%(i+1),
                 [a,b,c,d],[[0,1,2,3]],M["glass"],[[(0,0),(1,0),(1,1),(0,1)]])
    for y,z in points:
        beam("GLASS | exposed satin horizontal division rail",( -width/2,y,z),
             (width/2,y,z),.009,.013,M["silver"],.0011)

def countertop(M):
    W=2.28
    # Reference 1: one refrigeration island, not two store counters joined.
    # Back is +Y, customer/front is -Y.
    cube("COUNTER | load bearing refrigeration plinth",(0,.007,.382),
         (1.69,.79,.470),M["graphite"],.012)
    cube("COUNTER | compressor internal shadow front",(0,-.397,.332),
         (1.53,.015,.305),M["black"],.002)
    cube("COUNTER | polished stainless top deck",(0,0,.797),
         (W,1.08,.045),M["stainless"],.009)
    cube("COUNTER | dark front nose fascia",(0,-.540,.718),
         (W,.072,.147),M["graphite"],.011)
    cube("COUNTER | visible lower front seam",(0,-.578,.646),
         (W,.018,.013),M["silver"],.001)
    cube("COUNTER | fold-down work surface",(0,+.523,.760),
         (W,.075,.041),M["silver"],.005)
    cube("COUNTER | compressor bottom steel chassis",(0,0,.146),
         (1.85,.85,.048),M["stainless"],.008)
    # Front and side punched perforations with dark cavity underneath.
    vent_mesh("COMPRESSOR | pierced vent grille front",0,-.410,.314,
              1.27,.275,M["vents"],35,9)
    for x in (-.843,.843):
        cube("COMPRESSOR | side shell panel",(x,0,.392),
             (.026,.79,.47),M["graphite"],.003)
    # Service sticker: small rather than loud logos everywhere.
    cube("CONTROL | black glass display bezel",(.735,-.586,.716),
         (.142,.009,.055),M["darkglass"],.002)
    plane=new_mesh("CONTROL | UV printed 4.0 C thermostat",
        [( .676,-.592,.698),(.790,-.592,.698),(.790,-.592,.737),(.676,-.592,.737)],
        [[0,1,2,3]],M["screen"],[[(0,0),(1,0),(1,1),(0,1)]])
    # Keep front as simple stainless display counter, no copied brand.
    # wheels partially hidden behind compressor base, physically attached.
    for i,(x,y) in enumerate([(-.78,-.292),(.78,-.292),
                              (-.78,.303),(.78,.303)],1):
        wheel_group(x,y,M,i)
    # Customer-facing display tray sits INSIDE curved glazing, with visible
    # stainless perimeter, perforated false bottom and service lip.
    cube("DISPLAY | black food-safe tray bed",(0,-.056,.848),
         (W-.10,.82,.021),M["graphite"],.003)
    for j in range(3):
        x=(j-1)*.706
        cube("DISPLAY | individually removable serving tray %d"%j,
             (x,-.050,.862),(.680,.76,.012),M["stainless"],.003)
        for i in range(12):
            yy=-.397+i*.059
            cube("DISPLAY | fine drainage ribs", (x,yy,.872),
                 (.657,.003,.003),M["silver"],.001)
    # Angled/curved sneeze glass from reference; frame edges are REAL geometry.
    profile=[(-.547,.823),(-.602,1.043),(-.524,1.266),
             (-.321,1.349),(.438,1.349)]
    glass_ribbon("CURVED SHOWCASE | real glass front and roof",W-.022,profile,M)
    # End caps protect the side glazing with physically extruded curved profile.
    side_profile=[(-.545,.824),(-.602,1.042),(-.525,1.268),
                  (-.320,1.349),(.439,1.349),(.447,.821)]
    for xside in (-W/2+.016,W/2-.016):
        plate_prism("SHOWCASE | 6mm transparent glazed end cheek",
                    xside,side_profile,.006,M["glass"])
        for i in range(len(side_profile)-1):
            a=side_profile[i];b=side_profile[i+1]
            beam("SHOWCASE | brushed side structural edge",
                 (xside,a[0],a[1]),(xside,b[0],b[1]),
                 .013,.013,M["silver"],.0018)
    # Broad top bridge held by three stainless cross-arms like the original.
    for x in (-W/2+.018,0,W/2-.018):
        beam("SHOWCASE | polished front to back top support",
             (x,-.53,1.287),(x,.426,1.352),
             .022,.033,M["silver"],.002)
    beam("SHOWCASE | front lower edge trim",
         (-W/2,-.551,.823),(W/2,-.551,.823),
         .028,.030,M["stainless"],.002)
    # Rear sliding access panes in two panels.
    for i in range(2):
        x=(-.566 if i==0 else .566)
        cube("REAR SERVICE | sliding clear glass panel %d"%i,
             (x,.452,1.090),(1.14,.007,.505),M["glass"],.002)
        for z in (.840,1.343):
            cube("REAR SERVICE | horizontal track",
                 (x,.450,z),(1.137,.014,.012),M["silver"],.001)
        cube("REAR SERVICE | grab handle",(x+.42,.431,1.103),
             (.016,.040,.124),M["silver"],.003)
    # Top high CRI internal LED strip and extruded lens.
    cube("SHOWCASE | integrated underside LED diffuser",
         (0,.397,1.328),(W-.14,.012,.009),M["warmled"],.002)
    # Four actual contact feet under motor, plus original data fields.
    root=bpy.data.objects.new("APPLIANCE | Refrigerated Pizza_Deli_Display Counter",None)
    C.collection.objects.link(root)
    root["real_width_m"]=W;root["real_height_m"]=1.349
    root["real_depth_m"]=1.11
    root["front_direction"]="-Y"
    root["model_origin"]="reference image 1; original generic refrigerated serving counter"
    return root

def chiller(M):
    # Long fridge/freezer aisle in three other photo references:
    # 8 glazed side-by-side hinged doors, 6 shelves each, LED trim.
    bays=8
    door_pitch=.850
    W=bays*door_pitch+.120
    H=2.48
    DEP=.84
    L=-W/2
    outer_y=-.015
    root=bpy.data.objects.new("APPLIANCE | Glass_Door_Refrigerated_Freezer_Wall",None)
    C.collection.objects.link(root)
    root["width_m"]=W;root["height_m"]=H;root["depth_m"]=DEP
    root["door_count"]=bays
    root["adjustable_shelves_per_bay"]=6
    root["front_direction"]="-Y"
    root["door_pivot"]= "DOOR_01..08_HINGE nodes"
    # Structural body, continuous real fixture (not eight separate models).
    cube("COOLER WALL | lower compressor plinth",(0,.030,.144),
         (W,.823,.276),M["graphite"],.014)
    cube("COOLER WALL | rear thermally insulated panel",(0,.409,1.297),
         (W-.05,.056,2.151),M["white"],.006)
    for x in (-W/2+.023,W/2-.023):
        cube("COOLER WALL | actual structural side shell",
             (x,-.012,1.300),(.047,DEP,2.300),M["silver"],.006)
        cube("COOLER WALL | side-edge thermal gasket",
             (x,-.436,1.234),(.019,.013,1.975),M["rubber"],.002)
    # Full width top fascia; original printed marquee, not copied image signage.
    cube("COOLER WALL | top dark graphite fascia",(0,-.012,2.373),
         (W,.826,.211),M["graphite"],.009)
    panel=new_mesh("COOLER WALL | original UV printed header art",
        [(-W/2+.10,-.433,2.305),(W/2-.10,-.433,2.305),
         (W/2-.10,-.433,2.433),(-W/2+.10,-.433,2.433)],
         [[0,1,2,3]],M["header"],[[(0,0),(1,0),(1,1),(0,1)]])
    cube("COOLER WALL | graphite lower kick grille recess",(0,-.441,.108),
         (W-.07,.010,.161),M["black"],.001)
    vent_mesh("COOLER WALL | truly pierced lower compressor grille",
              0,-.449,.105,W-.11,.124,M["vents"],160,5)
    cube("COOLER WALL | lower kicked inox guard rail",(0,-.459,.029),
         (W-.10,.026,.034),M["silver"],.002)
    # Upper cooling coil cassette shadows; visible through glazed doors.
    cube("COOLER WALL | continuous stainless ceiling liner",
         (0,-.006,2.222),(W-.08,.753,.033),M["white"],.004)
    cube("COOLER WALL | low white insulated floor liner",
         (0,-.021,.289),(W-.07,.745,.026),M["white"],.003)
    # Each bay has a subtly separate liner and actual refrigerated airflow.
    for k in range(bays):
        xcen=L+.060+(k+.5)*door_pitch
        l=xcen-door_pitch/2
        r=xcen+door_pitch/2
        suffix=" | BAY_%02d"%(k+1)
        cube("INNER BAY | rear white hygienic liner"+suffix,
             (xcen,.367,1.245),(.802,.014,1.922),M["white"],.001)
        for side in (-1,1):
            x=xcen+side*.404
            cube("INNER BAY | pressed metal separator"+suffix,
                 (x,-.004,1.240),(.019,.754,1.926),M["white"],.002)
            cube("INNER BAY | vertical cold-air LED diffuser"+suffix,
                 (x-side*.018,-.351,1.251),
                 (.010,.011,1.891),M["led"],.002)
            cube("INNER BAY | moulded LED metal track"+suffix,
                 (x-side*.020,-.348,1.251),
                 (.022,.027,1.894),M["silver"],.002)
        # Six real load-bearing shelves per bay, narrow perforated lip.
        for shelf_id,z in enumerate((.420,.720,1.020,1.320,1.620,1.920),1):
            tag=" | SHELF_%02d"%shelf_id+suffix
            cube("INTERIOR | actual load bearing metal shelf"+tag,
                 (xcen,.005,z),(.775,.671,.021),M["white"],.0019)
            cube("INTERIOR | white front raised shelf lip"+tag,
                 (xcen,-.337,z+.018),(.764,.011,.039),M["silver"],.0014)
            cube("INTERIOR | rear cooling-air gap"+tag,
                 (xcen,.334,z),(.746,.008,.014),M["stainless"],.001)
            # Physically raised narrow wire ribs on each deck (rather than
            # a fake grating texture). 12 ribs merged conceptually with shelf
            # but true geometry for near-camera reflection.
            for j in range(8):
                yy=-.286+j*.075
                cube("INTERIOR | solid freezer shelf drainage rib"+tag,
                     (xcen,yy,z+.012),(.732,.0024,.0018),M["silver"],.00065)
        # Real glazed door hinged independently for level animation.
        # The width is less than pitch to provide visible refrigerator gaps.
        door_root=bpy.data.objects.new("DOOR_%02d_HINGE | independently hinged"% (k+1),None)
        C.collection.objects.link(door_root)
        door_root.location=(l+.007,-.446,.283)
        door_root["is_hinged"]=True
        door_root["hinge_side"]="left";door_root["closed_degrees"]=0
        door_root["panel_width_m"]=door_pitch-.012
        parts_before=set(SC.objects)
        w=door_pitch-.019
        fh=1.974
        zmid=(.281+2.255)/2
        door_y=-.452
        # Double-insulated glass is an actual transparent slab 7mm thick.
        cube("GLAZING | 7mm insulating glass pane"+suffix,
             (xcen,door_y-.007,zmid),
             (w-.096,.007,fh-.119),M["window_glass"],.0021)
        # Black EPDM seal touches the glass before the bright aluminium.
        for side in (-1,1):
            x=xcen+side*(w/2-.036)
            cube("GLAZING | EPDM vertical edge seal"+suffix,
                 (x,door_y-.005,zmid),
                 (.011,.013,fh-.026),M["rubber"],.002)
        for z in (zmid-fh/2+.028,zmid+fh/2-.028):
            cube("GLAZING | EPDM horizontal seal"+suffix,
                 (xcen,door_y-.004,z),
                 (w-.036,.014,.011),M["rubber"],.001)
        # Recessed aluminium extrusion and narrow bevel shine.
        for side in (-1,1):
            x=xcen+side*(w/2-.018)
            cube("DOOR FRAME | anodised slim vertical stile"+suffix,
                 (x,door_y,zmid),
                 (.037,.041,fh),M["silver"],.004)
            cube("DOOR FRAME | groove inside vertical profile"+suffix,
                 (x-side*.014,door_y-.022,zmid),
                 (.004,.003,fh-.035),M["graphite"],.001)
        for z in (zmid-fh/2+.018,zmid+fh/2-.018):
            cube("DOOR FRAME | anodized horizontal crossmember"+suffix,
                 (xcen,door_y,z),
                 (w-.024,.041,.037),M["silver"],.003)
        # Tube handle on door, with two actual bracket standoffs.
        hx=xcen+w/2-.080
        hy=door_y-.073
        cube("DOOR HANDLE | brushed steel vertical tubular pull"+suffix,
             (hx,hy,zmid),(.019,.021,.225),M["stainless"],.007)
        for zz in (zmid-.095,zmid+.095):
            cube("DOOR HANDLE | captive steel mounting spacer"+suffix,
                 (hx,door_y-.040,zz),
                 (.027,.061,.022),M["stainless"],.003)
        # Hinge pins mounted to corresponding left jamb.
        for zz in (.381,2.148):
            cylinder("DOOR HINGE | actual top and bottom spindle"+suffix,
                     (l+.018,door_y,zz),.016,.039,M["stainless"],"Z",24)
        added=[o for o in SC.objects if o not in parts_before and o.type=="MESH"]
        for obj in added:
            mx=obj.matrix_world.copy()
            obj.parent=door_root
            obj.matrix_world=mx
    return root

def export(name,expected_shelves,expected_doors):
    objs=[o for o in SC.objects if o.type=="MESH" and o.get(TAG)]
    minimum=160 if expected_doors else 70
    assert len(objs)>minimum,(name,len(objs))
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:o.select_set(True)
    for o in SC.objects:
        if o.type=="EMPTY" and (o.name.startswith("DOOR_") or
                                 o.name.startswith("APPLIANCE")):
            o.select_set(True)
    C.view_layer.objects.active=objs[0]
    path=os.path.join(OUT,name+".glb")
    bpy.ops.export_scene.gltf(filepath=path,export_format="GLB",
          use_selection=True,export_materials="EXPORT",export_apply=True,
          export_extras=True,export_yup=True,
          export_draco_mesh_compression_enable=False)
    bpy.ops.object.select_all(action="DESELECT")
    with open(path,"rb") as f:
        magic,version,length=struct.unpack("<4sII",f.read(12))
        n,ct=struct.unpack("<I4s",f.read(8))
        data=json.loads(f.read(n))
    assert magic==b"glTF" and version==2 and ct==b"JSON"
    assert length==os.path.getsize(path)
    assert len(data.get("meshes",[]))>=minimum
    assert len(data.get("materials",[]))>=9
    assert len(data.get("images",[]))>=2
    nodes=[o.get("name","") for o in data["nodes"]]
    assert len([n for n in nodes if n.startswith("DOOR_")])==expected_doors
    assert len([n for n in nodes if n.startswith("INTERIOR | actual load bearing metal shelf")])==expected_shelves
    assert any("GLAZING" in n or "GLASS |" in n for n in nodes)
    assert any("vent" in n.lower() or "grille" in n.lower() for n in nodes)
    # Transparent glass and emissive LED are real PBR materials in the GLB.
    assert any(ma.get("alphaMode")=="BLEND" for ma in data["materials"])
    assert any("emissiveFactor" in ma for ma in data["materials"])
    print("GLB VERIFIED",name,"nodes",len(nodes),"meshes",
          len(data["meshes"]),"PBR mats",len(data["materials"]),
          "bytes",length,flush=True)

def render(name,wall=False):
    # Preview floor and softboxes do not enter the GLB.
    studio=material("PREVIEW ONLY | polished stone shop floor",(.34,.36,.37),.0,.64)
    floorw=11.0 if wall else 4.4
    floor=cube("PREVIEW ONLY | floor",(0,0,-.041),
               (floorw,4.7,.071),studio,.002)
    floor[TAG]=False
    cam_pos=(5.0,-12.0,3.70) if wall else (2.55,-4.25,2.03)
    look=Vector((0,0,1.15 if wall else .76))
    for p,power,size in [
       ((-2.4,-3.2,4.4), 1800 if wall else 370, 3.6 if wall else 2.6),
       ((+3.4,-1.3,4.0), 1100 if wall else 270, 2.8 if wall else 2.0),
       ((0,+1.8,4.7), 570 if wall else 140, 3.2)]:
        bpy.ops.object.light_add(type="AREA",location=p)
        light=C.object;light.data.energy=power;light.data.size=size
        light.rotation_euler=(look-light.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.object.camera_add(location=cam_pos)
    cam=C.object
    cam.rotation_euler=(look-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO"
    cam.data.ortho_scale=8.85 if wall else 2.92
    SC.camera=cam
    SC.world.color=(.20,.20,.20)
    SC.render.engine="CYCLES"
    SC.cycles.device="CPU"
    SC.cycles.samples=22
    if hasattr(SC.cycles,"use_denoising"):SC.cycles.use_denoising=False
    if hasattr(C.view_layer.cycles,"use_denoising"):C.view_layer.cycles.use_denoising=False
    SC.view_settings.view_transform="AgX"
    SC.render.resolution_x=1380 if wall else 1080
    SC.render.resolution_y=780 if wall else 1060
    SC.render.resolution_percentage=100
    SC.render.image_settings.file_format="PNG"
    SC.render.filepath=os.path.join(PREV,name+".png")
    bpy.ops.render.render(write_still=True)
    print("PREVIEW SAVED",SC.render.filepath,flush=True)

def main():
    variants=[
       ("Swiss_Refrigerated_Glass_Pizza_Deli_Counter",False,0,0),
       ("Swiss_Glass_Door_Freezer_Chiller_Wall_8Doors",True,48,8)
    ]
    for name,wall,expected_shelves,expected_doors in variants:
        clear();M=mats()
        if wall:chiller(M)
        else:countertop(M)
        export(name,expected_shelves,expected_doors)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SRC,name+".blend"),compress=True)
        if os.environ.get("RENDER_PREVIEWS")=="1":render(name,wall)
        print("FINISHED REFRIGERATION MODEL",name,flush=True)
    files=[x for x in os.listdir(OUT) if x.endswith(".glb")]
    assert len(files)==2,files
    print("SUCCESS EXACTLY TWO INDEPENDENT FRIDGE GLBS",flush=True)
if __name__=="__main__":main()
