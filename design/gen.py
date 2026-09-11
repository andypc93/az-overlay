"""Generate AZ-Overlay design artboards (.dc.html) from the app's real theme values."""
import json
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# THEMES["dark"] from settings_ui.py
T = dict(bg="#000000", card="#161616", field="#242424", line="#333333", text="#f5f5f7",
         muted="#a1a1a6", accent="#b6ff00", accent_text="#101600", accent_hover="#ceff59",
         hover="#303030", pressed="#3c3c3c", strong_line="#6a6a6a", disabled="#757575",
         badge_bg="#253314", badge_text="#b6ff00", selection="#253314", sidebar="#0b0b0b",
         preview="#121212", preview_end="#1f1f1f")
# Overlay colors from config.json
C = dict(idle_fill="#1e1e1e", idle_outline="#c9d400", pressed_fill="#c9d400",
         idle_text="#ffffff", pressed_text="#000000", pressed_outline="#c9d400")

FONT = "'Segoe UI', system-ui, -apple-system, sans-serif"
PT = 96 / 72  # Qt pt -> css px
W, H = 1040, 860
KEYS_H, HELP_H = 1100, 960  # these pages scroll at the default 860 height; show them at full length

BASE_CSS = f"""
    body {{ margin: 0; background: {T['bg']}; color: {T['text']}; font-family: {FONT}; font-size: {10*PT:.2f}px; }}
    a {{ color: {T['accent']}; text-decoration: none; }} a:hover {{ color: {T['accent_hover']}; }}
    * {{ box-sizing: border-box; }}
"""


# ---- pieces ---------------------------------------------------------------
def icon(name):
    stroke = f'fill="none" stroke="{T["accent_text"]}" stroke-width="1.6"'
    if name == "Layout":
        g = (f'<rect x="7" y="7" width="18" height="18" rx="3" {stroke}></rect>'
             f'<line x1="13" y1="7" x2="13" y2="25" {stroke}></line>'
             f'<line x1="13" y1="15" x2="25" y2="15" {stroke}></line>')
    elif name == "Keys":
        g = "".join(f'<rect x="{x}" y="{y}" width="4" height="4" rx="1" {stroke}></rect>'
                    for x in (7, 14, 21) for y in (9, 16))
        g += f'<line x1="11" y1="24" x2="21" y2="24" {stroke}></line>'
    elif name == "Appearance":
        g = "".join(f'<circle cx="{x}" cy="{y}" r="5" {stroke}></circle>' for x, y in ((12, 12), (20, 12), (16, 20)))
    else:
        glyph = "i" if name == "About" else "?"
        g = (f'<circle cx="16" cy="16" r="10" {stroke}></circle>'
             f'<text x="16" y="22.5" text-anchor="middle" font-family="{FONT}" font-size="18" font-weight="700" fill="{T["accent_text"]}">{glyph}</text>')
    gid = f"g{name}"
    return (f'<svg width="28" height="28" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" style="flex: 0 0 auto;">'
            f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{T["accent"]}"></stop><stop offset="1" stop-color="{T["accent"]}"></stop></linearGradient></defs>'
            f'<rect x="0" y="0" width="32" height="32" rx="8" fill="url(#{gid})"></rect>{g}</svg>')


def arrow():
    return (f'<svg width="10" height="10" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" style="flex: 0 0 auto;">'
            f'<polygon points="4,7 16,7 10,13" fill="{T["text"]}"></polygon></svg>')


def combo(text, width=None, flex=None, placeholder=False):
    size = f"width: {width}px;" if width else ""
    grow = f"flex: {flex};" if flex else ""
    color = T["muted"] if placeholder else T["text"]
    return (f'<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; {size} {grow} '
            f'background: {T["field"]}; border: 1px solid transparent; border-radius: 9px; padding: 7px 10px 7px 10px; min-height: 36px; color: {color};">'
            f'<span>{text}</span>{arrow()}</div>')


