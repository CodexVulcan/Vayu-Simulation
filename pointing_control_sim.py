"""
pointing_control_sim.py

WHAT THIS COMPUTES
-------------------
RMS and peak gimbal pointing error for two controllers under a modelled
high-altitude gust-disturbance profile evaluated across N=40 Monte Carlo seeds:
  - Baseline: fixed-gain PID (tuned once at nominal wind).
  - Upgrade:  PID + First-Order Disturbance Observer (DOB) feedforward.

DERIVED vs ASSUMED
-------------------
DERIVED (Monte Carlo statistical output across N=40 runs):
  - Mean RMS pointing error (PID vs DOB) & 95% Confidence Interval
  - Mean Peak pointing error (PID vs DOB)
  - Mean % pointing error reduction

ASSUMED (see CONFIG below):
  - Gimbal inertia J, damping b
  - Wind->torque dynamic pressure model (rho = 0.78 kg/m^3 at 4,500m ASL, ISA standard)
  - Actuator sizing constraint: control torque limit >= peak gust torque (8.5 N*m peak at 45 m/s)
  - DOB observer bandwidth & rate sensor noise floor
"""
import numpy as np

CONFIG = {
    "n_seeds": 40,
    "base_seed": 42,
    "J": 0.8,                 # kg*m^2, gimbal inertia
    "b": 0.15,                # N*m*s/rad, viscous damping
    "dt": 0.002,              # s, simulation timestep (500 Hz control loop)
    "T": 30.0,                # s, simulation duration
    "skip_transient_s": 2.0,
    "rho": 0.78,              # kg/m^3, standard ISA air density at 4,500m ASL
    "Cd": 1.2,                # drag coefficient, gimbal head
    "sail_area_m2": 0.06,     # effective wind-facing area
    "moment_arm_m": 0.15,     # moment arm length
    "wind_mean_mps": 12.0,    # mean background wind speed
    "wind_corr_time_s": 2.0,  # Ornstein-Uhlenbeck correlation time
    "wind_sigma": 6.0,        # turbulence intensity
    "n_gust_bursts": 25,
    "gust_peak_range_mps": (30.0, 45.0),
    "pid_gains": {"Kp": 6.0, "Ki": 1.5, "Kd": 0.9},
    "dob_bandwidth_rad_s": 8.0,
    "control_torque_limit_Nm": 10.0,  # Sized for peak gust load (8.5 N*m at 45 m/s)
    "gyro_noise_std_rad_s": 0.001,    # Sensor noise on rate measurement
}


def _build_disturbance(cfg, N, dt, rng):
    # 1. Background wind turbulence (Ornstein-Uhlenbeck process)
    v = np.zeros(N)
    v[0] = cfg["wind_mean_mps"]
    for i in range(1, N):
        dv = -(v[i - 1] - cfg["wind_mean_mps"]) / cfg["wind_corr_time_s"] * dt \
             + cfg["wind_sigma"] * np.sqrt(dt) * rng.standard_normal()
        v[i] = v[i - 1] + dv

    # 2. Add discrete gust events (Gaussian spatial/temporal envelope)
    gust_idx = rng.choice(N, size=cfg["n_gust_bursts"], replace=False)
    width = int(0.5 / dt)
    for gt in gust_idx:
        peak = rng.uniform(*cfg["gust_peak_range_mps"])
        for k in range(max(0, gt - width), min(N, gt + width)):
            v[k] = max(v[k], peak * np.exp(-((k - gt) * dt / 0.3) ** 2))

    # 3. Dynamic pressure torque: Tau = 0.5 * rho * Cd * A * l * v^2
    def wind_to_torque(vv):
        return 0.5 * cfg["rho"] * cfg["Cd"] * cfg["sail_area_m2"] * cfg["moment_arm_m"] * (vv ** 2)

    tau_magnitude = wind_to_torque(v)

    # Low-frequency directional drift (prevents non-physical 2ms sign chatter)
    dir_raw = rng.standard_normal(N)
    b_lp = np.exp(-dt / 1.0)  # 1-second directional correlation filter
    dir_smooth = np.zeros(N)
    curr_dir = 1.0
    for i in range(N):
        curr_dir = b_lp * curr_dir + (1 - b_lp) * dir_raw[i]
        dir_smooth[i] = np.sign(curr_dir if curr_dir != 0 else 1.0)

    tau = tau_magnitude * dir_smooth
    return tau


