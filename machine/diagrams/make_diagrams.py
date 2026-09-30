#!/usr/bin/env python3
"""
make_diagrams.py — generate the dimensioned SVG schematics referenced by ../PLATTER.md.

All dimensions are in millimetres and live in the DIMS dict so they can be changed in one
place. Run:  python3 make_diagrams.py   (writes *.svg next to this file; no dependencies).
"""
import math
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------------------
# master dimensions (mm)
# ----------------------------------------------------------------------------------------
DIMS = dict(
    base_w=700, base_t=18,            # plywood base plate
    pedestal_d=120, pedestal_h=100,   # laminated plywood hub pedestal
    shf_h=22, shf_d=42,               # SHF12 flange shaft support
    shaft_d=12, shaft_top=196,        # shaft top, measured from base top
    hub_bot=126, hub_top=196, hub_od=45,
    brg_od=28, brg_w=8,               # 6001-2RS
    upper_brg_z=182,                  # upper bearing pocket bottom (pocket 182-190, collar 190-196)
    flange_d=90, flange_t=6,          # hub top flange bolted to platter
    boss_od=40, boss_top=146,         # lower boss the 72T pulley mounts on
    belt_z=138,                       # belt centreline height
    platter_d=600, platter_t=12,      # 12 mm Baltic birch
    nail_r=290, nails=288, nail_len=30, nail_proud=18, nail_lean=12, nail_d=1.5,
    p72_pd=72 * 2 / math.pi, p18_pd=18 * 2 / math.pi,
    motor_cd=155, motor_w=57, motor_h=113, motor_riser=12, shaft23_d=10,
    tower_r=340, tower_w=20, tower_h=300,
    tip_in_r=275, tip_out_r=310, tip_high=234, tip_low=216,
    ramp_start_r=297, ramp_end_r=305,
    roller_r=270,
)
D = DIMS
D["platter_z"] = D["hub_top"]                 # platter underside
D["board_top"] = D["hub_top"] + D["platter_t"]
D["nail_top"] = D["board_top"] + D["nail_proud"]

# ----------------------------------------------------------------------------------------
# tiny SVG helper
# ----------------------------------------------------------------------------------------
class SVG:
    def __init__(self, w, h, title):
        self.w, self.h = w, h
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="Helvetica, Arial, sans-serif" font-size="11">',
            '<defs><marker id="a" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" '
            'markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#c33"/></marker>'
            '<marker id="b" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" '
            'markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#357"/></marker>'
            '<pattern id="wood" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            '<line x1="0" y1="0" x2="0" y2="6" stroke="#b58a4a" stroke-width="1"/></pattern>'
            '<pattern id="steel" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">'
            '<line x1="0" y1="0" x2="0" y2="5" stroke="#667" stroke-width="0.8"/></pattern>'
            '<pattern id="print" width="4" height="4" patternUnits="userSpaceOnUse">'
            '<circle cx="2" cy="2" r="0.7" fill="#3a7"/></pattern></defs>',
            f'<rect width="{w}" height="{h}" fill="#fff"/>',
            f'<text x="12" y="22" font-size="15" font-weight="bold">{title}</text>',
        ]

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill="#eee", stroke="#222", sw=1, extra=""):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def line(self, x1, y1, x2, y2, stroke="#222", sw=1, dash=None, marker=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = f' marker-end="url(#{marker})"' if marker else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
                 f'stroke-width="{sw}"{d}{m}/>')

    def circle(self, cx, cy, r, fill="none", stroke="#222", sw=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}"{d}/>')

    def poly(self, pts, fill="none", stroke="#222", sw=1, close=True):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        tag = "polygon" if close else "polyline"
        self.add(f'<{tag} points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x, y, s, size=11, anchor="start", fill="#222", weight="normal", rot=0):
        r = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
                 f'fill="{fill}" font-weight="{weight}"{r}>{s}</text>')

    def hdim(self, x1, x2, y, label, above=True):
        self.add(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="#c33" '
                 f'stroke-width="1" marker-start="url(#a)" marker-end="url(#a)"/>')
        self.text((x1 + x2) / 2, y - 4 if above else y + 12, label, size=10, anchor="middle", fill="#c33")

    def vdim(self, x, y1, y2, label, side="left"):
        self.add(f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="#c33" '
                 f'stroke-width="1" marker-start="url(#a)" marker-end="url(#a)"/>')
        if side == "left":
            self.text(x - 5, (y1 + y2) / 2 + 4, label, size=10, anchor="end", fill="#c33")
        else:
            self.text(x + 5, (y1 + y2) / 2 + 4, label, size=10, anchor="start", fill="#c33")

    def note(self, x, y, s, size=10):
        self.text(x, y, s, size=size, fill="#444")

    def save(self, name):
        self.add("</svg>")
        path = os.path.join(OUT, name)
        with open(path, "w") as f:
            f.write("\n".join(self.parts))
        print("wrote", path)


