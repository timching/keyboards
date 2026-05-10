#!/usr/bin/env python3
"""
Render a QMK keymap JSON to one SVG per layer.

Usage: ./render_keymap.py <keymap.json> <keymap_dir>

Writes <keymap_dir>/layers/layer_NN_*.svg and <keymap_dir>/layers.md (index).

Designed as a training reference. Single unified style for any key that's
mapped on the layer; KC_TRNS / KC_NO fade into the bezel so the eye skips
them and only "real" mappings stand out.
"""
import json, sys, re
from pathlib import Path

# ─── Palette ─────────────────────────────────────────────────────────────────
# Configured keys all share one look. The orange BORDER is the cue that says
# "this key is mapped on this layer." Unmapped keys recede toward the bezel.
BEZEL        = "#16243b"
KEY_ACT_BG   = "#ede4cc"   # cream
KEY_ACT_FG   = "#1a2940"   # dark navy text
KEY_ACT_BD   = "#e9b659"   # orange border = "mapped"
KEY_TRNS_BG  = "#243758"   # visible silhouette, clearly muted
KEY_NO_BG    = "#1a2a44"   # very faint silhouette so grid stays visible
KEY_INACT_BD = "#2a3d5e"   # 1px border on inactive cells to outline the grid
TITLE_FG     = "#e9b659"

# ─── Geometry ────────────────────────────────────────────────────────────────
KEY_W, KEY_H   = 80, 80
GAP            = 8
PAD            = 30
TITLE_H        = 50
BORDER_WIDTH   = 2.5

# ─── Keycode -> display label ────────────────────────────────────────────────
LABELS = {
    "KC_TAB": "Tab", "KC_BSPC": "Back\nSpace", "KC_ESC": "Esc",
    "KC_LSFT": "Left\nShift", "KC_RSFT": "Right\nShift",
    "KC_LCTL": "Left\nCtrl", "KC_RCTL": "Right\nCtrl",
    "KC_LALT": "Left\nAlt", "KC_RALT": "Right\nAlt",
    "KC_LGUI": "", "KC_RGUI": "",
    "KC_SPC": "Space", "KC_ENT": "Enter\n↵", "KC_DEL": "Del",
    "KC_LEFT": "←", "KC_RGHT": "→", "KC_UP": "↑", "KC_DOWN": "↓",
    "KC_HOME": "Home", "KC_END": "End", "KC_PGUP": "PgUp", "KC_PGDN": "PgDn",
    "KC_GRV": "`\n~", "KC_TILD": "~",
    "KC_MINS": "-\n_", "KC_EQL": "=\n+", "KC_LBRC": "[\n{", "KC_RBRC": "]\n}",
    "KC_BSLS": "\\\n|", "KC_PIPE": "|", "KC_SCLN": ";\n:", "KC_QUOT": "'\n\"",
    "KC_COMM": ",\n<", "KC_DOT": ".\n>", "KC_SLSH": "/\n?",
    "KC_EXLM": "!", "KC_AT": "@", "KC_HASH": "#", "KC_DLR": "$",
    "KC_PERC": "%", "KC_CIRC": "^", "KC_AMPR": "&", "KC_ASTR": "*",
    "KC_LPRN": "(", "KC_RPRN": ")", "KC_UNDS": "_", "KC_PLUS": "+",
    "KC_LCBR": "{", "KC_RCBR": "}",
    "KC_MNXT": "⏭", "KC_MPRV": "⏮", "KC_MPLY": "⏯",
    "KC_VOLU": "Vol+", "KC_VOLD": "Vol-", "KC_MUTE": "Mute",
    "UG_TOGG": "RGB\nToggle", "UG_VALU": "RGB\nVal+", "UG_VALD": "RGB\nVal-",
    "UG_HUEU": "RGB\nHue+", "UG_HUED": "RGB\nHue-",
    "UG_SATU": "RGB\nSat+", "UG_SATD": "RGB\nSat-",
}


