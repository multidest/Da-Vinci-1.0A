# XYZ Da Vinci 1.0A - Advanced Mechanical & Slicer Tuning Guide

This guide details calibration procedures and configuration optimizations to address the physical and mechanical asymmetries between the **X** and **Y** axes on the XYZ Da Vinci 1.0A Cartesian 3D printer.

---

## 0. The Mechanical Asymmetry of the Da Vinci 1.0A

Before applying software adjustments, it is essential to understand the physical reality of this chassis:

| Attribute | X Axis | Y Axis | Impact |
| :--- | :--- | :--- | :--- |
| **Moving Mass** | Lightweight toolhead carriage + E3D V6 hotend + BLTouch (~250–300g) | Entire X gantry assembly: 2 steel rods, X motor, pulleys, carriage, wiring harness (~1,200–1,500g) | **Y carries ~4–5× more mass than X.** Y has significantly higher inertia and lower resonant frequency. |
| **Belts** | Single short GT2 belt (~500mm loop) | Dual long parallel belts (~1000mm each) driven by a cross-shaft | Long belts stretch more under acceleration and tension load. |
| **Chassis Geometry**| Toolhead rides perpendicular rods | Stamped sheet-metal side frames with press-fit rod bushings | Sheet-metal frames are rarely perfectly square ($90.00^\circ$); gantry skew is common. |
| **Endstops** | Optical flag switch on right carriage | Optical flag switch at rear gantry | Subject to electrical phase variation depending on stepper driver microstep cycle. |

---

## 1. Resonance & Vibration Compensation (`[input_shaper]`)

### Problem
Because Y carries ~4× more mass than X, its natural resonant frequency ($f_y$) is much lower than X ($f_x$):
* **X Resonant Frequency**: Typically $\sim 45\text{–}60\text{ Hz}$ (higher stiffness-to-mass ratio).
* **Y Resonant Frequency**: Typically $\sim 25\text{–}32\text{ Hz}$ (heavy gantry inertia).

At our calibrated $3000\text{ mm/s}^2$ acceleration, unshaped Y-direction moves will produce visible ringing (ghosting waves around vertical corners), whereas X-direction moves may remain relatively clean.

### Klipper Configuration
Add to `klipper/printer.cfg`:
```ini
[input_shaper]
shaper_freq_x: 0    # Frequency to be measured (Hz)
shaper_type_x: mzv  # Shaper algorithm: mzv, ei, 2hump_ei
shaper_freq_y: 0    # Frequency to be measured (Hz)
shaper_type_y: mzv  # Shaper algorithm: mzv, ei, 2hump_ei
```

### Tuning Procedures

#### Method A: Manual Ringing Tower (Calipers)
1. Slice a standard two-walled cube or ringing tower with:
   - Infill: 0%, Top layers: 0, Outer walls: 2
   - Speed: $80\text{–}100\text{ mm/s}$
   - Acceleration: $3000\text{ mm/s}^2$ (or run `SET_VELOCITY_LIMIT ACCEL=3000`)
2. Measure the ripple wavelength on the X-face ($L_x$ in mm) and Y-face ($L_y$ in mm) with calipers.
3. Calculate shaper frequency:
   $$f = \frac{V}{L}$$
   *(where $V$ is print speed in mm/s and $L$ is ripple distance between peaks in mm)*.
4. Input the calculated values into `[input_shaper]`.

#### Method B: Accelerometer (ADXL345 via Raspberry Pi GPIO)
1. Mount an ADXL345 sensor to the toolhead (for X) and bed/gantry (for Y).
2. Connect to the Pi's SPI pins and configure `[adxl345]` and `[resonance_tester]`.
3. Run:
   ```gcode
   TEST_RESONANCES AXIS=X
   TEST_RESONANCES AXIS=Y
   ```
4. Generate resonance graphs using `~/klipper/scripts/calibrate_shaper.py` to identify optimal shaper types and frequencies automatically.

---

## 2. Gantry Orthogonality & Skew Correction (`[skew_correction]`)

### Problem
The Da Vinci's stamped sheet-metal frame and dual-rod alignment often result in an angle between X and Y that deviates from $90.0^\circ$ (e.g., $89.5^\circ$ or $90.4^\circ$).
* **Symptom**: Printed square boxes become subtle parallelograms/rhombuses. Holes and circular pegs become slightly elliptical. Multi-part assemblies (lids, interlocking enclosures) do not fit together cleanly.

### Klipper Configuration
Add to `klipper/printer.cfg`:
```ini
[skew_correction]
```

### Tuning Procedure
1. Download and print a high-precision calibration print (e.g., **YACS - Yet Another Calibration Square** or a $100 \times 100\text{ mm}$ calibration test piece).
2. Using digital calipers, measure:
   - Length $A \rightarrow B$ ($X$ width): expected $100.0\text{ mm}$
   - Diagonal $A \rightarrow C$: diagonal across opposite corners
   - Diagonal $B \rightarrow D$: diagonal across other opposite corners
3. In the Klipper console, compute the skew factor:
   ```gcode
   SET_SKEW XY=AC,BD,AB
   SKEW_PROFILE SAVE=davinci_skew
   SAVE_CONFIG
   ```
4. Load the profile automatically on every print by adding this to `START_PRINT` in `klipper/macros.cfg`:
   ```gcode
   SKEW_PROFILE LOAD=davinci_skew
   ```
