# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file, abort
from werkzeug import secure_filename
from flask_sqlalchemy import SQLAlchemy

from os import path, makedirs, getcwd
import json

import random
import string

from .kml_creation import density_kml


# initialize app

_ROOT = path.abspath(path.dirname(__file__))
temp_folder = path.join(_ROOT, "templates")
app = Flask(__name__, template_folder=temp_folder)

with open(path.join(_ROOT, "mapomat.json"), 'r') as f:
    # u = pickle._Unpickler(f)
    # u.encoding = 'latin1'
    data = json.load(f)

app.config.update(data)

# Make dir
result_folder = path.join(_ROOT, "results")
app.config['result_folder'] = result_folder

if not path.exists(result_folder):
    makedirs(result_folder)


# add db, define db class

app.config['DB_PATH'] = path.join(_ROOT, "mapomat.db")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % app.config['DB_PATH']
# Make annoying warning go away
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create db if necessary
if not path.exists(app.config['DB_PATH']):
    db.create_all()

city_max_length = app.config['city_categories']


class KmlInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.Unicode(city_max_length))
    legend = db.Column(db.Text)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

    def __init__(self, **kvargs):
        for key, item in kvargs.items():
            setattr(self, key, item)


# define app routes

@app.route("/", methods=['GET'])
def hello():
    return render_template(
        'hello.html',
        city_categories=app.config['city_categories'],
        super_categories=app.config['super_categories'],
        categories=app.config['categories'],
    )


@app.route("/", methods=['POST'])
def new_result():
    city = request.json['city']
    colors = request.json['colors']
    scaling = request.json['scaling']
    result_folder = app.config['result_folder']

    identifier = (''.join(random.choice(string.ascii_lowercase + string
                  .digits) for _ in range(20)))

    if len(colors) > 0:
        # make legend and density-dicts
        legend = {}
        dicts = []
        for color in colors:
            legend[color['name']] = color['color']
            key = color['key']
            grid = app.config['grids'][city].get(key, None)

            # remove the css '#' from color-string
            grid['color'] = color['color'][1:]
            dicts.append(grid)

        density_kml(
            result_folder,
            identifier,
            city,
            dicts,
            app.config['borders'],
            scaling=lambda x: x ** scaling,
        )

    else:
        legend = {"Nothing selected": "ffffff"}
        identifier = 'nothing'

    # add everything to info.json in the identifier folder
    info_path = path.join(result_folder, identifier, 'info.json')
    info = {'city': city,
            'legend': json.dumps(legend),
            'lat': app.config['citylatlon'][city]['lat'],
            'lon': app.config['citylatlon'][city]['lon']}

    from pprint import pprint
    pprint(info)
    print(type(info['lat']))

    with open(info_path, 'w') as info_file:
        json.dump(info, info_file)
        info_file.close()

    return identifier


@app.route("/result/<identifier>", methods=['GET'])
def result(identifier):
    # load info
    data_path = path.join(app.config['result_folder'], identifier)
    if not path.exists(data_path):
        abort(404)

    with open(path.join(data_path, 'info.json'), 'r') as info_file:
        info = json.load(info_file)
        info_file.close()

    return render_template('kml.html',
                           lat=info['lat'],
                           lon=info['lon'],
                           kml=path.join(data_path, 'data.kml'),
                           identifier=identifier,
                           city=info['city'],
                           legend=json.loads(info['legend']))


@app.route("/kml/<identifier>.kml", methods=['GET'])
def deliver(identifier):
    identifier = secure_filename(identifier)
    kml_path = path.join(getcwd(),
                         app.config['result_folder'],
                         identifier,
                         'data.kml')

    if path.exists(kml_path):
        return send_file(kml_path)
    else:
        abort(404)
