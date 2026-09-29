# String art resources

Research recovered on 2026-09-29. Every URL here was fetched and verified live on that date unless the text says otherwise.

## Part 1 — The algorithm (image → nail sequence)

**Origin:** Petros Vrellis, "A New Way to Knit" (2016). 28" aluminium bicycle rim, 200 pegs,
one continuous thread, 3,000–4,000 chords, 1–2 km of thread, written in openFrameworks and
never released. https://artof01.com/vrellis/works/knit.html (live). Everything open-source
descends from reverse-engineering his description.

**Canonical greedy loop** (what nearly every repo below implements):
1. Grayscale → crop square → resize (300–800 px) → circular mask → invert (dark = high).
2. Place N nails evenly on the circle (N = 200–300; the Reddit/halfmonty lineage uses 288).
3. Precompute pixel list for every chord, N(N−1)/2 pairs (~41k for N=288). Linspace sampling or
   Bresenham; Xiaolin Wu anti-aliasing gives fractional coverage weights (Birsak, kaspar98).
4. Keep a residual image. From the current nail, score every candidate chord by summed residual
   darkness along it; pick the max.
5. Subtract a constant `LINE_WEIGHT` (≈15–20 of 255, or opacity 0.1–0.2) along the chosen chord,
   clamp at 0, append nail to output, repeat for MAX_LINES (3,000–4,000).

**Standard refinements:**
- `MIN_DISTANCE` (~20 nails): forbid chords between near neighbours (they hug the rim).
- `MIN_LOOP` / last-k-nails deque (~20): forbid revisiting recent nails (kills ping-pong).
  Some also forbid reusing an exact nail pair.
- Line weight/opacity is the main tuning knob. Contrast/gamma preprocessing helps.
- Supersample or block-upscale the working image so a pixel has range beyond binary
  (possibly-wrong: 16×16 blocks; Birsak: render at 4096² then box-filter down 8× to 512²).
- Stop when the best improvement ≤ 0 instead of a fixed line count.
- Random candidate subset for speed; CUDA/FPGA parallel scoring exists (221× speedup).
- Multi-colour: run the greedy per thread colour against per-channel residuals.

**Reference parameter set used by the whole halfmonty/kmmeerts lineage:**
288 nails, 4000 lines, min distance 20, no-revisit window 20, line weight ~15–20/255,
500–800 px working image, circular mask, ~0.625 m hoop.

**Beyond greedy (papers):**
- **Birsak, Rist, Wonka, Musialski, "String Art: Towards Computational Fabrication of String
  Images", Eurographics/CGF 2018.** DOI 10.1111/cgf.13359. Preprint (live):
  https://www.cg.tuwien.ac.at/research/publications/2018/Birsak2018-SA/Birsak2018-SA-preprint.pdf
  Binary non-linear least squares; 256 pins, 630 mm frame, 0.15 mm thread; 4 edge types per
  pin pair (left/right winding on each pin → 130,560 edges); greedy add, then iteratively
  remove edges that reduce error, alternate until stuck; then make the graph Eulerian and run
  Hierholzer to get ONE continuous path; fabricated by a KUKA robot (~5000 windings, 2500 m,
  ~2 h). Official code: https://github.com/birsakm/StringArt (MATLAB, no license).
  The left/right-winding + Eulerian-path machinery is exactly what matters for a robot.
- Fang, Liu, Shamir, "Automatic thread painting generation", arXiv 1802.04706 (weighted least
  squares over chord space + error-diffusion sampling; 300 pins).
- Demoussel et al., "A Greedy Algorithm for Generative String Art", Bridges 2022:
  https://archive.bridgesmathart.org/2022/bridges2022-63.pdf
- Radon-transform approach: https://community.wolfram.com/groups/-/m/t/3478004
- US patent 12,423,349 "Methods and systems for generating a string image" covers the
  line-weight/error-array greedy (note only; hobby use is not a concern).

**Best short explanations of the math:**
- https://possiblywrong.wordpress.com/2022/01/22/string-art/ (why per-pixel range matters)
- https://contentnation.net/en/grumpydevelop/stringart (C++ engineering notes)
- https://hackaday.com/2021/03/18/an-algorithm-for-art-thread-portraits/ ("300 nails is the sweet spot")
- https://hackaday.io/project/130951-diy-knit-portrait (Raphael Schaaf reverse-engineering Vrellis)
- https://michael-crum.com/string_art_generator/ (generalised frames, colour)
- https://nanxili.github.io/15418-threadart/ (CUDA parallel greedy)