# ----------------------------------------------------------------------------------------
# 1. hub / platter section
# ----------------------------------------------------------------------------------------
def hub_section():
    S = 1.5
    ox, oy = 340, 560
    X = lambda mm: ox + mm * S
    Z = lambda mm: oy - mm * S
    s = SVG(1120, 610, "1. Platter hub section (side view through the axis, tower at right)")

    left = -140
    # base plate
    s.rect(X(left), Z(0), (D["tower_r"] + 40 - left) * S, D["base_t"] * S, fill="url(#wood)")
    s.text(X(left + 4), Z(-13), f'base plate {D["base_w"]} x {D["base_w"]} x {D["base_t"]} plywood (partial view; sits on a bench)', size=10)

    # pedestal
    pr = D["pedestal_d"] / 2
    s.rect(X(-pr), Z(D["pedestal_h"]), 2 * pr * S, D["pedestal_h"] * S, fill="url(#wood)")
    s.text(X(-pr + 4), Z(56), f'pedestal Ø{D["pedestal_d"]} x {D["pedestal_h"]}', size=10)
    s.text(X(-pr + 4), Z(42), "laminated plywood rounds,", size=10)
    s.text(X(-pr + 4), Z(28), "glued + screwed to base", size=10)

    # SHF12
    sr = D["shf_d"] / 2
    z0 = D["pedestal_h"]
    s.rect(X(-sr), Z(z0 + D["shf_h"]), 2 * sr * S, D["shf_h"] * S, fill="#bbb")
    s.text(X(sr + 5), Z(z0 + 6), "SHF12 flange shaft support, 4x M5", size=10)

    # shaft
    shr = D["shaft_d"] / 2
    s.rect(X(-shr), Z(D["shaft_top"]), 2 * shr * S, (D["shaft_top"] - z0) * S, fill="url(#steel)")

    # hub body, boss, flange
    hr = D["hub_od"] / 2
    s.rect(X(-hr), Z(D["hub_top"]), 2 * hr * S, (D["hub_top"] - D["hub_bot"]) * S, fill="url(#print)")
    br = D["boss_od"] / 2
    s.rect(X(-br), Z(D["boss_top"]), 2 * br * S, (D["boss_top"] - D["hub_bot"]) * S, fill="url(#print)")
    fr = D["flange_d"] / 2
    s.rect(X(-fr), Z(D["hub_top"]), 2 * fr * S, D["flange_t"] * S, fill="url(#print)")

    # bearings
    bo = D["brg_od"] / 2
    for zb in (D["hub_bot"], D["upper_brg_z"]):
        for sign in (-1, 1):
            s.rect(X(min(sign * shr, sign * bo)), Z(zb + D["brg_w"]), (bo - shr) * S, D["brg_w"] * S, fill="#89c")
    # collars: spacer under lower bearing, preload collar above upper bearing (recessed in hub top)
    s.rect(X(-9), Z(D["hub_bot"]), 18 * S, 4 * S, fill="#999")
    s.rect(X(-9), Z(D["upper_brg_z"] + D["brg_w"] + 6), 18 * S, 6 * S, fill="#999")

    # 72T pulley on the boss
    pr72 = D["p72_pd"] / 2 + 1
    s.rect(X(-pr72), Z(D["belt_z"] + 8), 2 * pr72 * S, 16 * S, fill="#dd8")

    # platter
    s.rect(X(left), Z(D["board_top"]), (300 - left) * S, D["platter_t"] * S, fill="url(#wood)")
    s.text(X(left + 4), Z(D["board_top"] + 30), f'platter Ø{D["platter_d"]} x {D["platter_t"]} Baltic birch, bolted to hub flange (6x M5)', size=10)

    # nail at the ring, leaning outward
    nx = D["nail_r"]
    lean = math.radians(D["nail_lean"])
    top = (nx + D["nail_proud"] * math.sin(lean), D["board_top"] + D["nail_proud"] * math.cos(lean))
    s.line(X(nx), Z(D["board_top"]), X(top[0]), Z(top[1]), stroke="#333", sw=2.5)
    s.line(X(nx), Z(D["board_top"]), X(nx - 12 * math.sin(lean)), Z(D["board_top"] - 12 * math.cos(lean)),
           stroke="#333", sw=2.5, dash="3,2")
    s.text(X(nx - 118), Z(D["nail_top"] + 4), f'nail Ø{D["nail_d"]} x {D["nail_len"]}, {D["nail_lean"]}° outward lean', size=10)

    # motor under platter on riser
    mx = D["motor_cd"]
    mw = D["motor_w"] / 2
    s.rect(X(mx - mw), Z(D["motor_riser"]), 2 * mw * S, D["motor_riser"] * S, fill="url(#wood)")
    s.rect(X(mx - mw), Z(D["motor_riser"] + D["motor_h"]), 2 * mw * S, D["motor_h"] * S, fill="#ccc")
    s.text(X(mx - mw + 4), Z(70), "NEMA23", size=11, weight="bold")
    s.text(X(mx - mw + 4), Z(56), "23HS45-4204S", size=10)
    s.text(X(mx - mw + 4), Z(42), "on 12 mm riser", size=10)
    s.text(X(mx - mw + 4), Z(28), "(slotted, for tension)", size=10)
    zs = D["motor_riser"] + D["motor_h"]
    s.rect(X(mx - 5), Z(zs + 21), 10 * S, 21 * S, fill="url(#steel)")
    pr18 = D["p18_pd"] / 2 + 1
    s.rect(X(mx - pr18), Z(D["belt_z"] + 8), 2 * pr18 * S, 16 * S, fill="#dd8")
    # belt
    s.line(X(pr72), Z(D["belt_z"] + 7), X(mx - pr18), Z(D["belt_z"] + 7), stroke="#a52", sw=2)
    s.line(X(pr72), Z(D["belt_z"] - 7), X(mx - pr18), Z(D["belt_z"] - 7), stroke="#a52", sw=2)

    # labels for hub stack: right column between platter and belt, left column beside the belt
    lx = X(fr + 6)
    s.text(lx, Z(D["hub_top"] - 4), "hub top flange Ø90 x 6 (printed PETG or aluminium)", size=10)
    s.text(lx, Z(D["hub_top"] - 16), "preload collar Ø12, recessed in hub top", size=10)
    s.text(lx, Z(D["hub_top"] - 28), "6001-2RS upper bearing, pocket Ø28 x 8", size=10)
    s.text(lx, Z(D["hub_top"] - 40), "hub body Ø45, 70 tall", size=10)
    s.text(X(mx + pr18 + 6), Z(D["belt_z"] - 4), "18T GT2, 10 mm bore", size=10)
    lxl = X(-pr - 6)
    s.text(lxl, Z(D["belt_z"] + 12), f'72T GT2 (PD {D["p72_pd"]:.1f}) on boss Ø40, 4x M4', size=10, anchor="end")
    s.text(lxl, Z(D["belt_z"] + 1), "GT2 belt; tensioner idler not shown", size=10, anchor="end")
    s.text(lxl, Z(D["hub_bot"] + 2), "6001-2RS lower bearing", size=10, anchor="end")
    s.text(lxl, Z(D["hub_bot"] - 9), "spacer 4 mm", size=10, anchor="end")

    # tower and head plate
    tx = D["tower_r"]
    s.rect(X(tx - 10), Z(D["tower_h"]), 20 * S, D["tower_h"] * S, fill="#9ab")
    s.text(X(tx + 14), Z(D["tower_h"] - 14), "2020 extrusion", size=10)
    s.text(X(tx + 14), Z(D["tower_h"] - 28), "300 mm tower", size=10)
    hp_z = D["nail_top"] + 30
    s.rect(X(tx - 16), Z(hp_z + 40), 6 * S, 80 * S, fill="#bbb")
    s.text(X(tx - 20), Z(hp_z + 38), "head plate (swappable)", size=10, anchor="end")
    s.rect(X(D["tip_in_r"] - 20), Z(hp_z + 12), (tx - 16 - D["tip_in_r"] + 20) * S, 12 * S, fill="#9ab")
    s.text(X(D["tip_in_r"] - 22), Z(hp_z + 1), "linear slide, 40 mm stroke", size=10)
    s.line(X(D["tip_in_r"]), Z(hp_z), X(D["tip_in_r"]), Z(D["tip_high"]), stroke="#c33", sw=2)
    s.circle(X(D["tip_in_r"]), Z(D["tip_high"]), 3, fill="#c33")
    s.text(X(D["tip_in_r"] - 8), Z(D["tip_high"] + 4), "tip (inside, high)", size=10, fill="#c33", anchor="end")

    # vertical dimension stack at far left
    dx = X(left + 30)
    s.vdim(dx, Z(0), Z(D["pedestal_h"]), f'{D["pedestal_h"]}')
    s.vdim(dx, Z(D["pedestal_h"]), Z(D["hub_bot"]), "26")
    s.vdim(dx, Z(D["hub_bot"]), Z(D["hub_top"]), "70")
    s.vdim(dx, Z(D["hub_top"]), Z(D["board_top"]), "12")
    s.vdim(X(left + 8), Z(0), Z(D["board_top"]), f'{D["board_top"]}')
    s.hdim(X(-hr), X(hr), Z(D["hub_bot"] - 18), f'Ø{D["hub_od"]}')
    s.hdim(X(0), X(mx), Z(D["board_top"] + 42), f'centre distance {D["motor_cd"]} (set by your belt length)')
    s.hdim(X(0), X(D["nail_r"]), Z(D["board_top"] + 62), f'nail ring R = {D["nail_r"]}')
    s.hdim(X(0), X(tx), Z(D["board_top"] + 84), f'tower R = {D["tower_r"]}')
    s.vdim(X(mx + 100), Z(0), Z(D["belt_z"]), f'belt centreline {D["belt_z"]}', side="right")
    s.vdim(X(nx + 22), Z(D["board_top"]), Z(D["nail_top"]), f'{D["nail_proud"]} proud', side="right")
    for zz in (0, D["belt_z"]):
        s.line(X(mx + 30), Z(zz), X(mx + 100), Z(zz), stroke="#c33", sw=0.6, dash="2,2")

    s.note(12, 602, "Fixed shaft, rotating hub. Two deep-groove bearings 56 mm apart carry the weight and the moment; "
                    "pulley and platter are one rigid body on the hub. Nothing slides on wood.")
    s.save("1_hub_section.svg")


