#!/usr/bin/env python
# encoding: utf-8
"""
field.py

Created by José Sánchez-Gallego on 17 Feb 2014.
Licensed under a 3-clause BSD license.

Revision history:
    17 Feb 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from .. import config, readPath, Session, plateDB
from ..dbclasses import Plate, Plates
from ..exceptions import TotoroError
import os
from astropy import table


session = Session()


class Fields(Plates):

    def __init__(self, tilingCatalogue=None, rejectDrilled=True, **kwargs):

        self.tilingCatalogue = readPath(config['tilingCatalogue']) \
            if tilingCatalogue is None else readPath(tilingCatalogue)

        self._tiles = self._getTiles(**kwargs)

        if rejectDrilled:
            self._rejectDrilled(**kwargs)

        list.__init__(
            self,
            [Plate.createMockPlate(
                location_id=tile['ID'],
                ra=tile['RA'], dec=tile['DEC'])
             for tile in self._tiles])

    def _getTiles(self, **kwargs):

        if not os.path.exists(self.tilingCatalogue):
            raise TotoroError('tiling catalogue does not exist.')

        tiles = table.Table.read(self.tilingCatalogue)
        tiles = tiles[tiles['DEC'] > -5]

        return tiles

    def _rejectDrilled(self, rejectMode='locationid', radecTol=1., **kwargs):

        if rejectMode.lower() == 'locationid':
            allPlates = self.getAllMaNGAPlates(onlyLeading=True)
            locIDs = [plate.location_id+1000 for plate in allPlates]

        validIdx = [idx for idx in range(len(self._tiles))
                    if self._tiles[idx]['ID'] not in locIDs]

        self._tiles = self._tiles[validIdx]

    @staticmethod
    def getAllMaNGAPlates(onlyLeading=True):

        with session.begin():
            mangaPlates = session.query(plateDB.Plate).join(
                plateDB.PlateToSurvey).join(plateDB.Survey).filter(
                    plateDB.Survey.label == 'MaNGA')

            if onlyLeading:
                subQmanga = mangaPlates.subquery()
                mangaPlates = session.query(plateDB.Plate).outerjoin(
                    subQmanga, plateDB.Plate.pk == subQmanga.c.pk).join(
                        plateDB.SurveyMode).filter(
                            plateDB.SurveyMode.label == 'MaNGA dither')

        return mangaPlates.all()
