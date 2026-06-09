"""
interfsim.py — Engine giao thoa kế cấu hình tự do 2D (East-North) cho mô phỏng
quan sát Mặt Trời. Thay thế phần hình học 1D Đông-Tây trong notebook gốc bằng
bộ ENU -> XYZ -> (u,v,w) chuẩn (Thompson, Moran & Swenson, "Interferometry and
Synthesis in Radio Astronomy", 3rd ed., Eq. 4.1), nhất quán cho:
  - per-antenna geometric phase  (chuỗi điện áp / FPGA / correlator)
  - baseline (u,v,w)             (u-v coverage + imaging)
  - fringe stopping              (dùng w-term, đúng cho mọi quỹ đạo nguồn)

Hai engine:
  (A) simulate_voltages(...)  — chuỗi điện áp thật (per-antenna), giữ nguyên mô
      hình nhiễu Johnson và xuất được hex/FPGA như notebook gốc, nay cho vị trí 2D.
  (B) forward_visibilities(...) — mô hình thuận van Cittert-Zernike (rẻ, nhanh),
      sinh V trực tiếp từ sky model (điểm hoặc đĩa Mặt Trời) -> quét nhiều case.

Tác giả engine: dựng cho đồ án giao thoa kế 610 MHz.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from itertools import combinations
from concurrent.futures import ProcessPoolExecutor

C_LIGHT = 299_792_458.0


# ════════════════════════════════════════════════════════════════════════════
# 1. CẤU HÌNH MẢNG ANTEN — vị trí tự do trong mặt phẳng East-North
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class ArrayConfig:
    """Vị trí anten trong hệ địa phương ENU (East, North, Up) tính bằng mét.
    Up = 0 cho mảng đặt trên mặt đất phẳng. positions_enu shape (N, 3)."""
    name: str
    positions_enu: np.ndarray

    def __post_init__(self):
        self.positions_enu = np.atleast_2d(np.asarray(self.positions_enu, float))
        if self.positions_enu.shape[1] == 2:  # cho phép nhập (E,N), tự thêm U=0
            z = np.zeros((self.positions_enu.shape[0], 1))
            self.positions_enu = np.hstack([self.positions_enu, z])
        # đưa tâm mảng về gốc (không đổi baseline, gọn cho u-v)
        self.positions_enu = self.positions_enu - self.positions_enu.mean(0)

    @property
    def n_ant(self) -> int:
        return self.positions_enu.shape[0]

    @property
    def pairs(self) -> list[tuple[int, int]]:
        return list(combinations(range(self.n_ant), 2))

    @property
    def baseline_vectors_enu(self) -> np.ndarray:
        """(B, 3) vector baseline b_ij = r_i - r_j cho mỗi cặp."""
        p = self.positions_enu
        return np.array([p[i] - p[j] for i, j in self.pairs])

    @property
    def baseline_lengths(self) -> np.ndarray:
        return np.linalg.norm(self.baseline_vectors_enu, axis=1)

    def summary(self) -> str:
        bl = self.baseline_lengths
        return (f"{self.name}: N={self.n_ant} anten, {len(self.pairs)} baseline, "
                f"baseline min/max = {bl.min():.1f}/{bl.max():.1f} m")


# ════════════════════════════════════════════════════════════════════════════
# 2. QUAN SÁT — vĩ độ trạm, xích vĩ nguồn, lưới hour-angle, tần số
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class Observation:
    lat_deg: float          # vĩ độ trạm (Hanoi ~ +21.0; Learmonth ~ -21.8)
    dec_deg: float          # xích vĩ Mặt Trời
    fc_hz: float = 610e6
    H_deg: np.ndarray = field(default_factory=lambda: np.linspace(-84.2, 84.2, 600))

    @property
    def lam(self) -> float:
        return C_LIGHT / self.fc_hz

    @property
    def H_rad(self) -> np.ndarray:
        return np.radians(self.H_deg)

    @property
    def dec_rad(self) -> float:
        return np.radians(self.dec_deg)

    @property
    def lat_rad(self) -> float:
        return np.radians(self.lat_deg)


# ════════════════════════════════════════════════════════════════════════════
# 3. HÌNH HỌC — ENU -> XYZ xích đạo -> (u,v,w), per-antenna phase, zenith angle
# ════════════════════════════════════════════════════════════════════════════
def enu_to_xyz(enu: np.ndarray, lat_rad: float) -> np.ndarray:
    """Quay hệ ENU địa phương sang XYZ xích đạo (X->H=0,δ=0; Y->Đông; Z->NCP)."""
    E, N, U = enu[..., 0], enu[..., 1], enu[..., 2]
    X = -N * np.sin(lat_rad) + U * np.cos(lat_rad)
    Y = E
    Z = N * np.cos(lat_rad) + U * np.sin(lat_rad)
    return np.stack([X, Y, Z], axis=-1)


def source_dir_xyz(H_rad: np.ndarray, dec_rad: float) -> np.ndarray:
    """Vector đơn vị tới nguồn trong hệ XYZ, shape (T, 3)."""
    cd = np.cos(dec_rad)
    return np.stack([cd * np.cos(H_rad), -cd * np.sin(H_rad),
                     np.full_like(H_rad, np.sin(dec_rad))], axis=-1)


def compute_uvw(baseline_vecs_enu: np.ndarray, obs: Observation):
    """(u,v,w) tính bằng bước sóng cho mỗi (thời điểm, baseline).
    Trả về u, v, w mỗi cái shape (T, B). Đây là TMS Eq. 4.1."""
    b_xyz = enu_to_xyz(baseline_vecs_enu, obs.lat_rad) / obs.lam   # (B,3) [λ]
    Xl, Yl, Zl = b_xyz[:, 0], b_xyz[:, 1], b_xyz[:, 2]            # (B,)
    H = obs.H_rad[:, None]                                         # (T,1)
    sH, cH = np.sin(H), np.cos(H)
    sd, cd = np.sin(obs.dec_rad), np.cos(obs.dec_rad)
    u = sH * Xl + cH * Yl
    v = -sd * cH * Xl + sd * sH * Yl + cd * Zl
    w = cd * cH * Xl - cd * sH * Yl + sd * Zl
    return u, v, w


def antenna_phase(positions_enu: np.ndarray, obs: Observation) -> np.ndarray:
    """Pha hình học mỗi anten theo thời gian, shape (T, N). Dùng cho chuỗi điện áp.
    phi_k(t) = -2π/λ · (r_k · ŝ(t))  — tổng quát hoá tau_k của notebook gốc."""
    ant_xyz = enu_to_xyz(positions_enu, obs.lat_rad)              # (N,3) [m]
    s = source_dir_xyz(obs.H_rad, obs.dec_rad)                   # (T,3)
    proj = ant_xyz @ s.T                                          # (N,T) [m]
    return (-2 * np.pi / obs.lam * proj).T                        # (T,N)


def zenith_angle_deg(obs: Observation) -> np.ndarray:
    """Góc thiên đỉnh của nguồn theo thời gian (deg). Anten cắm thẳng -> boresight
    là thiên đỉnh, nên đây chính là góc lệch boresight để tra primary beam."""
    sin_el = (np.sin(obs.lat_rad) * np.sin(obs.dec_rad) +
              np.cos(obs.lat_rad) * np.cos(obs.dec_rad) * np.cos(obs.H_rad))
    sin_el = np.clip(sin_el, -1.0, 1.0)
    return 90.0 - np.degrees(np.arcsin(sin_el))


# ════════════════════════════════════════════════════════════════════════════
# 4. SKY MODELS — van Cittert-Zernike forward
# ════════════════════════════════════════════════════════════════════════════
def vis_point_sources(u, v, sources):
    """sources: list (flux, l_rad, m_rad). V(u,v) = Σ flux·exp(-2πi(ul+vm))."""
    V = np.zeros(u.shape, dtype=np.complex128)
    for flux, l0, m0 in sources:
        V += flux * np.exp(-2j * np.pi * (u * l0 + v * m0))
    return V


def vis_uniform_disk(u, v, flux, diameter_rad, l0=0.0, m0=0.0):
    """Đĩa đều (đường kính góc diameter_rad): V = flux·2J1(x)/x, x=π·θ_d·q."""
    from scipy.special import j1
    q = np.sqrt(u**2 + v**2)
    x = np.pi * diameter_rad * q
    jinc = np.where(x < 1e-9, 1.0, 2 * j1(x) / np.where(x < 1e-9, 1.0, x))
    shift = np.exp(-2j * np.pi * (u * l0 + v * m0))
    return flux * jinc * shift


# ════════════════════════════════════════════════════════════════════════════
# 5. ENGINE A — chuỗi điện áp thật (per-antenna) cho FPGA + correlator
# ════════════════════════════════════════════════════════════════════════════
def simulate_voltages(config: ArrayConfig, obs: Observation,
                      amplitude_envelope: np.ndarray, noise_sigma: float,
                      source_process: np.ndarray | None = None,
                      seed: int | None = None) -> np.ndarray:
    """V_matrix (T, N) — giống Cell 3 nhưng vị trí anten 2D bất kỳ.
    amplitude_envelope (T,): V_rms · primary_beam(zenith). noise_sigma: per-quad."""
    rng = np.random.default_rng(seed)
    T = obs.H_rad.size
    if source_process is None:
        source_process = (rng.standard_normal(T) + 1j * rng.standard_normal(T)) / np.sqrt(2)
    signal_core = amplitude_envelope * source_process            # (T,)
    phase = antenna_phase(config.positions_enu, obs)             # (T,N)
    noise = noise_sigma * (rng.standard_normal((T, config.n_ant)) +
                           1j * rng.standard_normal((T, config.n_ant)))
    return signal_core[:, None] * np.exp(1j * phase) + noise


def correlate(V_matrix: np.ndarray, config: ArrayConfig, integration_bins: int):
    """Tương quan chéo + tích luỹ. Trả về visibilities (NI, B) và chỉ số dump centers."""
    T = V_matrix.shape[0]
    NI = T // integration_bins
    nval = NI * integration_bins
    vis = np.empty((NI, len(config.pairs)), dtype=np.complex128)
    for b, (i, j) in enumerate(config.pairs):
        cc = (V_matrix[:, i] * np.conj(V_matrix[:, j]))[:nval]
        vis[:, b] = cc.reshape(NI, integration_bins).mean(1)
    centers = (np.arange(NI) * integration_bins + integration_bins // 2)
    return vis, centers


# ════════════════════════════════════════════════════════════════════════════
# 6. ENGINE B — forward visibility (rẻ) cho quét nhiều case / baseline lớn
# ════════════════════════════════════════════════════════════════════════════
def forward_visibilities(config: ArrayConfig, obs: Observation, sky,
                         time_weight: np.ndarray | None = None,
                         noise_std: float = 0.0, seed: int | None = None):
    """Sinh V tại các (u,v) lấy mẫu từ sky model.
    sky: dict {'type':'point','sources':[(flux,l,m),...]} hoặc
              {'type':'disk','flux':..,'diameter_rad':..,'l0':..,'m0':..}
    time_weight (T,): trọng số biên độ theo thời gian (vd primary_beam² khi transit).
    noise_std: độ lệch chuẩn nhiễu phức trên mỗi visibility (radiometer).
    Trả về u,v,w (T,B) và vis (T,B)."""
    u, v, w = compute_uvw(config.baseline_vectors_enu, obs)
    if sky['type'] == 'point':
        V = vis_point_sources(u, v, sky['sources'])
    elif sky['type'] == 'disk':
        V = vis_uniform_disk(u, v, sky.get('flux', 1.0), sky['diameter_rad'],
                             sky.get('l0', 0.0), sky.get('m0', 0.0))
    else:
        raise ValueError(sky['type'])
    if time_weight is not None:
        V = V * time_weight[:, None]
    if noise_std > 0:
        rng = np.random.default_rng(seed)
        V = V + noise_std * (rng.standard_normal(V.shape) + 1j * rng.standard_normal(V.shape))
    return u, v, w, V


# ════════════════════════════════════════════════════════════════════════════
# 7. IMAGER — dirty image + PSF (DFT trực tiếp, fringe-stop bằng w-term)
# ════════════════════════════════════════════════════════════════════════════
def make_dirty_image(u, v, w, vis, fov_deg=3.0, grid=256, do_fringe_stop=True,
                     block=8192, time_step=1, dtype=np.complex64):
    """Dirty image qua DFT trực tiếp + Hermitian, tính THEO KHỐI để RAM thấp.
    Tránh mảng trung gian chục GB của einsum 'k,kj,ki->ij' (nguyên nhân tràn
    pagefile ổ C). Trả về (image, l_deg, m_deg).
    do_fringe_stop=True: nhân exp(+2πi·w) để dồn nguồn (ở phase center) về (0,0)
      — cần cho chuỗi điện áp; forward model đã ở tâm nên đặt False.
    block      : số visibility xử lý mỗi khối (nhỏ hơn -> nhẹ RAM hơn).
    time_step  : >1 thì lấy thưa thời gian (trục 0) -> nhanh hơn cho lúc thử nghiệm.
    dtype      : complex64 (mặc định, nửa RAM) hoặc complex128 nếu cần chính xác hơn."""
    l = np.radians(np.linspace(-fov_deg / 2, fov_deg / 2, grid))   # East-West
    m = np.radians(np.linspace(-fov_deg / 2, fov_deg / 2, grid))   # North-South

    if time_step > 1:                                              # lấy thưa thời gian
        u = u[::time_step]; v = v[::time_step]
        w = w[::time_step]; vis = vis[::time_step]

    uf = u.ravel().astype(np.float64)
    vf = v.ravel().astype(np.float64)
    Vf = ((vis * np.exp(2j * np.pi * w)) if do_fringe_stop else vis).ravel().astype(dtype)

    # dirty[i,j] = Σ_k Vf[k]·exp(2πi·u_k·l_j)·exp(2πi·v_k·m_i)
    #            = exp_vm.T @ (Vf · exp_ul)  — nhân ma trận theo khối, KHÔNG tạo mảng (K×grid×grid)
    dirty = np.zeros((grid, grid), dtype=np.complex128)            # tích luỹ chính xác
    K = Vf.size
    for s in range(0, K, block):
        e = min(s + block, K)
        eu = np.exp(2j * np.pi * np.outer(uf[s:e], l)).astype(dtype)   # (blk, grid_l) ~ vài MB
        ev = np.exp(2j * np.pi * np.outer(vf[s:e], m)).astype(dtype)   # (blk, grid_m)
        dirty += (ev.T @ (Vf[s:e, None] * eu)).astype(np.complex128)

    img = 2.0 * np.real(dirty)
    peak = np.max(np.abs(img))
    if peak > 0:
        img = img / peak
    return img, np.degrees(l), np.degrees(m)


def synthesized_beam(u, v, w, fov_deg=3.0, grid=256, do_fringe_stop=True,
                     block=8192, time_step=1, dtype=np.complex64):
    """PSF = dirty image của nguồn điểm đơn vị tại tâm (đo hình dạng búp tổng hợp)."""
    ones = np.ones(u.shape, dtype=dtype)
    return make_dirty_image(u, v, w, ones, fov_deg, grid, do_fringe_stop,
                            block, time_step, dtype)


# ════════════════════════════════════════════════════════════════════════════
# 8. BUILDERS — dựng layout tuỳ ý + presets
# ════════════════════════════════════════════════════════════════════════════
def linear(n, spacing, az_deg=90.0, name=None):
    """Mảng thẳng n anten, bước spacing m, theo phương la bàn az (0=Bắc,90=Đông)."""
    az = np.radians(az_deg)
    r = np.arange(n) * spacing
    E, N = r * np.sin(az), r * np.cos(az)
    nm = name or f"linear_n{n}_d{spacing:g}_az{az_deg:g}"
    return ArrayConfig(nm, np.column_stack([E, N]))


def cross(n_arm, spacing, name=None):
    """Mảng chữ thập: một nhánh Đông-Tây + một nhánh Bắc-Nam, dùng chung tâm."""
    r = np.arange(1, n_arm + 1) * spacing
    pts = [(0.0, 0.0)]
    for d in r:
        pts += [(d, 0), (-d, 0), (0, d), (0, -d)]   # E,W,N,S
    nm = name or f"cross_arm{n_arm}_d{spacing:g}"
    return ArrayConfig(nm, np.array(pts))


def tee(n_ew, n_ns, spacing, name=None):
    """Mảng chữ T: nhánh Đông-Tây dài + nhánh Bắc lên (lấp v không đối xứng)."""
    pts = [(i * spacing, 0.0) for i in range(n_ew)]
    pts += [(0.0, j * spacing) for j in range(1, n_ns + 1)]
    nm = name or f"tee_{n_ew}x{n_ns}_d{spacing:g}"
    return ArrayConfig(nm, np.array(pts))


def random_2d(n, extent, seed=0, name=None):
    """n anten rải ngẫu nhiên trong ô vuông ±extent/2 m (u-v phủ kín, ít cách đều)."""
    rng = np.random.default_rng(seed)
    pts = (rng.random((n, 2)) - 0.5) * extent
    nm = name or f"random_n{n}_ext{extent:g}_s{seed}"
    return ArrayConfig(nm, pts)


def from_enu(positions_enu, name="custom"):
    """Vị trí tuỳ ý: mảng (N,2) hoặc (N,3) đơn vị mét."""
    return ArrayConfig(name, np.asarray(positions_enu, float))


# Hai CASE theo yêu cầu ----------------------------------------------------------
def preset_compact():
    """CASE 1 — bám dự án ngoài trời: mảng Đông-Tây 4 anten [0,5,10,15] m."""
    return linear(4, 5.0, az_deg=90.0, name="compact_outdoor_EW")


def preset_extended():
    """CASE 2 — tham vọng: chữ thập 2D khoảng cách tăng dần. Bao gồm cả baseline
    ngắn (5,15 m — nối với case ngoài trời) lẫn baseline > 65 m để phân giải cấu
    trúc đĩa Mặt Trời (null đầu tiên ~65 m ở 610 MHz). Không bị lỗ hổng tâm u-v."""
    r = np.array([5.0, 15.0, 35.0, 65.0])          # graded -> baseline 5..130 m
    pts = [(0.0, 0.0)]
    for d in r:
        pts += [(d, 0), (-d, 0), (0, d), (0, -d)]   # E,W,N,S
    return ArrayConfig("extended_graded_cross_2D", np.array(pts))


# ════════════════════════════════════════════════════════════════════════════
# 9. SWEEP SONG SONG — chạy nhiều layout cùng lúc, tận dụng nhiều nhân CPU
# ════════════════════════════════════════════════════════════════════════════
def _worker(args):
    config, obs, sky, time_weight, fov_deg, grid, noise_std, seed = args
    u, v, w, V = forward_visibilities(config, obs, sky, time_weight, noise_std, seed)
    img, l_deg, m_deg = make_dirty_image(u, v, w, V, fov_deg, grid, do_fringe_stop=False)
    psf, _, _ = synthesized_beam(u, v, w, fov_deg, grid, do_fringe_stop=False)
    return config.name, dict(image=img, psf=psf, u=u, v=v,
                             bl_max=float(config.baseline_lengths.max()),
                             l_deg=l_deg, m_deg=m_deg)


def sweep_layouts(configs, obs, sky, time_weight=None, fov_deg=3.0, grid=192,
                  noise_std=0.0, seed=0, n_workers=None):
    """Chạy forward-model + dirty image cho nhiều ArrayConfig song song.
    Trả về dict {name: {image, psf, u, v, bl_max, l_deg, m_deg}}."""
    jobs = [(cfg, obs, sky, time_weight, fov_deg, grid, noise_std, seed) for cfg in configs]
    out = {}
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        for name, res in ex.map(_worker, jobs):
            out[name] = res
    return out