def button(text, kind="default", min_width=None, min_height=None, disabled=False):
    bg, color, weight = T["field"], T["text"], 600
    if kind == "primary":
        bg, color = T["accent"], T["accent_text"]
    elif kind == "quiet":
        bg, color, weight = "transparent", T["accent"], 400
    if disabled:
        bg, color = T["field"], T["disabled"]
    mw = f"min-width: {min_width}px;" if min_width else ""
    mh = f"min-height: {min_height}px;" if min_height else ""
    return (f'<div style="display: flex; align-items: center; justify-content: center; background: {bg}; color: {color}; '
            f'border: 1px solid transparent; border-radius: 10px; padding: 8px 15px; font-weight: {weight}; {mw} {mh} white-space: nowrap;">{text}</div>')


def section(text):
    return (f'<div style="color: {T["muted"]}; font-size: {8*PT:.2f}px; font-weight: 600; letter-spacing: 1.2px; '
            f'text-transform: uppercase;">{text}</div>')


def muted(text, wrap=True):
    ws = "" if wrap else "white-space: nowrap;"
    return f'<div style="color: {T["muted"]}; {ws}">{text}</div>'


def card(*children, extra=""):
    return (f'<div style="display: flex; flex-direction: column; gap: 14px; background: {T["card"]}; border: 1px solid {T["line"]}; '
            f'border-radius: 18px; padding: 18px 22px 18px 22px; {extra}">' + "".join(children) + '</div>')


def disclosure(title, opened=False):
    glyph = "▾" if opened else "▸"
    color = T["accent"] if opened else T["text"]
    return (f'<div style="display: flex; align-items: center; gap: 10px; background: {T["card"]}; border: 1px solid {T["line"]}; '
            f'border-radius: 12px; padding: 12px 16px; color: {color};">'
            f'<span style="font-size: 11px; width: 10px;">{glyph}</span><span>{title}</span></div>')


def switch(text, on=False):
    track = T["accent"] if on else T["strong_line"]
    knob_x = 22 if on else 4
    return (f'<div style="display: flex; align-items: center; height: 32px;">'
            f'<div style="position: relative; width: 56px; height: 32px; flex: 0 0 auto;">'
            f'<div style="position: absolute; left: 2px; top: 4px; width: 42px; height: 24px; border-radius: 12px; background: {track};"></div>'
            f'<div style="position: absolute; left: {knob_x}px; top: 6px; width: 20px; height: 20px; border-radius: 10px; background: {T["accent_text"]};"></div>'
            f'</div><span>{text}</span></div>')


def slider(label, pct, value):
    return (f'<div style="display: flex; align-items: center; gap: 16px;">'
            f'<div style="width: 46px; flex: 0 0 auto;">{label}</div>'
            f'<div style="flex: 1; position: relative; height: 32px;">'
            f'<div style="position: absolute; left: 0; right: 0; top: 13.5px; height: 5px; border-radius: 2px; background: {T["line"]};"></div>'
            f'<div style="position: absolute; left: 0; width: {pct}%; top: 13.5px; height: 5px; border-radius: 2px; background: {T["accent"]};"></div>'
            f'<div style="position: absolute; left: calc({pct}% - 11.5px); top: 4.5px; width: 23px; height: 23px; border-radius: 12px; background: #ffffff; border: 1px solid {T["line"]};"></div>'
            f'</div>'
            f'<div style="width: 68px; flex: 0 0 auto; text-align: center; color: {T["accent"]}; background: {T["selection"]}; '
            f'border-radius: 8px; padding: 4px 8px; font-weight: 600;">{value}</div></div>')


def field(text, width=None, align="left", placeholder=False, flex=None):
    size = f"width: {width}px;" if width else ""
    grow = f"flex: {flex};" if flex else ""
    color = T["muted"] if placeholder else T["text"]
    return (f'<div style="{size} {grow} background: {T["field"]}; border: 1px solid transparent; border-radius: 9px; '
            f'padding: 7px 10px; min-height: 36px; display: flex; align-items: center; justify-content: {"center" if align == "center" else "flex-start"}; color: {color};">{text}</div>')


