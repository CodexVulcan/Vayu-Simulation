"""
thermal_derating_sim.py

WHAT THIS COMPUTES
-------------------
How much continuous processing/dissipation the edge-compute enclosure
can sustain before hitting its rated thermal limit, comparing sea-level
natural convection to the reduced convection at ~4500m ASL. This is the
"processing derating" figure in Section 7.5, and is a WARM-case (not
cold-case) result -- see note below.

This is the paper's Section 7.5 (derating) result.

DERIVED vs ASSUMED
-------------------
DERIVED: steady-state internal temperature, max sustainable dissipation,
% derating required at altitude.

ASSUMED (see CONFIG):
  - Enclosure thermal resistance (aerogel case)
  - Chip/controller max rated temperature
  - Natural-convection heat-transfer coefficient scaling with air
    density^0.6 (laminar free-convection approximation)

NOTE
----
At -40C ambient, this power budget is nowhere near the thermal limit --
the enclosure is oversized relative to cold-case risk (see
COLD_CASE_NOTE in the output). The binding constraint is instead the
WARM case (+15C ambient) with reduced convection at altitude, which is
what the paper's 27.3%-style derating figure actually reports. Don't
conflate the two cases when writing this up.

RUN
---
    python3 thermal_derating_sim.py
"""

CONFIG = {
    "P_electronics_W": 18.0,
    "T_max_chip_C": 85.0,
    "T_ambient_cold_C": -40.0,
    "T_ambient_warm_C": 15.0,
    "R_th_aerogel_K_per_W": 4.2,
    "R_th_standard_K_per_W": 0.9,
    "rho_sea_level": 1.225,
    "rho_altitude": 0.72,
    "convection_density_exponent": 0.6,  # laminar natural-convection scaling
}


def run(cfg=CONFIG):
    # Cold-case reference (not the binding constraint -- see module docstring)
    T_internal_aerogel_cold = cfg["T_ambient_cold_C"] + cfg["P_electronics_W"] * cfg["R_th_aerogel_K_per_W"]
    T_internal_standard_cold = cfg["T_ambient_cold_C"] + cfg["P_electronics_W"] * cfg["R_th_standard_K_per_W"]
    P_max_aerogel_cold = (cfg["T_max_chip_C"] - cfg["T_ambient_cold_C"]) / cfg["R_th_aerogel_K_per_W"]
    P_max_standard_cold = (cfg["T_max_chip_C"] - cfg["T_ambient_cold_C"]) / cfg["R_th_standard_K_per_W"]

    # Warm-case, reduced-convection derating (the actual reported figure)
    conv_derate_factor = (cfg["rho_altitude"] / cfg["rho_sea_level"]) ** cfg["convection_density_exponent"]
    R_th_aerogel_altitude = cfg["R_th_aerogel_K_per_W"] / conv_derate_factor

    P_max_sea_equiv = (cfg["T_max_chip_C"] - cfg["T_ambient_warm_C"]) / cfg["R_th_aerogel_K_per_W"]
    P_max_altitude = (cfg["T_max_chip_C"] - cfg["T_ambient_warm_C"]) / R_th_aerogel_altitude
    derate_pct = (1 - P_max_altitude / P_max_sea_equiv) * 100

    return {
        "cold_case": {
            "T_internal_aerogel_C": T_internal_aerogel_cold,
            "T_internal_standard_C": T_internal_standard_cold,
            "P_max_aerogel_W": P_max_aerogel_cold,
            "P_max_standard_W": P_max_standard_cold,
            "note": "Cold ambient is NOT throughput-limiting at this power level with either "
                    "enclosure -- shown for reference only, not the reported derating figure.",
        },
        "warm_case_reported": {
            "convection_derate_factor": conv_derate_factor,
            "P_max_sea_level_equivalent_W": P_max_sea_equiv,
            "P_max_at_altitude_W": P_max_altitude,
            "derating_required_pct": derate_pct,
        },
        "config": cfg,
    }


if __name__ == "__main__":
    r = run()
    cc = r["cold_case"]
    wc = r["warm_case_reported"]
    print("Thermal / processing derating")
    print(f"  [cold-case reference, not the reported figure]")
    print(f"    Internal temp, aerogel  @ -40C ambient : {cc['T_internal_aerogel_C']:.1f} C")
    print(f"    Internal temp, standard @ -40C ambient : {cc['T_internal_standard_C']:.1f} C")
    print(f"  [warm-case -- the reported derating figure]")
    print(f"    Convection derate factor @ altitude     : {wc['convection_derate_factor']:.3f}")
    print(f"    Max dissipation, sea-level-equivalent   : {wc['P_max_sea_level_equivalent_W']:.1f} W")
    print(f"    Max dissipation, at altitude            : {wc['P_max_at_altitude_W']:.1f} W")
    print(f"    Processing/thermal derating required    : {wc['derating_required_pct']:.1f}%")
