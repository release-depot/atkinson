#! /usr/bin/env python
"""
Base error class for Atkinson operations

Each of the errors atkinson can raise should use this base class. This will
ensure that each error can be acted upon and has the needed properties
"""

from abc import ABC, abstractmethod


class BaseError(ABC):
    """Atkinson base error class"""

    @property
    @abstractmethod
    def message(self):
        """The error message to use/log"""

    @abstractmethod
    def action(self):
        """
        The action to take on this error.
        This make be logging or displaying an error to more advanced error
        handling
        """

    @abstractmethod
    def clear(self):
        """
        Perform error clear actions.
        This may be updating logging or more advanced error clearing methods
        """
