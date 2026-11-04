#!/usr/bin/env python3
"""Generate the KiCad wiring schematic for the string art machine.

Writes wiring.kicad_sch, StringArt.kicad_sym (the module symbols), sym-lib-table and
wiring.kicad_pro next to this script. Every connection is a short wire stub with a net label,
so the netlist is defined entirely by the NET names in BLOCKS below.

Pin numbers and gpio assignments mirror ../fluidnc-config.yaml, which follows the PiBot V4.96 Pro
factory YAML and wiki.

    python3 machine/wiring/make_schematic.py
    flatpak run --command=kicad-cli org.kicad.KiCad sch erc machine/wiring/wiring.kicad_sch
"""

import json
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = "wiring"
LIB = "StringArt"
G = 2.54          # grid
PIN_LEN = 2.54
STUB = 5.08       # wire stub from pin end to label
NS = uuid.UUID("6d1f8a4e-2b7c-4f0e-9a51-3c2d7e8b9f10")


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


FONT = "(effects (font (size 1.27 1.27)))"
HIDE = "(effects (font (size 1.27 1.27)) (hide yes))"

# ---------------------------------------------------------------------------------------------
# Blocks. Pin entries are (pin name, net) or None for a gap; net None means no-connect.
# "hdr" entries (strings) are section captions drawn inside the body above the next pin.
# ---------------------------------------------------------------------------------------------
BLOCKS = [
    dict(ref="J1", sym="PSU_24V", value="24 V 6 A brick + barrel-to-screw adapter",
         at=(38.1, 45.72), w=15.24,
         left=[],
         right=[("+24V", "+24V"), ("GND", "GND")]),
    dict(ref="M4", sym="DRILL_555", value="555 drill motor (24 V)",
         at=(101.6, 106.68), w=12.7, motor=True,
         left=[("+", "DRILL+"), ("-", "GND")],
         right=[]),
    dict(ref="D1", sym="FLYBACK", value="1N5822 flyback (recommended)",
         at=(101.6, 129.54), w=12.7,
         left=[("K", "DRILL+"), ("A", "GND")],
         right=[]),

    dict(ref="U1", sym="PIBOT_V496", value="PiBot V4.96 Pro (ESP32, FluidNC)",
         at=(180.34, 50.8), w=50.8,
         left=["Vmot-main (board) 24 V",
               ("VMAIN+", "+24V"), ("VMAIN-", "GND"),
               "Vmot-driver (sockets) 24 V",
               ("VDRV+", "+24V"), ("VDRV-", "GND"),
               None, "Limit inputs (SW-VCC 5V)",
               ("X_LIM/gpio33", "X_LIM"), ("Y_LIM/gpio32", "Y_LIM"),
               ("Z_LIM/gpio35", "Z_LIM"), ("LIM_GND", "GND"),
               None, "On-board relay (gpio26)",
               ("RLY_COM", "+24V"), ("RLY_NO", "DRILL+"), ("RLY_NC", None)],
         right=["Slot 1 terminal (routing jumpers IN)",
                ("EN/I2SO.0", None), ("STP/I2SO.2", "X_STEP"),
                ("DIR/I2SO.1", "X_DIR"), ("S1_GND", "GND"),
                None, "Socket 2 (Y) signals",
                ("STEP/I2SO.5", "Y_STEP"), ("DIR/I2SO.4", "Y_DIR"), ("EN/I2SO.7", "Y_EN"),
                None, "Socket 3 (Z) signals",
                ("STEP/I2SO.10", "Z_STEP"), ("DIR/I2SO.9", "Z_DIR"), ("EN/I2SO.8", "Z_EN"),
                None, "Driver logic (VDD jumper 5V)",
                ("VDD", "VDD"), ("MS1", "VDD"), ("MS2", "VDD")]),

    dict(ref="U2", sym="DM542T", value="DM542T, DIP 1-8: OFF ON OFF OFF ON ON OFF ON",
         at=(289.56, 30.48), w=15.24,
         left=[("PUL+", "X_STEP"), ("PUL-", "GND"), ("DIR+", "X_DIR"),
               ("DIR-", "GND"), ("ENA+", None), ("ENA-", None)],
         right=[("VDC", "+24V"), ("GND", "GND"), None,
                ("A+", "X_A+"), ("A-", "X_A-"), ("B+", "X_B+"), ("B-", "X_B-")]),
    dict(ref="M1", sym="NEMA23", value="23HS45-4204S platter (X)",
         at=(363.22, 38.1), w=15.24, motor=True,
         left=[("A+/blk", "X_A+"), ("A-/grn", "X_A-"), ("B+/red", "X_B+"), ("B-/blu", "X_B-")],
         right=[]),

    dict(ref="U3", sym="TMC2209", value="TMC2209 in socket 2 (Y), Vref 0.9-1.0 V",
         at=(289.56, 101.6), w=15.24,
         left=[("STEP", "Y_STEP"), ("DIR", "Y_DIR"), ("EN", "Y_EN"),
               ("MS1", "VDD"), ("MS2", "VDD"), ("VIO", "VDD"), ("GND", "GND")],
         right=[("VM", "+24V"), ("GND", "GND"), None,
                ("1A", "Y_A1"), ("1B", "Y_A2"), ("2A", "Y_B1"), ("2B", "Y_B2")]),
    dict(ref="M2", sym="NEMA17", value="17HE08-1004S threader (Y)",
         at=(363.22, 109.22), w=15.24, motor=True,
         left=[("A1/blk", "Y_A1"), ("A2/grn", "Y_A2"), ("B1/red", "Y_B1"), ("B2/blu", "Y_B2")],
         right=[]),

    dict(ref="U4", sym="TMC2209", value="TMC2209 in socket 3 (Z), Vref 0.9-1.0 V",
         at=(289.56, 162.56), w=15.24,
         left=[("STEP", "Z_STEP"), ("DIR", "Z_DIR"), ("EN", "Z_EN"),
               ("MS1", "VDD"), ("MS2", "VDD"), ("VIO", "VDD"), ("GND", "GND")],
         right=[("VM", "+24V"), ("GND", "GND"), None,
                ("1A", "Z_A1"), ("1B", "Z_A2"), ("2A", "Z_B1"), ("2B", "Z_B2")]),
    dict(ref="M3", sym="NEMA17", value="17HE08-1004S drill Z",
         at=(363.22, 170.18), w=15.24, motor=True,
         left=[("A1/blk", "Z_A1"), ("A2/grn", "Z_A2"), ("B1/red", "Z_B1"), ("B2/blu", "Z_B2")],
         right=[]),

    dict(ref="SW1", sym="ENDSTOP", value="X index (nail 0)",
         at=(38.1, 162.56), w=10.16,
         left=[], right=[("COM", "GND"), ("NC", "X_LIM"), ("NO", None)]),
    dict(ref="SW2", sym="ENDSTOP", value="Y home (tip outside)",
         at=(38.1, 187.96), w=10.16,
         left=[], right=[("COM", "GND"), ("NC", "Y_LIM"), ("NO", None)]),
    dict(ref="SW3", sym="ENDSTOP", value="Z home (drill up)",
         at=(38.1, 213.36), w=10.16,
         left=[], right=[("COM", "GND"), ("NC", "Z_LIM"), ("NO", None)]),
]

