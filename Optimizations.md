# Klipper Configuration Optimization Roadmap
**Target Printer**: XYZprinting Da Vinci 1.0A  
**Hardware Profile**: Arduino Due / Atmel SAM3X8E, E3D Bowden Conversion, Winstar 1604A LCD (8-bit parallel), BLTouch Probe, Fluidd / Moonraker.  
**Base Status**: Printer is functional and producing successful prints.

This document tracks identified areas for improvement, ranging from thermal stability and workflow speed to configuration hygiene and modern Klipper feature integrations. As tasks are addressed, their statuses and implementation notes will be updated.

---

## 0. Completed Baseline & Safety Fixes

- [x] **0.1 Open-Circuit Thermistor Protection**
  - **Status**: Completed
  - **Details**: Changed `min_temp` from `-50` (extruder) and `-100` (bed) to `0` in `klipper/printer.cfg`. Protects against runaway heating in the event of broken thermistor wiring.
- [x] **0.2 Bed Thermal Runaway Detection**
  - **Status**: Completed
  - **Details**: Reduced `check_gain_time` on `[verify_heater heater_bed]` from `5000` (~83 minutes) to `150` seconds.
- [x] **0.3 LCD 1604 Display Geometry**
  - **Status**: Completed
  - **Details**: Uncommented `line_length: 16` in `[display]` to ensure proper line wrapping and screen buffer alignment on the 16x4 character display.
- [x] **0.4 Nozzle Cleaning Macro & Legacy Alias**
  - **Status**: Completed
  - **Details**: Verified `[gcode_macro CLEAN_NOZZLE]` wiping coordinates and added `[gcode_macro M100]` alias in `klipper/macros.cfg` for compatibility with stock Da Vinci routines and slicer scripts.
- [x] **0.5 Disable Part Fan During Warm-up**
  - **Status**: Completed
  - **Details**: Commented out `M106 S255` in `START_PRINT` before heating, preventing cooling of the bed/nozzle during initial warm-up.

---

## 1. Print Quality & Hardware Tuning

### [x] 1.1 Bed Heater Control: Watermark Maintained (Hardware Constraint)
- **Status**: Completed / Reverted to Watermark
- **Findings**: Bed PID was calibrated at 80°C (`Kp: 60.510`, `Ki: 0.746`, `Kd: 1227.599`). However, testing showed the stock power supply / mainboard bed FET circuitry cannot handle high-frequency PWM current oscillations. 
- **Resolution**: Retained `control: watermark` (bang-bang) for electrical stability. PID values preserved as comments for reference.

### [x] 1.2 Back-Center Z-Homing with Cleaning Zone Routing & Mesh Zero Reference
- **Status**: Completed
- **Rationale**: Homing Z at back-right introduced X-tilt bias and off-axis cantilever torque. Homing at back-center (`Probe: 100, 175` -> `Nozzle: 140, 175`) places the probe directly over the central Z leadscrew and between the two vertical guide rods for maximum rigidity.
- **Safe Routing**: To prevent the carriage from clipping the rear-right cleaning zone / wiper chute, `[safe_z_home]` was replaced with `[homing_override]`. It drops Z by 10mm, homes X and Y to endstops, exits the cleaning chute into the safe print surface area at `(190, 200)`, steps to `(190, 175)`, slides horizontally across the rear print surface to `(140, 175)` for Z homing, and finally returns to the safe print spot at `(190, 200)`.
- **Mesh Synchronization**: Added `zero_reference_position: 100, 175` to `[bed_mesh]`, ensuring the bed mesh is mathematically normalized ($0.000\,\text{mm}$) against the exact spot where Z homing occurs.

