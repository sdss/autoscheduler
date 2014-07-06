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

session = Session()


class Plugging(BaseDBClass):

    sets = []
    # _complete = False

    def __init__(self, inp, format='pk', autocomplete=True,
                 sets=True, **kwargs):

        self.__DBClass__ = plateDB.Plugging
        super(BaseDBClass, self).__init__(inp, format=format,
                                          autocomplete=autocomplete)

        if sets:
            self.loadSetsFromDB()

    def loadSetsFromDB(self):

        with session.begin():
            sets = session.query(mangaDB.Set).join(mangaDB.Exposure).join(
                plateDB.Exposure).join(plateDB.Observation).filter(
                plateDB.Observation.plugging_pk == self.pk)

        for set in sets:
            self.sets.append(Set(set.pk, autocomplete=True,
                                 format='pk', exposures=True))

    def getValidSets(self):
        return [ss for ss in self.sets if ss.valid]

    # @property
    # def complete(self):
    #     if self._complete is not None:
    #         return self._complete

    #     goodSets = [ss for ss in self
    #                 if ss.quality in ['good', 'excellent']]

    #     SN_blue = np.sum([ss.SN_blue for ss in goodSets], axis=0)
    #     SN_red = np.sum([ss.SN_red for ss in goodSets], axis=0)

    #     if all(SN_red >= R_SN2) and all(SN_blue >= B_SN2):
    #         return True
    #     else:
    #         return False

    # @complete.setter
    # def complete(self, value):
    #     assert isinstance(value, bool) or value is None
    #     self._complete = value

    # def hasIncompleteSet(self):
    #     if any([ss.missingDither for ss in self]):
    #         return True
    #     return False

    # def getIncompleteSets(self):
    #     return [ss for ss in self if ss.missingDither]

    # def getHAlimit(self):
    #     if not self.hasIncompleteSet():
    #         return None
    #     else:
    #         return [ss.HAlimits for ss in self if ss.complete is False]

    # @property
    # def SN_Red(self):
    #     snRed = np.array([0., 0.])
    #     for ss in self:
    #         if ss.quality == 'bad':
    #             continue
    #         for ee in ss:
    #             if ee.valid is True:
    #                 snRed += ee.SN_red
    #     return snRed

    # @property
    # def SN_Blue(self):
    #     snBlue = np.array([0., 0.])
    #     for ss in self:
    #         if ss.quality == 'bad':
    #             continue
    #         for ee in ss:
    #             if ee.valid is True:
    #                 snBlue += ee.SN_blue
    #     return snBlue