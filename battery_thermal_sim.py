"""
battery_thermal_sim.py

WHAT THIS COMPUTES
-------------------
Net usable battery capacity at -40C ambient for:
  - Baseline: COTS Li-ion pack, unheated.
  - Upgrade:  LiFePO4 pack, heated to a thermostat floor via an embedded
              resistive heater, inside the aerogel double-wall enclosure.
              The heater's own parasitic energy draw is subtracted from
              the pack before comparing capacities, so the "improvement"
              number is a net figure, not a chemistry-only figure.

This is the paper's Table 4 / Section 7.2 result.

DERIVED vs ASSUMED
-------------------
DERIVED: heater continuous power draw (from enclosure R_th + ambient/floor
delta), heater energy over the mission, net usable capacity, % improvement.

ASSUMED (see CONFIG):
  - Li-ion / LiFePO4 capacity-vs-temperature curves (piecewise-linear,
    typical published COTS 18650 behaviour -- replace with a datasheet
    curve for the actual cell chosen before final submission)
  - Enclosure thermal resistance (aerogel vs standard case)
  - Pack size, mission duration, heater thermostat floor temperature

RUN
---
    python3 battery_thermal_sim.py
"""
import numpy as np

CONFIG = {
    "T_ambient_C": -40.0,
    "T_heater_floor_C": 0.0,        # heater cuts in below this core temp
    "R_th_aerogel_K_per_W": 4.2,    # aerogel double-wall enclosure (assumed)
    "R_th_standard_K_per_W": 0.9,   # standard IP65 single-wall case (assumed, for comparison)
    "pack_capacity_Wh": 220.0,
    "mission_hours": 6.0,           # BSF QR 2019 battery-backup requirement
    "liion_capacity_curve": {       # temp_C -> fraction of rated 25C capacity
        25: 1.00, 0: 0.85, -10: 0.70, -20: 0.55, -30: 0.40, -40: 0.25,
    },
    "lifepo4_capacity_curve": {
        25: 1.00, 0: 0.92, -10: 0.85, -20: 0.75, -30: 0.60, -40: 0.45,
    },
}


def _capacity_at(curve, T_c):
    pts = sorted(curve.items())
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return float(np.interp(T_c, xs, ys))


def run(cfg=CONFIG):
    cap_liion_unheated = _capacity_at(cfg["liion_capacity_curve"], cfg["T_ambient_C"])
    cap_lifepo4_at_floor = _capacity_at(cfg["lifepo4_capacity_curve"], cfg["T_heater_floor_C"])

    dT = cfg["T_heater_floor_C"] - cfg["T_ambient_C"]
    heater_W_aerogel = dT / cfg["R_th_aerogel_K_per_W"]
    heater_W_standard = dT / cfg["R_th_standard_K_per_W"]

    heater_Wh = heater_W_aerogel * cfg["mission_hours"]
    heater_frac_of_pack = heater_Wh / cfg["pack_capacity_Wh"]
    cap_lifepo4_net = cap_lifepo4_at_floor * (1 - heater_frac_of_pack)

    heater_Wh_standard = heater_W_standard * cfg["mission_hours"]
    heater_frac_standard = heater_Wh_standard / cfg["pack_capacity_Wh"]

    return {
        "cap_liion_unheated_pct": cap_liion_unheated * 100,
        "cap_lifepo4_at_floor_pct": cap_lifepo4_at_floor * 100,
        "heater_W_aerogel_case": heater_W_aerogel,
        "heater_Wh_over_mission": heater_Wh,
        "heater_pct_of_pack": heater_frac_of_pack * 100,
        "cap_lifepo4_net_pct": cap_lifepo4_net * 100,
        "relative_gain_pct": (cap_lifepo4_net / cap_liion_unheated - 1) * 100,
        "heater_pct_of_pack_standard_case": heater_frac_standard * 100,
        "config": cfg,
    }


if __name__ == "__main__":
    r = run()
    print("Battery capacity retention: Li-ion (unheated) vs LiFePO4+heater")
    print(f"  Li-ion @ -40C, unheated            : {r['cap_liion_unheated_pct']:.1f}% of rated capacity")
    print(f"  LiFePO4 cell held at heater floor   : {r['cap_lifepo4_at_floor_pct']:.1f}% of rated capacity")
    print(f"  Heater draw (aerogel case)          : {r['heater_W_aerogel_case']:.1f} W continuous")
    print(f"  Heater energy over mission           : {r['heater_Wh_over_mission']:.1f} Wh "
          f"({r['heater_pct_of_pack']:.1f}% of pack)")
    print(f"  LiFePO4 NET usable capacity          : {r['cap_lifepo4_net_pct']:.1f}% of rated capacity")
    print(f"  Relative gain vs unheated Li-ion     : {r['relative_gain_pct']:.1f}%")
    print(f"  (Reference) same heater, standard case: {r['heater_pct_of_pack_standard_case']:.1f}% of pack "
          f"-- shows why the enclosure upgrade is a precondition")
