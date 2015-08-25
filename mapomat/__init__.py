# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file
from werkzeug import secure_filename

from ast import literal_eval
from os import path, makedirs, getcwd

from .import_data import import_businesses as get_busi
from .supercats import add_supercats as get_cats
from .kml_creation import density_kml

_ROOT = path.abspath(path.dirname(__file__))
temp_fold = path.join(_ROOT, "templates")

app = Flask(__name__, template_folder=temp_fold)
app.config.from_object('mapomat.config')
app.config['PROPAGATE_EXCEPTIONS']=True

# Make dir
if not path.exists("kml_files"):
    makedirs("kml_files")

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


@app.route("/kml/<filename>", methods=['GET'])
def deliver(filename):
    filename = secure_filename(filename)
    kml_path = path.join(getcwd(), "kml_files", filename)
    if path.exists(kml_path):
        return send_file(kml_path)
    else:
        return "File not found!"

if __name__ == "__main__":
    app.run(debug=True)
