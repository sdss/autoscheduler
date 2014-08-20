#!/usr/bin/env python
# encoding: utf-8
"""
plugging.py

Created by José Sánchez-Gallego on 24 Mar 2014.
Licensed under a 3-clause BSD license.

Revision history:
    24 Mar 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from .. import Session, plateDB, mangaDB
from .baseDBClass import BaseDBClass
from .set import Set
from .. import log


session = Session()


class Plugging(BaseDBClass):

    def __init__(self, inp, format='pk', autocomplete=True,
                 sets=False, **kwargs):

        self.sets = []
        self._isActive = None

        self.__DBClass__ = plateDB.Plugging
        super(Plugging, self).__init__(inp, format=format,
                                       autocomplete=autocomplete)

        self.plateid = self._getPlateID()

        log.debug('Loaded plugging with pk={0} for plateid={1}'.format(
            self.pk, self.plateid))

        if sets:
            self.loadSetsFromDB()

    def loadSetsFromDB(self):

        with session.begin(subtransactions=True):
            sets = session.query(mangaDB.Set).join(mangaDB.Exposure).join(
                plateDB.Exposure).join(plateDB.Observation).filter(
                plateDB.Observation.plugging_pk == self.pk).all()

        for set in sets:
            self.sets.append(Set(set.pk, autocomplete=True,
                                 format='pk', exposures=True))

    def _getPlateID(self):

        with session.begin(subtransactions=True):
            return session.query(plateDB.Plate).join(
                plateDB.Plugging).filter(
                plateDB.Plugging.pk == self.pk).one().plate_id

    def getPluggingStatus(self):
        """Returns the status of the plugging."""

        with session.begin(subtransactions=True):
            plStatus = session.query(plateDB.PluggingStatus).join(
                plateDB.Plugging).filter(plateDB.Plugging.pk == self.pk).one()
            return plStatus.label

    @property
    def isActive(self):
        if self._isActive is not None:
            return self._isActive

        with session.begin(subtransactions=True):
            activePluggins = zip(*session.query(
                plateDB.ActivePlugging.plugging_pk).all())[0]

        if self.pk in activePluggins:
            return True
        return False

    @isActive.setter
    def isActive(self, value):
        self._isActive = value

