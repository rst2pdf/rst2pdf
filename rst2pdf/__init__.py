# See LICENSE.txt for licensing terms

import importlib.metadata

try:
    version = importlib.metadata.version('rst2pdf')
except importlib.metadata.PackageNotFoundError:
    version = None