NOTES = """NOTES
1. Pins follow the PiBot V4.96 Pro factory YAML (wiki.pibot.com, checked 2026-11-04) and
   ../fluidnc-config.yaml. Steppers are on the I2S shift register (I2SO.n). gpio2 is the probe INPUT.
2. Board jumpers: VDD = 5V, SW-VCC = 5V, GPIO26 = Relay Output, USB-5V removed, SPI removed,
   MS1 + MS2 fitted (1/16), RST/SLP off. Slot 1 routing jumpers IN and its socket EMPTY;
   slots 2-6 routing jumpers OUT. A driver in a jumpered slot destroys the driver and the board.
3. Power: 24 V to BOTH Vmot-main (board) and Vmot-driver (socket drivers), plus the DM542T VDC.
   Recommended: inline 5-6 A fuse after J1. Never unplug a motor with power on.
4. DM542T common cathode: STP to PUL+, DIR to DIR+, slot GND to PUL- and DIR-, ENA open.
   DIP SW1-3 = OFF ON OFF (2.36 A RMS), SW4 OFF, SW5-8 = ON ON OFF ON (3200 pulses/rev).
5. TMC2209 standalone, 1/16: MS1 = MS2 = HIGH via the shared MS caps. Vref 0.9-1.0 V, max 1.4 V.
6. Endstops COM to GND, NC to the input: closed at rest, opens when hit or if a wire breaks;
   config pins have no :low. Input LEDs are lit at rest and go out when a switch is pressed.
7. Drill through the on-board relay: COM from +24 V, NO to DRILL+. D1 across the drill, stripe to +.
8. Coil pairs: black/green = A (1A/1B), red/blue = B (2A/2B). Swap one pair to reverse an axis."""


