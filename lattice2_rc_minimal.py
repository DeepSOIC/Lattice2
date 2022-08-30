__doc__ = 'minimal resource pack for loading at freecad startup'

import PySide.QtCore as qtc
import os


ret = \
qtc.QResource.registerResource(os.path.dirname(__file__) + "/PyResources/wb-icon.rcc".replace('/', os.path.sep))

if not ret:
    raise RuntimeError('Loading Lattice2/PyResources/wb-icon.rcc returned False, not loaded?')

