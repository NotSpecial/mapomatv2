# -*- coding: utf-8 -*-
from mapomat.import_data import import_businesses as get_busi
from mapomat.supercats import add_supercats as get_cats
from mapomat.distances import make_cell_collection

import pickle

print("importing data ...")
# 1: Getting raw data
(busi, box, combos) = get_cats(get_busi(
    fields=['categories', 'city', 'latitude', 'longitude', 'business_id']))

# Correct Montreal/Montréal problem
busi.loc[busi['city'] == u'Montréal', 'city'] = u"Montreal"

# Filter out small cities
# Get cities with over 1000 businesses
idx = (busi.groupby('city')['categories'].count()
       .order(ascending=False) > 1000)
# Use this list to index itself to get only the names
cities = idx[idx].index.tolist()

print('sorting businesses into cells ...')
# sorting into cells
cells = make_cell_collection(15, busi)

# add cell coord to the businesses df
busi['cell_coord'] = busi.apply(lambda row: cells.get_cell(row), axis=1)

# Create city grids
city_grids = {}

# group dataframe
c_groups = busi.groupby('city')

# helper dict to collect all names
names = combos.copy()
for key in box:
    names[key] = box[key]['name']

for city in cities:
    city_grids[city] = {}
    df_city = c_groups.get_group(city)

    # Super and sub categories
    # We add 3 values:
    # name of category
    # max number of businesses in a single cell
    # all cells with number of businesses

    def make_data(column):
        # Groupy groupy group
        gr = df_city.groupby(column)
        # Take a random column (e.g. city) and count
        # Needed later
        gr_count = gr['city'].count()

        # Groups are all supercats/cats with at least
        # 1 cell, create dicts for them:
        for key in gr.groups.keys():
            if ((type(key) != tuple and key == -1) or
                    (type(key) == tuple and -1 in key)):
                continue  # Skip uncategoried

            # Stop if too few businesses in the category
            if gr_count[key] < 10:
                continue

            # Select group, group again by cell, select
            # one random column (all are equal), here city
            # and count businesses
            cell_counts = (gr.get_group(key)
                           .groupby('cell_coord')['city'].count())

            city_grids[city][key] = {}

            # Name
            city_grids[city][key]['name'] = (
                names[key])

            # Max
            city_grids[city][key]['max'] = (
                cell_counts.max())

            # Cell dict
            cell_dict = {}
            for x, y in cell_counts.index:
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

print("formatting data for web...")
# Create dictionaries for web display
latlongdata = busi.groupby('city')[['latitude', 'longitude']].mean()
citylatlon = {
    city: {
        'lat': latlongdata.loc[city, 'latitude'],
        'lon': latlongdata.loc[city, 'longitude']
    } for city in cities
}

super_categories = {key: box[key]['name'] for key in box if key != -1}

categories = {}
for superkey in box:
    if superkey == -1:
        continue  # skip entirely
    subbox = box[superkey]['sub_categories']
    categories[superkey] = (
        {key: subbox[key]['name'] for key in subbox if key != -1})

# Create city dict. Make sure to cast all keys form numpy.int to int
# json lib has problems with numpy int and doesnt parse sometimes
city_categories = {city: {} for city in cities}
for city in cities:
    # Iterate twice: Once to find integers fo
    for key in city_grids[city]:  # categories for city
        if type(key) == tuple:
            continue
        # Create super categories
        city_categories[city][int(key)] = []

    for key in city_grids[city]:  # categories for city
        if type(key) != tuple:
            continue
        # Create super categories
        city_categories[city][int(key[0])].append(int(key[1]))


print('saving data ...')
data = {
    'citylatlon': citylatlon,
    'super_categories': super_categories,
    'categories': categories,
    'grids': city_grids,
    'borders': cells.get_borders(),
    'city_categories': city_categories
}

print('additional configuration ...')
result_folder = input("folder to store user requests ('results'): ")
if len(result_folder) == 0:
    result_folder = 'results'
config = {
    'result_folder': result_folder
}
data.update(config)

with open("mapomat/mapomat.dat", 'wb') as f:
    # force latin1 encoding
    # p = pickle._Pickler(f)
    # p.encoding = 'latin1'
    pickle.dump(data, f)


""" Old version
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
"""
