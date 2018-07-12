#!/usr/bin/python

# -------------------------------------------------------------------
# Import statements
# -------------------------------------------------------------------
from decimal import *
#############################################
# This needs to be phased out:
#from hooloovookit.AstronomicalCalculations import *
# In favor of:
#from hooloovookit.astro import *
apo_lat = 32.7802778 # Latitude at APO
apo_lon = 105.820278 # Longitude at APO
#from hooloovookit.astro import moonSkyMag
from autoscheduler.sdssUtilities import Moon
#############################################
import os
import sys
import cPickle as pickle

from textwrap import TextWrapper

from autoscheduler.sdssUtilities import convert, astrodatetime

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, relation, exc, column_property
from sqlalchemy import orm
from sqlalchemy.orm.session import Session
from sqlalchemy import String # column types, only used for custom type definition
from sqlalchemy import func # for aggregate, other functions
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from autoscheduler.plateDBtools.database.DatabaseConnection import DatabaseConnection
# from autoscheduler.plateDBtools.database.apo.catalogdb.ModelClasses import *

import datetime

db = DatabaseConnection()

metadata_pickle_filename = "ModelClasses_apo_platedb.pickle"
#cached_metadata = False
# ------------------------------------------
# Load the cached metadata if it's available
# ------------------------------------------
# NOTE: delete this cache is the database schema changes!!
# TODO: determine this programmatically (may not be possible)
# Only attempt to read/write the cache if the environment
# variable "MODEL_CLASSES_CACHE" is set to "YES".
use_cache = "MODEL_CLASSES_CACHE" in os.environ and os.environ["MODEL_CLASSES_CACHE"] == "YES"
if use_cache:
    cache_path = os.path.join(os.path.expanduser("~"), ".sqlalchemy_cache")
    cached_metadata = None
    if os.path.exists(cache_path):
        try:
            cached_metadata = pickle.load(open(os.path.join(cache_path, metadata_pickle_filename)))
        except IOError:
            # cache file not found
            pass
else:
    cached_metadata = False
# ------------------------------------------


class PluggingException(Exception):
    """Custom class for plugging exceptions. Adds contact information."""

    def __init__(self, message, *args):

        tw = TextWrapper()
        tw.width = 79
        tw.subsequent_indent = ''
        tw.break_on_hyphens = False

        # Adds custom error
        message += '\n\n'
        message += '*' * 79 + '\n'

        addenda = ('If you are not sure of how to solve this problem '
                   'please copy this error message and email to Jose '
                   'Sanchez-Gallego <j.sanchezgallego@uky.edu> and Drew '
                   'Chojnowski <drewski@nmsu.edu> and CC Demitri Muna '
                   '<muna@astronomy.ohio-state.edu> and John Parejko '
                   '<john.parejko@yale.edu>.\n')
        addenda = '\n'.join(tw.wrap(addenda))
        message += addenda + '\n'

        message += '*' * 79 + '\n'

        super(PluggingException, self).__init__(message)


class ActivePluggingException(PluggingException):
    """Custom class for problems with Active Pluggings."""
    pass


''' Notes worth reading!
* SQLAlchemy does not assume that deletes cascade: you have to tell it to do so!
  see: http://www.sqlalchemy.org/docs/05/ormtutorial.html#deleting

  See the definition of Profilometry.measurements for an example.

* You can perform an "order_by" on lists properties, see Profilometry.measurements
  again for an example.


'''
# -----------------------------------------
# This is to hide the warning:
# /Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/site-packages/sqlalchemy/engine/base.py:1265: SAWarning: Did not recognize type 'fibertype' of column 'fiber_type' self.dialect.reflecttable(conn, table, include_columns)
# -----------------------------------------
from sqlalchemy.dialects.postgresql import base as pg
pg.ischema_names['fibertype'] = String
# -----------------------------------------

# -----------------------------------------
# The snippet below is to hide the warning:
# /usr/local/lib/python2.6/dist-packages/sqlalchemy/engine/reflection.py:46: SAWarning: Skipped unsupported reflection of expression-based index q3c_mytable_idx
# -----------------------------------------
import warnings
warnings.filterwarnings(action="ignore", message="Skipped unsupported reflection")
warnings.filterwarnings("ignore", 'Predicate of partial index')
# -----------------------------------------

# ========================
# Define database classes
# ========================
#Base = declarative_base(bind=engine)
Base = db.Base

# Can access the "table" object (if needed somewhere) via:
# plate_table = Plate.__table__

