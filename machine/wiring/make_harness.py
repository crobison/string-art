#!/usr/bin/env python3
"""Generate step-by-step WireViz wiring diagrams for the string art machine.

Each STEP below becomes harness/NN_name.yml and is rendered by WireViz to .png/.svg/.html (the
html includes the parts and wire list). The same wires are written into guide.html, the
illustrated novice guide built from guide.src.html. Every wire is checked against the KiCad netlist from
make_schematic.py, so the two drawings cannot disagree: a wire whose ends are on different nets,
or that lands on a no-connect pin, stops the build.

    .venv/bin/pip install wireviz          # needs graphviz (apt install graphviz)
    .venv/bin/python machine/wiring/make_harness.py
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
OUT = HERE / "harness"
sys.path.insert(0, str(HERE))
import make_schematic  # noqa: E402

POWER = "18 AWG"
SIGNAL = "22 AWG"

# ---------------------------------------------------------------------------------------------
# Connectors: pins are (label, kicad) where kicad is "REF.PIN" from make_schematic.BLOCKS, or
# "=NET" for something that is only a net (the lever-nut blocks).
# ---------------------------------------------------------------------------------------------
CONNECTORS = {
    "PSU": dict(type="24 V power brick", subtype="barrel adapter rated 10 A, or bare leads",
                pins=[("+", "J1.+24V"), ("-", "J1.GND")], colors=["RD", "BK"],
                notes="Set the brick to 24.0 V (never higher) with a meter BEFORE connecting anything."),
    "WAGO+": dict(type="Wago 221-415 lever nut", subtype="+24 V bus (5-way)",
                  pins=[(f"+24V {i}", "=+24V") for i in range(1, 6)], colors=["RD"] * 5,
                  notes="All 5 slots are the same point. Strip 11 mm, lift lever, insert, close."),
    "WAGO-": dict(type="Wago 221-415 lever nut", subtype="GND bus (5-way)",
                  pins=[(f"GND {i}", "=GND") for i in range(1, 6)], colors=["BK"] * 5,
                  notes="All 5 slots are the same point."),
    "PIBOT_PWR": dict(type="PiBot V4.96 Pro", subtype="orange power inputs, bottom edge",
                      pins=[("Vmot +", "U1.VMAIN+"), ("Vmot -", "U1.VMAIN-"),
                            ("Vmot-Driver +", "U1.VDRV+"), ("Vmot-Driver -", "U1.VDRV-")],
                      notes="Vmot (orange plug, CN3) powers the board. Vmot-Driver (CN4) powers the\n"
                            "socket drivers. Both need 24 V. + and - are printed under each.\n"
                            "\"VMOT Main\" on the black 5-pin header is an output: nothing goes there."),
    "DM542T_HV": dict(type="DM542T", subtype="power + motor terminal",
                      pins=[("GND", "U2.GND"), ("+VDC", "U2.VDC"), ("A+", "U2.A+"),
                            ("A-", "U2.A-"), ("B+", "U2.B+"), ("B-", "U2.B-")],
                      notes="Follow the labels printed on the driver, not this order."),
    "DM542T_SIG": dict(type="DM542T", subtype="signal terminal",
                       pins=[("PUL+", "U2.PUL+"), ("PUL-", "U2.PUL-"), ("DIR+", "U2.DIR+"),
                             ("DIR-", "U2.DIR-"), ("ENA+", "U2.ENA+"), ("ENA-", "U2.ENA-")],
                       loops=[[2, 4]],
                       notes="Short jumper PUL- to DIR-. ENA+ and ENA- stay empty.\n"
                             "DIP switches 1-8: OFF ON OFF OFF ON ON OFF ON.\n"
                             "5V/24V signal selector (newer drivers): 5V."),
    "PIBOT_X": dict(type="PiBot V4.96 Pro", subtype="slot 1 green terminal (X, routing jumpers in)",
                    pins=[("EN", "U1.EN/I2SO.0"), ("STP", "U1.STP/I2SO.2"),
                          ("DIR", "U1.DIR/I2SO.1"), ("GND", "U1.S1_GND")],
                    notes="Slot 1's StepStick socket stays EMPTY. The terminal has no pin labels:\n"
                          "find GND with a continuity beep to Vmot -, then DIR, STP, EN follow."),
    "NEMA23": dict(type="NEMA23 23HS45-4204S", subtype="platter motor (X), 4 flying leads",
                   pins=[("A+", "M1.A+/blk"), ("A-", "M1.A-/grn"), ("B+", "M1.B+/red"),
                         ("B-", "M1.B-/blu")], colors=["BK", "GN", "RD", "BU"]),
    "PIBOT_YM": dict(type="PiBot V4.96 Pro", subtype="slot 2 green terminal (Y, TMC2209 fitted)",
                     pins=[("2B", "U3.2B"), ("2A", "U3.2A"), ("1A", "U3.1A"), ("1B", "U3.1B")],
                     notes="No pin labels on the board. Pins 1-4 are 2B, 2A, 1A, 1B:\n"
                           "one coil on the two screws at each end."),
    "NEMA17_Y": dict(type="NEMA17 17HE08-1004S pancake", subtype="threader motor (Y)",
                     pins=[("A+", "M2.A+/blk"), ("A-", "M2.A-/blu"), ("B+", "M2.B+/grn"),
                           ("B-", "M2.B-/red")], colors=["BK", "BU", "GN", "RD"],
                     notes="Coils: black-blue and green-red, about 3.6 ohm each."),
    "PIBOT_ZM": dict(type="PiBot V4.96 Pro", subtype="slot 3 green terminal (Z, TMC2209 fitted)",
                     pins=[("2B", "U4.2B"), ("2A", "U4.2A"), ("1A", "U4.1A"), ("1B", "U4.1B")],
                     notes="No pin labels on the board. Pins 1-4 are 2B, 2A, 1A, 1B:\n"
                           "one coil on the two screws at each end."),
    "NEMA17_Z": dict(type="NEMA17 17HE08-1004S pancake", subtype="drill feed motor (Z)",
                     pins=[("A+", "M3.A+/blk"), ("A-", "M3.A-/blu"), ("B+", "M3.B+/grn"),
                           ("B-", "M3.B-/red")], colors=["BK", "BU", "GN", "RD"],
                     notes="Coils: black-blue and green-red, about 3.6 ohm each."),
    "PIBOT_XL": dict(type="PiBot V4.96 Pro", subtype="X limit input io33 (3-pin JST-XH)",
                     pins=[("SIG", "U1.X_LIM/gpio33"), ("GND", "U1.LIM_GND"), ("5V", "U1.SW_VCC")],
                     notes="GND is the middle pin. The end pin that reads 5 V is SW-VCC: leave it empty."),
    "PIBOT_YL": dict(type="PiBot V4.96 Pro", subtype="Y limit input io32 (3-pin JST-XH)",
                     pins=[("SIG", "U1.Y_LIM/gpio32"), ("GND", "U1.LIM_GND"), ("5V", "U1.SW_VCC")],
                     notes="GND is the middle pin. The end pin that reads 5 V is SW-VCC: leave it empty."),
    "PIBOT_ZL": dict(type="PiBot V4.96 Pro", subtype="Z limit input io35 (3-pin JST-XH)",
                     pins=[("SIG", "U1.Z_LIM/gpio35"), ("GND", "U1.LIM_GND"), ("5V", "U1.SW_VCC")],
                     notes="GND is the middle pin. The end pin that reads 5 V is SW-VCC: leave it empty."),
    "SW_X": dict(type="Endstop switch", subtype="X index: fires at nail 0",
                 pins=[("COM", "SW1.COM"), ("NC", "SW1.NC"), ("NO", "SW1.NO")],
                 notes="Tabs are marked C, NC, NO. Leave NO empty."),
    "SW_Y": dict(type="Endstop switch", subtype="Y home: tip outside the ring",
                 pins=[("COM", "SW2.COM"), ("NC", "SW2.NC"), ("NO", "SW2.NO")],
                 notes="Tabs are marked C, NC, NO. Leave NO empty."),
    "SW_Z": dict(type="Endstop switch", subtype="Z home: drill fully up",
                 pins=[("COM", "SW3.COM"), ("NC", "SW3.NC"), ("NO", "SW3.NO")],
                 notes="Tabs are marked C, NC, NO. Leave NO empty."),
    "PIBOT_RLY": dict(type="PiBot V4.96 Pro", subtype="on-board relay terminal (gpio26)",
                      pins=[("COM", "U1.RLY_COM"), ("NC", "U1.RLY_NC"), ("NO", "U1.RLY_NO")],
                      notes="RLY jumper on relay. Middle pin is NC: use the two outer pins."),
    "DRILL": dict(type="555 drill motor", subtype="24 V, solder tabs",
                  pins=[("+ (red dot)", "M4.+"), ("-", "M4.-")]),
    "D1": dict(type="1N5822 diode", subtype="flyback, solder across the drill tabs",
               pins=[("K (stripe)", "D1.K"), ("A", "D1.A")],
               notes="Stripe end to the drill + tab. Backwards = dead short when the relay closes."),
}

# ---------------------------------------------------------------------------------------------
# Steps: each wire is (from connector, pin label, colour, to connector, pin label).
# Wires in a step that share a cable name are drawn as one cable.
# ---------------------------------------------------------------------------------------------
STEPS = [
    dict(name="01_power", title="Step 1: 24 V power distribution", gauge=POWER, cables={
        "PSU leads": [("PSU", "+", "RD", "WAGO+", "+24V 1"), ("PSU", "-", "BK", "WAGO-", "GND 1")],
        "PiBot Vmot": [("WAGO+", "+24V 2", "RD", "PIBOT_PWR", "Vmot +"),
                       ("WAGO-", "GND 2", "BK", "PIBOT_PWR", "Vmot -")],
        "PiBot Vmot-Driver": [("WAGO+", "+24V 3", "RD", "PIBOT_PWR", "Vmot-Driver +"),
                              ("WAGO-", "GND 3", "BK", "PIBOT_PWR", "Vmot-Driver -")],
        "DM542T power": [("WAGO+", "+24V 4", "RD", "DM542T_HV", "+VDC"),
                         ("WAGO-", "GND 4", "BK", "DM542T_HV", "GND")],
    }),
    dict(name="02_platter", title="Step 2: platter motor (X) on the DM542T", gauge=SIGNAL, cables={
        "X step/dir": [("PIBOT_X", "STP", "YE", "DM542T_SIG", "PUL+"),
                       ("PIBOT_X", "DIR", "WH", "DM542T_SIG", "DIR+"),
                       ("PIBOT_X", "GND", "BK", "DM542T_SIG", "PUL-")],
        "NEMA23 leads (18 AWG)": [("NEMA23", "A+", "BK", "DM542T_HV", "A+"),
                         ("NEMA23", "A-", "GN", "DM542T_HV", "A-"),
                         ("NEMA23", "B+", "RD", "DM542T_HV", "B+"),
                         ("NEMA23", "B-", "BU", "DM542T_HV", "B-")],
    }),
    dict(name="03_arm_drill_motors", title="Step 3: threader (Y) and drill-feed (Z) motors",
         gauge=SIGNAL, cables={
        "Y motor cable": [("PIBOT_YM", p, c, "NEMA17_Y", m)
                          for p, m, c in zip(["1A", "1B", "2A", "2B"], ["A+", "A-", "B+", "B-"],
                                             ["BK", "BU", "GN", "RD"])],
        "Z motor cable": [("PIBOT_ZM", p, c, "NEMA17_Z", m)
                          for p, m, c in zip(["1A", "1B", "2A", "2B"], ["A+", "A-", "B+", "B-"],
                                             ["BK", "BU", "GN", "RD"])],
    }),
    dict(name="04_endstops", title="Step 4: endstops (wired normally-closed)", gauge=SIGNAL,
         cables={
        f"{a} endstop": [(f"PIBOT_{a}L", "SIG", "WH", f"SW_{a}", "NC"),
                         (f"PIBOT_{a}L", "GND", "BK", f"SW_{a}", "COM")]
        for a in "XYZ"
    }),
    dict(name="05_drill_relay", title="Step 5: drill on the on-board relay", gauge=SIGNAL, cables={
        "Drill 24 V (18 AWG)": [("WAGO+", "+24V 5", "RD", "PIBOT_RLY", "COM"),
                                ("PIBOT_RLY", "NO", "RD", "DRILL", "+ (red dot)"),
                                ("WAGO-", "GND 5", "BK", "DRILL", "-")],
        "Diode legs": [("DRILL", "+ (red dot)", "SR", "D1", "K (stripe)"),
                       ("DRILL", "-", "SR", "D1", "A")],
    }),
]


def netmap():
    _, nets = make_schematic.schematic()
    return {member: net for net, members in nets.items() for member in members}


def net_of(nm, conn, label):
    kicad = dict(CONNECTORS[conn]["pins"])[label]
    if kicad.startswith("="):
        return kicad[1:]
    return nm.get(kicad)


def check(nm):
    errors = []
    for step in STEPS:
        for cable, wires in step["cables"].items():
            for a, pa, _, b, pb in wires:
                na, nb = net_of(nm, a, pa), net_of(nm, b, pb)
                if na is None or na != nb:
                    errors.append(f"{step['name']} {cable}: {a}.{pa} ({na}) -> {b}.{pb} ({nb})")
    for name, c in CONNECTORS.items():
        for x, y in c.get("loops", []):
            na, nb = (net_of(nm, name, c["pins"][i - 1][0]) for i in (x, y))
            if na is None or na != nb:
                errors.append(f"loop {name} {x}-{y}: {na} != {nb}")
    if errors:
        sys.exit("Harness disagrees with the schematic:\n  " + "\n  ".join(errors))


def step_yaml(step):
    used = []
    for wires in step["cables"].values():
        for a, _, _, b, _ in wires:
            used += [c for c in (a, b) if c not in used]
    connectors = {}
    for name in used:
        c = CONNECTORS[name]
        d = dict(type=c["type"], subtype=c["subtype"],
                 pinlabels=[p[0] for p in c["pins"]],
                 hide_disconnected_pins=True, show_name=False)
        if "colors" in c:
            d["pincolors"] = c["colors"]
        if "loops" in c:
            d["loops"] = c["loops"]
        if "notes" in c:
            d["notes"] = c["notes"]
        connectors[name] = d

    cables, connections = {}, []
    for cable, wires in step["cables"].items():
        gauge = POWER if "18 AWG" in cable else step["gauge"]
        cables[cable] = dict(category="bundle", gauge=gauge, show_equiv=False,
                             colors=[w[2] for w in wires])
        for i, (a, pa, _, b, pb) in enumerate(wires, 1):
            connections.append([{a: [pa]}, {cable: [i]}, {b: [pb]}])

    return dict(metadata=dict(title=step["title"]),
                options=dict(fontname="DejaVu Sans", bgcolor="WH", color_mode="full"),
                connectors=connectors, cables=cables, connections=connections)


def guide_data(nm):
    """Wires per step, in build order, for the illustrated guide page."""
    def end(conn, pin):
        c = CONNECTORS[conn]
        return dict(id=conn, type=c["type"], subtype=c["subtype"], pin=pin)

    steps = []
    for step in STEPS:
        wires = []
        for cable, ws in step["cables"].items():
            gauge = POWER if "18 AWG" in cable else step["gauge"]
            for a, pa, color, b, pb in ws:
                wires.append(dict(cable=cable, color=color, gauge=gauge, net=net_of(nm, a, pa),
                                  **{"from": end(a, pa), "to": end(b, pb)}))
        used = {w[k]["id"] for w in wires for k in ("from", "to")}
        for name in sorted(used):
            for x, y in CONNECTORS[name].get("loops", []):
                pa, pb = (CONNECTORS[name]["pins"][i - 1][0] for i in (x, y))
                wires.append(dict(cable="Jumper", color="RD", gauge=step["gauge"],
                                  net=net_of(nm, name, pa),
                                  **{"from": end(name, pa), "to": end(name, pb)}))
        steps.append(dict(name=step["name"], title=step["title"], wires=wires))
    return steps


def write_guide(nm):
    src = (HERE / "guide.src.html").read_text()
    marker = "/*@STEPS@*/null"
    assert marker in src
    data = json.dumps(guide_data(nm), separators=(",", ":"))
    (HERE / "guide.html").write_text(src.replace(marker, data))
    print("guide.html: ok")


def main():
    nm = netmap()
    check(nm)
    write_guide(nm)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    wireviz = shutil.which("wireviz") or str(Path(sys.executable).with_name("wireviz"))
    for step in STEPS:
        path = OUT / f"{step['name']}.yml"
        path.write_text(f"# Generated by make_harness.py: {step['title']}\n"
                        + yaml.safe_dump(step_yaml(step), sort_keys=False, allow_unicode=True))
        subprocess.run([wireviz, "-f", "hps", str(path)], check=True)
        print(f"{path.name}: ok")


if __name__ == "__main__":
    main()
