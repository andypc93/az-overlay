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
DARK = dict(T)
LIGHT = dict(bg="#f2f2f7", card="#ffffff", field="#f0f0f5", line="#e3e3eb", text="#1c1c1e",
             muted="#6c6c76", accent="#416800", accent_text="#ffffff", accent_hover="#325100",
             hover="#e8e8f0", pressed="#dddde7", strong_line="#aaaab5", disabled="#90909a",
             badge_bg="#e8f7ed", badge_line="#e8f7ed", badge_text="#416800", selection="#e6f3cf",
             sidebar="#eaeaf1", preview="#f5f8f0", preview_end="#eaf0df")
# Overlay colors from config.json
C = dict(idle_fill="#1e1e1e", idle_outline="#c9d400", pressed_fill="#c9d400",
         idle_text="#ffffff", pressed_text="#000000", pressed_outline="#c9d400")

FONT = "'Segoe UI', system-ui, -apple-system, sans-serif"
PT = 96 / 72  # Qt pt -> css px
W, H = 1040, 860
KEYS_H, HELP_H = 1100, 960  # these pages scroll at the default 860 height; show them at full length

def base_css():
    return f"""
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


def window(active, body, height=H, head=None, side=None):
    return (f'<div style="width: {W}px; height: {height}px; display: flex; flex-direction: column; background: {T["bg"]}; overflow: hidden;">'
            f'{head or header()}<div style="flex: 1; display: flex; min-height: 0;">{side or sidebar(active)}{body}</div>{footer()}</div>')


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
  <style>{base_css()}{extra_css}
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


def tile(svg_body):
    return (f'<div style="width: 40px; height: 40px; flex: 0 0 auto; display: flex; align-items: center; justify-content: center; '
            f'border-radius: 12px; color: {T["accent"]}; background: {T["selection"]};">'
            f'<svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{T["accent"]}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{svg_body}</svg></div>')


def tile_row(svg_body, heading, desc):
    return (f'<div style="display: flex; gap: 14px; align-items: flex-start;">{tile(svg_body)}'
            f'<div style="display: flex; flex-direction: column; gap: 3px; flex: 1;">'
            f'<div style="font-size: {11*PT:.2f}px; font-weight: 600;">{heading}</div>{muted(desc)}</div></div>')


ICON_PERSON = '<circle cx="12" cy="8" r="4"></circle><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7"></path>'
ICON_LICENSE = '<rect x="5" y="3" width="14" height="18" rx="2"></rect><line x1="9" y1="8" x2="15" y2="8"></line><line x1="9" y1="12" x2="15" y2="12"></line><line x1="9" y1="16" x2="12" y2="16"></line>'
ICON_STACK = '<path d="M12 3l9 5-9 5-9-5 9-5z"></path><path d="M3 13l9 5 9-5"></path><path d="M3 17l9 5 9-5"></path>'


def hero(section_text, title, body, row, note):
    return (f'<div style="display: flex; flex-direction: column; gap: 14px; border: 1px solid {T["badge_text"]}; border-radius: 18px; '
            f'padding: 18px 22px; background: linear-gradient(135deg, {T["selection"]}, {T["card"]});">'
            f'{section(section_text)}'
            f'<div style="font-size: {20*PT:.2f}px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2; text-wrap: pretty;">{title}</div>'
            f'{muted(body)}<div style="height: 6px;"></div>{row}{muted(note)}</div>')


def about_page():
    overview = hero(
        "AZ-Overlay",
        "A customizable input overlay for Azeron keypads, keyboards, and controllers.",
        "Show your inputs as you play with a transparent, click-through overlay and live layout editing.",
        f'<div style="display: flex; align-items: center; gap: 16px;"><div style="flex: 1;">Enjoying the overlay? A donation helps support its development. Thank you!</div>'
        f'{button("Donate with Venmo", kind="primary", min_width=110)}{button("Donate with PayPal", disabled=True)}</div>',
        "Opens Venmo in your browser. PayPal donations are not available yet.",
    )
    credits = card(
        section("Credits"),
        tile_row(ICON_PERSON, "Created by Andres Perez", "Copyright 2026 Andres Perez. Released under the MIT License."),
        tile_row(ICON_STACK, "Built with", "PySide6, pynput, and the optional pygame-ce controller backend."),
    )
    return window("About", page("About", "Every move. On display.", overview, credits))


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


# ---- stick direction sketches ---------------------------------------------
import math

S_SCALE = 0.75
S_W, S_H = 2 * (100 * S_SCALE + 8 * S_SCALE) - 8 * S_SCALE, 2 * (140 * S_SCALE + 8 * S_SCALE) - 8 * S_SCALE  # 156 x 216
S_R = 7.5
S_FONT = int(13 * S_SCALE) * PT   # 12px
S_LBL = int(int(13 * S_SCALE) * 0.75) * PT  # 8px
DIRS = (("W", 0, -1), ("S", 0, 1), ("A", -1, 0), ("D", 1, 0))


def _txt(x, y, text, size, fill, anchor="middle", weight=700, opacity=None):
    op = f' fill-opacity="{opacity}"' if opacity is not None else ""
    return (f'<text x="{x:.1f}" y="{y + size * 0.35:.1f}" text-anchor="{anchor}" font-family="{FONT}" '
            f'font-size="{size:.1f}" font-weight="{weight}" fill="{fill}"{op}>{text}</text>')


def _glow(shape_attrs, tag="circle"):
    return (f'<{tag} {shape_attrs} fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.18" stroke-width="12"></{tag}>'
            f'<{tag} {shape_attrs} fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.09" stroke-width="6"></{tag}>')


def _box(x, y):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{S_W:.1f}" height="{S_H:.1f}" rx="{S_R}" fill="{C["idle_fill"]}" stroke="{C["idle_outline"]}" stroke-width="1.2"></rect>'


def stick_current(x, y, active):
    cx, cy = x + S_W / 2, y + S_H / 2
    rad = min(S_W, S_H) * 0.30
    dy_off = -0.8 if active else 0
    kx, ky, kr = cx, cy + dy_off * rad * 0.6, rad * 0.42
    out = _box(x, y)
    out += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="none" stroke="{C["idle_outline"]}" stroke-width="1.2"></circle>'
    out += f'<circle cx="{kx:.1f}" cy="{ky:.1f}" r="{kr:.1f}" fill="{C["idle_outline"]}" stroke="{C["idle_outline"]}" stroke-width="1.2"></circle>'
    out += _txt(x + S_W - 6, y + S_H - 4 - S_LBL * 0.6, "Left Stick", S_LBL, C["idle_text"], anchor="end")
    for name, dx, dy in DIRS:
        lit = active and name == "W"
        px, py, dr = cx + dx * rad * 0.62, cy + dy * rad * 0.62, rad * 0.30
        if lit:
            out += _glow(f'cx="{px:.1f}" cy="{py:.1f}" r="{dr:.1f}"')
        out += (f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{dr:.1f}" fill="{C["pressed_fill"] if lit else C["idle_fill"]}" '
                f'stroke="{C["idle_outline"]}" stroke-width="{2.2 if lit else 1.2}"></circle>')
        out += _txt(cx + dx * rad * 1.4, cy + dy * rad * 1.4, name, S_FONT, C["pressed_outline"] if lit else C["idle_text"])
    return out


def stick_ring(x, y, active):
    """A: ring gauge. Deflection lights an arc on the outer ring; letters sit outside the ring."""
    cx, cy = x + S_W / 2, y + S_H / 2 + 6
    ring = 50
    out = _box(x, y)
    out += _txt(cx, y + 6 + S_LBL * 0.6, "Left Stick", S_LBL, C["idle_text"], weight=600)
    out += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{ring}" fill="none" stroke="{C["idle_outline"]}" stroke-opacity="0.4" stroke-width="1.2"></circle>'
    for name, dx, dy in DIRS:  # tick marks
        out += (f'<line x1="{cx + dx * (ring - 5):.1f}" y1="{cy + dy * (ring - 5):.1f}" x2="{cx + dx * (ring + 5):.1f}" y2="{cy + dy * (ring + 5):.1f}" '
                f'stroke="{C["idle_outline"]}" stroke-opacity="0.6" stroke-width="1.2"></line>')
    if active:  # arc centred on "up", 70 degrees wide
        a0, a1 = math.radians(-90 - 35), math.radians(-90 + 35)
        d = (f'M {cx + ring * math.cos(a0):.1f} {cy + ring * math.sin(a0):.1f} A {ring} {ring} 0 0 1 '
             f'{cx + ring * math.cos(a1):.1f} {cy + ring * math.sin(a1):.1f}')
        out += f'<path d="{d}" fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.25" stroke-width="14" stroke-linecap="round"></path>'
        out += f'<path d="{d}" fill="none" stroke="{C["pressed_outline"]}" stroke-width="5" stroke-linecap="round"></path>'
    ky = cy - (0.8 * ring * 0.55 if active else 0)
    if active:
        out += f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx:.1f}" y2="{ky:.1f}" stroke="{C["pressed_outline"]}" stroke-opacity="0.6" stroke-width="2"></line>'
    out += f'<circle cx="{cx:.1f}" cy="{ky:.1f}" r="11" fill="{C["pressed_fill"] if active else C["idle_outline"]}"></circle>'
    for name, dx, dy in DIRS:
        lit = active and name == "W"
        out += _txt(cx + dx * (ring + 18), cy + dy * (ring + 18), name, S_FONT, C["pressed_outline"] if lit else C["idle_text"], opacity=None if lit else 0.85)
    return out


def stick_petals(x, y, active):
    """B: four petals. Each direction is a wedge-shaped key around a small analog dot."""
    cx, cy = x + S_W / 2, y + S_H / 2
    r0, r1, half = 16, 50, math.radians(36)
    out = _box(x, y)
    out += _txt(x + S_W - 6, y + S_H - 4 - S_LBL * 0.6, "Left Stick", S_LBL, C["idle_text"], anchor="end")
    for name, dx, dy in DIRS:
        ang = math.atan2(dy, dx)
        pts = []
        for a, r in ((ang - half, r0), (ang - half, r1), (ang, r1 + 6), (ang + half, r1), (ang + half, r0)):
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts) + " Z"
        lit = active and name == "W"
        if lit:
            out += _glow(f'd="{d}" stroke-linejoin="round"', tag="path")
        out += (f'<path d="{d}" fill="{C["pressed_fill"] if lit else C["idle_fill"]}" stroke="{C["idle_outline"]}" '
                f'stroke-width="{2.2 if lit else 1.2}" stroke-linejoin="round"></path>')
        out += _txt(cx + dx * 35, cy + dy * 35, name, S_FONT, C["pressed_text"] if lit else C["idle_text"])
    ky = cy - (0.8 * 8 if active else 0)
    out += f'<circle cx="{cx:.1f}" cy="{ky:.1f}" r="9" fill="{C["idle_outline"]}"></circle>'
    return out


def stick_vector(x, y, active):
    """C: no box. A round pad with a crosshair; the knob drags a vector line from centre."""
    cx, cy = x + S_W / 2, y + S_H / 2
    rad = 52
    out = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad}" fill="{C["idle_fill"]}" stroke="{C["idle_outline"]}" stroke-width="1.2"></circle>'
    for x1, y1, x2, y2 in ((cx - rad, cy, cx + rad, cy), (cx, cy - rad, cx, cy + rad)):
        out += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{C["idle_outline"]}" stroke-opacity="0.3" stroke-width="1"></line>'
    out += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad * 0.5:.1f}" fill="none" stroke="{C["idle_outline"]}" stroke-opacity="0.3" stroke-width="1"></circle>'
    ky = cy - (0.8 * rad * 0.7 if active else 0)
    if active:
        out += f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx:.1f}" y2="{ky:.1f}" stroke="{C["pressed_outline"]}" stroke-width="3" stroke-linecap="round"></line>'
        out += _glow(f'cx="{cx:.1f}" cy="{ky:.1f}" r="13"')
    out += f'<circle cx="{cx:.1f}" cy="{ky:.1f}" r="13" fill="{C["pressed_fill"] if active else C["idle_fill"]}" stroke="{C["idle_outline"]}" stroke-width="{2.2 if active else 1.2}"></circle>'
    for name, dx, dy in DIRS:
        lit = active and name == "W"
        out += _txt(cx + dx * (rad + 16), cy + dy * (rad + 16), name, S_FONT, C["pressed_outline"] if lit else C["idle_text"], opacity=None if lit else 0.7)
    out += _txt(cx, cy + rad + 36, "Left Stick", S_LBL, C["idle_text"], weight=600)
    return out


def stick_keycross(x, y, active):
    """D: key cross. The four bindings are drawn as real keys in a cross, analog dot in the middle."""
    cx, cy = x + S_W / 2, y + S_H / 2
    kw, kh, off = 40, 30, 38
    out = _box(x, y)
    out += _txt(x + S_W - 6, y + S_H - 4 - S_LBL * 0.6, "Left Stick", S_LBL, C["idle_text"], anchor="end")
    for name, dx, dy in DIRS:
        lit = active and name == "W"
        rx, ry = cx + dx * off - kw / 2, cy + dy * off - kh / 2
        attrs = f'x="{rx:.1f}" y="{ry:.1f}" width="{kw}" height="{kh}" rx="6"'
        if lit:
            out += _glow(attrs, tag="rect")
        out += f'<rect {attrs} fill="{C["pressed_fill"] if lit else C["idle_fill"]}" stroke="{C["idle_outline"]}" stroke-width="{2.2 if lit else 1.2}"></rect>'
        out += _txt(cx + dx * off, cy + dy * off, name, S_FONT, C["pressed_text"] if lit else C["idle_text"])
    ky = cy - (0.8 * 6 if active else 0)
    out += f'<circle cx="{cx:.1f}" cy="{ky:.1f}" r="8" fill="{C["idle_outline"]}"></circle>'
    return out


def stick_sheet(draw, name, motive, tradeoff):
    fw, fh = 560, 360
    pad_y = 40
    left, right = 100, 300
    svg = ""
    for x0, active, cap in ((left, False, "idle"), (right, True, "W held / stick up")):
        svg += draw(x0, pad_y, active)
        svg += _txt(x0 + S_W / 2, pad_y + S_H + 18, cap, 8 * PT, T["muted"], weight=400)
    inner = (f'<div style="width: {fw}px; height: {fh}px; background: #0c0c0e; position: relative; overflow: hidden; display: flex; flex-direction: column;">'
             f'<svg width="{fw}" height="{fh - 64}" viewBox="0 0 {fw} {fh - 64}" xmlns="http://www.w3.org/2000/svg" style="display: block;">{svg}</svg>'
             f'<div style="display: flex; flex-direction: column; gap: 3px; padding: 0 20px 14px 20px;">'
             f'<div style="font-size: {11*PT:.2f}px; font-weight: 600;">{name}</div>'
             f'<div style="color: {T["muted"]}; font-size: {8*PT:.2f}px;">{motive} Trade-off: {tradeoff}</div></div></div>')
    return inner, fw, fh


STICK_OPTIONS = {
    "StickCurrent.dc.html": (stick_current, "Current", "Ring, knob and four dots as shipped.", "dots crowd the knob; letters float far from their dots."),
    "StickA.dc.html": (stick_ring, "Option A: Ring gauge", "Outer ring shows deflection as a lit arc; letters live outside it.", "arc needs analog input to shine; plain WASD only lights a letter."),
    "StickB.dc.html": (stick_petals, "Option B: Petals", "Each direction is its own wedge key, so a press reads like any other pad.", "busiest shape; diagonals show as two lit wedges."),
    "StickC.dc.html": (stick_vector, "Option C: Vector", "Drops the box. Round pad, crosshair, and a line that follows the knob.", "breaks the grid look of the surrounding keys."),
    "StickD.dc.html": (stick_keycross, "Option D: Key cross", "The four bindings drawn as real keys in a cross around a small analog dot.", "least room for the analog motion itself."),
}


# ---- pad (button) style sketches ------------------------------------------
P_W, P_H, P_R = 75.0, 105.0, 7.5   # one key at scale 0.75


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _mixc(a, b, t):
    return _hex(tuple(x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))))


def _scale(h, f):  # Qt darker(150) = /1.5, lighter(140) = *1.4 (value only, roughly)
    return _hex(tuple(v * f for v in _rgb(h)))


def _rect(x, y, w, h, rx, fill, stroke=None, sw=1.2, extra=""):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}"{st}{extra}></rect>'


def pad_body(style, x, y, t):
    """SVG for one key body in a pad style at lit level t (0 or 1). Returns (svg, text color)."""
    w, h, r = P_W, P_H, P_R
    if style == "pill":
        r = min(w, h) / 2
    outline = _mixc(C["idle_outline"], C["pressed_outline"], t)
    text = _mixc(C["idle_text"], C["pressed_text"], t)
    out = ""
    if t > 0 and style != "underline":
        out += _rect(x, y, w, h, r, "none", C["pressed_outline"], 12, ' stroke-opacity="0.18"')
        out += _rect(x, y, w, h, r, "none", C["pressed_outline"], 6, ' stroke-opacity="0.09"')
    if style == "outline":
        out += _rect(x, y, w, h, r, C["pressed_fill"], outline, 1.2 + t, f' fill-opacity="{t}"')
    elif style == "keycap":
        out += _rect(x, y, w, h, r, _mixc(_scale(C["idle_fill"], 1 / 1.5), _scale(C["pressed_fill"], 1 / 1.3), t), outline, 1.2 + t)
        inset = max(3.0, min(w, h) * 0.10)
        out += _rect(x + inset, y + inset * 0.6, w - 2 * inset, h - inset * 2.2, max(1.0, r * 0.7),
                     _mixc(_scale(C["idle_fill"], 1.4), C["pressed_fill"], t))
    elif style == "underline":
        out += _rect(x, y, w, h, r, _mixc(C["idle_fill"], C["pressed_fill"], t * 0.35))
        bar_h = max(2.0, h * 0.08)
        bar = _mixc(C["idle_outline"], C["pressed_outline"], t)
        out += (f'<clipPath id="clip{x:.0f}{y:.0f}">{_rect(x, y, w, h, r, "#000")}</clipPath>'
                f'<g clip-path="url(#clip{x:.0f}{y:.0f})">'
                f'<rect x="{x:.1f}" y="{y + h - bar_h:.1f}" width="{w:.1f}" height="{bar_h:.1f}" fill="{bar}" fill-opacity="{0.43 + 0.57 * t:.2f}"></rect></g>')
        text = _mixc(C["idle_text"], C["pressed_outline"], t)
    else:
        out += _rect(x, y, w, h, r, _mixc(C["idle_fill"], C["pressed_fill"], t), outline, 1.2 + t)
    return out, text


def pad_sheet(style, name, motive, tradeoff):
    fw, fh = 560, 300
    svg = ""
    keys = (("Space", 0), ("F", 0), ("Space", 1), ("F", 1))
    x0 = (fw - (4 * P_W + 3 * 20)) / 2
    y0 = 40
    for i, (label, t) in enumerate(keys):
        x = x0 + i * (P_W + 20)
        body, text = pad_body(style, x, y0, t)
        svg += body
        svg += _txt(x + P_W / 2, y0 + P_H / 2, label, S_FONT, text)
    svg += _txt(x0 + P_W + 10, y0 + P_H + 18, "idle", 8 * PT, T["muted"], weight=400)
    svg += _txt(x0 + 3 * P_W + 50, y0 + P_H + 18, "pressed", 8 * PT, T["muted"], weight=400)
    inner = (f'<div style="width: {fw}px; height: {fh}px; background: #0c0c0e; position: relative; overflow: hidden; display: flex; flex-direction: column;">'
             f'<svg width="{fw}" height="{fh - 64}" viewBox="0 0 {fw} {fh - 64}" xmlns="http://www.w3.org/2000/svg" style="display: block;">{svg}</svg>'
             f'<div style="display: flex; flex-direction: column; gap: 3px; padding: 0 20px 14px 20px;">'
             f'<div style="font-size: {11*PT:.2f}px; font-weight: 600;">{name}</div>'
             f'<div style="color: {T["muted"]}; font-size: {8*PT:.2f}px;">{motive} Trade-off: {tradeoff}</div></div></div>')
    return inner, fw, fh


PAD_OPTIONS = {
    "PadClassic.dc.html": ("classic", "Classic", "Filled tile, thin border, glow when lit. As shipped.", "reads a little heavy on busy layouts."),
    "PadOutline.dc.html": ("outline", "Outline", "See-through until pressed, then fills solid. Lightest on the game underneath.", "idle labels sit straight on the game, so contrast depends on the scene."),
    "PadKeycap.dc.html": ("keycap", "Keycap", "Dark rim with a raised face, so each key reads as a physical cap.", "two tones eat space on small keys."),
    "PadUnderline.dc.html": ("underline", "Underline", "Flat borderless tile; a bar along the bottom and the label carry the state.", "no glow, so a quick tap is easy to miss."),
    "PadPill.dc.html": ("pill", "Pill", "Fully rounded ends, like the classic look with softer geometry.", "wide keys become long capsules."),
}


# ---- mouse layouts (geometry straight from the app) ------------------------
import sys
sys.path.insert(0, os.path.join(OUT, ".."))
if not os.path.exists(os.path.join(OUT, "..", "templates.py")):
    sys.path.insert(0, r"C:\dev\az-overlay")
from PySide6.QtCore import QRectF  # noqa: E402
from PySide6.QtGui import QPainterPath  # noqa: E402
import overlay as app_overlay  # noqa: E402
import templates as app_templates  # noqa: E402


def qpath_to_svg(path):
    out, i, n = [], 0, path.elementCount()
    while i < n:
        e = path.elementAt(i)
        if e.type == QPainterPath.ElementType.MoveToElement:
            out.append(f"M {e.x:.1f} {e.y:.1f}")
        elif e.type == QPainterPath.ElementType.LineToElement:
            out.append(f"L {e.x:.1f} {e.y:.1f}")
        elif e.type == QPainterPath.ElementType.CurveToElement:
            c1, c2 = path.elementAt(i + 1), path.elementAt(i + 2)
            out.append(f"C {e.x:.1f} {e.y:.1f} {c1.x:.1f} {c1.y:.1f} {c2.x:.1f} {c2.y:.1f}")
            i += 2
        i += 1
    return " ".join(out) + " Z"


def mouse_board():
    cw = ch = 40.0
    radius = min(10, cw * 0.2, ch * 0.2)
    font_px = 9 * PT
    lit = {"Left", "5"}
    x_cursor, gap, top = 30.0, 60.0, 50.0
    svg, widest = "", 0
    for name, _n in app_templates.MICE:
        prof = app_templates.build("Mouse", name)
        def cell(col, row, w, h):
            return QRectF(x_cursor + col * cw + 2, top + row * ch + 2, w * cw, h * ch)
        rects = []
        for d in prof["decor"]:
            r = cell(d["col"], d["row"], d["w"], d["h"])
            rects.append(r)
            svg += (f'<path d="{qpath_to_svg(app_overlay.decor_path(d["kind"], r))}" fill="{C["idle_fill"]}" '
                    f'stroke="{C["idle_outline"]}" stroke-opacity="0.47" stroke-width="1.2"></path>')
        for k in prof["keys"]:
            r = cell(k["col"], k["row"], k["w"], k["h"])
            rects.append(r)
            on = k["label"] in lit
            body = qpath_to_svg(app_overlay.shape_path(r, k.get("shape", "rect"), radius))
            if on:
                svg += (f'<path d="{body}" fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.18" stroke-width="12"></path>'
                        f'<path d="{body}" fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.09" stroke-width="6"></path>')
            svg += (f'<path d="{body}" fill="{C["pressed_fill"] if on else C["idle_fill"]}" stroke="{C["idle_outline"]}" '
                    f'stroke-width="{2.2 if on else 1.2}"></path>')
            tr = app_overlay.key_text_rect(r, k.get("shape", "rect"))
            size = font_px if len(k["label"]) <= 4 else font_px * 0.85
            if k["label"] in ("▲", "▼"):
                size = 9.0
            svg += _txt(tr.center().x(), tr.center().y(), k["label"], size, C["pressed_text"] if on else C["idle_text"])
        w = max(r.right() for r in rects) - x_cursor + 4
        svg += _txt(x_cursor + w / 2, top - 22, name, 8 * PT, T["muted"], weight=400)
        x_cursor += w + gap
        widest = max(widest, max(r.bottom() for r in rects))
    fw, fh = int(x_cursor - gap + 30), int(widest + 40)
    inner = (f'<div style="width: {fw}px; height: {fh}px; background: #0c0c0e; position: relative; overflow: hidden;">'
             f'<svg width="{fw}" height="{fh}" viewBox="0 0 {fw} {fh}" xmlns="http://www.w3.org/2000/svg" style="display: block;">{svg}</svg></div>')
    return inner, fw, fh



# ---- prototype: bulk delete on the Keys page (wayfinder ticket 05) ----------
# Three structurally different options. Selection = the pads in column 3 of the
# Cyborg 2 layout, as if the user ctrl-clicked them. Throwaway once one wins.
def _cfg_keys():
    with open(os.path.join(os.path.dirname(OUT), "config.json"), encoding="utf-8") as f:
        return json.load(f)["keys"]


SEL_COL = 3


def pad_map(width, height, selected_cols=(SEL_COL,), marquee=False):
    """Visual layout (PadLayoutEditor) with multi-selected pads, scaled to fit."""
    keys = _cfg_keys()
    cw, ch, gap = 100, 140, 8
    xs = [k["col"] * (cw + gap) for k in keys]
    ys = [k["row"] * (ch + gap) for k in keys]
    bw = max(x + k.get("w", 1) * (cw + gap) - gap for x, k in zip(xs, keys)) - min(xs)
    bh = max(y + k.get("h", 1) * (ch + gap) - gap for y, k in zip(ys, keys)) - min(ys)
    ratio = min((width - 24) / bw, (height - 24) / bh)
    ox = (width - bw * ratio) / 2 - min(xs) * ratio
    oy = (height - bh * ratio) / 2 - min(ys) * ratio
    svg = f'<rect x="0" y="0" width="{width}" height="{height}" fill="{T["preview"]}"></rect>'
    sel_rects = []
    for k, x, y in zip(keys, xs, ys):
        rx, ry = ox + x * ratio, oy + y * ratio
        rw = (k.get("w", 1) * (cw + gap) - gap) * ratio
        rh = (k.get("h", 1) * (ch + gap) - gap) * ratio
        sel = k["col"] in selected_cols
        if sel:
            sel_rects.append((rx, ry, rw, rh))
        fill = T["selection"] if sel else T["field"]
        stroke = T["accent"] if sel else T["strong_line"]
        svg += (f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" rx="5" fill="{fill}" '
                f'stroke="{stroke}" stroke-width="{2 if sel else 1}"></rect>')
        svg += _txt(rx + rw / 2, ry + rh / 2 + 4, k["label"] or "", 11, T["accent"] if sel else T["text"], weight=600)
    if marquee and sel_rects:
        x0 = min(r[0] for r in sel_rects) - 8
        y0 = min(r[1] for r in sel_rects) - 8
        x1 = max(r[0] + r[2] for r in sel_rects) + 8
        y1 = max(r[1] + r[3] for r in sel_rects) + 8
        svg += (f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" fill="{T["accent"]}" '
                f'fill-opacity="0.08" stroke="{T["accent"]}" stroke-width="1.5" stroke-dasharray="6 4"></rect>')
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
            f'style="display: block; border-radius: 10px;">{svg}</svg>')


def pad_table(rows, selected, cols=("Label", "Input"), height=42):
    n = len(cols)
    thead = (f'<div style="display: grid; grid-template-columns: repeat({n}, minmax(0, 1fr)); color: {T["muted"]}; '
             f'font-size: {8*PT:.2f}px; font-weight: 600; border-bottom: 1px solid {T["line"]};">'
             + "".join(f'<div style="padding: 8px;">{c}</div>' for c in cols) + '</div>')
    trs = ""
    for i, cells in enumerate(rows):
        sel = i in selected
        bg = T["selection"] if sel else "transparent"
        color = T["accent"] if sel else T["text"]
        trs += (f'<div style="display: grid; grid-template-columns: repeat({n}, minmax(0, 1fr)); height: {height}px; '
                f'align-items: center; background: {bg}; color: {color}; border-bottom: 1px solid {T["line"]};">'
                + "".join(f'<div style="padding: 8px;">{c}</div>' for c in cells) + '</div>')
    return f'<div style="display: flex; flex-direction: column; background: {T["card"]};">{thead}{trs}</div>'


def _rows_from_cfg():
    keys = _cfg_keys()
    rows, selected = [], set()
    for i, k in enumerate(keys[:12]):
        rows.append((k["label"] or f"#{i + 1}", k.get("input", "")))
        if k["col"] == SEL_COL:
            selected.add(i)
    return rows, selected


def undo_bar(text="Undo delete · 12 pads"):
    return (f'<div style="display: flex; align-items: center; gap: 12px; background: {T["selection"]}; '
            f'border: 1px solid {T["accent"]}; border-radius: 10px; padding: 8px 12px; color: {T["accent"]}; '
            f'font-weight: 600;">{text}<span style="color: {T["muted"]}; font-weight: 400;">Ctrl+Z</span></div>')


KEYS_TITLE = ("Keys &amp; inputs", "Choose a pad. Record an input. Make it yours.")


def bulk_a():
    """Option A: today's page; Remove counts the selection, Delete row/column join Add row/Add column."""
    rows, selected = _rows_from_cfg()
    c1 = card(
        section("Pads"),
        muted("Ctrl-click or shift-click to select several pads. Delete removes the selection."),
        switch("Show all pads", on=True),
        pad_map(756, 220),
        f'<div style="display: flex; align-items: center; gap: 10px;">{field("Search by label or input", placeholder=True, flex=1)}{muted("30 / 30 pads", wrap=False)}</div>',
        f'<div style="display: flex; align-items: center; gap: 10px;">{button("Record input", kind="primary")}<div style="flex: 1;"></div>{button("Add pad")}{button("Remove 3 pads", kind="quiet")}</div>',
        f'<div style="display: flex; align-items: center; gap: 10px;">{button("Add row")}{button("Add column")}<div style="width: 18px;"></div>{button("Delete row")}{button("Delete column")}</div>',
        muted("3 pads selected"),
        pad_table(rows, selected),
        undo_bar(),
        switch("Edit position &amp; size"),
    )
    return window("Keys", page(*KEYS_TITLE, c1, disclosure("Sticks &amp; d-pads")), height=KEYS_H)


