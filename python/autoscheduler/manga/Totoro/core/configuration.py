#!/usr/bin/env python
# encoding: utf-8
"""
configuration.py

Created by José Sánchez-Gallego on 10 Dec 2013.
Copyright (c) 2013. All rights reserved.
Licensed under a 3-clause BSD license.

Includes classes and functions to read and write the configuration
file for Totoro. Uses a simplified version of the astropy configuration
system.

"""

import yaml
import os
from .. import __TOTORO_CONFIG_PATH__, __DEFAULT_CONFIG_FILE__
from ..exceptions import TotoroError


class TotoroConfig(dict):

    def __init__(self, configurationFile):

        if not os.path.exists(configurationFile):
            raise TotoroError('configuration file', configurationFile,
                              'not found.')

        yamlData = yaml.load(open(configurationFile))
        if yamlData is None:
            yamlData = {}

        dict.__init__(self, yamlData)

    def save(self, path=__TOTORO_CONFIG_PATH__):
        outUnit = open(path, 'w')
        yaml.dump(dict(self), outUnit, default_flow_style=False)
        outUnit.close()

    def createTemplate(self, path=__TOTORO_CONFIG_PATH__):

        defaultConfig = TotoroConfig(__DEFAULT_CONFIG_FILE__)
        defaultConfig.save()
