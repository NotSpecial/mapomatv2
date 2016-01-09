# -*- coding: utf-8 -*-
from __future__ import division
from os import path, mkdir
from simplekml import Kml


def dict_to_kml(kml, borders, cell_dict, color_mapper, *args):
    def make_polygon(folder, name, lowerleft, upperright, style):
        pol = folder.newpolygon(name=name)
        pol.extrude = 1
        coords = [lowerleft,
                  (lowerleft[0], upperright[1]),
                  upperright,
                  (upperright[0], lowerleft[1]),
                  lowerleft]
        pol.outerboundaryis = coords
        pol.style.polystyle.color = style

    longitudes = borders[0]
    latitudes = borders[1]
    for x, row in cell_dict.items():
        for y, cell in row.items():
            make_polygon(kml, 'Cell-{}-{}:{}'.format(x, y, cell),
                         (longitudes[int(x)], latitudes[int(y)]),
                         (longitudes[int(x) + 1], latitudes[int(y) + 1]),
                         color_mapper(cell, *args))
    return kml


def density_kml(folder, filename, city, dicts, borders,
                scaling=(lambda x: x)):
    def rgb_to_bgr(color):
        return "{rgb[4]}{rgb[5]}{rgb[2]}{rgb[3]}{rgb[0]}{rgb[1]}".format(
            rgb=color)

    def add_folder(kml, data):
        def cell_to_color(value, color, scaling):
            norm_value = scaling(value)
            return '{0:02x}{1}'.format(int(norm_value * 200), color)

        folder_dict = data['dict']

        # normalizing
        maximum = data['max']
        norm_scaling = lambda x: scaling(x / maximum)

        # make a kml of polygons
        folder = kml.newfolder(name=data['name'])
        color = rgb_to_bgr(data['color'])
        folder = dict_to_kml(folder, borders, folder_dict, cell_to_color,
                             color, norm_scaling)
        return kml

    kml = Kml()

    for data in dicts:
        kml = add_folder(kml, data)

    mkdir(path.join(folder, filename))

    kml_path = path.join(folder, filename, 'data.kml')
    kml.save(kml_path)
