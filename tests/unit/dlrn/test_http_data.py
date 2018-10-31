#! /usr/bin/env python
"""Tests for the DLRN api submodule"""

import os.path

import requests_mock

from atkinson.dlrn.http_data import DlrnHttpData, dlrn_http_factory


def test_factory_good_config(datadir):
    """
    Given we have a valid config file
    When we call the factory function
    Then we get a DlrnHttpData instance
    """
    config_file = os.path.join(datadir, 'config.yml')
    actual = dlrn_http_factory('tester', config_file=config_file)
    assert isinstance(actual, DlrnHttpData)


def test_factory_bad_config(datadir):
    """
    Given we have a bad config file
    When we call the factory function
    Then we get None
    """
    config_file = os.path.join(datadir, 'bad.yml')
    actual = dlrn_http_factory('tester', config_file=config_file)
    assert actual is None


def test_no_data_good_status(datadir):
    """
    GIVEN we have a DlrnHttpData instance with a working config
    WHEN we fetch the commit yaml but it contains no data
    AND the status code is good.
    THEN we get an empty list back from the call
    """
    config_file = os.path.join(datadir, 'config.yml')
    with requests_mock.Mocker() as mock:
        mock.get('http://testhost/test/consistent/commit.yaml',
                 text='',
                 status_code=200)
        dlrn = dlrn_http_factory('tester', config_file=config_file)
        actual = dlrn.commit('consistent')
        assert [] == actual


def test_no_data_bad_status(datadir):
    """
    GIVEN we have a DlrnHttpData instance with a working config
    WHEN we fetch the commit yaml but get a bad status code
    THEN we get an empty list back from the call
    """
    config_file = os.path.join(datadir, 'config.yml')
    with requests_mock.Mocker() as mock:
        mock.get('http://testhost/test/consistent/commit.yaml',
                 status_code=404)
        dlrn = dlrn_http_factory('tester', config_file=config_file)
        actual = dlrn.commit('consistent')
        assert [] == actual


def test_good_data_good_status(datadir):
    """
    GIVEN we have a DlrnHttpData instance with a working config
    WHEN we fetch the commit yaml and it contains data
    AND the status code is good
    THEN we get a list of commits back from the call
    """
    config_file = os.path.join(datadir, 'config.yml')
    real_data = os.path.join(datadir, 'commit.yaml')
    expected = [{'name': 'python-networking-l2gw',
                 'dist_hash': '44eea44aaa02e9d314c0288788254a9f316c5772',
                 'commit_hash': '1c087246c4a31bec1124acde610731c884c435f1'}]
    with open(real_data, 'r') as data:
        with requests_mock.Mocker() as mock:
            mock.get('http://testhost/test/consistent/commit.yaml',
                     text=data.read(),
                     status_code=200)
            dlrn = dlrn_http_factory('tester', config_file=config_file)
            actual = dlrn.commit('consistent')
            assert expected == actual


def test_good_data_bad_status(datadir):
    """
    GIVEN we have a DlrnHttpData instance
    WHEN we fetch the commit yaml and it contains data
    AND the status code is bad
    THEN we get a list of commits back from the call
    """
    config_file = os.path.join(datadir, 'config.yml')
    real_data = os.path.join(datadir, 'commit.yaml')
    with open(real_data, 'r') as data:
        expected = []
        with requests_mock.Mocker() as mock:
            mock.get('http://testhost/test/consistent/commit.yaml',
                     text=data.read(),
                     status_code=404)
            dlrn = dlrn_http_factory('tester', config_file=config_file)
            actual = dlrn.commit('consistent')
            assert expected == actual


def test_get_versions_good_status(datadir):
    """
    GIVEN we have a DlrnHttpData instance and commit and distgit hashs
    WHEN we call get_versions
    AND the status code is good
    THEN we get a dictionary with data
    """
    config_file = os.path.join(datadir, 'config.yml')
    real_data = os.path.join(datadir, 'versions.csv')
    with open(real_data, 'r') as data:
        expected = {'test-project': {'source': 'abc123',
                                     'state': 'SUCCESS',
                                     'distgit': 'zxy987',
                                     'nvr': 'test-project-1.0.el7'}}
        with requests_mock.Mocker() as mock:
            mock.get('http://testhost/test/ab/c1/abc123_zxy987/versions.csv',
                     text=data.read(),
                     status_code=200)
            dlrn = dlrn_http_factory('tester', config_file=config_file)
            actual = dlrn.get_versions('abc123', 'zxy987')
            assert expected == actual


def test_get_versions_bad_status(datadir):
    """
    GIVEN we have a DlrnHttpData instance and commit and distgit hashs
    WHEN we call get_versions
    AND the status code is bad
    THEN we get an empty dictionary
    """
    config_file = os.path.join(datadir, 'config.yml')
    real_data = os.path.join(datadir, 'versions.csv')
    with open(real_data, 'r') as data:
        expected = {}
        with requests_mock.Mocker() as mock:
            mock.get('http://testhost/test/ab/c1/abc123_zxy987/versions.csv',
                     text=data.read(),
                     status_code=404)
            dlrn = dlrn_http_factory('tester', config_file=config_file)
            actual = dlrn.get_versions('abc123', 'zxy987')
            assert expected == actual
