# Fusion 360 Propeller Generator

A Python script for Autodesk Fusion 360 that generates a parametric, twisted propeller
(hub, blades and shaft bore) from a handful of dimensions. Made for small 3D-printed
propellers, for example thrusters on model boats and drones.

You choose the diameter, number of blades and pitch angle, and the script calculates the
pitch and twist, builds the blade and creates the whole propeller as a single body.

## What the script does

1. Creates a hub (cylinder) with a shaft bore.
2. Calculates the pitch `P` from the pitch angle at 0.7R:

   `P = 2π · 0.7R · tan(PHI_07)`

3. Calculates the blade angle at several radii. It is steepest at the root and flattest at the tip:

   `φ(r) = atan( P / (2π · r) )`

4. Draws a thin rectangular section (chord length x thickness) at each radius, rotated to `φ(r)`.
5. Lofts the sections into one twisted blade.
6. Creates the remaining blades with a circular pattern, joins everything to the hub and cuts the shaft bore.
7. Shows a rough estimate of theoretical speed, thrust and power at your chosen RPM.

## What is the "angle" of a propeller?

The pitch angle is measured between the blade's chord line and the plane of rotation (the plane
perpendicular to the shaft). It is not constant along the blade, so it is specified at 70 % of the
radius (0.7R). A larger angle gives more thrust per revolution, but demands more torque from the motor.

## Installation

1. Download or clone this repository.
2. Copy the folder to Fusion's scripts directory:
   - Windows: `%appdata%\Autodesk\Autodesk Fusion 360\API\Scripts`
   - macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts`

   Or in Fusion: **Utilities → Scripts and Add-Ins → Scripts → "+" → Add existing script from device**
   and select the folder.
3. Open a design in Fusion, press **Shift+S**, select the script and click **Run**.

The script cannot be run from a regular Python installation, because the `adsk` module only exists
inside Fusion's built-in Python.

## Parameters

All parameters are at the top of `Impeller.py` (mm and degrees):

| Parameter | Default | Description |
|---|---|---|
| `D` | 24.0 | Propeller diameter |
| `HUB_D` | 8.0 | Hub diameter |
| `BORE_D` | 5.1 | Shaft bore (shaft diameter plus a little clearance) |
| `HUB_L` | 10.0 | Hub length |
| `BLADES` | 3 | Number of blades |
| `PHI_07` | 25.0 | Pitch angle at 0.7R |
| `C_MAX` | 10.0 | Blade width (chord length) at mid-blade |
| `T` | 1.0 | Blade thickness |
| `HAND` | 1 | `1` or `-1` mirrors the propeller (right- or left-handed) |
| `N_SEC` | 6 | Number of sections in the loft |
| `ROOT_R` | 3.5 | Innermost section (sits inside the hub) |
| `RPM` | 1500 | Only used for the estimate at the end |

Change the values, save and run the script again. Undo with `Ctrl+Z` first if you want to
replace a propeller you have already created.

## Tips

- The propeller is built in the root component at the origin, with its axis along Z. Move it into place with Move/Copy.
- For two propellers that spin in opposite directions, make one with `HAND = 1` and one with `HAND = -1`.
- Print with the axis vertical. Resin gives a nicer result than FDM at this scale.
- Add a D-flat to the shaft or use a set screw, otherwise the propeller will slip.

## Limitations

- The blade is a thin, slightly twisted plate with no real airfoil profile and no camber.
  It suits small, low-speed propellers.
- The estimate uses typical thrust and torque coefficients (`K_T = 0.25`, `K_Q = 0.03`).
  These are rough figures, and measured performance can differ significantly.
- The script is made for blades arranged around the Z axis. Other setups may need adjustments.

## License

MIT, see `LICENSE`.