### [x] 1.3 BLTouch Probing Speed & Lift Optimization
- **Status**: Testing / Applied (Revertable)
- **Rationale**: Previously, `speed: 1.5` and `lift_speed: 1` caused each sample retract to take 2.5 seconds, making mesh generation excessively slow.
- **Tuned Values**: Set `speed: 3.0` (downward probing) and `lift_speed: 4.0` (upward retract, within safe Z max limits). This cuts probe cycle time by over 60%. Original values preserved in comments if testing shows any pin timing issues.

---

## 2. Print Lifecycle Workflows (`START_PRINT` & `END_PRINT`)

### [x] 2.1 Adaptive Bed Meshing (Dynamic Per-Print Probing)
- **Status**: Completed
- **Rationale**: The Da Vinci bed surface and cantilever bracket are thermally/mechanically unstable across heat cycles, making stored mesh profiles inaccurate.
- **Implementation**: Enabled Klipper's native adaptive meshing by updating `START_PRINT` in `klipper/macros.cfg` to `BED_MESH_CALIBRATE ADAPTIVE=1`, configured `adaptive_margin: 5` in `[bed_mesh]`, and added `[exclude_object]` to `klipper/printer.cfg`. Klipper now probes only the specific bounding box of the model being printed on every job, drastically reducing probing time while ensuring fresh, accurate first-layer compensation.

### [x] 2.2 Purge / Priming Line Pathing
- **Status**: Completed
- **Implementation**: Updated `START_PRINT` in `klipper/macros.cfg` from the old single-line back-and-forth wipe (which plowed through wet plastic) to a clean two-line prime routine:
  1. Primes forward along $X=1.0$ from $Y=170$ to $Y=20$ ($15\,\text{mm}$ extruded).
  2. Steps laterally by $0.4\,\text{mm}$ to $X=1.4$.
  3. Primes rearwards along $X=1.4$ from $Y=20$ back to $Y=170$ ($15\,\text{mm}$ extruded).
  4. Retracts $0.5\,\text{mm}$ to prevent ooze, lifts $Z$ by $2\,\text{mm}$, and wipes off to $X=5$ before heading to the print area.

### [x] 2.3 Streamline `END_PRINT` Redundancies
- **Status**: Completed
- **Implementation**: Cleaned up `END_PRINT` in `klipper/macros.cfg`:
  1. Retracts $3\,\text{mm}$ to prevent ooze.
  2. Turns off all heaters (`TURN_OFF_HEATERS`) and part cooling fan (`M106 S0`).
  3. Lowers bed to $Z=195$ for easy print removal without colliding with the nozzle.
  4. Runs `CLEAN_NOZZLE` to clean the hot tip over the waste scraper.
  5. Returns to the safe print spot `(190, 200)` so the carriage never rests inside the narrow wiper chute.
  6. Disables steppers once (`M84`) and plays completion chimes. Removed duplicate `G28 X Y`, duplicate `M84`, and the blocking `M190 S55` cooling wait.

---

## 3. Configuration Hygiene & Macro Deduplication

### [x] 3.1 Unify Fluidd Client Macros (`_CLIENT_VARIABLE`)
- **Status**: Completed
- **Implementation**: 
  1. Removed duplicate `PAUSE`, `RESUME`, and `CANCEL_PRINT` macro blocks from `klipper/macros.cfg`.
  2. Removed redundant `[display_status]`, `[virtual_sdcard]`, and `[pause_resume]` sections from `klipper/printer.cfg` (already provided by `fluidd.cfg`).
  3. Configured Fluidd's official `[gcode_macro _CLIENT_VARIABLE]` in `klipper/printer.cfg` with safe park coordinates `(190, 200)` and custom lift/retraction values. Fluidd now manages pause/resume/cancel natively with toolhead parking, extruder temperature recovery, and layer pause support.

### [x] 3.2 Filament Dryer Loop MCU Flood Optimization
- **Status**: Completed
- **Implementation**: Changed `[delayed_gcode DRYER_TIMER]` interval from 1 second to 60 seconds. Updated status display to report time remaining in minutes (`M117 Drying: 240m`), cutting command chatter by 60x. Configured `SET_IDLE_TIMEOUT TIMEOUT={TIME + 1800}` to prevent heater shutdowns during drying, and restored the default 10-minute timeout upon stopping.