def bulk_b():
    """Option B: a selection toolbar exists only while pads are selected; Add controls stay quiet."""
    rows, selected = _rows_from_cfg()
    toolbar = (f'<div style="display: flex; align-items: center; gap: 10px; background: {T["field"]}; '
               f'border: 1px solid {T["accent"]}; border-radius: 12px; padding: 8px 8px 8px 14px;">'
               f'<span style="color: {T["accent"]}; font-weight: 600;">3 selected</span>'
               f'<div style="flex: 1;"></div>{button("Delete")}{button("Delete row")}{button("Delete column")}{button("Clear", kind="quiet")}</div>')
    c1 = card(
        section("Pads"),
        muted("Select pads here or in the table. A toolbar shows what you can do with the selection."),
        switch("Show all pads", on=True),
        pad_map(756, 220),
        toolbar,
        f'<div style="display: flex; align-items: center; gap: 10px;">{field("Search by label or input", placeholder=True, flex=1)}{muted("30 / 30 pads", wrap=False)}</div>',
        pad_table(rows, selected),
        f'<div style="display: flex; align-items: center; gap: 10px;">{button("Record input", kind="primary")}<div style="flex: 1;"></div>{button("Add pad")}{button("Add row")}{button("Add column")}</div>',
        f'<div style="display: flex; justify-content: flex-end;">{undo_bar()}</div>',
        switch("Edit position &amp; size"),
    )
    return window("Keys", page(*KEYS_TITLE, c1, disclosure("Sticks &amp; d-pads")), height=KEYS_H)