## Part 2 — Open-source implementations (Python, C, others)

All verified live via GitHub on 2026-09-29 unless noted.

### Python (the "Python one" is almost certainly kmmeerts' gist or a descendant)
| Repo | Stars | License | Notes |
|---|---|---|---|
| kmmeerts gist `stringart.py` https://gist.github.com/kaspermeerts/781f0137b361b51224dcab722ae387b4 | — | — | The r/DIY 2019 original. N_PINS=288, MAX_LINES=4000, MIN_DISTANCE=20, MIN_LOOP=20, LINE_WEIGHT=15, HOOP 0.625 m. OpenCV+NumPy. Outputs PNG + **JSON pin sequence** + thread length. Ancestor of halfmonty. |
| theveloped/ThreadTone https://github.com/theveloped/ThreadTone | 484 | MIT | Greedy, 200 pins, **exports G-code** for a Cartesian plotter. Blog http://www.thevelop.nl/blog/2016-12-25/ThreadTone/ |
| danielvarga/string-art https://github.com/danielvarga/string-art | 136 | none | Sparse least squares + quantisation; the [Var17] baseline Birsak cites. Not a continuous-path generator. |
| kaspar98/StringArt https://github.com/kaspar98/StringArt | 90 | none | Greedy, circle or rectangle, `-s` strength 0.1, outputs ordered nail list. |
| hooyah/nailedit https://github.com/hooyah/nailedit | 39 | MIT | 2024. |
| grvlbit/stringart https://github.com/grvlbit/stringart | 29 | GPL-3 | Naive greedy, 300 px. |
| jennynotjen/threadPortraitAlgorithm https://github.com/jennynotjen/threadPortraitAlgorithm | 28 | none | Hackaday-featured. 298 nails on 80 cm; outputs `results.txt` sequence. |
| a-m-farahani/StringArt https://github.com/a-m-farahani/StringArt | 21 | none | Python port of the Birsak approach. |
| syllebra/string_art https://github.com/syllebra/string_art | 18 | MIT | Non-circular nail layouts. |
| GistNoesis/3d-printer-weaver https://github.com/GistNoesis/3d-printer-weaver | 16 | MIT | Makes a 3D printer wind string art. |
| Xunius/string_art | 15 | — | Hough-transform variant. |
PyPI: `stringart` 0.1.0 is a curve-stitching toy, NOT a portrait generator. `string-art` / `pystringart` don't exist.

