# -*- coding: utf-8 -*-

# This file is a part of IoT-LAB oml-plot-tools
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

"""Tests for radio.py."""

import unittest
from unittest import mock

from .. import radio
from .common import (
    IS_PYTHON_3_10,
    assert_called_with_nparray,
    fixture_path,
    utest_help_as_doc,
    utest_plot_and_compare,
)


class TestRadioOmlPlot(unittest.TestCase):
    """Tests for radio OML plot functions."""

    def setUp(self):
        """Set up radio OML data for plot tests."""
        radio_file = fixture_path("examples", "radio.oml")
        self.data = radio.oml_load(radio_file)
        self.title = ""

    def test_plot_all(self):
        """Test plotting all radio data."""
        ref_img = fixture_path("examples", "radio_single.png")
        radio.oml_plot_rssi(self.data, self.title)
        utest_plot_and_compare(self, ref_img, 100)

    def test_plot_current(self):
        """Test plotting RSSI data for each channel separately."""
        # multiple images are printed but only last one is kept
        ref_img = fixture_path("examples", "radio_separated_last.png")
        radio.oml_plot_rssi(self.data, self.title, separated=True)
        utest_plot_and_compare(self, ref_img, 50)

    def test_plot_clock(self):
        """Test plotting OML clock data for radio."""
        ref_img = fixture_path("examples", "radio_clock.png")
        radio.common.oml_plot_clock(self.data)
        utest_plot_and_compare(self, ref_img, 50)


class TestRadioPlot(unittest.TestCase):
    """Tests for radio_plot function with different plot selections."""

    def setUp(self):
        """Set up test OML data and arguments for radio_plot tests."""
        meas_file = fixture_path("examples", "radio.oml")
        self.data = radio.oml_load(meas_file)[0:1]

        self.title = "TITLE_TESTS"
        self.args = [
            "plot_oml_radio",
            "-i",
            meas_file,
            "--begin",
            "0",
            "--end",
            "1",
            "-l",
            self.title,
        ]

        self.oml_plot_rssi = mock.patch("oml_plot_tools.radio.oml_plot_rssi").start()
        self.oml_plot_clock = mock.patch(
            "oml_plot_tools.radio.common.oml_plot_clock"
        ).start()

    def tearDown(self):
        """Stop all mocks after each test."""
        mock.patch.stopall()

    def radio_main(self, *args):
        """Call radio main with given additional args."""
        with mock.patch("sys.argv", list(self.args) + list(args)):
            radio.main()

    def test_plot_joined(self):
        """Test radio_plot with joined channels selection."""
        self.radio_main("--all")
        assert_called_with_nparray(self.oml_plot_rssi, self.data, self.title)

    def test_plot_separated(self):
        """Test radio_plot with separated channels selection."""
        self.radio_main("--plot")
        assert_called_with_nparray(
            self.oml_plot_rssi, self.data, self.title, separated=True
        )

    def test_plot_time(self):
        """Test radio_plot with time verification selection."""
        self.radio_main("--time")
        assert_called_with_nparray(self.oml_plot_clock, self.data)

    def test_plot_default_joined(self):
        """Test radio_plot default selection is joined channels."""
        self.radio_main()
        assert_called_with_nparray(self.oml_plot_rssi, self.data, self.title)


class TestRadioHelpers(unittest.TestCase):
    """Tests for radio helper functions like list_channels and with_channel."""

    def setUp(self):
        """Set up test OML data for radio helper function tests."""
        radio_file = fixture_path("examples", "radio.oml")
        self.data = radio.oml_load(radio_file)

    def test_list_channels(self):
        """Test listing channels from radio OML data."""
        channels = radio.list_channels(self.data)
        self.assertIsInstance(channels, list)
        self.assertEqual(channels, sorted(channels))

    def test_with_channel(self):
        """Test filtering radio OML data by specific channel."""
        channels = radio.list_channels(self.data)
        if channels:
            subset = radio.with_channel(self.data, channels[0])
            self.assertTrue(all(subset["channel"] == channels[0]))

    def test_radio_plot_joined(self):
        """Test with joined channels selection calls correct plotting function."""
        with mock.patch("oml_plot_tools.radio.oml_plot_rssi") as mock_rssi:
            with mock.patch("oml_plot_tools.radio.common.plot_show"):
                radio.radio_plot(self.data, "Title", ["joined"])
                mock_rssi.assert_called_once_with(self.data, "Title")

    def test_radio_plot_separated(self):
        """Test with separated channels selection calls correct plotting function."""
        with mock.patch("oml_plot_tools.radio.oml_plot_rssi") as mock_rssi:
            with mock.patch("oml_plot_tools.radio.common.plot_show"):
                radio.radio_plot(self.data, "Title", ["separated"])
                mock_rssi.assert_called_once_with(self.data, "Title", separated=True)

    def test_radio_plot_time(self):
        """Test with time verification selection calls correct plotting function."""
        with mock.patch("oml_plot_tools.radio.common.oml_plot_clock") as mock_clock:
            with mock.patch("oml_plot_tools.radio.common.plot_show"):
                radio.radio_plot(self.data, "Title", ["time"])
                self.assertTrue(mock_clock.called)


class TestDoc(unittest.TestCase):
    """Tests that module help matches its docstring."""

    @unittest.skipIf(IS_PYTHON_3_10, "Python 3.10 not supported")
    def test_doc(self):
        """Test that the module help output matches its docstring."""
        utest_help_as_doc(self, radio)