def bulk_c():
    """Option C: visual first; big layout with a drag-box, actions in a side rail, table demoted to a compact list."""
    rows, selected = _rows_from_cfg()
    rail = (f'<div style="display: flex; flex-direction: column; gap: 8px; width: 176px; flex: 0 0 auto;">'
            f'{button("Record input", kind="primary")}<div style="height: 6px;"></div>'
            f'{section("Add")}{button("Pad")}{button("Row")}{button("Column")}<div style="height: 6px;"></div>'
            f'{section("Delete")}{button("3 selected")}{button("Their rows")}{button("Their columns")}'
            f'<div style="height: 6px;"></div>{undo_bar("Undo · 12 pads")}</div>')
    body = f'<div style="display: flex; gap: 16px; align-items: flex-start;">{pad_map(560, 330, marquee=True)}{rail}</div>'
    c1 = card(
        section("Pads"),
        muted("Drag a box or ctrl-click pads on the layout. Everything you can do with them sits on the right."),
        body,
        f'<div style="display: flex; align-items: center; gap: 10px;">{field("Search by label or input", placeholder=True, flex=1)}{muted("3 selected · 30 pads", wrap=False)}</div>',
        pad_table(rows[:8], selected, height=34),
        switch("Edit position &amp; size"),
    )
    return window("Keys", page(*KEYS_TITLE, c1, disclosure("Sticks &amp; d-pads")), height=KEYS_H)


