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
  - **Details**: Configured `[verify_heater heater_bed]` with `check_gain_time: 180`, `heating_gain: 1`, `max_error: 360`, and `hysteresis: 8`. Prevents premature heater fault shutdowns caused by watermark temperature swings, drafts, or cooling fan startup while maintaining reliable runaway safety.
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

### [x] 5.8 Macro Categorization & UI Button Organization
- **Status**: Completed
- **Rationale**: With dozens of macros defined for print control, maintenance, calibration, drying, lighting, and motion tuning, an unorganized macro list clutters the web dashboard.
- **Implementation**:
  1. Added dedicated `[gcode_macro]` wrappers in `klipper/macros.cfg` for all `klipper_auto_speed` calibration commands (`AUTO_SPEED_CALIBRATE`, `AUTO_SPEED_VALIDATE_SPEED`, `AUTO_SPEED_FIND_ACCEL`, `AUTO_SPEED_FIND_VELOCITY`, `X_ENDSTOP_ACCURACY_TEST`, `Y_ENDSTOP_ACCURACY_TEST`) with parameter passthrough (`{rawparams}`).
  2. Organized all macros in Fluidd's Moonraker database into 5 clean, color-coded functional categories:
     - **Tuning & Calibration**: Full Auto Speed calibration, 10x validation, accel/velocity search, endstop accuracy checks, bed screws tilt, and exercise routines.
     - **Maintenance & Tools**: Nozzle cleaning chute scrub, fast Bowden load/unload, and filament swap pause (`M600`).
     - **Filament Dryer**: Bed drop macro (`DRYER_DROP_BED` / `DROP_BED`) to load spools, preset drying cycles for PLA, PETG, ABS, custom temperature/time drying, status monitor, and emergency stop.
     - **Chamber & Hardware**: Case light toggle/on/off and beeper tone.
     - **Print Control**: Pause, resume, and cancel print.
  3. Set non-user-facing and internal macros (`start_print`, `end_print`, `m100`, `m355`, stepper phase updates) to hidden (`visible: false`) to keep the dashboard focused and clean.

### [x] 5.10 Front Panel Button Responsiveness Fix & Home Button Repurposing
- **Status**: Completed
- **Rationale**: The Da Vinci 1.0A front panel navigation buttons (Up, Down, Left, OK) were intermittently unresponsive or required multiple taps to register. Additionally, the physical Home button was mapped to `kill_pin`, causing accidental emergency shutdowns if pressed.
- **Root Cause**:
  1. **Missing Pull-up and Inversion (`^!`)**: The front panel buttons short to GND when pressed. Without pull-up and inversion configured in `[display]`, the SAM3X8E inputs floated/read HIGH (1 = unpressed). Klipper's `MCU_buttons` initialized assuming 0 = unpressed, causing it to read `0x3F` on boot and perceive every button as already held down.
  2. **Short-Click Timeout**: For `click_pin` (OK), Klipper's 800 ms short-click timer started immediately upon boot. Once expired, `is_short_click` became False; subsequent user presses were ignored unless rapidly double-tapped within the timer window. Navigation buttons also triggered on release rather than press.
  3. **Accidental Shutdowns**: `kill_pin` on `PA28` instantly halted the printer with `MCU 'mcu' shutdown: Shutdown due to kill button`.
- **Implementation**:
  1. **Pull-Up & Invert Pin Definitions (`klipper/printer.cfg`)**:
     - Configured `up_pin: ^!PC19`, `down_pin: ^!PC29`, `back_pin: ^!PA26`, and `click_pin: ^!PA27`.
     - Pins now idle at 0 (unpressed) and cleanly transition to 1 (pressed) when depressed.
  2. **Increased Long-Press Duration (`klippy/extras/display/menu_keys.py`)**:
     - Increased `LONG_PRESS_DURATION` from `0.800` s to `1.500` s so deliberate/firm presses do not prematurely trigger long-press actions.
  3. **Repurposed Home Button (`klipper/printer.cfg` & `klipper/macros.cfg`)**:
     - Removed `kill_pin: ^!PA28` from `[display]`.
     - Added `[gcode_button home_button]` listening on `pin: ^!PA28` with `press_gcode: HOME_BUTTON`.
     - Defined `[gcode_macro HOME_BUTTON]` to safely perform homing (`G28`) when idle, while ignoring with an informative alert during printing to protect active jobs.

