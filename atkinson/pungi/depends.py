#! /usr/bin/env python
""" Interface with rpmreq to determine build dependencies """
from __future__ import print_function

import copy
import os
import stat
import logging

from toolchest.rpm.utils import split_filename, componentize

try:
    from rpmreq.actions import build_requires
    from rpmreq.query import Repo
except ImportError:
    def build_requires(filename, repos, **kwargs):  # NOQA
        # pylint: disable=unused-argument
        """
        Stub build-requires
        rpmreq and, by extension, hawkey is required for deployment,
        but not for testing.
        Hawkey is part of libdnf, written in C, and not published
        to PyPI.
        """
        if 'logger' in kwargs:
            kwargs['logger'].warn('build_requires: hawkey missing')
        return [], [], []

    from collections import namedtuple
    Repo = namedtuple('Repo', ['id', 'url'])

from atkinson.config.manager import ConfigManager


class DependencySet():
    """
    Dependency Set generated from a source spec file and a given build tag.
    Includes: Met dependencies, dependencies with the wrong version,
              and missing dependencies.

    Met dependencies:
        [ {'name', 'version', 'release', 'epoch', 'component'}, ... ]
                                                   ^ From source rpm name
        ('comparison' is included, too, but is always '==')

    Unmet dependencies:
        [ {'name', 'version', 'release', 'epoch', 'comparison'}, ... ]
                                                   ^ >=, ==, >, if available
    Missing:
        [ {'name', 'version', 'release', 'epoch', 'comparison'}, ... ]

    Config file format:
    ---

    build_sources:
        build-version-1:
            - http://whatever-location-1/x86_64
            - http://whatever-location-2/x86_64
        build-version-2:
            - http://whatever-location-3/arch/
    """

    def __init__(self, **kwargs):
        if 'config' not in kwargs:
            # Don't need to keep this around
            args = {}
            if 'config_file' in kwargs:
                args['filenames'] = [kwargs['config_file']]
                del kwargs['config_file']
            else:
                args['filenames'] = ['build_sources.yml']

            if 'config_path' in kwargs:
                args['paths'] = kwargs['config_path']

            mgr = ConfigManager(**args)
            self.config = copy.copy(mgr.config)
        else:
            self.config = copy.copy(kwargs['config'])
            del kwargs['config']

        self.met = []
        self.wrong_version = []
        self.unmet = []

        # Allow caller to inject logging infrastructure, if desired.
        # Eventually, pass to rpmreq, although, we don't log anything
        # in this code directly.
        if 'logger' in kwargs:
            self.log = kwargs['logger']
            self.provided_log = True
        else:
            self.log = logging.getLogger(__name__)
            self.provided_log = False

        if 'filename' in kwargs and 'version' in kwargs:
            filename = kwargs['filename']
            del kwargs['filename']
            version = kwargs['version']
            del kwargs['version']
            self.get_spec_build_deps(filename, version, **kwargs)

    def get_spec_build_deps(self, filename, version, **kwargs):
        """Call in to rpmreq and retrieve dependencies."""
        st_info = os.stat(filename)
        if not stat.S_ISREG(st_info.st_mode):
            raise ValueError('{0} is not a regular file'.format(filename))

        if not filename.endswith('.spec'):
            raise ValueError('{0} is not a spec file'.format(filename))

        self.filename = filename

        if not self.config or self.config == {} or \
                'build_sources' not in self.config:
            return

        srcs = self.config['build_sources']
        if version not in srcs:
            raise ValueError('Invalid version: {0}, expected one of {1}'.format(
                version,
                [ver for ver in srcs]))

        repos = []
        for idx in range(len(srcs[version])):
            repos.append(Repo(str(idx), srcs[version][idx]))

        # TODO: rpmreq supporting passdown of logger
        # e.g. if self.provided_log:
        #          (add logger=self.log to kwargs)
        met_deps, wrong_version, unmet_deps = \
            build_requires(filename, repos)

        self.met = transmogrify_met(met_deps)
        self.wrong_version = transmogrify_unmet(wrong_version)
        self.unmet = transmogrify_unmet(unmet_deps)

        if 'logger' in kwargs:
            kwargs['logger'].info(str(self))

    def __str__(self):
        """Report useful information about ourself."""
        fname = os.path.basename(self.filename)
        str_format = '{0}: {1} met, {2} incorrect, {3} missing'
        return str_format.format(fname, len(self.met), len(self.wrong_version), len(self.unmet))