### [x] 3.3 Remove Obsolete `multiprobe_*` Macros
- **Status**: Completed
- **Implementation**: Removed legacy `multiprobe_ALL`, `multiprobe_1`, `multiprobe_2`, `multiprobe_3`, and `multiprobe_4` macros (which were for the stock conductive contact pads and had out-of-bounds `Y-5` moves). Replaced with a simple `[gcode_macro SCREWS_TILT]` that calls `SCREWS_TILT_CALCULATE` using the BLTouch.

### [x] 3.4 Remove Obsolete `Bed_Tilt_Calibration` Macro
- **Status**: Completed
- **Implementation**: Removed `Bed_Tilt_Calibration` (which called the inactive `BED_TILT_CALIBRATE` command) and removed commented-out legacy `BedScrewsCalculate`.

---

## 4. Modern Features & Quality of Life Enhancements

### [x] 4.1 Enable `[exclude_object]` (Cancel Individual Failed Parts)
- **Status**: Completed
- **Implementation**: Added `[exclude_object]` to `klipper/printer.cfg` and `enable_object_processing: True` under `[file_manager]` in `klipper/moonraker.conf`. This enables Fluidd's interactive part canceler (canceling a single failed object on multi-part prints) and provides the object bounding box data required for adaptive meshing.

### [x] 4.2 Case Lighting Control Macros
- **Status**: Completed
- **Rationale**: `Case_Light` is configured as a pin in `printer.cfg`. Adding G-code macros allows toggling the chamber LEDs directly from the Fluidd dashboard or during print events.
- **Implementation**: Added `LIGHTS_ON`, `LIGHTS_OFF`, `LIGHTS_TOGGLE`, and `M355` compatibility alias in `klipper/macros.cfg`. Fluidd can now toggle the chamber LEDs natively.

### [x] 4.3 Firmware Retraction (`[firmware_retraction]`)
- **Status**: Completed
- **Rationale**: Allows adjusting retraction distance and unretract speed on the fly via the Fluidd web UI during a print, which is especially useful for fine-tuning an E3D Bowden setup across different filament types without reslicing.
- **Implementation**: Added `[firmware_retraction]` to `klipper/printer.cfg` with initial Bowden values (`retract_length: 3.5`, `retract_speed: 40`, `unretract_extra_length: 0`, `unretract_speed: 35`). Fluidd automatically exposes interactive retraction tuning sliders.

---

## 5. Advanced Refinements & Workflow Polish

### [x] 5.1 Bed Mesh Height Fading (`fade_start` / `fade_end`)
- **Status**: Completed
- **Rationale**: `[bed_mesh]` previously had no `fade_end` configured (defaulted to `fade_end: 0.0`), applying mesh compensation across the full 200mm print height. This caused continuous Z motor oscillation throughout long prints and slanted/warped walls.
- **Implementation**: Added `fade_start: 1.0`, `fade_end: 10.0`, and `fade_target: 0` to `[bed_mesh]` in `klipper/printer.cfg`.

### [-] 5.2 Fix `END_PRINT` Air-Wiping & Safe Part Clearance
- **Status**: Skipped / Preserved by User Request
- **Details**: Maintained existing `END_PRINT` sequence without modification.

### [-] 5.3 `START_PRINT` Standby Nozzle Temp Probing & First Layer Squish Default
- **Status**: Skipped / Preserved by User Request
- **Details**: Maintained existing `START_PRINT` heating sequence and layer height defaults without modification.

### [x] 5.4 Slicer Compatibility: `M600` Filament Change Macro
- **Status**: Completed
- **Rationale**: Slicers (PrusaSlicer, OrcaSlicer, Cura) and Fluidd layer-pause events output `M600` for color changes and manual filament swaps.
- **Implementation**: Added `[gcode_macro M600]` in `klipper/macros.cfg` which forwards to `PAUSE`.

