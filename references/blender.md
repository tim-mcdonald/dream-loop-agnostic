# Modeling in Blender

Build in code. The best documented Blender results from agents, including the strongest computer-use models, come from bpy code in a render, compare, fix loop. Computer use is for looking, not building, except for sculpting.

## Control method

| Situation | Method |
|---|---|
| A Blender MCP server is connected | MCP, one small code step per call |
| No MCP | Headless: `blender --background --python script.py` |
| Baking, long renders, final export | Headless, even with MCP (MCP calls time out) |
| Checking the open scene: materials, modifiers, node graphs, face orientation | Computer use, if available. Turn what you find into script fixes |
| Organic detail code can't express (creature forms, cloth folds, eroded rock), after a code blockout | Computer use, sculpting only. Set brush and camera up in code, then use a few stroke types (grab, drag, draw) along short, planned paths; free-form strokes come out jagged |
| Everything else | Code. Never build through the GUI |

## Process

1. Keep each asset's build script in `.dream-loop/blender/<asset>.py` as the source of truth, and work on a `.blend` copy there, never the user's file. Sculpted meshes are the exception: save them as `.blend`, note it in `state.md`, and have the script import them instead of rebuilding them.
2. Estimate real sizes in meters from the targets and put them in the script as constants.
3. Build in stages (blockout, form, detail, materials). After each stage, run [scripts/blender-inspect.py](../scripts/blender-inspect.py) and compare its four fixed views against a crop of the asset from the target, and its reported dimensions against your constants. It renders with Workbench by default; for the materials stage pass `--engine CYCLES`. Fix what the numbers flag first. Always inspect after sculpting, since screenshots can't show non-manifold edges or triangle blowups.
4. Avoid the plain-primitive look: bevel hard edges, use subdivision with support loops, shade smooth, and vary instances.
5. Before export: rebuild headless from the script to prove it reproduces, bake procedural textures to images (glTF exports them as flat grey), and apply scale. Then export:
   ```python
   bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
   ```
6. Load the GLB in the product and check orientation, scale, and FPS there.

If a bpy call fails, check `bpy.app.version`, look up the API for that version, and retry with the error message.
