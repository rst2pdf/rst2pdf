import pytest


# callback that returns a test file of the form {...}/rst2pdf/tests/input/test{n}.txt
def pytest_collect_file(parent, path):
    print(path.ext, path.basename)
    if path.ext == ".txt" and path.basename.startswith("test"):
        return FunctionalTestFile(path, parent)


class FunctionalTestFile(pytest.File):
    def collect(self):
        print("collect", self.fspath, type(self.fspath))

        yield FunctionalTestItem(self.name, self, self.fspath)


class FunctionalTestItem(pytest.Item):
    def __init__(self, name, parent, spec):
        super().__init__(name, parent)
        self.txtFile = spec.dirpath()
        print("TestItem", self.txtFile)

    def runtest(self):
        txtFile = open(self.spec)
        print(txtFile.readlines())
        # print(self.spec.open)
        for name, value in sorted(self.spec.items()):
            # some custom test execution (dumb example follows)
            if name != value:
                raise FunctionalTestException(self, name, value)

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
