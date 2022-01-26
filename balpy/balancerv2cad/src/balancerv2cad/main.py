"""
Example Driver code
"""
# standard lib

# third party
from dotenv import dotenv_values

# package
import balancerv2cad as ks
from balancerv2cad.logger import pkg_logger as pl

logger = pl.PackageLogger().get_logger()


def run() -> None:
    """
    Example function to execute through poetry scripts
    """
    config: dict = dotenv_values(".env")

    try:
        logger.info("CAPTAIN_ONE: %s :: package name: %s@%s",
                    config['CAPTAIN_ONE'], ks.__package__, ks.__version__)

        logger.info("CAPTAIN_ONE: %s :: package name: %s@%s",
                    config['CAPTAIN_TWO'], ks.__package__, ks.__version__)
    except KeyError as error:
        logger.error(
            'Could not find %s in .env file. Please consult the README', error)
        logger.info('Testing for %s@%s', ks.__package__, ks.__version__)
        logger.debug('Testing for %s@%s', ks.__package__, ks.__version__)
        logger.warning('Testing for %s@%s', ks.__package__, ks.__version__)
        logger.error('Testing for %s@%s', ks.__package__, ks.__version__)