class Cartridge(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.cartridge']
    else:
        __tablename__ = 'cartridge'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'} # requires metadata to work

    def __repr__(self):
        return "<Cartridge: cartridge_id=%s>" % self.number

class Constants(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.constants']
    else:
        __tablename__ = 'constants'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'} # requires metadata to work

    def __repr__(self):
        return "<Constants>"

class Gprobe(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.gprobe']
    else:
        __tablename__ = 'gprobe'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'} # requires metadata to work

    def __repr__(self):
        return "<Gprobe: gprobe=%d cartridge=%s>" % (self.gprobe_id, self.cartridge.number)

class Plugging(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plugging']
    else:
        __tablename__ = 'plugging'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<Plugging: plate=%d cartridge=%d>" % (self.plate.plate_id,
                                  self.cartridge.number)

    @property
    def fscan_datetime(self):
        return convert.mjd2datetime(self.fscan_mjd)

    def scienceExposures(self):
        session = Session.object_session(self)
        return session.query(Exposure).join(Observation, ExposureFlavor) \
                    .filter(Observation.plugging_pk == self.pk) \
                    .filter(ExposureFlavor.label == 'Science').all()  # DM  all()

    def getSumSn2(self, cameras=None):
        session = Session.object_session(self)
        if cameras == None: cameras = ['r1', 'r2', 'b1', 'b2']
        exposures = session.query(Exposure).join(Observation).filter(Observation.plugging==self).all()
        SumSn2=[0,0,0,0]
        for i,camName in enumerate(cameras):
                camera = session.query(Camera).filter_by(label=camName).one()
                for exposure in exposures:
                    cframe = session.query(CameraFrame).filter_by(exposure=exposure).filter_by(camera=camera).one()
		    if cframe.sn2 > 0.2:
                    	 SumSn2[i]= SumSn2[i]+cframe.sn2 #edit
        return SumSn2

    def percentDone(self):
        if len(self.activePlugging) > 0:
            session = Session.object_session(self)

            #- Refresh observations to ensure they are in sync with DB
            r1_sum = float(sum([obs.sumOfCamera('r1') for obs in self.observations]))
            r2_sum = float(sum([obs.sumOfCamera('r2') for obs in self.observations]))
            b1_sum = float(sum([obs.sumOfCamera('b1') for obs in self.observations]))
            b2_sum = float(sum([obs.sumOfCamera('b2') for obs in self.observations]))

            min_r_percent = min([r1_sum, r2_sum]) / float(session.query(BossSN2Threshold).join(Camera).filter(Camera.label == 'r1').one().sn2_threshold) * 100.0
            min_b_percent = min([b1_sum, b2_sum]) / float(session.query(BossSN2Threshold).join(Camera).filter(Camera.label == 'b1').one().sn2_threshold) * 100.0

            percent_done = min([min_r_percent, min_b_percent])

            if percent_done > 100.0: percent_done = 100.0

            return percent_done
        else:
            return 0

    def updateStatus(self):
        session = Session.object_session(self)

        cameras = ['r1', 'r2', 'b1', 'b2']

        exposureExcellent = 1
        exposureBad = 2
        exposureTest = 3
        exposureText = ["", "Excellent", "Bad", "Test"]

        flagAuto = session.query(PluggingStatus).filter_by(pk=0).one()
        flagGood = session.query(PluggingStatus).filter_by(pk=1).one()
        flagIncomplete = session.query(PluggingStatus).filter_by(pk=2).one()
        flagOverGood = session.query(PluggingStatus).filter_by(pk=3).one()
        flagOverIncomplete = session.query(PluggingStatus).filter_by(pk=4).one()

        # If plugging status is overwritten, nothing for us to calculate
        if self.status == flagOverGood or self.status == flagOverIncomplete:
            return 0

        exposures = session.query(Exposure).join(Observation).filter(Observation.plugging==self).all()

        for camName in cameras:
            try:
                camera = session.query(Camera).filter_by(label=camName).one()
                sn2Thresh = session.query(BossSN2Threshold).filter_by(camera=camera).one()

                sumsn2 = 0.0
                goodExposures = 0
                for exposure in exposures:
                    if exposure.status.pk != exposureExcellent:
                        continue
                    else:
                        goodExposures += 1

                    try:
                        cframe = session.query(CameraFrame).filter_by(exposure=exposure).filter_by(camera=camera).one()

                        sn2 = cframe.sn2
                        if sn2 > sn2Thresh.sn2_min:
                            sumsn2 += float(sn2)
                    except sqlalchemy.orm.exc.MultipleResultsFound:
                        print "More than one CameraFrame found.  Expecting only one! \n\n"
                        raise
                    except (sqlalchemy.orm.exc.NoResultFound, KeyError):
                        print "!WARNING:  Could not get sn2 from platedb"
                        pass
                    except:
                        print "Problem loading CameraFrame \n\n"
                        raise

                # Not enough sn2, plugging is incomplete
                if sumsn2 < float(sn2Thresh.sn2_threshold):
                    # Set the plugging status to incomplete
                    self.status = flagIncomplete
                    session.flush()
                    return

                # Not enough exposures, plugging is incomplete
                if goodExposures < float(sn2Thresh.min_exposures):
                    # Set the plugging status to incomplete
                    self.status = flagIncomplete
                    session.flush()
                    return

            except:
                print "Problem calculating sumsn2"
                raise

        # Set the plugging status to complete
        # print "plugging is complete"
        self.status = flagGood
        #print "Plugging Complete"
        session.flush()
        return

    def mangaUpdateStatus(self, status):
        '''Update the plugging status of manga exposures, based on Totoro'''

        session = Session.object_session(self)

        flagAuto = session.query(PluggingStatus).filter_by(pk=0).one()
        flagGood = session.query(PluggingStatus).filter_by(pk=1).one()
        flagIncomplete = session.query(PluggingStatus).filter_by(pk=2).one()
        flagOverGood = session.query(PluggingStatus).filter_by(pk=3).one()
        flagOverIncomplete = session.query(PluggingStatus).filter_by(pk=4).one()

        if status:
        	self.status = flagGood
        else:
        	self.status = flagIncomplete

    def makeActive(self):
        """Makes the plugging active."""

        session = Session.object_session(self)

        cartNo = self.cartridge.number

        # Checks if the plate has already an active plugging
        platePK = self.plate.pk
        activePluggings = session.query(ActivePlugging).all()

        for aP in activePluggings:
            if aP.plugging.plate.pk == platePK and aP.plugging_pk != self.pk:
                warnings.warn('plate {0} is already loaded in cart {1} with a '
                              'different plugging. Removing previous active '
                              'plugging'
                              .format(self.plate.plate_id,
                                      aP.plugging.cartridge.number),
                              UserWarning)
                session.delete(aP)

        # Checks if the plugging is already active
        try:
            activePlugging = session.query(ActivePlugging).filter(
               ActivePlugging.plugging_pk == self.pk).one()
        except MultipleResultsFound:
            raise ActivePluggingException(
                'more than one active plugging for plugging pk={0}. This '
                'should never happen!'.format(self.pk))
        except NoResultFound:
            activePlugging = None

        # If plugging is already active, checks the cart number
        if activePlugging is not None:
            if activePlugging.pk != cartNo:
                raise ActivePluggingException(
                    'plugging pk={0} is already active but its cart number '
                    'does not match the one in the plugging ({1}!={2}). This '
                    'should never happen.'
                    .format(self.pk, activePlugging.pk, cartNo))

            warnings.warn('plugging pk={0} is already active. '
                          'Not doing anything.'.format(self.pk), UserWarning)
            return activePlugging

        # Makes the plugging active
        activePlugging = session.query(ActivePlugging).get(cartNo)
        if activePlugging is not None:
            activePlugging.plugging_pk = self.pk
            session.flush()
        else:
            session.add(ActivePlugging(pk=cartNo, plugging_pk=self.pk))
            session.flush()

        # Check that it worked
        # Checks if the plugging is already active
        try:
            activePlugging = session.query(ActivePlugging).filter(
                ActivePlugging.plugging_pk == self.pk).one()
        except NoResultFound:
            raise ActivePluggingException(
                'something went wrong when trying to make plugging pk={0} '
                'active'.format(self.pk))

        return activePlugging

class ActivePlugging(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.active_plugging']
    else:
        __tablename__ = 'active_plugging'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<Active Plugging: plate=%d cartridge=%d>" % (self.plugging.plate.plate_id,
                                     self.plugging.cartridge.number)

class PlPlugMapM(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.pl_plugmap_m']
    else:
        __tablename__ = 'pl_plugmap_m'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def platePointing(self):
        session = Session.object_session(self) # class method that returns the session this object is in
        try:
            pp = session.query(PlatePointing)\
                .join(Plate, Plugging)\
                .filter(Plate.pk==self.plugging.plate.pk)\
                .filter(PlatePointing.pointing_name==self.pointing_name).one()
                # first filter above: remove degeneracy in relation
        except sqlalchemy.orm.exc.NoResultFound:
            print "A plate pointing for a plugmap (pk=%d) could not be found (plate id=%d, pk=%d)" % \
                (self.pk, self.plugging.plate.plate_id, self.plugging.plate.pk)
            pp = None
        return pp

    def visibility(self):
        '''Retrieves the visiblity range for this plate
           as a map with keys "ha_observable_min" and "ha_observable_max".
           Each value is an array of values corresponding to each pointing.
        '''
        max_found = False
        min_found = False

        visibilities = dict()

        # Just loop over every line in the "file" until the two keys are found.
        # They're near the top, so it won't take long.
        for line in self.file.split("\n"):
            if line[0:17] == "ha_observable_min":
                min_found = True
                visibilities["ha_observable_min"] = [float(x) for x in line[17:].split()]
            elif line[0:17] == "ha_observable_max":
                visibilities["ha_observable_max"] = [float(x) for x in line[17:].split()]
                max_found = True

            if min_found and max_found:
                break

        return visibilities

    def __repr__(self):
        return "<PlPlugMapM file: %s (id=%d)>" % (self.filename, self.pk)


class Plate(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate']
    else:
        __tablename__ = 'plate'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    #def platePointingWithPointingName(self, pname):
    #   session = Session.object_session(self)
    #   try:
    #       pp = session.query(PlatePointing).filter(PlatePointing.pointing_name==pname)
    #   except sqlalchemy.orm.exc.NoResultFound:
    #       pp = None
    #   return pp

    def __repr__(self):
        return "<Plate: plate_id=%s>" % self.plate_id

    def calculatedCompletionStatus(self):
        """ Determine whether the plate is done from
            the pluggings done on that plate"""
        if True not in ["boss" in survey.label.lower() for survey in self.surveys]:
            return "n/a"

        if self.completionStatus.pk == 0: # pk = 0 -> "Automatic"
            return self._automaticCompletionStatus()
        else:
            # If the status is "Force Complete" or "Force Incomplete",
            #   return that status
            return self.completionStatus.label

    def _automaticCompletionStatus(self):
        """ If the plate completion status were automatic, is it complete or incomplete """
        if True not in ["boss" in survey.label.lower() for survey in self.surveys]:
            return "n/a"

        session = Session.object_session(self)
        plug_statuses = session.query(PluggingStatus.label).join(Plugging,Plate).filter(Plate.plate_id == self.plate_id).all()

        for status in [a[0] for a in plug_statuses]:
            if 'Good' in status:
                return 'Complete'
        return 'Incomplete'

    @property
    def firstPointing(self):
        return self.design.pointings[0]

    """
    # LEFT OFF HERE!
    def tilePlatesRecalculate(self, old_completion_status_pk, new_completion_status_pk):
        session = Session.object_session(self)
        if old_completion_status_pk == 0 and new_completion_status_pk == 3 and self._automaticCompletionStatus() == "Complete":
            # Changing from Automatic (complete) to Force Incomplete

            # If the most recent entry in completion_status_history is by "platedb" and is "Do Not Observe,"
            #   change the completion_status back to whatever the entry before that one is
            if len(self.completionStatusHistory) > 0:
                try:
                    mostRecentChange = self.completionStatusHistory[-1]
                    if mostRecentChange.first_name == 'platedb':
                        prevStatus_pk = self.completionStatusHistory[-2].plate_completion_status_pk
                        previousStatus = session.query(PlateCompletionStatus).\
                                        filter(PlateCompletionStatus.pk == prevStatus_pk).one()
                except IndexError:
                    # This could happen if the plate's completion status was only changed once from
                    #   automatic -> do not observe by the script. In that case, the completion status should
                    #   go back to automatic
                    previousStatus = session.query(PlateCompletionStatus).\
                                        filter(PlateCompletionStatus.pk == 0).one() # Automatic
                self.completionStatus = previousStatus
                session.flush()
    """

class Survey(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.survey']
    else:
        __tablename__ = 'survey'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def display_string(self):
        if self.label == None:
            return self.plateplan_name
        else:
            return self.label

    def __repr__(self):
        return "<Survey: %s / %s (pk=%s)>" % (self.label, self.plateplan_name, self.pk)

class PlateRun(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_run']
    else:
        __tablename__ = 'plate_run'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<PlateRun: '%s' (pk=%s)>" % (self.label, self.pk)

class PlateLocation(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_location']
    else:
        __tablename__ = 'plate_location'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class PlateStatus(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_status']
    else:
        __tablename__ = 'plate_status'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<PlateStatus: '%s' (pk=%s)>" % (self.label, self.pk)

class PlateToPlateStatus(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_to_plate_status']
    else:
        __tablename__ = 'plate_to_plate_status'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class PlateCompletionStatus(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_completion_status']
    else:
        __tablename__ = 'plate_completion_status'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class PlateCompletionStatusHistory(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_completion_status_history']
    else:
        __tablename__ = 'plate_completion_status_history'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class Tile(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.tile']
    else:
        __tablename__ = 'tile'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<Tile: id={0} (pk={1})>".format(self.id, self.pk)

    def calculatedCompletionStatus(self):
        """ Determine whether the tile is done from
            whether the plates in it are done"""

        if self.status.pk == 0:
            plates = self.plates

            for plate in plates:
                if 'Complete' in plate.calculatedCompletionStatus():
                    return 'Complete'
                else:
                    pass

            return 'Incomplete'
        else:
            return self.status.label

class TileStatus(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.tile_status']
    else:
        __tablename__ = 'tile_status'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class TileStatusHistory(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.tile_status_history']
    else:
        __tablename__ = 'tile_status_history'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class PlateToSurvey(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_to_survey']
    else:
        __tablename__ = 'plate_to_survey'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class DesignValue(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.design_value']
    else:
        __tablename__ = 'design_value'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class DesignField(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.design_field']
    else:
        __tablename__ = 'design_field'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class Design(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.design']
    else:
        __tablename__ = 'design'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<Design (pk=%s)>" % (self.pk)

    @property
    def designDictionary(self):
        #returns dictionary of key value pairs, as strings
        dv = {}
        for v in self.values:
            dv[v.field.label.lower()] =  v.value
        return dv

    def no_science_targets(self):
        ''' This returns the sum total of science targets as a list
            for each pointing.'''

        session = Session.object_session(self) # class method that returns the session this object is in

        try:
            design_values = session.query(DesignValue).join(Design, DesignField).\
                            filter(DesignValue.design==self).\
                            filter(DesignField.label.ilike("n%_science")).all()

            # create a list, initialized to 0, with the number of pointings
            science_targets = [0]*len(design_values[0].value.split())

            for design_value in design_values:
                for idx, value in enumerate(design_value.value.split()):
                    science_targets[idx] = science_targets[idx] + int(value)
            return science_targets
        except:
            return [0]

    def getDesignId(self):
        ''' This returns the designID of the plate, given the plate object '''

        session = Session.object_session(self)
        try:
            designId = session.query(DesignValue).join(Design,DesignField).\
                                filter(DesignValue.design==self).\
                        filter(DesignField.label.ilike("designid")).one()
            designId = designId.value
            return designId
        except:
            return -1

    def numPlates(self):
        ''' This returns the number of plates in a design, given the design object '''

        session = Session.object_session(self)
        try:
            numPlate = session.query(Plate).join(Design).\
                                filter(Plate.design==self).count()
            return numPlate
        except:
            return -1

    def numObservations(self):
        ''' This returns the number of observations for a design, given the design object '''

        session = Session.object_session(self)
        try:
            numObs = session.query(Observation).join(Plugging,Plate,Design).\
                             filter(Design.pk==self.pk).count()
            return numObs
        except:
            return -1

    def getRa(self):
        ''' This returns the ra and dec for a design, given the design object '''

        session = Session.object_session(self)
        try:
            ra = session.query(DesignValue).join(Design,DesignField).\
                         filter(DesignValue.design==self).\
                     filter(DesignField.label.ilike("racen")).one()
            ra = ra.value
            return ra
        except:
            return -1

    def getDec(self):
        ''' This returns the ra and dec for a design, given the design object '''

        session= Session.object_session(self)
        try:
            dec = session.query(DesignValue).join(Design,DesignField).\
                         filter(DesignValue.design==self).\
                                     filter(DesignField.label.ilike("deccen")).one()
            dec = dec.value
            return dec
        except:
            return -1


class PluggingToInstrument(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plugging_to_instrument']
    else:
        __tablename__ = 'plugging_to_instrument'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class Exposure(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.exposure']
    else:
        __tablename__ = 'exposure'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def mjd(self):
    	'''
    	Returns the *SDSS* MJD. See line ~140 (the mjd4Gang function) here
    	for notes on this value.
    	https://svn.sdss.org/deprecated/operations/iop/trunk/etc/iopUtils.tcl
    	'''
        return int(float(self.start_time) / 86400.0 + 0.3)

    def startTimeUT(self):
        #return convert.mjd2datetime(self.mjd())
        return convert.mjd2ut(Decimal(self.start_time) / Decimal('86400'))


    def getHeaderValue(self, headerLabel):

        session=Session.object_session(self)
        try:
            keyValue = session.query(ExposureHeaderValue.value).join(Exposure,ExposureHeaderKeyword).\
                       filter(Exposure.pk==self.pk).\
                           filter(ExposureHeaderKeyword.label==headerLabel).first()


            return keyValue
        except:
            return '--'

    def whichLamp(self):
        session=Session.object_session(self)

        returnValue = '--'
        try:
            keyValue = session.query(ExposureHeaderValue).join(Exposure,ExposureHeaderKeyword).\
                           filter(Exposure.pk==self.pk).\
                           filter(ExposureHeaderKeyword.label=='LAMPTHAR').first()
            if keyValue.value.strip() == '1':
                returnValue = 'ThAr'

        except:
            pass

        try:
            keyValue = session.query(ExposureHeaderValue).join(Exposure,ExposureHeaderKeyword).\
                               filter(Exposure.pk==self.pk).\
                               filter(ExposureHeaderKeyword.label=='LAMPUNE').first()
            if keyValue.value.strip() == '1':
                returnValue = 'UNe'

        except:
            pass
        try:
            keyValue = session.query(ExposureHeaderValue).join(Exposure,ExposureHeaderKeyword).\
                               filter(Exposure.pk==self.pk).\
                               filter(ExposureHeaderKeyword.label=='LAMPQRTZ').first()
            if keyValue.value.strip() == '1':
                returnValue = 'QRTZ'
        except:
            pass

        return returnValue

    def calcSecZ(self):

        session = Session.object_session(self)

        try:
            keyValue = session.query(ExposureHeaderValue).join(Exposure,ExposureHeaderKeyword).\
                                   filter(Exposure.pk==self.pk).\
                                   filter(ExposureHeaderKeyword.label=='ALT').first()
            secZ = 1 / math.cos(90.0 - float(keyValue.value))
            return round(secZ,3)
        except:
            return '--'

class ExposureFlavor(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.exposure_flavor']
    else:
        __tablename__ = 'exposure_flavor'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<ExposureFlavor: %s (pk=%s)>" % (self.label, self.pk)

class ExposureStatus(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.exposure_status']
    else:
        __tablename__ = 'exposure_status'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<ExposureStatus: %s (pk=%s)>" % (self.label, self.pk)

class CameraFrame(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.camera_frame']
    else:
        __tablename__ = 'camera_frame'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}


#This should not go here!
#-----------------------
#from apogeeqldb.ModelClasses import *

class Observation(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.observation']
    else:
        __tablename__ = 'observation'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def startTime(self):
        session = Session.object_session(self) # class method that returns the session this object is in

        try:
            start_time = session.query(func.min(Exposure.start_time)).\
                            join(Observation).filter(Exposure.observation==self).one()
        except:
            return None

        return start_time[0] # item returned seems to be a tuple

    def endTime(self):
        session = Session.object_session(self) # class method that returns the session this object is in

        try:
            end_time = session.query(func.max(func.sum(Exposure.start_time, Exposure.exposure_time))).\
                            join(Observation).filter(Exposure.observation==self).one()
        except:
            return None

        return end_time[0] # item returned seems to be a tuple

    def sumOfCamera(self, cameraLabel, mjd=None):
        session = Session.object_session(self) # class method that returns the session this object is in

        if mjd != None:
            totsn2 = sum([sum([cf.sn2 for cf in x.cameraFrames if cf.camera.label == cameraLabel and cf.exposure.flavor.label=='Science' and cf.exposure.status.label=='Good' and cf.sn2 > 0.2]) for x in self.exposures if mjd == int(x.start_time/(24*60*60))])
        else:
            totsn2 = sum([sum([cf.sn2 for cf in x.cameraFrames if cf.camera.label == cameraLabel and cf.exposure.flavor.label=='Science' and cf.exposure.status.label=='Good' and cf.sn2 > 0.2]) for x in self.exposures])

        return totsn2

    #def sumOfApogeePlate(self):

        #session = Session.object_session(self)

        ##print "Num of EXP: ", len(self.exposures)
        #return sum([exp.quickred[0].snr_standard for exp in self.exposures if exp.exposure_flavor_pk>0 and exp.flavor.label=='Object' and len(exp.quickred)>0])


    def numOfScienceExposures(self):
        session = Session.object_session(self)

        try:
            value = session.query(Exposure).join(ExposureFlavor).\
                        filter(Exposure.observation_pk==self.pk).\
                        filter(ExposureFlavor.label=='Science').count()
            return value
        except:
            return -1

    def numOfObjectExposures(self):
        session = Session.object_session(self)

        try:
            value = session.query(Exposure).join(ExposureFlavor).\
                            filter(Exposure.observation_pk==self.pk).\
                            filter(ExposureFlavor.label=='Object').count()
            return value
        except:
            return -1

    def numOfApogeePlates(self):
        session = Session.object_session(self)

        try:
            value = session.query(Plate).join(Plugging,Observation,PlateToSurvey,Survey).\
                            filter(Observation.mjd == self.mjd).\
                    filter(Survey.label=="APOGEE").count()
            return value
        except:
            return -1

    def __repr__(self):
        return "<Observation: mjd = %s (pk=%s)>" % (str(self.mjd), self.pk)

class ObservationStatus(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.observation_status']
    else:
        __tablename__ = 'observation_status'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<ObservationStatus: %s (pk=%s)>" % (self.label, self.pk)

    # example static class
#   def with_id(id):
#       # do something
#       # return
#   with_id = staticmethod(with_id)

class Pointing(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.pointing']
    else:
        __tablename__ = 'pointing'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def platePointing(self, plateid):
        session = Session.object_session(self)
        try:
            pp = session.query(PlatePointing)\
                .join(Plate, Pointing)\
                .filter(Pointing.pk==self.pk)\
                .filter(Plate.plate_id==plateid).one()
        except sqlalchemy.orm.exc.NoResultFound:
            print "A PlatePointing record for this pointing (pk=%d) was not be found (plate id=%d)" % \
                (self.pk, plateid)
            print "It looks like that plate needs to be loaded into the database (see $PLATEDB_DIR/bin/platePlans2db.py)"
            pp = None
        return pp

class PlateInput(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_input']
    else:
        __tablename__ = 'plate_input'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class PlatePointing(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_pointing']
    else:
        __tablename__ = 'plate_pointing'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<PlatePointing: plate=%s, pointing=%s (id=%d)>" % (self.plate.plate_id, self.pointing_name, self.pk)

    def times(self, datetimeObj):
        times_for_pp = dict()

        # All in degrees
        ra = float(self.pointing.center_ra)
        dec = float(self.pointing.center_dec)
        ha = float(self.hour_angle)
        LST = (ra + ha) / 15.0 # convert to hours

        gmst_h, gmst_m, gmst_s = convert.lst2gmst(apo_lon, LST)
        utc = convert.gmst2utcDatetime(datetime.datetime(datetimeObj.year, datetimeObj.month, datetimeObj.day, gmst_h, gmst_m, int(gmst_s)))

        times_for_pp["nominal"] = utc

        try:
            # error is thrown when ha_min or ha_max == None (i.e. not available)
            ha_min = float(self.ha_observable_min)
            ha_max = float(self.ha_observable_max)

            LST_min = (ra + ha_min) / 15.0 # convert to hours
            gmst_min_h, gmst_min_m, gmst_min_s = convert.lst2gmst(apo_lon, LST_min)
            utc_min = convert.gmst2utcDatetime(datetime.datetime(datetimeObj.year, datetimeObj.month, datetimeObj.day, gmst_min_h, gmst_min_m, int(gmst_min_s)))

            LST_max = (ra + ha_max) / 15.0 # convert to hours
            gmst_max_h, gmst_max_m, gmst_max_s = convert.lst2gmst(apo_lon, LST_max)
            utc_max = convert.gmst2utcDatetime(datetime.datetime(datetimeObj.year, datetimeObj.month, datetimeObj.day, gmst_max_h, gmst_max_m, int(gmst_max_s)))

            times_for_pp["min"] = utc_min
            times_for_pp["max"] = utc_max

        except TypeError:
            # default to +- 1hr if values not found in database
            times_for_pp["min"] = utc + datetime.timedelta(hours=-1)
            times_for_pp["max"] = utc + datetime.timedelta(hours=+1)

        # correct for dates crossing the day line
        if times_for_pp["min"] > times_for_pp["nominal"]:
            times_for_pp["min"] = times_for_pp["min"] + datetime.timedelta(days=-1)

        if times_for_pp["max"] < times_for_pp["nominal"]:
            times_for_pp["max"] = times_for_pp["max"] + datetime.timedelta(days=+1)

        return times_for_pp

    def skyBrightness(self, datetimeObj=None, mjd=None):
        if datetimeObj == None and mjd == None:
            return None
        elif mjd == None and datetimeObj != None:
            mjd = convert.datetime2mjd(datetimeObj)
        elif datetimeObj == None and mjd != None:
            mjd = float(mjd)
        else:
            return None

        # Create an RADec object for the current pointing
        ra = float(self.pointing.center_ra)
        dec = float(self.pointing.center_dec)

        skyMag = Moon.mjdRADec2skyBright(mjd, ra, dec)

        if skyMag == 0.0:
            skyMag = "--"
        else:
            skyMag = "%.1f" % skyMag

        return skyMag

    def HA(self, datetimeObj=datetime.datetime.now()):
        # Compute the hour angle of the platePointing for the given datetime object
        gmstDatetime = convert.utcDatetime2gmst(datetimeObj)
        lst = convert.gmstDatetime2lstDatetime(apo_lon, gmstDatetime)

        lstDegrees = convert.datetime2decimalTime(lst)*15.0
        ha = lstDegrees - float(self.pointing.center_ra)

        if ha < -180.0: ha += 360.0
        elif ha > 180.0: ha -= 360.0

        return ha

    def altitude(self, datetimeObj=datetime.datetime.now()):
        ra = float(self.pointing.center_ra)
        dec = float(self.pointing.center_dec)
        alt,az = convert.raDec2AltAz(ra, dec, apo_lat, apo_lon, datetimeObj)

        return alt

    def azimuth(self, datetimeObj=datetime.datetime.now()):
        ra = float(self.pointing.center_ra)
        dec = float(self.pointing.center_dec)
        alt,az = convert.raDec2AltAz(ra, dec, apo_lat, apo_lon, datetimeObj)

        return az

class PlatePointingToPointingStatus(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_pointing_to_pointing_status']
    else:
        __tablename__ = 'plate_pointing_to_pointing_status'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class PointingStatus(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.pointing_status']
    else:
        __tablename__ = 'pointing_status'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class Instrument(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.instrument']
    else:
        __tablename__ = 'instrument'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class Profilometry(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.profilometry']
    else:
        __tablename__ = 'profilometry'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class ProfilometryMeasurement(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.prof_measurement']
    else:
        __tablename__ = 'prof_measurement'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<ProfilometryMeasurement: Num: %s (%s,%s,%s,%s,%s)>" % (self.number, self.r1, self.r2, self.r3, self.r4, self.r5)

class ProfilometryTolerances(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.prof_tolerances']
    else:
        __tablename__ = 'prof_tolerances'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class Camera(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.camera']
    else:
        __tablename__ = 'camera'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class BossSN2Threshold(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.boss_sn2_threshold']
    else:
        __tablename__ = 'boss_sn2_threshold'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class BossPluggingInfo(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.boss_plugging_info']
    else:
        __tablename__ = 'boss_plugging_info'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class PluggingStatus(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plugging_status']
    else:
        __tablename__ = 'plugging_status'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

class PlateHolesFile(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_holes_file']
    else:
        __tablename__ = 'plate_holes_file'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<PlateHolesFile: pk=%s>" % self.pk

class Fiber(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.fiber']
    else:
        __tablename__ = 'fiber'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<Fiber: number:%d pk=%s>" % (self.fiber_id, self.pk)

class ExposureHeaderValue(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.exposure_header_value']
    else:
        __tablename__ = 'exposure_header_value'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def keyword(self):
        if self.keyword is None:
            return None
        else:
            return self.keyword.label

    def __repr__(self):
        return "<ExposureHeaderValue: %s (keyword=%s) pk=%s>" % (self.value, self.keyword.label, self.pk)

class ExposureHeaderKeyword(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.exposure_header_keyword']
    else:
        __tablename__ = 'exposure_header_keyword'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<ExposureHeaderKeyword: %s (pk=%s)>" % (self.label, self.pk)

class PlateHole(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_hole']
    else:
        __tablename__ = 'plate_hole'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<PlateHole: (%s, %s) pk=%s>" % (str(self.xfocal), str(self.yfocal), self.pk)

class CmmMeas(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.cmm_meas']
    else:
        __tablename__ = 'cmm_meas'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def getHoles(self, label):
        """Returns a list of holes with plateHoleType.label == label."""

        session = Session.object_session(self)
        return session.query(PlateHole).join(
            HoleMeas, PlateHoleType, CmmMeas).filter(
                CmmMeas.pk == self.pk,
                PlateHoleType.label == label).all()

    def __repr__(self):
        return "<CmmMeas pk=%s>" % (self.pk,)


class HoleMeas(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.hole_meas']
    else:
        __tablename__ = 'hole_meas'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<HoleMeas: pk=%s>" % (self.pk,)

class PlateHoleType(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.plate_hole_type']
    else:
        __tablename__ = 'plate_hole_type'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<PlateHoleType: %s (pk=%s)>" % (self.label, self.pk)

class ObjectType(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.object_type']
    else:
        __tablename__ = 'object_type'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<ObjectType: %s (pk=%s)>" % (self.label, self.pk)

class ApogeeThreshold(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.apogee_threshold']
    else:
        __tablename__ = 'apogee_threshold'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

    def __repr__(self):
        return "<ApogeeThreshold: pk=%s>" % self.pk

class SurveyMode(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['platedb.survey_mode']
    else:
        __tablename__ = 'survey_mode'
        __table_args__ = {'autoload' : True, 'schema' : 'platedb'}

# ======================================================================
# ======================================================================

def dbo_with_pk(session, table_class, id):

    try:
        dbo = session.query(table_class).filter_by(pk=id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        dbo = None
    except sqlalchemy.orm.exc.MultipleResultsFound:
        print "ERROR: ModelClasses.py:dbo_with_pk: There is a unique constraint violation on your primary key in table '%s'!" + A.__name__

    return dbo

# ========================
# Define relationships
# ========================

# Ref: http://www.sqlalchemy.org/docs/05/reference/ext/declarative.html?highlight=declarative_base#configuring-relations
#
# Format:
# ParentTable.relationName = relation(ForeignTable, primaryJoin=ParentTable.key == ForeignTable.key, backref="reverseRelationName")
# Template = relation(, primaryjoin=. == ., backref="")
#

# --------------------------
# Relationships from "Plate"
# --------------------------
# To one relationships
PlateRun.plates = relation(Plate, order_by=Plate.plate_id, backref="platerun")
Plate.design    = relation(Design, primaryjoin=Plate.design_pk == Design.pk, backref="plate")
Plate.location  = relation(PlateLocation, backref="plates")
# Many to many relationships
Plate.surveys   = relation(Survey,
                           secondary=PlateToSurvey.__table__, # note that this is the Table, not the object class!
                           backref="plates")

Plate.pluggings = relation(Plugging, order_by=Plugging.fscan_mjd, backref="plate")
Plate.cmmMeasurements = relation(CmmMeas, backref="plate")
Plate.currentSurveyMode = relation(SurveyMode, primaryjoin=Plate.current_survey_mode_pk == SurveyMode.pk, backref="plates")



PlatePointing.plate = relation(Plate, backref="plate_pointings")
PlatePointing.pointing = relation(Pointing, backref="plate_pointings")
PlatePointing.observations = relation(Observation,
                                      order_by=Observation.mjd.desc(),
                                      backref="plate_pointing")

Plate.statuses = relation('PlateStatus',
                          secondary=PlateToPlateStatus.__table__,
                          backref="plates")

Plate.completionStatus = relation(PlateCompletionStatus, backref='plates')

PlateCompletionStatusHistory.plate = relation(Plate, backref='completionStatusHistory')
PlateCompletionStatusHistory.completionStatus = relation(PlateCompletionStatus, backref='completionStatusHistory')

Tile.plates = relation(Plate, order_by=Plate.plate_id, backref="tile")
Tile.status = relation(TileStatus, backref='tiles')

TileStatusHistory.tile = relation(Tile, backref='statusHistory')
TileStatusHistory.status = relation(TileStatus, backref='statusHistory')

def ra(self):
    return self.plates[0].plate_pointings[0].pointing.center_ra
def dec(self):
    return self.plates[0].plate_pointings[0].pointing.center_dec

Tile.ra = ra
Tile.dec = dec

# ---------------------------
# Relationships from "Design"
# ---------------------------
Design.pointings = relation(Pointing, backref="design")
Design.values = relation(DesignValue, backref="design")
Design.inputs = relation(PlateInput, backref="design")

#DesignValue.design = relation(Design, primaryjoin=DesignValue.design_pk == Design.pk, backref="values")
DesignValue.field = relation(DesignField, backref="design_values")

# ---------------------------
# Relationships from Plugging
# ---------------------------
Plugging.cartridge = relation(Cartridge, backref="pluggings")
Plugging.plplugmapm = relation(PlPlugMapM, backref="plugging")
Plugging.instruments = relation(Instrument, secondary=PluggingToInstrument.__table__, backref="pluggings")
Plugging.observations = relation(Observation, backref="plugging")
Plugging.activePlugging = relation(ActivePlugging, backref="plugging")
Plugging.status = relation(PluggingStatus, backref="pluggings")

# ------------------------------------
# Observation & Exposure relationships
# ------------------------------------
Observation.status = relation(ObservationStatus, backref="observations")
#Exposure.observation = relation(Observation,
#                               backref="exposures",
#                               order_by="Exposure.start_time")
Observation.exposures = relation(Exposure,
                                 backref="observation",
                                 order_by="Exposure.start_time, Exposure.exposure_no")

Exposure.camera = relation(Camera, backref="exposures")
Exposure.survey = relation(Survey, backref="exposures")
Exposure.flavor = relation(ExposureFlavor, backref="exposures")
Exposure.status = relation(ExposureStatus, backref="exposures")
Exposure.headerValues = relation(ExposureHeaderValue,
                                order_by="ExposureHeaderValue.index",
                                backref="exposure")
ExposureHeaderValue.header = relation(ExposureHeaderKeyword, backref="headerValues")
Exposure.surveyMode = relation(SurveyMode, backref="exposures")

Camera.instrument = relation(Instrument, backref="cameras")
CameraFrame.camera = relation(Camera, backref="cameraFrames")
CameraFrame.exposure = relation(Exposure, backref="cameraFrames")

Gprobe.cartridge = relation(Cartridge, backref="gprobes")

BossPluggingInfo.plugging = relation(Plugging, backref="bossPluggingInfo")
BossSN2Threshold.camera = relation(Camera, backref="bossSN2Threshold")

Profilometry.plugging = relation(Plugging, backref='profilometries')

Profilometry.measurements = relation(ProfilometryMeasurement,
                                     backref="profilometry",
                                     order_by="ProfilometryMeasurement.number",
                                     cascade="all, delete, delete-orphan")
Profilometry.tolerances = relation(ProfilometryTolerances, backref="profilometry")
ProfilometryTolerances.survey = relation(Survey, backref="profilometry_tolerances")

PlateHolesFile.plate = relation(Plate, backref="plateHolesFile")

PlPlugMapM.fibers = relation(Fiber, backref="plPlugMapM")
#Fiber.plplugmapm = relation(PlPlugMapM, backref="fibers")

Fiber.plateHoles = relation(PlateHole, backref="fiber")

PlateHole.plateHoleType = relation(PlateHoleType, backref="plateHole")
PlateHole.plateHolesFile = relation(PlateHolesFile, backref="plateHole")
PlateHole.objectType = relation(ObjectType, backref="plateHole")

CmmMeas.measHoles = relation(HoleMeas, backref="cmmMeas")

HoleMeas.plateHole = relation(PlateHole, backref="holeMeas")


# This should be uncommented when the catalogdb integration is complete -
# I don't want to existing code to break before then! [demitri]
#PlateHole.catalogObject = relation(CatalogObject, backref="plateHoles")

''' This is a convenience method that excapsulates the query
    to retrieve the specific PlatePointing for a given PlPlugMapM object.
    Note: do not call this unless the PlPlugMapM object is an a session
          (either from a session.add() statement or having been retrieved from
          the database).
'''
# def platePointing(self):
#   session = Session.object_session(self) # class method that returns the session this object is in
#   try:
#       pp = session.query(PlatePointing)\
#           .join(Plate, Plugging)\
#           .filter(Plate.pk==self.plugging.plate.pk)\
#           .filter(PlatePointing.pointing_name==self.pointing_name).one()
#           # first filter above: remove degeneracy in relation
#   except sqlalchemy.orm.exc.NoResultFound:
#       pp = None
#   return pp
# PlPlugMapM.platePointing = platePointing


# Below are just old notes...

#mapper(Plate, Plate.__table__,
#      properties={'survey':relation(mapper(Survey, Survey.__table__, non_primary = True))},
#      non_primary = True
#      )

# define relationships
# --------------------
# Plate <<---> Survey
# mapper(Plate, Plate.__table__,
#   properties={'survey' : relation(Survey, backref='plates')},
#   non_primary = True)
#
# mapper(Survey, Survey.__table__, non_primary = True)


# ---------------------------------------------------------
# Test that all relationships/mappings are self-consistent.
# ---------------------------------------------------------
from sqlalchemy.orm import configure_mappers
try:
    configure_mappers()
except RuntimeError, error:
    print """
An error occurred when verifying the relationships between the database tables.
Most likely this is an error in the definition of the SQLAlchemy relationships -
see the error message below for details.
"""
    print "Error type: %s" % sys.exc_info()[0]
    print "Error value: %s" % sys.exc_info()[1]
    print "Error trace: %s" % sys.exc_info()[2]
    sys.exit(1)


# ----------------------------------------
# If no cached metadata was found, save it
# ----------------------------------------
if use_cache:
    if not cached_metadata:
        # cache the metadata for future loading
        # - MUST DELETE IF THE DATABASE SCHEMA HAS CHANGED
        try:
            if not os.path.exists(cache_path):
                os.makedirs(cache_path)
            with open(os.path.join(cache_path, metadata_pickle_filename), 'w') as cachefile:
                pickle.dump(obj=Base.metadata, file=cachefile)
        except:
            # couldn't write the file for some reason
            pass