def _simulate(cfg, tau_dist, use_dob, rng):
    N = len(tau_dist)
    dt = cfg["dt"]
    J, b = cfg["J"], cfg["b"]
    Kp, Ki, Kd = cfg["pid_gains"]["Kp"], cfg["pid_gains"]["Ki"], cfg["pid_gains"]["Kd"]
    limit = cfg["control_torque_limit_Nm"]
    noise_std = cfg["gyro_noise_std_rad_s"]

    theta = omega = integ = prev_err = dist_hat = 0.0
    err_hist = np.zeros(N)
    prev_omega_meas = 0.0

    for i in range(N):
        err = -theta  # reference is 0 rad (station-keeping)
        integ += err * dt
        deriv = (err - prev_err) / dt

        tau_pid = Kp * err + Ki * integ + Kd * deriv
        tau_cmd = tau_pid - (dist_hat if use_dob else 0.0)
        tau_cmd = np.clip(tau_cmd, -limit, limit)

        # Plant dynamics
        alpha = (tau_cmd + tau_dist[i] - b * omega) / J
        omega += alpha * dt
        theta += omega * dt

        if use_dob:
            # Rate gyro measurement with noise
            omega_meas = omega + noise_std * rng.standard_normal()
            alpha_est = (omega_meas - prev_omega_meas) / dt
            prev_omega_meas = omega_meas

            # Disturbance Observer estimate: Tau_dist_est = J * alpha + b * omega - Tau_cmd
            tau_dist_est_raw = J * alpha_est + b * omega_meas - tau_cmd
            dist_hat += cfg["dob_bandwidth_rad_s"] * (tau_dist_est_raw - dist_hat) * dt

        prev_err = err
        err_hist[i] = err

    return err_hist


def run(cfg=CONFIG):
    n_seeds = cfg.get("n_seeds", 40)
    base_seed = cfg.get("base_seed", 42)

    rms_pid_list, rms_dob_list = [], []
    peak_pid_list, peak_dob_list = [], []
    cuts_list = []

    skip = int(cfg["skip_transient_s"] / cfg["dt"])

    for s in range(n_seeds):
        seed = base_seed + s
        rng = np.random.default_rng(seed)
        N = int(cfg["T"] / cfg["dt"])

        tau_dist = _build_disturbance(cfg, N, cfg["dt"], rng)

        err_pid = _simulate(cfg, tau_dist, use_dob=False, rng=rng)
        err_dob = _simulate(cfg, tau_dist, use_dob=True, rng=rng)

        rms_p = float(np.sqrt(np.mean(err_pid[skip:] ** 2))) * 1000.0  # mrad
        rms_d = float(np.sqrt(np.mean(err_dob[skip:] ** 2))) * 1000.0  # mrad
        peak_p = float(np.max(np.abs(err_pid[skip:]))) * 1000.0       # mrad
        peak_d = float(np.max(np.abs(err_dob[skip:]))) * 1000.0       # mrad

        cut = (1.0 - rms_d / rms_p) * 100.0

        rms_pid_list.append(rms_p)
        rms_dob_list.append(rms_d)
        peak_pid_list.append(peak_p)
        peak_dob_list.append(peak_d)
        cuts_list.append(cut)

    mean_rms_pid = np.mean(rms_pid_list)
    mean_rms_dob = np.mean(rms_dob_list)
    mean_peak_pid = np.mean(peak_pid_list)
    mean_peak_dob = np.mean(peak_dob_list)

    mean_cut = np.mean(cuts_list)
    std_cut = np.std(cuts_list, ddof=1)
    ci95_cut = 1.96 * (std_cut / np.sqrt(n_seeds))

    return {
        "n_seeds": n_seeds,
        "rms_pid_mrad_mean": mean_rms_pid,
        "rms_dob_mrad_mean": mean_rms_dob,
        "rms_reduction_pct_mean": mean_cut,
        "rms_reduction_pct_ci95": ci95_cut,
        "rms_reduction_pct_min": np.min(cuts_list),
        "rms_reduction_pct_max": np.max(cuts_list),
        "peak_pid_mrad_mean": mean_peak_pid,
        "peak_dob_mrad_mean": mean_peak_dob,
        "peak_reduction_pct_mean": (1.0 - mean_peak_dob / mean_peak_pid) * 100.0,
        "config": cfg,
    }


if __name__ == "__main__":
    r = run()
    print(f"Pointing control evaluation over N={r['n_seeds']} Monte Carlo seeds:")
    print(f"  PID Baseline RMS Error : {r['rms_pid_mrad_mean']:.2f} mrad")
    print(f"  DOB+PID Upgrade RMS Error: {r['rms_dob_mrad_mean']:.2f} mrad")
    print(f"  RMS Pointing Error Cut : {r['rms_reduction_pct_mean']:.1f}% (95% CI: +/-{r['rms_reduction_pct_ci95']:.1f}%, Range: {r['rms_reduction_pct_min']:.1f}%-{r['rms_reduction_pct_max']:.1f}%)")
    print(f"  Peak Error - PID       : {r['peak_pid_mrad_mean']:.2f} mrad")
    print(f"  Peak Error - DOB       : {r['peak_dob_mrad_mean']:.2f} mrad")
