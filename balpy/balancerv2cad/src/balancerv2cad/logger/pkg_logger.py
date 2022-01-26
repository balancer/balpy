"""
Customized system wide logger
"""
# pylint: disable=R0903

# standard lib
import logging
import sys
from logging.config import dictConfig
from pathlib import PosixPath
from typing import Literal

# 3rd party
from colorama import Back, Fore, init

# balancerv2cader package
from balancerv2cad import LOGGING_CONFIG, DEFAULT_LOGGER_NAME, BASE_DIR

init(autoreset=True)


class PackageLogger:
    """
    Logging class
    """
    def __init__(self) -> None:
        # defaults to project root directory, change this
        # and __init__.py if you want the log file to go elsewhere
        self._log_dump: PosixPath = BASE_DIR

        # blast off
        self.__load_configuration()

    def __load_configuration(self) -> None:
        """
        Load the config dictionary
        :meta private:
        :param: self
        :return none
        """
        # if dump site doesn't exist, create it,
        # and all parent folders leading up to it
        if not self._log_dump.is_dir():
            self._log_dump.mkdir(parents=True)

        try:
            # if syntax is wrong, logging module will raise ValueError,
            # catch, and exit execution
            dictConfig(LOGGING_CONFIG)
        except ValueError as error:
            print(
                f'{Fore.RED}Loading default logging config failed, syntax error\n\n{error}'
            )
            sys.exit(1)
        except KeyError as error:
            print(
                f'{Fore.RED}Loading logging config failed, syntax error\n\n{error}'
            )
            sys.exit(1)

    @staticmethod
    def get_logger(
            name: Literal['production'] = DEFAULT_LOGGER_NAME
    ) -> logging.Logger:
        """
        Return a logger by name.
        Only logger names that are defined in the config
        file will be used
        :param: name that represents a predefined logger, defaults to dev
        :return: an instance of Logger configured by custom params
        """
        # first test to see if the name is a valid defined logger name
        valid: bool = False
        if LOGGING_CONFIG['loggers']:
            for logger_name in LOGGING_CONFIG['loggers']:
                if logger_name == name:
                    valid = True

        if not valid:
            # name passed is not a valid listed logger,
            # return dev as default logger
            print(
                f'\n{Back.BLACK}{Fore.RED}{name}: IS NOT A VALID LOGGER\n'
                f'{Back.BLACK}{Fore.YELLOW}FALLING BACK TO {DEFAULT_LOGGER_NAME}\n'
            )
            logger = logging.getLogger(DEFAULT_LOGGER_NAME)
            return logger

        # name was valid
        logger = logging.getLogger(name)
        return logger
