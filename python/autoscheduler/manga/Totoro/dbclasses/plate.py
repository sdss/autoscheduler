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
from .. import Session, plateDB, mangaDB
from ..utils import mlhalimit, isPlateComplete
import sqlalchemy
from ..exceptions import TotoroNotImplemented, TotoroError
from .. import log, config
from ..utils import rearrageExposures
import numpy as np
from ..utils import createSite
from .. import dustMap

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

    @staticmethod
    def getPlates(onlyPlugged=False, onlyAtAPO=False,
                  onlyIncomplete=False, **kwargs):

        if onlyPlugged:
            with session.begin():
                activePluggings = session.query(
                    plateDB.ActivePlugging).join(plateDB.Plugging).join(
                        plateDB.Plate).join(plateDB.PlateToSurvey).join(
                            plateDB.Survey).filter(
                                plateDB.Survey.label == 'MaNGA').all()

                plates = [session.query(plateDB.Plate).get(
                          actPlug.plugging.plate_pk)
                          for actPlug in activePluggings]

        elif onlyPlugged is False and onlyAtAPO:
            with session.begin():
                plates = session.query(
                    plateDB.Plate).join(plateDB.PlateLocation).filter(
                        plateDB.PlateLocation.label == 'APO').join(
                            plateDB.PlateToSurvey).join(plateDB.Survey).filter(
                                plateDB.Survey.label == 'MaNGA').all()

        else:
            with session.begin():
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
                 pluggings=True, sets=True, rearrageExposures=False,
                 verbose=True, **kwargs):

        self.pluggings = None
        self.sets = None
        self._complete = None

        self._rearrageExposures = rearrageExposures

        self.site = createSite()

        self.__DBClass__ = plateDB.Plate
        super(Plate, self).__init__(inp, format=format,
                                    autocomplete=autocomplete)

        self.checkPlate()

        if 'coords' in kwargs:
            self.coords = kwargs['coords']
        else:
            self.coords = self.getCoords()

        if verbose:
            log.debug('Loaded plate with pk={0}, plateid={1}'.format(
                self.pk, self.plate_id))

        if 'dust' in kwargs:
            self.dust = kwargs['dust']
        else:
            if dustMap is None:
                self.dust = None
            else:
                self.dust = dustMap(self.coords[0], self.coords[1])

        self.mlhalimit = mlhalimit(self.coords[1])

        if pluggings:
            self.loadPluggingsFromDB()

        if sets:
            self.loadSetsFromDB()

    @classmethod
    def fromPlateID(cls, plateid, **kwargs):

        with session.begin():
            plate = session.query(
                plateDB.Plate).filter(plateDB.Plate.plate_id == plateid).one()

        return cls(plate.pk, **kwargs)

    def checkPlate(self):

        if not hasattr(self, 'pk') or not hasattr(self, 'plate_id'):
            raise AttributeError('Plate instance has no pk or plate_id.')

        if not self.isMaNGA:
            raise TotoroError('this is not a MaNGA plate!')

    @property
    def isMaNGA(self):

        with session.begin():
            surveyCount = session.query(plateDB.Survey).join(
                plateDB.PlateToSurvey).join(plateDB.Plate).filter(
                    plateDB.Plate.pk == self.pk,
                    plateDB.Survey.label == 'MaNGA').count()

        if surveyCount == 1:
            return True

        return False

    def getCoords(self):

        with session.begin():
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

        with session.begin():
            pluggings = session.query(plateDB.Plugging).filter(
                plateDB.Plugging.plate_pk == self.pk)

        for plugging in pluggings:
            self.pluggings.append(Plugging(plugging.pk, autocomplete=True,
                                           format='pk', sets=False))

    def loadSetsFromDB(self):

        from .set import Set

        self.sets = []

        if self._rearrageExposures:
            status = rearrageExposures(self, force=True)

            if status is False:
                raise TotoroError('failed while reorganising exposures.')

        with session.begin():
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

    def getPlateCompletion(self):

        totalSN = self.getCumulatedSN2()

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

        validStatuses = ['Good', 'Excellent']
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

        with session.begin():
            cart = session.query(plateDB.Cartridge).join(
                plateDB.Plugging).join(plateDB.ActivePlugging).join(
                    plateDB.Plate).filter(
                        plateDB.Plate.pk == self.pk).one()

        return cart.number

    def getValidSets(self, includeIncomplete=False):

        validSets = []
        for set in self.sets:
            quality = set.getQuality()
            if quality in ['Good', 'Excellent', 'Poor']:
                validSets.append(set)
            elif includeIncomplete and quality == 'Incomplete':
                validSets.append(set)

        return validSets

    def getValidExposures(self, includeIncompleteSets=False):

        validSets = self.getValidSets(includeIncomplete=includeIncompleteSets)

        validExposures = []
        for set in validSets:
            for exp in set.exposures:
                if exp.valid is True:
                    validExposures.append(exp)

        return validExposures

    def getUTVisibilityWindow(self, format='str'):

        ha0 = -self.mlhalimit
        ha1 = self.mlhalimit

        lst0 = (ha0 + self.coords[0]) % 360. / 15
        lst1 = (ha1 + self.coords[0]) % 360. / 15

        ut0 = self.site.localTime(lst0, utc=True, returntype='datetime')
        ut1 = self.site.localTime(lst1, utc=True, returntype='datetime')

        if format == 'str':
            return ('{0:%H:%M}'.format(ut0), '{0:%H:%M}'.format(ut1))
        else:
            return (ut0, ut1)
