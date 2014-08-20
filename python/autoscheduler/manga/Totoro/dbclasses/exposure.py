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
from .. import logic
from .. import log, config
import numpy as np
from .. import utils
from astropy import time
from .. import dustMap


session = Session()


class Exposure(BaseDBClass):

    def __init__(self, inp, format='pk', autocomplete=True,
                 extendFromMaNGA=True, verbose=True, mock=False, **kwargs):

        self._valid = None
        self._ditherPosition = None
        self._sn2Array = None

        self.isMock = mock

        if not self.isMock:
            self.__DBClass__ = plateDB.Exposure
            super(Exposure, self).__init__(inp=inp, format=format,
                                           autocomplete=autocomplete)

            if verbose:
                log.debug('Loaded exposure with pk={0}'.format(self.pk))

            if extendFromMaNGA:
                self.loadFromMangaDB()

            self.ra, self.dec = self.getCoordinates()

        else:
            self.ra, self.dec = kwargs['ra'], kwargs['dec']

        self.mlhalimit = utils.mlhalimit(self.dec)
        self.site = utils.createSite(verbose=False)

    def loadFromMangaDB(self):

        with session.begin(subtransactions=True):

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

    @classmethod
    def createMockExposure(cls, startTime=None, expTime=None,
                           ditherPosition='E', ra=None, dec=None,
                           verbose=False, **kwargs):

        if ra is None or dec is None:
            raise TotoroError('ra and dec must be specified')

        newExposure = cls(None, mock=True, ra=ra, dec=dec)
        newExposure.pk = None if 'pk' not in kwargs else kwargs['pk']

        if startTime is None:
            startTime = time.Time.now().jd

        if expTime is None:
            expTime = config['exposure']['exposureTime']

        newExposure.ditherPosition = ditherPosition

        tt = time.Time(startTime, format='jd', scale='tai')
        t0 = time.Time(0, format='mjd', scale='tai')
        startTimePlateDB = (tt - t0).sec
        newExposure.start_time = startTimePlateDB

        newExposure.exposure_time = expTime

        newExposure.simulateObservedParamters()

        if verbose:
            log.debug('Created mock exposure with pk={0}'.format(
                newExposure.pk))

        return newExposure

    def simulateObservedParamters(self):

        self.manga_seeing = 1.0

        self._dust = dustMap(self.ra, self.dec)

        haRange = self.getHARange()
        ha = utils.calculateMean(haRange)
        self._airmass = utils.computeAirmass(self.dec, ha)

        sn2Red = config['simulation']['redSN2'] / self._airmass ** \
            config['simulation']['alphaRed'] / self._dust['iIncrease'][0]
        sn2Blue = config['simulation']['blueSN2'] / self._airmass ** \
            config['simulation']['alphaBlue'] / self._dust['gIncrease'][0]

        self._sn2Array = np.array([sn2Blue, sn2Blue, sn2Red, sn2Red])

        self._valid = True
        self.status = 'Good'

    def getCoordinates(self):

        if hasattr(self, 'ra') and hasattr(self, 'dec'):
            return np.array([self.ra, self.dec])

        with session.begin(subtransactions=True):
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
        ha = (lst * 15. - self.ra) % 360.

        return np.array([ha, ha + expTime / 3600. * 15]) % 360.

    def getSN2Array(self):
        """Returns an array with the SN2 of the exposure. The return
        format is [b1SN2, b2SN2, r1SN2, r2SN2]."""

        if self._sn2Array is not None:
            return self._sn2Array

        with session.begin(subtransactions=True):
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
            return logic.checkExposure(self)

    @valid.setter
    def valid(self, value):
        self._valid = value

    @property
    def ditherPosition(self):
        if self._ditherPosition is None:
            return self.manga_dither_position[0].upper()
        else:
            return self._ditherPosition

    @ditherPosition.setter
    def ditherPosition(self, value):
        self._ditherPosition = value

    @property
    def seeing(self):
        return self.manga_seeing

    def getLSTRange(self):

        ha0, ha1 = self.getHARange()

        lst0 = (ha0 + self.ra) % 360. / 15
        lst1 = (ha1 + self.ra) % 360. / 15

        return np.array([lst0, lst1])

    def getUTObserved(self, format=None):

        startTime = float(self.start_time)
        t0 = time.Time(0, format='mjd', scale='tai')
        tStart = t0 + time.TimeDelta(startTime, format='sec', scale='tai')

        lst0, lst1 = self.getLSTRange()

        ut0 = self.site.localTime(lst0, date=tStart.datetime,
                                  utc=True, returntype='datetime')
        ut1 = self.site.localTime(lst1, date=tStart.datetime,
                                  utc=True, returntype='datetime')

        if format == 'str':
            return ('{0:%H:%M}'.format(ut0), '{0:%H:%M}'.format(ut1))
        else:
            return (ut0, ut1)

        return (ut0, ut1)

    def getJDObserved(self):

        startTime = float(self.start_time)
        t0 = time.Time(0, format='mjd', scale='tai')

        tStart = t0 + time.TimeDelta(startTime, format='sec', scale='tai')
        tEnd = tStart + time.TimeDelta(
            float(self.exposure_time), format='sec', scale='tai')

        return (tStart.jd, tEnd.jd)

    def getPlatePK(self):

        with session.begin(subtransactions=True):
            platePK = session.query(plateDB.Plate.pk).join(
                plateDB.PlatePointing, plateDB.Observation,
                plateDB.Exposure).filter(
                    plateDB.Exposure.pk == self.pk).scalar()

        return int(platePK)

    def getMJD(self):

        with session.begin(subtransactions=True):
            mjd = session.query(plateDB.Observation.mjd).join(
                plateDB.Exposure).filter(
                    plateDB.Exposure.pk == self.pk).scalar()

        return int(mjd)
