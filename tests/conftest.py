import sys
import pytest
import logging as log
from autotest import run_single, dirname, checkmd5


# hook (callback) that returns a test file of the form {...}/rst2pdf/tests/input/test{n}.txt
def pytest_collect_file(parent, path):
    if path.ext == ".txt" and path.basename.startswith("test"):
        return FunctionalTestFile(path, parent)


class FunctionalTestFile(pytest.File):
    def collect(self):
        log.debug("FunctionalTestFile: %s", self.fspath)
        yield FunctionalTestItem(self.name, self, self.fspath)


class FunctionalTestItem(pytest.Item):
    def __init__(self, name, parent, testFile):
        super().__init__(name, parent)
        self.testFile = testFile
        log.debug("FunctionalTestItem %s", self.testFile)

    def runtest(self):
        # log.debug(self.testFile.open().readlines())
        key, errcode = run_single(self.testFile)
        log.debug("%s, %d", key, errcode)
        if key in ["incomplete"]:
            raise FunctionalTestException(key, errcode)
        assert key == "good", "%s is not good: %s" % (self.name, key)

    def repr_failure(self, excinfo):
        """ called when self.runtest() raises an exception. """
        if isinstance(excinfo.value, FunctionalTestException):
            return "\n".join(
                [
                    "usecase execution failed",
                    "   spec failed: {1!r}: {2!r}".format(*excinfo.value.args),
                    "   no further details known at this point.",
                ]
            )

    def reportinfo(self):
        return self.fspath, 0, "usecase: {}".format(self.name)


class FunctionalTestException(Exception):
    """ custom exception for error reporting. """
