#! /usr/bin/env python
"""Search tools for configuration files"""

from __future__ import print_function

import os


def _check_available(filename):   # pragma: no cover
    """Check to see if the filename exists and is a file"""
    return os.path.exists(filename) and os.path.isfile(filename)


def config_search_paths(override_list=None):
    """Generate a list of paths to search for config files"""
    default = [os.path.expanduser('~/.atkinson'), '/etc/atkinson', os.path.realpath('./configs')]
    if override_list is None:
        return default

    ret_list = []
    if isinstance(override_list, list):
        for raw in override_list:
            ret_list.append(os.path.realpath(os.path.expanduser(raw)))
    else:
        ret_list = [os.path.realpath(os.path.expanduser(override_list))]

    ret_list.extend(default)
    return ret_list


def get_config_file(filename='config.yml', overrides=None):
    """Search for filename, or return the default config file"""
    ret_path = ''
    for path in config_search_paths(override_list=overrides):
        full_path = os.path.join(path, filename)
        if _check_available(full_path):
            ret_path = full_path
            break
    return ret_path
