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
from .. import Session, plateDB
from ..utils import mlhalimit
from astropysics import coords
import sqlalchemy

session = Session()


class Plate(BaseDBClass):

    pluggings = []
    _complete = None

    def __init__(self, inp, format='pk', autocomplete=True,
                 pluggings=True, **kwargs):

        self.__DBClass__ = plateDB.Plate
        super(Plate, self).__init__(inp, format=format,
                                    autocomplete=autocomplete)

        self.checkPlate()

        if 'coords' in kwargs:
            self.coords = kwargs['coords']
        else:
            self.coords = self.getCoords()

        if pluggings:
            self.loadPluggingsFromDB()

        if 'dust' in kwargs:
            self.dust = kwargs['dust']
        else:
            from .. import dustMap
            self.dust = dustMap

        self.mlhalimit = mlhalimit(self.coords.dec.degrees)

    def checkPlate(self):
        if not hasattr(self, 'pk') or not hasattr(self, 'plate_id'):
            raise AttributeError('Plate instance has no pk or plate_id.')

    def getCoords(self):

        with session.begin():
            try:
                plate = session.query(plateDB.plate).get(self.pk)
            except:
                raise sqlalchemy.orm.exc.NoResultFound(
                    'No plate with pk={0}'.format(self.pk))

            centerRA = plateDB.ra(plate)
            centerDec = plateDB.dec(plate)

            return coords.ICRSCoordinates(centerRA, centerDec)

    def loadPluggingsFromDB(self):

        with session.begin():
            pluggings = session.query(plateDB.Plugging).filter(
                plateDB.Pluggings.plate_pk == self.pk)

        for plugging in pluggings:
            self.pluggings.append(Plugging(plugging.pk, autocomplete=True,
                                           format='pk', sets=True))

    @property
    def complete(self):
        if self._complete is not None:
            return self._complete
        else:
            if len(self.pluggings) == 0:
                return False
            else:
                pluggingStatuses = [plugging.plugging_status_pk
                                    for plugging in self.pluggings]

                for pluggingStatus in pluggingStatuses:
                    if pluggingStatus in [1, 3]:
                        return True

                return self.getPlateCompletion()

    @complete.setter
    def complete(self, value):
        self._complete = value

    def getPlateCompletion(self):

        validSets = self.getValidSets()


        return False

    def getValidSets(self):
        validSets = []
        for plugging in self.pluggings:
            validSets += plugging.getValidSets()
        return validSets

