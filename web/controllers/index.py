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
    
    # Get parameters from URL
    mjd = int(request.args.get("mjd", -1))
    surveys = request.args.get("surveys", 'apogee,eboss,manga').split(',')
    mode = request.args.get("mode", 'observing')
    verbose = bool(request.args.get("v", False))
    
    if mode == 'planning': plan = True
    else: plan = False

    plugresults = s4as.run_scheduler(plan=plan, mjd=mjd, surveys=surveys, loud=verbose)
    


    #session = db.Session()

    return flask.jsonify(**plugresults)

