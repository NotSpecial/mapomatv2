# -*- coding: utf-8 -*-
from flask import Flask, render_template, request

from ast import literal_eval
from os import path, makedirs

from mapomat.import_data import import_businesses as get_busi
from mapomat.supercats import add_supercats as get_cats
from mapomat.kml_creation import density_kml

app = Flask("Map-o-Mat")
app.config.from_object('config')

# Make dir
if not path.exists("kml_files"):
    makedirs("kml_files")

(busi, box, combos) = get_cats(get_busi(
    fields=['categories', 'city', 'latitude', 'longitude', 'business_id']))

# Correct Montreal/Montréal program
busi.loc[busi['city'] == 'Montreal', 'city'] = "Montréal"

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


app.config.update({
    'cities': cities,
    'citylatlon': citylatlon,
    'super_categories': super_categories,
    'categories': categories,
    'df': busi,
    'combos': combos
})


@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html',
                           cities=app.config['cities'],
                           supercats=app.config['super_categories'],
                           subcats=app.config['categories'])


@app.route("/", methods=['POST'])
def result():
    city = request.form['city']
    sup = [int(item) for item in request.form.getlist('supercat')]
    sub = [literal_eval(item) for item in request.form.getlist('subcat')]

    supercats = {
        key: app.config['super_categories'][key] for key in sup
    }

    subcats = {
        key: app.config['combos'][key] for key in sub
    }

    if (len(sup) > 0) or (len(sub) > 0):
        name, legend = density_kml(city, supercats, subcats, app.config['df'])

        url = app.config['KML_URL'] + name
    else:
        url = ""
        legend = {}

    return render_template('kml.html',
                           lat=app.config['citylatlon'][city]['lat'],
                           lon=app.config['citylatlon'][city]['lon'],
                           kmlurl=url,
                           city=city,
                           legend=legend)

if __name__ == "__main__":
    app.run()
