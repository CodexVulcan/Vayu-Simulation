"""
reliability_rbd_sim.py

WHAT THIS COMPUTES
-------------------
System MTTF via a series reliability block diagram (RBD) over six
subsystems, for baseline vs upgraded hardware.

This is the paper's Table 6 / Section 7.4 result.

DERIVED vs ASSUMED
-------------------
DERIVED: system failure rate (sum of component rates x altitude
multipliers), MTTF = 1 / failure rate, % improvement.

ASSUMED (see CONFIG -- these are the numbers to defend/replace with
real component MTBF data or MIL-HDBK-217F-style calculations before
this is presented as anything more than an order-of-magnitude estimate):
  - Per-component baseline failure rate (arbitrary "rate units", i.e.
    relative FIT-scale, not vendor-certified)
  - Per-component altitude/cold stress multiplier, baseline vs upgraded
  - Per-component base-rate improvement factor from the hardware upgrade

Because every rate above is an assumption rather than a vendor figure,
the single point estimate below is reported alongside a sensitivity
sweep (mttf_sensitivity): each rate and multiplier is perturbed
independently and the resulting improvement % is summarized as a
mean and a 5th-95th percentile range. Treat the range, not the point
estimate, as the defensible claim until real component data replaces
CONFIG.

RUN
---
    python3 reliability_rbd_sim.py
"""

import numpy as np

CONFIG = {
    "baseline_failure_rate": {
        "battery":        3.5,
        "bearings":       2.8,
        "seals":          1.6,
        "semiconductors": 1.2,
        "rf_radar":       0.9,
        "edge_compute":   0.8,
    },
    "baseline_altitude_multiplier": {
        "battery":        2.6,
        "bearings":       2.2,
        "seals":          2.0,
        "semiconductors": 1.8,
        "rf_radar":       1.3,
        "edge_compute":   1.4,
    },
    "upgraded_base_failure_rate": {
        "battery":        1.4,   # LiFePO4 + heater
        "bearings":       1.1,   # ceramic-hybrid
        "seals":          0.9,   # PEEK
        "semiconductors": 0.85,  # derated 65-70%
        "rf_radar":       0.9,   # unchanged (inherited architecture)
        "edge_compute":   0.8,   # unchanged
    },
    "upgraded_altitude_multiplier": {
        "battery":        1.35,
        "bearings":       1.25,
        "seals":          1.15,
        "semiconductors": 1.3,
        "rf_radar":       1.15,
        "edge_compute":   1.15,
    },
    "deployment_hours_per_year": 8760,
}


def run(cfg=CONFIG):
    lam_baseline = sum(
        cfg["baseline_failure_rate"][k] * cfg["baseline_altitude_multiplier"][k]
        for k in cfg["baseline_failure_rate"]
    )
    lam_upgraded = sum(
        cfg["upgraded_base_failure_rate"][k] * cfg["upgraded_altitude_multiplier"][k]
        for k in cfg["upgraded_base_failure_rate"]
    )
    mttf_baseline_hr = 1e6 / lam_baseline
    mttf_upgraded_hr = 1e6 / lam_upgraded

    return {
        "lambda_baseline": lam_baseline,
        "lambda_upgraded": lam_upgraded,
        "mttf_baseline_hr": mttf_baseline_hr,
        "mttf_upgraded_hr": mttf_upgraded_hr,
        "mttf_baseline_years": mttf_baseline_hr / cfg["deployment_hours_per_year"],
        "mttf_upgraded_years": mttf_upgraded_hr / cfg["deployment_hours_per_year"],
        "mttf_improvement_pct": (mttf_upgraded_hr / mttf_baseline_hr - 1) * 100,
        "config": cfg,
    }


def _perturb_rates(cfg, rng, spread):
    """Return a deep-copied cfg with every assumed rate/multiplier
    independently perturbed by a uniform factor in [1-spread, 1+spread].
    Deployment hours/year is left untouched (it's a fact, not an
    assumption)."""
    perturbed = {"deployment_hours_per_year": cfg["deployment_hours_per_year"]}
    for dict_key in (
        "baseline_failure_rate",
        "baseline_altitude_multiplier",
        "upgraded_base_failure_rate",
        "upgraded_altitude_multiplier",
    ):
        perturbed[dict_key] = {
            comp: val * rng.uniform(1 - spread, 1 + spread)
            for comp, val in cfg[dict_key].items()
        }
    return perturbed


def mttf_sensitivity(cfg=CONFIG, n_trials=500, spread=0.3, seed=7):
    """Perturb every assumed failure rate and altitude multiplier by
    +/-spread (uniform, independent per component) and report the
    resulting MTTF-improvement distribution. Use this range, not the
    single run() point estimate, as the headline claim."""
    rng = np.random.default_rng(seed)
    improvements = np.empty(n_trials)
    for i in range(n_trials):
        trial_cfg = _perturb_rates(cfg, rng, spread)
        improvements[i] = run(trial_cfg)["mttf_improvement_pct"]

    return {
        "n_trials": n_trials,
        "spread": spread,
        "mean_pct": float(improvements.mean()),
        "std_pct": float(improvements.std(ddof=1)),
        "p5_pct": float(np.percentile(improvements, 5)),
        "p95_pct": float(np.percentile(improvements, 95)),
        "min_pct": float(improvements.min()),
        "max_pct": float(improvements.max()),
    }


if __name__ == "__main__":
    r = run()
    print("System reliability: series RBD, baseline vs upgraded")
    print(f"  Baseline failure rate : {r['lambda_baseline']:.2f}  -> MTTF = {r['mttf_baseline_hr']:,.0f} h "
          f"(~{r['mttf_baseline_years']:.1f} yr continuous)")
    print(f"  Upgraded failure rate : {r['lambda_upgraded']:.2f}  -> MTTF = {r['mttf_upgraded_hr']:,.0f} h "
          f"(~{r['mttf_upgraded_years']:.1f} yr continuous)")
    print(f"  MTTF improvement (point estimate): {r['mttf_improvement_pct']:.1f}%")

    s = mttf_sensitivity()
    print(f"\nSensitivity (N={s['n_trials']} trials, each rate/multiplier "
          f"perturbed +/-{s['spread']*100:.0f}%):")
    print(f"  MTTF improvement: mean {s['mean_pct']:.1f}%, "
          f"5th-95th percentile {s['p5_pct']:.1f}%-{s['p95_pct']:.1f}%, "
          f"range {s['min_pct']:.1f}%-{s['max_pct']:.1f}%")
