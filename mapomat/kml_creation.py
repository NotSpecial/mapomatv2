from __future__ import division
from os import path, mkdir
from .cache import cache_result
from werkzeug import secure_filename
import numpy as np
from simplekml import Kml
from random import choice
import string


def region(businesses, cells, city, radius):
    random_choice = businesses[businesses['city'] == city][:1].squeeze()
    region_indices = [item['index'] for item in
                      cells.get_region(random_choice, radius)]
    return list(set(
        businesses.loc[region_indices, 'city'].tolist()))


@cache_result('pickles')
def region_cells(businesses, cells, city, radius):
    region_filter = region(businesses, cells, city, radius)
    region_bizs = businesses[businesses['city'].isin(region_filter)]
    region_cell_coords = []
    for idx, biz in region_bizs.iterrows():
        region_cell_coords.append(cells.get_cell(biz))
    region_cell_coords = set(region_cell_coords)
    cell_dict = cells.to_dict()
    ret = {}
    for coord in region_cell_coords:
        if coord[0] not in ret:
            ret[coord[0]] = {}
        ret[coord[0]][coord[1]] = [
            i['index'] for i in cell_dict[coord[0]][coord[1]]]
    return ret, region_bizs


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
            if cell is not np.nan:
                make_polygon(kml, 'Cell-{}-{}:{}'.format(x, y, cell),
                             (longitudes[x], latitudes[y]),
                             (longitudes[x + 1], latitudes[y + 1]),
                             color_mapper(cell, *args))
    return kml


def make_dict(city, category, businesses, cells, supercat=True):

    # filter by relevant region
    (region_dict, region_businesses) = region_cells(businesses, cells, city, 5)

    grouped = region_businesses.groupby('cell_coord')

    # get businesses from given category
    if supercat:
        in_cat = (region_businesses['super_category'] == category)
    else:
        in_cat = (region_businesses['category'] == category)

    cat_dict = {}
    for x, row in region_dict.items():
        for y in row:
            # count the number of filtered businesses in this cell
            count = grouped.get_group((x, y))[in_cat]['business_id']\
                .count()
            # only add cell if there exist such businesses
            if count > 0:
                if x not in cat_dict:
                    cat_dict[x] = {}
                cat_dict[x][y] = count

    # find maximum for normalizing
    values = [item for row in cat_dict.values() for item in row.values()]
    if len(values) > 0:
        maximum = np.max(values)
    else:
        maximum = None

    return {'dict': cat_dict, 'max': maximum}


def density_kml(city, dicts, borders, folder='results',
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

    identifier = ''.join(choice(string.ascii_lowercase + string.digits) \
        for _ in range(20))

    mkdir(path.join(folder, identifier))

    kml_path = path.join(folder, identifier, 'data.kml')
    kml.save(kml_path)

    return identifier
