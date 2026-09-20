"""
radar_range_sim.py

WHAT THIS COMPUTES
-------------------
Detection range via a simplified monostatic radar range equation, for
a baseline (28 dBi) vs upgraded (31 dBi) antenna/front-end gain.

This is the paper's Section 7.5 (range) result.

DERIVATION APPROACH
--------------------
The receiver noise floor (Pmin) is not guessed: it is SOLVED so that
the baseline configuration reproduces the BSF QR 2019 "high RF-noise /
urban" figure of 3 km. Pmin is then held fixed while only the antenna
gain is changed for the upgraded case. This anchors the model to a
real published spec instead of an arbitrary sensitivity assumption.

ASSUMED (see CONFIG):
  - Transmit power, frequency, target RCS (typical small-drone order
    of magnitude), antenna gains baseline vs upgraded.

RUN
---
    python3 radar_range_sim.py
"""
import numpy as np

CONFIG = {
    "c_mps": 3e8,
    "freq_GHz": 10.0,          # X-band
    "Pt_W": 25.0,
    "G_baseline_dBi": 28.0,
    "G_upgraded_dBi": 31.0,
    "sigma_rcs_m2": 0.01,       # small-drone RCS, typical published order-of-magnitude
    "R_target_baseline_m": 3000.0,  # BSF QR 2019 "high RF-noise / urban" figure
}


def _radar_range(Pt, G, wavelength, sigma, Pmin):
    R4 = (Pt * G ** 2 * wavelength ** 2 * sigma) / ((4 * np.pi) ** 3 * Pmin)
    return R4 ** 0.25


def run(cfg=CONFIG):
    wavelength = cfg["c_mps"] / (cfg["freq_GHz"] * 1e9)
    G_base = 10 ** (cfg["G_baseline_dBi"] / 10)
    G_upg = 10 ** (cfg["G_upgraded_dBi"] / 10)

    Pmin = (cfg["Pt_W"] * G_base ** 2 * wavelength ** 2 * cfg["sigma_rcs_m2"]) \
        / ((4 * np.pi) ** 3 * cfg["R_target_baseline_m"] ** 4)

    R_base = _radar_range(cfg["Pt_W"], G_base, wavelength, cfg["sigma_rcs_m2"], Pmin)
    R_upg = _radar_range(cfg["Pt_W"], G_upg, wavelength, cfg["sigma_rcs_m2"], Pmin)

    return {
        "range_baseline_km": R_base / 1000,
        "range_upgraded_km": R_upg / 1000,
        "range_improvement_pct": (R_upg / R_base - 1) * 100,
        "solved_Pmin_W": Pmin,
        "config": cfg,
    }


if __name__ == "__main__":
    r = run()
    print("Detection range: baseline (28 dBi) vs upgraded (31 dBi) front end")
    print(f"  Baseline range : {r['range_baseline_km']:.2f} km (anchored to BSF QR 2019 urban-noise figure)")
    print(f"  Upgraded range : {r['range_upgraded_km']:.2f} km")
    print(f"  Improvement    : {r['range_improvement_pct']:.1f}%")
