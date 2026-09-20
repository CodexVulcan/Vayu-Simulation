"""
run_all.py

Runs every simulation module in this folder and writes the combined
output to results/results.json (machine-readable) and results/results.md
(the exact tables the research paper's Section 7/8 numbers are copied
from). Re-run this after changing any CONFIG dict to regenerate both
files and confirm what changed.

RUN
---
    python3 run_all.py
"""
import json
import datetime
from pathlib import Path

import pointing_control_sim
import battery_thermal_sim
import bearing_lubrication_sim
import reliability_rbd_sim
import radar_range_sim
import thermal_derating_sim
import cost_lifecycle_sim

OUT_DIR = Path(__file__).parent / "results"
OUT_DIR.mkdir(exist_ok=True)


def _strip_config(d):
    """Drop the echoed CONFIG blocks from the JSON export's top level
    result values (kept in a separate 'configs' section instead) so the
    numeric results stay easy to scan."""
    return {k: v for k, v in d.items() if k != "config" and k != "mttf_used"}


def main():
    pointing = pointing_control_sim.run()
    battery = battery_thermal_sim.run()
    bearing = bearing_lubrication_sim.run()
    reliability = reliability_rbd_sim.run()
    radar = radar_range_sim.run()
    thermal = thermal_derating_sim.run()
    cost = cost_lifecycle_sim.run(mttf=reliability)

    results = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pointing_control": _strip_config(pointing),
        "battery_capacity": _strip_config(battery),
        "bearing_torque": _strip_config(bearing),
        "reliability_mttf": _strip_config(reliability),
        "radar_range": _strip_config(radar),
        "thermal_derating": thermal,  # nested, no top-level config to strip
        "cost_lifecycle": _strip_config(cost),
        "configs": {
            "pointing_control": pointing["config"],
            "battery_capacity": battery["config"],
            "bearing_torque": bearing["config"],
            "reliability_mttf": reliability["config"],
            "radar_range": radar["config"],
            "thermal_derating": thermal["config"],
            "cost_lifecycle": cost["config"],
        },
    }

    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2, default=str))

    md = []
    md.append(f"# Simulation Results\n")
    md.append(f"_Generated {results['generated_utc']}. Regenerate with `python3 run_all.py`._\n")

    md.append("## 7.1 Pointing control — DOB+UKF vs fixed-gain PID\n")
    md.append("| Metric | Fixed-gain PID | DOB + UKF | Improvement |")
    md.append("|---|---|---|---|")
    md.append(f"| RMS pointing error | {pointing['rms_pid_mrad']:.1f} mrad | {pointing['rms_dob_mrad']:.1f} mrad | {pointing['rms_reduction_pct']:.1f}% reduction |")
    md.append(f"| Peak pointing error | {pointing['peak_pid_mrad']:.1f} mrad | {pointing['peak_dob_mrad']:.1f} mrad | {pointing['peak_reduction_pct']:.1f}% reduction |\n")

    md.append("## 7.2 Battery capacity retention — Li-ion vs LiFePO4 + heater\n")
    md.append("| Configuration | Capacity outcome |")
    md.append("|---|---|")
    md.append(f"| Li-ion, unheated, -40C ambient | {battery['cap_liion_unheated_pct']:.1f}% of rated capacity |")
    md.append(f"| LiFePO4 cell held at heater floor | {battery['cap_lifepo4_at_floor_pct']:.1f}% of rated capacity |")
    md.append(f"| Heater parasitic draw (aerogel case) | {battery['heater_W_aerogel_case']:.1f} W continuous — {battery['heater_pct_of_pack']:.1f}% of pack over mission |")
    md.append(f"| LiFePO4 NET usable capacity | {battery['cap_lifepo4_net_pct']:.1f}% of rated — {battery['relative_gain_pct']:.1f}% relative gain |\n")

    md.append("## 7.3 Bearing startup torque — grease vs dry ceramic-hybrid\n")
    md.append("| Bearing type | Startup torque multiple at -40C vs +20C |")
    md.append("|---|---|")
    md.append(f"| Petroleum-greased steel (baseline) | {bearing['torque_multiple_grease']:.2f}x |")
    md.append(f"| Dry-lubricated ceramic-hybrid (upgrade) | {bearing['torque_multiple_ceramic']:.2f}x |")
    md.append(f"| **Reduction** | **{bearing['torque_reduction_pct']:.1f}%** |\n")

    md.append("## 7.4 System reliability — RBD/MTTF\n")
    md.append("| Configuration | System failure rate | MTTF |")
    md.append("|---|---|---|")
    md.append(f"| Baseline (altitude-derated) | {reliability['lambda_baseline']:.2f} | {reliability['mttf_baseline_hr']:,.0f} h (~{reliability['mttf_baseline_years']:.1f} yr) |")
    md.append(f"| Upgraded (hardened) | {reliability['lambda_upgraded']:.2f} | {reliability['mttf_upgraded_hr']:,.0f} h (~{reliability['mttf_upgraded_years']:.1f} yr) |")
    md.append(f"| **Improvement** | | **{reliability['mttf_improvement_pct']:.1f}%** |\n")

    md.append("## 7.5 Detection range and thermal/processing derating\n")
    md.append("| Front end | Detection range |")
    md.append("|---|---|")
    md.append(f"| Baseline (28 dBi) | {radar['range_baseline_km']:.2f} km |")
    md.append(f"| Upgraded (31 dBi) | {radar['range_upgraded_km']:.2f} km — +{radar['range_improvement_pct']:.1f}% |\n")
    wc = thermal["warm_case_reported"]
    md.append(f"Warm-case (+15C ambient) processing/thermal derating required at altitude: **{wc['derating_required_pct']:.1f}%** "
               f"({wc['P_max_sea_level_equivalent_W']:.1f} W → {wc['P_max_at_altitude_W']:.1f} W sustainable dissipation).\n")

    md.append("## 8. Cost and efficiency\n")
    md.append("| | Baseline | Upgraded |")
    md.append("|---|---|---|")
    md.append(f"| Per-unit BOM | Rs {cost['bom_baseline_inr']:,} | Rs {cost['bom_upgraded_inr']:,} ({cost['bom_delta_pct']:+.1f}%) |")
    md.append(f"| Expected failures / 5yr | {cost['failures_baseline_5yr']:.2f} | {cost['failures_upgraded_5yr']:.2f} |")
    md.append(f"| Field-service cost / 5yr | Rs {cost['service_cost_baseline_inr']:,.0f} | Rs {cost['service_cost_upgraded_inr']:,.0f} |")
    md.append(f"| **5-yr lifecycle cost** | **Rs {cost['lifecycle_baseline_inr']:,.0f}** | **Rs {cost['lifecycle_upgraded_inr']:,.0f} ({cost['lifecycle_delta_pct']:+.1f}%)** |\n")

    (OUT_DIR / "results.md").write_text("\n".join(md))

    print(f"Wrote {OUT_DIR / 'results.json'}")
    print(f"Wrote {OUT_DIR / 'results.md'}")


if __name__ == "__main__":
    main()
