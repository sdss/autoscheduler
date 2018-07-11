#!/usr/bin/env python
# encoding: utf-8
"""
CallableConnection.py

Created by José Sánchez-Gallego on 2 Apr 2014.
Licensed under a 3-clause BSD license.

Revision history:
    2 Apr 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
import os
from autoscheduler.plateDBtools.database.DatabaseConnection import DatabaseConnection


DB_CONFIG = {
    'user': 'sdss3',
    'password': '4-surveys',
    'database': 'apo_platedb',
    'host': 'localhost',
    'port': 5432
}


class CallableConnection(object):
    """Creates a new connection based on an input configuration dict."""

    def __init__(self, db_config=None, **kwargs):

        if db_config is None:
            db_config = DB_CONFIG.copy()
        elif isinstance(db_config, dict):
            for key in DB_CONFIG:
                if key not in db_config:
                    db_config[key] = DB_CONFIG[key]
        else:
            raise TypeError('db_config is not a dictionary.')

        if 'PLATEDB_USER' in os.environ:
            db_config['user'] = os.environ['PLATEDB_USER']
        if 'PLATEDB_PASSWORD' in os.environ:
            db_config['password'] = os.environ['PLATEDB_PASSWORD']
        if 'PLATEDB_HOST' in os.environ:
                db_config['host'] = os.environ['PLATEDB_HOST']
        if 'PLATEDB_PORT' in os.environ:
                db_config['port'] = os.environ['PLATEDB_PORT']

        # The database connection string depends on the
        # version of SQLAlchemy.
        # sa_major_version = sqlalchemy.__version__[0:3]

        # if sa_major_version == '0.5':
        #     database_connection_string = 'postgres://%s@%s:%s/%s' % \
        #     (db_config['user'], db_config['host'],
        #      db_config['port'], db_config['database'])
        # elif sa_major_version >= '0.6':

        database_connection_string = 'postgresql+psycopg2://%s:%s@%s:%s/%s' % \
            (db_config['user'], db_config['password'],
             db_config['host'], db_config['port'], db_config['database'])

        # Intial database connection creation and instances to be exported.
        db = DatabaseConnection(
            database_connection_string=database_connection_string)

        self.engine = db.engine
        self.metadata = db.metadata
        self.Session = db.Session
        # Base = declarative_base(bind=engine)
        self.Base = db.Base

        # ---
        # Test if 'db' is defined, otherwise define it.
        # This is to ensure that mutiple engines are not created
        # (DatabaseConnection class is a singleton).
        # ---
        # try:
        # 	 db = DatabaseConnection() # fails if not previously defined
        # except NameError:
        #    db = DatabaseConnection(
        #        database_connection_string=database_connection_string)
        # engine = db.engine
        # metadata = db.metadata
        # Session = db.Session
        # #Base = declarative_base(bind=engine)
        # Base = db.Base
