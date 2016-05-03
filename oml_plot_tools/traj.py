#!/usr/bin/python
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


"""
usage: plot_oml_traj [-h] [-i DATA] [--circuit-file CIRCUIT] [--site-map SITE]
                     [--nodes-list ID_LIST] [-l TITLE] [-b BEGIN] [-e END]
                     [-t] [-a] [-ti]

Plot iot-lab trajectory oml files

optional arguments:
  -h, --help            show this help message and exit
  -i DATA, --input DATA
                        Robot trajectory values
  --circuit-file CIRCUIT
                        Robot circuit file, '-' for stdin
  --site-map SITE       Site map
  --nodes-list ID_LIST  nodes list
  -l TITLE, --label TITLE
                        Graph title
  -b BEGIN, --begin BEGIN
                        Sample start
  -e END, --end END     Sample end

plot:
  Plot selection

  -t, --traj            Plot robot trajectory
  -a, --angle           Plot robot angle
  -ti, --time           Plot time verification
"""


import json
from collections import namedtuple
from cStringIO import StringIO
import itertools

import argparse

# Issues with numpy and matplotlib.cm
# pylint:disable=no-member
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.patches as patches
# http://stackoverflow.com/a/26605247/395687
# pip install --no-index -f http://dist.plone.org/thirdparty/ -U PIL
# or 'apt-get install python-imaging'
from PIL import Image

from . import common

import iotlabcli.parser.common
import iotlabcli.robot
import iotlabcli.rest
import iotlabcli.experiment


PACKAGE = __name__.split('.')[0]

DOCK_PLT = {
    'color': 'blue',
    'marker': 's',
    's': 10,
}
NODES_PLT = {
    'color': 'green',
    'marker': 's',
    's': 10,
}
CIRCUIT_EDGE_PLT = {
    'linestyle': 'dashed',
    'linewidth': 2,
    'edgecolor': 'red',
    'fill': False,
}
CIRCUIT_POINT_PLT = {
    'marker': 'o',
    'color': 'red',
}

MEASURES_D = common.measures_dict(
    ('x', float, 'X'),
    ('y', float, 'Y'),
    ('theta', float, 'yaw angle (rad)'),
)

Deco = namedtuple('Deco', ['marker', 'color', 'size', 'x', 'y'])
Map = namedtuple('Map', ['marker', 'file', 'ratio', 'sizex', 'sizey',
                         'offsetx', 'offsety'])

MapInfo = namedtuple('MapInfo', ['image', 'ratio', 'offsetx', 'offsety',
                                 'docks'])
Dock = namedtuple('Dock', ['x', 'y', 'theta'])


def oml_load(filename):
    """ Load consumption oml file """
    data = common.oml_load(filename, 'robot_pose', MEASURES_D.values())
    return data


def get_site_map(site):
    """ Load infos for site """
    # Get map config and with cache
    map_cfg = iotlabcli.robot.robot_get_map(site)
    map_info = _mapinfo_from_cfg(map_cfg)

    return map_info


def _mapinfo_from_cfg(map_cfg):
    """ MapInfo object from 'map_cfg' dict """

    # Load Image
    image_fd = StringIO(map_cfg['image'])
    image = Image.open(image_fd).convert('L')

    # Load Docks
    docks = map_cfg['dock'].values()
    docks = [Dock(d['x'], d['y'], d['theta']) for d in docks]

    # Create the whole MapInfo
    cfg = map_cfg['config']
    map_info = MapInfo(image, cfg['ratio'], cfg['offset'][0], cfg['offset'][1],
                       docks)
    return map_info


def circuit_load(filename):
    """ Load robot circuit file

    :returns: circuit json object
    {
       "coordinates": [
       {
         "name": "0",
         "x": 9.5036359876481,
         "y": -0.8644077467101,
         "z": 0,
         "w": -2.4504422620417
       },
       {
         "name": "1",
         "x": 0.88773354001121,
         "y": 9.750401138047,
         "z": 0,
         "w": 0.46435151843117
       }
      ],
      "points":["0", "1" ]
    }
    """
    # Handle '-' for stdin
    json_file = argparse.FileType('r')(filename)
    return json.load(json_file)


PARSER = argparse.ArgumentParser(
    prog='plot_oml_traj', description="Plot iot-lab trajectory oml files")
PARSER.add_argument('-i', '--input', dest='data', type=oml_load,
                    help="Robot trajectory values")
PARSER.add_argument('--circuit-file', dest='circuit', type=circuit_load,
                    help="Robot circuit file, '-' for stdin")
PARSER.add_argument('--site-map', metavar='SITE', dest='mapinfo',
                    type=get_site_map, help="Site map")
PARSER.add_argument('--nodes-list', metavar='ID_LIST', action='append',
                    type=iotlabcli.parser.common.nodes_list_from_str,
                    dest='nodes_list_list', default=[],
                    help='nodes list')

PARSER.add_argument('-l', '--label', dest='title', default="Robot",
                    help="Graph title")
PARSER.add_argument('-b', '--begin', default=0, type=int, help="Sample start")
PARSER.add_argument('-e', '--end', default=-1, type=int, help="Sample end")

_PLOT = PARSER.add_argument_group('plot', "Plot selection")
_PLOT.add_argument('-t', '--traj', dest='plot', const='traj',
                   action='append_const', help="Plot robot trajectory")
