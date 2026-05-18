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

"""Tests for consum.py."""

import unittest
from unittest import mock

from .. import common, consum
from .common import (
    IS_PYTHON_3_10,
    assert_called_with_nparray,
    fixture_path,
    utest_help_as_doc,
    utest_plot_and_compare,
)


class TestConsumptionOmlPlot(unittest.TestCase):
    """Tests for consumption OML plot functions."""

    def setUp(self):
        """Set up consumption OML data for plot tests."""
        conso_file = fixture_path("examples", "consumption.oml")
        self.data = consum.oml_load(conso_file)
        self.title = "Node"

    def test_plot_all(self):
        """Test plotting all consumption measures."""
        ref_img = fixture_path("examples", "consumption_all.png")
        consum.oml_plot(self.data, self.title, consum.MEASURES_D.values())
        utest_plot_and_compare(self, ref_img, 150)

    def test_plot_current(self):
        """Test plotting current consumption measure only."""
        ref_img = fixture_path("examples", "consumption_current.png")
        consum.oml_plot(self.data, self.title, [consum.MEASURES_D["current"]])
        utest_plot_and_compare(self, ref_img, 100)

    def test_plot_clock(self):
        """Test plotting OML clock data for consumption."""
        ref_img = fixture_path("examples", "consumption_clock.png")
        consum.common.oml_plot_clock(self.data)
        utest_plot_and_compare(self, ref_img, 50)


class TestConsumptionPlot(unittest.TestCase):
    """Tests for consumption main CLI entry point."""

    def setUp(self):
        """Set up mocks and test arguments for consumption main tests."""
        meas_file = fixture_path("examples", "consumption.oml")
        self.data = consum.oml_load(meas_file)[0:1]

        self.title = "TITLE_TESTS"
        self.args = [
            "plot_oml_consum",
            "-i",
            meas_file,
            "--begin",
            "0",
            "--end",
            "1",
            "-l",
            self.title,
        ]

        self.oml_plot = mock.patch("oml_plot_tools.consum.oml_plot").start()
        self.oml_plot_clock = mock.patch(
            "oml_plot_tools.consum.common.oml_plot_clock"
        ).start()

    def tearDown(self):
        """Stop all active patches after each test."""
        mock.patch.stopall()

    def consum_main(self, *args):
        """Call consumption main with given additional args."""
        with mock.patch("sys.argv", list(self.args) + list(args)):
            consum.main()

    def test_plot_selection(self):
        """Test individual measure selection options -p, -v, -c."""
        self.consum_main("-p")
        assert_called_with_nparray(
            self.oml_plot,
            self.data,
            self.title,
            [common.MeasureTuple("power", float, "Power (W)")],
        )

        self.consum_main("-v")
        assert_called_with_nparray(
            self.oml_plot,
            self.data,
            self.title,
            [common.MeasureTuple("voltage", float, "Voltage (V)")],
        )

        self.consum_main("-c")
        assert_called_with_nparray(
            self.oml_plot,
            self.data,
            self.title,
            [common.MeasureTuple("current", float, "Current (A)")],
        )

        self.oml_plot.reset_mock()
        self.consum_main("-c", "-v", "-p", "-p")
        self.assertEqual(self.oml_plot.call_count, 3)

    def test_plot_all(self):
        """Test -a option calls oml_plot with all measures."""
        self.consum_main("-a")
        assert_called_with_nparray(
            self.oml_plot, self.data, self.title, consum.MEASURES_D.values()
        )

    def test_plot_default_all(self):
        """Test that no measure option defaults to plotting all measures."""
        self.consum_main()
        assert_called_with_nparray(
            self.oml_plot, self.data, self.title, consum.MEASURES_D.values()
        )

    def test_plot_time(self):
        """Test -t option calls oml_plot_clock with consumption data."""
        self.consum_main("-t")
        assert_called_with_nparray(self.oml_plot_clock, self.data)


class TestConsumptionPlotDirect(unittest.TestCase):
    """Tests for direct calls to consumption OML loading and plotting."""

    def setUp(self):
        """Set up test OML data for direct loading and plotting tests."""
        meas_file = fixture_path("examples", "consumption.oml")
        self.data = consum.oml_load(meas_file)
        self.title = "Node"

    def test_consumption_plot_all(self):
        """Test direct call to consumption_plot with all measures."""
        with mock.patch("oml_plot_tools.consum.oml_plot") as mock_plot:
            with mock.patch("oml_plot_tools.consum.common.plot_show"):
                consum.consumption_plot(self.data, self.title, ["all"])
                self.assertTrue(mock_plot.called)

    def test_consumption_plot_power(self):
        """Test direct call to consumption_plot with power measure."""
        with mock.patch("oml_plot_tools.consum.oml_plot") as mock_plot:
            with mock.patch("oml_plot_tools.consum.common.plot_show"):
                consum.consumption_plot(self.data, self.title, ["power"])
                self.assertTrue(mock_plot.called)

    def test_consumption_plot_voltage(self):
        """Test direct call to consumption_plot with voltage measure."""
        with mock.patch("oml_plot_tools.consum.oml_plot") as mock_plot:
            with mock.patch("oml_plot_tools.consum.common.plot_show"):
                consum.consumption_plot(self.data, self.title, ["voltage"])
                self.assertTrue(mock_plot.called)

    def test_consumption_plot_current(self):
        """Test direct call to consumption_plot with current measure."""
        with mock.patch("oml_plot_tools.consum.oml_plot") as mock_plot:
            with mock.patch("oml_plot_tools.consum.common.plot_show"):
                consum.consumption_plot(self.data, self.title, ["current"])
                self.assertTrue(mock_plot.called)

    def test_consumption_plot_time(self):
        """Test direct call to consumption_plot with time measure."""
        with mock.patch("oml_plot_tools.consum.common.oml_plot_clock") as mock_clock:
            with mock.patch("oml_plot_tools.consum.common.plot_show"):
                consum.consumption_plot(self.data, self.title, ["time"])
                self.assertTrue(mock_clock.called)


class TestDoc(unittest.TestCase):
    """Tests that module help matches its docstring."""

    @unittest.skipIf(IS_PYTHON_3_10, "Python 3.10 not supported")
    def test_doc(self):
        """Test that the module help output matches its docstring."""
        utest_help_as_doc(self, consum)
