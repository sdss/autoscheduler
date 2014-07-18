#!/usr/bin/env python
# encoding: utf-8
"""
platedb.py

Created by José Sánchez-Gallego on 30 Mar 2014.
Licensed under a 3-clause BSD license.

Sets up the APO database configuration and creates the objects necessary to
connect to plateDB and mangaDB.

Revision history:
    30 Mar 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
import sys
from . import config

try:
    from hooloovookit.DatabaseConnection import DatabaseConnection
except ImportError as e:
    print('Couldn\'t find DatabaseConnection:', e)
    print('Did you setup hooloovookit before running?')
    sys.exit(1)

# The database connection string depends on the version of SQLAlchemy.
databaseConnectionString = \
    'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}'.format(
        **config['dbConnection'])

# Intial database connection creation and instances to be exported.
db = DatabaseConnection(database_connection_string=databaseConnectionString)
engine = db.engine
metadata = db.metadata
Session = db.Session
Base = db.Base

from platedb import ModelClasses as plateDB
from mangadb import ModelClasses as mangaDB
# from mangadb import SampleModelClasses as mangaSampleDB