def sides(b):
    """Yield (side, row, entry) with row index for pins and captions."""
    for side in ("left", "right"):
        for i, e in enumerate(b[side]):
            yield side, i, e


def rows(b):
    return max(len(b["left"]), len(b["right"]), 1)


def pin_geom(b, side, row):
    """Pin end in symbol coordinates (Y up) and the pin's angle."""
    half = b["w"] / 2
    y = -row * G
    if side == "left":
        return -half - PIN_LEN, y, 0
    return half + PIN_LEN, y, 180


def body(b):
    n = rows(b)
    return -b["w"] / 2, G * 1.5, b["w"] / 2, -(n - 1) * G - G


def lib_symbol(b, name):
    """Return the symbol definition named `name` (LIB-prefixed in the schematic cache)."""
    base = b["sym"]
    x0, y0, x1, y1 = body(b)
    out = [f"(symbol {q(name)}",
           "(pin_numbers (hide yes)) (pin_names (offset 0.762))",
           "(exclude_from_sim no) (in_bom yes) (on_board yes)",
           f"(property \"Reference\" {q(''.join(c for c in b['ref'] if c.isalpha()))} "
           f"(at {f(x0)} {f(y0 + 1.27)} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))",
           f"(property \"Value\" {q(base)} (at {f(x0)} {f(y1 - 1.27)} 0) "
           f"(effects (font (size 1.27 1.27)) (justify left top)))",
           f"(property \"Footprint\" \"\" (at 0 0 0) {HIDE})",
           f"(property \"Datasheet\" \"\" (at 0 0 0) {HIDE})",
           f"(property \"Description\" \"String art machine module\" (at 0 0 0) {HIDE})",
           f"(symbol {q(base + '_0_1')}",
           f"(rectangle (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) "
           "(stroke (width 0.254) (type default)) (fill (type background)))"]
    if b.get("motor"):
        cx = x1 - 3.81
        cy = (y0 + y1) / 2
        out.append(f"(circle (center {f(cx)} {f(cy)}) (radius 2.54) "
                   "(stroke (width 0.254) (type default)) (fill (type none)))")
        out.append(f"(text \"M\" (at {f(cx)} {f(cy)} 0) {FONT})")
    for side, row, e in sides(b):
        if isinstance(e, str):
            px, py, _ = pin_geom(b, side, row)
            x = x0 + 0.762 if side == "left" else x1 - 0.762
            just = "left" if side == "left" else "right"
            out.append(f"(text {q(e)} (at {f(x)} {f(py)} 0) "
                       f"(effects (font (size 1.27 1.27) (italic yes)) (justify {just})))")
    out.append(")")
    out.append(f"(symbol {q(base + '_1_1')}")
    for num, (side, row, e) in enumerate(p for p in sides(b) if isinstance(p[2], tuple)):
        px, py, ang = pin_geom(b, side, row)
        out.append(f"(pin passive line (at {f(px)} {f(py)} {ang}) (length {f(PIN_LEN)}) "
                   f"(name {q(e[0])} {FONT}) (number {q(num + 1)} {FONT}))")
    out.append(")")
    out.append("(embedded_fonts no)")
    out.append(")")
    return "\n".join(out)


def unique_symbols():
    seen = {}
    for b in BLOCKS:
        if b["sym"] in seen:
            prev = seen[b["sym"]]
            assert [p[0] if isinstance(p, tuple) else p for p in prev["left"] + prev["right"]] == \
                   [p[0] if isinstance(p, tuple) else p for p in b["left"] + b["right"]], b["sym"]
        else:
            seen[b["sym"]] = b
    return seen