### [x] 5.11 Custom Winstar 1604 Display Menus (`[display_menu.cfg]`)
- **Status**: Completed
- **Rationale**: The stock Klipper display menu lacks awareness of custom Da Vinci macros, filament cartridge EEPROM tracking, and on-board spool drying routines. By restructuring the display menu into a dedicated config file, all operations can be monitored and managed directly from the front panel without requiring a computer or web UI.
- **Implementation**:
  1. **Filament Menu Customization (`[menu __main __filament]`)**:
     - **Disabled raw extrusion commands** (`loadf`, `loads`, `unloadf`, `unloads`, `feed`) that bypass thermal and safety limits.
     - **Live Cartridge Stats**: Display live Material, Color, Remaining Length, Used Length, and recommended print temperatures read directly from `printer.xyz_cartridge`. Clicking stat lines re-polls the chip via `CARTRIDGE_READ`.
     - **Set Cartridge Submenu (`Set Cartridge >`)**: Allows setting both Material Type (`PLA`, `PETG`, `ABS`, `TPU`) and Remaining Length (5m to 400m in 10m steps) using interactive input dials, with a `Save to Chip` command that commits both values directly to the EEPROM with confirmation beeps (`SAVE_CARTRIDGE_SETUP`).
     - **Safe Operations**: Direct buttons for `LOAD_FILAMENT`, `UNLOAD_FILAMENT`, and `CLEAN_NOZZLE`.
  2. **Dedicated Drying Section (`Drying >`)**:
     - Grouped under the Filament menu: `Drop Bed` (`DRYER_DROP_BED`), `Dry PLA (50C)`, `Dry PETG (65C)`, `Dry ABS (70C)`, `Dryer Status`, and `Stop Dryer`.
  3. **Top-Level Macros Menu (`[menu __main __macros]`)**:
     - Placed at index 3 on the Main menu for quick access to hardware toggles and chores: Case Light toggle with dynamic state (`ON`/`OFF`), `Clean Nozzle`, and `Exercise Axes`.
  4. **Dedicated Bed Screws Tilt Menu (`[menu __main __screws_tilt]`)**:
     - Placed at index 4 on the Main menu for direct 1-click access.
     - **`Measure Tilt`**: Automatically homes axes only if unhomed, probes all 3 bed screws, and calculates level deviations.
     - **Live Adjustment Feedback**: Displays real-time screw status (`Rear R: Base`, `Rear L: CW 01:10` / `Level`, `Front: CCW 00:20` / `Level`), and overall bed condition (`Status: Level!` vs `Needs Adjusting`).
     - **Rapid Iteration**: Clicking any screw row or the status line immediately re-probes the bed after physical knob adjustment without needing menu re-navigation.

### [x] 5.12 Manual Extrusion Controls & Button Macro Anti-Queueing
- **Status**: Completed
- **Rationale**: Rapidly pressing menu or hardware buttons previously queued multiple executions of long-running macros (e.g. multiple 450 mm filament feeds). Additionally, fine manual filament control was needed on the screen for small purges or nozzle adjustments.
- **Implementation**:
  1. **Manual Extrusion Controls (`[display_menu.cfg]` & `[macros.cfg]`)**:
     - Added `[gcode_macro MANUAL_EXTRUDE]` with cold-extrusion safety protection checking `printer.extruder.can_extrude`.
     - Direct 1-click buttons in the Filament menu: `Extrude 10mm` (F200) and `Retract 10mm` (F300).
     - Interactive dial `Manual E: +/-10mm` (5 mm increments from -100 mm to +100 mm) to dial exact custom feed or retract amounts.
  2. **Single-Execution Button Anti-Queueing (`klippy/extras/display/menu.py` & `klippy/extras/gcode_button.py`)**:
     - Prevented `queue_gcode()` from stacking duplicate commands in `self.gcode_queue` when rapid button presses occur while a macro or command is actively executing.
     - Enforced a single-macro-at-a-time rule while prioritizing canceling/stopping commands (`CANCEL_PRINT`, `STOP_DRYER`, `PAUSE`, `M112`) so emergency actions always purge pending commands and take immediate effect.

### [x] 5.13 Direct On-Screen Print Controls (Pause, Resume, Cancel)
- **Status**: Completed
- **Rationale**: Stock Klipper displays an `OctoPrint` submenu during active prints with "Pause printing" and "Abort printing". However, in Fluidd/Moonraker setups, these send dummy serial action strings (`action:pause`, `action:cancel`) which are ignored by Moonraker and fail to execute. Furthermore, testing `gcode_mutex` during active `virtual_sdcard` execution erroneously dropped incoming display commands.
- **Implementation**:
  1. **Direct Main Menu Controls (`[display_menu.cfg]`)**:
     - Disabled the non-functional stock `[menu __main __octoprint]` menu.
     - Added prominent, direct top-level commands visible whenever a print is active:
       - `Pause Print` (index 1 when running) -> invokes real `PAUSE`.
       - `Resume Print` (index 1 when paused) -> invokes real `RESUME`.
       - `Cancel Print` (index 2) -> invokes real `CANCEL_PRINT`.
     - Mirrored these controls inside `[menu __main __tune]` for direct access alongside speed and baby-stepping tuning.
  2. **Active Print Action Dispatch Fix (`klippy/extras/display/menu.py` & `klippy/extras/gcode_button.py`)**:
     - Refined queue guard logic to only check active menu execution (`self.is_executing` and `self.gcode_queue`) rather than `gcode_mutex.test()`, allowing `virtual_sdcard` prints to yield and dispatch user pause/cancel commands smoothly.

