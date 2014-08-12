#!/usr/bin/python

import os, sys, flask, json
from flask import request, render_template, send_from_directory, current_app
#from ..model.database import db

from autoscheduler import s4as

index_page = flask.Blueprint("index_page", __name__)

@index_page.route('/autoscheduler', methods=['GET'])
def func_name():
    
    # Get parameters from URL
    mjd = int(request.args.get("mjd", -1))
    surveys = request.args.get("surveys", 'apogee,eboss,manga').split(',')
    mode = request.args.get("mode", 'observing')
    verbose = bool(request.args.get("v", False))
    ascii = bool(request.args.get("ascii",False))
    
    if mode == 'planning': plan = True
    else: plan = False

    plugresults = s4as.run_scheduler(plan=plan, mjd=mjd, surveys=surveys, loud=verbose)
    

    if ascii:
    	return json.dumps(plugresults, sort_keys=True, indent=4, separators=(',', ':'))
    else:
    	return flask.jsonify(**plugresults)