def bulk_final():
    """Winner (2026-09-12): B's selection toolbar, search directly above the table, A's full-width undo bar under it."""
    rows, selected = _rows_from_cfg()
    toolbar = (f'<div style="display: flex; align-items: center; gap: 10px; background: {T["field"]}; '
               f'border: 1px solid {T["accent"]}; border-radius: 12px; padding: 8px 8px 8px 14px;">'
               f'<span style="color: {T["accent"]}; font-weight: 600;">3 selected</span>'
               f'<div style="flex: 1;"></div>{button("Delete")}{button("Delete row")}{button("Delete column")}{button("Clear", kind="quiet")}</div>')
    c1 = card(
        section("Pads"),
        muted("Select pads on the layout or in the table. Delete removes the selection; Undo brings it back."),
        switch("Show all pads", on=True),
        pad_map(756, 220),
        toolbar,
        f'<div style="display: flex; align-items: center; gap: 10px;">{field("Search by label or input", placeholder=True, flex=1)}{muted("30 / 30 pads", wrap=False)}</div>',
        pad_table(rows, selected),
        undo_bar(),
        f'<div style="display: flex; align-items: center; gap: 10px;">{button("Record input", kind="primary")}<div style="flex: 1;"></div>{button("Add pad")}{button("Add row")}{button("Add column")}</div>',
        switch("Edit position &amp; size"),
    )
    return window("Keys", page(*KEYS_TITLE, c1, disclosure("Sticks &amp; d-pads")), height=KEYS_H)