### C / C++ (the "C one" is most likely one of these)
| Repo | Lang | Stars | License | Notes |
|---|---|---|---|---|
| abhishekaudupa/computational-string-art https://github.com/abhishekaudupa/computational-string-art | **pure C** | 7 | MIT | grayscale.c, canvas_maker.c, thread-generator.c, string-art.c; BMP in/out; has a YouTube series. Naive, WIP. |
| possibly-wrong/string-art https://github.com/possibly-wrong/string-art | C++ <200 lines | 33 | Unlicense | Greedy w/ 16×16 block upscaling, Bresenham, 256 pins, stops when improvement < 0, PGM in/out. **Best compact reference to port.** |
| gabrieleballetti/string-art https://github.com/gabrieleballetti/string-art | C++ | 18 | Unlicense | num_pins 256, opacity 0.2, skipped_neighbors 32, scale_factor 8; PGM. |
| MaloDrougard/knit https://github.com/MaloDrougard/knit | C++/Qt | 44 | GPL-3 | Qt port of Siegel's knitter. |
| grumpydevelop stringart https://git.contentnation.net/grumpydevelop/stringart | C++ | — | — | Multithreaded, ImageMagick, path-reuse penalty. |
| nanxili/15418-threadart https://github.com/nanxili/15418-threadart | C/CUDA | 3 | — | Birsak-style greedy, 221× GPU speedup. |
| SkookumAsFrig/StringArtOnFPGA | C++/Verilog | 4 | — | Cornell ECE 5760, DE1-SoC. |
| dwatman/string-art-cuda | C/CUDA | 0 | GPL-3 | Simulated annealing. |
| DanAla/String_Art https://github.com/DanAla/String_Art | C++ | 0 | MIT | Grayscale + CMYK; outputs nail sequence + SVG. |
Embedded (consume a precomputed sequence, don't generate on-device): omar-abdelgawad/string-art-machine
(C++ Arduino, MIT), Sacsitha/String-art-machine (Arduino C), ChanchalSakardeQH/StringArt_Nema17_A4899_OLED_SG90
(C, AGPL, web GUI + stepper + servo — name literally spells out the BOM).

### JavaScript / web
- **halfmonty/StringArtGenerator** https://github.com/halfmonty/StringArtGenerator — 587★, MIT. JS port of
  kmmeerts. The old GitHub Pages demo now redirects to a login-walled commercial service (Threaditate);
  run the repo locally.
- usedhondacivic/string-art-gen (Michael Crum) https://github.com/usedhondacivic/string-art-gen — 44★.
  Live: http://michael-crum.com/string-art-gen/ (any frame shape, multi-colour).
- piellardj/image-stylization-threading — 85★, GPL-3. Live: https://piellardj.github.io/image-stylization-threading/
- kitayoshi/string-knitting — 47★. Live: https://kitayoshi.github.io/string-knitting/
- dronperminov/StringArtGenerator — 46★ (Russian).

### Java / Processing (2016 originals)
- christiansiegel/knitter https://github.com/christiansiegel/knitter — Processing, 151★, MIT. CIRCLE/SQUARE/RECT;
  outputs `instruction.txt` pin order + `instruction.html` step viewer + thread length.
- MarginallyClever/weaving_algorithm https://github.com/MarginallyClever/weaving_algorithm — Processing, 186★, GPL-2.
  Dan Royer, 200 points, 2000 iterations.

### Rust
- spejamchr/string_art https://github.com/spejamchr/string_art — 14★, MIT. `--pin-count`, `--string-alpha`,
  multi-colour, `.json` sequence + GIF.
- `zing-art` crate: TUI that reads a nail-number CSV and shows the next nail in huge text (handy for hand-winding).
- Also rubcc95/string_art, ndbaker1/string-bean, loiccoyle/strandify, aaron404/gpu-string-art.

### Other web generators for validating output
- https://stringartgenerator.cc/ — free, 288 pins / 4000 lines defaults, TXT + SVG export.
- https://www.stringartgenerator.app/ — free, claims MIT, PDF nail sequences, CMYK.
- https://www.wowstrings.com/ — paid, exports nail coords + string endpoints for CNC.

### Not found
kylemcdonald string art; "Nick Casey"; "The Mathematics of String Art" blog; "stringart.app" as a domain;
Petros Vrellis's own app (his code was never released).

## Part 3 — Automated machine builds

### The build to copy: Bart Dring, "A New Spin on String Art Machines" (2019)
- Video: https://www.youtube.com/watch?v=M1gXuKFspgY ; source + STEP + parts: https://github.com/bdring/StringArt
- Hackaday: https://hackaday.com/2019/02/23/polar-platform-spins-out-intricate-string-art-portraits/
- **Mechanism:** rotating platter (X axis) + radial thread arm (Y axis) + drill on Z, treated as a
  3-axis CNC. 24" board, 256 nails. Nails set in **angled drilled holes** so the thread slides down
  by itself, so no Z motion is needed while threading. The machine drills its own nail holes.
- **Controller:** ESP32 running Grbl_ESP32 (now **FluidNC**), G-code streamed over WiFi.
- **Key trick:** the X axis is configured in units of *nail index* (0–255), not degrees, so small
  angular errors are tolerated. Wrap macro per nail, from `python/string_post.py`:
  ```
  G0 X{pin+0.5} Y28   ; approach one side of the nail, arm extended
  G0 Y0               ; retract arm past the nail
  G0 X{pin-0.5}       ; rotate half a pitch back, thread now behind the nail
  G0 Y28              ; extend again
  ```
  `drill.py` drills 256 holes with `G0 X{pin}` / `G1 Z-9` / `G0 Z10`.
- Path generator is MATLAB (slow); replace with our Python generator + the same post-processor.
- Nearly every later DIY rotating-platter build copies this design.

### Other rotating-platter builds (all verified)
- **StringIT!** (Instructables 2025): https://www.instructables.com/StringIT-Automated-String-Art-Machine/
  NEMA17 + DRV8825 base, MG996 servo rack-and-pinion radial feeder, second MG996 + lead screw drops a
  drill, ESP32, custom `StringArt.ino` reads `pins.txt`, 60 cm disc, STLs included. Based on Dring.
- **String Art Machine with Arduino Uno** (Instructables 2025): https://www.instructables.com/Stringart-Machine/
  3D-printed 20T:80T (4:1) gears, NEMA17, TMC2225, turntable on 4 door rollers + EVA foam, needle on
  2-servo XY slider. **320 pins made from 2.54 mm pin-header strips** set in a groove in 6 mm MDF
  (cheap and perfectly even). 402/602 black polyester thread; gravity clip + sponge friction tension.
- **ChanchalSakardeQH/StringArt_Nema17_A4899_OLED_SG90**: https://github.com/ChanchalSakardeQH/StringArt_Nema17_A4899_OLED_SG90
  ESP32, A4988 + NEMA17 disc, 2× SG90 (feeder, drill lift), limit-switch homing, OLED, web GUI
  served from the ESP32 with an in-browser generator. Wrap cycle: overshoot, swing out, sweep back, swing in, land.
- **Sacsitha/String-art-machine**: https://github.com/Sacsitha/String-art-machine — 300 nails, servo arm,
  WS2812B LED per nail, Hall-effect homing, ESP32/Mega.
- **ElvisTang717/String-Art-Machine**: https://github.com/ElvisTang717/String-Art-Machine — STM32 +
  TMC2208, CAD included. Documented failures worth reading: nails popping out of MDF, thread droop/tangle
  from poor tension, uneven nail heights, no homing. Drilled at 5°, recommends ≥10°.
- **Fab Academy Lima 2026**: https://fabacademy.org/2026/labs/lima/students/jennifer-wong/group-week12.html
  12 mm MDF on ball casters, 20:120 (6:1) printed gears, NEMA23 + DM556 at 24 V, ESP32. Finding:
  100–200 nails easy, **250+ nails caused control difficulties** with printed gears.
- **StringBoard UK** (commercial, home-built machine): lazy-susan turntable, stepper at 5:1, thread
  through a tensioner into a short flexible tube flicked between nails by a servo. https://stringboard.co.uk/

### Other mechanism families (for reference, not recommended)
- **Continuous-spin + solenoid flick** — shlonkin "Automate the Art" (2016): 26" bike rim spins
  continuously, 207 wire pins, a solenoid flicks the thread as the target pin passes, photointerrupter
  encoder, thread-out detector, Arduino + SD, ~3.5 h/piece. https://hackaday.io/project/13047-automate-the-art
  https://github.com/shlonkin/AutomatedArt
- **XY gantry with nail-placing head** — Paul MH (2023, RAMPS + modified GRBL, YOLO nail check, years of
  work, code not released) https://www.youtube.com/watch?v=LPYEd50j3s0 ; Kevin Dluzen (2020)
  https://hackaday.com/2020/12/11/cnc-router-frame-repurposed-for-colorful-string-art-bot/ ;
  Laarco Autograph (2016) https://hackaday.com/2016/04/28/autograph-a-string-art-printer/ .
  Only needed when nails are not on a circle. Much harder (thread collision, head must climb).
- **Industrial arm** — TU Wien (KUKA, 256 hooks, 63 cm), Marc Sallent, Univ. Novi Sad.
- **KAIST Spider Printer** — https://github.com/kabileva/Spider-Printer/ (laser-cut, Processing control).
- **Commercial NOVA-1** (China): https://www.stringartmachine.com/automatic-string-art-machine-nova/
  200/240/300 flat-foot nails in pre-drilled rings, 42–60 min/portrait. Useful for nail-count sanity.

### Not found
Stuff Made Here (no such video), Marginally Clever thread robot (pen plotter only), Michael Crum
machine (generator only), Thingiverse/Printables complete machines (none; useful parts: nail guide
thing:4564579, nail height tools thing:3697050, geared turntable thing:3170852).

### Hardware numbers
| Item | Guidance |
|---|---|
| Pitch | 300 nails on 60 cm = 1.2°, 6.3 mm arc |
| Resolution | NEMA17 @ 1/16 = 0.1125°/step direct; 4:1 → 0.028°; 6:1 → 0.019° |
| Real limit | Printed-gear backlash (0.2–0.5°). Always approach from the same direction, or use a GT2 belt around the platter rim. Dring's ±0.5-nail wrap tolerates this. |
| Motor | NEMA17 + 4–6:1 reduction is enough for ≤60 cm MDF. NEMA23 + DM556 for margin. |
| Servos | SG90 for tube flick; MG996 for rack-and-pinion arm |
| Bearing | Lazy-susan bearing, ball casters, or door rollers |
| Nails | Angled brads ≥10° in drilled holes, or 2.54 mm pin-header strips in a groove. Even spacing matters more than nail type. |
| Thread | Black polyester sewing thread, Tex 30 / #30 / 402 (≈0.15–0.2 mm). Gütermann Sew-All fits. 4000 m roll ≈ 6 portraits. |
| Tension | Friction block/sponge at spool + over-rotate then reverse at each nail. Elevated redirect hook keeps thread off the board. |
| Homing | Limit switch or Hall sensor on nail 0; G10 L20 zero in FluidNC |
| Frame | 6–12 mm MDF disc, 40–60 cm |
| Time | 40–90 min (commercial) to 2–5 h (DIY) per portrait |

### Firmware options
1. **FluidNC on ESP32 (recommended, Dring's route):** platter = X in nail-index units, arm = Y, drill = Z.
   Free acceleration planning, homing, WiFi streaming. Our job is only a Python post-processor
   (sequence → G-code). The `~/projects/esp32` folder suggests an ESP32 is on hand.
2. Custom Arduino/ESP32 sketch reading `pins.txt` (StringIT, Chanchal): simpler electronics, but you
   re-implement motion control.
3. Marlin/RAMPS: only if going the gantry route.
4. Klipper: no string-art build found; possible with a rotary axis + macros but unproven.

## Part 4 — Artists, videos, papers, community

### Petros Vrellis (the origin, 2016)
- Project page: https://artof01.com/vrellis/works/knit.html — 28" bicycle rim, 200 pegs, 3,000–4,000
  passes, 1–2 km thread, openFrameworks, "over 2 billion calculations". Code never released.
- Interview where he says he does not share/sell the algorithm: https://taylorholmes.com/?p=11796
  ("The algorithm spits out coordinates of nails, one after another".)
- Hackaday 2016 (first public reconstruction of his method; lists the first open clones):
  https://hackaday.com/2016/07/28/computer-designed-portraits-knit-by-hand/
- Booooooom interview: https://www.booooooom.com/2016/08/23/new-way-knit-with-experimental-artist-petros-vrellis/
- Vice: https://www.vice.com/en/article/code-knitting-algorithms-woven-portraits/
- Sells via Saatchi Art (https://www.saatchiart.com/vrellis), not Etsy.
- Demaine, Demaine & Vrellis, "String Art Font" (2017), discusses Eulerian paths: https://erikdemaine.org/fonts/stringart/

### Other practitioners with write-ups
- Ani & Andrew Abakumov (colour thread portraits, Mona Lisa / Girl with a Pearl Earring; ~8,000 lines,
  4+ km, 4–5 colours): https://www.engadget.com/2019-09-12-ani-abakumova-thread-algorithms.html
- Michael Crum (generalised frames, colour, and a machine): https://michael-crum.com/string_art_generator/
- Jenny Ma (298 nails, 80 cm): https://hackaday.com/2021/03/18/an-algorithm-for-art-thread-portraits/
- Tommy Clausner knit-portrait (Python+Rust, 201 hooks, 5,000 strings): https://github.com/TommyClausner/knit-portrait
- Raphael Schaaf DIY Knit Portrait: https://hackaday.io/project/130951-diy-knit-portrait
- Antoine Mauris Grasshopper tutorial (425 pins): https://scripting.molab.eu/tutorials/thread-art-generator/
- Christian Siegel "knitter" is the "Knit" project you probably remember (see Part 2).

### YouTube (titles verified via YouTube oEmbed)
Machine builds:
- "Building a String Art Machine" — Paul MH — https://www.youtube.com/watch?v=LPYEd50j3s0
  (Cartesian CNC that inserts nails and winds thread; Hackaday 2023 coverage
  https://hackaday.com/2023/09/27/string-art-build-uses-cnc-to-make-stringy-art/)
- "A New Spin on String Art Machines" — Barton Dring — https://www.youtube.com/watch?v=M1gXuKFspgY
  (24" round board on a rotary axis, Grbl_ESP32 — closest to what you want to build)
- "The making of a Thread Portrait with Robots - String Art" — Marc Sallent — https://www.youtube.com/watch?v=NFEXO5FEKDs
- "String art with a CNC Machine - full process (Rafael Nadal)" — Laarco Studio — https://www.youtube.com/watch?v=Uw1BIYtw-Lk
- "The Robot Thread Artist" — urdesign — https://www.youtube.com/watch?v=gGEtJ4ME3dM
- "String Art: Towards Computational Fabrication of String Images" — Peter Wonka Research — https://www.youtube.com/watch?v=wsO8Kso3zj4 (the Eurographics paper video, KUKA robot)
- "FPGA String Art" — Bruce Land (Cornell) — https://www.youtube.com/watch?v=MMGRWr4oZig
Algorithm explainers:
- "I Wrote an Algorithm to Draw Portraits from Thread | Thread Art" — Jenny Ma — https://www.youtube.com/watch?v=UsbBSttaJos
- "The Mathematics of String Art" — Virtually Passed — https://www.youtube.com/watch?v=WGccIFf6MF8
- "We Did Not Expect to Win Using THIS String Art Approach" — MARKitekta — https://www.youtube.com/watch?v=X4FUkcDMNI4
- "p5.js Coding Tutorial | String Art" — Patt Vira — https://www.youtube.com/watch?v=qH7ZgQghKUU
- "Programmer Makes Art With Thread" — Caters Clips — https://www.youtube.com/watch?v=hjkdmDHaiMA
NOT found: a "Stuff Made Here" string-art video; nothing from Coding Train, Sebastian Lague, Numberphile,
Matt Parker, or Code Bullet. Don't go looking for those.

### Hackaday / Instructables / Reddit
- Hackaday tag: https://hackaday.com/tag/string-art/
- Hackaday 2018 on the TU Wien robot: https://hackaday.com/2018/09/15/string-art-robot-is-an-autorouter-in-reverse/
- Instructables (bodies blocked to the crawler, titles verified):
  "StringIT! – Automated String Art Machine" https://www.instructables.com/StringIT-Automated-String-Art-Machine/
  "String Art Machine Completed With Arduino Uno" https://www.instructables.com/Stringart-Machine/
  "String Art Generator" (Python greedy walkthrough) https://www.instructables.com/String-Art-Generator/
- Reddit blocks the crawler; r/stringart exists. The original Python is from /u/kmmeerts on r/DIY (2019).

### Papers
- Birsak et al. 2018 (see Part 1). Project page: https://www.cg.tuwien.ac.at/research/publications/2018/Birsak2018-SA/
- Je, Abileva, Bianchi, Bazin (KAIST), "A computational approach for spider web-inspired fabrication of
  string art", CAVW 2019 — single continuous thread + custom machine: https://make.kaist.ac.kr/project/spiderweb-2019
  Code: https://github.com/makinteractlab/SpiderPrinter
- Demoussel et al., Bridges 2022: https://archive.bridgesmathart.org/2022/bridges2022-63.html
- Fang, Liu, Shamir, arXiv 1802.04706.
- KTH bachelor thesis "Computational String Art" (2024): http://www.diva-portal.org/smash/get/diva2:1880384/FULLTEXT01.pdf
- Univ. of Novi Sad robotic string art (Grasshopper + RobotStudio): https://www.arhns.uns.ac.rs/digital/?p=1726

### Commercial (useful as reference for nail counts / kit design)
- RingString kit: 46 cm, 240 pre-installed nails, monofilament, ~6 h by hand, €100: https://stringart.lv/products/ringstring-string-art-based-on-your-photo
- Stringer-S kits: 240–400 nails: https://stringer-s.com/
- StringAr (free generator, TXT pin sequence): https://stringar.com/
- Laarco "Autograph" machine (RPi + Arduino Mega, 2016): https://blog.arduino.cc/2016/05/06/autograph-is-a-machine-that-creates-art-using-nails-and-thread/
- No mass-market consumer string-art machine exists; every one found is a one-off.

