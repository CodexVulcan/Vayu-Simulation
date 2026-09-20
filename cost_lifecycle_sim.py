"""
cost_lifecycle_sim.py

WHAT THIS COMPUTES
-------------------
Per-unit BOM cost delta (baseline vs upgraded hardware) and a 5-year
lifecycle cost projection that folds in field-service savings from the
MTTF improvement computed in reliability_rbd_sim.py.

This is the paper's Section 8 (cost & efficiency) result.

DERIVED vs ASSUMED
-------------------
DERIVED: BOM totals and % delta, expected failures over 5 years (from
MTTF), field-service cost, 5-year lifecycle cost and % delta.

ASSUMED (see CONFIG):
  - BOM line-item prices (order-of-magnitude INR, NOT vendor quotes --
    replace with real supplier pricing before citing this externally)
  - Field-service callout cost (high-altitude-terrain logistics estimate)
  - Deployment duty cycle (8760 h/yr = continuous operation)

DEPENDENCY
----------
Imports MTTF figures from reliability_rbd_sim.py so the two results
stay consistent -- do not hand-edit an MTTF number here without also
updating that module.

RUN
---
    python3 cost_lifecycle_sim.py
"""
import reliability_rbd_sim

CONFIG = {
    "bom_baseline_inr": {
        "Standard IP65 enclosure": 3500,
        "COTS Li-ion pack (220Wh)": 4200,
        "Steel bearings + grease": 1800,
        "Std MOSFETs (undereated)": 2600,
        "Fixed-gain PID controller board": 1500,
    },
    "bom_upgraded_inr": {
        "Aerogel double-wall enclosure + preheat interlock": 9500,
        "LiFePO4 pack (220Wh) + heater + smart BMS": 11800,
        "Ceramic-hybrid dry-lubricated bearings": 6200,
        "Derated MOSFETs (higher voltage-class parts)": 4100,
        "DOB+UKF controller (added compute/sensing)": 3200,
    },
    "service_call_cost_inr": 45000,   # high-altitude-terrain field service, order-of-magnitude
    "years": 5,
    "deployment_hours_per_year": 8760,
}


def run(cfg=CONFIG, mttf=None):
    if mttf is None:
        mttf = reliability_rbd_sim.run()

    cost_baseline = sum(cfg["bom_baseline_inr"].values())
    cost_upgraded = sum(cfg["bom_upgraded_inr"].values())
    bom_delta_pct = (cost_upgraded / cost_baseline - 1) * 100

    hours_5yr = cfg["deployment_hours_per_year"] * cfg["years"]
    failures_baseline = hours_5yr / mttf["mttf_baseline_hr"]
    failures_upgraded = hours_5yr / mttf["mttf_upgraded_hr"]

    service_cost_baseline = failures_baseline * cfg["service_call_cost_inr"]
    service_cost_upgraded = failures_upgraded * cfg["service_call_cost_inr"]

    lifecycle_baseline = cost_baseline + service_cost_baseline
    lifecycle_upgraded = cost_upgraded + service_cost_upgraded
    lifecycle_delta_pct = (lifecycle_upgraded / lifecycle_baseline - 1) * 100

    return {
        "bom_baseline_inr": cost_baseline,
        "bom_upgraded_inr": cost_upgraded,
        "bom_delta_pct": bom_delta_pct,
        "failures_baseline_5yr": failures_baseline,
        "failures_upgraded_5yr": failures_upgraded,
        "service_cost_baseline_inr": service_cost_baseline,
        "service_cost_upgraded_inr": service_cost_upgraded,
        "lifecycle_baseline_inr": lifecycle_baseline,
        "lifecycle_upgraded_inr": lifecycle_upgraded,
        "lifecycle_delta_pct": lifecycle_delta_pct,
        "config": cfg,
        "mttf_used": mttf,
    }


if __name__ == "__main__":
    r = run()
    print("Cost model: BOM delta + 5-year lifecycle cost")
    print(f"  Baseline BOM (per unit) : Rs {r['bom_baseline_inr']:,}")
    print(f"  Upgraded BOM (per unit) : Rs {r['bom_upgraded_inr']:,}  ({r['bom_delta_pct']:+.1f}%)")
    print(f"  Expected failures / 5yr, baseline : {r['failures_baseline_5yr']:.2f} "
          f"-> service cost Rs {r['service_cost_baseline_inr']:,.0f}")
    print(f"  Expected failures / 5yr, upgraded : {r['failures_upgraded_5yr']:.2f} "
          f"-> service cost Rs {r['service_cost_upgraded_inr']:,.0f}")
    print(f"  5-yr lifecycle cost, baseline : Rs {r['lifecycle_baseline_inr']:,.0f}")
    print(f"  5-yr lifecycle cost, upgraded : Rs {r['lifecycle_upgraded_inr']:,.0f}")
    verdict = "net savings" if r["lifecycle_delta_pct"] < 0 else "net higher cost"
    print(f"  Lifecycle delta : {r['lifecycle_delta_pct']:+.1f}% ({verdict})")