def schematic():
    root = uid("root")
    items = []
    nets = {}
    for b in BLOCKS:
        X, Y = b["at"]
        x0, y0, x1, y1 = body(b)
        pins = []
        for num, (side, row, e) in enumerate(p for p in sides(b) if isinstance(p[2], tuple)):
            px, py, _ = pin_geom(b, side, row)
            sx, sy = X + px, Y - py
            pins.append(f"(pin {q(num + 1)} (uuid {q(uid(b['ref'], 'pin', num))}))")
            name, net = e
            if net is None:
                items.append(f"(no_connect (at {f(sx)} {f(sy)}) (uuid {q(uid(b['ref'], 'nc', num))}))")
                continue
            nets.setdefault(net, []).append(f"{b['ref']}.{name}")
            ex = sx - STUB if side == "left" else sx + STUB
            items.append(f"(wire (pts (xy {f(sx)} {f(sy)}) (xy {f(ex)} {f(sy)})) "
                         f"(stroke (width 0) (type default)) (uuid {q(uid(b['ref'], 'w', num))}))")
            ang, just = (180, "right") if side == "left" else (0, "left")
            items.append(f"(label {q(net)} (at {f(ex)} {f(sy)} {ang}) "
                         f"(effects (font (size 1.27 1.27)) (justify {just} bottom)) "
                         f"(uuid {q(uid(b['ref'], 'l', num))}))")
        items.append("\n".join([
            f"(symbol (lib_id {q(LIB + ':' + b['sym'])}) (at {f(X)} {f(Y)} 0) (unit 1)",
            "(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)",
            f"(uuid {q(uid(b['ref'], 'sym'))})",
            f"(property \"Reference\" {q(b['ref'])} (at {f(X + x0)} {f(Y - y0 - 1.27)} 0) "
            "(effects (font (size 1.27 1.27) (bold yes)) (justify left bottom)))",
            f"(property \"Value\" {q(b['value'])} (at {f(X + x0)} {f(Y - y1 + 1.27)} 0) "
            "(effects (font (size 1.27 1.27)) (justify left top)))",
            f"(property \"Footprint\" \"\" (at {f(X)} {f(Y)} 0) {HIDE})",
            f"(property \"Datasheet\" \"\" (at {f(X)} {f(Y)} 0) {HIDE})",
            f"(property \"Description\" \"\" (at {f(X)} {f(Y)} 0) {HIDE})",
            *pins,
            f"(instances (project {q(PROJECT)} (path {q('/' + root)} "
            f"(reference {q(b['ref'])}) (unit 1))))",
            ")"]))

    for net, members in nets.items():
        assert len(members) > 1, f"net {net} has one member: {members}"

    items.append(f"(text {q(NOTES)} (exclude_from_sim no) (at 116.84 170.18 0) "
                 f"(effects (font (size 1.524 1.524)) (justify left top)) (uuid {q(uid('notes'))}))")

    lib_syms = "\n".join(lib_symbol(b, f"{LIB}:{name}") for name, b in unique_symbols().items())
    return "\n".join([
        "(kicad_sch (version 20250114) (generator \"make_schematic\") (generator_version \"9.0\")",
        f"(uuid {q(root)})",
        "(paper \"A3\")",
        "(title_block (title \"String art machine wiring\") (date \"2026-11-04\") (rev \"2\")",
        " (company \"crobison/string-art\") (comment 1 \"Generated by machine/wiring/make_schematic.py\")",
        " (comment 2 \"Pins mirror machine/fluidnc-config.yaml\"))",
        f"(lib_symbols\n{lib_syms}\n)",
        *items,
        "(sheet_instances (path \"/\" (page \"1\")))",
        "(embedded_fonts no)",
        ")"]), nets


def main():
    sch, nets = schematic()
    (HERE / f"{PROJECT}.kicad_sch").write_text(sch + "\n")
    lib = "\n".join(lib_symbol(b, name) for name, b in unique_symbols().items())
    (HERE / f"{LIB}.kicad_sym").write_text(
        "(kicad_symbol_lib (version 20250114) (generator \"make_schematic\") "
        f"(generator_version \"9.0\")\n{lib}\n)\n")
    (HERE / "sym-lib-table").write_text(
        "(sym_lib_table\n  (version 7)\n"
        f"  (lib (name \"{LIB}\")(type \"KiCad\")(uri \"${{KIPRJMOD}}/{LIB}.kicad_sym\")"
        "(options \"\")(descr \"String art machine modules\"))\n)\n")
    pro = HERE / f"{PROJECT}.kicad_pro"
    if not pro.exists():
        pro.write_text(json.dumps({"meta": {"filename": pro.name, "version": 1}}, indent=2) + "\n")
    for net in sorted(nets):
        print(f"{net:12s} {', '.join(nets[net])}")


if __name__ == "__main__":
    main()
