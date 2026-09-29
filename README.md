# string-art

Photo → nail sequence → G-code for a circular string art portrait machine.

A circular frame with a few hundred evenly spaced nails; one continuous black thread wound
nail-to-nail in straight chords, chosen by software so the overlapping chords darken the image
and approximate a photograph.

```
string-art/
  docs/RESOURCES.md        every algorithm, repo, paper, video and machine build found (start here)
  generator/stringart.py   photo → nail sequence (JSON + TXT + PNG preview)
  generator/samples/       public-domain test portrait (Lincoln, Wikimedia Commons)
  generator/out/           outputs land here (git-ignored cache inside)
  machine/post.py          nail sequence JSON → FluidNC G-code (thread path and hole drilling)
  machine/fluidnc-config.yaml   controller config template for the rotating-platter machine
  machine/DESIGN.md        mechanism, BOM, numbers, lessons from other builds
```

## Setup

```
python3 -m venv .venv
.venv/bin/pip install -r generator/requirements.txt
```

## Generate a sequence

```
.venv/bin/python generator/stringart.py generator/samples/lincoln.jpg
.venv/bin/python generator/stringart.py photo.jpg --nails 256 --lines 3500 --line-weight 18 --hoop-diameter 0.6
```

Options (defaults are the well-known "288 nails / 4000 lines" reference set):

| flag | default | meaning |
|---|---|---|
| `--nails` | 288 | nails on the hoop. Any number; nail 0 is at 12 o'clock, numbered clockwise |
| `--lines` | 4000 | max chords |
| `--min-distance` | 20 | no chord between nails closer than this (in nail indices) |
| `--min-loop` | 20 | do not return to any of the last K nails |
| `--line-weight` | 15 | darkness (0–255) each chord removes; the main look-and-feel knob |
| `--size` | 500 | working image resolution |
| `--score` | sum | `sum` favours long chords through dark areas, `mean` favours contrast |
| `--gamma` | 1.0 | >1 darkens midtones before solving |
| `--hoop-diameter` | 0.625 | metres, only used for the thread-length estimate |

Outputs in `generator/out/`: `<name>.json` (machine input), `<name>.txt` (one nail per line for
winding by hand), `<name>.png` (preview). The 288-nail chord table takes ~8 s to build the first
time and is cached; solving 4000 lines takes ~2 s.

## Make G-code

```
.venv/bin/python machine/post.py generator/out/lincoln.json -o lincoln.gcode
.venv/bin/python machine/post.py generator/out/lincoln.json --drill -o lincoln_drill.gcode
```

The nail count is read from the JSON. On the controller side the only value tied to the nail
count is X `steps_per_mm` (steps per nail) in `machine/fluidnc-config.yaml`.

## Preview the sequence by hand

`<name>.txt` lists nails in order. Wind from nail 0: go to the next number, loop the nail from the
outside, continue.
