---
name: dream-loop-agnostic
description: Build a game, app, or scene so that live screenshots match one or more target images supplied by the user. Works with any vision-capable model, with or without subagents. Use when the user says "dream loop" or asks for something built to match a target image at a very high level of graphical fidelity.
license: MIT
---

# dream-loop (model-agnostic)

Build toward target images, compare live screenshots against them with an independent judge, and loop until they match. Adapted from [achimala/dream-loop](https://github.com/achimala/dream-loop).

## Setup

1. **Vision check.** Open a target image and confirm you actually see its contents. If you can't, stop and tell the user to switch to a vision-capable model.
2. **Targets.** The user supplies one or more images; if none, stop and ask. Copy them to `.dream-loop/targets/target-N.png`. Each is a **view** (a framing to reproduce, the default) or a **reference** (style or material only). Ask once if it's unclear. At least one must be a view.
3. **Capture.** Decide how to screenshot the product: browser automation if you have it, [scripts/preview-server.py](scripts/preview-server.py) for browser apps without it (the app POSTs a PNG to `/__capture`, saved as `.dream-loop/captures/latest.png`), or an OS screenshot command. Match each view's aspect ratio and camera. Look at every capture yourself before using it.
4. **Judge.** Pick a judge method per [references/judge.md](references/judge.md).

Use a gitignored `.dream-loop` folder for all working files. Keep `.dream-loop/state.md` current (targets, judge method, start time, round, scores, open gaps) and reread it after context compaction.

When a viewer can take only one image, pass a side-by-side composite of target and capture (ImageMagick, Pillow, or ffmpeg), and say which side is which.

Then follow [references/workflow.md](references/workflow.md).

## Time budget

If the user gives a time budget, record the start time and check the clock between rounds. Don't degrade visual fidelity or take shortcuts to hit it; meaningful, beautiful progress beats something complete but ugly. With no budget, run to an exit criterion, but warn that this may use a lot of tokens.
