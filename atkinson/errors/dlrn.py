#! /usr/bin/env python
"""
Atkinson Dlrn Error Handling.

The error classes here are for errors that occur when interacting with dlrn
and not errors in the atkinson application itself.
"""
import datetime
import os.path

from atkinson.errors import BaseError


class DlrnFTBFSError(BaseError):
    """
    DLRN Failing To Build From Source Error handler

    :param str release: String name for the release the error was found
    :param dict config: Dictionary of configuration data for the reporter
    :param BaseReport reporter: A reporter to use for this error
    :param str error_id: An error report id to be used (Default None)
    """
    def __init__(self, release, config, reporter, error_id=None):
        self.__release = release
        self.__conf = config
        self.__packages = None
        self.__report = None
        self.__reporter = reporter

        if error_id:
            self.__report = self.__reporter.get(error_id, config)
        else:
            title = self.__conf.get('title') + f"[{release}]"
            self.__report = self.__reporter.new(title,
                                                self.message,
                                                self.__conf)

    @property
    def id(self):
        """ Return the id for the error """
        return self.__report.report_id

    @property
    def packages(self):
        """ The list packages that failed to build """
        return self.__packages

    @packages.setter
    def packages(self, packages):
        self.__packages = {'Failing Builds': packages}

    @property
    def message(self):
        """ The error massage to display """
        url = os.path.join(self.__conf.get('url', ''), 'status_report.html')
        message = (f"Results as of: {datetime.datetime.utcnow()} UTC\n"
                   f"Build Details: {url}")
        return message

    def action(self):
        """ Run reporting actions """

        if self.packages:
            self.__report.update(description=self.message,
                                 checklist=self.packages)

    def clear(self):
        self.__report.update(description=self.message)
        self.__report.close()
