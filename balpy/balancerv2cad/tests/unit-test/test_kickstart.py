"""
Showcasing two different ways to properly test your code

1. By importing the balancerv2cad package in directly.
2. By passing in a function fixture defined in conftest.py
"""
import balancerv2cad as ks



def test_pkgname_using_fixture(version_test):
    """
    testing pkgname from passing the module
    in as a fixture
    """
    assert version_test.__package__ == 'balancerv2cad'
