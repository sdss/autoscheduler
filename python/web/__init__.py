#!/usr/bin/python

from __future__ import print_function

import os
import sys
import socket
from inspect import getmembers, isfunction

import flask

import jinja_filters
from .color_print import print_warning, print_error, print_info

def create_app(debug=False):
    app = flask.Flask(__name__)

    app.debug = debug

    print("{0}App '{1}' created.{2}".format('\033[92m', __name__, '\033[0m')) # to remove later

    # Define custom filters into the Jinja2 environment.
    # Any filters defined in the jinja_env submodule are made available.
    # See: http://stackoverflow.com/questions/12288454/how-to-import-custom-jinja2-filters-from-another-file-and-using-flask
    custom_filters = {name: function
                      for name, function in getmembers(jinja_filters)
                      if isfunction(function)}
    app.jinja_env.filters.update(custom_filters)

    if app.debug == False:
        # --------------------------------------
        # Configuration when running under uWSGI
        # --------------------------------------
        try:
            import uwsgi
            app.use_x_sendfile = True
        except ImportError:
            # not running under uWSGI (and presumably, nginx)
            pass

    # Change the implementation of "decimal" to a C-based version (much! faster)
    try:
        import cdecimal
        sys.modules["decimal"] = cdecimal
    except ImportError:
        pass # no available

    # Determine which configuration file should be loaded based on which
    # server we are running on. This value is set in the uWSGI config file
    # for each server.

    if app.debug: #args['debug']:
        if (os.path.dirname(os.path.realpath(__file__))).find('utah.edu') >= 0:
            server_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              'configuration_files',
                                              'dev-utah.sdss.edu.cfg')
        else:
            server_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              'configuration_files',
                                              'sdss-db4.local.cfg')
    else:
        try:
            import uwsgi
            server_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              'configuration_files',
                                              uwsgi.opt['xxxx']) # to set
        except ImportError:
            print_error("Trying to run in production mode, but not running under uWSGI.\n"
                       "You might try running again with the '--debug' flag.")
            sys.exit(1)

    print("Loading config file: {0}".format(server_config_file))
    app.config.from_pyfile(server_config_file)

    #print(app.config)
    print("Server_name = {0}".format(app.config["SERVER_NAME"]))
    
    # Load Modules as needed
    #execfile(app.config['MODULES_INIT_SCRIPT'], globals())
    #module('load', 'sdss_python_module/trunk')
    #print(os.environ['PYTHONPATH'].split(os.pathsep), sys.path, os.environ['SDSS_PYTHON_MODULE_DIR'])
    #import sdss
    #try:
    #    import sdss
    #except ImportError:
    #    print_error("The Python module 'sdss' could not be loaded.")
    #    sys.exit(1)
    
    
    # This "with" is necessary to prevent exceptions of the form:
    #    RuntimeError: working outside of application context
    with app.app_context():
        from .model.database import db
    
    # -------------------
    # Register blueprints
    # -------------------
    from .controllers.index import index_page

    app.register_blueprint(index_page)

    return app

# Perform early app setup here.
