# SPDX-License-Identifier: MIT

from docutils import nodes
from docutils.parsers.rst import roles
import importlib_metadata
import packaging.version


def _get_version(package):
    """Get version from the usual methods."""
    # TODO(stephenfin): Switch to 'importlib.metadata' once we drop support for
    # Python < 3.8
    try:
        parsed_version = packaging.version.parse(importlib_metadata.version(package))
    except importlib_metadata.PackageNotFoundError:
        return 'UNKNOWN', 'UNKNOWN'

    version = '.'.join(str(r) for r in parsed_version.release)

    if parsed_version.pre:
        revision = parsed_version.pre
    elif parsed_version.dev:
        revision = f'dev{parsed_version.dev}'
    elif parsed_version.is_postrelease:
        revision = f'post{parsed_version.post}'
    else:
        revision = 'final'

    return version, revision


def version_fn(name, rawtext, text, lineno, inliner, options=None, content=None):
    version, _ = _get_version(text)
    return [nodes.Text(version)], []


def revision_fn(name, rawtext, text, lineno, inliner, options=None, content=None):
    _, revision = _get_version(text)
    return [nodes.Text(revision)], []


roles.register_canonical_role('package-version', version_fn)
roles.register_canonical_role('package-revision', revision_fn)
