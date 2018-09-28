#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `atkinson` package."""

from atkinson.config.manager import ConfigManager


def test_nothing_loaded():
    """Test no config files found returns None"""
    manager = ConfigManager()
    assert manager.config == {}


def test_manager_load(datadir):
    """Test to see if a default (config.yml) is loaded using an override"""
    manager = ConfigManager(paths=datadir)
    expected = {'my_option': {'setting1': True, 'setting2': False}}
    assert manager.config == expected


def test_default_name_ignore_paths(datadir):
    """Test to see if we ignore the defaults nothing is loaded"""
    manager = ConfigManager(paths=datadir, defaults=False)
    assert manager.config == {}


def test_default_ignored_other_name(datadir):
    """Test if we give a custom name, it is loaded ignoring the defaults"""
    manager = ConfigManager(filenames='override.yml', paths=datadir, defaults=False)
    expected = {'my_option': {'setting2': True}}
    assert manager.config == expected


def test_override_wins(datadir):
    """Test if an override with same key overwrites the default"""
    manager = ConfigManager(filenames='override.yml', paths=datadir)
    expected = {'my_option': {'setting1': True, 'setting2': True}}
    assert manager.config == expected


def test_complex_override(datadir):
    """Test that a deep nested dict and list update"""
    manager = ConfigManager(filenames=['complex.yml', 'complex_override.yml'], paths=datadir)
    expected = {'my_option': {'extra': True,
                              'nested': {'more_nested': {'even_more_nested': True}},
                              'setting1': True,
                              'setting2': True,
                              'setting_list': [3, 2, 1]}}
    assert manager.config == expected
