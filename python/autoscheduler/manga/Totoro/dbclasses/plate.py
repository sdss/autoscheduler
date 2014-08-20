#!/usr/bin/env python
# encoding: utf-8
"""
plate.py

Created by José Sánchez-Gallego on 18 Apr 2014.
Licensed under a 3-clause BSD license.

Revision history:
    18 Apr 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from .plugging import Plugging
from .baseDBClass import BaseDBClass
from .set import Set
from .. import Session, plateDB, mangaDB
from ..utils import mlhalimit, isPlateComplete
import sqlalchemy
from ..exceptions import TotoroNotImplemented, TotoroError
from .. import log, config
from ..logic import rearrangeExposures
import numpy as np
from ..utils import createSite, getIntervalIntersectionLength
from .. import dustMap
from copy import deepcopy


session = Session()


class Plates(list):

    def __init__(self, inp=None, format='pk', **kwargs):

        if inp is None:

            plates = self.getPlates(**kwargs)

            list.__init__(
                self, [Plate(plate.pk, format='pk',
                             autocomplete=True, **kwargs)
                       for plate in plates])

        else:

            raise TotoroNotImplemented('creating Plate instances from pk '
                                       'not yet implemented.')

    @classmethod
    def fromList(cls, plateList, **kwargs):

        newPlates = Plates.__new__(cls)
        list.__init__(newPlates, plateList)

        return newPlates

    @staticmethod
    def getPlates(onlyPlugged=False, onlyAtAPO=True,
                  onlyIncomplete=False, **kwargs):

        if onlyPlugged:
            with session.begin(subtransactions=True):
                activePluggings = session.query(
                    plateDB.ActivePlugging).join(plateDB.Plugging).join(
                        plateDB.Plate).join(plateDB.PlateToSurvey).join(
                            plateDB.Survey).filter(
                                plateDB.Survey.label == 'MaNGA').all()

                plates = [session.query(plateDB.Plate).get(
                          actPlug.plugging.plate_pk)
                          for actPlug in activePluggings]

        elif onlyPlugged is False and onlyAtAPO:
            with session.begin(subtransactions=True):
                plates = session.query(
                    plateDB.Plate).join(plateDB.PlateLocation).filter(
                        plateDB.PlateLocation.label == 'APO').join(
                            plateDB.PlateToSurvey).join(plateDB.Survey).filter(
                                plateDB.Survey.label == 'MaNGA').all()

        else:
            with session.begin(subtransactions=True):
                plates = session.query(plateDB.Plate).join(
                    plateDB.PlateToSurvey).join(plateDB.Survey).filter(
                        plateDB.Survey.label == 'MaNGA').all()

        if onlyIncomplete:
            incompletePlates = []
            for plate in plates:
                if not isPlateComplete(plate.pk, format='plate_pk'):
                    incompletePlates.append(plate)
            plates = incompletePlates

        return plates


class Plate(BaseDBClass):

    def __init__(self, inp, format='pk', autocomplete=True,
                 pluggings=True, sets=True, rearrangeExposures=False,
                 verbose=True, mock=False, **kwargs):

        self.pluggings = []
        self.sets = []
        self._complete = None

        self.site = createSite()

        self.isMock = mock

        if not self.isMock:

            self._rearrangeExposures = rearrangeExposures

            self.__DBClass__ = plateDB.Plate
            super(Plate, self).__init__(inp, format=format,
                                        autocomplete=autocomplete)

            self.checkPlate()

            if verbose:
                log.debug('Loaded plate with pk={0}, plateid={1}'.format(
                    self.pk, self.plate_id))

        if 'coords' in kwargs:
            self.coords = kwargs['coords']
        else:
            self.coords = self.getCoords()

        if 'dust' in kwargs:
            self.dust = kwargs['dust']
        else:
            if dustMap is None:
                self.dust = None
            else:
                self.dust = dustMap(self.coords[0], self.coords[1])

        self.mlhalimit = mlhalimit(self.coords[1])

        if pluggings and not self.isMock:
            self.loadPluggingsFromDB()

        if sets and not self.isMock:
            self.loadSetsFromDB()

    @classmethod
    def fromPlateID(cls, plateid, **kwargs):

        with session.begin(subtransactions=True):
            plate = session.query(
                plateDB.Plate).filter(plateDB.Plate.plate_id == plateid).one()

        return cls(plate.pk, **kwargs)

    @classmethod
    def createMockPlate(cls, pk=None, location_id=None,
                        ra=None, dec=None, verbose=False):

        mockPlate = cls(None, mock=True, coords=(ra, dec))

        mockPlate.isMock = True
        mockPlate.pk = pk
        mockPlate.location_id = location_id

        if verbose:
            log.debug(
                'Created mock plate with ra={0:.3f} and dec={0:.3f}'.format(
                    mockPlate.coords[0], mockPlate.coords[1]))

        return mockPlate

    def checkPlate(self):

        if not hasattr(self, 'pk') or not hasattr(self, 'plate_id'):
            raise AttributeError('Plate instance has no pk or plate_id.')

        if not self.isMaNGA:
            raise TotoroError('this is not a MaNGA plate!')

    @property
    def isMaNGA(self):

        with session.begin(subtransactions=True):
            surveyCount = session.query(plateDB.Survey).join(
                plateDB.PlateToSurvey).join(plateDB.Plate).filter(
                    plateDB.Plate.pk == self.pk,
                    plateDB.Survey.label == 'MaNGA').count()

        if surveyCount == 1:
            return True

        return False

    def getCoords(self):

        with session.begin(subtransactions=True):
            try:
                platePointing = session.query(plateDB.Pointing).join(
                    plateDB.PlatePointing).filter(
                        plateDB.PlatePointing.plate_pk == self.pk).one()
            except:
                raise sqlalchemy.orm.exc.NoResultFound(
                    'No pointing for plate with pk={0}'.format(self.pk))

            centerRA = platePointing.center_ra
            centerDec = platePointing.center_dec

            return (float(centerRA), float(centerDec))

    def loadPluggingsFromDB(self):

        self.pluggings = []

        with session.begin(subtransactions=True):
            pluggings = session.query(plateDB.Plugging).filter(
                plateDB.Plugging.plate_pk == self.pk)

        for plugging in pluggings:
            self.pluggings.append(Plugging(plugging.pk, autocomplete=True,
                                           format='pk', sets=False))

    def loadSetsFromDB(self):

        from .set import Set

        self.sets = []

        if self._rearrangeExposures:
            status = rearrangeExposures(self, force=True)

            if status is False:
                raise TotoroError('failed while reorganising exposures.')

        with session.begin(subtransactions=True):
            sets = session.query(mangaDB.Set).join(mangaDB.Exposure).join(
                plateDB.Exposure).join(plateDB.Observation).join(
                    plateDB.PlatePointing).join(plateDB.Plate).filter(
                        plateDB.Plate.pk == self.pk).all()

        for set in sets:
            self.sets.append(Set(set.pk, autocomplete=True,
                                 format='pk', exposures=True))

    @property
    def isComplete(self):
        if self._complete is not None:
            return self._complete
        else:
            return self.getPlateCompletion()[0]

    @isComplete.setter
    def isComplete(self, value):
        self._complete = value

    def copy(self):
        return deepcopy(self)

    def getPlateCompletion(self, includeIncompleteSets=False):

        totalSN = self.getCumulatedSN2(includeIncomplete=includeIncompleteSets)

        for plugging in self.pluggings:
            pluggingStatus = plugging.getPluggingStatus()
            if pluggingStatus in ['Overriden Good']:
                return (True, totalSN)
            elif pluggingStatus in ['Incomplete', 'Overriden Incomplete']:
                return (False, totalSN)

        if np.all(totalSN[0:2] >= config['SN2thresholds']['plateBlue']) and \
                np.all(totalSN[2:] >= config['SN2thresholds']['plateRed']):
            return (True, totalSN)

        return (False, totalSN)

    def getCumulatedSN2(self, includeIncomplete=False):

        validStatuses = ['Good', 'Excellent', 'Bad']
        if includeIncomplete:
            validStatuses.append('Incomplete')

        validSets = []
        for set in self.sets:
            if set.getQuality() in validStatuses:
                validSets.append(set)

        if len(validSets) == 0:
            return np.array([0.0, 0.0, 0.0, 0.0])
        else:
            return np.sum([set.getSN2Array() for set in validSets], axis=0)

    def getCartridgeNumber(self):

        with session.begin(subtransactions=True):
            cart = session.query(plateDB.Cartridge).join(
                plateDB.Plugging).join(plateDB.ActivePlugging).join(
                    plateDB.Plate).filter(
                        plateDB.Plate.pk == self.pk)

        try:
            return cart.one().number
        except:
            return 0

    def getValidSets(self, includeIncomplete=False):

        validSets = []
        for set in self.sets:
            quality = set.getQuality()
            if quality in ['Good', 'Excellent', 'Poor']:
                validSets.append(set)
            elif includeIncomplete and quality == 'Incomplete':
                validSets.append(set)

        return validSets

    def getValidExposures(self):
        """Returns all valid exposures, even if they belong to an incomplete
        or bad set."""

        validExposures = []
        for set in self.sets:
            for exp in set.exposures:
                if exp.valid is True:
                    validExposures.append(exp)

        return validExposures

    def getLSTRange(self):

        ha0 = -self.mlhalimit
        ha1 = self.mlhalimit

        lst0 = (ha0 + self.coords[0]) % 360. / 15
        lst1 = (ha1 + self.coords[0]) % 360. / 15

        return (lst0, lst1)

    def getUTVisibilityWindow(self, format='str'):

        lst0, lst1 = self.getLSTRange()

        ut0 = self.site.localTime(lst0, utc=True, returntype='datetime')
        ut1 = self.site.localTime(lst1, utc=True, returntype='datetime')

        if format == 'str':
            return ('{0:%H:%M}'.format(ut0), '{0:%H:%M}'.format(ut1))
        else:
            return (ut0, ut1)

    def isVisible(self, LST0, LST1, minLength=None):
        """Returns True if the plate is visible in a range of LST."""

        if minLength is None:
            minLength = config['exposure']['exposureTime']

        lstIntersectionLength = getIntervalIntersectionLength(
            self.getLSTRange(), (LST0, LST1), wrapAt=24.)

        secIntersectionLength = lstIntersectionLength * 3600.

        return True if secIntersectionLength >= minLength else False

    def addMockExposure(self, startTime=None, set=None,
                        expTime=None, **kwargs):
        """Creates a mock expusure in the indicated set. If set=None,
        a new set will be created."""

        ra, dec = self.coords

        if set is None:
            set = self.getIncompleteSet(startTime, expTime)

        if set is None:
            set = Set.createMockSet(ra=ra, dec=dec, **kwargs)
            self.sets.append(set)

        set.addMockExposure(startTime=startTime, expTime=expTime,
                            ra=ra, dec=dec, **kwargs)

        return None

    def getIncompleteSet(self, startTime, expTime):
        """Returns incomplete sets that are valid for an exposure starting at
        JD=startTime."""

        LST0 = self.site.localSiderialTime(startTime)
        LST1 = (LST0 + expTime / 60.) % 24.

        incompleteSets = [set for set in self.sets if not set.complete]

        if len(incompleteSets) == 0:
            return None

        for set in incompleteSets:

            lstRange = set.getLSTRange()
            intersectionLength = getIntervalIntersectionLength(
                (LST0, LST1), lstRange)

            if intersectionLength * 3600 > expTime:
                return set

        return None

    def getLastExposure(self):
        """Returns the last exposure taken."""

        exposures = []
        for set in self.sets:
            for exp in set.exposures:
                if exp.valid:
                    exposures.append(exp)

        startTime = [exp.start_time for exp in exposures]
        order = np.argsort(startTime)

        return exposures[order[-1]]

    def getPriority(self):

        with session.begin(subtransactions=True):
            platePointing = session.query(plateDB.PlatePointing).join(
                plateDB.Plate).filter(plateDB.Plate.pk == self.pk).one()

        return platePointing.priority

    @property
    def isPlugged(self):

        for plugging in self.pluggings:
            if plugging.isActive:
                return True

        return False
