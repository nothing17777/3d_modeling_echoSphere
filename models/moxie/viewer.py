import base64
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).parent

st.set_page_config(page_title="Moxie 3D Model Viewer", layout="wide")
st.title("Moxie Robot — 3D Model Viewer")

tab_3d, tab_compare = st.tabs(["Interactive 3D model", "Reference vs. render"])

with tab_3d:
    glb_path = APP_DIR / "moxie.glb"
    if not glb_path.exists():
        st.error(f"Missing {glb_path.name}. Export it from Blender first:\n\n"
                  "blender -b moxie.blend --python-expr "
                  "\"import bpy; bpy.ops.export_scene.gltf(filepath='moxie.glb', export_format='GLB')\"")
    else:
        glb_b64 = base64.b64encode(glb_path.read_bytes()).decode()
        st.caption("Drag to rotate, scroll to zoom, right-drag to pan.")
        st.components.v1.html(
            f"""
            <script type="module"
                src="https://cdnjs.cloudflare.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js">
            </script>
            <model-viewer
                src="data:model/gltf-binary;base64,{glb_b64}"
                alt="Moxie robot 3D model"
                camera-controls
                auto-rotate
                shadow-intensity="1"
                exposure="1"
                camera-orbit="0deg 75deg 0.8m"
                style="width:100%; height:640px; background:#f0f0f0; border-radius:8px;">
            </model-viewer>
            """,
            height=660,
        )

with tab_compare:
    renders_dir = APP_DIR / "renders"
    ref_dir = APP_DIR.parent.parent / "reference" / "moxie_robot"

    st.subheader("Approach 1 — primitive-part assembly (recommended)")
    cols = st.columns(3)
    for col, name in zip(cols, ["moxie_front.png", "moxie_three_quarter.png", "moxie_side.png"]):
        p = renders_dir / name
        if p.exists():
            col.image(str(p), caption=name, use_container_width=True)

    st.subheader("Approach 2 — lathe revolve + photo projection")
    cols = st.columns(2)
    for col, name in zip(cols, ["moxie_lathe_front.png", "moxie_lathe_three_quarter.png"]):
        p = renders_dir / name
        if p.exists():
            col.image(str(p), caption=name, use_container_width=True)

    st.subheader("Original reference photos")
    if ref_dir.exists():
        ref_images = sorted(ref_dir.glob("*.png"))
        cols = st.columns(len(ref_images) or 1)
        for col, p in zip(cols, ref_images):
            col.image(str(p), caption=p.name, use_container_width=True)
    else:
        st.info(f"Reference folder not found at {ref_dir}")
