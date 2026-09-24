# Building Humans with MPFB

Parametric human workflow for Blender with the MPFB (MakeHuman) add-on installed. Read this instead of `blender.md` when the asset is a human body built from MPFB — the generic stage order (blockout, form, detail, materials) still applies, but every operation below replaces its Blender-native equivalent.

## Overview

Drive MPFB headless through `bpy.ops` only (`blender --background --python script.py`); never the GUI. Keep one build script per character as the source of truth: it must rebuild the `.blend` plus all baked PNGs from scratch. One proven character took 58 rounds to 8.0-8.5/10 at 30.9k tris across 3 objects (body + fitted system hair + fitted system brows), 1.80 m, zero inspect issues.
## When to Use

- Asset is a human (full body or head) and MPFB is installed
- NOT for creatures, clothing as separate meshes, or scenes without people — use `blender.md`

## Quick Reference

| Need | Operation |
|---|---|
| Base body | MPFB operators via `bpy.ops`; macro targets (age/sex/muscle/weight/height) first, then micro targets as decimals |
| Hide helper geometry | Mask modifier; eyes stay visible through it |
| Landmarks | `helper-l-eye`, `helper-r-eye`, etc.: average member verts for centers, span for radius |
| Skin detail | Bake AO; paint albedo in texture space; procedural tilefield → Sobel normals (detail-only by construction) — never bake normals from a subdivided+displaced mesh, it captures faceting as blobs |
| Export gate | Principled BSDF + baked images (+ Emission for eyes, NormalMap node), no procedurals; rebuild headless and require zero inspect issues |
| Hair, brows, lashes | Fit system MHCLO assets after all shaping (see Patterns); pick variants from `.thumb` sheets, keep an env override so they're switchable |
| Face detail density | Second UV layer from authored focus maps + self-masked RGBA detail + chained bump (see Patterns); legacy MakeSkin + ink operators cost more than they give |

## Patterns

**New geometry + mask modifier.** Added verts (brow cards, lash geometry) are hidden until registered in the mask's `body` group. Canary: tri count must rise after an additive change — unchanged means the change didn't land, even if the render looks plausible.

**Raycast seating.** Seat surface-hugging additions by raycasting from outside the body along the facing axis, plus a small positive offset. Walk the seed until the hit face has the expected material.

**3D-to-UV splat painting.** Paint soft zones per-face: select by 3D centroid tests, fill loop-UV polygons on an overlay, blur, composite. Prefer self-calibrating placements over magic numbers — e.g. waistband/hems as boundary faces (one material touching another) in the top/bottom fraction of the zone's own range.

**UV check before texture-space strokes.** Lines drawn between raycast-seated UV endpoints work; polylines through verts with streaked UVs paint blobs. Inspect the target faces' UV island first.

**Clay-check before paint-chasing.** When a mark is reported, reproduce it untextured first: still visible = geometry (fix targets/sculpts), gone = paint or lighting (fix zones/strokes/light). A deep ala groove from nose-narrowing targets survived every paint theory until the clay view settled it.
**Measurement probes before face adjustments.** Small scripts against the built blend: ball center vs lid-opening box (symmetry plus seating offset), depth profiles across folds (groove depth in mm), ray-seat diagnostics (aim to hit material/position). Numbers first — but the render stays ground truth for gaze direction, the probe for symmetry and offsets.
**Verify paint in the texture, not the render.** Geometry shadow masquerades as painted lines — a lid-fold shadow read as a painted liner for 10+ rounds while the stroke system drew literally nothing (zero dark pixels in the PNG; pixel-identical rebuild diff after deleting it). Check the PNG itself after any texture-space paint step, and delete dead paint systems: future seat changes resurrect their strays.

## Values Worth Tuning (per character — no universals)
**System assets before custom geometry.** MPFB ships hair, eyebrows, eyelashes, eyes, skins, and focus UV maps in its user/system data dirs. Sheet the `.thumb` PNGs, pick two contrasting candidates, test-fit both on a cached shaped blend (attach takes seconds), judge front and back, integrate the winner. Fitted MHCLO follows the final surface — attach AFTER all shaping (targets, bake, scale, code sculpt) with `subdiv_levels=0` and rig options off when there's no rig. Rename the fitted objects; the export gate counts every object.