def transmogrify_met(met_deps):
    """
    Convert a Hawkey dependency into a simple dict

    This is generally only used by DependencySet, but could be used
    elsewhere
    """
    if not isinstance(met_deps, list):
        raise ValueError('met_deps is not a list')
    ret = []
    for dep in met_deps:
        info = {'component': componentize(dep.sourcerpm),
                'epoch': dep.epoch,
                'name': dep.name,
                'comparison': '==',   # This is the version provided
                'version': dep.version,
                'release': dep.release}
        ret.append(info)
    return ret


def transmogrify_unmet(unmet_deps):
    """
    Convert list of string or repo.Depends to our simple dict format

    This is generally only used by DependencySet, but could be used
    elsewhere
    """
    if not isinstance(unmet_deps, list):
        raise ValueError('unmet_deps is not a list')
    ret = []
    for dep in unmet_deps:
        info = rpmdep_to_dep(str(dep))
        ret.append(info)
    return ret


def dep_to_tuple(dep):
    """Convert one of our dependencies into an RPM-style tuple"""
    if not isinstance(dep, dict):
        raise ValueError('dep is not a dict')
    if 'version' not in dep:
        raise ValueError('Cannot convert {0}: version missing'.format(str(dep)))
    epoch = 0
    version = None
    release = None
    if 'epoch' in dep:
        epoch = int(dep['epoch'])
    version = dep['version']
    if 'release' in dep:
        release = dep['release']
    return (epoch, version, release)


def dep_to_nevr(dep):
    """Convert one of our dependencies into an RPM NEVR string"""
    if not isinstance(dep, dict):
        raise ValueError('dep is not a dict')
    for field in ('name', 'version', 'release'):
        if field not in dep:
            raise ValueError('Cannot convert {0}: {1} missing'.format(str(dep), field))
    ret = dep['name']
    ret = ret + '-'
    if 'epoch' in dep and dep['epoch'] not in ('0', 0, ''):
        ret = ret + str(dep['epoch']) + ':'
    ret = ret + str(dep['version'])
    ret = ret + '-' + dep['release']
    return ret


def dep_to_rpmdep(dep):
    """Convert a dependency into an RPM dependency string"""
    if 'comparison' not in dep:
        return dep['name']
    ret = '{0} {1} '.format(dep['name'], dep['comparison'])
    if 'epoch' in dep and dep['epoch'] not in ('', 0, '0'):
        ret = ret + '{0}:'.format(dep['epoch'])
    ret = ret + '{0}'.format(dep['version'])
    if 'release' in dep and dep['release'] != '':
        ret = ret + '-{0}'.format(dep['release'])
    return ret


def rpmdep_to_dep(dep):
    """Convert a RPM style dependency into a simple dict"""
    vals = dep.split(' ')
    if len(vals) == 1:
        return {'name': vals[0]}
    if len(vals) != 3:
        raise ValueError('Could not parse: \"' + dep + '\"')
    ret = {'name': vals[0],
           'comparison': vals[1]}
    evr = vals[2].split('-')
    if len(evr) > 2:
        raise ValueError('Could not parse: \"' + dep + '\"')

    if len(evr) == 2:
        ret['release'] = evr[1]
        if ret['release'] == 'None':
            del ret['release']

    if ':' in evr[0]:
        e_v = evr[0].split(':')
        ret['epoch'] = int(e_v[0])
        if ret['epoch'] == '0':
            del ret['epoch']
        ret['version'] = e_v[1]
    else:
        ret['version'] = evr[0]

    return ret


def nevr_to_dep(dep):
    """Convert a RPM NEVR string to a simple dict"""
    (name, version, release, epoch, _) = split_filename(dep)
    ret = {}

    if name == '':
        raise ValueError('Could not parse: \"' + dep + '\"')

    ret['name'] = name
    ret['version'] = version
    ret['comparison'] = '=='
    if epoch not in ('', 0, '0'):
        ret['epoch'] = int(epoch)
    if release != 'None' and release is not None:
        ret['release'] = release

    return ret


def _main(argv):
    """Simple test program"""
    if len(argv) < 3:
        print('Usage: {0} <filename> <version>'.format(argv[0]))
        return 1
    depends = DependencySet(filename=argv[1], version=argv[2])
    if not depends:
        return 1

    if depends.met:
        print('Met:')
        for dep in depends.met:
            print('  ' + dep_to_nevr(dep))
    if depends.wrong_version:
        print()
        print('Wrong version:')
        for dep in depends.wrong_version:
            print('  ' + dep_to_rpmdep(dep))
    if depends.unmet:
        print()
        print('Unmet:')
        for dep in depends.unmet:
            print('  ' + dep_to_rpmdep(dep))
    return 0


if __name__ == '__main__':
    import sys
    exit(_main(sys.argv))
