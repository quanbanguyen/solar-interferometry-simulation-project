# =====================================================================
#  CELL X  —  XUẤT ẢNH RIÊNG LẺ CHO BÁO CÁO (thesis figure export)
#
#  ĐẶT CELL NÀY: sau Cell H (Case 2), trước Cell I (Sweep)
#  LÝ DO: Cell I ghi đè u, v, w, img, psf trong vòng lặp sweep
#
#  Kết quả: các file .png trong  IMG_DIR/thesis_figures/
#  Bước tiếp: copy toàn bộ vào  d:\datn\figures\
# =====================================================================

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from scipy.ndimage import convolve as nd_convolve
from scipy.special import j1
import os, shutil

plt.rcParams.update({
    'font.size': 10, 'axes.titlesize': 10, 'axes.labelsize': 9,
    'xtick.labelsize': 8, 'ytick.labelsize': 8,
    'figure.dpi': 150,
})

# ── Thư mục đầu ra ────────────────────────────────────────────────────
THESIS_FIG_DIR = os.path.join(IMG_DIR, "thesis_figures")
os.makedirs(THESIS_FIG_DIR, exist_ok=True)

def _save(name):
    p = os.path.join(THESIS_FIG_DIR, name)
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close('all')
    print(f"  [OK] {name}")

# Hằng dùng chung
theta_c = np.linspace(0, 2*np.pi, 300)
sun_r   = 16.0   # bán kính Mặt Trời ~ 16 arcmin

print("=" * 55)
print("Cell X: Bắt đầu xuất ảnh riêng lẻ cho báo cáo")
print("=" * 55)

# ══════════════════════════════════════════════════════════════════════
# [1]  fig_sws_flux_day
#      Thông lượng Learmonth 610 MHz theo thời gian
#      Nguồn: sfu_data (Cell A)
# ══════════════════════════════════════════════════════════════════════
t_h = np.linspace(0, 12, len(sfu_data))

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(t_h, sfu_data, color='darkorange', lw=0.9)
ax.set_xlabel("Time from transit window start  (hours)")
ax.set_ylabel("Solar flux density  (SFU)")
ax.set_title("Learmonth Solar Observatory — 610 MHz flux, 20 March 2025")
ax.grid(True, alpha=0.3, ls='--')
fig.tight_layout()
_save("fig_sws_flux_day.png")

# ══════════════════════════════════════════════════════════════════════
# [2]  fig_voltage_env
#      Envelope RMS điện áp anten (bell curve + noise floor)
#      Nguồn: V_matrix (Cell C), V_noise, T_sys (Cell A / Cell 0)
#      NOTE: ch4_pipeline.tex đã được sửa sang {fig_voltage_env}
# ══════════════════════════════════════════════════════════════════════
WINDOW = 500
def _srms(x, w):
    x2 = np.abs(x)**2
    cs = np.concatenate([[0], np.cumsum(x2)])
    r  = np.sqrt((cs[w:] - cs[:-w]) / w)
    return np.concatenate([np.full(w-1, r[0]), r])

V_env_uV   = _srms(V_matrix[:, 0], WINDOW) * 1e6
V_noise_uV = V_noise * 1e6

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.fill_between(t_h, V_env_uV, alpha=0.18, color='royalblue')
ax.plot(t_h, V_env_uV, color='royalblue', lw=1.0,
        label='RMS envelope  (Ant 1, 500-sample window)')
ax.axhline(V_noise_uV, color='red', lw=1.3, ls='--',
           label=f'Johnson–Nyquist noise floor  ({V_noise_uV:.3f} µV,  '
                 f'T_sys = {T_sys} K)')
ax.set_xlabel("Time from transit window start  (hours)")
ax.set_ylabel("RMS voltage  (µV)")
ax.set_title("Per-antenna signal amplitude — 500-sample sliding RMS,  20 March 2025")
ax.legend(fontsize=8.5)
ax.grid(True, alpha=0.3, ls='--')
fig.tight_layout()
_save("fig_voltage_env.png")

