# -*- coding: utf-8 -*-
from __future__ import division
import numpy as np


def region(businesses, cells, city, radius):
    random_choice = businesses[businesses['city'] == city][:1].squeeze()
    region_indices = [item['index'] for item in
                      cells.get_region(random_choice, radius)]
    return list(set(
        businesses.loc[region_indices, 'city'].tolist()))


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
