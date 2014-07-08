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
from ..exceptions import TotoroError
from .. import plateDB, mangaDB, Session
from ..utils import mlhalimit, checkExposure
from .. import log
import numpy as np
from ..utils import createSite
from astropy import time

session = Session()


class Exposure(BaseDBClass):

    def __init__(self, inp, format='pk', autocomplete=True,
                 extendFromMaNGA=True, verbose=True, **kwargs):

        self._valid = None

        self.__DBClass__ = plateDB.Exposure
        super(Exposure, self).__init__(inp=inp, format=format,
                                       autocomplete=autocomplete)

        if verbose:
            log.debug('Loaded exposure with pk={0}'.format(self.pk))

        if extendFromMaNGA:
            self.loadFromMangaDB()

        self.ra, self.dec = self.getCoordinates()
        self.mlhalimit = mlhalimit(self.dec)
        self.site = createSite(verbose=False)

    def loadFromMangaDB(self):

        with session.begin():

            try:
                mangaExposure = session.query(mangaDB.Exposure).filter(
                    mangaDB.Exposure.platedb_exposure_pk == self.pk).one()
            except:
                raise TotoroError(
                    'exposure pk={0} has no mangaDB counterpart'.format(
                        self.pk))

            try:
                mangaSN = session.query(mangaDB.SN2Values).filter(
                    mangaDB.SN2Values.exposure_pk == mangaExposure.pk).one()
            except:
                raise TotoroError(
                    'mangaDB.Exposure pk={0} '.format(mangaExposure.pk) +
                    'has no mangaDB.SN2Values counterpart')

        for column in mangaExposure.__table__.columns.keys():
            setattr(self, 'manga_' + column, getattr(mangaExposure, column))

        for column in mangaSN.__table__.columns.keys():
            setattr(self, 'manga_' + column, getattr(mangaSN, column))

        self.status = mangaExposure.status.label
        self.expTime = mangaExposure.platedbExposure.exposure_time

    def getCoordinates(self):

        with session.begin():
            pointing = session.query(plateDB.Pointing).join(
                plateDB.PlatePointing).join(plateDB.Observation).join(
                    plateDB.Exposure).join(mangaDB.Exposure).filter(
                        mangaDB.Exposure.pk == self.manga_pk).one()

        return np.array([pointing.center_ra, pointing.center_dec], np.float)

    def getHARange(self):
        """Returns the HA range in which the exposure was taken."""

        startTime = float(self.start_time)
        expTime = float(self.exposure_time)

        t0 = time.Time(0, format='mjd', scale='tai')
        tStart = t0 + time.TimeDelta(startTime, format='sec', scale='tai')

        lst = self.site.localSiderialTime(tStart.jd)
        ha = (lst * 15. - self.ra)
        if ha > 180:
            ha -= 360.

        return np.array([ha, ha + expTime / 3600. * 15])

    def getSN2Array(self):
        """Returns an array with the SN2 of the exposure. The return
        format is [b1SN2, b2SN2, r1SN2, r2SN2]."""

        with session.begin():
            SN2Values = session.query(mangaDB.SN2Values).join(
                mangaDB.Exposure).filter(
                    mangaDB.Exposure.pk == self.manga_pk).one()

        return np.array([SN2Values.b1_sn2, SN2Values.b2_sn2,
                         SN2Values.r1_sn2, SN2Values.r2_sn2])

    @property
    def valid(self):
        if self._valid is not None:
            return self._valid
        else:
            return checkExposure(self)

    @valid.setter
    def valid(self, value):
        self._valid = value

    @property
    def ditherPosition(self):
        return self.manga_dither_position[0].upper()

    @property
    def seeing(self):
        return self.manga_seeing

    def getUTObserved(self):

        startTime = float(self.start_time)
        t0 = time.Time(0, format='mjd', scale='tai')
        tStart = t0 + time.TimeDelta(startTime, format='sec', scale='tai')

        ha0, ha1 = self.getHARange()

        lst0 = (ha0 + self.ra) % 360. / 15
        lst1 = (ha1 + self.ra) % 360. / 15

        ut0 = '{0:%H:%M}'.format(self.site.localTime(
            lst0, date=tStart.datetime, utc=True, returntype='datetime'))
        ut1 = '{0:%H:%M}'.format(self.site.localTime(
            lst1, date=tStart.datetime, utc=True, returntype='datetime'))

        return (ut0, ut1)

    def getPlatePK(self):

        with session.begin():
            platePK = session.query(plateDB.Plate.pk).join(
                plateDB.PlatePointing, plateDB.Observation,
                plateDB.Exposure).filter(
                    plateDB.Exposure.pk == self.pk).scalar()

        return platePK

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