# ══════════════════════════════════════════════════════════════════════
# [3]  fig_fringe_pattern
#      Fringe thực sự: Re(V₀₁) theo thời gian → chu kỳ ~14 phút (8m @ 610 MHz, δ=0°)
#      Nguồn: visibilities, IDX_01 (Cell E)
# ══════════════════════════════════════════════════════════════════════
t_vis       = np.linspace(0, 12, NI)
fringe_real = np.real(visibilities[:, IDX_01])

fig, axes = plt.subplots(2, 1, figsize=(9, 5.5),
                          gridspec_kw={'height_ratios': [1, 2], 'hspace': 0.42})

# Panel trên: toàn transit 12h
axes[0].plot(t_vis, fringe_real, color='royalblue', lw=0.5, alpha=0.8)
axes[0].set_ylabel("Re(V₀₁)  (V²)")
axes[0].set_title(f"Interference fringe — {bl_labels[IDX_01]},  "
                  f"20 March 2025  (δ = 0°, 12-h transit)")
axes[0].grid(True, alpha=0.3, ls='--')

# Panel dưới: zoom 2h quanh transit để thấy rõ chu kỳ
mask  = (t_vis >= 5.0) & (t_vis <= 7.0)
t_min = (t_vis[mask] - 6.0) * 60   # phút lệch so với đỉnh transit

axes[1].plot(t_min, fringe_real[mask], color='royalblue', lw=1.0)
axes[1].set_xlabel("Time relative to transit peak  (minutes)")
axes[1].set_ylabel("Re(V₀₁)  (V²)")
axes[1].set_title("Zoom: ±60 min around transit  →  fringe period ≈ 14 min  (B=8 m, f=610 MHz)")
axes[1].grid(True, alpha=0.3, ls='--')

fig.tight_layout()
_save("fig_fringe_pattern.png")

# ══════════════════════════════════════════════════════════════════════
# [4]  fig_uv_coverage
#      UV plane của compact EW array (Case 1)
#      Nguồn: u, v (Cell F)  — phải chạy trước Cell I
# ══════════════════════════════════════════════════════════════════════
cmap_bl = plt.cm.tab10(np.linspace(0, 0.9, NB))

fig, ax = plt.subplots(figsize=(8.5, 4.0))
for b in range(NB):
    kw = dict(s=1.5, color=cmap_bl[b], label=bl_labels[b])
    ax.scatter( u[:, b],  v[:, b], **kw)
    ax.scatter(-u[:, b], -v[:, b], s=1.5, color=cmap_bl[b])
ax.set_xlabel("u  (wavelengths λ)")
ax.set_ylabel("v  (wavelengths λ)")
ax.set_title("UV coverage — compact E–W array (Case 1)\n"
             "20 March 2025,  H ∈ [±90°]  (δ = 0° → v ≡ 0,  EW array has no N–S resolution)")
# With δ=0° and a purely EW array, v = B·sin(δ)·cos(H) = 0 for all baselines.
# set_aspect('equal') on degenerate v=0 data causes LinAlgError in tight_layout.
_u_max = float(np.abs(u).max()) * 1.08
ax.set_xlim(-_u_max, _u_max)
ax.set_ylim(-_u_max * 0.12, _u_max * 0.12)
ax.grid(True, alpha=0.3, ls='--')
ax.legend(markerscale=6, fontsize=8, loc='upper right')
fig.tight_layout()
_save("fig_uv_coverage.png")

