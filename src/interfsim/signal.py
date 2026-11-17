"""Radiometry and the voltage-level engine ("Engine A").

Engine A synthesises complex baseband voltages per antenna, sample by sample,
so the output can drive an FPGA/correlator testbench. Each sample stands for
one coarse time step along the hour-angle track (not one ADC sample at the
full bandwidth); see docs/AUDIT.md for the implications.
"""
from __future__ import annotations

import numpy as np

from .array import ArrayConfig
from .constants import K_B, SFU
from .geometry import Observation, antenna_phase


def effective_area(gain_dBi: float, lam_m: float) -> float:
    """A_e = G lambda^2 / (4 pi) [m^2]."""
    return 10.0 ** (gain_dBi / 10.0) * lam_m ** 2 / (4.0 * np.pi)


def source_power(flux_sfu, a_eff_m2: float, bw_hz: float, pol_factor: float = 0.5):
    """Power delivered by a source of flux density S [SFU] to a matched receiver [W].

    pol_factor = 0.5 for one linear polarisation receiving unpolarised emission
    (P = 1/2 S A_e B); use 1.0 for a dual-polarisation total-power sum.
    """
    return pol_factor * np.asarray(flux_sfu, float) * SFU * a_eff_m2 * bw_hz


def noise_power(t_sys_k: float, bw_hz: float) -> float:
    """Johnson-Nyquist noise power k T B [W]."""
    return K_B * t_sys_k * bw_hz


def power_to_vrms(power_w, r_load_ohm: float):
    return np.sqrt(np.asarray(power_w, float) * r_load_ohm)


def snr_db(p_signal_w, p_noise_w):
    """Per-sample power SNR in dB (both arguments in watts)."""
    return 10.0 * np.log10(np.asarray(p_signal_w, float) / p_noise_w)


def radiometer_snr(p_signal_w, p_noise_w, bw_hz: float, t_int_s: float):
    """Total-power radiometer SNR = (P_s/P_n) sqrt(B tau)."""
    return np.asarray(p_signal_w, float) / p_noise_w * np.sqrt(bw_hz * t_int_s)


def complex_noise(rng: np.random.Generator, shape, sigma_per_quadrature: float) -> np.ndarray:
    return sigma_per_quadrature * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))


def simulate_voltages(config: ArrayConfig, obs: Observation,
                      amplitude_envelope: np.ndarray, noise_sigma: float,
                      source_process: np.ndarray | None = None,
                      seed: int | None = None,
                      components: np.ndarray | None = None) -> np.ndarray:
    """Complex voltages V (T, N).

    amplitude_envelope : (T,) RMS source voltage including the primary beam.
    noise_sigma        : per-quadrature receiver noise RMS [V], independent per antenna.
    components         : optional (K, 3) array of (flux_fraction, l, m). Each
        component radiates its own independent Gaussian process, so an extended
        source decorrelates on long baselines exactly as the van Cittert-Zernike
        theorem predicts. Without it the source is a single point at the phase
        centre driven by `source_process`.
    """
    rng = np.random.default_rng(seed)
    T = obs.H_deg.size
    env = np.broadcast_to(np.asarray(amplitude_envelope, float), (T,))
    if components is None:
        if source_process is None:
            source_process = complex_noise(rng, T, 1 / np.sqrt(2))
        sig = (env * source_process)[:, None] * np.exp(1j * antenna_phase(config.positions_enu, obs))
    else:
        sig = np.zeros((T, config.n_ant), dtype=np.complex128)
        for frac, l, m in np.asarray(components, float):
            proc = complex_noise(rng, T, np.sqrt(frac / 2))
            sig += (env * proc)[:, None] * np.exp(1j * antenna_phase(config.positions_enu, obs, l, m))
    return sig + complex_noise(rng, (T, config.n_ant), noise_sigma)
