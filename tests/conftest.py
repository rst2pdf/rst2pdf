# A pytest plugin for rst2pdf functional tests.
# This is a "local per-directory" plugin as described here: https://docs.pytest.org/en/latest/writing_plugins.html#conftest-py-local-per-directory-plugins
# Inspired by http://pytest.org/en/latest/example/nonpython.html
# This file contains hooks (callbacks) that are called during pytest's execution. As pytest crawls the tests/ directory,
# it calls theses functions.
#
# Test files are of the form "test[...].txt", therefore they are not "python" tests or unit tests, but functional tests.
#
#
#
# Notes
#  * We used to use nose to invoke the tests. There may be some "noseisms", still to be removed. TODO
#  * Sphinx tests are not executed.  Perhaps they should be moved to a separate test directory and dealt with appropriately. TODO
#  * Since these are functional tests, they reside in a directory outside the rst2pdf code (https://docs.pytest.org/en/latest/goodpractices.html#choosing-a-test-layout-import-rules)


import sys
import os
import pytest
import logging as log
from autotest import run_single, dirname, checkmd5


# hook (callback) that filters the incoming files as they are collected.
def pytest_collect_file(parent, path):
    if path.ext == ".txt" and path.basename.startswith("test"):
        return FunctionalTestFile(path, parent)


class FunctionalTestFile(pytest.File):
    def collect(self):
        # self.name = relative path to txt file
        # self.fspath = absolute path to txt file

        yield FunctionalTestItem(name=self.name, parent=self, testFile=self.fspath)


class FunctionalTestItem(pytest.Item):
    def __init__(self, name, parent, testFile):
        log.debug(f"FunctionalTestItem {name} - {testFile}")
        super().__init__(
            name=name, parent=parent, nodeid=name
        )  # nodeid is what appears on the line for each test.  We only have one test per file, so make it the file name
        self.testFile = testFile

    def runtest(self):
        # log.debug(self.testFile.open().readlines())
        log.debug("runtest")
        key, errcode = run_single(self.testFile)
        log.debug("%s, %d", key, errcode)
        if errcode != 0:
            raise FunctionalTestException(key, errcode)

    def repr_failure(self, excinfo):
        """ called when self.runtest() raises an exception. """
        if isinstance(excinfo.value, FunctionalTestException):
            return f"Functional Test failed {excinfo.value.args}.  See below, or see output log file for test {self.name}. "
        else:
            log.error(f"unknown failure {excinfo}")
            print("Unknown failure:", str(excinfo))
            print(excinfo.getrepr())

    def reportinfo(self):
        return self.fspath, 0, "usecase: {}".format(self.name)


class FunctionalTestException(Exception):
    """ custom exception for error reporting. """