5. Clear skew at the end of the print by adding this to `END_PRINT`:
   ```gcode
   SET_SKEW CLEAR=1
   ```

---

## 3. Axis-Specific Scaling & Belt Stretch (`rotation_distance`)

### Problem
* The X axis uses a short, direct belt loop ($\sim 500\text{ mm}$).
* The Y axis uses dual long belts ($\sim 1000\text{ mm}$ each) spanning the entire chassis depth.
* Long belts experience greater elastic elongation under tension and carriage acceleration than short belts. A commanded $100.0\text{ mm}$ move may result in $100.02\text{ mm}$ on X but $99.82\text{ mm}$ on Y.

### Tuning Procedure
1. Print a large calibration cross ($150\text{ mm} \times 150\text{ mm}$) centered on the bed to minimize end-curl measurement error.
2. Measure the exact printed lengths of the X arm ($L_{\text{actual}, X}$) and Y arm ($L_{\text{actual}, Y}$) using calipers.
3. Compute the corrected `rotation_distance` for each axis independently:
   $$\text{New } \text{rotation\_distance} = \text{Current } \text{rotation\_distance} \times \frac{L_{\text{actual}}}{L_{\text{requested}}}$$
4. Update `[stepper_x]` and `[stepper_y]` in `klipper/printer.cfg` with their axis-specific values instead of sharing the nominal `40.0`.

---

## 4. Slicer Feature-Dependent Acceleration & Jerk (Cura)

### Problem
While Klipper's hardware motion limit is configured to `max_accel: 3000 mm/s²`, running $3000\text{ mm/s}^2$ on **outer visible perimeters** can transmit small surface artifacts, especially on the heavy Y axis. However, restricting the whole printer to low acceleration wastes significant print time during travel and infill.

### Recommended Cura Profile Settings

In Ultimaker Cura, enable **Acceleration Control** and **Jerk Control** in the print settings:

| Setting | Recommended Value | Rationale |
| :--- | :---: | :--- |
| **Print Acceleration** | `2000 mm/s²` | Solid balance of speed and structural stability |
| **Outer Wall Acceleration** | `1000–1200 mm/s²` | Produces glass-smooth outer surfaces with zero ghosting |
| **Inner Wall Acceleration** | `2000 mm/s²` | Faster perimeter tracing without visible defects |
| **Infill Acceleration** | `3000 mm/s²` | Maximum speed inside the part where ripples do not matter |
| **Travel Acceleration** | `3000 mm/s²` | Blazing-fast non-print transitions; minimizes oozing and stringing |
| **Print Jerk / SCV** | `5 mm/s` | Matches Klipper's `square_corner_velocity: 5.0` |
| **Travel Jerk** | `8–10 mm/s` | Snappy travel starts and stops |

---

## 5. Stepper Phase Homing Repeatability (`[endstop_phase]`)

### Problem
The Da Vinci 1.0A uses optical infrared beam-break endstops. While optical switches are immune to mechanical switch contact bounce, they have microscopic trigger variations depending on which electrical motor phase the stepper driver is energizing at the moment the beam is interrupted.

### Klipper Configuration
Add to `klipper/printer.cfg`:
```ini
[endstop_phase]
```

### Tuning Procedure
1. Home the printer (`G28`).
2. Run the endstop phase calibration helper macros already configured in `macros.cfg`:
   ```gcode
   update_x_phase
   update_y_phase
   ```
   *(Or run `ENDSTOP_PHASE_CALIBRATE stepper=stepper_x` and `ENDSTOP_PHASE_CALIBRATE stepper=stepper_y`)*.
3. Move the axis away and home several times to gather phase samples.
4. Save the calibrated phases with `SAVE_CONFIG`.
5. **Result**: Klipper will always home to the optical sensor and then automatically lock to the exact same full-step electrical cycle, yielding sub-micron homing repeatability.

---

## 6. Cornering Dynamics (`square_corner_velocity`)

### Problem
`square_corner_velocity` (SCV) controls the velocity at which the toolhead can traverse a $90^\circ$ direction change without decelerating to zero.
* **If SCV is too high ($> 8.0\text{ mm/s}$)**: The sudden momentum reversal of the heavy $1.3\text{ kg}$ Y gantry causes a mechanical thump or frame shudder.
* **If SCV is too low ($< 4.0\text{ mm/s}$)**: The nozzle dwells too long at corners, causing localized plastic bulges and rounded sharp corners.

### Recommendation
* On the Da Vinci 1.0A, keep `square_corner_velocity: 5.0` (default) in `[printer]`.
* If Input Shaping is calibrated and frame rigidity is solid, SCV can be incrementally tested up to **`7.0 mm/s`** for sharper corners and faster cycle times.

---

## 7. High-Speed Pressure Advance Calibration

### Problem
With acceleration raised from $1000\text{ mm/s}^2$ to $3000\text{ mm/s}^2$, the nozzle accelerates and decelerates into corners 3× faster. With a Bowden extruder setup (~500mm PTFE tube), extrusion pressure lag is magnified during fast deceleration.

### Tuning Procedure
1. Current baseline in `[extruder]` is `pressure_advance = 0.2`.
2. To fine-tune for your specific filament at $3000\text{ mm/s}^2$:
   ```gcode
   TUNING_TOWER COMMAND=SET_PRESSURE_ADVANCE PARAMETER=ADVANCE START=0.0 FACTOR=.005
   ```
3. Inspect the printed tuning tower corners to find where corner seams and blobbing disappear without causing line starvation.
