# -*- coding: utf-8 -*-
from import_data import import_businesses as get_busi
from supercats import add_supercats as get_cats

import pickle

(busi, box, combos) = get_cats(get_busi(
    fields=['categories', 'city', 'latitude', 'longitude', 'business_id']))

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

data = {
    'cities': cities,
    'citylatlon': citylatlon,
    'super_categories': super_categories,
    'categories': categories,
    'df': busi,
    'combos': combos
}

with open("mapomat.dat", 'wb') as f:
    pickle.dump(data, f)
