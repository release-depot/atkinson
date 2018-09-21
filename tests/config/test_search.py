#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `atkinson` package."""

import os

from unittest.mock import patch
from atkinson.config import search


def base_search_paths():
    """Helper function to generate the basic results"""
    home = os.environ['HOME']
    ret_list = [os.path.join(home, '.atkinson'),
                '/etc/atkinson',
                os.path.realpath('./configs')]
    return ret_list


def test_config_path_no_override():
    """Test we only get our paths"""
    assert search.config_search_paths() == base_search_paths()


def test_cofig_path_override():
    """Test if a single override is added"""
    expected = ['/opt']
    expected.extend(base_search_paths())
    assert search.config_search_paths('/opt') == expected


def test_config_path_override_list():
    """Test if a list of overrides is added"""
    expected = ['/opt', '/usr/share']
    expected.extend(base_search_paths())
    assert search.config_search_paths(['/opt', '/usr/share']) == expected


def test_config_path_with_user():
    """Test if a list that contains a path with ~ is expanded"""
    expected = [os.path.join(os.environ['HOME'], 'my_configs')]
    expected.extend(base_search_paths())
    assert search.config_search_paths('~/my_configs') == expected


def test_conf_path_list_user():
    """Test override list has a path with ~"""
    expected = [os.path.join(os.environ['HOME'], 'my_configs')]
    expected.extend(base_search_paths())
    assert search.config_search_paths(['~/my_configs']) == expected


def test_default_returned_slot_1():
    """Test config returned from ~/.atkinson"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.return_value = True
        assert search.get_config_file() == os.path.expanduser('~/.atkinson/config.yml')


def test_default_returned_slot_2():
    """Test config returned from /etc/atkinson"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.side_effect = [False, True]
        assert search.get_config_file() == '/etc/atkinson/config.yml'


def test_default_returned_slot_3():
    """Test config returned from ./config"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.side_effect = [False, False, True]
        assert search.get_config_file() == os.path.realpath('./configs/config.yml')


def test_default_not_found():
    """Test config can't be found in the default paths"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.side_effect = [False, False, False]
        assert search.get_config_file() == ''


def test_custom_returned_slot_1():
    """Test config returned from ~/.atkinson"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.side_effect = [True]
        expected = os.path.expanduser('~/.atkinson/my_config.yml')
        assert search.get_config_file(filename='my_config.yml') == expected


def test_custom_returned_slot_2():
    """Test config returned from /etc/atkinson"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.side_effect = [False, True]
        assert search.get_config_file(filename='my_config.yml') == '/etc/atkinson/my_config.yml'


def test_custom_returned_slot_3():
    """Test config returned from ./config"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.side_effect = [False, False, True]
        expected = os.path.realpath('./configs/my_config.yml')
        assert search.get_config_file(filename='my_config.yml') == expected


def test_default_override():
    """Test default config from override"""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.side_effect = [True]
        expected = os.path.expanduser('~/my_config_dir/config.yml')
        assert search.get_config_file(overrides='~/my_config_dir') == expected


def test_default_override_not_found():
    """Test an override is given but the file is not found. Fall back to the defaults."""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.side_effect = [False, True]
        expected = os.path.expanduser('~/.atkinson/config.yml')
        assert search.get_config_file(overrides=['~/my_config_dir']) == expected


def test_default_second_override():
    """Test overrides are given, the file is found in the second."""
    with patch('atkinson.config.search._check_available') as aval_mock:
        aval_mock.side_effect = [False, True]
        my_overrides = ['~/my_config_dir', '~/my_second_configs']
        expected = os.path.expanduser('~/my_second_configs/config.yml')
        assert search.get_config_file(overrides=my_overrides) == expected