_PLOT.add_argument('-a', '--angle', dest='plot', const='angle',
                   action='append_const', help="Plot robot angle")
_PLOT.add_argument('-ti', '--time', dest='plot', const='time',
                   action='append_const', help="Plot time verification")


def trajectory_plot(data, title, mapinfo, circuit, selection, nodes=()):
    """ Plot trajectories infos """

    plot_data = False

    if 'traj' in selection:
        plot_data |= oml_plot_map(data, title, mapinfo, circuit, nodes)

    # Figure angle initialization
    if 'angle' in selection:
        plot_data |= oml_plot_angle(data, title)

    # Clock verification
    if 'time' in selection:
        plot_data |= common.oml_plot_clock(data)

    if plot_data:
        plt.tight_layout()
        plt.show()
    else:
        print "Nothing to plot"


def oml_plot_angle(data, title, xlabel=common.TIMESTAMP_LABEL):
    """ Plot data 'angel' field """
    ylabel = MEASURES_D['theta'].label
    title = '%s %s' % (title, 'angle')

    plt.figure()
    plt.title(title)
    plt.grid()
    plt.plot(data['timestamp'], data['theta'])
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    return True


def _image_extent(mapinfo):
    """ Image 'imshow' extent values
    Place image in the robot coordinates """
    left = mapinfo.offsetx
    right = mapinfo.offsetx + mapinfo.image.size[0] * mapinfo.ratio

    bottom = mapinfo.offsety
    top = mapinfo.offsety + mapinfo.image.size[1] * mapinfo.ratio

    return (left, right, bottom, top)


def oml_plot_map(data, title, mapinfo, circuit=None, nodes=()):
    """ Plot iot-lab oml data

    :param data: numpy array with robot trajectory
    :param title: plot title
    :param mapinfo: MapInfo object
    :param circuit: circuit json
    """

    if not (mapinfo or circuit or not common.array_empty(data)):
        return False  # nothing to graph

    # Figure trajectory initialization
    plt.figure()
    plt.title(title + ' trajectory')
    plt.grid()

    # Map and dock background
    _plot_mapinfo(mapinfo)
    # Plot theorical circuit
    _plot_circuit(circuit)
    # Plot actual robot trajectory
    _plot_robot_traj(data)

    _plot_nodes(nodes)

    return True


def _plot_mapinfo(mapinfo):
    """ Plot map and docks background """
    if mapinfo is None:
        return

    # Plot map image in background
    extent = _image_extent(mapinfo)
    arr = np.asarray(mapinfo.image)
    plt.imshow(arr, cmap=cm.Greys_r, aspect='equal', extent=extent)

    # Plot docks
    for dock in mapinfo.docks:
        plt.scatter(dock.x, dock.y, **DOCK_PLT)


def _plot_circuit(circuit):
    """ Plot circuit, scaled to map if available"""
    if circuit is None:
        return

    coords = [circuit['coordinates'][p] for p in circuit['points']]

    # Get coordinates
    coords_x = [c['x'] for c in coords]
    coords_y = [c['y'] for c in coords]
    coords = (coords_x, coords_y)

    # Get edges between checkpoints
    edges = patches.Polygon(zip(*coords), **CIRCUIT_EDGE_PLT)

    # Plot
    a_x = plt.gcf().add_subplot(111)
    a_x.add_patch(edges)
    plt.plot(*coords, **CIRCUIT_POINT_PLT)


def _plot_nodes(nodes_list):
    """Plot nodes on map."""
    for node in nodes_list:
        try:
            x = float(node['x'])  # pylint:disable=invalid-name
            y = float(node['y'])  # pylint:disable=invalid-name
        except ValueError:
            print '%s: No coordinates' % node['network_address']
        else:
            plt.scatter(x, y, **NODES_PLT)


def _plot_robot_traj(robot_traj):
    """ Plot robot trajectory """
    if robot_traj is None:
        return

    plt.plot(robot_traj['x'], robot_traj['y'])
    plt.xlabel('X (m)')
    plt.ylabel('Y (m)')


def nodes_coordinates(nodes_list_list):
    """Return nodes coordinates as a list for nodes_list_list."""

    api = iotlabcli.rest.Api(None, None)
    # Can't use info_experiment unauthenticated...
    username, password = iotlabcli.get_user_credentials(None, None)
    api = iotlabcli.Api(username, password)

    # splat
    all_nodes = iotlabcli.experiment.info_experiment(api)['items']
    all_nodes_dict = dict(((n['network_address'], n) for n in all_nodes))

    nodes_list = frozenset(itertools.chain.from_iterable(nodes_list_list))

    nodes_coords_list = [all_nodes_dict[n] for n in nodes_list]
    return nodes_coords_list


def main():  # pylint:disable=too-many-statements
    """ Main command """
    opts = PARSER.parse_args()
    # default to plot traj/map
    selection = opts.plot or ('traj')
    # select samples
    data = opts.data[opts.begin:opts.end] if opts.data is not None else None

    nodes = nodes_coordinates(opts.nodes_list_list)

    trajectory_plot(data, opts.title, opts.mapinfo, opts.circuit,
                    selection, nodes)


if __name__ == "__main__":
    main()
