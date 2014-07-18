# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import warnings
warnings.filterwarnings('ignore', module='astropy.time.core')
warnings.filterwarnings('ignore', module='hooloovookit.astro.skycalc')
warnings.filterwarnings(
    'ignore', 'Module argparse was already imported')

__minimum_numpy_version__ = '1.5.0'
__minimum_astropy_version__ = '0.3.0'
__minimum_sqlalchemy_version__ = '0.9.0b1'

try:
    from .version import version as __version__
except:
    __version__ = ''

from .readPath import readPath
__DEFAULT_CONFIG_FILE__ = readPath('+defaults.yaml')
__TOTORO_CONFIG_PATH__ = readPath('~/.totoro/totoro.yaml')

# Reads the configuration file
from .core.configuration import TotoroConfig
config = TotoroConfig(__DEFAULT_CONFIG_FILE__)

if os.path.exists(__TOTORO_CONFIG_PATH__):
    # If a custom configuration file exists, updates default values.
    config.update(TotoroConfig(__TOTORO_CONFIG_PATH__))

# Creates the custom logging system
from .core.logger import initLog
log = initLog()
log.info('Logging starts now.')

from sdss.manga import DustMap
dustMap = DustMap()

log.info('Creating connection with DB.')
from .APOplateDB import Session, Base, db, engine
from .APOplateDB import plateDB, mangaDB
from .scheduler import Planner, Nightly
