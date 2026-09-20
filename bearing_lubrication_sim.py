"""
bearing_lubrication_sim.py

WHAT THIS COMPUTES
-------------------
Startup (breakaway) torque multiple at -40C vs +20C for:
  - Baseline: petroleum-greased steel bearings.
  - Upgrade:  dry-lubricated ceramic-hybrid bearings.

This is the paper's Table 5 / Section 7.3 result.

DERIVED vs ASSUMED
-------------------
DERIVED: viscosity ratio, torque ratio, % reduction.

ASSUMED (see CONFIG):
  - Arrhenius-form viscosity/temperature model, calibrated to a
    reference viscosity + activation-energy term that reproduces the
    published order-of-magnitude behaviour for NLGI-2 lithium-complex
    grease (roughly a 10x viscosity increase from +20C to -40C).
    Replace with a manufacturer viscosity-temperature curve for the
    actual grease/bearing selected before final submission.
  - Torque scales with viscosity^0.5 (sub-linear boundary-lubrication
    scaling for rolling-element bearings, not direct proportionality).
  - Dry ceramic-hybrid bearing torque is treated as near-flat with
    temperature (+/-15%, not viscosity-governed) since it is not
    grease-lubricated.

RUN
---
    python3 bearing_lubrication_sim.py
"""
import numpy as np

CONFIG = {
    "T_ref_C": 20.0,
    "T_cold_C": -40.0,
    "grease_v_ref_cSt": 150.0,     # viscosity at T_ref
    "grease_Ea_over_R": 2600.0,    # Kelvin, calibrated activation-energy term
    "torque_viscosity_exponent": 0.5,
    "ceramic_hybrid_torque_multiple": 1.15,  # assumed near-flat behaviour
}


def _grease_viscosity_cSt(T_c, v_ref, Ea_over_R, T_ref_C=293.15 - 273.15):
    T_k = T_c + 273.15
    T_ref_k = T_ref_C + 273.15
    return v_ref * np.exp(Ea_over_R * (1.0 / T_k - 1.0 / T_ref_k))


def run(cfg=CONFIG):
    v_ref = _grease_viscosity_cSt(cfg["T_ref_C"], cfg["grease_v_ref_cSt"], cfg["grease_Ea_over_R"], cfg["T_ref_C"])
    v_cold = _grease_viscosity_cSt(cfg["T_cold_C"], cfg["grease_v_ref_cSt"], cfg["grease_Ea_over_R"], cfg["T_ref_C"])
    visc_ratio = v_cold / v_ref
    torque_ratio_grease = visc_ratio ** cfg["torque_viscosity_exponent"]
    torque_ratio_ceramic = cfg["ceramic_hybrid_torque_multiple"]

    return {
        "viscosity_ref_cSt": v_ref,
        "viscosity_cold_cSt": v_cold,
        "viscosity_ratio": visc_ratio,
        "torque_multiple_grease": torque_ratio_grease,
        "torque_multiple_ceramic": torque_ratio_ceramic,
        "torque_reduction_pct": (1 - torque_ratio_ceramic / torque_ratio_grease) * 100,
        "config": cfg,
    }


if __name__ == "__main__":
    r = run()
    print("Bearing startup torque: petroleum grease vs dry ceramic-hybrid")
    print(f"  Grease viscosity @ +{CONFIG['T_ref_C']:.0f}C : {r['viscosity_ref_cSt']:.0f} cSt")
    print(f"  Grease viscosity @ {CONFIG['T_cold_C']:.0f}C : {r['viscosity_cold_cSt']:.0f} cSt "
          f"(ratio {r['viscosity_ratio']:.1f}x)")
    print(f"  Startup torque multiple, greased steel  : {r['torque_multiple_grease']:.2f}x")
    print(f"  Startup torque multiple, ceramic-hybrid : {r['torque_multiple_ceramic']:.2f}x")
    print(f"  Reduction from upgrade                  : {r['torque_reduction_pct']:.1f}%")
