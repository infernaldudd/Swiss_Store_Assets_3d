"""Build four game-ready illuminated storefront signs for Unreal and glTF engines.

Run with: blender -b -t 2 --python tools/build_store_signs.py
Everything is authored in metres, with the front pointing toward -Y.
Source references: user-provided Swiss Coop and Migros storefront photographs.
The names LOOP and AMIGOS are original fictional replacements.
"""
import bpy
import math
import os
import traceback
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'assets')
PREV = os.path.join(ROOT, 'previews')
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREV, exist_ok=True)

def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def mat(name, color, metallic=0.0, roughness=0.42, emit=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    emission_input = 'Emission Color' if 'Emission Color' in p.inputs else 'Emission'
    p.inputs[emission_input].default_value = (*color, 1)
    if 'Emission Strength' in p.inputs:
        p.inputs['Emission Strength'].default_value = emit
    return m

def load_font(paths):
    for path in paths:
        if os.path.isfile(path):
            return bpy.data.fonts.load(path)
    return bpy.data.fonts.get('Bfont')

FONT_ROUND = load_font([
    '/usr/share/fonts/truetype/lato/Lato-Heavy.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
])
FONT_SIGN = load_font([
    '/usr/share/fonts/truetype/lato/Lato-Black.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
])
FONT_SECONDARY = load_font([
    '/usr/share/fonts/truetype/lato/Lato-Bold.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
])

# PBR channel-letter bodies with glowing translucent-like acrylic fronts.
RETURN_LOOP = mat('LOOP | satin copper return', (0.29, 0.094, 0.025), 0.35, 0.34)
RETURN_AMIGOS = mat('AMIGOS | orange anodized return', (0.36, 0.11, 0.021), 0.35, 0.34)
RETURN_WHITE = mat('LOOP | silver return', (0.34, 0.37, 0.40), 0.67, 0.28)
FRONTS_LOOP = [
    mat('LOOP | coral face', (1.00, 0.245, 0.067), 0.02, 0.36, 2.5),
    mat('LOOP | sunset orange face', (1.00, 0.325, 0.067), 0.02, 0.36, 2.6),
    mat('LOOP | amber face', (1.00, 0.385, 0.050), 0.02, 0.36, 2.5),
    mat('LOOP | golden-orange face', (1.00, 0.505, 0.095), 0.02, 0.36, 2.4),
]
FRONTS_AMIGOS = [
    mat('AMIGOS | illuminated vermilion', (1.00, 0.210, 0.035), 0.02, 0.37, 2.1),
    mat('AMIGOS | illuminated orange', (1.00, 0.305, 0.045), 0.02, 0.37, 2.2),
]
FRONT_WHITE = mat('restaurant | diffused cool-white acrylic', (0.82, 0.90, 1.00), 0.0, 0.26, 2.3)
STEEL = mat('mounts | brushed stainless steel', (0.48, 0.53, 0.57), 0.82, 0.29)
DARK_STEEL = mat('mounts | graphite powder coat', (0.075, 0.082, 0.089), 0.80, 0.38)
SCREWS = mat('hardware | black rubber washers', (0.025, 0.030, 0.030), 0.12, 0.65)

def mark_asset(obj):
    obj['asset'] = True
    return obj

def mesh_text(body, name, width, center_z, font, side_material,
              front_materials, thickness=0.12, center_x=0.0, forward_y=-0.145):
    # Text is created in local XY. Rotation makes positive local Z face -Y.
    data = bpy.data.curves.new(name + ' typography', 'FONT')
    data.body = body
    data.font = font
    data.size = 1.0
    data.align_x = 'LEFT'
    data.align_y = 'BOTTOM_BASELINE'
    data.resolution_u = 16
    data.fill_mode = 'BOTH'
    data.extrude = thickness * 0.5
    data.bevel_depth = min(0.007, thickness * 0.06)
    data.bevel_resolution = 3
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.context.view_layer.update()
    if obj.dimensions.x <= 0:
        raise ValueError('Text failed to generate: ' + body)
    obj.scale = (width / obj.dimensions.x,) * 3
    bpy.ops.object.convert(target='MESH')
    # Bake size into vertices but leave orientation at identity until assignments.
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)
    mesh = obj.data
    min_x = min(v.co.x for v in mesh.vertices)
    max_x = max(v.co.x for v in mesh.vertices)
    min_y = min(v.co.y for v in mesh.vertices)
    max_y = max(v.co.y for v in mesh.vertices)
    for v in mesh.vertices:
        v.co.x -= 0.5 * (min_x + max_x)
        v.co.y -= 0.5 * (min_y + max_y)
    mesh.materials.append(side_material)
    for fm in front_materials:
        mesh.materials.append(fm)
    span = max(max_x-min_x, 0.01)
    for poly in mesh.polygons:
        # Text's frontmost face uses local +Z, which becomes world -Y.
        if poly.normal.z > 0.65:
            x = (poly.center.x + 0.5 * span) / span
            segment = min(len(front_materials)-1, max(0, int(x * len(front_materials))))
            poly.material_index = segment + 1
        else:
            poly.material_index = 0
    obj.rotation_euler.x = math.pi / 2
    obj.location = (center_x, forward_y, center_z)
    mark_asset(obj)
    return obj

