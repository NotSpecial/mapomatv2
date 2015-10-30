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

    # Make dir
    if not path.exists("kml_files"):
        makedirs("kml_files")

    with open(path.join(_ROOT, "mapomat.dat"), 'rb') as f:
        # u = pickle._Unpickler(f)
        # u.encoding = 'latin1'
        data = pickle.load(f)

    app.config.update(data)

    @app.route("/", methods=['GET'])
    def hello():
        return render_template(
            'hello.html',
            city_categories=app.config['city_categories'],
            super_categories=app.config['super_categories'],
            categories=app.config['categories'],
        )

    @app.route("/", methods=['POST'])
    def result():
        city = request.form['city']
        sup = [int(item) for item in request.form.getlist('supercat')]
        sub = [literal_eval(item) for item in request.form.getlist('subcat')]

        dicts = {key: app.config['grids'][city].get(key, None)
                 for key in (sub + sup)}

        colors = request.form['colors']

        if len(dicts) > 0:
            legend = {}
            for data in dicts:
                legend[data['name']] = data['color']
            name = density_kml(
                city,
                dicts,
                app.config['borders'],
                colors,
                scaling=lambda x: x ** (0.6)
            )

        else:
            name = ""
            legend = {"Nothing selected": "ffffff"}

        return render_template('kml.html',
                               lat=app.config['citylatlon'][city]['lat'],
                               lon=app.config['citylatlon'][city]['lon'],
                               kml=name,
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