# ----------------------------------------------------------------------------------------
# 2. plan view
# ----------------------------------------------------------------------------------------
def plan_view():
    S = 0.62
    cx, cy = 380, 320
    X = lambda mm: cx + mm * S
    Y = lambda mm: cy + mm * S
    s = SVG(1000, 640, "2. Plan view (from above). Nail 0 and the tower are at 12 o'clock.")

    b = D["base_w"] / 2
    s.rect(X(-b), Y(-b), 2 * b * S, 2 * b * S, fill="url(#wood)")
    s.text(X(-b + 6), Y(-b + 14), f'base {D["base_w"]} x {D["base_w"]}', size=10)

    # platter + ring
    s.circle(X(0), Y(0), D["platter_d"] / 2 * S, fill="#f6ecd8", stroke="#222", sw=1.5)
    s.circle(X(0), Y(0), D["nail_r"] * S, stroke="#222", dash="2,3")
    for i in range(D["nails"]):
        a = -math.pi / 2 + 2 * math.pi * i / D["nails"]
        r1, r2 = D["nail_r"] - 2, D["nail_r"] + 2
        s.line(X(r1 * math.cos(a)), Y(r1 * math.sin(a)), X(r2 * math.cos(a)), Y(r2 * math.sin(a)), stroke="#333", sw=0.7)
    s.text(X(-D["nail_r"] * 0.7 + 10), Y(-D["nail_r"] * 0.7 - 6), f'{D["nails"]} nails, pitch {2 * math.pi * D["nail_r"] / D["nails"]:.2f} mm', size=10)

    # hidden parts under the platter, dashed
    for ang in (90 + 30, 90 - 30, -90):
        a = math.radians(ang)
        rx, ry = D["roller_r"] * math.cos(a), D["roller_r"] * math.sin(a)
        s.circle(X(rx), Y(ry), 11 * S, fill="none", stroke="#a60", sw=1.5, dash="3,2")
    s.text(X(-b + 6), Y(b - 8), "dashed = under the platter: 3x rim rollers (608 wheels) at R 270, home switch, motor, belt", size=10)

    s.circle(X(0), Y(0), D["p72_pd"] / 2 * S, fill="#dd8", stroke="#886", dash="3,2")
    s.circle(X(0), Y(0), D["shaft_d"] / 2 * S, fill="#888")
    s.text(X(28), Y(-4), "72T", size=10)
    mx, my = 0, D["motor_cd"]
    mw = D["motor_w"] / 2
    s.rect(X(mx - mw), Y(my - mw), 2 * mw * S, 2 * mw * S, fill="none", stroke="#555", extra='stroke-dasharray="4,3"')
    s.circle(X(mx), Y(my), D["p18_pd"] / 2 * S, fill="#dd8", stroke="#886", dash="3,2")
    s.text(X(mx + 34), Y(my + 4), "NEMA23 + 18T", size=10)
    r72, r18 = D["p72_pd"] / 2, D["p18_pd"] / 2
    s.line(X(-r72), Y(0), X(-r18), Y(my), stroke="#a52", sw=1.5, dash="4,3")
    s.line(X(r72), Y(0), X(r18), Y(my), stroke="#a52", sw=1.5, dash="4,3")
    s.circle(X(r72 * 0.6 + 14), Y(my * 0.5), 8 * S, fill="none", stroke="#a52", dash="3,2")
    s.text(X(r72 * 0.6 + 26), Y(my * 0.5 + 4), "your printed tensioner idler", size=10)
    s.rect(X(-D["nail_r"] + 4), Y(-8), 16 * S, 16 * S, fill="none", stroke="#262", extra='stroke-dasharray="3,2"')
    s.text(X(-D["nail_r"] + 26), Y(-14), "home switch on base,", size=10)
    s.text(X(-D["nail_r"] + 26), Y(0), "tab on platter underside", size=10)

    # tower + head at 12 o'clock
    tx, ty = 0, -D["tower_r"]
    s.rect(X(tx - 10), Y(ty - 10), 20 * S, 20 * S, fill="#9ab", stroke="#357")
    s.rect(X(tx - 50), Y(ty - 4), 100 * S, 8 * S, fill="#bbb", stroke="#555")
    s.text(X(tx + 60), Y(ty - 8), "tower (2020) + head plate 100 wide", size=10)
    s.rect(X(tx - 6), Y(-D["tip_out_r"]), 12 * S, (D["tip_out_r"] - D["tip_in_r"]) * S, fill="#9ab", stroke="#357")
    s.circle(X(tx), Y(-D["tip_in_r"]), 3, fill="#c33")
    s.circle(X(tx), Y(-D["tip_out_r"]), 3, fill="none", stroke="#c33")
    s.text(X(tx + 12), Y(-D["tip_in_r"] + 10), f'tip IN  R{D["tip_in_r"]}', size=10, fill="#c33")
    s.text(X(tx + 12), Y(-D["tip_out_r"] - 4), f'tip OUT R{D["tip_out_r"]}', size=10, fill="#c33")
    s.text(X(tx - 14), Y(-D["nail_r"] + 4), "nail 0", size=10, weight="bold", anchor="end")

    # dims to the right of the base
    s.hdim(X(0), X(D["platter_d"] / 2), Y(b - 30), f'R {D["platter_d"] // 2}')
    s.vdim(X(b + 30), Y(0), Y(D["motor_cd"]), f'{D["motor_cd"]}', side="right")
    s.vdim(X(b + 30), Y(0), Y(-D["tower_r"]), f'{D["tower_r"]}', side="right")
    s.vdim(X(b + 80), Y(0), Y(-D["nail_r"]), f'{D["nail_r"]}', side="right")

    s.note(12, 622, "Platter turns clockwise (viewed from above) for +X. Only the tower and head stand above the platter.")
    s.save("2_plan_view.svg")