BULK_OPTIONS = {
    "BulkFinal.dc.html": (bulk_final, "Keys · bulk delete (chosen)"),
    "BulkA.dc.html": (bulk_a, "Option A · Buttons row"),
    "BulkB.dc.html": (bulk_b, "Option B · Selection toolbar"),
    "BulkC.dc.html": (bulk_c, "Option C · Visual first"),
}


# ---- prototype: settings header without a Save button (wayfinder ticket 07) ---
# Layouts always autosave, so the header loses "Save layout" and gains Duplicate /
# Rename. Three structurally different options. Throwaway once one wins.
def _header_shell(*rows):
    return (f'<div style="display: flex; flex-direction: column; gap: 18px; background: {T["card"]}; '
            f'border-bottom: 1px solid {T["line"]}; padding: 20px 26px 18px 26px;">' + "".join(rows) + '</div>')


def _tagline_row(right=""):
    return (f'<div style="display: flex; align-items: center; gap: 10px;">{muted("Every move. On display.", wrap=False)}'
            f'<div style="flex: 1;"></div>{right}<span>Theme</span>{combo("Dark", width=100)}</div>')


def header_a():
    """Option A: today's row minus Save; Duplicate / Rename / Delete live under More; autosave note under the row."""
    return _header_shell(
        _tagline_row(),
        f'<div style="display: flex; align-items: center; gap: 10px;">{muted("Layout", wrap=False)}'
        f'{combo("Azeron Cyborg II", flex=1)}{button("More", kind="quiet")}'
        f'<div style="width: 8px;"></div>{button("+ New layout", kind="primary")}</div>',
        f'<div style="margin-top: -8px;">{muted("Changes save automatically.")}</div>',
    )


