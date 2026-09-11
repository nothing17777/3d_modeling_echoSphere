"""
Approach 2: Moxie robot via lathe (spin) revolve of a traced silhouette profile,
with the actual reference photo camera-projected onto the surface as texture.

Differs from build_moxie.py (primitive-part assembly + cropped face decal):
this builds ONE continuous organic shell from a revolved profile curve, then
projects the full photograph onto it from the front camera view so the whole
body carries real photographic detail, not just the face.

Run: blender -b -P build_moxie_lathe.py
"""
import bpy, bmesh, math, os

OUT_DIR = "/Volumes/T7 Shield/IPMD/models/moxie/renders"
os.makedirs(OUT_DIR, exist_ok=True)
PHOTO = "/Volumes/T7 Shield/IPMD/reference/moxie_robot/moxie-front-standing.png"

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

clear_scene()

# --- Profile: (height_z, radius) traced by eye from the reference photo,
# normalized to the same 0.325 m total height used in approach 1 ---
TOTAL_H = 0.325
profile_norm = [
    (0.000, 0.145),  # base bottom, flared skirt
    (0.019, 0.155),
    (0.058, 0.140),
    (0.109, 0.105),  # base waist (where skirt meets torso)
    (0.167, 0.150),  # torso widest point
    (0.244, 0.145),
    (0.308, 0.110),  # neck taper
    (0.346, 0.135),
    (0.410, 0.200),  # head base widening
    (0.564, 0.245),  # head widest
    (0.744, 0.230),
    (0.872, 0.150),
    (0.949, 0.075),
    (1.000, 0.015),  # head apex point
]

verts_2d = [(z * TOTAL_H, r * TOTAL_H) for z, r in profile_norm]

mesh = bpy.data.meshes.new("Moxie_Lathe_Profile")
bm = bmesh.new()
prev = None
for z, r in verts_2d:
    v = bm.verts.new((r, 0, z))
    if prev:
        bm.edges.new((prev, v))
    prev = v
bm.to_mesh(mesh)
bm.free()

profile_obj = bpy.data.objects.new("Moxie_Profile_Curve", mesh)
bpy.context.collection.objects.link(profile_obj)
bpy.context.view_layer.objects.active = profile_obj
profile_obj.select_set(True)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.spin(steps=48, angle=math.radians(360), center=(0, 0, 0), axis=(0, 0, 1))
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

body = profile_obj
body.name = "Moxie_Lathe_Body"
body.data.name = "Moxie_Lathe_Body_mesh"

# shade smooth
for p in body.data.polygons:
    p.use_smooth = True

# --- Material: photo projected from the front camera (UV project from view) ---
mat = bpy.data.materials.new("Moxie_Photo_Projection")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Roughness"].default_value = 0.35
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(PHOTO, check_existing=True)
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
body.data.materials.append(mat)

# --- Camera positioned to match the reference photo framing, used for UV projection ---
scene = bpy.context.scene
cam_data = bpy.data.cameras.new("ProjCam")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("ProjCam", cam_data)
cam_obj.location = (0, -0.55, TOTAL_H * 0.5)
cam_obj.rotation_euler = (math.radians(90), 0, 0)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj
bpy.context.view_layer.update()

# UV-project the body from this camera's view onto the photo
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')

bpy.ops.object.mode_set(mode='OBJECT')

# Headless-safe: compute perspective-projected UVs from the camera manually
# (equivalent to "Project From View" but doesn't need a live 3D viewport).
uv_layer = body.data.uv_layers.new(name="ProjectedUV")
cam_mat_inv = cam_obj.matrix_world.inverted()
render = scene.render
fov = cam_data.angle
aspect = render.resolution_x / render.resolution_y
for poly in body.data.polygons:
    for li in poly.loop_indices:
        vi = body.data.loops[li].vertex_index
        co_world = body.matrix_world @ body.data.vertices[vi].co
        co_cam = cam_mat_inv @ co_world
        depth = -co_cam.z
        ndc_x = (co_cam.x / depth) / math.tan(fov / 2)
        ndc_y = (co_cam.y / depth) / math.tan(fov / 2) * aspect
        uv_layer.data[li].uv = (ndc_x * 0.5 + 0.5, ndc_y * 0.5 + 0.5)

# --- Render scene (reuse similar lighting/world settings as approach 1) ---
for o in list(bpy.data.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o, do_unlink=True)

scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.render.resolution_x = 900
scene.render.resolution_y = 1100
scene.world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.93, 0.93, 0.93, 1)
bg.inputs[1].default_value = 0.6
scene.view_settings.view_transform = 'Standard'

key = bpy.data.lights.new("Key", 'AREA')
key.energy = 40
key_obj = bpy.data.objects.new("Key", key)
key_obj.location = (-0.8, -0.8, 1.0)
key_obj.rotation_euler = (math.radians(50), 0, math.radians(-40))
bpy.context.collection.objects.link(key_obj)

fill = bpy.data.lights.new("Fill", 'AREA')
fill.energy = 18
fill_obj = bpy.data.objects.new("Fill", fill)
fill_obj.location = (0.8, -0.5, 0.6)
fill_obj.rotation_euler = (math.radians(60), 0, math.radians(40))
bpy.context.collection.objects.link(fill_obj)

scene.render.filepath = os.path.join(OUT_DIR, "moxie_lathe_front.png")
bpy.ops.render.render(write_still=True)
print("RENDERED:", scene.render.filepath)

# three-quarter view
cam_obj.location = (0.4, -0.45, TOTAL_H * 0.55)
cam_obj.rotation_euler = (math.radians(78), 0, math.radians(35))
scene.render.filepath = os.path.join(OUT_DIR, "moxie_lathe_three_quarter.png")
bpy.ops.render.render(write_still=True)
print("RENDERED:", scene.render.filepath)

blend_path = "/Volumes/T7 Shield/IPMD/models/moxie/moxie_lathe.blend"
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("SAVED:", blend_path)