# ----------------------------------------------------------------------------------------
# 3. wrap sequence
# ----------------------------------------------------------------------------------------
def wrap_sequence():
    s = SVG(1000, 440, "3. Wrap sequence, plan view close-up at the ring (thread wraps the OUTSIDE of each nail)")
    panels = [
        ("A  rest / index", "G0 X n+0.5   (tip inside, high)", 0.5, "in"),
        ("B  out", "G0 Y outside   (tip crosses high, drops outside)", 0.5, "out"),
        ("C  sweep", "G0 X n-0.5   (platter turns back one pitch)", -0.5, "out"),
        ("D  in", "G0 Y inside   (tip rises, crosses back in)", -0.5, "in"),
    ]
    pitch = 60
    for k, (title, gcode, delta, tip) in enumerate(panels):
        ox = 40 + k * 240
        oy = 230
        s.text(ox, 52, title, size=12, weight="bold")
        s.text(ox, 68, gcode, size=9, fill="#c33")
        s.line(ox - 10, oy, ox + 200, oy, stroke="#999", dash="3,3")
        s.text(ox + 186, oy - 6, "outside", size=9, fill="#999")
        s.text(ox + 186, oy + 14, "inside", size=9, fill="#999")
        nails = {}
        for j, name in enumerate(("n-1", "n", "n+1")):
            nx = ox + 40 + j * pitch
            nails[name] = nx
            s.circle(nx, oy, 4, fill="#333")
            s.text(nx - 8, oy - 10, name, size=10)
        tx = nails["n"] + delta * pitch
        ty = oy - 30 if tip == "out" else oy + 30
        px, py = ox + 60, oy + 130
        s.circle(px, py, 4, fill="#333")
        s.text(px + 8, py + 4, "P (previous nail)", size=9)
        n = nails["n"]
        if k in (0, 1):
            s.line(px, py, tx, ty, stroke="#c33", sw=1.5)
        elif k == 2:
            s.line(px, py, n + 4, oy - 2, stroke="#c33", sw=1.5)
            s.line(n + 4, oy - 2, tx, ty, stroke="#c33", sw=1.5)
        else:
            s.line(px, py, n + 4, oy - 2, stroke="#c33", sw=1.5)
            s.line(n + 4, oy - 2, n - 3, oy - 4, stroke="#c33", sw=1.5)
            s.line(n - 3, oy - 4, tx, ty, stroke="#c33", sw=1.5)
        s.circle(tx, ty, 5, fill="#fff" if tip == "out" else "#c33", stroke="#c33", sw=2)
        s.text(tx + 9, ty + (-6 if tip == "out" else 16), "tip " + ("LOW" if tip == "out" else "HIGH"), size=9, fill="#c33")
        if k == 2:
            s.add(f'<path d="M{n + 34},{oy - 52} A 38 38 0 0 0 {n - 34},{oy - 52}" '
                  f'fill="none" stroke="#357" stroke-width="1.5" marker-end="url(#b)"/>')
            s.text(n - 40, oy - 60, "platter turns 1 nail (tip sweeps past n on the outside)", size=9, fill="#357")
    s.note(12, 405, "The tip only ever moves radially. The platter's own ±0.5-nail moves do the tangential sweep. In the platter's frame the")
    s.note(12, 420, "tip circles nail n on the outside, so the thread hooks it and leaves inward. The tip is above the nail tops whenever")
    s.note(12, 435, "it crosses the ring (B and D), so it never has to hit the 5 mm gap between nails.")
    s.save("3_wrap_sequence.svg")


