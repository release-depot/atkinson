#! /usr/bin/env python
"""Module for loading/accessing config data"""

import yaml

from atkinson.config.search import get_config_files


def _update(current, incoming):
    """
    Method to update deeply nested dictionaries

    :param current: The current data we want to update.
    :param incoming: The data we want to update current with

    :return: A dictionary that is current with incoming's content
    """
    for key, value in incoming.items():
        if isinstance(value, dict):
            current[key] = _update(current.get(key, {}), value)
        else:
            current[key] = value
    return current


class ConfigManager():
    """Atkinson config file manager class"""
    def __init__(self, filenames=None, paths=None, defaults=True):
        """
        Constructor

        :param filenames: The file name(s) to load
        :param paths: Additional paths to use in the search
        :param defaults: Use the default file name and search paths
        """
        self._config_data = {}
        self._config_files = []
        for found_config in get_config_files(filenames=filenames,
                                             overrides=paths,
                                             add_defaults=defaults):
            self._parse(found_config)

    def _parse(self, filename):
        """
        Method to parse the config data

        :param filename: The fully qualified path to load and parse
        """
        with open(filename, 'r') as file_handle:
            data = yaml.safe_load(file_handle.read())
            self.config_data = _update(self._config_data, data)
            self._config_files.append(filename)

    @property
    def config(self):
        """
        The configuration data

        :return: Dictionary of configuration data
        """
        return self._config_data

    @property
    def config_files(self):
        """
        A list of processed config files

        :return: A list of config files found and parsed
        """
        return self._config_files
