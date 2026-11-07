; Platter (X) speed, ramp and repeatability test.
; Run it on fluidnc-bench.yaml (no homing needed) or on stringart.yaml after $H.
; Upload it to the board's flash or SD card and run it from the WebUI.
;
; Before you start:
;   - Stick a strip of tape on the platter rim and draw a fine line across it.
;   - Fix a pointer (a pin in a block, a ruler edge) on the base, touching that line.
;   - No thread on the machine, nothing on the platter that can slide off.
;   - Keep a hand near the E-stop or the brick's plug. Press ! (feed hold) in the WebUI to pause.
;
; Every move is relative (G91) and each section ends exactly where it started:
; 144 nails = 6400 steps, so the line must come back to the pointer after every section.
; 288 nails = 1 platter turn. F values are nails per minute; G0 runs at the config's max rate.
; During the 5 s pauses, check the line against the pointer. A drift of even a fraction of a
; mm means steps were lost: stop and lower max_rate or acceleration.
; Total run time is about 6 minutes.

G94 ; feed in units per minute
G91 ; relative moves

; ---- 1. Speed ladder: half a turn out and back at rising speeds.
; Listen and watch. It should get faster without new noise. Note the speed at which it starts
; to buzz, judder or sound rough (a resonance). If that happens below 1500, set max_rate below it.
G1 X144 F300
G1 X-144
G4 P2
G1 X144 F600
G1 X-144
G4 P2
G1 X144 F900
G1 X-144
G4 P2
G1 X144 F1200
G1 X-144
G4 P2
G1 X144 F1500
G1 X-144
G4 P5 ; check the line now

; ---- 2. Ramp: full speed (G0), quarter, half and full turns.
; Starts and stops should look soft: about 1 s to reach speed, no lurch, no belt slap,
; no rocking of the platter after it stops.
G0 X72
G0 X-72
G4 P1
G0 X144
G0 X-144
G4 P1
G0 X288
G0 X-288
G4 P5 ; check the line now

; ---- 3. Threading pattern: a jump, then the 1-nail sweep, like each wrap.
; The jumps here add up to zero (37+100-61-76 = 0) and every sweep is +1 then -1.
G0 X37
G0 X1
G0 X-1
G0 X100
G0 X1
G0 X-1
G0 X-61
G0 X1
G0 X-1
G0 X-76
G0 X1
G0 X-1
G4 P1
G0 X37
G0 X1
G0 X-1
G0 X100
G0 X1
G0 X-1
G0 X-61
G0 X1
G0 X-1
G0 X-76
G0 X1
G0 X-1
G4 P5 ; check the line now

; ---- 4. Repeatability: 10 half turns each way at full speed.
G0 X144
G0 X-144
G0 X144
G0 X-144
G0 X144
G0 X-144
G0 X144
G0 X-144
G0 X144
G0 X-144
G0 X144
G0 X-144
G0 X144
G0 X-144
G0 X144
G0 X-144
G0 X144
G0 X-144
G0 X144
G0 X-144
G4 P1 ; final check: the line should still sit on the pointer

G90 ; back to absolute moves