**Probe, then integrate.** Keep a stop-after-shaping hook in the build script that dumps the shaped blend. All fit and appearance experiments run as small probe scripts against that cached file with env-var parameters — the build script changes only for winners.

**Retire covered regions.** When a fitted asset covers body area (scalp under mesh hair), reassign those faces to the underlying material and collapse their UVs onto one safe tile (e.g. forehead) so peek-through reads as skin, not smeared texture. Material-only trims never cut holes — verify before repairing phantom gaps.

**Harden authored alpha, don't edit asset files.** Shipped textures often average semi-transparent alpha and wash gray under a bright key. Clamp-multiply the texture's alpha (x1.5-2) inside your own material graph; never modify the shipped files.

**Custom ink layers, no MakeSkin required.** The makeup operators demand legacy MakeSkin materials, whose flat base loses to a custom graph with baked AO, albedo zones, and procedural normals. Take the pattern, not the shader: authored focus unwraps (`face_solid.json.gz` etc.) applied with `MeshService.add_uv_map_from_dict` as a second UV layer, an RGBA detail texture (feathered alpha edges, neutral corners including texel 0,0) mixed over base albedo by its own alpha, and a bump texture chained onto the existing normal. Paint uniform-density detail on authored unwraps (the unwrap already weights importance); reserve T-zone weighting for planar projections. Loop-index addressing means no face may be added or deleted between creation and focus-map application.

**Illustrated targets.** For painted references, skip pore/bump/micro-normal detail entirely — smooth albedo with painted gradient modeling matches paintings better; keep the full detail recipe for realistic targets.

Sample from targets each time; one character's numbers will be wrong for the next body. What transfers is the list and the method:

- **Body micros:** glute volume, leg definition, pectoral size, lat width, abdominal definition, arm volume, shoulder/trap shape — largest deviation first across front/side/back views.
- **Face micros:** eye openness (verify lid coverage in close-up), chin structure, cheek fullness, lip volume — plus youth read when the target is younger: `head-age-decr`, larger eye scale, fuller cheeks, blush zones on cheek apples plus nose bridge (Rematch-style makeup).
- **Code sculpts** for what targets don't cover (e.g. brow-ridge projection plus its groove) — small measured offsets, seated on the surface.
- **Calibrate strength at final distance:** albedo usually must overstate the sampled reference delta to survive flat game lighting — step up multiplicatively until it reads full-body. Normal detail goes the other way: felt, not seen.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Added verts invisible, judged as present anyway | Check tri count before judging pixels |
| Name used before definition in a long generated script | `py_compile` before every headless build; grep the log for markers |
| Painted feature lands in the wrong place | UV island check first |
| Normal bake shows broad patches | Bake caught low-vs-high faceting; switch to procedural detail-only normals |
| Pass looks done close-up, vanishes full-body | Judge at final distance; adjust in measured steps |
| Build log looks clean but the render is stale | `blender --background` exits 0 on uncaught script exceptions — grep every build log for Traceback before capturing |
| `import PIL` fails in the build script | Blender's python has no PIL — paint PNGs with system python, load them with `bpy.data.images.load` |
| Focus-map detail lands on wrong faces | Loop indices shifted: a face was added or deleted after creation; focus maps require untouched ordering |
| Boundary smoothing breaks manifoldness | `bmesh.ops.subdivide_edges` on material-boundary edges produced 268 non-manifold edges; prefer a vertex-color blend (boundary fraction + neighbor smoothing) mixed in the shader — zero topology risk |
| Painterly target, renders look desaturated next to it | AgX/Filmic eats red saturation in brights; capture with Standard view transform (`CAPTURE_VIEW_TRANSFORM` env) when judging against un-tonemapped references — presentation only, model/export unaffected |
| Silent headless timeout, no error | Rerun before debugging — usually machine load |
| Temp crops pile up in `captures/` | Delete round-specific crops when the verdict is written |
| Cross-eyed or mis-seated gaze after eye targets | Probe ball center vs opening for symmetry, measure pupil vs opening center in the render for gaze; translate helper-eye verts post-bake (downstream UVs adapt) |
| Painted lid detail never appears, only strays draw | Lid-margin UV is a ~6px blob with a seam through it — body-UV strokes can't render there; liner needs dedicated lid UVs/cards or geometry ribbons |
| Nose-base lines sharpen after narrowing the nose | Width/depth targets deepen the ala groove (check untextured); ease `nose-trans-backward` / nose widths |