def header_b():
    """Option B: every layout action visible in one row; autosave note sits with the tagline."""
    return _header_shell(
        _tagline_row(muted("Changes save automatically", wrap=False) + '<div style="width: 18px;"></div>'),
        f'<div style="display: flex; align-items: center; gap: 10px;">{muted("Layout", wrap=False)}'
        f'{combo("Azeron Cyborg II", flex=1)}{button("Rename")}{button("Duplicate")}{button("Delete", kind="quiet")}'
        f'<div style="width: 8px;"></div>{button("+ New layout", kind="primary")}</div>',
    )


def header_c():
    """Option C: the layout name is the title; click it to rename, chevron to switch; actions on the right."""
    title = (f'<div style="display: flex; align-items: center; gap: 12px;">'
             f'<span style="font-size: {20*PT:.2f}px; font-weight: 700; letter-spacing: -0.5px;">Azeron Cyborg II</span>{arrow()}'
             f'<span style="color: {T["muted"]}; font-size: {8*PT:.2f}px; border: 1px solid {T["line"]}; border-radius: 6px; padding: 2px 6px;">click to rename</span></div>')
    return _header_shell(
        _tagline_row(),
        f'<div style="display: flex; align-items: center; gap: 10px;">'
        f'<div style="display: flex; flex-direction: column; gap: 4px;">{title}{muted("Changes save automatically")}</div>'
        f'<div style="flex: 1;"></div>{button("Duplicate")}{button("Delete", kind="quiet")}'
        f'<div style="width: 8px;"></div>{button("+ New layout", kind="primary")}</div>',
    )


