"""Generate the press-animation artboards: one overlay pad per sheet, drawn with the app's
real pad values and timings (overlay.PRESS_ANIMS, draw_pad, config.json colors).

Each sheet mirrors what ships: same durations, same distances, same easing. Hold or tap
the pad to play it. Regenerate with `python gen_press.py`, then re-seed the canvas.
"""
import json
import os

OUT = os.path.dirname(os.path.abspath(__file__))

FONT = "'Segoe UI', system-ui, -apple-system, sans-serif"
ACC = "#c9d400"          # idle_outline / pressed_fill / pressed_outline
FLASH = "#f2ff66"        # pressed_fill lightened, as Qt's QColor.lighter(190) leaves it
IDLE_FILL = "#1e1e1e"
IDLE_TEXT = "#ffffff"
PRESSED_TEXT = "#000000"
PAD_W, PAD_H = 100, 140  # config.json cell_w / cell_h
# overlay.draw_pad: glow pens of width 12 at .18 and 6 at .09, then the 1.2 -> 2.2 px outline
IDLE_SHADOW = f"0 0 0 1.2px {ACC}"
LIT_SHADOW = f"0 0 0 2.2px {ACC}, 0 0 0 3px rgba(201, 212, 0, 0.09), 0 0 0 6px rgba(201, 212, 0, 0.18)"
W, H = 560, 300

BASE_CSS = f"""
    body {{ margin: 0; background: #000000; color: #f5f5f7; font-family: {FONT}; font-size: 13.33px; }}
    a {{ color: #b6ff00; text-decoration: none; }} a:hover {{ color: #ceff59; }}
    * {{ box-sizing: border-box; }}
    .pad {{
      position: relative; width: {PAD_W}px; height: {PAD_H}px; border-radius: 10px;
      background: {IDLE_FILL}; color: {IDLE_TEXT}; box-shadow: {IDLE_SHADOW};
      display: flex; align-items: center; justify-content: center;
      font-weight: 700; font-size: 17.33px; line-height: 1;
      cursor: pointer; user-select: none; -webkit-user-select: none; touch-action: none;
      transition: background-color 140ms linear, color 140ms linear, box-shadow 140ms linear;
    }}
    .pad.is-down {{ background: {ACC}; color: {PRESSED_TEXT}; box-shadow: {LIT_SHADOW}; transition-duration: 0ms; }}
    .label {{ position: relative; z-index: 1; }}
"""

# overlay.press_scale: squash to (.93, .90) over 60 ms, then SPRING_KEYS over 550 ms
SPRING_CSS = """
    .pad.is-down { transform: scale(.93, .9); transition: transform 60ms ease-out, background-color 0ms, color 0ms, box-shadow 0ms; }
    .pad.is-up { animation: spring .55s linear both; }
    @keyframes spring {
      0%   { transform: scale(.93, .90); }
      45%  { transform: scale(1.06, 1.08); }
      75%  { transform: scale(.985, .99); }
      100% { transform: scale(1, 1); }
    }
"""

# overlay._draw_press_marks: a ring from .12 to 1.0 of the pad's half-diagonal (86 px here),
# clipped to the body, over 600 ms, in the label color so it reads on the lit fill.
# Clipping is why a press never paints over its neighbour.
RIPPLE_CSS = f"""
    .pad {{ overflow: hidden; }}
    .ring {{
      position: absolute; left: 50%; top: 50%; border-radius: 50%; border: 3.5px solid {PRESSED_TEXT};
      opacity: 0; pointer-events: none;
    }}
    .pad.is-down .ring {{ animation: ring .6s cubic-bezier(.33,0,.67,1) forwards; }}
    @keyframes ring {{
      0%   {{ width: 21px; height: 21px; margin: -10.5px 0 0 -10.5px; opacity: .6; }}
      100% {{ width: 172px; height: 172px; margin: -86px 0 0 -86px; opacity: 0; }}
    }}
"""