# ----------------------------------------------------------------------------------------
# 4. threader head side view with cam ramp
# ----------------------------------------------------------------------------------------
def threader_head():
    S = 5.5
    ox, oy = 60, 600
    X = lambda mm: ox + (mm - 258) * S            # window R 258..352
    Z = lambda mm: oy - (mm - 195) * S            # window z 195..300
    s = SVG(1000, 660, "4. Threader head, side view along the ring (radial = left/right). Passive cam ramp dips the tip outside the ring.")

    # board and nail
    s.rect(X(258), Z(D["board_top"]), (300 - 258) * S, D["platter_t"] * S, fill="url(#wood)")
    s.text(X(260), Z(D["board_top"] - 9.5), "platter (edge at R 300)", size=10)
    lean = math.radians(D["nail_lean"])
    r = D["nail_r"]
    top = (r + D["nail_proud"] * math.sin(lean), D["board_top"] + D["nail_proud"] * math.cos(lean))
    s.line(X(r), Z(D["board_top"]), X(top[0]), Z(top[1]), stroke="#333", sw=3)
    for i in range(6):
        zz = D["board_top"] + 0.6 + i * 0.9
        rr = r + (zz - D["board_top"]) * math.tan(lean) + 1.0
        s.circle(X(rr), Z(zz), 1.6, fill="#c33", stroke="none")
    s.text(X(295), Z(D["board_top"] + 2), "wrap stack (≤3 mm)", size=9, fill="#c33")
    s.line(X(258), Z(D["nail_top"]), X(312), Z(D["nail_top"]), stroke="#999", dash="2,2")
    s.text(X(259), Z(D["nail_top"] - 4), f'nail tops z {D["nail_top"]}', size=9, fill="#666")

    # tower + head plate
    s.rect(X(D["tower_r"] - 10), Z(296), 20 * S, 101 * S, fill="#9ab")
    s.text(X(D["tower_r"] - 6), Z(292), "tower", size=10)
    hp_z = D["nail_top"] + 30
    s.rect(X(D["tower_r"] - 16), Z(hp_z + 40), 6 * S, 80 * S, fill="#bbb")
    s.text(X(D["tower_r"] - 18), Z(hp_z + 42), "head plate", size=10, anchor="end")
    rail_z = hp_z + 12
    s.rect(X(D["tip_in_r"] - 25), Z(rail_z + 6), (D["tower_r"] - 16 - D["tip_in_r"] + 25) * S, 6 * S, fill="#9ab")
    s.text(X(D["tip_in_r"] - 24), Z(rail_z + 14), "MGN12 rail 150 (or 2x Ø8 rod + LM8UU), GT2 belt to NEMA17 pancake on the plate", size=9)

    # carriage + tip arm at inside (solid) and outside (ghost)
    ramp_hi = rail_z - 20
    step = (D["tip_high"] - D["tip_low"]) / 1.8
    ramp_lo = ramp_hi - step
    for rpos, ghost in ((D["tip_in_r"], False), (D["tip_out_r"], True)):
        col = "#357" if not ghost else "#59a"
        s.rect(X(rpos - 12), Z(rail_z + 12), 24 * S, 6 * S, fill="none", stroke=col, sw=1.5)
        tipz = D["tip_high"] if not ghost else D["tip_low"]
        follower_z = ramp_hi if not ghost else ramp_lo
        s.line(X(rpos), Z(rail_z), X(rpos), Z(tipz), stroke=col, sw=2)
        s.circle(X(rpos + 4), Z(follower_z + 2), 2.5 * S * 0.6, fill="#fff", stroke=col, sw=1.5)
        s.circle(X(rpos), Z(tipz), 3, fill=col)
        s.text(X(rpos) + 8, Z(tipz) + 4, f'tip {"LOW" if ghost else "HIGH"} z {tipz}', size=9, fill=col)
    s.text(X(D["tip_in_r"] + 6), Z(ramp_hi + 6), "follower wheel", size=9, fill="#357")

    pts = [(D["tip_in_r"] - 25, ramp_hi), (D["ramp_start_r"], ramp_hi), (D["ramp_end_r"], ramp_lo), (D["tower_r"] - 16, ramp_lo)]
    s.poly([(X(a), Z(b)) for a, b in pts], stroke="#a60", sw=2.5, close=False)
    s.text(X(D["tip_in_r"] - 3), Z(ramp_hi + 6), "cam ramp (fixed)", size=9, fill="#a60", anchor="end")
    s.text(X(D["tip_in_r"] - 3), Z(ramp_lo + 1), f'drop R {D["ramp_start_r"]}→{D["ramp_end_r"]}', size=9, fill="#a60", anchor="end")
    s.text(X(D["tip_in_r"] - 3), Z(ramp_lo - 2), f'step {step:.0f} x lever 1.8 = {D["tip_high"] - D["tip_low"]} at tip', size=9, fill="#a60", anchor="end")

    # dims below the board
    s.hdim(X(D["tip_in_r"]), X(D["tip_out_r"]), Z(197.5), f'stroke {D["tip_out_r"] - D["tip_in_r"]}')
    s.hdim(X(D["nail_r"]), X(D["tip_out_r"]), Z(204), f'{D["tip_out_r"] - D["nail_r"]}')
    s.hdim(X(D["tip_in_r"]), X(D["nail_r"]), Z(204), f'{D["nail_r"] - D["tip_in_r"]}')
    s.vdim(X(266), Z(D["board_top"]), Z(D["tip_low"]), f'{D["tip_low"] - D["board_top"]}')
    s.vdim(X(262), Z(D["board_top"]), Z(D["tip_high"]), f'{D["tip_high"] - D["board_top"]}')
    s.vdim(X(284), Z(D["board_top"]), Z(D["nail_top"]), f'{D["nail_proud"]}')

    s.note(12, 632, "Tip = 16G blunt dispensing needle (1.65 OD / 1.19 ID) in a printed holder, thread fed from above through a PTFE tube.")
    s.note(12, 647, "Clearances: tip HIGH is 8 mm above the nail tops (3.7 mm outward lean of the tops included); tip LOW is 8 mm above the board, 10 mm below the tops.")
    s.save("4_threader_head.svg")


