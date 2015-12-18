# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file
from werkzeug import secure_filename

from ast import literal_eval
from os import path, makedirs, getcwd
import pickle
import json

from .kml_creation import density_kml


def create_app():
    _ROOT = path.abspath(path.dirname(__file__))
    temp_fold = path.join(_ROOT, "templates")
    app = Flask(__name__, template_folder=temp_fold)

    # Make dir
    if not path.exists("kml_files"):
        makedirs("kml_files")

    with open(path.join(_ROOT, "mapomat.dat"), 'rb') as f:
        # u = pickle._Unpickler(f)
        # u.encoding = 'latin1'
        data = pickle.load(f)

    app.config.update(data)
    app.config.update({'result_folder': 'results'})

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
        result_folder = app.config['result_folder']

        if len(colors) > 0:
            # make legend and density-dicts
            legend = {}
            dicts = []
            for color in colors:
                legend[color['name']] = color['color']
                key = literal_eval(color['key'])
                grid = app.config['grids'][city].get(key, None)
                # remove the css '#' from color-string
                grid['color'] = color['color'][1:]
                dicts.append(grid)

            identifier = density_kml(
                city,
                dicts,
                app.config['borders'],
                scaling=lambda x: x ** (0.6),
                folder=result_folder
            )

        else:
            legend = {"Nothing selected": "ffffff"}
            identifier = 'nothing'

        # add everything to info.json in the identifier folder
        info_path = path.join(result_folder, identifier, 'info.json')
        info = {'city': city,
                'legend': legend,
                'lat': app.config['citylatlon'][city]['lat'],
                'lon': app.config['citylatlon'][city]['lon']}
        with open(info_path, 'w') as info_file:
            json.dump(info, info_file)
            info_file.close()

        return identifier

    @app.route("/result/<identifier>", methods=['GET'])
    def result(identifier):
        # load info
        data_path = path.join(app.config['result_folder'], identifier)
        with open(path.join(data_path, 'info.json'), 'r') as info_file:
            info = json.load(info_file)
            info_file.close()

        return render_template('kml.html',
                               lat=info['lat'],
                               lon=info['lon'],
                               kml=path.join(data_path, 'data.kml'),
                               identifier=identifier,
                               city=info['city'],
                               legend=info['legend'])

    @app.route("/kml/<identifier>", methods=['GET'])
    def deliver(identifier):
        identifier = secure_filename(identifier)
        kml_path = path.join(getcwd(),
                             app.config['result_folder'],
                             identifier,
                             'data.kml')
        print(kml_path)
        if path.exists(kml_path):
            return send_file(kml_path)
        else:
            return "File not found!"

    return app
