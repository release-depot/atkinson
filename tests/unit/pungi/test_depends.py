#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `atkinson.pungi.depends` package."""

import copy
import os

import pytest

from toolchest.genericargs import GenericArgs

from atkinson.pungi.depends import rpmdep_to_dep, dep_to_tuple, dep_to_nevr
from atkinson.pungi.depends import dep_to_rpmdep, nevr_to_dep, transmogrify_met
from atkinson.pungi.depends import transmogrify_unmet, DependencySet


def test_rpmdep_to_dep():
    """Tests for rpmdep_to_dep"""
    with pytest.raises(ValueError):
        rpmdep_to_dep('foo 1.0')
    with pytest.raises(ValueError):
        rpmdep_to_dep('foo > 1.0-1-1')

    expected = {'name': 'foo'}
    assert rpmdep_to_dep('foo') == expected

    expected = {'name': 'foo', 'comparison': '>', 'version': '2.0'}
    assert rpmdep_to_dep('foo > 2.0') == expected

    expected = {'name': 'foo', 'comparison': '>=', 'release': '7',
                'epoch': 1, 'version': '2.0'}
    assert rpmdep_to_dep('foo >= 1:2.0-7') == expected


def test_dep_to_tuple():
    """Test dep_to_tuple"""
    with pytest.raises(ValueError):
        dep_to_tuple('Hello')
    with pytest.raises(ValueError):
        dep_to_tuple({})

    assert dep_to_tuple({'version': '1.0', 'release': '7'}) == (0, '1.0', '7')
    assert dep_to_tuple({'epoch': '2', 'version': '1.0', 'release': '7'}) == (2, '1.0', '7')


def test_dep_to_nevr():
    """Tests for dep_to_nevr function"""
    with pytest.raises(ValueError):
        dep_to_nevr({})

    val = {'name': 'test', 'version': '1.0', 'release': '1.el7ost'}
    for key in val:
        val_copy = copy.copy(val)
        del val_copy[key]
        print(val_copy)
        with pytest.raises(ValueError):
            dep_to_nevr(val_copy)

    assert dep_to_nevr(val) == 'test-1.0-1.el7ost'

    val['epoch'] = 1
    assert dep_to_nevr(val) == 'test-1:1.0-1.el7ost'


def test_dep_to_rpmdep():
    """Tests for dep_to_rpmdep function"""
    assert dep_to_rpmdep({'name': 'foo'}) == 'foo'
    assert dep_to_rpmdep({'name': 'foo',
                          'comparison': '>',
                          'version': '2.0'}) == 'foo > 2.0'

    assert dep_to_rpmdep({'name': 'foo',
                          'comparison': '>=',
                          'release': '7',
                          'epoch': '1',
                          'version': '2.0'}) == 'foo >= 1:2.0-7'


def test_nevr_to_dep():
    """Tests for nevr_to_dep function"""
    with pytest.raises(ValueError):
        nevr_to_dep('1.0-1')

    val = {'name': 'test', 'version': '1.0', 'release': '1.el7ost', 'comparison': '=='}
    assert nevr_to_dep('test-1.0-1.el7ost') == val

    val['epoch'] = 1
    assert nevr_to_dep('test-1:1.0-1.el7ost') == val


def test_transmogrify_met():
    """Tests for transmogrify_met function"""
    val_one = GenericArgs()
    val_two = GenericArgs()

    val_one.sourcerpm = 'foo-1.2-1.src.rpm'
    val_one.epoch = 0
    val_one.name = 'foo'
    val_one.version = '1.2'
    val_one.release = '1'

    val_two.sourcerpm = 'test-0.3-4.src.rpm'
    val_two.epoch = 1
    val_two.name = 'test'
    val_two.version = '0.3'
    val_two.release = '4'

    vals = [val_one, val_two]
    deps = transmogrify_met(vals)
    assert dep_to_nevr(deps[0]) == 'foo-1.2-1'
    assert dep_to_nevr(deps[1]) == 'test-1:0.3-4'


def test_transmogrify_unmet():
    """Tests for transmogrify_unmet function"""
    deps_nevr = ['test-1:0.3-4', 'foo-1.2-1']
    deps = []
    expected = []
    for dep in deps_nevr:
        expected.append(nevr_to_dep(dep))
        deps.append(dep_to_rpmdep(nevr_to_dep(dep)))

    with pytest.raises(ValueError):
        transmogrify_unmet('')

    ret = transmogrify_unmet(deps)
    assert expected == ret


def test_dependency_set_base():
    """ Test the DependencySet class """
    depset = DependencySet()
    assert depset.met == []
    assert depset.unmet == []
    assert depset.met == []

    # Config injection
    conf = {'build_sources':
            {'koji-tag-1': ['http://localhost/1',
                            'http://localhost/1.1'],
             'koji-tag-2': ['http://localhost/2']}}
    conf_copy = copy.copy(conf)

    depset = DependencySet(config={'build_sources':
                                   {'koji-tag-1': ['http://localhost/1',
                                                   'http://localhost/1.1'],
                                    'koji-tag-2': ['http://localhost/2']}})
    assert depset.config == conf_copy


def test_dependency_set(datadir):
    """ Test loading a configuration file """
    depset = DependencySet(config_file='test_build_sources.yml',
                           config_path=datadir)
    print(depset.config)
    assert depset.config == {'build_sources':
                             {'koji-tag-1': ['http://localhost/1',
                                             'http://localhost/1.1'],
                              'koji-tag-2': ['http://localhost/2']}}

    # Invalid version
    with pytest.raises(ValueError):
        specfile = os.path.join(datadir, 'openstack-swift.spec')
        depset.get_spec_build_deps(specfile, 'invalid-version')

    # File not fount
    with pytest.raises(OSError):
        specfile = os.path.join(datadir, 'nonexistent')
        depset.get_spec_build_deps(specfile, 'koji-tag-1')

    # Don't load a directory
    with pytest.raises(ValueError):
        depset.get_spec_build_deps(datadir, 'koji-tag-1')
