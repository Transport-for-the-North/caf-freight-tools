"""
Handles tool logging and other general tasks
"""
#standard imports
import logging
import pathlib
from typing import Optional

#constants

PARENT_LOGGER = "TV"

class ThirstyVehicleLog:
    """Manages the Thirsty Truck tool log file.

    Parameters
    ----------
    file : pathlib.Path, optional
        File to save the log file to, if not given doesn't create
        a file. Can be done later with `DlitLog.add_file_handler`.
    """

    def __init__(self, title: str, file: Optional[pathlib.Path] = None):
        self.logger = logging.getLogger(PARENT_LOGGER)
        self.logger.setLevel(logging.DEBUG)

        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        self.logger.addHandler(sh)

        logging.captureWarnings(True)
        self.init_message(logging.INFO, title)

        if file is not None:
            self.add_file_handler(file)

    def init_message(self, level: int, init_msg: str) -> None:
        """Log tool initialisation message."""
        self.logger.log(level, init_msg)
        self.logger.log(level, "-" * len(init_msg))

    def add_file_handler(self, file: pathlib.Path) -> None:
        """Add file handler to logger.

        Parameters
        ----------
        file : pathlib.Path
            Path to log file to create or append to.
        """
        if not file.parent.exists():
            file.parent.mkdir()

        exists = file.exists()

        fh = logging.FileHandler(file)
        fh.setLevel(logging.DEBUG)
        form = logging.Formatter(
            "{asctime} [{name:20.20}] [{levelname:10.10}] {message}", style="{"
        )
        fh.setFormatter(form)
        self.logger.addHandler(fh)

        if not exists:
            self.logger.info("Created log file: %s", file)
        else:
            self.logger.info("Appending log messages to: %s", file)

    def __enter__(self):
        """Initialises logger and log file."""
        return self

    def __exit__(self, excepType, excepVal, traceback):
        """Closes log file.

        Note
        ----
        This function should not be called manually but will be
        called upon error / exit of a `with` statement.
        """
        # Write exception to logfile
        if excepType is not None or excepVal is not None or traceback is not None:
            self.logger.critical(
                "Oh no a critical error occurred (I'm not angry, just disappointed)", exc_info=True)
        else:
            self.logger.info("Program completed without any fatal errors")

        self.logger.info("Closing log file")
        logging.shutdown()

def get_logger(name: str)->logging.Logger:
    return logging.getLogger(f"{PARENT_LOGGER}.{name}")