def _layout_body():
    c1 = card(
        section("Position your overlay"),
        f'<div style="display: flex;">{button("Edit on screen", kind="primary", min_width=156, min_height=38)}</div>',
        muted("Drag to reposition. Scroll to resize. Ctrl+Alt+E toggles this from anywhere; Esc or Done editing ends it."),
        form(slider("Size", 10, "50%"), slider("Opacity", 83, "85%")),
        disclosure("Precise position &amp; scale"),
    )
    return page("Layout", "Get your overlay in the right place, at the right size.",
                c1, disclosure("Key dimensions"), disclosure("Keyboard shortcuts"))


HEADER_OPTIONS = {
    "HeaderA.dc.html": (header_a, "Option A · More menu"),
    "HeaderB.dc.html": (header_b, "Option B · Actions in the row"),
    "HeaderC.dc.html": (header_c, "Option C · Layout name as title"),
}


# Round 2 (user: B's buttons + C's big title, no autosave note, tagline placed better).
def _title_block(sub=""):
    return (f'<div style="display: flex; flex-direction: column; gap: 4px;">'
            f'<div style="display: flex; align-items: center; gap: 12px;">'
            f'<span style="font-size: {20*PT:.2f}px; font-weight: 700; letter-spacing: -0.5px;">Azeron Cyborg II</span>{arrow()}</div>{sub}</div>')


def _actions(theme=False):
    extra = f'<div style="width: 14px;"></div><span>Theme</span>{combo("Dark", width=100)}' if theme else ""
    return (f'<div style="flex: 1;"></div>{button("Rename")}{button("Duplicate")}{button("Delete", kind="quiet")}'
            f'<div style="width: 8px;"></div>{button("+ New layout", kind="primary")}{extra}')


def header_d():
    """Option D: tagline as a small uppercase eyebrow above the title; Theme keeps the top-right corner."""
    eyebrow = (f'<div style="color: {T["accent"]}; font-size: {8*PT:.2f}px; font-weight: 600; letter-spacing: 2px; '
               f'text-transform: uppercase;">Every move. On display.</div>')
    return _header_shell(
        f'<div style="display: flex; align-items: center; gap: 10px;">{eyebrow}<div style="flex: 1;"></div><span>Theme</span>{combo("Dark", width=100)}</div>',
        f'<div style="display: flex; align-items: center; gap: 10px;">{_title_block()}{_actions()}</div>',
    )


def header_e():
    """Option E: tagline leaves the header for a wordmark block at the top of the sidebar; header is one row."""
    return _header_shell(
        f'<div style="display: flex; align-items: center; gap: 10px;">{_title_block()}{_actions(theme=True)}</div>',
    )


def sidebar_brand(active):
    """Sidebar whose Workspace label becomes a wordmark: mark, name, tagline."""
    mark = (f'<svg width="30" height="30" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" style="flex: 0 0 auto;">'
            f'<rect x="0" y="0" width="32" height="32" rx="8" fill="{T["accent"]}"></rect>'
            f'<rect x="7" y="9" width="7" height="7" rx="2" fill="{T["accent_text"]}"></rect>'
            f'<rect x="18" y="9" width="7" height="7" rx="2" fill="none" stroke="{T["accent_text"]}" stroke-width="1.6"></rect>'
            f'<rect x="7" y="19" width="7" height="7" rx="2" fill="none" stroke="{T["accent_text"]}" stroke-width="1.6"></rect>'
            f'<rect x="18" y="19" width="7" height="7" rx="2" fill="{T["accent_text"]}"></rect></svg>')
    brand = (f'<div style="display: flex; flex-direction: column; gap: 8px;">'
             f'<div style="display: flex; align-items: center; gap: 10px;">{mark}<span style="font-weight: 700; font-size: {12*PT:.2f}px; letter-spacing: -0.3px;">AZ-Overlay</span></div>'
             f'<div style="color: {T["muted"]}; font-size: {9*PT:.2f}px; line-height: 1.35;">Every move.<br>On display.</div></div>')
    items = []
    for name in ("Layout", "Keys", "Appearance", "About", "Help"):
        sel = name == active
        bg = T["selection"] if sel else "transparent"
        color = T["accent"] if sel else T["muted"]
        weight = 600 if sel else 400
        items.append(f'<div style="display: flex; align-items: center; gap: 12px; padding: 10px; margin: 3px 0; border-radius: 10px; '
                     f'background: {bg}; color: {color}; font-weight: {weight};">{icon(name)}<span>{name}</span></div>')
    return (f'<div style="width: 184px; flex: 0 0 auto; display: flex; flex-direction: column; gap: 18px; background: {T["sidebar"]}; '
            f'border-right: 1px solid {T["line"]}; padding: 24px 12px 20px 12px;">{brand}'
            f'<div style="display: flex; flex-direction: column;">' + "".join(items) + '</div></div>')


