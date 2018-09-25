#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `atkinson` package."""

import os

import pytest

from unittest.mock import patch
from atkinson.config import search


class CheckAvailMock(object):
    """Class to control how paths are checked"""
    def __init__(self, expected):
        """Constructor"""
        self.expected = expected

    def check(self, full_path):
        """Method to match paths that we want"""
        return full_path in self.expected


def test_config_path_no_override():
    """Test we only get our paths"""
    assert list(search.config_search_paths()) == list(search.DEFAULT_CONFIG_PATHS)


def test_cofig_path_override():
    """Test if a single override is added"""
    expected = list(search.DEFAULT_CONFIG_PATHS)
    expected.append('/opt')
    assert list(search.config_search_paths('/opt')) == expected


def test_config_path_override_list():
    """Test if a list of overrides is added"""
    expected = list(search.DEFAULT_CONFIG_PATHS)
    expected.extend(['/opt', '/usr/share'])
    assert list(search.config_search_paths(['/opt', '/usr/share'])) == expected


def test_config_path_with_user():
    """Test if a list that contains a path with ~ is expanded"""
    expected = list(search.DEFAULT_CONFIG_PATHS)
    expected.extend([os.path.join(os.environ['HOME'], 'my_configs')])
    assert list(search.config_search_paths('~/my_configs')) == expected


def test_conf_path_list_user():
    """Test override list has a path with ~"""
    expected = list(search.DEFAULT_CONFIG_PATHS)
    expected.extend([os.path.join(os.environ['HOME'], 'my_configs')])
    assert list(search.config_search_paths(['~/my_configs'])) == expected


def test_default_returned_all():
    """Test config returned from ~/.atkinson"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.return_value = True
        expected = [os.path.join(x, 'config.yml') for x in search.DEFAULT_CONFIG_PATHS]
        assert list(search.get_config_files()) == expected


@pytest.mark.parametrize('expected', [os.path.realpath('./configs/config.yml'),
                                      '/etc/atkinson/config.yml',
                                      os.path.expanduser('~/.atkinson/config.yml')])
def test_default_slots(expected):
    """Test config returned from each default path individually"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        check = CheckAvailMock(expected)
        aval_mock.side_effect = check.check
        assert list(search.get_config_files()) == [expected]


def test_default_not_found():
    """Test config can't be found in the default paths"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.return_value = False
        assert list(search.get_config_files()) == []


@pytest.mark.parametrize('expected_path', list(search.DEFAULT_CONFIG_PATHS))
def test_custom_returned_slot(expected_path):
    """Test custom config file name can be returned from the default paths"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        file_name = 'my_config.yml'
        expected = [os.path.join(expected_path, file_name)]
        check = CheckAvailMock(expected)
        aval_mock.side_effect = check.check
        assert list(search.get_config_files(filenames=file_name)) == expected


def test_default_override():
    """Test default config from override"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        file_name = 'config.yml'
        override = '~/my_config_dir'
        expected = [os.path.join(os.path.expanduser(override), file_name)]
        check = CheckAvailMock(expected)
        aval_mock.side_effect = check.check
        assert list(search.get_config_files(overrides=override)) == expected


def test_default_override_not_found():
    """Test an override is given but the file is not found. Fall back to the defaults."""
    with patch('atkinson.config.search._check_available') as aval_mock:
        my_overrides = ['~/my_config_dir']
        file_name = 'config.yml'
        expected = [os.path.join(os.path.expanduser(x), file_name) for x in my_overrides]
        check = CheckAvailMock(expected)
        aval_mock.side_effect = check.check
        assert list(search.get_config_files(overrides=my_overrides)) == expected


def test_default_second_override():
    """Test overrides are given, the file is found in the second."""
    with patch('atkinson.config.search._check_available') as aval_mock:
        my_overrides = ['~/my_config_dir', '~/my_second_configs']
        file_name = 'config.yml'
        expected = [os.path.join(os.path.expanduser(x), file_name) for x in my_overrides]
        check = CheckAvailMock(expected)
        aval_mock.side_effect = check.check
        assert list(search.get_config_files(overrides=my_overrides)) == expected


def test_several_confs_no_override():
    """ Test that several configs can be found"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        file_names = ['configA.yml', 'configB.yml']
        expected = [os.path.join('/etc/atkinson', x) for x in file_names]
        check = CheckAvailMock(expected)
        aval_mock.side_effect = check.check
        assert list(search.get_config_files(filenames=file_names)) == expected


def test_several_confs_mix_override():
    """Test that several configs can be found in overrides and defaults"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        file_names = ['configA.yml', 'configB.yml']
        override = '/opt/configs'
        expected = ['/etc/atkinson/configB.yml', '/opt/configs/configA.yml']
        check = CheckAvailMock(expected)
        aval_mock.side_effect = check.check
        assert list(search.get_config_files(filenames=file_names, overrides=override)) == expected


def test_override_extra_defaults():
    """Test an extra filename, override and default filename returns the correct order"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        override = '/opt/configs'
        expected = ['/opt/configs/config.yml', '/opt/configs/extra.yml']
        check = CheckAvailMock(expected)
        aval_mock.side_effect = check.check
        assert list(search.get_config_files(filenames='extra.yml', overrides=override)) == expected
