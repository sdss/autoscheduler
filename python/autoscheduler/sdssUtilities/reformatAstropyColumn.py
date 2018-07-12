#!/usr/bin/env python
# encoding: utf-8
"""
reformatAstropyColumn.py

Created by José Sánchez-Gallego on 10 Feb 2015.
Licensed under a 3-clause BSD license.

Revision history:
    10 Feb 2015 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from astropy import table
import numpy as np


def reformatAstropyColumn(inputTable, columnName, newFormat):
    """Changes the format of a column for an `astropy.table.Column`.

    Returns a new table in which the desired column has been cast to a
    new dtype format.

    Parameters
    ----------
    inputTable : `astropy.table.Table`
        The input table whose column format wants to be changed.

    columnName : string or list of strings
        The name or names (as a list) of the columns to modify.

    newFormat : dtype or list of dtypes
        The new dtype format of the column. If a list, it must have the same
        size as `columnName`.

    Returns
    -------
    outputTable : `astropy.table.Table`
        A new `astropy.table.Table`, identical to `inputTable` but with the
        desired column(s) cast to a new format.

    Example
    -------
      >> table1 = table.Table([[1,2,3],[4,5,6]], names=['columnA', 'columnB'])
      >> table2 = reformatAstropyColumn(table1, 'columnB', 'S5')

    """

    if isinstance(columnName, (list, tuple, np.ndarray)):
        assert isinstance(newFormat, (list, tuple, np.ndarray))
        assert len(columnName) == len(newFormat)
    else:
        columnName = [columnName]
        newFormat = [newFormat]

    dtypes = [inputTable[col].dtype for col in inputTable.colnames]
    colIndices = [inputTable.colnames.index(colName) for colName in columnName]

    newDtype = dtypes
    for ii, colIndex in enumerate(colIndices):
        newDtype[colIndex] = newFormat[ii]

    return table.Table(inputTable, dtype=newDtype)
