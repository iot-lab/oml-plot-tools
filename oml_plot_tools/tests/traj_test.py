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

"""Tests for traj.py."""

import json
import unittest
from unittest import mock

from .. import common, traj
from .common import (
    IS_PYTHON_3_10,
    assert_called_with_nparray,
    fixture_path,
    utest_help_as_doc,
    utest_plot_and_compare,
)


def robot_get_map(site):
    """Simulate robot_get_map using examples files."""
    map_cfg = {}

    with open(fixture_path("examples", f"{site}-iotlab.png"), "rb") as _fd:
        map_cfg["image"] = _fd.read()

    with open(fixture_path("examples", f"{site}-mapconfig.json")) as _fd:
        map_cfg["config"] = json.load(_fd)

    with open(fixture_path("examples", f"{site}-dockconfig.json")) as _fd:
        map_cfg["dock"] = json.load(_fd)

    return map_cfg


def maps_load(site):
    """Load given site map and return mapinfo."""
    map_cfg = robot_get_map(site)
    return traj._mapinfo_from_cfg(map_cfg)  # noqa: SLF001, #pylint: disable=protected-access


class TestTrajectoryOmlPlot(unittest.TestCase):
    """Tests for trajectory OML plot functions."""

    def setUp(self):
        """Set up trajectory OML data for plot tests."""
        robot_file = fixture_path("examples", "robot.oml")
        circuit_file = fixture_path("examples", "Jhall_w.json")

        self.data = traj.oml_load(robot_file)
        self.mapinfo = maps_load("grenoble")
        self.circuit = traj.circuit_load(circuit_file)
        self.title = "Robot"

    def test_plot_all(self):
        """Test plotting all trajectory data with map and circuit."""
        ref_img = fixture_path("examples", "trajectory_all.png")
        traj.oml_plot_map(self.data, self.title, self.mapinfo, self.circuit)
        utest_plot_and_compare(self, ref_img, 11000)

    def test_plot_traj_only(self):
        """Test plotting trajectory data without map and circuit."""
        ref_img = fixture_path("examples", "trajectory_only.png")
        traj.oml_plot_map(self.data, self.title, None, None)
        utest_plot_and_compare(self, ref_img, 1500)

    def test_plot_traj_circuit(self):
        """Test plotting trajectory data with circuit but no map."""
        ref_img = fixture_path("examples", "trajectory_circuit.png")
        traj.oml_plot_map(None, self.title, None, self.circuit)
        utest_plot_and_compare(self, ref_img, 1500)

    def test_plot_traj_nothing(self):
        """Test plotting with no data, map, or circuit should print message."""
        ret = traj.oml_plot_map(None, None, None, None)
        self.assertFalse(ret)

    def test_plot_angle(self):
        """Test plotting trajectory angle data."""
        ref_img = fixture_path("examples", "trajectory_angle.png")
        traj.oml_plot_angle(self.data, self.title)
        utest_plot_and_compare(self, ref_img, 50)

    def test_plot_clock(self):
        """Test plotting trajectory clock data."""
        ref_img = fixture_path("examples", "trajectory_clock.png")
        common.oml_plot_clock(self.data)
        utest_plot_and_compare(self, ref_img, 100)


class TestTrajectory(unittest.TestCase):
    """Tests for trajectory main CLI entry point."""

    def setUp(self):
        """Set up mocks and test arguments for trajectory main tests."""
        meas_file = fixture_path("examples", "robot.oml")
        self.data = traj.oml_load(meas_file)[0:1]

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

        self.oml_plot_map = mock.patch("oml_plot_tools.traj.oml_plot_map").start()
        self.oml_plot_map.return_value = False
        self.oml_plot_angle = mock.patch("oml_plot_tools.traj.oml_plot_angle").start()
        self.oml_plot_angle.return_value = False
        self.oml_plot_clock = mock.patch(
            "oml_plot_tools.traj.common.oml_plot_clock"
        ).start()
        self.oml_plot_clock.return_value = False

        self.plot_show = mock.patch("oml_plot_tools.traj.common.plot_show").start()

    def tearDown(self):
        """Stop all mocks after each test."""
        mock.patch.stopall()

    def traj_main(self, *args):
        """Call traj main with given additional args."""
        with mock.patch("sys.argv", list(self.args) + list(args)):
            traj.main()

    def test_plot_traj(self):
        """Test with trajectory selection calls correct plotting function."""
        self.oml_plot_map.return_value = True
        self.traj_main("--traj")
        assert_called_with_nparray(self.oml_plot_map, self.data, self.title, None, None)
        self.assertFalse(self.oml_plot_angle.called)
        self.assertFalse(self.oml_plot_clock.called)
        self.assertTrue(self.plot_show.called)

    def test_plot_angle(self):
        """Test with angle selection calls correct plotting function."""
        self.oml_plot_angle.return_value = True
        self.traj_main("--angle")
        self.assertFalse(self.oml_plot_map.called)
        assert_called_with_nparray(self.oml_plot_angle, self.data, self.title)
        self.assertFalse(self.oml_plot_clock.called)
        self.assertTrue(self.plot_show.called)

    def test_plot_clock(self):
        """Test with time selection calls correct plotting function."""
        self.oml_plot_clock.return_value = True
        self.traj_main("--time")
        self.assertFalse(self.oml_plot_map.called)
        self.assertFalse(self.oml_plot_angle.called)
        assert_called_with_nparray(self.oml_plot_clock, self.data)
        self.assertTrue(self.plot_show.called)

    def test_plot_nothing(self):
        """Test no selections should print message and not call plotting functions."""
        self.oml_plot_map.return_value = False
        self.args = ["plot_oml_consum"]
        self.traj_main("--traj")

        assert_called_with_nparray(self.oml_plot_map, None, "Robot", None, None)
        self.assertFalse(self.oml_plot_angle.called)
        self.assertFalse(self.oml_plot_clock.called)

    @mock.patch("iotlabcli.robot.robot_get_map", robot_get_map)
    def test_plot_mapinfo(self):
        """Test with mapinfo selection calls correct plotting function."""
        self.args = ["plot_oml_consum"]
        self.traj_main("--site-map", "grenoble")
        self.assertTrue(self.oml_plot_map.called)

    def test_trajectory_plot_nothing_to_show(self):
        """Test with selections that do not produce any plot should print message."""
        self.oml_plot_map.return_value = False
        self.oml_plot_angle.return_value = False
        self.oml_plot_clock.return_value = False
        with mock.patch("builtins.print") as mock_print:
            traj.trajectory_plot(None, "T", None, None, ["traj"])
            mock_print.assert_called_with("Nothing to plot")

    def test_trajectory_plot_all_selections(self):
        """Test trajectory_plot with all selections calls all plotting functions."""
        self.oml_plot_map.return_value = True
        self.oml_plot_angle.return_value = True
        self.oml_plot_clock.return_value = True
        traj.trajectory_plot(
            self.data, self.title, None, None, ["traj", "angle", "time"]
        )
        self.assertTrue(self.oml_plot_map.called)
        self.assertTrue(self.oml_plot_angle.called)
        self.assertTrue(self.oml_plot_clock.called)
        self.assertTrue(self.plot_show.called)


class TestDoc(unittest.TestCase):
    """Tests that module help matches its docstring."""

    @unittest.skipIf(IS_PYTHON_3_10, "Python 3.10 not supported")
    def test_doc(self):
        """Test that the module help output matches its docstring."""
        utest_help_as_doc(self, traj)