# ══════════════════════════════════════════════════════════════════════
# [5]  fig_visibility_jinc
#      |V| vs baseline + jinc lý thuyết (Case 2, extended array)
#      Nguồn: case2_data.npz (Cell H)
# ══════════════════════════════════════════════════════════════════════
npz_path2 = os.path.join(IMG_DIR, "case2_forward_model", "case2_data.npz")
if os.path.exists(npz_path2):
    d2   = np.load(npz_path2)
    u2_  = d2['u2']; v2_ = d2['v2']; V2_ = d2['V2']
    NI2  = V2_.shape[0]; t2 = NI2 // 2
    bl2  = np.sqrt(u2_[t2]**2 + v2_[t2]**2)     # baseline (λ) tại transit
    va2  = np.abs(V2_[t2]); va2 = va2 / va2.max()

    theta_s = np.radians(0.53)   # đường kính đĩa Mặt Trời
    b_fine  = np.linspace(0.5, bl2.max() * 1.05, 700)
    x_j     = np.pi * b_fine * theta_s
    jinc_   = np.abs(2 * j1(x_j) / x_j)
    b_null  = 1.22 / theta_s   # first null ≈ 132 λ

    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.scatter(bl2, va2, s=6, color='royalblue', zorder=3,
               label='Simulated |V|  (forward model, Case 2)')
    ax.plot(b_fine, jinc_, color='darkorange', lw=1.8,
            label='Analytic jinc  (uniform disk, 0.53°)')
    ax.axvline(b_null, color='red', ls='--', lw=1.2,
               label=f'First null ≈ {b_null:.0f} λ  (≈ 65 m at 610 MHz)')
    ax.set_xlabel("Baseline length  (wavelengths λ)")
    ax.set_ylabel("Normalised visibility amplitude  |V(b)|")
    ax.set_title("Van Cittert–Zernike validation: visibility amplitude vs. baseline,  "
                 "20 March 2025")
    ax.legend(fontsize=8.5)
    ax.grid(True, alpha=0.3, ls='--')
    fig.tight_layout()
    _save("fig_visibility_jinc.png")
    del u2_, v2_, V2_
else:
    print("  [SKIP] fig_visibility_jinc — chạy Cell H trước (case2_data.npz chưa có)")

# ══════════════════════════════════════════════════════════════════════
# [6]  fig_dirty_image  —  Dirty image Case 1 riêng lẻ
#      Nguồn: img, l_arcmin, m_arcmin (Cell G)
# ══════════════════════════════════════════════════════════════════════
ext1     = [l_arcmin[0], l_arcmin[-1], m_arcmin[0], m_arcmin[-1]]
img_norm = img / img.max()

fig, ax = plt.subplots(figsize=(5.5, 5.2))
im = ax.imshow(img_norm, extent=ext1, origin='lower', cmap='hot',
               vmin=0, vmax=1, aspect='equal')
ax.plot(sun_r*np.cos(theta_c), sun_r*np.sin(theta_c),
        'c--', lw=1.5, label="Solar disk  (32′ diam.)")
ax.set_xlabel("East–West offset  (arcmin)")
ax.set_ylabel("North–South offset  (arcmin)")
ax.set_title("Dirty image — compact E–W array (Case 1),  20 March 2025")
ax.legend(fontsize=8, loc='upper right')
plt.colorbar(im, ax=ax, shrink=0.88, label='Normalised intensity')
fig.tight_layout()
_save("fig_dirty_image.png")

# ══════════════════════════════════════════════════════════════════════
# [7]  fig_dirty_beam  —  PSF Case 1 riêng lẻ
#      Nguồn: psf, fwhm_ew, fwhm_ns (Cell G)
# ══════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(5.5, 5.2))
im = ax.imshow(psf, extent=ext1, origin='lower', cmap='RdBu_r',
               vmin=-0.5, vmax=1, aspect='equal')
ax.plot([-fwhm_ew/2, fwhm_ew/2], [0, 0], 'y-', lw=2.5,
        label=f"FWHM E–W = {fwhm_ew:.1f}′")
ax.plot([0, 0], [-fwhm_ns/2, fwhm_ns/2], 'c-', lw=2.5,
        label=f"FWHM N–S = {fwhm_ns:.1f}′")
ax.set_xlabel("East–West offset  (arcmin)")
ax.set_ylabel("North–South offset  (arcmin)")
ax.set_title("Synthesised dirty beam (PSF) — compact E–W array (Case 1)")
ax.legend(fontsize=8, loc='upper right')
plt.colorbar(im, ax=ax, shrink=0.88, label='Normalised PSF')
fig.tight_layout()
_save("fig_dirty_beam.png")

# ══════════════════════════════════════════════════════════════════════
# [8]  fig_sky_conv_psf  —  3 panel: sky model | sky*PSF | dirty image
#      Validate: ảnh (c) phải giống (b) đến mức pixel
#      Nguồn: img, psf, l_arcmin, m_arcmin (Cell G)
# ══════════════════════════════════════════════════════════════════════
lg, mg   = np.meshgrid(l_arcmin, m_arcmin)
sky_mdl  = (np.sqrt(lg**2 + mg**2) <= sun_r).astype(float)
psf_n    = psf / (psf.sum() + 1e-30)
sky_conv = nd_convolve(sky_mdl, psf_n, mode='wrap')
sky_conv = sky_conv / sky_conv.max()

fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5))
kw_im = dict(extent=ext1, origin='lower', cmap='hot', vmin=0, vmax=1, aspect='equal')
for ax_, data, title in zip(
    axes,
    [sky_mdl,   sky_conv,   img_norm],
    ["(a)  True sky model\n(uniform disk, 32′ diam.)",
     "(b)  Sky ∗ PSF\n(independently computed)",
     "(c)  Dirty image from DFT\n(Eq. dirty-dft)"],
):
    im_ = ax_.imshow(data, **kw_im)
    ax_.set_title(title, fontsize=9.5)
    ax_.set_xlabel("E–W  (arcmin)", fontsize=8.5)
    ax_.set_ylabel("N–S  (arcmin)", fontsize=8.5)
    plt.colorbar(im_, ax=ax_, shrink=0.82, label='Norm. intensity')

fig.suptitle("Imaging validation: dirty image = sky ∗ PSF  "
             "(Case 1, compact E–W array)", fontsize=10.5)
fig.tight_layout()
_save("fig_sky_conv_psf.png")

# ══════════════════════════════════════════════════════════════════════
# [9]  fig_dirty_from_dft  —  Case 1.5 CROSS: 4 panel
#      Nguồn: img_c, psf_c, la, ma, fwhm_ew_c, fwhm_ns_c (Cell G2)
# ══════════════════════════════════════════════════════════════════════
ext_c     = [la[0], la[-1], ma[0], ma[-1]]
ic_c      = np.argmin(np.abs(la))
ir_c      = np.argmin(np.abs(ma))
img_c_n   = img_c / img_c.max()

fig = plt.figure(figsize=(11, 9))
gs  = gridspec.GridSpec(2, 2, hspace=0.40, wspace=0.32)

# (a) dirty image
ax1 = fig.add_subplot(gs[0, 0])
im1 = ax1.imshow(img_c_n, extent=ext_c, origin='lower', cmap='hot',
                 vmin=0, vmax=1, aspect='equal')
ax1.plot(sun_r*np.cos(theta_c), sun_r*np.sin(theta_c), 'c--', lw=1.3)
ax1.set_title("(a)  Dirty image — cross layout (Case 1.5)")
ax1.set_xlabel("E–W  (arcmin)"); ax1.set_ylabel("N–S  (arcmin)")
plt.colorbar(im1, ax=ax1, shrink=0.87)

# (b) PSF
ax2 = fig.add_subplot(gs[0, 1])
im2 = ax2.imshow(psf_c, extent=ext_c, origin='lower', cmap='RdBu_r',
                 vmin=-0.5, vmax=1, aspect='equal')
ax2.plot([-fwhm_ew_c/2, fwhm_ew_c/2], [0, 0], 'y-', lw=2.2,
         label=f"FWHM E–W = {fwhm_ew_c:.1f}′")
ax2.plot([0, 0], [-fwhm_ns_c/2, fwhm_ns_c/2], 'c-', lw=2.2,
         label=f"FWHM N–S = {fwhm_ns_c:.1f}′")
ax2.set_title(f"(b)  PSF — cross 4-ant")
ax2.set_xlabel("E–W  (arcmin)"); ax2.set_ylabel("N–S  (arcmin)")
ax2.legend(fontsize=7.5)
plt.colorbar(im2, ax=ax2, shrink=0.87)

# (c) E–W 1D cut
ax3 = fig.add_subplot(gs[1, 0])
ax3.plot(la, img_c_n[ir_c, :], color='darkorange', lw=1.8, label='Dirty image')
ax3.plot(la, psf_c[ir_c, :],   color='gray',       lw=1.2, ls='--', label='PSF')
ax3.axhline(0.5, color='gold', ls=':', lw=1, label=f"FWHM = {fwhm_ew_c:.1f}′")
ax3.set_xlabel("E–W offset  (arcmin)")
ax3.set_ylabel("Normalised intensity")
ax3.set_title("(c)  E–W profile through centre")
ax3.legend(fontsize=8); ax3.grid(True, alpha=0.3, ls='--')

