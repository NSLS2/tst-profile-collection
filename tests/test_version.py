from importlib.metadata import version

import tst_lab_tools
from tst_lab_tools._version import __version__


def test_package_imports():
    assert tst_lab_tools.__name__ == "tst_lab_tools"


def test_version_matches_installed_metadata():
    assert __version__ == version("tst-lab-tools")
