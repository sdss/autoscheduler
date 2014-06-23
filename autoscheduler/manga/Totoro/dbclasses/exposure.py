#!/usr/bin/env python
# encoding: utf-8
"""
exposure.py

Created by José Sánchez-Gallego on 13 Mar 2014.
Licensed under a 3-clause BSD license.

Revision history:
    13 Mar 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from .baseDBClass import BaseDBClass
from .. import plateDB, mangaDB, Session

session = Session()


class Exposure(BaseDBClass):

    def __init__(self, inp, format='pk', autocomplete=True,
                 extendFromMaNGA=True, **kwargs):

        self.__DBClass__ = plateDB.Exposure
        super(BaseDBClass, self).__init__(inp=inp, format=format,
                                          autocomplete=autocomplete)

        if extendFromMaNGA:
            self.loadFromMangaDB()

    def loadFromMangaDB(self):
        oldDBClass = self.__DBClass__
        self.__DBClass__ = mangaDB.Exposure
        self.loadFromDB(self.pk, format='pk')
        self.__DBClass__ = oldDBClass

    # def __init__(self, startTime=None, ID=None, expTime=EXPTIME(),
    #              ditherPos='C', obsType='sci', HAstart=0.0,
    #              SN_blue=(0.0, 0.0), SN_red=(0.0, 0.0), Set=None,
    #              avgSeeing=AVG_SEEING(), valid=None, **kwargs):

    #     if startTime is None:
    #         raise ValueError('startTime must be specified.')
    #     if not isinstance(startTime, time.Time):
    #         raise ValueError('startTime must be an instance of '
    #                          'astropy.time.Time.')
    #     self.startTime = startTime

    #     if not isinstance(expTime, Real):
    #         raise ValueError('expTime must be a number in minutes.')
    #     self.expTime = expTime

    #     self.ditherPos = ditherPos.upper()
    #     if self.ditherPos not in DITHER_POSITIONS():
    #         raise ValueError(
    #             'invalid dither position {0}.'.format(self.ditherPos))

    #     self.obsType = obsType.lower()
    #     if self.obsType not in EXPTYPES():
    #         raise ValueError('invalid obsType {0}.'.format(self.obsType))

    #     self.set = Set
    #     self.ID = ID

    #     if isinstance(HAstart, coo.Longitude):
    #         self.HAstart = HAstart
    #     elif isinstance(HAstart, Real):
    #         self.HAstart = coo.Longitude(HAstart, unit=uu.hour)
    #     else:
    #         raise ValueError('HAstart must be an '
    #                          'astropy.coordinates.Longitude '
    #                          'object or a number.')

    #     self.SN_red = np.array(SN_red)
    #     self.SN_blue = np.array(SN_blue)

    #     if not isinstance(avgSeeing, Real):
    #         raise ValueError('avgSeeing must be a number in minutes.')
    #     self.avgSeeing = avgSeeing

    #     self._complete = None

    # @property
    # def HAend(self):
    #     return coo.Longitude(
    #         self.HAstart.hour + self.expTime / 60, unit=uu.hour,
    #         wrap_angle='180d')

    # @property
    # def valid(self):

    #     if self._complete is not None and isinstance(self._complete, bool):
    #         return self._complete
    #     else:
    #         return self._checkValidity()

    # @valid.setter
    # def valid(self, value):
    #     self._complete = value

    # def _checkValidity(self):
    #     if self.expTime < EXPTIME():
    #         return False
    #     if any(self.SN_blue < B_SN2_EXPOSURE()) or \
    #             any(self.SN_red < R_SN2_EXPOSURE()):
    #         return False
    #     if self.avgSeeing > MIN_SEEING_EXPOSURE():
    #         return False
    #     return True
