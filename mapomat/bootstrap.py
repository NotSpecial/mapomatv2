# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file
from werkzeug import secure_filename

from ast import literal_eval
from os import path, makedirs, getcwd
import pickle

from .kml_creation import density_kml


def create_app():
    _ROOT = path.abspath(path.dirname(__file__))
    temp_fold = path.join(_ROOT, "templates")
    app = Flask(__name__, template_folder=temp_fold)
    app.config.from_object('mapomat.config')

    # Make dir
    if not path.exists("kml_files"):
        makedirs("kml_files")

    with open(path.join(_ROOT, "mapomat.dat"), 'rb') as f:
        # u = pickle._Unpickler(f)
        # u.encoding = 'latin1'
        data = pickle.load(f)

    app.config.update(data)

    app.config['KML_URL'] = app.config['BASE_URL'] + "kml/"

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
            name, legend = density_kml(
                city,
                supercats,
                subcats,
                app.config['df'],
                app.config['cells']
            )

            url = app.config['KML_URL'] + name
        else:
            url = ""
            legend = {"Nothing selected": "ffffff"}

        return render_template('kml.html',
                               lat=app.config['citylatlon'][city]['lat'],
                               lon=app.config['citylatlon'][city]['lon'],
                               base_url=app.config['BASE_URL'],
                               kml_url=url,
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

    return app
