#! /usr/bin/env python
"""Search tools for configuration files"""

from __future__ import print_function

import os


# Using a tuple here over a list to insure it's immutable.
DEFAULT_CONFIG_PATHS = (os.path.realpath('./configs'),
                        '/etc/atkinson',
                        os.path.expanduser('~/.atkinson'))


def _check_available(filename):   # pragma: no cover
    """
    Check to see if the filename exists and is a file

        :param filename: str A fully qualified path and file
        :returns: Boolean
    """
    return os.path.exists(filename) and os.path.isfile(filename)


def config_search_paths(override_list=None):
    """
    Generate a list of paths to search for config files

        :param override_list: A list for string path to use as a override location Default: None
        :returns: generator function of search paths.
    """
    for default in DEFAULT_CONFIG_PATHS:
        yield default

    if override_list is not None:
        if isinstance(override_list, list):
            for override_path in override_list:
                yield os.path.realpath(os.path.expanduser(override_path))
        else:
            yield os.path.realpath(os.path.expanduser(override_list))


def get_config_files(filenames=None, overrides=None, add_defaults=True):
    """
    Search for filename, or return the default config file

        :param filenames: list or string of file names to search for Default: None
        :param overrides: list of string of paths to use for searching Default: None
        :param add_defaults: Boolean Control if the default file name (config.yml) is added
                             to the search

        :returns: generator function of available config files
    """
    file_names = []
    if add_defaults is True:
        file_names.append('config.yml')

    if filenames is not None:
        if isinstance(filenames, list):
            file_names.extend(filenames)
        else:
            file_names.append(filenames)

    for path in config_search_paths(override_list=overrides):
        for filename in file_names:
            full_path = os.path.join(path, filename)
            if _check_available(full_path):
                yield full_path
