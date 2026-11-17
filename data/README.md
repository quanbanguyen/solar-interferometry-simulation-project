# Data

| Folder | Origin | Format | Licence / attribution |
|---|---|---|---|
| `rstn/learmonth/D-M-YYYY.txt` | Radio Solar Telescope Network, Learmonth Solar Observatory (Australia), 1-s fixed-frequency flux | `HHMMSS F245 F410 F610 F1415 F2695 F4995 F8800 F15400` in SFU, `//////` = missing; the time is **UT** | US Government data distributed by NOAA NCEI; cite RSTN/NCEI |
| `rstn/learmonth/undated_solar_signal.txt` | same format, date unknown (thesis v0 input) | | as above |
| `rstn/csv/` | CSV conversions made by thesis v1 (`legacy/v1/sws_to_csv.py`); night rows are forward-filled there | CSV | derived |
| `antenna/nec/yagi_610_uframe.nec` | 610 MHz U-frame Yagi (4 reflectors, folded dipole, 6 directors), reconstructed from an HFSS design table and the physical antenna | NEC-2 card deck | author |
| `antenna/nec/yagi_two_ant_d*.nec` | two identical Yagis at 0.5, 5, 10, 15 m spacing (mutual-coupling study) | NEC-2 | author |
| `antenna/nec_out/*.out.txt` | 4NEC2 output of the two-antenna runs: full 3-D pattern at 1° steps, θ = −180…0° | NEC output | author |
| `antenna/beams/UFRAME_primary_beam_610MHz.npz` | single-Yagi pattern used by the pipeline: `theta_deg` (181, −180…0), `phi_deg` (361), `gain_dBi` (181×361), peak 9.48 dBi along the boom (+y) | npz | author |
| `antenna/beams/yagi_pattern_610MHz_v0.csv` | earlier pattern (θ 0…180, φ step 5°) | CSV (`theta_deg,phi_deg,gain_dBi`) | author |
| `field/hoa_lac_610MHz_daily_power/` | daily averaged received-power plots from the 610 MHz two-element instrument at Hoa Lac, 2025-03-20 … 2025-05-11 | PNG | author / project team |

## Beam file conventions

Beams are stored in the frame of the EM model. For the U-frame Yagi: x = element axis,
y = boom (main beam), z = completes the right-handed frame. 4NEC2 scanned θ from −180° to 0°,
which `TabulatedBeam` maps to the usual θ ∈ [0°, 180°] with φ + 180°. The `[antenna]` section of
a config (`boresight_axis`, `element_axis`, `pointing_*`, `element_az_deg`) places this frame on the sky.

Regenerate a beam from any NEC output: `interfsim beam data/antenna/nec_out/<file>.out.txt --npz out.npz`.
