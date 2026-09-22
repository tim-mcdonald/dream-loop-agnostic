"""Self-check for blender-inspect.py. Run: blender --background --factory-startup --python blender-inspect.test.py"""
import os
import runpy
import tempfile

import bpy

here = os.path.dirname(os.path.abspath(__file__))
inspect = runpy.run_path(os.path.join(here, "blender-inspect.py"))["inspect"]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
bpy.ops.mesh.primitive_cube_add(size=2)
cube = bpy.context.active_object
cube.scale = (2, 1, 1)
mat = bpy.data.materials.new("noisy")
mat.use_nodes = True
noise = mat.node_tree.nodes.new("ShaderNodeTexNoise")
bsdf = mat.node_tree.nodes["Principled BSDF"]
mat.node_tree.links.new(noise.outputs["Color"], bsdf.inputs["Base Color"])
cube.data.materials.append(mat)
camera_before = bpy.context.scene.camera

with tempfile.TemporaryDirectory() as out:
    report = inspect(out)
    issues = " | ".join(report["objects"][0]["issues"])
    assert report["objects"][0]["triangles"] == 12, report
    assert [round(v, 3) for v in report["scene_size"]] == [4, 2, 2], report["scene_size"]
    assert "unapplied scale" in issues, issues
    assert "TEX_NOISE" in issues, issues
    assert "non-manifold" not in issues, issues
    for path in report["renders"].values():
        assert os.path.getsize(path) > 0, path
    assert bpy.context.scene.camera == camera_before
    assert "dl_inspect_cam" not in bpy.data.objects

print("blender-inspect self-check: OK")
