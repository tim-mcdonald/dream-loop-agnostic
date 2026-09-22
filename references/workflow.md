# Dream Loop Workflow

Build the product yourself, in one continuous context, so you keep what you learned and what already failed. Don't hand building to worker subagents; they re-read the code every round and lose that history. Use subagents for judging.

## The loop

1. Implement the view targets, using reference targets for style and materials
2. Test the product and fix bugs, loading issues, and asset orientation or scale
3. Capture a screenshot for each view target
4. Judge each screenshot against its target, per [judge.md](judge.md)
5. Address all of the judge's feedback, largest gaps first
6. Test again, then check the exit criteria. If not done, return to step 3

The round score is the lowest view score. Re-judge every view each round so fixing one doesn't regress another.

## Exit criteria

- **score >= 8 and FPS acceptable**: done. Show the user the screenshots next to their targets and ask if they want more rounds.
- **score >= 8 but FPS too low**: optimize, lossless wins first, then re-judge to confirm no visual regression.
- **Stall approaching**: the best score hasn't improved by a full point in 2 rounds, or the judge named the same gap twice in a row. Stop tweaking. Rethink the approach: assets, lighting, camera, or scene layout may be fundamentally wrong. Aim for a dramatic improvement.
- **Stalled**: the big rethink didn't raise the score. Stop and ask the user whether the current state is good enough or what looks off.
- **Round cap**: stop at the user's cap, or check in after 5 rounds if none was set.
- Otherwise, keep looping.

## 3D assets

Go down this list in order. Don't fall back to procedural assets to save time.

1. **Download** free assets, only if the user allowed it.
2. **Blender**, if installed or connected through MCP, for characters, buildings, scenery, greenery, and other detailed or important assets. Read [blender.md](blender.md) first.
3. **Procedural** in code, only when nothing above is available or it truly gives the closest result.

Textures and normal maps are what make assets look real; never settle for flat colors. Sources, in order: textures the user provided (reference targets often serve this), downloads if allowed, crops from the target images made tileable with normal maps derived from them, and procedural textures as a last resort.