def cube(name, center, size, material, bevel=0.0, export=True):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new('radiused fabricated edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        mod2 = obj.modifiers.new('weighted normals', 'WEIGHTED_NORMAL')
    if export:
        mark_asset(obj)
    return obj

def cylinder(name, center, radius, length, material, axis='Y'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=length, location=center)
    obj = bpy.context.object
    obj.name = name
    if axis == 'Y':
        obj.rotation_euler.x = math.pi / 2
    elif axis == 'X':
        obj.rotation_euler.y = math.pi / 2
    obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.use_smooth = True
    mark_asset(obj)
    return obj

def rear_mounts(width, z, num=4, y=-0.052):
    # Hardware is intentionally behind the letters and is mostly hidden front-on.
    positions = [-width * 0.43 + i * width * 0.86/(num-1) for i in range(num)]
    for i, x in enumerate(positions):
        cylinder('standoff %02d' % (i+1), (x, y, z), 0.018, 0.105, STEEL)
        cylinder('wall anchor %02d' % (i+1), (x, 0.012, z), 0.034, 0.012, DARK_STEEL)
        cylinder('sealing pad %02d' % (i+1), (x, 0.022, z), 0.039, 0.005, SCREWS)

def build_loop():
    mesh_text('LOOP', 'LOOP | four dimensional channel letters', 3.30, 0.05,
              FONT_ROUND, RETURN_LOOP, FRONTS_LOOP, 0.12)
    rear_mounts(3.1, 0.04, 4)
    return 3.30, 0.90

def build_loop_restaurant():
    mesh_text('LOOP', 'LOOP restaurant | upper orange channel letters',
              3.15, 0.41, FONT_ROUND, RETURN_LOOP, FRONTS_LOOP, 0.115)
    mesh_text('restaurant', 'LOOP restaurant | white lower lettering',
              2.34, -0.38, FONT_SECONDARY, RETURN_WHITE, [FRONT_WHITE],
              0.078, center_x=0.35, forward_y=-0.117)
    rear_mounts(2.9, 0.36, 4)
    rear_mounts(2.18, -0.35, 3)
    return 3.15, 1.58

def build_amigos():
    mesh_text('AMIGOS', 'AMIGOS | large fabricated six-letter sign', 5.20, 0.0,
              FONT_SIGN, RETURN_AMIGOS, FRONTS_AMIGOS, 0.165,
              forward_y=-0.187)
    rear_mounts(4.96, 0.0, 7, y=-0.065)
    return 5.20, 1.10

def build_double_a():
    # Referencing Swiss storefronts with two projecting illuminated M letters:
    # fictional AMIGOS uses A initials, one above another.
    for i, z in enumerate((0.68, -0.68), 1):
        mesh_text('A', 'AMIGOS | projecting A %d'%i, 1.02, z,
                  FONT_SIGN, RETURN_AMIGOS, [FRONTS_AMIGOS[0]],
                  0.18, center_x=-0.04, forward_y=-0.25)
        # White rear sign enclosure, concealed from the front view
        cube('projecting sign rear housing %d'%i, (0.0, -0.083, z),
             (0.94, 0.07, 1.02), DARK_STEEL, 0.015)
    # Heavy-gauge bracket mounts to facade. Wall is on positive Y.
    cube('main vertical rear mounting rail', (0.52, 0.035, 0.0),
         (0.085, 0.16, 2.29), STEEL, 0.012)
    for z in (-0.85, 0.0, 0.85):
        cube('wall plate %.2f'%z, (0.55, 0.12, z),
             (0.22, 0.038, 0.19), DARK_STEEL, 0.009)
        cylinder('rail bolt %.2f'%z, (0.55, 0.096, z), 0.018,
                 0.025, STEEL)
    for z in (-0.68, 0.68):
        cube('forward mounting arm %.2f'%z, (0.26, -0.035, z),
             (0.53, 0.07, 0.07), STEEL, 0.010)
    # Discreet full-name manufacturer plaque, as this is an A-shaped logo sign.
    mesh_text('AMIGOS', 'AMIGOS | identity plaque', 0.57, -1.35,
              FONT_SECONDARY, RETURN_AMIGOS, [FRONTS_AMIGOS[1]], 0.036,
              center_x=-0.02, forward_y=-0.16)
    return 1.10, 3.04

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z','Y').to_euler()

def preview(name, width, height):
    # A backdrop and lights exist only for PNG previews, NOT in exported GLB.
    wall = mat('preview only | finely textured limestone',
               (0.30, 0.32, 0.33), 0.0, 0.92)
    cube('PREVIEW ONLY - facade wall', (0, 0.32, 0), (width+1.35, 0.20, height+0.95),
         wall, 0.02, export=False)
    bpy.ops.object.camera_add(location=(width*0.12, -max(width*1.72, 5.35), height*0.12+0.30))
    cam = bpy.context.object
    cam.name = 'PREVIEW ONLY - camera'
    aim(cam, (0,0,0))
    cam.data.type='ORTHO'
    cam.data.ortho_scale=max(width+1.25, (height+1.00)*2.05)
    bpy.context.scene.camera=cam
    for loc, power, size in [((-width*.5,-3,3),750,4.0),
                              ((width*.6,-1,0.5),380,2.4)]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        obj=bpy.context.object
        obj.name='PREVIEW ONLY - softbox'
        obj.data.energy=power
        obj.data.shape='DISK'
        obj.data.size=size
        aim(obj, (0,0,0))
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version >= (4,2,0) else 'BLENDER_EEVEE'
    scene.render.resolution_x=1100
    scene.render.resolution_y=590
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=os.path.join(PREV,name+'.png')
    scene.world.color=(0.10,0.10,0.10)
    scene.render.film_transparent=False
    if hasattr(scene, 'eevee') and hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples=32
    # Fog-glow bloom only affects preview; emissive PBR faces remain in the GLB.
    try:
        scene.use_nodes=True
        tree=scene.node_tree
        tree.nodes.clear()
        rl=tree.nodes.new('CompositorNodeRLayers')
        gl=tree.nodes.new('CompositorNodeGlare')
        gl.glare_type='FOG_GLOW'
        gl.threshold=1.25
        gl.quality='MEDIUM'
        out=tree.nodes.new('CompositorNodeComposite')
        tree.links.new(rl.outputs['Image'],gl.inputs['Image'])
        tree.links.new(gl.outputs['Image'],out.inputs['Image'])
    except Exception:
        pass
    try:
        bpy.ops.render.render(write_still=True)
        print('Preview rendered:', scene.render.filepath)
    except Exception as exc:
        print('Preview render skipped (GLB still built):', exc)
        traceback.print_exc()

def export_asset(name):
    bpy.ops.object.select_all(action='DESELECT')
    selected=[]
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.get('asset'):
            obj.select_set(True)
            selected.append(obj)
    if not selected:
        raise RuntimeError('Refusing to export an empty asset')
    # Keep every fabricated part independently addressable for material edits.
    path=os.path.join(OUT,name+'.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB',
                              use_selection=True, export_apply=True,
                              export_yup=True, export_materials='EXPORT')
    size=os.path.getsize(path)
    if size < 3000:
        raise RuntimeError('Suspiciously small GLB: '+path)
    print('EXPORTED', path, 'bytes=', size, 'mesh_objects=', len(selected))
    bpy.ops.object.select_all(action='DESELECT')

def main():
    variants=[
        ('LOOP_Wordmark',build_loop),
        ('LOOP_Restaurant',build_loop_restaurant),
        ('AMIGOS_Wordmark',build_amigos),
        ('AMIGOS_DoubleA_Projected',build_double_a)
    ]
    for name, builder in variants:
        reset()
        width,height=builder()
        export_asset(name)
        preview(name,width,height)
    print('COMPLETE: 4 GLBs in',OUT)

if __name__=='__main__':
    main()