def label_for(kc: str) -> str:
    """Return the display label for a keycode. Empty string -> no text."""
    if kc in ("KC_TRNS", "KC_NO", "KC_LGUI", "KC_RGUI"):
        return ""

    if (m := re.match(r"^(MO|TO|TG|DF|OSL|TT)\((\d+)\)$", kc)):
        return f"{m.group(1)}\n{m.group(2)}"

    if (m := re.match(r"^(LCTL|LSFT|LALT|LGUI|RCTL|RSFT|RALT|RGUI)\(KC_(\w+)\)$", kc)):
        glyph = {"LCTL": "⌃", "RCTL": "⌃",
                 "LSFT": "⇧", "RSFT": "⇧",
                 "LALT": "⌥", "RALT": "⌥",
                 "LGUI": "⌘", "RGUI": "⌘"}[m.group(1)]
        return f"{glyph}{m.group(2)}"

    if (m := re.match(r"^KC_F(\d{1,2})$", kc)):
        return f"F{m.group(1)}"
    if (m := re.match(r"^KC_([0-9])$", kc)):
        return m.group(1)
    if (m := re.match(r"^KC_([A-Z])$", kc)):
        return m.group(1)

    if kc in LABELS:
        return LABELS[kc]

    return kc.removeprefix("KC_")


# ─── SVG building ────────────────────────────────────────────────────────────
def svg_text(x: float, y: float, text: str, fill: str, size: int = 18,
             weight: str = "600") -> str:
    lines = text.split("\n")
    line_h = size * 1.05
    start_y = y - (len(lines) - 1) * line_h / 2
    tspans = "".join(
        f'<tspan x="{x}" y="{start_y + i * line_h:.1f}">{html_escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    return (f'<text text-anchor="middle" dominant-baseline="central" '
            f'font-family="Helvetica, Arial, sans-serif" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}">{tspans}</text>')


def html_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def render_apple(cx: float, cy: float, fill: str, size: float = 28) -> str:
    s = size / 100
    path = ("M50 14c-3 0-7 3-9 5-2 2-4 5-3 8 4 0 8-2 10-5 2-2 3-5 2-8z "
            "M68 38c-5 0-9 3-11 3-3 0-7-3-12-3-7 0-13 4-16 11-7 14 1 35 8 47 "
            "3 6 7 12 13 12 5 0 7-3 14-3 7 0 9 3 14 3 6 0 10-6 13-12 4-7 6-14 6-14 "
            "-1 0-12-5-12-18 0-11 9-16 9-16-5-7-12-10-26-10z")
    return (f'<g transform="translate({cx - size/2:.1f}, {cy - size/2:.1f}) '
            f'scale({s:.3f})" fill="{fill}">'
            f'<path d="{path}"/></g>')


def render_key(x: float, y: float, kc: str) -> list[str]:
    """Render one key cell. Returns list of SVG element strings."""
    out = []

    if kc == "KC_NO":
        out.append(f'<rect x="{x}" y="{y}" width="{KEY_W}" height="{KEY_H}" '
                   f'rx="9" ry="9" fill="{KEY_NO_BG}" '
                   f'stroke="{KEY_INACT_BD}" stroke-width="1"/>')
        return out

    if kc == "KC_TRNS":
        out.append(f'<rect x="{x}" y="{y}" width="{KEY_W}" height="{KEY_H}" '
                   f'rx="9" ry="9" fill="{KEY_TRNS_BG}" '
                   f'stroke="{KEY_INACT_BD}" stroke-width="1"/>')
        return out

    # Active key: shadow + cream fill + orange border.
    out.append(f'<rect x="{x}" y="{y+2}" width="{KEY_W}" height="{KEY_H}" '
               f'rx="9" ry="9" fill="#000" fill-opacity="0.30"/>')
    out.append(f'<rect x="{x}" y="{y}" width="{KEY_W}" height="{KEY_H}" '
               f'rx="9" ry="9" fill="{KEY_ACT_BG}" '
               f'stroke="{KEY_ACT_BD}" stroke-width="{BORDER_WIDTH}"/>')

    cx, cy = x + KEY_W / 2, y + KEY_H / 2
    label = label_for(kc)

    if kc in ("KC_LGUI", "KC_RGUI"):
        out.append(render_apple(cx, cy, KEY_ACT_FG))
    elif (m := re.match(r"^(MO|TO|TG|DF|OSL|TT)\n(\d+)$", label)):
        # Layer-op: small prefix on top, large bold number below.
        out.append(svg_text(cx, cy - 16, m.group(1), KEY_ACT_FG, size=13, weight="500"))
        out.append(svg_text(cx, cy + 13, m.group(2), KEY_ACT_FG, size=30, weight="700"))
    elif label:
        font_size = 18 if "\n" not in label and len(label) <= 4 else 14
        if len(label) == 1 and label.isalnum():
            font_size = 26
        out.append(svg_text(cx, cy, label, KEY_ACT_FG, size=font_size))

    return out