# overlay: pop over 450 ms, ten sparks from .30 to 1.10 of the half-width (15 -> 55 px) over 700 ms.
# They die just past the rim because the overlay window is only 4 px bigger than the pad grid.
BURST_CSS = f"""
    .pad.is-down {{ animation: pop .45s linear both; }}
    @keyframes pop {{
      0%   {{ transform: scale(1); }}
      35%  {{ transform: scale(.95); }}
      70%  {{ transform: scale(1.05); }}
      100% {{ transform: scale(1); }}
    }}
    .burst {{ position: absolute; left: 50%; top: 50%; width: 0; height: 0; pointer-events: none; z-index: 2; }}
    .spark {{
      position: absolute; left: -4.5px; top: -4.5px; width: 9px; height: 9px; border-radius: 50%;
      background: {PRESSED_TEXT}; animation: spark .7s cubic-bezier(.33,0,.67,1) forwards;
    }}
    .spark:nth-child(1) {{ --a: 0deg; }}    .spark:nth-child(2) {{ --a: 36deg; }}
    .spark:nth-child(3) {{ --a: 72deg; }}   .spark:nth-child(4) {{ --a: 108deg; }}
    .spark:nth-child(5) {{ --a: 144deg; }}  .spark:nth-child(6) {{ --a: 180deg; }}
    .spark:nth-child(7) {{ --a: 216deg; }}  .spark:nth-child(8) {{ --a: 252deg; }}
    .spark:nth-child(9) {{ --a: 288deg; }}  .spark:nth-child(10) {{ --a: 324deg; }}
    .spark:nth-child(even) {{ background: {IDLE_TEXT}; width: 6.3px; height: 6.3px; left: -3.15px; top: -3.15px; }}
    @keyframes spark {{
      0%   {{ transform: rotate(var(--a)) translateX(15px) scale(1); opacity: 1; }}
      55%  {{ opacity: 1; }}
      100% {{ transform: rotate(var(--a)) translateX(55px) scale(0); opacity: 0; }}
    }}
"""

# overlay: the glow pens widen from 12/6 px to 24/12 px while their alpha decays, and the
# color itself fades over 650 ms instead of the usual 140 (overlay.PRESS_FADE_MS).
EMBER_CSS = f"""
    .pad.is-up {{ animation: ember .65s linear both; }}
    @keyframes ember {{
      0%   {{ background: {ACC}; color: {PRESSED_TEXT};
             box-shadow: 0 0 0 2.2px {ACC}, 0 0 0 3px rgba(201, 212, 0, 0.13), 0 0 0 6px rgba(201, 212, 0, 0.24); }}
      45%  {{ background: #6f7600; color: #202200;
             box-shadow: 0 0 0 1.6px rgba(201, 212, 0, .75), 0 0 0 5px rgba(201, 212, 0, 0.05), 0 0 0 9px rgba(201, 212, 0, 0.09); }}
      100% {{ background: {IDLE_FILL}; color: {IDLE_TEXT};
             box-shadow: 0 0 0 1.2px {ACC}, 0 0 0 6px rgba(201, 212, 0, 0), 0 0 0 12px rgba(201, 212, 0, 0); }}
    }}
"""

# overlay.draw_pad: the pressed fill and outline are mixed towards QColor.lighter(190) and
# settle over 220 ms. Every pad style inherits it, because it is done in the color set.
STRIKE_CSS = f"""
    .pad.is-down {{ animation: strike .22s cubic-bezier(.33,0,.67,1) both; }}
    @keyframes strike {{
      0%   {{ background: {FLASH}; color: {PRESSED_TEXT};
             box-shadow: 0 0 0 2.2px {FLASH}, 0 0 0 4px rgba(242, 255, 102, 0.18), 0 0 0 8px rgba(242, 255, 102, 0.28); }}
      100% {{ background: {ACC}; color: {PRESSED_TEXT}; box-shadow: {LIT_SHADOW}; }}
    }}
"""

RING_HTML = '<span class="ring"></span>'
BURST_HTML = ('<sc-if value="{{ burst }}" hint-placeholder-val="{{ false }}"><span class="burst">'
              + '<span class="spark"></span>' * 10 + '</span></sc-if>')

LOGIC = """
class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.state = { phase: 'idle', burst: false };
    this.t = null;
    this.tb = null;
  }
  componentWillUnmount() {
    clearTimeout(this.t);
    clearTimeout(this.tb);
  }
  renderVals() {
    const ph = this.state.phase;
    return {
      cls: ph === 'down' ? 'is-down' : ph === 'up' ? 'is-up' : '',
      burst: this.state.burst,
      down: (e) => {
        if (e && e.preventDefault) e.preventDefault();
        clearTimeout(this.t);
        clearTimeout(this.tb);
        this.setState({ phase: 'down', burst: true });
        this.tb = setTimeout(() => this.setState({ burst: false }), 720);
      },
      up: () => {
        if (this.state.phase !== 'down') return;
        this.setState({ phase: 'up' });
        clearTimeout(this.t);
        this.t = setTimeout(() => this.setState({ phase: 'idle' }), UP_MS);
      },
    };
  }
}
"""


