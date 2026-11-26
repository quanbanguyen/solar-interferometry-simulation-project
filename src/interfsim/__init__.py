"""interfsim - end-to-end simulator for small radio interferometers.

From a measured solar flux time series and a simulated antenna pattern to
per-antenna voltages, correlator output, u-v coverage and dirty images.
"""
from .array import (
                    ArrayConfig,
                    cross,
                    from_enu,
                    from_file,
                    linear,
                    make_array,
                    preset_compact,
                    preset_cross4,
                    preset_dlite,
                    preset_extended,
                    random_2d,
                    tee,
                    triangle_center,
)
from .beam import GaussianBeam, IsotropicBeam, Mount, TabulatedBeam, load_beam
from .burst import MovingBurst, burst_voltages, centroid_crb, track_centroid
from .correlator import autocorrelate, correlate
from .geometry import Observation, altaz_deg, antenna_phase, compute_uvw, enu_to_xyz, zenith_angle_deg
from .imaging import forward_visibilities, make_dirty_image, sweep_layouts, synthesized_beam
from .signal import effective_area, noise_power, power_to_vrms, simulate_voltages, snr_db, source_power
from .sky import disk_components, vis_gaussian, vis_point_sources, vis_uniform_disk

__version__ = "0.2.0"

__all__ = [
    "ArrayConfig", "cross", "from_enu", "from_file", "linear", "make_array", "preset_compact",
    "preset_cross4", "preset_dlite", "preset_extended", "random_2d", "tee", "triangle_center",
    "GaussianBeam", "IsotropicBeam", "Mount", "TabulatedBeam", "load_beam",
    "MovingBurst", "burst_voltages", "centroid_crb", "track_centroid",
    "autocorrelate", "correlate",
    "Observation", "altaz_deg", "antenna_phase", "compute_uvw", "enu_to_xyz", "zenith_angle_deg",
    "forward_visibilities", "make_dirty_image", "sweep_layouts", "synthesized_beam",
    "effective_area", "noise_power", "power_to_vrms", "simulate_voltages", "snr_db", "source_power",
    "disk_components", "vis_gaussian", "vis_point_sources", "vis_uniform_disk",
]
