"""
radar_range_sim.py

WHAT THIS COMPUTES
-------------------
Detection range via a monostatic radar range equation for baseline (28 dBi)
vs upgraded (31 dBi) antenna/front-end gain.

DERIVATION & ANCHORING
----------------------
The receiver noise floor (Pmin) is back-solved so that the baseline
reproduces the BSF QR 2019 "high RF-noise / urban" figure of 3.0 km.
Pmin is held fixed while antenna gain is upgraded (+3 dBi).

LIMITATIONS & COMPLIANCE GAP
-----------------------------
1. Back-solving Pmin anchors the model to published specs to show relative
   scaling (+41.3% range), but cannot independently predict range from first principles.
2. The upgraded radar range (4.24 km) remains below the MHA 5.0 km rural requirement
   (0.76 km gap). While MHA's 5 km spec targets passive RF detection, the gap is declared.
"""
import numpy as np

CONFIG = {
    "c_mps": 3e8,
    "freq_GHz": 10.0,               # X-band
    "Pt_W": 25.0,
    "G_baseline_dBi": 28.0,
    "G_upgraded_dBi": 31.0,
    "sigma_rcs_m2": 0.01,           # small-drone RCS (0.01 m^2)
    "R_target_baseline_m": 3000.0,  # BSF QR 2019 urban baseline (3.0 km)
    "R_mha_spec_rural_m": 5000.0,   # MHA 2025 rural target spec (5.0 km)
}


def _radar_range(Pt, G, wavelength, sigma, Pmin):
    R4 = (Pt * (G ** 2) * (wavelength ** 2) * sigma) / (((4.0 * np.pi) ** 3) * Pmin)
    return R4 ** 0.25


def run(cfg=CONFIG):
    wavelength = cfg["c_mps"] / (cfg["freq_GHz"] * 1e9)
    G_base = 10.0 ** (cfg["G_baseline_dBi"] / 10.0)
    G_upg = 10.0 ** (cfg["G_upgraded_dBi"] / 10.0)

    # Back-solve noise floor Pmin at 3.0 km baseline anchor
    Pmin = (cfg["Pt_W"] * (G_base ** 2) * (wavelength ** 2) * cfg["sigma_rcs_m2"]) \
        / (((4.0 * np.pi) ** 3) * (cfg["R_target_baseline_m"] ** 4))

    R_base_m = _radar_range(cfg["Pt_W"], G_base, wavelength, cfg["sigma_rcs_m2"], Pmin)
    R_upg_m = _radar_range(cfg["Pt_W"], G_upg, wavelength, cfg["sigma_rcs_m2"], Pmin)

    R_base_km = R_base_m / 1000.0
    R_upg_km = R_upg_m / 1000.0
    R_spec_km = cfg["R_mha_spec_rural_m"] / 1000.0
    gap_km = R_spec_km - R_upg_km

    return {
        "range_baseline_km": R_base_km,
        "range_upgraded_km": R_upg_km,
        "range_improvement_pct": (R_upg_km / R_base_km - 1.0) * 100.0,
        "mha_spec_rural_km": R_spec_km,
        "mha_spec_gap_km": gap_km,
        "mha_spec_met": R_upg_km >= R_spec_km,
        "solved_Pmin_W": Pmin,
        "config": cfg,
    }


if __name__ == "__main__":
    r = run()
    print("Detection Range Analysis: Baseline (28 dBi) vs Upgraded (31 dBi) Front End")
    print(f"  Baseline Range : {r['range_baseline_km']:.2f} km (Anchored to BSF QR 2019 urban figure)")
    print(f"  Upgraded Range : {r['range_upgraded_km']:.2f} km (+{r['range_improvement_pct']:.1f}% relative gain)")
    print(f"  MHA Spec Gap   : {r['mha_spec_gap_km']:.2f} km gap vs {r['mha_spec_rural_km']:.1f} km MHA rural spec requirement")
    if not r['mha_spec_met']:
        print("  Status         : DECLARED GAP (Radar reaches 4.24 km vs 5.0 km spec requirement)")
