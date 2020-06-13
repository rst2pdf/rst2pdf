# See LICENSE.txt for licensing terms

# TODO(stephenfin): Switch to 'importlib.metadata' once we drop support for
# Python < 3.8
import importlib_metadata

try:
    version = importlib_metadata.version('rst2pdf')
except importlib_metadata.PackageNotFoundError:
    version = None
