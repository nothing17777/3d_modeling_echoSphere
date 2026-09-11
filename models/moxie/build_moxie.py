"""
Moxie robot (Embodied Inc.) - Blender Python build script.
Run: blender -b -P build_moxie.py -- <stage>

Real-world scale: robot height ~0.325 m (12.8in), all units meters.
Named, separate parts per component.
"""
import bpy, sys, math, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = argv[0] if argv else "all"
OUT_DIR = os.path.join(os.path.dirname(bpy.data.filepath) or os.getcwd(), "renders")
OUT_DIR = "/Volumes/T7 Shield/IPMD/models/moxie/renders"
os.makedirs(OUT_DIR, exist_ok=True)

# Colors sampled from reference/moxie_robot photos (sRGB->linear converted).
TEAL = (0.045, 0.24, 0.22, 1.0)
LIGHT_TEAL = (0.10, 0.37, 0.34, 1.0)
WHITE_FACE = (0.86, 0.88, 0.82, 1.0)
DARK_CAM = (0.03, 0.03, 0.03, 1.0)
GREEN_IRIS = (0.20, 0.65, 0.30, 1.0)
BEZEL_BLACK = (0.015, 0.015, 0.015, 1.0)

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)

def mat(name, color, rough=0.4, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m

def image_mat(name, image_path, rough=0.25):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.blend_method = 'BLEND'
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = rough
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(image_path, check_existing=True)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    out.location = (300, 0)
    bsdf.location = (0, 0)
    tex.location = (-300, 0)
    return m

def add(obj, name, material=None, parent=None):
    obj.name = name
    obj.data.name = name + "_mesh"
    if material:
        obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj

def sphere(name, radius, loc, scale=(1,1,1), material=None, parent=None, segs=32, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=segs, ring_count=rings)
    o = bpy.context.active_object
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return add(o, name, material, parent)

def cylinder(name, radius, depth, loc, rot=(0,0,0), scale=(1,1,1), material=None, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return add(o, name, material, parent)

def cone(name, radius1, radius2, depth, loc, rot=(0,0,0), material=None, parent=None):
    bpy.ops.mesh.primitive_cone_add(radius1=radius1, radius2=radius2, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    return add(o, name, material, parent)

def plane(name, size, loc, rot=(0,0,0), material=None, parent=None):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    o = bpy.context.active_object
    return add(o, name, material, parent)

def torus(name, major_r, minor_r, loc, rot=(0,0,0), material=None, parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_r, minor_radius=minor_r, location=loc, rotation=rot)
    o = bpy.context.active_object
    return add(o, name, material, parent)

def build():
    clear_scene()
    teal = mat("Teal_Shell", TEAL, rough=0.35)
    light_teal = mat("Light_Teal", LIGHT_TEAL, rough=0.3)
    white_face = mat("Face_White", WHITE_FACE, rough=0.15)
    dark = mat("Dark_Camera", DARK_CAM, rough=0.2)
    green = mat("Iris_Green", GREEN_IRIS, rough=0.2)
    black = mat("Black", (0.02,0.02,0.02,1), rough=0.3)
    white_glow = mat("LightStrip", (1,1,1,1), rough=0.1)
    bezel = mat("Face_Bezel", BEZEL_BLACK, rough=0.25)

    empty = bpy.data.objects.new("Moxie_Root", None)
    bpy.context.collection.objects.link(empty)

    # Total height target ~0.325m. Head is the dominant mass (~45% of height),
    # torso a squat barrel, base a wide flat skirt.

    # --- Base (wide flat rounded skirt robot sits on) ---
    base = sphere("Base", 0.095, (0, 0, 0.035), scale=(1, 1, 0.4), material=teal, parent=empty)

    # --- Torso (squat barrel, wider than tall, flatter front) ---
    torso = sphere("Torso", 0.088, (0, 0, 0.135), scale=(1, 0.85, 0.95), material=teal, parent=empty)

    # --- Speaker grille (front of torso, dark circle) ---
    speaker = cylinder("Speaker_Grille", 0.026, 0.006, (0, -0.083, 0.098),
                        rot=(math.radians(90), 0, 0), material=dark, parent=empty)

    # --- Chest light strip (thin horizontal pill above speaker) ---
    light_strip = cylinder("Chest_Light_Strip", 0.006, 0.004, (0, -0.086, 0.155),
                            rot=(math.radians(90), 0, 0), scale=(4.0, 1, 1), material=white_glow, parent=empty)

    # --- Neck (short, mostly hidden under head overhang) ---
    neck = cylinder("Neck", 0.032, 0.015, (0, 0, 0.205), material=teal, parent=empty)

    # --- Head: large teardrop dome, apex pulled back-and-up (hood shape) ---
    head = sphere("Head", 0.125, (0, 0.01, 0.325), scale=(1, 1, 1.05), material=teal, parent=empty)
    head_point = cone("Head_Point", 0.03, 0.0, 0.055, (0, 0.05, 0.44),
                       rot=(math.radians(-12), 0, 0), material=teal, parent=empty)

    # --- Face bezel: thin black rim just behind the face screen edge (flat, low profile) ---
    face_bezel = sphere("Face_Bezel", 0.102, (0, -0.086, 0.325), scale=(1, 0.13, 1.10), material=bezel, parent=empty)

    # --- Face screen: flat plane textured with the actual photographed face graphic, clearly in front ---
    face_tex_path = "/Volumes/T7 Shield/IPMD/models/moxie/textures/moxie_face.png"
    face_material = image_mat("Face_Texture", face_tex_path)
    face = plane("Face_Screen", 0.19, (0, -0.118, 0.325), rot=(math.radians(90), 0, 0),
                 material=face_material, parent=empty)
    face.scale = (1.0, 0.75, 1.0)
    bpy.ops.object.select_all(action='DESELECT')

    # --- Camera module (small dark notch at top-front hairline, above face) ---
    cam_bump = cylinder("Camera_Module", 0.010, 0.012, (0, -0.098, 0.408),
                         rot=(math.radians(75), 0, 0), material=dark, parent=empty)

    # --- Side sensor bump on head (small dark dot, right side) ---
    ear_bump = sphere("Head_Sensor_Ring", 0.008, (0.118, -0.01, 0.35), scale=(1,0.5,1), material=black, parent=empty)

    # --- Arms: shoulder sphere + rounded forearm capsule + paddle hand, both sides ---
    def build_arm(side):
        s = 1 if side == "Right" else -1
        shoulder = sphere(f"Shoulder_{side}", 0.034, (s*0.112, 0, 0.16), scale=(1,0.9,1), material=teal, parent=empty)
        upper = cylinder(f"UpperArm_{side}", 0.024, 0.09, (s*0.132, 0, 0.115),
                          rot=(0, math.radians(s*10), 0), scale=(1.5, 0.7, 1), material=teal, parent=empty)
        elbow = sphere(f"Elbow_{side}", 0.024, (s*0.14, 0, 0.07), scale=(1,0.9,1), material=light_teal, parent=empty)
        forearm = cylinder(f"Forearm_{side}", 0.020, 0.075, (s*0.135, 0.02, 0.03),
                            rot=(math.radians(-14), math.radians(s*8), 0), scale=(1.4, 0.7, 1), material=light_teal, parent=empty)
        hand = sphere(f"Hand_{side}", 0.024, (s*0.128, 0.045, -0.005), scale=(1.2, 0.7, 0.9), material=light_teal, parent=empty)
        return [shoulder, upper, elbow, forearm, hand]

    build_arm("Right")
    build_arm("Left")

    bpy.context.view_layer.update()

def setup_render_scene(cam_side="front"):
    for o in list(bpy.data.objects):
        if o.type in ('CAMERA', 'LIGHT'):
            bpy.data.objects.remove(o, do_unlink=True)

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1100
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.93, 0.93, 0.93, 1)
    bg.inputs[1].default_value = 0.6
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.exposure = 0.0

    cam_positions = {
        "front": ((0, -0.9, 0.28), (math.radians(85), 0, 0)),
        "side": ((0.9, 0, 0.28), (math.radians(85), 0, math.radians(90))),
        "three_quarter": ((0.65, -0.65, 0.35), (math.radians(75), 0, math.radians(45))),
    }
    loc, rot = cam_positions.get(cam_side, cam_positions["front"])
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 50
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    cam_obj.location = loc
    cam_obj.rotation_euler = rot
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    key = bpy.data.lights.new("Key", 'AREA')
    key.energy = 40
    key_obj = bpy.data.objects.new("Key", key)
    key_obj.location = (-0.8, -0.8, 1.0)
    key_obj.rotation_euler = (math.radians(50), 0, math.radians(-40))
    key.size = 1.0
    bpy.context.collection.objects.link(key_obj)

    fill = bpy.data.lights.new("Fill", 'AREA')
    fill.energy = 18
    fill_obj = bpy.data.objects.new("Fill", fill)
    fill_obj.location = (0.8, -0.5, 0.6)
    fill_obj.rotation_euler = (math.radians(60), 0, math.radians(40))
    fill.size = 1.0
    bpy.context.collection.objects.link(fill_obj)

def render(name):
    scene = bpy.context.scene
    scene.render.filepath = os.path.join(OUT_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED: {scene.render.filepath}")

build()

for view in ["front", "three_quarter", "side"]:
    setup_render_scene(view)
    render(f"moxie_{view}")

blend_path = "/Volumes/T7 Shield/IPMD/models/moxie/moxie.blend"
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"SAVED: {blend_path}")
