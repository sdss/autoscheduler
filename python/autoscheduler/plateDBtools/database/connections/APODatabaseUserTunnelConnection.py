#!/usr/bin/python

import os
import sys
import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from autoscheduler.plateDBtools.database.DatabaseConnection import DatabaseConnection

'''APO database configuration parameters'''
db_config = {
    'user'     : 'sdssdb',
    'password' : '4-photometry',
    'database' : 'apodb',
    'host'     : 'localhost',
    'port'     : 6000
}

if os.environ.has_key("PLATEDB_USER"):
    db_config['user'] = os.environ["PLATEDB_USER"]
if os.environ.has_key("PLATEDB_PASSWORD"):
    db_config['password'] = os.environ["PLATEDB_PASSWORD"]
if os.environ.has_key("PLATEDB_HOST"):
    db_config['host'] = os.environ["PLATEDB_HOST"]

# The database connection string depends on the
# version of SQLAlchemy.
#sa_major_version = sqlalchemy.__version__[0:3]

#if sa_major_version == "0.5":
#   database_connection_string = 'postgres://%s@%s:%s/%s' % (db_config["user"], db_config["host"], db_config["port"], db_config["database"])
#elif sa_major_version >= "0.6":
database_connection_string = 'postgresql+psycopg2://%s:%s@%s:%s/%s' % (db_config["user"], db_config["password"], db_config["host"], db_config["port"], db_config["database"])

# Intial database connection creation and instances to be exported.
db = DatabaseConnection(database_connection_string=database_connection_string)
engine = db.engine
metadata = db.metadata
Session = db.Session
#Base = declarative_base(bind=engine)
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
