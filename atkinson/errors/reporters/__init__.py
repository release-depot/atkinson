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

        :param str title: A title for the report
        :param str description: Description for the report
        :param dict config: Configuration information for the report
        """

    @classmethod
    @abstractmethod
    def get(cls, report_id, config):
        """
        Get a current report object by ID

        :param str report_id: The ID for the report
        :param dict config: Configuration information for the report
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
