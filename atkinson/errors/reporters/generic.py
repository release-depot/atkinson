#! /usr/bin/env python
""" Python logging based reporter """

from atkinson.errors.reporters import BaseReport
from atkinson.logging.logger import getLogger


class GenericReporter(BaseReport):
    """ Class for a generic reporter based on the logging module """

    def __init__(self, title, logger):
        """
        Class constructor
        :param logger: The logger to use
        """
        self.__title = title
        self.__log = logger

    @classmethod
    def new(cls, title, description, config):
        """
        Create a new report
        :param title: The title for the report
        :param description: A description for the report
        :param config: Configuration dictionary for the report
        :return: A LoggingReporter instance
        """
        log = getLogger()
        log.error(f"{title}: {description}")
        return cls(title, log)

    @classmethod
    def get(cls, report_id, config):
        """
        Retrieve an active report
        :param report_id: The unique id (the report title) for the report
        :param config: Configuration dictionary for the report
        :return: A LoggingReporter instance
        """
        return cls(report_id, getLogger())

    @property
    def report_id(self):
        """
        Return the unique id for this report
        """
        return self.__title

    def update(self, **kwargs):
        """
        Update the report
        :param kwargs: A dictionary of named arguments to report
        """
        if self.__log:
            message = (f"{self.__title}:\n\t"
                       + "\n\t".join([f"{key}: {value}"
                                      for key, value in kwargs.items()]))
            self.__log.error(message)

    def close(self):
        """
        Close the report
        """
        self.__log.error(f"Closing report: {self.report_id}")
        self.__log = None
