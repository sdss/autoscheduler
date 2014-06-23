#!/usr/bin/env python
# encoding: utf-8
"""
baseDBClass.py

Created by José Sánchez-Gallego on 22 Apr 2014.
Licensed under a 3-clause BSD license.

Revision history:
    22 Apr 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function

from __future__ import division
from __future__ import print_function
from ..exceptions import TotoroWarning, TotoroError
from warnings import warn
from .. import Session

session = Session()


class BaseDBClass(object):

    __DBClass__ = None

    def __init__(self, inp, format='pk', autocomplete=True, **kwargs):

        if not isinstance(inp, (int, dict)):
            raise TypeError('inp must be and integer or a dictionary.')

        if format != 'dict':
            if autocomplete is False:
                warn('inp has format={0} '.format(format) +
                     'but autocomplete=False. Setting autocomplete=True',
                     TotoroWarning)
                autocomplete = True
            if isinstance(inp, dict):
                self.loadFromDB(inp[format], format=format)
                self.loadFromDict(inp)
            else:
                self.loadFromDB(inp, format=format)

        else:
            if not isinstance(inp, dict):
                raise TotoroError('format=dict but input is not a dictionary.')
            if autocomplete:
                self.loadFromDB(inp['pk'], format='pk')
            self.loadFromDict(inp)

    def loadFromDict(self, inp):
        if not isinstance(inp, dict):
            raise TotoroError('input must be a dictionary.')

        for key, value in inp.items():
            setattr(self, key, value)

    def loadFromDB(self, inp, format='pk'):

        if self.__DBClass__ is None:
            raise TotoroError('BaseDBClass.__DBClass__ is not set. '
                              'You need to set it up before using loadFromDB.')

        with session.begin():

            if format == 'pk':
                qResult = session.query(self.__DBClass__).get(inp)
            else:
                qResult = session.query(self.__DBClass__).filter(
                    getattr(self.__DBClass__, format) == inp)

                if qResult.count() == 0:
                    raise TotoroError('no results found for '
                                      '{0}={1}.'.format(format, inp))

                elif qResult.count() > 1:
                    raise TotoroError('more than one result found for ' +
                                      '{0}={1}. '.format(format, inp) +
                                      'Your DB may need debugging.')

        for column in qResult.__table__.columns.keys():
            setattr(self, column, getattr(qResult, column))
