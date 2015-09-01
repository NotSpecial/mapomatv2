# -*- coding: utf-8 -*-
from mapomat.import_data import import_businesses as get_busi
from mapomat.supercats import add_supercats as get_cats
from mapomat.distances import make_cell_collection
from mapomat.kml_creation import make_dict

import pickle

print("importing data ...")
# 1: Getting raw data
(busi, box, combos) = get_cats(get_busi(
    fields=['categories', 'city', 'latitude', 'longitude', 'business_id']))

print('filtering data ...')
# 2: Cleaning up data
# - only keep cities with moe than 1000 businesses
# - Montreal appears twice under different name - fix that

# Correct Montreal/Montréal problem
busi.loc[busi['city'] == u'Montréal', 'city'] = u"Montreal"

# Filter out uncategorized from dicitonaries
for key in box.keys():
    # super level
    if (key == -1):
        box.pop(key)
        continue
    # sub level
    for subkey in box[key]['sub_categories'].keys():
        if (subkey == -1):
            box[key]['sub_categories'].pop(subkey)

for key in combos.keys():
    if (key[0] == -1) or (key[1] == -1):
        combos.pop(key)

# Filter out small cities
# Get cities with over 1000 businesses
idx = (busi.groupby('city')['categories'].count()
       .order(ascending=False) > 1000)
# Use this list to index itself to get only the names
cities = idx[idx].index.tolist()

print("formatting data for web...")
# Create dictionaries for web display
latlongdata = busi.groupby('city')[['latitude', 'longitude']].mean()
citylatlon = {
    city: {
        'lat': latlongdata.loc[city, 'latitude'],
        'lon': latlongdata.loc[city, 'longitude']
    } for city in cities
}

super_categories = {key: box[key]['name'] for key in box}

categories = {}
for superkey in box:
    subbox = box[superkey]['sub_categories']
    categories[superkey] = (
        {key: subbox[key]['name'] for key in subbox})

print('sorting businesses into cells ...')
# sorting into cells
cells = make_cell_collection(15, busi)

# add cell coord to the businesses df
busi['cell_coord'] = busi.apply(lambda row: cells.get_cell(row), axis=1)

print('structuring by city ...')
# Save data into dictionary by city
city_grids = {}
for city in cities:
    print('processing ' + city + ' ...')
    city_grids[city] = {}

    # first supercats
    for superkey in box:
        data = make_dict(city, superkey, busi, cells, supercat=True)
        if len(data['dict']) > 0:
            data['name'] = box[superkey]['name']
            city_grids[city][superkey] = data

    # sub-categories
    for combo in combos:
        data = make_dict(city, combo, busi, cells, supercat=False)
        if len(data['dict']) > 0:
            data['name'] = combos[combo]
            city_grids[city][combo] = data

print('saving data ...')
data = {
    'cities': cities,
    'citylatlon': citylatlon,
    'super_categories': super_categories,
    'categories': categories,
    'grids': city_grids,
    'borders': cells.get_borders()
}

""" ALTERNATIVE VERSION

# Create city grids
city_grids = {}

# group dataframe
c_groups = busi.groupby('city')

for city in cities:
    city_grids[city] = {}
    df_city = c_groups.get_group(city)

    # Super and sub categories
    # We add 3 values:
    # name of category
    # max number of businesses in a single cell
    # all cells with number of businesses

    # helper dict to collect all names
    names = combos.copy()
    for key in box:
        names[key] = box[key]['name']

    def make_data(column):
        # Groupy groupy group
        gr = df_city.groupby(column)

        # Groups are all supercats/cats with at least
        # 1 cell, create dicts for them:
        for key in gr.groups.keys():
            city_grids[city][key] = {}

            # Name
            city_grids[city][key]['name'] = (
                names[key])

            # Select group, group again by cell, select
            # one random column (all are equal), here city
            # and count businesses
            cell_counts = (gr.get_group(key)
                .groupby('cell_coord')['city'].count())

            # Max
            city_grids[city][key]['max'] = (
                cell_counts.max())

            # Cell dict
            cell_dict = {}
            for x,y in cell_counts.index:
                try:
                    cell_dict[x][y] = cell_counts[(x, y)]
                except KeyError:
                    # Key error only if x is not in keys yet
                    cell_dict[x] = {y: cell_counts[(x, y)]}

            city_grids[city][key]['dict'] = cell_dict

    # Super
    make_data("super_category")
    # sub
    make_data("category")

    # Done!

"""

with open("mapomat/mapomat.dat", 'wb') as f:
    # force latin1 encoding
    # p = pickle._Pickler(f)
    # p.encoding = 'latin1'
    pickle.dump(data, f)
