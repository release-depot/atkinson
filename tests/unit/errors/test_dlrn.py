#! /usr/bin/env python
"""Test for the DLRN error handlers"""

from unittest.mock import create_autospec

import pytest

from atkinson.errors import BaseError
from atkinson.errors.dlrn import DlrnFTBFSError
from atkinson.errors.reporters import BaseReport


@pytest.fixture(scope='module')
def get_config():
    """ Test config generator """
    return {'url': 'test/url',
            'title': 'Test Error'}


@pytest.fixture()
def get_reporter():
    """ Test reporter mock generator """
    reporter = create_autospec(BaseReport)
    return reporter


@pytest.fixture()
def get_report():
    """ Test reporter mock generator """
    report = create_autospec(BaseReport)
    return report


def test_is_base(get_config, get_reporter):
    """
    Given we have DlrnFTBFSError object
    When we check the subclass is BaseError
    Then we get True
    """
    assert issubclass(DlrnFTBFSError, BaseError)


def test_packages(get_config, get_reporter):
    """
    Given we have a DlrnFTBFSError instance
    When we set the packages property
    Then we get the same list of packages
    """
    packs = ['my_package']
    expected = {'Failing Builds': packs}
    error = DlrnFTBFSError('Test Release', get_config, get_reporter)
    error.packages = packs
    assert expected == error.packages


def test_message(get_config, get_reporter):
    """
    Given we have a DlrnFTBFSError instance
    When we access the message property
    Then we get a non-empty string
    """
    error = DlrnFTBFSError('Test Release', get_config, get_reporter)
    assert error.message != ''


def test_error_id_calls_get(get_config, get_reporter):
    """
    Given we have a DlrnFTBFSError instance
    And it was initialized with an error id
    When object initialization is complete
    Then we have a call to fetch a report for that error id.
    """
    reporter = get_reporter
    DlrnFTBFSError('Test Release', get_config, reporter, error_id='1234')
    assert reporter.get.called
    args, kwargs = reporter.get.call_args
    assert args == ('1234', get_config)
    assert kwargs == {}


def test_action_raises_new_report(get_config, get_reporter):
    """
    Given we have a DlrnFTBFSError instance
    And no active reports and no packages
    When we call action
    Then a new report is created
    """
    reporter = get_reporter
    conf = get_config
    error = DlrnFTBFSError('Test Release', conf, reporter)
    error.action()
    assert reporter.new.called
    assert not reporter.update.called


def test_action_raises_new_report_packages(get_config,
                                           get_reporter, get_report):
    """
    Given we have a DlrnFTBFSError instance
    And no active reports and has packages
    When we call action
    Then a new report is created and update is called
    """
    reporter = get_reporter
    report = get_report
    reporter.new.return_value = report
    error = DlrnFTBFSError('Test Release', get_config, reporter)
    error.packages = ['my_bad_package']
    error.action()
    assert reporter.new.called
    assert report.update.called


def test_existing_updates(get_config, get_reporter, get_report):
    """
    Given we have a DlrnFTBFSError instance
    And an active report and have packages
    When we call action
    Then the existing report is updated.
    """
    reporter = get_reporter
    report = get_report
    reporter.get.return_value = report
    error = DlrnFTBFSError('Test Release', get_config, reporter,
                           error_id='1234')
    error.packages = ['my_bad_package']
    error.action()
    assert reporter.get.called
    assert not reporter.new.called
    assert report.update.called


def test_close(get_config, get_reporter, get_report):
    """
    Given we have a DlrnFTBFSError instance
    And an active report
    When we call clear
    Then the report is updated and cleared.
    """
    reporter = get_reporter
    report = get_report
    reporter.get.return_value = report
    error = DlrnFTBFSError('Test Release', get_config, reporter,
                           error_id='1234')
    error.clear()
    assert reporter.get.called
    assert report.update.called
    assert report.close.called
