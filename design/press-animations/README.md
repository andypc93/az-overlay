# Press animations

Playable sheets for the **Press** setting under Pads on Appearance
(`overlay.PRESS_ANIMS`). One overlay pad per sheet, drawn with the app's real pad
values and the same timings and distances the code uses. Hold or tap a pad to play it.

- `gen_press.py` regenerates the artboards (`*.dc.html`) and `canvas.json`.
- Published canvas (Claude Design preview): https://claude.ai/code/artifact/695e990b-d7c8-422f-a15d-cd26921e50e7

Keep these in step with `draw_pad` and the `PRESS_*` constants in `overlay.py`; the
comments in `gen_press.py` name the code each sheet mirrors.
