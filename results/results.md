# Simulation Results

_Generated 2026-09-20T03:30:45.091171+00:00. Regenerate with `python3 run_all.py`._

## 7.1 Pointing control — DOB+UKF vs fixed-gain PID

| Metric | Fixed-gain PID | DOB + UKF | Improvement |
|---|---|---|---|
| RMS pointing error | 38.0 mrad | 11.9 mrad | 68.7% reduction |
| Peak pointing error | 162.5 mrad | 44.4 mrad | 72.7% reduction |

## 7.2 Battery capacity retention — Li-ion vs LiFePO4 + heater

| Configuration | Capacity outcome |
|---|---|
| Li-ion, unheated, -40C ambient | 25.0% of rated capacity |
| LiFePO4 cell held at heater floor | 92.0% of rated capacity |
| Heater parasitic draw (aerogel case) | 9.5 W continuous — 26.0% of pack over mission |
| LiFePO4 NET usable capacity | 68.1% of rated — 172.4% relative gain |

## 7.3 Bearing startup torque — grease vs dry ceramic-hybrid

| Bearing type | Startup torque multiple at -40C vs +20C |
|---|---|
| Petroleum-greased steel (baseline) | 3.13x |
| Dry-lubricated ceramic-hybrid (upgrade) | 1.15x |
| **Reduction** | **63.3%** |

## 7.4 System reliability — RBD/MTTF

| Configuration | System failure rate | MTTF |
|---|---|---|
| Baseline (altitude-derated) | 22.91 | 43,649 h (~5.0 yr) |
| Upgraded (hardened) | 7.36 | 135,870 h (~15.5 yr) |
| **Improvement** | | **211.3%** |

## 7.5 Detection range and thermal/processing derating

| Front end | Detection range |
|---|---|
| Baseline (28 dBi) | 3.00 km |
| Upgraded (31 dBi) | 4.24 km — +41.3% |

Warm-case (+15C ambient) processing/thermal derating required at altitude: **27.3%** (16.7 W → 12.1 W sustainable dissipation).

## 8. Cost and efficiency

| | Baseline | Upgraded |
|---|---|---|
| Per-unit BOM | Rs 13,600 | Rs 34,800 (+155.9%) |
| Expected failures / 5yr | 1.00 | 0.32 |
| Field-service cost / 5yr | Rs 45,156 | Rs 14,507 |
| **5-yr lifecycle cost** | **Rs 58,756** | **Rs 49,307 (-16.1%)** |