def header_f():
    """Option F: tagline sits under the big title in accent, where the autosave note was; one row, Theme far right."""
    sub = f'<div style="color: {T["accent"]}; font-size: {9*PT:.2f}px;">Every move. On display.</div>'
    return _header_shell(
        f'<div style="display: flex; align-items: center; gap: 10px;">{_title_block(sub)}{_actions(theme=True)}</div>',
    )


HEADER_OPTIONS.update({
    "HeaderD.dc.html": (header_d, "Option D · Eyebrow tagline"),
    "HeaderE.dc.html": (header_e, "Option E · Tagline in the sidebar wordmark"),
    "HeaderF.dc.html": (header_f, "Option F · Tagline under the title"),
})
HEADER_SIDEBARS = {"HeaderE.dc.html": sidebar_brand}

# ---- emit -----------------------------------------------------------------
def settings_boards(theme, suffix=""):
    """The five settings pages in one theme. Every builder reads the shared T palette."""
    T.clear()
    T.update(DARK if theme == "dark" else LIGHT)
    out = {
        f"Main{suffix}.dc.html" if not suffix else f"Layout{suffix}.dc.html": layout_page(),
        f"Keys{suffix}.dc.html": keys_page(),
        f"Appearance{suffix}.dc.html": appearance_page(),
        f"About{suffix}.dc.html": about_page(),
        f"Help{suffix}.dc.html": help_page(),
    }
    T.clear()
    T.update(DARK)
    return out


boards = settings_boards("dark")
light_boards = settings_boards("light", "Light")
boards.update(light_boards)
overlay_html, ow, oh = overlay_page()
boards["Overlay.dc.html"] = overlay_html
stick_boards = {}
for fname, (draw, name, motive, tradeoff) in STICK_OPTIONS.items():
    html, sw, sh = stick_sheet(draw, name, motive, tradeoff)
    boards[fname] = html
    stick_boards[fname] = (sw, sh)
mouse_html, mw, mh = mouse_board()
boards["MouseLayouts.dc.html"] = mouse_html
pad_boards = {}
for fname, (style, name, motive, tradeoff) in PAD_OPTIONS.items():
    html, pw, ph = pad_sheet(style, name, motive, tradeoff)
    boards[fname] = html
    pad_boards[fname] = (pw, ph)
for fname, (fn, _title) in BULK_OPTIONS.items():
    boards[fname] = fn()
for fname, (fn, _title) in HEADER_OPTIONS.items():
    _side = HEADER_SIDEBARS.get(fname)
    boards[fname] = window("Layout", _layout_body(), head=fn(), side=_side("Layout") if _side else None)
for name, inner in boards.items():
    if name in light_boards:
        T.clear()
        T.update(LIGHT)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(doc(inner))
    T.clear()
    T.update(DARK)

GX = W + 100
canvas = {
    "artboards": [
        {"file": "Main.dc.html", "title": "Settings · Layout", "x": 0, "y": 0, "w": W, "h": H},
        {"file": "Appearance.dc.html", "title": "Settings · Appearance", "x": GX, "y": 0, "w": W, "h": H},
        {"file": "Overlay.dc.html", "title": "Overlay · Cyborg 2 layout", "x": 2 * GX, "y": 0, "w": ow, "h": oh},
        {"file": "Keys.dc.html", "title": "Settings · Keys (full length)", "x": 0, "y": H + 140, "w": W, "h": KEYS_H},
        {"file": "Help.dc.html", "title": "Settings · Help (full length)", "x": GX, "y": H + 140, "w": W, "h": HELP_H},
        {"file": "About.dc.html", "title": "Settings · About", "x": 2 * GX, "y": H + 140, "w": W, "h": H},
        {"file": "MouseLayouts.dc.html", "title": "Overlay · Mouse layouts", "x": 0, "y": H + 140 + KEYS_H + 140, "w": mw, "h": mh},
        {"file": "LayoutLight.dc.html", "title": "Settings · Layout (light)", "page": "page-4", "x": 0, "y": 0, "w": W, "h": H},
        {"file": "AppearanceLight.dc.html", "title": "Settings · Appearance (light)", "page": "page-4", "x": GX, "y": 0, "w": W, "h": H},
        {"file": "AboutLight.dc.html", "title": "Settings · About (light)", "page": "page-4", "x": 2 * GX, "y": 0, "w": W, "h": H},
        {"file": "KeysLight.dc.html", "title": "Settings · Keys (light, full length)", "page": "page-4", "x": 0, "y": H + 140, "w": W, "h": KEYS_H},
        {"file": "HelpLight.dc.html", "title": "Settings · Help (light, full length)", "page": "page-4", "x": GX, "y": H + 140, "w": W, "h": HELP_H},
    ] + [
        {"file": fname, "title": STICK_OPTIONS[fname][1], "page": "page-2",
         "x": (i % 3) * (560 + 100), "y": (i // 3) * (360 + 140), "w": sw, "h": sh}
        for i, (fname, (sw, sh)) in enumerate(stick_boards.items())
    ] + [
        {"file": fname, "title": BULK_OPTIONS[fname][1], "page": "page-5",
         "x": i * GX, "y": 0, "w": W, "h": KEYS_H}
        for i, fname in enumerate(BULK_OPTIONS)
    ] + [
        {"file": fname, "title": HEADER_OPTIONS[fname][1], "page": "page-6",
         "x": (i % 3) * GX, "y": (i // 3) * (H + 140), "w": W, "h": H}
        for i, fname in enumerate(HEADER_OPTIONS)
    ] + [
        {"file": fname, "title": PAD_OPTIONS[fname][1], "page": "page-3",
         "x": (i % 3) * (560 + 100), "y": (i // 3) * (300 + 140), "w": pw, "h": ph}
        for i, (fname, (pw, ph)) in enumerate(pad_boards.items())
    ],
    "pages": [{"id": "page-1", "name": "Screens"}, {"id": "page-4", "name": "Screens · Light"},
              {"id": "page-2", "name": "Stick directions"}, {"id": "page-3", "name": "Pad styles"},
              {"id": "page-5", "name": "Bulk delete (prototype)"}, {"id": "page-6", "name": "Header (prototype)"}],
    "launch": {"view": "canvas", "page": "page-4"},
}
with open(os.path.join(OUT, "canvas.json"), "w", encoding="utf-8") as f:
    json.dump(canvas, f, indent=2)
print("wrote", ", ".join(boards), "canvas.json")