def stepper(value):
    step = (f'style="display: flex; align-items: center; justify-content: center; width: 36px; height: 34px; border-radius: 10px; '
            f'background: {T["field"]}; color: {T["accent"]}; font-size: {15*PT:.2f}px; flex: 0 0 auto;"')
    return (f'<div style="display: flex; align-items: center; gap: 4px; width: 208px;">'
            f'<div {step}>−</div>{field(value, align="center", flex=1)}<div {step}>+</div></div>')


def form_row(label, control, label_w=90):
    return (f'<div style="display: flex; align-items: center; gap: 16px;">'
            f'<div style="width: {label_w}px; flex: 0 0 auto;">{label}</div>{control}</div>')


def form(*rows):
    return '<div style="display: flex; flex-direction: column; gap: 12px;">' + "".join(rows) + '</div>'


# ---- chrome ---------------------------------------------------------------
def header():
    return (f'<div style="display: flex; flex-direction: column; gap: 18px; background: {T["card"]}; border-bottom: 1px solid {T["line"]}; padding: 20px 26px 18px 26px;">'
            f'<div style="display: flex; align-items: center; gap: 10px;">{muted("Every move. On display.", wrap=False)}'
            f'<div style="flex: 1;"></div><span>Theme</span>{combo("Dark", width=100)}</div>'
            f'<div style="display: flex; align-items: center; gap: 10px;">{muted("Layout", wrap=False)}'
            f'{combo("Choose a saved layout", flex=1, placeholder=True)}{button("Save layout")}{button("More", kind="quiet")}'
            f'<div style="width: 8px;"></div>{button("+ New layout", kind="primary")}</div></div>')


def sidebar(active):
    items = []
    for name in ("Layout", "Keys", "Appearance", "About", "Help"):
        sel = name == active
        bg = T["selection"] if sel else "transparent"
        color = T["accent"] if sel else T["muted"]
        weight = 600 if sel else 400
        items.append(f'<div style="display: flex; align-items: center; gap: 12px; padding: 10px; margin: 3px 0; border-radius: 10px; '
                     f'background: {bg}; color: {color}; font-weight: {weight};">{icon(name)}<span>{name}</span></div>')
    return (f'<div style="width: 184px; flex: 0 0 auto; display: flex; flex-direction: column; gap: 12px; background: {T["sidebar"]}; '
            f'border-right: 1px solid {T["line"]}; padding: 28px 12px 20px 12px;">{section("Workspace")}'
            f'<div style="display: flex; flex-direction: column;">' + "".join(items) + '</div></div>')


def footer():
    return (f'<div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px; background: {T["card"]}; '
            f'border-top: 1px solid {T["line"]}; padding: 10px 20px;">{switch("Overlay visible", on=False)}{button("Quit overlay", kind="quiet")}</div>')


def page(title, description, *cards):
    return (f'<div style="flex: 1; overflow: hidden; display: flex; flex-direction: column; gap: 16px; padding: 24px 28px 24px 28px;">'
            f'<div style="font-size: {27*PT:.2f}px; font-weight: 700; letter-spacing: -1px; line-height: 1.2;">{title}</div>'
            f'{muted(description)}<div style="height: 4px;"></div>' + "".join(cards) + '</div>')


def window(active, body, height=H):
    return (f'<div style="width: {W}px; height: {height}px; display: flex; flex-direction: column; background: {T["bg"]}; overflow: hidden;">'
            f'{header()}<div style="flex: 1; display: flex; min-height: 0;">{sidebar(active)}{body}</div>{footer()}</div>')


def doc(inner, extra_css=""):
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <style>{BASE_CSS}{extra_css}
  </style>
