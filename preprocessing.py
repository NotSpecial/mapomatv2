# -*- coding: utf-8 -*-
from preprocessing.import_data import import_businesses as get_busi
from preprocessing.supercats import add_supercats as get_cats
from preprocessing.distances import make_cell_collection

import json

from ast import literal_eval

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

            # save all keys as string
            # this way we can save the data as json and dont have to convert
            # web form inputs back (can just use the strings)
            newkey = str(key)

            city_grids[city][newkey] = {}

            # Name
            city_grids[city][newkey]['name'] = (
                names[key])

            # Max
            city_grids[city][newkey]['max'] = (
                int(cell_counts.max()))

            # Cell dict
            cell_dict = {}
            for x, y in cell_counts.index:
                try:
                    cell_dict[int(x)][int(y)] = int(cell_counts[(x, y)])
                except KeyError:
                    # Key error only if x is not in keys yet
                    cell_dict[int(x)] = {int(y): int(cell_counts[(x, y)])}

            city_grids[city][newkey]['dict'] = cell_dict

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

# TODO: The following part is not very pretty
# The different data dicts should be consistent
# As of now, the cat dicts are nested dicts for super and sub categories
# The grid dict uses ints for super cats and tuples for subcats

# Create city dict. Make sure to cast all keys form numpy.int to int
# json lib has problems with numpy int and doesnt parse sometimes
city_categories = {city: {} for city in cities}
for city in cities:
    # Iterate twice: Once to find integers for super cats
    for key in city_grids[city]:  # categories for city
        if "(" in key:  # keys are str, if ( is in it its a tuple
            continue
        # Create super categories
        city_categories[city][int(key)] = []

    for key in city_grids[city]:  # categories for city
        if "(" not in key:
            continue
        cat_tuple = literal_eval(key)
        # Create super categories
        city_categories[city][int(cat_tuple[0])].append(int(cat_tuple[1]))


# Save data
print('saving data ...')
data = {
    'citylatlon': citylatlon,
    'super_categories': super_categories,
    'categories': categories,
    'grids': city_grids,
    'borders': cells.get_borders(),
    'city_categories': city_categories
}

with open("mapomat/mapomat.json", 'w') as f:
    # force latin1 encoding
    # p = pickle._Pickler(f)
    # p.encoding = 'latin1'
    json.dump(data, f)