### [x] 5.5 Bowden Filament Loading / Unloading Macros (`LOAD_FILAMENT` / `UNLOAD_FILAMENT`)
- **Status**: Completed
- **Rationale**: The E3D Bowden conversion has a ~500mm PTFE feed path. Manually advancing filament from the extruder drive to the nozzle is tedious.
- **Implementation**: Added `LOAD_FILAMENT` (fast feed through Bowden tube, slow hotend purge) and `UNLOAD_FILAMENT` (tip-shaping retract, fast evacuation from tube) in `klipper/macros.cfg`.

### [x] 5.6 Configuration Cleanliness & Client Variable Sync
- **Status**: Completed
- **Implementation**: 
  1. Fixed trailing space in `[fan]` header in `klipper/printer.cfg`.
  2. Removed obsolete `# is not compatible with screws_tilt_adjust` comment.
  3. Cleaned up outdated LCD description comment.
  4. In `[gcode_macro _CLIENT_VARIABLE]`: set `variable_speed_hop: 5.0` (matching `max_z_velocity`) and enabled `variable_use_fw_retract: True`.

### [x] 5.7 Automated Motion Limits & Acceleration Tuning (`klipper_auto_speed`)
- **Status**: Completed / Calibrated
- **Rationale**: Determining the true physical speed and acceleration limits of the X and Y axes requires detecting step loss under extreme acceleration and speed. Doing this manually via iterative trial-and-error is time-consuming.
- **Implementation**:
  1. Installed the `klipper_auto_speed` module on the host Pi and installed `matplotlib` into `~/klippy-env` for graph generation.
  2. Linked `auto_speed.py` and `autospeed/` into Klipper's `klippy/extras/`.
  3. Added `[auto_speed]` in `klipper/printer.cfg` configured with `margin: 35` to strictly keep all high-speed moves within the safe print bed ($X \in [35, 190]$, $Y \in [35, 180]$) and away from the rear wiper chute ($X > 190, Y > 190$).
  4. Set binary search brackets (`accel_min: 500`, `accel_max: 4000`, `velocity_min: 50`, `velocity_max: 250`) tailored for 12V NEMA17 motors and A4988 drivers.
  5. Added `[update_manager klipper_auto_speed]` to `klipper/moonraker.conf` for Moonraker/Fluidd update tracking.
  6. **Upstream Bug Fixes Applied**:
     - *BLTouch virtual endstop compatibility*: Patched `handle_connect` in `autospeed/main.py` to extract rails directly from kinematics when Z uses `probe:z_virtual_endstop` (which bypassed `home_rails_end`).
     - *Chute Collision Prevention*: Centered opposing axis during 1D tests and added `_ensure_safe_clearance()` in `autospeed/main.py` to move Y forward to bed center ($Y=107.5$) before homing X and after homing Y, avoiding collision with the rear cleaning chute ($X>190, Y>190$).
     - *Steps-per-mm Metric Fix*: Corrected step difference calculation to divide by `1.0 / stepper.get_step_dist()` ($80.0\text{ steps/mm}$) instead of raw microsteps ($16$), ensuring mathematically exact millimeter readings.
- **Empirical Calibration Results**:
  - **Discovered Maximum Limits**:
    - **X Axis**: Max Accel: `3927 mm/s²`, Max Velocity: `245 mm/s`
    - **Y Axis**: Max Accel: `3927 mm/s²`, Max Velocity: `245 mm/s`
  - **Recommended Operational Limits** (20% safety margin / 0.8 derate):
    - **Acceleration**: `3142 mm/s²` (configured to `3000 mm/s²` in `[printer]`, a **3× increase** over the previous `1000 mm/s²` baseline)
    - **Velocity**: `196 mm/s` (configured to `195 mm/s` in `[printer]`)


