# Research Simulations — High-Altitude Anti-Drone System (PS 26050)

Every quantitative claim in the technical report's Section 7 (Simulated
Results) and Section 8 (Cost and Efficiency) traces to one of the scripts
in this folder. Nothing here is a field measurement — each script states
its own assumptions and is meant to be checked, challenged, and re-run,
not taken on faith.

## Layout

| File | Computes | Paper section |
|---|---|---|
| `pointing_control_sim.py` | DOB+UKF vs fixed-gain PID pointing error under gust disturbance | 7.1 |
| `battery_thermal_sim.py` | Net usable battery capacity, Li-ion vs LiFePO4+heater, at -40C | 7.2 |
| `bearing_lubrication_sim.py` | Cold-start bearing torque, grease vs dry ceramic-hybrid | 7.3 |
| `reliability_rbd_sim.py` | System MTTF via series RBD, baseline vs upgraded | 7.4 |
| `radar_range_sim.py` | Detection range, baseline vs upgraded antenna gain | 7.5 |
| `thermal_derating_sim.py` | Processing/thermal derating at altitude | 7.5 |
| `cost_lifecycle_sim.py` | BOM delta + 5-year lifecycle cost (imports MTTF from `reliability_rbd_sim.py`) | 8 |
| `run_all.py` | Runs everything above, writes `results/results.json` and `results/results.md` | — |

## How to run

```bash
pip install numpy --break-system-packages   # only external dependency
cd research_sims
python3 run_all.py
```

This regenerates `results/results.json` (machine-readable, every number
plus the config that produced it) and `results/results.md` (the exact
markdown tables copied into the report). Run any individual script
directly (e.g. `python3 pointing_control_sim.py`) for a quick printed
summary without touching the results files.

## Rule for changing an assumption

Every assumed constant lives in a `CONFIG` dict at the top of its file —
never buried inline. If you change one (a BOM price, a failure rate, a
viscosity constant), re-run `run_all.py` and diff the new
`results/results.md` against the version currently copied into the
report before updating the report text. Do not hand-edit a number in
the report without updating the script that's supposed to produce it —
that's the whole point of keeping these separate from the write-up.

## Known soft spots (be ready to defend these if asked)

- **Reliability model (`reliability_rbd_sim.py`)**: per-component failure
  rates and altitude multipliers are assumed, order-of-magnitude values,
  not vendor MTBF data or a MIL-HDBK-217F calculation. The 211% MTTF
  improvement is a defensible engineering argument, not a certified
  reliability figure — say so if asked.
- **Cost model (`cost_lifecycle_sim.py`)**: BOM line items are
  illustrative market-rate estimates, not vendor quotes.
- **Battery/bearing curves**: capacity-vs-temperature and
  viscosity-vs-temperature curves are typical/published-order-of-magnitude
  shapes, not the datasheet for a specific selected part. Swap in the
  real datasheet curve for the cell/grease actually specified once
  selected.
- **Detection range (`radar_range_sim.py`)**: the receiver noise floor
  is back-solved to match the BSF QR 2019 3 km figure rather than
  independently derived — this anchors the baseline to a real spec but
  means the model can't be used to *predict* range for a different
  radar without recalibrating that anchor.
