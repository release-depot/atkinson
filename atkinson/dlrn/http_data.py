#! /usr/bin/env python
"""Functions for working with the DLRN API"""

import csv
import os.path
import requests

from toolchest import yaml

from atkinson.config.manager import ConfigManager
from atkinson.logging.logger import getLogger


def _raw_fetch(url):
    """
    Fetch remote data and return the text output.

    :param url: The URL to fetch the data from
    :return: Raw text data, None otherwise
    """
    ret_data = None
    req = requests.get(url)
    if req.status_code == requests.codes.ok:
        ret_data = req.text

    return ret_data


def _fetch_yaml(url):
    """
    Fetch remote data and process the text as yaml.

    :param url: The URL to fetch the data from
    :return: Parsed yaml data in the form of a dictionary
    """
    ret_data = None
    raw_data = _raw_fetch(url)
    if raw_data is not None:
        ret_data = yaml.parse(raw_data)

    return ret_data


def dlrn_http_factory(host, config_file=None, logger=getLogger()):
    """
    Create a DlrnData instance based on a host.

    :param host: A host name string to build instances
    :param config_file: A dlrn config file(s) to use in addition to
                        the default.
    :param logger: An atkinson logger to use. Default is the base logger.
    :return: A DlrnData instance
    """
    manager = None
    files = ['dlrn.yml']
    if config_file is not None:
        if isinstance(config_file, list):
            files.extend(config_file)
        else:
            files.append(config_file)

    local_path = os.path.realpath(os.path.dirname(__file__))
    manager = ConfigManager(filenames=files, paths=local_path)

    if manager is None:
        return None

    config = manager.config
    if host not in config:
        return None

    return DlrnHttpData(config[host]['url'],
                        config[host]['release'],
                        logger=logger)


class DlrnHttpData():
    """A class used to interact with the dlrn API"""
    def __init__(self, url, release, logger=getLogger()):
        """
        Class constructor

        :param url: The URL to the host to obtain data.
        :param releases: The release name to use for lookup.
        :param logger: An atkinson logger to use. Default is the base logger.
        """
        self.url = url
        self.release = release
        self._logger = logger

    def _build_url(self, commit_hash, distgit_hash):
        """
        Generate a url given a commit hash and distgit hash to match the format
        base/AB/CD/ABCD123_XYZ987 where ABCD123 is the commit hash and XYZ987
        is a portion of the distgit hash.

        :param commit_hash: A string with the full commit hash on the change
        :param dlrn_hash: A string with the full dlrn hash to fetch from
        :return: A string with the full URL.
        """
        first = commit_hash[0:2]
        second = commit_hash[2:4]
        third = commit_hash + '_' + distgit_hash[0:8]
        return os.path.join(self.url, self.release, first, second,
                            third)

    def commit(self, name):
        """
        Get RDO consistent information

        :param name: The name of the link to process E.G. consistent or current

        :return: A list of dictionaries of name, dist-git hash and source hash.
                 An empty list is returned otherwise.
        """
        ret_data = []
        full_url = os.path.join(self.url,
                                self.release,
                                name, 'commit.yaml')
        data = _fetch_yaml(full_url)
        if data is not None and 'commits' in data:
            for pkg in data['commits']:
                if pkg['status'] == 'SUCCESS':
                    ret_data.append({'name': pkg['project_name'],
                                     'dist_hash': pkg['distro_hash'],
                                     'commit_hash': pkg['commit_hash']})
                else:
                    msg = '{0} has a status of error'.format(str(pkg))
                    self._logger.warning(msg)

        return ret_data

    def get_versions(self, commit_hash, distgit_hash):
        """
        Get the version data for the versions.csv file and return the
        data in a dictionary

        :param commit_hash: A string with the full commit hash on the change
        :param dlrn_hash: A string with the full dlrn hash to fetch from

        :return: A dictionary of packages with commit and dist-git hashes
        """
        ret_dict = {}
        full_url = os.path.join(self._build_url(commit_hash, distgit_hash),
                                'versions.csv')
        data = _raw_fetch(full_url)
        if data is not None:
            data = data.replace(' ', '_')
            split_data = data.split()
            reader = csv.DictReader(split_data)
            for row in reader:
                ret_dict[row['Project']] = {'source': row['Source_Sha'],
                                            'state': row['Status'],
                                            'distgit': row['Dist_Sha'],
                                            'nvr': row['Pkg_NVR']}
        else:
            msg = 'Could not fetch {0}'.format(full_url)
            self._logger.error(msg)

        return ret_dict
