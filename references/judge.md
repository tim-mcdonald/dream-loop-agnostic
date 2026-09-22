# Judge

Judge with a clean context each time, to keep it objective. Use the first option available:

1. **Subagent** with a fresh context and vision. Give it absolute image paths and the prompt below.
2. **Separate model call** from the shell with the images attached (an OpenAI-compatible endpoint, `ollama`, `llm`, a vendor CLI). Best for local open-weight setups.
3. **Self-judge**, as a last resort: update `state.md`, then judge from the images alone without looking at code or plans. Describe the target, then the capture, then list the differences, then score. When in doubt, take the lower score.

For each view target, give the judge the target, the matching capture, the previous round's capture and verdict if any, and any reference targets labeled as references. Save verdicts to `.dream-loop/verdicts/round-R-target-N.md`.

## Judge prompt

Pass this verbatim:

> You are judging how close the current product is relative to the target image. Score along this rubric:
>
> - **Composition (0-3):** Are the camera, framing, and layout correct? Are the position and scale of all major components correct compared to the target image?
> - **Lighting (0-3):** Check color palette, exposure, shadows, contrast, and atmosphere. Pay attention to reflections, glows, etc. Ensure the scene overall is not too dark or too light compared to the target.
> - **Materials (0-3):** Check that every surface looks right, with the expected textures, roughness, translucency, wetness, etc. Ensure assets don't look blocky, plasticky, smooth, or fake, unless the target image specifically also does this.
> - **Details (0-1):** Go through everything with a fine-toothed comb. Not a single pixel should be different. Every tiny speck and detail should match between the two images.
>
> You can give fractional scores. You should be nitpicky and precise, and include a list of all gaps and blockers that need to be resolved for a perfect score on each category. It's OK to output a gigantic list if the current product is nowhere close to the target. It needs to be comprehensive and actionable so that another agent could go fix everything on the list, come back, and get a substantially improved score. Avoid non-actionable feedback like "This tree looks fake." You need to name exactly what's giving that impression and how the agent should fix it.
> Everything is within reason. If models or scenes need to be completely redesigned, say so. Don't sugarcoat it. The goal is for both images to be identical. The product should exactly reach the target. Do not settle for less.
>
> You should lastly also provide a total score out of 10 by summing these up.
>
> If a previous verdict and screenshot are provided, maintain consistency with prior judgment, but do not feel obligated to match or increase score. If the product regressed, it should score worse.
>
> End your answer with one line in exactly this form: `TOTAL: <score>/10`
