# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file, abort
from werkzeug import secure_filename
from flask_sqlalchemy import SQLAlchemy

from os import path, makedirs
import json

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

# Determine longest city string for database field length
city_max_length = max([len(key) for key in app.config['city_categories']])


class KmlInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.Unicode(city_max_length))
    legend = db.Column(db.Text)
    color_info = db.Column(db.Text)
    scaling = db.Column(db.Float)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

    def __init__(self, **kvargs):
        for key, item in kvargs.items():
            setattr(self, key, item)

# Create db if necessary
if not path.exists(app.config['DB_PATH']):
    db.create_all()


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
    scaling = float(request.json['scaling'])

    if len(colors) > 0:
        # make legend and density-dicts
        legend = {}
        for color in colors:
            legend[color['name']] = color['color']
    else:
        legend = {"Nothing selected": "ffffff"}

    color_info = (
        {item['key']: item['color'] for item in colors})

    # Save info_data
    info_data = {'city': city,
                 'legend': json.dumps(legend),
                 'color_info': json.dumps(color_info),
                 'scaling': scaling,
                 'lat': app.config['citylatlon'][city]['lat'],
                 'lon': app.config['citylatlon'][city]['lon']}

    info = KmlInfo(**info_data)

    db.session.add(info)
    db.session.commit()

    return str(info.id)


@app.route("/result/<identifier>", methods=['GET'])
def result(identifier):
    identifier = secure_filename(identifier)
    # load info
    data_path = path.join(app.config['result_folder'], identifier)

    # Load info from db
    info = db.session.query(KmlInfo).get(identifier)

    # If identifier is invalid return 404
    if info is None:
        abort(404)

    return render_template('kml.html',
                           lat=info.lat,
                           lon=info.lon,
                           kml=path.join(data_path, 'data.kml'),
                           identifier=str(info.id),
                           city=info.city,
                           legend=json.loads(info.legend))


@app.route("/kml/<identifier>.kml", methods=['GET'])
def deliver(identifier):
    identifier = secure_filename(identifier)
    kml_path = path.join(app.config['result_folder'],
                         '%s.kml' % identifier)

    # Load info from db
    info = db.session.query(KmlInfo).get(identifier)

    # If identifier is invalid return 404
    if info is None:
        abort(404)

    if len(info.color_info) > 0:
        # make legend and density-dicts
        dicts = []
        for key, color in json.loads(info.color_info).items():
            grid = app.config['grids'][info.city].get(key, None)

            # remove the css '#' from color-string
            grid['color'] = color[1:]
            dicts.append(grid)

    # Create kml
    if not path.exists(kml_path):
        density_kml(
            kml_path,
            info.city,
            dicts,
            app.config['borders'],
            scaling=lambda x: x ** info.scaling,
        )

    return send_file(kml_path)
