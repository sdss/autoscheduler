#!/usr/bin/python

# -------------------------------------------------------------------
# Import statements
# -------------------------------------------------------------------
import sys

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, relation, exc, column_property, backref
from sqlalchemy import orm
from sqlalchemy.orm.session import Session
from sqlalchemy import String # column types, only used for custom type definition
from sqlalchemy import func # for aggregate, other functions

#from platedb.ModelClasses import *

#try:
#	import hooloovookit.DatabaseConnection
#	db = hooloovookit.DatabaseConnection.DatabaseConnection()
#except ImportError:
#	print "Couldn't find DatabaseConnection\nDid you setup hooloovookit before running?"
#	sys.exit(1)

print "Importing PlateDB Model Classes..."
from autoscheduler.plateDBtools.database.apo.platedb.ModelClasses import *

try:
    from autoscheduler.plateDBtools.database.connections.APODatabaseAdminLocalConnection import db
except:
    print "Problem loading platedb, did you 'setup' the product?"
    sys.exit(0)


''' Notes worth reading!
* SQLAlchemy does not assume that deletes cascade: you have to tell it to do so!
  see: http://www.sqlalchemy.org/docs/05/ormtutorial.html#deleting
'''

# ========================
# Define database classes
# ========================
Base = db.Base
        
class Quicklook(Base):
    __tablename__ = 'quicklook'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<Quicklook: pk=%s>" % self.pk
        
class QuicklookPrediction(Base):
    __tablename__ = 'quicklook_prediction'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<QuicklookPrediction: pk=%s>" % self.pk
    
class Quicklook60(Base):
    __tablename__ = 'quicklook60'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<Quicklook60: pk=%s>" % self.pk

class RequiredFitsKeywords(Base):
    __tablename__ = 'required_fitskeywords'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<RequiredFitsKeywords: pk=%s>" % self.pk
        
class Quickred(Base):
    __tablename__ = 'quickred'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<Quickred: pk=%s>" % self.pk
        
class ApogeeSnrGoals(Base):
    __tablename__ = 'apogee_snr_goals'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<ApogeeSnrGoals: pk=%s>" % self.pk
        
class Quicklook60Repspec(Base):
    __tablename__ = 'quicklook60_repspec'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<Quicklook60Repspec: pk=%s>" % self.pk

class RequiredFitsKeywordsError(Base):
    __tablename__ = 'required_fitskeywords_error'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<RequiredFitsKeywordsError: pk=%s>" % self.pk
        
class QuickredSpectrum(Base):
    __tablename__ = 'quickred_spectrum'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<QuickredSpectrum: pk=%s>" % self.pk
        
class QuickredImbinzoom(Base):
    __tablename__ = 'quickred_imbinzoom'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<Quickred_imbinzoom: pk=%s>" % self.pk
        
class Quicklook60Imbinzoom(Base):
    __tablename__ = 'quicklook60_imbinzoom'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<Quicklook60Imbinzoom: pk=%s>" % self.pk
        
        
class FitsKeywordsErrorType(Base):
    __tablename__ = 'fitskeywords_errortype'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}
    
    def __repr__(self):
        return "<FitsKeywordsErrortype: pk=%s>" % self.pk
        
class Reduction(Base):
    __tablename__ = 'reduction'
    __table_args__ = {'autoload' : True, 'schema' : 'apogeeqldb'}

    def __repr__(self):
        return "<Reduction: pk=%s>" % self.pk
        
        
# ========================
# Define relationships
# ========================

QuicklookPrediction.quicklook = relation(Quicklook, backref="predictions")

Quicklook60.quicklook = relation(Quicklook, backref="quicklook60")

#RequiredFitsKeywords.quicklook = relation(Quicklook, backref="fitskeywords")

#These are the tables that are linked to platedb.
#------------------------------------------------
Quickred.exposure = relation(Exposure, backref=backref("quickred",uselist=False))
Quicklook.exposure = relation(Exposure, backref="quicklook")
Reduction.exposure = relation(Exposure, backref=backref("reduction",uselist=False))


#This relationship does not totally exist yet in the schema. Need to add
#apogee_snr_goals_pk to quickred table and quicklook table
#--------------------------------------
#Quickred.snrGoals = relation("ApogeeSnrGoals, backref="quickred")
#Quicklook.snrGoals = relation("ApogeeSnrGoals, backref="quicklook")

Quicklook60Repspec.quicklook60 = relation(Quicklook60, backref="repspecs")

RequiredFitsKeywordsError.quicklook = relation(Quicklook, backref = "errors")

QuickredSpectrum.quickred = relation(Quickred, backref="spectrums")

QuickredImbinzoom.quickred = relation(Quickred, backref="qrImbinzooms")

Quicklook60Imbinzoom.quicklook60 = relation(Quicklook60, backref="ql60Imbinzooms")

RequiredFitsKeywordsError.type = relation(FitsKeywordsErrorType, backref="keywordsError")