def sheet(name, desc, tradeoff, css="", extra_html="", up_ms=150):
    inner = (
        f'<div style="width: {W}px; height: {H}px; background: #0c0c0e; position: relative; overflow: hidden; display: flex; flex-direction: column;">'
        f'<div style="height: 236px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px;">'
        f'<div class="pad {{{{ cls }}}}" onPointerDown="{{{{ down }}}}" onPointerUp="{{{{ up }}}}" onPointerLeave="{{{{ up }}}}" onPointerCancel="{{{{ up }}}}">'
        f'<span class="label">Space</span>{extra_html}</div>'
        f'<div style="color: #a1a1a6; font-size: 10.67px;">hold or tap</div>'
        f'</div>'
        f'<div style="display: flex; flex-direction: column; gap: 3px; padding: 0 20px 14px 20px;">'
        f'<div style="font-size: 14.67px; font-weight: 600;">{name}</div>'
        f'<div style="color: #a1a1a6; font-size: 10.67px;">{desc} Trade-off: {tradeoff}</div>'
        f'</div></div>'
    )
    props = json.dumps({"$preview": {"width": W, "height": H}})
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <style>{BASE_CSS}{css}  </style>
</helmet>
{inner}
</x-dc>
<script data-dc-script data-props='{props}'>{LOGIC.replace("UP_MS", str(up_ms))}</script>
</body>
</html>
"""


# file, canvas title, heading, what it does, trade-off, css, extra markup, release-phase ms
OPTIONS = [
    ("Main.dc.html", "Classic", "Classic",
     "Lights the moment the key goes down and fades out over 140 ms. What earlier versions did.",
     "a tap and a hold look the same, and nothing marks the moment of impact.",
     "", "", 150),
    ("PressSpring.dc.html", "Spring", "Spring",
     "The pad squashes while held and springs back with a small overshoot on release.",
     "movement can distract on dense layouts.",
     SPRING_CSS, "", 560),
    ("PressRipple.dc.html", "Ripple", "Ripple",
     "A ring travels out from the middle of the pad on every press, clipped to the pad edge.",
     "on a small pad the ring is over almost as soon as it starts.",
     RIPPLE_CSS, RING_HTML, 150),
    ("PressBurst.dc.html", "Burst", "Burst",
     "The pad pops and scatters sparks across its face, then sits lit while held.",
     "busy during fast combos, and the sparks stay near the pad so they are not clipped.",
     BURST_CSS, BURST_HTML, 150),
    ("PressEmber.dc.html", "Ember", "Ember",
     "Release blooms the glow wide and lets it die out over 650 ms, like a cooling coil.",
     "the lingering glow blurs very fast sequences.",
     EMBER_CSS, "", 660),
    ("PressStrike.dc.html", "Strike", "Strike",
     "The press flashes bright and settles into the pressed color in about a fifth of a second.",
     "the flash can be harsh over a bright scene.",
     STRIKE_CSS, "", 150),
]


def main():
    boards = []
    for i, (fname, title, name, desc, tradeoff, css, extra, up_ms) in enumerate(OPTIONS):
        with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
            f.write(sheet(name, desc, tradeoff, css, extra, up_ms))
        boards.append({"file": fname, "title": title, "x": (i % 3) * 660, "y": (i // 3) * 440,
                       "w": W, "h": H, "is_interactive": True})
    canvas = {
        "artboards": boards,
        "annotations": [{"id": "shipped", "x": 0, "y": -110, "w": 700,
                         "text": "All six ship as the Press setting under Pads on Appearance.\n"
                                 "Same timings and distances as the app; hold or tap a pad to play it."}],
        "launch": {"view": "canvas"},
    }
    with open(os.path.join(OUT, "canvas.json"), "w", encoding="utf-8") as f:
        json.dump(canvas, f, indent=2)
    print(f"wrote {len(boards)} artboards + canvas.json to {OUT}")


if __name__ == "__main__":
    main()
