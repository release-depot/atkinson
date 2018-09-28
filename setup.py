#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

TEST_REQUIRES = ['pytest', 'pytest-datadir', 'coverage']

setup(
    author="Jason Joyce",
    author_email='fuzzball81@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Python based release manager.",
    setup_requires=['pytest-runner'],
    install_requires=['pyyaml==3.13'],
    tests_require=TEST_REQUIRES,
    extras_require={'docs': ['sphinx', 'sphinx-autobuild', 'sphinx-rtd-theme'],
                    'test': TEST_REQUIRES},
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='atkinson',
    name='atkinson',
    packages=find_packages(include=['atkinson.*']),
    test_suite='tests',
    url='https://github.com/release-depot/atkinson',
    version='0.0.1',
    zip_safe=False,
)
