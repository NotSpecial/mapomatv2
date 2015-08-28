from .cache import cache_result
from os import path
from werkzeug import secure_filename
from colorsys import hsv_to_rgb
import numpy as np
from simplekml import Kml


def region(businesses, cells, city, radius):
    random_choice = businesses[businesses['city'] == city][:1].squeeze()
    region_indices = [item['index'] for item in
                      cells.get_region(random_choice, radius)]
    return list(set(
        businesses.iloc[region_indices]['city'].tolist()))


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
                make_polygon(kml, 'Cell-{}-{}'.format(x, y),
                             (longitudes[x], latitudes[y]),
                             (longitudes[x + 1], latitudes[y + 1]),
                             color_mapper(cell, *args))
    return kml


def density_kml(city, supercats, subcats, businesses, cells,
                folder='kml_files', scaling=(lambda x: x ** 2)):

    num_colors = len(supercats) + len(subcats)

    def split_colors(index):
        print(i)
        print(num_colors)
        hue = index / num_colors
        print(hue)
        (r, g, b) = hsv_to_rgb(hue, 1, 1)
        return "{2:02x}{1:02x}{0:02x}".format(int(r * 255),
                                              int(g * 255),
                                              int(b * 255))

    def add_folder(kml, df_filter, i_color):
        def cell_to_color(value, color, scaling):
            norm_value = scaling(value)
            return '{0:02x}{1}'.format(int(norm_value * 180), color)

        folder_dict = {}
        for x, row in region_dict.items():
            folder_dict[x] = {}
            for y in row:
                # count the number of filtered businesses in this cell
                count = grouped.get_group((x, y))[df_filter]['business_id']\
                    .count()
                # only add cell if there exist such businesses
                if count > 0:
                    folder_dict[x][y] = (
                        grouped.get_group((x, y))[in_cat]['business_id']
                        .count())

        # normalizing
        values = [itm for row in folder_dict.values() for itm in row.values()]
        maximum = np.max(values)
        norm_scaling = lambda x: scaling(x / maximum)

        # make a kml of polygons
        folder = kml.newfolder(name=name)
        color = split_colors(i_color)
        print("{i} von {n}".format(i=i_color, n=num_colors))
        print(color)
        folder = dict_to_kml(folder, cells.get_borders(), folder_dict,
                             cell_to_color, color, norm_scaling)
        return kml

    # filter by relevant region
    (region_dict, region_businesses) = region_cells(businesses, cells, city, 5)

    grouped = region_businesses.groupby('cell_coord')

    kml = Kml()

    i = 0  # indexer for different colors
    # iterate through super categories
    for supercat, name in supercats.items():
        in_cat = (region_businesses['super_category'] == supercat)
        kml = add_folder(kml, in_cat, i)
        i += 1

    # iterate through sub-categories
    for subcat, name in subcats.items():
        in_cat = (region_businesses['category'] == subcat)
        kml = add_folder(kml, in_cat, i)
        i += 1

    # save kml
    kml_name = secure_filename(city) + "_"
    for key in supercats:
        kml_name += "x%i" % key
    kml_name += "_"
    for key in subcats:
        kml_name += "x%iy%i" % (key[0], key[1])
    kml_name += ".kml"

    kml_name = secure_filename(kml_name)
    kml_path = path.join(folder, kml_name)
    kml.save(kml_path)

    # make legend
    legend = {}
    supercat_names = list(supercats.values())
    subcat_names = list(subcats.values())
    for i in range(num_colors):
        if i < len(supercats):
            legend[supercat_names[i]] = \
                "{bgr[4]}{bgr[5]}{bgr[2]}{bgr[3]}{bgr[0]}{bgr[1]}".format(
                    bgr=split_colors(i))
        else:
            legend[subcat_names[i - len(supercats)]] = \
                "{bgr[4]}{bgr[5]}{bgr[2]}{bgr[3]}{bgr[0]}{bgr[1]}".format(
                    bgr=split_colors(i))
    return kml_name, legend
