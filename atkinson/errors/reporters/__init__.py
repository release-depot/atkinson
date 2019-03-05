#! /usr/bin/env python
"""
General error report classes
"""

from abc import ABC, abstractmethod


class BaseReport(ABC):
    """ Abstract base class for error reports """

    @classmethod
    @abstractmethod
    def new(cls, title, description, config):
        """
        Create a new report and return a report object

        :param title: A title for the report (str)
        :param description: Description for the report (str)
        :param config: Configuration information for the report (dict)
        """

    @classmethod
    @abstractmethod
    def get(cls, report_id, config):
        """
        Get a current report object by ID

        :param report_id: The ID for the report (str)
        :param config: Configuration information for the report (dict)
        """

    @property
    @abstractmethod
    def report_id(self):
        """
        The id of the report
        """

    @abstractmethod
    def update(self, **kwargs):
        """
        Update the data on an active report

        :param kwargs: Name=value pairs of data to update in the report
        """

    @abstractmethod
    def close(self):
        """
        Close out the report
        """
