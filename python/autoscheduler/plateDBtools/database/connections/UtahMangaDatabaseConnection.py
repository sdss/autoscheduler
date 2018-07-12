#!/usr/bin/python

import os
import sys
import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from autoscheduler.plateDBtools.database.DatabaseConnection import DatabaseConnection

'''Utah MaNGA database configuration parameters'''

dbname = "manga"

try: machine = os.environ['HOSTNAME']
except: machine = None

try: localhost = bool(os.environ['MANGA_LOCALHOST'])
except: localhost = machine=='manga'

try: kingspeak = os.environ['UUFSCELL']='kingspeak.peaks'
except: kingspeak = None

if localhost:
    # for connecting to manga database from localhost
    try: user = os.environ['USER']
    except: user = None
    password = None
    host = None
    port = None
elif kingspeak:
    # for connecting to manga database from the manga cluster at Utah
    user = "sdss"
    password = "4-manga"
    host = "manga.wasatch.peaks"
    port = 5432
else:
    # for connecting to manga database from the Utah Namespace
    user = "sdss"
    password = "4-manga"
    host = "manga.sdss.org"
    port = 5432

db_config = {
    'user'     : user,
    'password' : password,
    'database' : dbname,
    'host'     : host,
    'port'     : port
}

# The database connection string depends on the
# version of SQLAlchemy.
#sa_major_version = sqlalchemy.__version__[0:3]

#if sa_major_version == "0.5":
#   database_connection_string = 'postgres://%s@%s:%s/%s' % (db_config["user"], db_config["host"], db_config["port"], db_config["database"])
#elif sa_major_version >= "0.6":


if localhost:
#    database_connection_string = 'postgresql+psycopg2://%(user)s@%(host)s/%(database)s' % db_config
    database_connection_string = 'postgresql+psycopg2:///%(database)s' % db_config
else:
    database_connection_string = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:%(port)i/%(database)s' % db_config



# Intial database connection creation and instances to be exported.
db = DatabaseConnection(database_connection_string=database_connection_string)
engine = db.engine
metadata = db.metadata
Session = db.Session
Base = db.Base

# ---
# Test if "db" is defined, otherwise define it.
# This is to ensure that mutiple engines are not created
# (DatabaseConnection class is a singleton).
# ---
# try:
#   db = DatabaseConnection() # fails if not previously defined
# except NameError:
#   db = DatabaseConnection(database_connection_string=database_connection_string)
#   engine = db.engine
#   metadata = db.metadata
#   Session = db.Session
#   #Base = declarative_base(bind=engine)
#   Base = db.Base
