"""Standardize logging on behalf of the package.

Logger.initialize(debugging=True) will duplicate any log output, and add debug messages,
to <PKG>_YYYYMMDD_HHMMSS.log in the temporary directory.

clear; tail -f `ls /tmp/*.log | tail -n 1`

    Typical usage example:

    from gallant_input.logger import Logger

    Logger.initialize(debugging=True)      # At the beginning
    Logger.debug('DEBUGGING')              # Debug logging is controlled by Logger.initialize()
    Logger.error('Something went wrong!')  # Log errors to stderr
    Logger.info('You should know this.')   # Log information to stdout
    Logger.shutdown()                      # At the end
"""
# Standard
from datetime import datetime
from enum import IntEnum
import logging
import os
import sys
# Third Party
# Local
from gallant_input.constants import PKG_SHORT_TITLE
from gallant_input.misc import determine_tmp_dir


# pylint: disable=too-few-public-methods, no-self-argument
class LogLevel(IntEnum):
    """Defines logging levels."""
    DEBUG = logging.DEBUG  # Debug messages
    ERROR = logging.ERROR  # Error messages
    INFO = logging.INFO    # Standard messages


class DebugHandler(logging.Filter):
    """Filters what can be logger by a specific logger."""
    def filter(self, record):
        return record.levelno in (logging.DEBUG,)


class ErrorHandler(logging.Filter):
    """Filters what can be logger by a specific logger."""
    def filter(self, record):
        return record.levelno in (logging.ERROR,)


class InfoHandler(logging.Filter):
    """Filters what can be logger by a specific logger."""
    def filter(self, record):
        return record.levelno in (logging.INFO,)


class Logger():
    """Logging class for the package."""

    _initialized = False  # Logging subsystem status
    _filename = ''        # Absolute debug log filename

    def __del__(self) -> None:
        """Class dtor."""
        Logger.shutdown()

    @staticmethod
    def initialize(debugging: bool = False) -> None:
        """Initializes the logging subsystem.

        Args:
            debug: [Optional] If True, sets the logging level to DEBUG and logs to
                jitb_YYYYMMDD_HHMMSS.log in the temporary directory.

        Function is optional as the logging class auto-initializes if called without initialization
        """
        # LOCAL VARIABLES
        debug = None                       # Debug stream handler
        error = None                       # Error stream handler
        normal = None                      # Info stream handler
        root_logger = logging.getLogger()  # Root logger
        # Message formatter
        formatter = logging.Formatter(fmt='[%(asctime)s.%(msecs)03d] %(levelname)-9s - %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')

        # SETUP
        Logger._filename = _create_filename()

        if debugging:
            normal = logging.FileHandler(Logger._filename)
            normal.addFilter(InfoHandler())
            normal.setFormatter(formatter)
            normal.setLevel(logging.INFO)

            error = logging.FileHandler(Logger._filename)
            error.addFilter(ErrorHandler())
            error.setFormatter(formatter)
            error.setLevel(logging.ERROR)

            root_logger.addHandler(normal)
            root_logger.addHandler(debug)
            root_logger.addHandler(error)
        else:
            root_logger.setLevel(logging.INFO)

        # DONE
        Logger._initialized = True

    def debug(message: str, logger: str = __name__) -> None:
        """Log debug level messages.

        Args:
            message: Message to log
            logger: Logger name if needed.
        """
        Logger._check_logger()
        logging.getLogger(logger).debug(message)

    def error(message: str, logger: str = __name__) -> None:
        """Log error level messages.

        Args:
            message: Message to log
            logger: Logger name if needed.
        """
        print(message, file=sys.stderr)
        Logger._check_logger()
        logging.getLogger(logger).error(message)

    def info(message: str, logger: str = __name__) -> None:
        """Log info level messages.

        Args:
            message: Message to log
            logger: Logger name if needed.
        """
        print(message, file=sys.stdout)
        Logger._check_logger()
        logging.getLogger(logger).info(message)

    def log(level: LogLevel, message: str = '', logger: str = __name__) -> None:
        """Log on behalf of the project.

        Args:
            level: Priority level of message
            message: Message to log
            logger: Logger name if needed.
        """
        logging.getLogger(logger).log(level, message)

    @staticmethod
    def shutdown() -> None:
        """Call logging.shutdown()."""
        logging.shutdown()

    # pylint: disable=no-method-argument
    def _check_logger() -> None:
        """Verify the logger was initialized."""
        if Logger._initialized is False:
            raise RuntimeError('Call Logger.initialize() first!')


def _create_filename() -> str:
    """Determine filename to use for logging."""
    # LOCAL VARAIBLES
    abs_log_filename = ''  # Absolute filename of the log to use
    now = datetime.now()   # Current date and time
    number = 0             # Number of times the generated filename has been detected

    # CREATE IT
    while True:
        abs_log_filename = os.path.join(determine_tmp_dir(),
                                        f'{PKG_SHORT_TITLE.lower()}_'
                                        f'{now.strftime("%Y%m%d_%H%M%S")}-{str(number)}.log')
        if os.path.isfile(abs_log_filename):
            number += 1
        else:
            break

    # DONE
    return abs_log_filename


def log_exception(error: Exception) -> None:
    """Print an exception message to stderr."""
    try:
        Logger.error(repr(error))
    except RuntimeError:
        # Failed arg parsing can result in a failure to initialize the logger
        print(repr(error), file=sys.stderr, flush=True)  # Just print it to stderr
