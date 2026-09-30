# Machine design notes

Target: a Bart Dring style **rotating platter + radial thread arm**, controlled by an ESP32 running
FluidNC, fed G-code from `post.py`. This is the simplest proven DIY architecture, and almost every
later hobby build copies it. Full reference list is in `../docs/RESOURCES.md`.

Reference build to copy: https://github.com/bdring/StringArt (source, STEP files, parts list) and
the video https://www.youtube.com/watch?v=M1gXuKFspgY

## How it works

- The board (an MDF disc with nails around the rim) sits on a turntable driven by a stepper.
  This is the X axis, and it is configured in **nail units**: X=37 means nail 37 is under the arm.
- A radial arm carries the thread guide (a small tube or hook) and moves in and out across the nail
  ring. Extended (Y_OUT) the guide is outside the ring; retracted (Y_IN) it is inside.
- To wrap a nail the platter brings it to `pin + 0.5` with the tip resting inside the ring, the
  tip moves outside the ring, the platter turns back to `pin - 0.5` (sweeping the tip past the
  nail on the outside), and the tip comes back inside. The thread has now looped the nail from the
  outside. Full mechanics, dimensions and figures are in `PLATTER.md`.
- Nails are driven into holes drilled at **10° or more outward lean** so the thread slides down the
  nail on its own. No Z motion is needed while threading.
- The thread runs from a spool through a friction tensioner and an elevated redirect hook above
  the board, then to the arm guide. Slight over-rotation before reversing keeps tension at every nail.

## Changing the nail count

The generator takes `--nails N`. The JSON carries N. `post.py` reads N from the JSON. The only
machine-side change is `steps_per_mm` on X in the FluidNC config, which is really steps per nail:

    steps_per_nail = motor_steps_per_rev × microsteps × gear_ratio / N

New nail count means a new board (or new holes), a new drill program (`post.py --drill`), and
that one number. Nothing else.

## Bill of materials (starting point)

| Part | Suggestion | Why |
|---|---|---|
| Board | 12 mm MDF disc, 500–600 mm diameter | stiff, cheap, holds nails; 6 mm sags with 4000 tensioned lines |
| Turntable bearing | 300 mm+ lazy-susan bearing, or 3–4 ball casters under the rim | takes the board's weight off the motor |
| Platter drive | **On hand:** NEMA23 23HS45-4204S (4.2 A, ~3 N·m) on a DM542T, GT2 belt 4:1 to a printed ring on the platter | 3 N·m is far more than a 60 cm MDF disc needs; 4:1 at 16 microsteps gives 0.028°/step, 44.4 steps per nail at 288 nails. Direct drive is viable too. |
| Arm drive | **On hand:** NEMA17 on a short GT2 belt or T8 lead screw (a real Y axis, homes like one) | 30–40 mm stroke |
| Drill (optional) | **On hand:** second NEMA17 on a T8 lead-screw Z. **Ordered 2026-09-29:** Mingzhe 555 motor kit with mini drill chuck and mount, 12–36 V, $15.99, Amazon B0HJ72X4B5, arriving Oct 14–28. Runs straight from 24 V, no buck needed | light enough for the pancake NEMA17 Z; JT0 chuck grips 1.2–1.5 mm nail bits |
| Drill relay | **Ordered 2026-09-29:** HiLetgo 5 V 1-channel opto-isolated relay module, 2-pack, $7.39, Amazon B00LW15A4W, arriving overnight | set to low-level trigger for 3.3 V logic; coil from the 5 V LM2596, input from the PiBot spindle-enable/relay signal, drill's 24 V through the contacts |
| Controller | **Ordered 2026-09-29:** PiBot V4.96 Pro (classic ESP32, FluidNC, 6 StepStick sockets + 5 V external-driver headers, 12–24 V), $99 with OLED and antenna, Amazon B0HKNMK5CH, arriving Oct 5–7 | free motion planning, homing, WiFi G-code upload; DM542T on the X external header, TMC2209s in the Y and Z sockets |
| Drivers | DM542T (on hand) for the platter. **Ordered 2026-09-29:** BIGTREETECH TMC2209 V1.3 5-pack, $29.99, arriving overnight. Two used, three spare | DM542T DIP settings and TMC2209 Vref are in fluidnc-config.yaml |
| PSU | **Ordered 2026-09-29:** adjustable 3–24 V 6 A 144 W AC/DC brick with barrel tips and 4-way splitter, $26.99, arriving overnight. Set to 24 V | 144 W covers the DM542T's 4 A peak plus two 1 A NEMA17s. Needs a female barrel-jack-to-screw-terminal adapter to reach the board and DM542T; confirm the brick actually holds 24 V at 6 A under load, cheap adjustable bricks sometimes sag |
| Low-voltage rails | **On hand:** LM2596 buck modules. One set to 5 V for the relay coil, lights, or a servo. The 555 drill is 24 V rated, so no 12 V rail is needed | Realistically 2 A each without a heatsink. Set the trimpot with a meter before connecting a load; no reverse-polarity protection |
| Homing | **Ordered 2026-09-29:** R REIFENG 6-pack mechanical endstops with 1 m cables, $10.99, Amazon B07PCN6T6F, arriving Friday Oct 2; one per axis plus spares. Optional Hall sensor + magnet for the platter index | nail 0 must be repeatable to a fraction of a pitch; PiBot inputs take dry contacts, wire signal + ground only |
| PSU | 24 V, 5 A | headroom for the platter motor |
| Nails | 1.2–1.5 mm × 20 mm brads, or 2.54 mm pin-header strips in a routed groove | evenness matters more than nail type |
| Thread | black polyester sewing thread, Tex 30 / #30 / 402 (≈0.15–0.2 mm). Gütermann Sew-All works | 1 portrait ≈ 1–2 km; a 4000 m cone ≈ 2–3 portraits at 288 nails |
| Tensioner | sponge/felt pinch at the spool + spring-loaded redirect arm | droop and tangles are the number one failure |

