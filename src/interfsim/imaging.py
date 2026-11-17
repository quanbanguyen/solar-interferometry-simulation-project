"""Imaging: forward visibilities ("Engine B") and direct-DFT dirty images."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor

import numpy as np

from .array import ArrayConfig
from .geometry import Observation, compute_uvw
from .sky import sky_visibilities


def forward_visibilities(config: ArrayConfig, obs: Observation, sky: dict,
                         time_weight: np.ndarray | None = None,
                         noise_std: float = 0.0, seed: int | None = None):
    """Model visibilities at the sampled (u, v) of a sky dict (see sky.sky_visibilities).

    time_weight (T,) scales each time step, e.g. the primary-beam power along
    the track. noise_std is the per-quadrature complex noise per visibility.
    Returns u, v, w, V, each (T, B).
    """
    u, v, w = compute_uvw(config.baseline_vectors_enu, obs)
    V = sky_visibilities(sky, u, v)
    if time_weight is not None:
        V = V * np.asarray(time_weight)[:, None]
    if noise_std > 0:
        rng = np.random.default_rng(seed)
        V = V + noise_std * (rng.standard_normal(V.shape) + 1j * rng.standard_normal(V.shape))
    return u, v, w, V


def fringe_stop(vis: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Remove the geometric phase exp(-2 pi i w) left in raw correlator output."""
    return vis * np.exp(2j * np.pi * w)


def image_axes(fov_deg: float, grid: int) -> tuple[np.ndarray, np.ndarray]:
    """Direction cosines l (E-W) and m (N-S) of the image pixels [rad, small-angle]."""
    l = np.radians(np.linspace(-fov_deg / 2, fov_deg / 2, grid))
    return l, l.copy()


def make_dirty_image(u, v, w, vis, fov_deg: float = 3.0, grid: int = 256,
                     do_fringe_stop: bool = True, block: int = 8192, time_step: int = 1,
                     dtype=np.complex64, weights=None, normalize: bool = True):
    """Dirty image by direct Fourier transform (Hermitian-symmetrised).

    I(l, m) = 2 Re sum_k W_k V_k exp(+2 pi i (u_k l + v_k m)) / sum W_k

    Computed block-wise as a matrix product so memory stays O(block * grid).
    do_fringe_stop: True for raw correlator output (Engine A), False for
    forward-model visibilities that are already phased to the centre.
    normalize: True scales the peak to 1 (thesis behaviour); False returns
    flux units per synthesised beam for a weight-normalised natural image.
    Returns (image, l_deg, m_deg).
    """
    l, m = image_axes(fov_deg, grid)
    if time_step > 1:
        u, v, w, vis = u[::time_step], v[::time_step], w[::time_step], vis[::time_step]
        if weights is not None:
            weights = weights[::time_step]
    Vf = (fringe_stop(vis, w) if do_fringe_stop else vis).ravel()
    W = np.ones(Vf.shape) if weights is None else np.asarray(weights, float).ravel()
    Vf = (Vf * W).astype(dtype)
    uf, vf = np.ravel(u).astype(np.float64), np.ravel(v).astype(np.float64)

    dirty = np.zeros((grid, grid), dtype=np.complex128)
    for s in range(0, Vf.size, block):
        e = min(s + block, Vf.size)
        eu = np.exp(2j * np.pi * np.outer(uf[s:e], l)).astype(dtype)
        ev = np.exp(2j * np.pi * np.outer(vf[s:e], m)).astype(dtype)
        dirty += (ev.T @ (Vf[s:e, None] * eu)).astype(np.complex128)

    img = 2.0 * np.real(dirty) / (2.0 * W.sum())
    if normalize:
        peak = np.max(np.abs(img))
        if peak > 0:
            img = img / peak
    return img, np.degrees(l), np.degrees(m)


def synthesized_beam(u, v, w, fov_deg: float = 3.0, grid: int = 256, **kw):
    """PSF: dirty image of a unit point source at the phase centre (peak = 1)."""
    kw.pop("do_fringe_stop", None)
    return make_dirty_image(u, v, w, np.ones(np.shape(u), np.complex64), fov_deg, grid,
                            do_fringe_stop=False, **kw)


def _sweep_worker(args):
    config, obs, sky, time_weight, fov_deg, grid, noise_std, seed, time_step = args
    u, v, w, V = forward_visibilities(config, obs, sky, time_weight, noise_std, seed)
    img, l_deg, m_deg = make_dirty_image(u, v, w, V, fov_deg, grid, do_fringe_stop=False,
                                         time_step=time_step)
    psf, _, _ = synthesized_beam(u, v, w, fov_deg, grid, time_step=time_step)
    return config.name, dict(image=img, psf=psf, u=u, v=v, l_deg=l_deg, m_deg=m_deg,
                             bl_max=float(config.baseline_lengths.max()))


def sweep_layouts(configs, obs, sky, time_weight=None, fov_deg=3.0, grid=192,
                  noise_std=0.0, seed=0, time_step=1, n_workers: int | None = 1):
    """Forward model + dirty image + PSF for several layouts.

    n_workers > 1 runs layouts in parallel processes (needs an importable
    __main__ on Windows, i.e. not from an interactive cell)."""
    jobs = [(c, obs, sky, time_weight, fov_deg, grid, noise_std, seed, time_step) for c in configs]
    if n_workers == 1:
        return dict(map(_sweep_worker, jobs))
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        return dict(ex.map(_sweep_worker, jobs))