# (d) N–S 1D cut
ax4 = fig.add_subplot(gs[1, 1])
ax4.plot(ma, img_c_n[:, ic_c], color='royalblue', lw=1.8, label='Dirty image')
ax4.plot(ma, psf_c[:, ic_c],   color='gray',      lw=1.2, ls='--', label='PSF')
ax4.axhline(0.5, color='cyan', ls=':', lw=1, label=f"FWHM = {fwhm_ns_c:.1f}′")
ax4.set_xlabel("N–S offset  (arcmin)")
ax4.set_ylabel("Normalised intensity")
ax4.set_title("(d)  N–S profile through centre")
ax4.legend(fontsize=8); ax4.grid(True, alpha=0.3, ls='--')

fig.suptitle(
    f"Case 1.5 — Cross 4-antenna layout (2D coverage)\n"
    f"N–S FWHM: {fwhm_ns:.1f}′ (Case 1, E–W only)  →  {fwhm_ns_c:.1f}′ "
    f"(Case 1.5, cross)  [{fwhm_ns/fwhm_ns_c:.1f}× improvement]",
    fontsize=10
)
_save("fig_dirty_from_dft.png")

# ══════════════════════════════════════════════════════════════════════
# [10] fig_case2_image  —  Dirty image Case 2 (extended graded-cross)
#      Nguồn: case2_data.npz (Cell H) — img2 đã bị xoá trong Cell H
# ══════════════════════════════════════════════════════════════════════
if os.path.exists(npz_path2):
    d2_   = np.load(npz_path2)
    img2_ = d2_['img2']
    l2_a  = d2_['l2_deg'] * 60
    m2_a  = d2_['m2_deg'] * 60
    ext2  = [l2_a[0], l2_a[-1], m2_a[0], m2_a[-1]]

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    im = ax.imshow(img2_ / img2_.max(), extent=ext2, origin='lower', cmap='hot',
                   vmin=0, vmax=1, aspect='equal')
    ax.plot(sun_r*np.cos(theta_c), sun_r*np.sin(theta_c),
            'c--', lw=1.5, label="Solar disk  (32′ diam.)")
    ax.set_xlabel("East–West offset  (arcmin)")
    ax.set_ylabel("North–South offset  (arcmin)")
    ax.set_title("Dirty image — extended graded-cross (Case 2)\n"
                 "b_max = 130 m,  forward model,  610 MHz")
    ax.legend(fontsize=8, loc='upper right')
    plt.colorbar(im, ax=ax, shrink=0.88, label='Normalised intensity')
    fig.tight_layout()
    _save("fig_case2_image.png")
    del img2_
else:
    print("  [SKIP] fig_case2_image — chạy Cell H trước")

# ══════════════════════════════════════════════════════════════════════
# [11] fig_layout_sweep  —  copy _montage.png từ Cell I
#      Cell I phải chạy SAU cell này
# ══════════════════════════════════════════════════════════════════════
montage_src = os.path.join(IMG_DIR, "sweep_layouts", "_montage.png")
montage_dst = os.path.join(THESIS_FIG_DIR, "fig_layout_sweep.png")
if os.path.exists(montage_src):
    shutil.copy2(montage_src, montage_dst)
    print(f"  [OK] fig_layout_sweep.png  (copied from Cell I montage)")
else:
    print(f"  [SKIP] fig_layout_sweep — chạy Cell I trước, rồi chạy lại dòng copy này")

# ══════════════════════════════════════════════════════════════════════
print()
print("=" * 55)
print(f"Hoàn tất! Ảnh đã lưu tại:")
print(f"  {THESIS_FIG_DIR}")
print()
print("Bước tiếp theo:")
print("  1. Kiểm tra các hình trong thư mục trên")
print("  2. Copy tất cả .png vào  d:\\datn\\figures\\")
print("  3. Biên dịch lại báo cáo (Ctrl+Alt+B)")
print("=" * 55)