## Purchase status (2026-09-29)

**On hand:** NEMA23 23HS45-4204S, DM542T, 2× NEMA17 17HE08-1004S, 5× LM2596 buck modules.

**Ordered, four Amazon orders totalling $206.78 with tax:** PiBot V4.96 Pro, TMC2209 5-pack, 24 V 6 A adjustable
PSU, HiLetgo relay 2-pack, 6-pack endstops, 555 drill kit.

**Still to buy:**
- Female barrel-jack-to-screw-terminal adapter (to get the PSU brick onto the board and the DM542T)
- GT2 belt, 20T pulley for the NEMA23 shaft (8 mm bore), and a printed 80T ring for the platter (4:1)
- Lazy-susan bearing, 12" or larger
- GT2 belt + 20T pulley (5 mm bore) for the arm, or a short T8 lead screw; T8 lead screw kit for the drill Z
- 22 AWG 4-conductor motor wire, JST-XH 2.54 crimp kit or pre-made leads, ferrules
- MicroSD card, 32 GB or smaller
- 1.2–1.5 mm drill bits (a few, they snap)
- Board: 12 mm MDF disc 500–600 mm; nails; black polyester sewing thread
- Optional: E-stop button, 40 mm 24 V fan for the driver sockets

## Numbers

| | |
|---|---|
| Pitch, 288 nails on 600 mm | 1.25°, 6.5 mm arc |
| NEMA17 at 1/16, direct | 0.1125°/step |
| with 6:1 | 0.019°/step, 66.7 steps per nail |
| Printed gear backlash | 0.2–0.5°, so always approach from the same direction or use a belt |
| Typical portrait | 3000–4000 lines, 1.5–2.2 km thread, 40–90 min machine time at 3 s per line |

## Lessons from other builds (worth reading before cutting anything)

- Nails popping out of MDF, thread droop from poor tension, uneven nail heights, no homing:
  https://github.com/ElvisTang717/String-Art-Machine (documented failures).
- 250+ nails with 3D-printed gears caused control difficulties; 200 was easy:
  https://fabacademy.org/2026/labs/lima/students/jennifer-wong/group-week12.html
- Pin-header strips as nails, door-roller turntable, sponge tensioner:
  https://www.instructables.com/Stringart-Machine/
- Servo rack-and-pinion arm, ESP32, reads a `pins.txt`: https://www.instructables.com/StringIT-Automated-String-Art-Machine/
- Limit-switch homing and a web GUI on the ESP32 itself:
  https://github.com/ChanchalSakardeQH/StringArt_Nema17_A4899_OLED_SG90

## Workflow

```
photo.jpg
  → generator/stringart.py photo.jpg --nails 288 --hoop-diameter 0.6
  → generator/out/photo.json (+ .png preview, .txt hand list)
  → machine/post.py generator/out/photo.json            → photo.gcode
  → machine/post.py generator/out/photo.json --drill    → photo_drill.gcode (once per board)
  → upload to FluidNC (WebUI), home, tie thread to nail 0, run
```
