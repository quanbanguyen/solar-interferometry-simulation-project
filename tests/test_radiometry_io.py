import numpy as np
import pytest

import interfsim as ix
from interfsim.io import quantize_iq, read_hex, read_rstn_day, write_hex
from interfsim.nec import read_nec_pattern


def test_radiometry_values():
    lam = 299_792_458.0 / 610e6
    ae = ix.effective_area(9.48, lam)
    assert ae == pytest.approx(0.1705, rel=1e-3)
    p_n = ix.noise_power(150.0, 1e6)
    assert p_n == pytest.approx(2.0709735e-15)
    p_s = ix.source_power(100.0, ae, 1e6, pol_factor=0.5)
    assert p_s == pytest.approx(0.5 * 100e-22 * ae * 1e6)
    # SNR is a ratio of powers: no load resistance anywhere (thesis v1 multiplied by R_load)
    assert ix.snr_db(p_s, p_n) == pytest.approx(10 * np.log10(p_s / p_n))


def test_hex_round_trip(tmp_path):
    rng = np.random.default_rng(0)
    V = rng.normal(size=(200, 4)) + 1j * rng.normal(size=(200, 4))
    I, Q, scale = quantize_iq(V, bits=16)
    assert np.abs(I).max() <= 32767 and np.abs(Q).max() <= 32767
    write_hex(tmp_path / "s.txt", I, Q)
    I2, Q2 = read_hex(tmp_path / "s.txt")
    assert np.array_equal(I, I2) and np.array_equal(Q, Q2)
    assert np.abs((I + 1j * Q) / scale - V).max() < 1.0 / scale


def test_rstn_reader(tmp_path):
    p = tmp_path / "20-3-2025.txt"
    p.write_text("000000 000014 000041 000069 000137 000179 000198 000259 005024\n"
                 "000001 ////// ////// ////// ////// ////// ////// ////// //////\n"
                 "101639 000030 000039 000062 000111 000143 000159 000229 000507\n")
    d = read_rstn_day(p)
    assert d.date == np.datetime64("2025-03-20")
    assert d.ut[2] == np.datetime64("2025-03-20T10:16:39")
    assert d.channel(610)[0] == 69 and np.isnan(d.channel("F610")[1])
    assert d.valid.tolist() == [True, False, True]


def test_nec_parser_and_negative_theta_beam(tmp_path):
    """4NEC2 scans with negative theta: the beam peak must land on the +y boom axis."""
    rows = []
    for th in range(-180, 1, 10):
        for ph in range(0, 361, 30):
            t, p = np.radians(th), np.radians(ph)
            y = np.sin(t) * np.sin(p)           # NEC direction cosine along +y
            g = 10 * np.log10(max(y, 0) ** 4 + 1e-3) + 9
            rows.append(f"{th:8.2f} {ph:8.2f} {g:8.2f} -999.99 {g:8.2f} 0 0 LINEAR 1 0 0 0")
    text = ("  FREQUENCY= 6.1000E+02 MHZ\n - - - RADIATION PATTERNS - - -\n header\n"
            + "\n".join(rows) + "\n\n AVERAGE POWER GAIN= 1.0\n")
    f = tmp_path / "ant.out"
    f.write_text(text)
    pat = read_nec_pattern(f)
    assert pat.freq_MHz == 610.0 and pat.gain_total_dBi.shape == (19, 13)
    b = ix.TabulatedBeam.from_nec_out(f, ix.Mount("+y", "+x", pointing_el_deg=90))
    assert b.peak_theta_phi == (90.0, 90.0)
    assert b.boresight_power() == pytest.approx(1.0)
    assert b.power_altaz(0, 0) < 0.05           # horizon is far off the boresight


@pytest.mark.skipif(not ix.beam.default_beam_path().exists(), reason="beam data not present")
def test_shipped_beam_points_to_zenith():
    b = ix.load_beam(ix.beam.default_beam_path())
    assert b.gain_max_dBi == pytest.approx(9.48)
    assert b.boresight_power() == pytest.approx(1.0)
    # elements N-S: the E-W (H-plane) cut is broader than the N-S (E-plane) cut
    assert b.power_altaz(90, 50) > b.power_altaz(0, 50)
