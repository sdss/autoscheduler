#!/usr/bin/python

import os
import sys
import flask
from flask import request, render_template, send_from_directory, current_app
from ..model.database import db

import s4as

index_page = flask.Blueprint("index_page", __name__)

@index_page.route('/', methods=['GET'])
def func_name():
    ''' Documentation here. '''
    templateDict = {}

    plugresults = s4as.run_scheduler()

    session = db.Session()

    return flask.jsonify(**plugresults)
#    return render_template("index.html", **templateDict)