### [x] 5.14 Legacy Display Menu Overrides & Enhancements
- **Status**: Completed
- **Rationale**: Clean up legacy defaults, fix pin naming mismatches, and add missing modern presets in Klipper's stock display menu.
- **Implementation**:
  1. **Fixed Case Light in `Control` Menu**: Mapped `[output_pin Case_Light]` to `Lights: ON / OFF` (fixing previous invisibility caused by case mismatch `caselight`) and disabled non-functional PWM slider.
  2. **Tactile Baby-Stepping (`Tune > Offset Z`)**: Increased step size from `0.005 mm` to `0.01 mm` so live first-layer adjustments are responsive with push buttons.
  3. **Temperature Preheats**: Added **Preheat PETG** (230°C / 70°C) and **Preheat Spool** (dynamic 1-click preheat to active cartridge temperatures).
  4. **Calibration Clean-Up**: Removed non-functional delta printer calibrations (`Delta cal. auto`, `Delta cal. man`) and added direct shortcuts for **`Calib Probe Z`** (`PROBE_CALIBRATE`) and **`Bed Mesh Calib`** (`BED_MESH_CALIBRATE`).
  5. **Modernized Virtual Storage Label**: Renamed legacy `SD Card` menu to `Print Files`.

### [x] 5.15 Preserving Stepper Energization & Coordinates During Print Pause
- **Status**: Completed
- **Rationale**: By default, Klipper's built-in `[idle_timeout]` runs `M84` after 10 minutes of inactivity. When a print was paused, this timeout would fire, de-energizing the X, Y, and Z stepper motors. Once steppers lost holding torque, printer axes could drift and Klipper marked the machine as unhomed, requiring a full rehome and effectively ruining the in-progress print.
- **Implementation**:
  1. **Conditional `[idle_timeout]` in `printer.cfg`**:
     - Configured a dedicated `[idle_timeout]` section that checks `{% if printer.pause_resume.is_paused %}`.
     - When paused, only the hotend heater is shut down (`M104 S0`) to prevent filament cooking and heat creep, while `M84` is intentionally omitted so all steppers remain energized and positional lock is 100% maintained.
     - When truly idle (not paused/printing), `TURN_OFF_HEATERS` and `M84` disable motors normally after 30 minutes.
  2. **Pause Timeout Window via `[gcode_macro _CLIENT_VARIABLE]`**:
     - Configured `variable_idle_timeout: 43200` (12 hours) so Fluidd automatically extends the idle timer window upon pausing.
  3. **Automatic Reheat on Resume**:
     - Fluidd's `RESUME` macro automatically checks `last_extruder_temp`, reheats the hotend with `M109`, unretracts, restores the baseline idle timeout, and returns to the exact layer coordinates without requiring any homing.

### [x] 5.16 Interactive Fluidd Modal & Visual Console Card for Filament Cartridge
- **Status**: Completed
- **Rationale**: The printer's UNI/O filament cartridge EEPROM tracks remaining length, material type, color, and preheat presets. Previously, interacting with the cartridge required CLI commands or manual G-code. A graphical, interactive interface inside Fluidd gives the user a dedicated management UI similar to bed screw leveling.
- **Implementation**:
  1. **Interactive Dialog Modal (`action:prompt`)**:
     - Implemented `CARTRIDGE_PANEL` (and `CARTRIDGE_STATUS`) using Klipper/Fluidd's `action:prompt` modal protocol.
     - Displays live status: material, color, remaining meters, percentage gauge, used meters (lifetime and this print), and target temperatures.
     - Provides one-click action buttons: `[Preheat Spool]`, `[Reset PLA (200m)]`, `[Reset ABS (200m)]`, `[Reset PETG (200m)]`, and `[Sync to Chip Now]`.
     - Handles unformatted and undetected states with interactive formatting buttons.
  2. **Visual Console Card**:
     - Running `CARTRIDGE_STATUS` prints a formatted box-drawing card with a dynamic ASCII fill bar (`[███████████████████░] 94.3%`) directly into Fluidd's console.
  3. **Dashboard Integration**:
     - Standardized macros under the `CARTRIDGE_` prefix for native grouping into dedicated Fluidd dashboard panels.










