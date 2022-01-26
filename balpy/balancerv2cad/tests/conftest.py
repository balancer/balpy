"""
Define fixtures here.
Fixtures are 'setup' and 'tear down' code
for our actual function tests and unit module tests.
Any fixture defined in this module can in turn be shared
with any other test as long as it is a sub-directory of the
tests folder.

Never include this module in any other modules. This module is
technically a 'plugin', pytest recognizes it as such and uses it
correctly
"""
# pylint: disable=W0621, E1101, C0103, W0612

# standard lib
import sys

# third party
import pytest

# balancerv2cad package
import balancerv2cad

# noinspection PyCallByClass


@pytest.fixture()
def version_test() -> None:
    """
    test version
    """
    # Setup code
    sys.stdout.write('\nRunning setup code for balancerv2cad module\n')

    yield balancerv2cad

    # tear down code
    sys.stdout.write('Running Teardown code for balancerv2cad module\n')