def render_layer(layer: list[str], layer_idx: int, layer_name: str = "") -> str:
    rows, cols = 4, 12
    if len(layer) != rows * cols:
        raise ValueError(f"Layer {layer_idx} has {len(layer)} keys, expected {rows*cols}")

    grid_w = cols * KEY_W + (cols - 1) * GAP
    grid_h = rows * KEY_H + (rows - 1) * GAP
    total_w = grid_w + 2 * PAD
    total_h = grid_h + 2 * PAD + TITLE_H

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" '
        f'width="{total_w}" height="{total_h}">',
        f'<rect x="0" y="0" width="{total_w}" height="{total_h}" '
        f'rx="14" ry="14" fill="{BEZEL}"/>',
        svg_text(total_w / 2, TITLE_H / 2 + 8,
                 f"Layer {layer_idx}" + (f" — {layer_name}" if layer_name else ""),
                 TITLE_FG, size=22, weight="700"),
    ]

    for i, kc in enumerate(layer):
        r, c = divmod(i, cols)
        x = PAD + c * (KEY_W + GAP)
        y = PAD + TITLE_H + r * (KEY_H + GAP)
        parts.extend(render_key(x, y, kc))

    parts.append("</svg>")
    return "\n".join(parts)


def parse_layer_names(notes: str) -> dict[int, str]:
    names = {}
    if not notes:
        return names
    m = re.search(r"Layers?:\s*(.+?)(?:\.|$)", notes, re.DOTALL)
    if not m:
        return names
    for chunk in m.group(1).split("|"):
        cm = re.match(r"\s*(\d+(?:-\d+)?)\s+(.+?)\s*$", chunk)
        if not cm:
            continue
        rng, name = cm.group(1), cm.group(2)
        if "-" in rng:
            a, b = (int(x) for x in rng.split("-"))
            for i in range(a, b + 1):
                names[i] = name
        else:
            names[int(rng)] = name
    return names


def render_index_md(keyboard: str, keymap: str,
                    generated: list[tuple[int, str, str]],
                    img_subdir: str) -> str:
    """Build the markdown index that embeds every layer SVG for browsing on GitHub."""
    lines = [
        f"# {keyboard} — `{keymap}`",
        "",
        "_Generated by `tools/render_keymap.py` — do not edit by hand._",
        "",
        "| Tier | Look |",
        "|---|---|",
        "| **Mapped key** | Cream fill, dark navy text, orange border |",
        "| **`KC_TRNS`** | Faint silhouette, no label — passes through to layer below |",
        "| **`KC_NO`** | Barely-visible silhouette — key blocked on this layer |",
        "",
    ]
    for i, name, fname in generated:
        title = f"Layer {i}" + (f" — {name}" if name else "")
        lines += [f"## {title}", "", f"![{title}]({img_subdir}/{fname})", ""]
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: render_keymap.py <keymap.json> <keymap_dir>")
    src = Path(sys.argv[1])
    keymap_dir = Path(sys.argv[2])
    layers_dir = keymap_dir / "layers"
    layers_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(src.read_text())
    layer_names = parse_layer_names(data.get("notes", ""))
    generated: list[tuple[int, str, str]] = []

    for i, layer in enumerate(data["layers"]):
        name = layer_names.get(i, "")
        slug = re.sub(r"[^\w-]+", "_", name).strip("_").lower()
        fname = f"layer_{i:02d}" + (f"_{slug}" if slug else "") + ".svg"
        (layers_dir / fname).write_text(render_layer(layer, i, name))
        generated.append((i, name, fname))
        print(f"-> {layers_dir / fname}")

    index = keymap_dir / "layers.md"
    index.write_text(render_index_md(
        data.get("keyboard", ""), data.get("keymap", ""), generated, "layers"))
    print(f"-> {index}")


if __name__ == "__main__":
    main()