</helmet>
{inner}
</x-dc>
</body>
</html>
"""


# ---- pages ----------------------------------------------------------------
def layout_page():
    c1 = card(
        section("Position your overlay"),
        f'<div style="display: flex;">{button("Edit on screen", kind="primary", min_width=156, min_height=38)}</div>',
        muted("Drag to reposition. Scroll to resize. Choose Done editing when you’re finished."),
        form(slider("Size", 10, "50%"), slider("Opacity", 83, "85%")),
        disclosure("Precise position &amp; scale"),
    )
    return window("Layout", page("Layout", "Get your overlay in the right place, at the right size.",
                                 c1, disclosure("Key dimensions"), disclosure("Keyboard shortcuts")))


def keys_page():
    rows = [("Page Up", ""), ("9", ""), ("Alt", ""), ("H", ""), ("X", ""), ("F1", ""), ("Esc", "")]
    thead = (f'<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); color: {T["muted"]}; '
             f'font-size: {8*PT:.2f}px; font-weight: 600; border-bottom: 1px solid {T["line"]};">'
             f'<div style="padding: 8px;">Label</div><div style="padding: 8px;">Input</div></div>')
    trs = ""
    for i, (label, inp) in enumerate(rows):
        bg = T["selection"] if i == 0 else "transparent"
        trs += (f'<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); height: 42px; align-items: center; '
                f'background: {bg}; border-bottom: 1px solid {T["line"]};"><div style="padding: 8px;">{label}</div><div style="padding: 8px;">{inp}</div></div>')
    table = f'<div style="display: flex; flex-direction: column; background: {T["card"]};">{thead}{trs}</div>'
    c1 = card(
        section("Pads"),
        muted("Double-click a cell to edit. Leave Input empty to use the label, or select a pad and capture a key or controller button."),
        switch("Show all pads"),
        f'<div style="display: flex; align-items: center; gap: 10px;">{field("Search by label or input", placeholder=True, flex=1)}{muted("30 / 30 pads", wrap=False)}</div>',
        f'<div style="display: flex; align-items: center; gap: 10px;">{button("Record input", kind="primary")}<div style="flex: 1;"></div>{button("Add pad")}{button("Remove", kind="quiet")}</div>',
        f'<div style="display: flex; align-items: center; gap: 10px;">{button("Add row")}{button("Add column")}</div>',
        muted("Selected: Page Up"),
        table,
        switch("Edit position &amp; size"),
    )
    return window("Keys", page("Keys &amp; inputs", "Choose a pad. Record an input. Make it yours.", c1, disclosure("Sticks &amp; d-pads")), height=KEYS_H)


def pad_preview():
    # PadPreview: width 756 (card inner), height 160, ratio 0.77
    w, h, gap, r = 77, 108, 28, 10
    x0, y0 = (756 - (2 * w + gap)) / 2, (160 - h - 18) / 2
    font_px = 13 * PT
    out = (f'<svg width="756" height="160" viewBox="0 0 756 160" xmlns="http://www.w3.org/2000/svg" style="display: block;">'
           f'<defs><linearGradient id="pv" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{T["preview"]}"></stop>'
           f'<stop offset="1" stop-color="{T["preview_end"]}"></stop></linearGradient></defs>'
           f'<rect x="0" y="0" width="756" height="160" rx="14" fill="url(#pv)"></rect>')
    for x, state in ((x0, "idle"), (x0 + w + gap, "pressed")):
        if state == "pressed":
            out += (f'<rect x="{x}" y="{y0}" width="{w}" height="{h}" rx="{r}" fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.18" stroke-width="12"></rect>'
                    f'<rect x="{x}" y="{y0}" width="{w}" height="{h}" rx="{r}" fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.09" stroke-width="6"></rect>')
        sw = 1.2 if state == "idle" else 2.2
        out += (f'<rect x="{x}" y="{y0}" width="{w}" height="{h}" rx="{r}" fill="{C[state + "_fill"]}" stroke="{C[state + "_outline"]}" stroke-width="{sw}"></rect>'
                f'<text x="{x + w / 2}" y="{y0 + h / 2 + font_px * 0.35}" text-anchor="middle" font-family="{FONT}" font-size="{font_px:.1f}" font-weight="700" fill="{C[state + "_text"]}">Space</text>'
                f'<text x="{x + w / 2}" y="{y0 + h + 16}" text-anchor="middle" font-family="{FONT}" font-size="{8 * PT:.2f}" fill="{T["muted"]}">{state}</text>')
    return out + "</svg>"


def color_button(hexval):
    return (f'<div style="display: flex; align-items: center; gap: 8px; width: 126px; height: 36px; padding: 0 12px; border-radius: 10px; '
            f'background: {T["field"]}; font-family: Consolas, {FONT}; font-size: 12px; justify-content: center;">'
            f'<span style="width: 18px; height: 18px; border-radius: 9px; background: {hexval}; border: 0.5px solid {T["strong_line"]}; flex: 0 0 auto;"></span>'
            f'<span>{hexval.upper()}</span></div>')


def appearance_page():
    c0 = card(section("Preview"), pad_preview())
    c1 = card(section("Key text"),
              form(form_row("Font", combo("Segoe UI", width=200), label_w=56),
                   form_row("Size", stepper("13 pt"), label_w=56),
                   form_row("Weight", switch("Bold", on=True), label_w=56)),
              extra="flex: 1;")
    grid_cells = [f'<div></div>', muted("Idle"), muted("Pressed")]
    for part, text in (("fill", "Fill"), ("outline", "Border"), ("text", "Text")):
        grid_cells += [f'<div>{text}</div>', color_button(C[f"idle_{part}"]), color_button(C[f"pressed_{part}"])]
    grid = (f'<div style="display: grid; grid-template-columns: 56px 126px 126px; column-gap: 16px; row-gap: 8px; align-items: center;">'
            + "".join(grid_cells) + '</div>')
    c2 = card(section("Colors"), grid, f'<div style="display: flex;">{button("Reset colors", kind="quiet")}</div>', extra="flex: 1;")
    columns = f'<div style="display: flex; gap: 16px; align-items: stretch;">{c1}{c2}</div>'
    return window("Appearance", page("Appearance", "Make it yours. Preview your font and colors as you edit.", c0, columns))


def about_page():
    overview = card(section("AZ-Overlay"),
                    muted("A customizable input overlay for Azeron keypads, keyboards, and controllers. Show your inputs as you play "
                          "with a transparent, click-through overlay and live layout editing."))
    credits = card(section("Created by Andres Perez"),
                   muted("Copyright 2026 Andres Perez. Released under the MIT License."),
                   muted("Built with PySide6, pynput, and the optional pygame-ce controller backend."))
    donations = card(section("Support AZ-Overlay"),
                     muted("Enjoying the overlay? A donation helps support its development. Thank you!"),
                     f'<div style="display: flex; gap: 12px;">{button("Donate with PayPal", disabled=True)}{button("Donate with Venmo")}</div>')
    return window("About", page("About", "Every move. On display.", overview, credits, donations))


def help_page():
    contact = (f'<div style="display: flex; flex-direction: column; gap: 14px; border: 1px solid {T["badge_text"]}; border-radius: 18px; '
               f'padding: 18px 22px; background: linear-gradient(135deg, {T["selection"]}, {T["card"]});">'
               f'{section("Let’s talk")}'
               f'<div style="font-size: {20*PT:.2f}px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2;">A little help. A better overlay.</div>'
               f'{muted("Questions, bugs, or a feature you’d love to see? Get in touch with Andres.")}'
               f'<div style="height: 6px;"></div>'
               f'<div style="display: flex; align-items: center; gap: 16px;"><div style="flex: 1;">andres6perez@gmail.com</div>{button("Email", kind="primary", min_width=110)}</div>'
               f'{muted("Opens Gmail in your browser. For bugs, include your device and what happened.")}</div>')
    steps = ""
    for n, (heading, desc) in enumerate((
        ("Pick your layout", "Choose + New layout and start with a template for your device."),
        ("Find the perfect spot", "On Layout, choose Edit on screen. Drag to move, scroll to resize, then choose Done editing."),
        ("Connect your inputs", "On Keys, select a pad and choose Record input to assign a key or controller button."),
        ("Make it yours", "Adjust fonts and colors on Appearance. Changes to saved layouts are saved automatically."),
    ), start=1):
        steps += (f'<div style="display: flex; gap: 14px; align-items: flex-start;">'
                  f'<div style="width: 40px; height: 40px; flex: 0 0 auto; display: flex; align-items: center; justify-content: center; '
                  f'border-radius: 12px; color: {T["accent"]}; background: {T["selection"]}; font-size: {11*PT:.2f}px; font-weight: 700;">{n:02}</div>'
                  f'<div style="display: flex; flex-direction: column; gap: 3px; flex: 1;">'
                  f'<div style="font-size: {11*PT:.2f}px; font-weight: 600;">{heading}</div>{muted(desc)}</div></div>')
    guide = card(section("Quick start"), steps)
    tip = card(section("Can’t see your overlay?"),
               muted("Turn on Overlay visible below, and use windowed or borderless mode in your game."))
    return window("Help", page("Help", "Get set up, find your way, or send an idea.", contact, guide, tip), height=HELP_H)


# ---- overlay --------------------------------------------------------------
def overlay_page():
    with open(os.path.join(OUT, "..", "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    s = 0.75
    cw, ch, gap = cfg["cell_w"] * s, cfg["cell_h"] * s, cfg["gap"] * s
    radius = min(10 * s, cw * 0.2, ch * 0.2)
    font_px = int(cfg["font"]["size"] * s) * PT
    stick_px = int(int(cfg["font"]["size"] * s) * 0.75) * PT
    pressed = {"Space", "W"}

    def cell(col, row, w=1, h=1):
        return col * (cw + gap) + 2, row * (ch + gap) + 2, w * (cw + gap) - gap, h * (ch + gap) - gap

    ext_w = max(cell(k["col"], k["row"], k["w"], k["h"])[0] + cell(k["col"], k["row"], k["w"], k["h"])[2] for k in cfg["keys"])
    ext_h = max(cell(k["col"], k["row"], k["w"], k["h"])[1] + cell(k["col"], k["row"], k["w"], k["h"])[3] for k in cfg["keys"])
    for st in cfg["sticks"]:
        x, y, w, h = cell(st["col"], st["row"], st["w"], st["h"])
        ext_w, ext_h = max(ext_w, x + w), max(ext_h, y + h)
    ext_w, ext_h = ext_w + 4, ext_h + 4

    svg = ""
    for st in cfg["sticks"]:
        x, y, w, h = cell(st["col"], st["row"], st["w"], st["h"])
        cx, cy = x + w / 2, y + h / 2
        rad = min(w, h) * 0.30
        svg += (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{radius:.1f}" fill="{C["idle_fill"]}" stroke="{C["idle_outline"]}" stroke-width="1.2"></rect>'
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="none" stroke="{C["idle_outline"]}" stroke-width="1.2"></circle>')
        if st.get("axes"):
            kr = rad * 0.42
            svg += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{kr:.1f}" fill="{C["idle_outline"]}" stroke="{C["idle_outline"]}" stroke-width="1.2"></circle>'
        svg += (f'<text x="{x + w - 6:.1f}" y="{y + h - 4 - stick_px * 0.25:.1f}" text-anchor="end" font-family="{FONT}" font-size="{stick_px:.1f}" font-weight="700" fill="{C["idle_text"]}">{st["label"]}</text>')
        dot_r = rad * 0.30
        for name, dx, dy in (("up", 0, -1), ("down", 0, 1), ("left", -1, 0), ("right", 1, 0)):
            label = st.get(name)
            if not label:
                continue
            px, py = cx + dx * rad * 0.62, cy + dy * rad * 0.62
            lit = label in pressed
            fill = C["pressed_fill"] if lit else C["idle_fill"]
            if lit:
                svg += (f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{dot_r:.1f}" fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.18" stroke-width="12"></circle>'
                        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{dot_r:.1f}" fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.09" stroke-width="6"></circle>')
            svg += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{dot_r:.1f}" fill="{fill}" stroke="{C["idle_outline"]}" stroke-width="{2.2 if lit else 1.2}"></circle>'
            tx, ty = cx + dx * rad * 1.4, cy + dy * rad * 1.4
            tcol = C["pressed_outline"] if lit else C["idle_text"]
            svg += (f'<text x="{tx:.1f}" y="{ty + font_px * 0.35:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{font_px:.1f}" font-weight="700" fill="{tcol}">{label}</text>')
    for k in cfg["keys"]:
        if not k["label"]:
            continue
        x, y, w, h = cell(k["col"], k["row"], k["w"], k["h"])
        lit = k["label"] in pressed
        if lit:
            svg += (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{radius:.1f}" fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.18" stroke-width="12"></rect>'
                    f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{radius:.1f}" fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.09" stroke-width="6"></rect>')
        fill = C["pressed_fill"] if lit else C["idle_fill"]
        text = C["pressed_text"] if lit else C["idle_text"]
        label = k["label"]
        size = font_px if len(label) <= 5 else font_px * 0.8
        lines = label.split(" ") if len(label) > 5 else [label]
        svg += f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{radius:.1f}" fill="{fill}" stroke="{C["idle_outline"]}" stroke-width="{2.2 if lit else 1.2}"></rect>'
        cx, cy = x + w / 2, y + h / 2
        if len(lines) == 1:
            svg += f'<text x="{cx:.1f}" y="{cy + size * 0.35:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{size:.1f}" font-weight="700" fill="{text}">{label}</text>'
        else:
            for i, ln in enumerate(lines):
                dy = (i - (len(lines) - 1) / 2) * size * 1.15
                svg += f'<text x="{cx:.1f}" y="{cy + dy + size * 0.35:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{size:.1f}" font-weight="700" fill="{text}">{ln}</text>'

    frame_w, frame_h = 900, 760
    ox, oy = (frame_w - ext_w) / 2, (frame_h - ext_h) / 2
    inner = (f'<div style="width: {frame_w}px; height: {frame_h}px; background: #0c0c0e; position: relative; overflow: hidden;">'
             f'<svg width="{ext_w:.0f}" height="{ext_h:.0f}" viewBox="0 0 {ext_w:.1f} {ext_h:.1f}" xmlns="http://www.w3.org/2000/svg" '
             f'style="position: absolute; left: {ox:.0f}px; top: {oy:.0f}px; opacity: {cfg["opacity"]};">{svg}</svg></div>')
    return inner, frame_w, frame_h


# ---- emit -----------------------------------------------------------------
boards = {
    "Main.dc.html": layout_page(),
    "Keys.dc.html": keys_page(),
    "Appearance.dc.html": appearance_page(),
    "About.dc.html": about_page(),
    "Help.dc.html": help_page(),
}
overlay_html, ow, oh = overlay_page()
boards["Overlay.dc.html"] = overlay_html
for name, inner in boards.items():
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(doc(inner))

GX = W + 100
canvas = {
    "artboards": [
        {"file": "Main.dc.html", "title": "Settings · Layout", "x": 0, "y": 0, "w": W, "h": H},
        {"file": "Appearance.dc.html", "title": "Settings · Appearance", "x": GX, "y": 0, "w": W, "h": H},
        {"file": "Overlay.dc.html", "title": "Overlay · Cyborg 2 layout", "x": 2 * GX, "y": 0, "w": ow, "h": oh},
        {"file": "Keys.dc.html", "title": "Settings · Keys (full length)", "x": 0, "y": H + 140, "w": W, "h": KEYS_H},
        {"file": "Help.dc.html", "title": "Settings · Help (full length)", "x": GX, "y": H + 140, "w": W, "h": HELP_H},
        {"file": "About.dc.html", "title": "Settings · About", "x": 2 * GX, "y": H + 140, "w": W, "h": H},
    ],
    "launch": {"view": "canvas"},
}
with open(os.path.join(OUT, "canvas.json"), "w", encoding="utf-8") as f:
    json.dump(canvas, f, indent=2)
print("wrote", ", ".join(boards), "canvas.json")
