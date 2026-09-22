"""Render fixed views of a Blender scene and report export-readiness stats.

Headless:
    blender --background scene.blend --python blender-inspect.py -- --out DIR [--engine ENGINE] [--collection NAME]

Inside a live session (e.g. Blender MCP execute_blender_code):
    import runpy, sys; sys.argv = ["x", "--", "--out", "DIR"]
    runpy.run_path("/abs/path/blender-inspect.py", run_name="__main__")

Writes front/right/top/three-quarter PNGs and stats.json to DIR, and prints the stats.
Restores the scene's camera and render settings afterwards, so it is safe on a live scene.
"""
import argparse
import json
import os
import sys

import bmesh
import bpy
from mathutils import Vector

VIEWS = {
    "front": Vector((0, -1, 0)),
    "right": Vector((1, 0, 0)),
    "top": Vector((0, 0, 1)),
    "three-quarter": Vector((1, -1, 0.8)).normalized(),
}
# Upstream nodes that glTF export can't represent; anything like this must be baked to an image first.
PROCEDURAL_PREFIXES = ("TEX_",)
GLTF_SAFE_TEX = {"TEX_IMAGE", "TEX_ENVIRONMENT"}


def upstream(node, seen=None):
    seen = set() if seen is None else seen
    for socket in node.inputs:
        for link in socket.links:
            n = link.from_node
            if n.name not in seen:
                seen.add(n.name)
                yield n
                yield from upstream(n, seen)


def material_issues(mat):
    if mat is None:
        return ["empty material slot"]
    # use_nodes is deprecated in 5.x (materials always use nodes) and may disappear.
    if not getattr(mat, "use_nodes", True) or mat.node_tree is None:
        return []
    nodes = mat.node_tree.nodes
    out = next((n for n in nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
    if out is None:
        return ["no active Material Output"]
    chain = list(upstream(out))
    issues = []
    if not any(n.type == "BSDF_PRINCIPLED" for n in chain):
        issues.append("no Principled BSDF feeding the output (glTF needs one)")
    procedural = sorted({n.type for n in chain if n.type.startswith(PROCEDURAL_PREFIXES) and n.type not in GLTF_SAFE_TEX})
    if procedural:
        issues.append(f"procedural textures {procedural}: bake to image textures before export")
    return issues


def object_stats(ob, depsgraph):
    ob_eval = ob.evaluated_get(depsgraph)
    mesh = ob_eval.to_mesh()
    try:
        coords = [ob.matrix_world @ v.co for v in mesh.vertices]
        tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        non_manifold = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
        boundary = sum(1 for e in bm.edges if e.is_boundary)
        bm.free()
        has_uv = len(mesh.uv_layers) > 0
    finally:
        ob_eval.to_mesh_clear()
    issues = []
    if any(abs(s - 1) > 1e-4 for s in ob.scale):
        issues.append(f"unapplied scale {tuple(round(s, 4) for s in ob.scale)}")
    if any(s < 0 for s in ob.scale):
        issues.append("negative scale (flips normals)")
    if non_manifold:
        issues.append(f"{non_manifold} non-manifold edges")
    if not has_uv:
        issues.append("no UV map")
    for slot in ob.material_slots:
        issues += [f"material {slot.material.name if slot.material else '?'}: {i}" for i in material_issues(slot.material)]
    return coords, {
        "name": ob.name,
        "triangles": tris,
        "boundary_edges": boundary,
        "issues": issues,
    }


def bbox(coords):
    lo = Vector(tuple(min(c[i] for c in coords) for i in range(3)))
    hi = Vector(tuple(max(c[i] for c in coords) for i in range(3)))
    return lo, hi


def render_views(scene, center, extent, out_dir, engine):
    saved = (scene.camera, scene.render.engine, scene.render.filepath,
             scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage)
    cam_data = bpy.data.cameras.new("dl_inspect_cam")
    cam = bpy.data.objects.new("dl_inspect_cam", cam_data)
    scene.collection.objects.link(cam)
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = extent * 1.1
    dist = extent * 3
    cam_data.clip_end = dist * 3
    try:
        scene.camera = cam
        scene.render.engine = engine
        scene.render.resolution_x = scene.render.resolution_y = 1024
        scene.render.resolution_percentage = 100
        paths = {}
        for name, d in VIEWS.items():
            cam.location = center + d * dist
            # The default camera looks down -Z with +Y up, which is already the top view.
            cam.rotation_euler = (0, 0, 0) if name == "top" else (-d).to_track_quat("-Z", "Y").to_euler()
            paths[name] = scene.render.filepath = os.path.join(out_dir, f"{name}.png")
            bpy.ops.render.render(write_still=True)
        return paths
    finally:
        (scene.camera, scene.render.engine, scene.render.filepath,
         scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage) = saved
        bpy.data.objects.remove(cam)
        bpy.data.cameras.remove(cam_data)


def inspect(out_dir, engine="BLENDER_WORKBENCH", collection=None):
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    source = bpy.data.collections[collection].all_objects if collection else scene.objects
    meshes = [ob for ob in source if ob.type == "MESH" and ob.visible_get()]
    if not meshes:
        raise SystemExit("blender-inspect: no visible mesh objects")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    all_coords, objects = [], []
    for ob in meshes:
        coords, stats = object_stats(ob, depsgraph)
        all_coords += coords
        objects.append(stats)
    lo, hi = bbox(all_coords)
    size = hi - lo
    extent = max(size.length, 1e-3)  # diagonal, so every view angle fits
    report = {
        "blender_version": bpy.app.version_string,
        "units": scene.unit_settings.system,
        "scene_bbox_min": [round(v, 4) for v in lo],
        "scene_bbox_max": [round(v, 4) for v in hi],
        "scene_size": [round(v, 4) for v in size],
        "total_triangles": sum(o["triangles"] for o in objects),
        "objects": objects,
        "renders": render_views(scene, (lo + hi) / 2, extent, out_dir, engine),
    }
    with open(os.path.join(out_dir, "stats.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(prog="blender-inspect")
    parser.add_argument("--out", required=True)
    parser.add_argument("--engine", default="BLENDER_WORKBENCH", help="Workbench is fast and version-stable; use EEVEE/Cycles to review materials")
    parser.add_argument("--collection")
    args = parser.parse_args(argv)
    inspect(args.out, args.engine, args.collection)