# ----------------------------------------------------------------------------------------
# 5. nail and thread-stack detail (exaggerated thread size)
# ----------------------------------------------------------------------------------------
def nail_detail():
    S = 6.0
    ox, oy = 260, 300
    X = lambda mm: ox + mm * S
    Z = lambda mm: oy - mm * S
    s = SVG(1000, 430, "5. Nail detail: outward lean makes every new wrap slide down onto the stack (thread size exaggerated)")
    lean = math.radians(D["nail_lean"])
    s.rect(X(-30), Z(0), 70 * S, 12 * S, fill="url(#wood)")
    s.text(X(-29), Z(-10), "platter, 12 mm Baltic birch", size=10)
    hole_depth = 12
    hx = hole_depth * math.sin(lean)
    s.poly([(X(-0.8), Z(0)), (X(0.8), Z(0)), (X(0.8 - hx), Z(-hole_depth)), (X(-0.8 - hx), Z(-hole_depth))], fill="#fff", stroke="#555")
    proud = D["nail_proud"]
    s.poly([(X(-0.75 - hx), Z(-hole_depth)), (X(0.75 - hx), Z(-hole_depth)),
            (X(0.75 + proud * math.sin(lean)), Z(proud)), (X(-0.75 + proud * math.sin(lean)), Z(proud))], fill="#666", stroke="#222")
    # exaggerated wraps on the outer face
    for i in range(8):
        z = 0.5 + i * 0.6
        rr = 0.75 + z * math.tan(lean) + 0.45
        s.circle(X(rr), Z(z), 2.4, fill="#c33", stroke="none")
    s.text(X(8), Z(12), "wraps (Ø0.15–0.2 thread) stack up the OUTER face,", size=10, fill="#c33")
    s.text(X(8), Z(10.2), "≤3 mm for ~14 wraps per nail", size=10, fill="#c33")
    # forces
    s.line(X(4), Z(3.5), X(-8), Z(3.5), stroke="#357", sw=2, marker="b")
    s.text(X(-30), Z(5.5), "chord tension T pulls inward", size=10, fill="#357")
    s.line(X(4), Z(3.5), X(4 - 3 * math.sin(lean)), Z(3.5 - 3 * math.cos(lean)), stroke="#3a7", sw=2, marker="b")
    s.text(X(10), Z(0.8), f'T·sin({D["nail_lean"]}°) pushes the wrap DOWN the nail', size=10, fill="#3a7")
    s.line(X(0), Z(0), X(0), Z(proud + 3), stroke="#999", dash="2,2")
    s.text(X(1), Z(proud + 2), f'{D["nail_lean"]}° lean: tops move {proud * math.sin(lean):.1f} mm outward', size=10)
    s.vdim(X(-12), Z(0), Z(proud), f'{proud} proud')
    s.vdim(X(-20), Z(0), Z(-hole_depth), f'{hole_depth} deep, Ø1.3 hole')
    s.vdim(X(5.5), Z(0), Z(3), "≤3", side="right")
    s.note(12, 398, f'Effective wrap radius drifts outward by 3 × tan({D["nail_lean"]}°) = {3 * math.tan(lean):.2f} mm over a full stack, the same on every nail: '
                    "a uniform radius change, not an error.")
    s.note(12, 414, "Use smooth-shank pins (no rings or ridges). A small head is fine and acts as a safety stop; the tip clears it by 8 mm.")
    s.save("5_nail_detail.svg")


if __name__ == "__main__":
    hub_section()
    plan_view()
    wrap_sequence()
    threader_head()
    nail_detail()
