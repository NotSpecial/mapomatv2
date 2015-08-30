# -*- coding: utf-8 -*-
from mapomat.import_data import import_businesses as get_busi
from mapomat.supercats import add_supercats as get_cats
from mapomat.distances import make_cell_collection
from mapomat.kml_creation import make_dict

import pickle


print("importing data ...", end='\r')
(busi, box, combos) = get_cats(get_busi(
    fields=['categories', 'city', 'latitude', 'longitude', 'business_id']))

print('processing data ...', end='\r')
# Correct Montreal/Montréal program
busi.loc[busi['city'] == u'Montréal', 'city'] = u"Montreal"

# Get cities with over 1000 businesses
idx = (busi.groupby('city')['categories'].count()
       .order(ascending=False) > 1000)
# Use this list to index itself to get only the names
cities = idx[idx].index.tolist()

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
    categories[superkey] = {key: subbox[key]['name'] for key in subbox}

# sorting into cells
print('sorting businesses into cells ...', end='\r')
cells = make_cell_collection(15, busi)

# add cell coord to the businesses df
busi['cell_coord'] = busi.apply(lambda row: cells.get_cell(row), axis=1)

print('creating city analysises ...', end='\r')
city_grids = {}
for city in cities:
    print('processing ' + city + ' ...', end='\r')
    city_grids[city] = {}
    # first supercats
    for superkey in box:
        if superkey != -1:
            data = make_dict(city, superkey, busi, cells, supercat=True)
            if len(data['dict']) > 0:
                data['name'] = box[superkey]['name']
                city_grids[city][superkey] = data

    # sub-categories
    for combo in combos:
        if combo[0] != -1 and combo[1] != -1:
            data = make_dict(city, combo, busi, cells, supercat=False)
            if len(data['dict']) > 0:
                data['name'] = combos[combo]
                city_grids[city][combo] = data

print('saving data ...', end='\r')
data = {
    'cities': cities,
    'citylatlon': citylatlon,
    'super_categories': super_categories,
    'categories': categories,
    'df': busi,
    'combos': combos,
    'grids': city_grids,
    'borders': cells.get_borders()
}

with open("mapomat/mapomat.dat", 'wb') as f:
    # force latin1 encoding
    p = pickle._Pickler(f)
    p.encoding = 'latin1'
    p.dump(data)
