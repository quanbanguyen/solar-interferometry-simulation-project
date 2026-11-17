#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# GNU Radio version: v3.9.2.0-85-g08bb05c1

from distutils.version import StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

from datetime import datetime
from gnuradio import blocks
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import dlite_epy_block_0 as epy_block_0  # embedded python block
import dlite_epy_block_0_0 as epy_block_0_0  # embedded python block
import dlite_epy_block_0_0_0 as epy_block_0_0_0  # embedded python block
import dlite_epy_block_1_0 as epy_block_1_0  # embedded python block
import sdrplay3



from gnuradio import qtgui

class dlite(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Not titled yet")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "dlite")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Variables
        ##################################################
        self.vector_length = vector_length = 512
        self.timenow = timenow = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.samp_rate = samp_rate = 8000000
        self.path = path = 'E:/ĐATN/data/'
        self.frequency = frequency = 35000000
        self.Datetime = Datetime = datetime.now().strftime("%Y_%m_%d")

        ##################################################
        # Blocks
        ##################################################
        self.sdrplay3_rspdx_0 = sdrplay3.rspdx(
            "",
            stream_args=sdrplay3.stream_args(
                output_type='fc32',
                channels_size=1
            ),
        )
        self.sdrplay3_rspdx_0.set_sample_rate(samp_rate)
        self.sdrplay3_rspdx_0.set_center_freq(frequency)
        self.sdrplay3_rspdx_0.set_bandwidth(8000e3)
        self.sdrplay3_rspdx_0.set_antenna("Antenna B")
        self.sdrplay3_rspdx_0.set_gain_mode(False)
        self.sdrplay3_rspdx_0.set_gain(-40, "IF")
        self.sdrplay3_rspdx_0.set_gain(-4, "RF")
        self.sdrplay3_rspdx_0.set_freq_corr(0)
        self.sdrplay3_rspdx_0.set_dc_offset_mode(False)
        self.sdrplay3_rspdx_0.set_iq_balance_mode(False)
        self.sdrplay3_rspdx_0.set_agc_setpoint(-30)
        self.sdrplay3_rspdx_0.set_hdr_mode(False)
        self.sdrplay3_rspdx_0.set_rf_notch_filter(True)
        self.sdrplay3_rspdx_0.set_dab_notch_filter(True)
        self.sdrplay3_rspdx_0.set_biasT(True)
        self.sdrplay3_rspdx_0.set_debug_mode(True)
        self.sdrplay3_rspdx_0.set_sample_sequence_gaps_check(False)
        self.sdrplay3_rspdx_0.set_show_gain_changes(False)
        self.fft_vxx_0 = fft.fft_vcc(vector_length, True, window.blackmanharris(vector_length), True, 1)
        self.epy_block_1_0 = epy_block_1_0.csv_filesink(vec_length=vector_length, samp_rate=samp_rate, freq=frequency, prefix=path, save_toggle="True", integration_select=0, short_long_time_scale=0, az="", elev="", location="")
        self.epy_block_0_0_0 = epy_block_0_0_0.integration(vec_length=vector_length, n_integrations=10)
        self.epy_block_0_0 = epy_block_0_0.integration(vec_length=vector_length, n_integrations=32)
        self.epy_block_0 = epy_block_0.integration(vec_length=vector_length, n_integrations=vector_length)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, vector_length)
        self.blocks_nlog10_ff_0 = blocks.nlog10_ff(10, vector_length, 0)
        self.blocks_multiply_conjugate_cc_0 = blocks.multiply_conjugate_cc(vector_length)
        self.blocks_complex_to_real_0 = blocks.complex_to_real(vector_length)



        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_real_0, 0), (self.blocks_nlog10_ff_0, 0))
        self.connect((self.blocks_multiply_conjugate_cc_0, 0), (self.blocks_complex_to_real_0, 0))
        self.connect((self.blocks_nlog10_ff_0, 0), (self.epy_block_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.epy_block_0, 0), (self.epy_block_0_0, 0))
        self.connect((self.epy_block_0_0, 0), (self.epy_block_0_0_0, 0))
        self.connect((self.epy_block_0_0_0, 0), (self.epy_block_1_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_conjugate_cc_0, 1))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_conjugate_cc_0, 0))
        self.connect((self.sdrplay3_rspdx_0, 0), (self.blocks_stream_to_vector_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "dlite")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_vector_length(self):
        return self.vector_length

    def set_vector_length(self, vector_length):
        self.vector_length = vector_length
        self.epy_block_0.n_integrations = self.vector_length
        self.epy_block_0.vec_length = self.vector_length
        self.epy_block_0_0.vec_length = self.vector_length
        self.epy_block_0_0_0.vec_length = self.vector_length
        self.epy_block_1_0.vec_length = self.vector_length

    def get_timenow(self):
        return self.timenow

    def set_timenow(self, timenow):
        self.timenow = timenow

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.epy_block_1_0.samp_rate = self.samp_rate
        self.sdrplay3_rspdx_0.set_sample_rate(self.samp_rate)

    def get_path(self):
        return self.path

    def set_path(self, path):
        self.path = path
        self.epy_block_1_0.prefix = self.path

    def get_frequency(self):
        return self.frequency

    def set_frequency(self, frequency):
        self.frequency = frequency
        self.epy_block_1_0.freq = self.frequency
        self.sdrplay3_rspdx_0.set_center_freq(self.frequency)

    def get_Datetime(self):
        return self.Datetime

    def set_Datetime(self, Datetime):
        self.Datetime = Datetime




def main(top_block_cls=dlite, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
