#! /usr/bin/env python
""" Tests for the GenericReporter reporter """

from logging import Logger
from unittest.mock import create_autospec, patch

import pytest

from atkinson.errors.reporters.generic import GenericReporter


@pytest.fixture()
def get_logger_mock():
    """ Get the mock of the atkinson logging module. """

    patcher = patch('atkinson.errors.reporters.generic.getLogger')
    log = patcher.start()
    log.return_value = create_autospec(Logger)
    yield log
    patcher.stop()


def test_new(get_logger_mock):
    """
    Given we have a GenericReporter instance
    When we call new
    Then we get a GenericReporter object back and the logger is called
    """

    mock_log = get_logger_mock()
    report = GenericReporter.new('Test', 'Test description', {})
    assert isinstance(report, GenericReporter)
    assert mock_log.error.called


def test_get():
    """
    Given we have a report id and a GenericReporter instance
    When we call get
    Then we get a GenericReporter object back
    """
    report = GenericReporter.get('Test', {})
    assert isinstance(report, GenericReporter)


def test_report_id():
    """
    Given we have a GenericReporter instance
    When we call object.report_id
    Then we get back the report's title
    """
    title = 'Test'
    report = GenericReporter.new('Test', 'Test Description', {})
    assert report.report_id == title


def test_update(get_logger_mock):
    """
    Given we have an existing report
    When we call update with arguments
    Then then a new error message is generated
    """
    expected = "Test:\n\tkey1: value1\n\tkey2: value2"
    update_args = {'key1': 'value1', 'key2': 'value2'}
    mock_log = get_logger_mock()
    report = GenericReporter.new('Test', 'Test description', {})
    report.update(**update_args)
    assert mock_log.error.called
    args, kwargs = mock_log.error.call_args
    assert args == (expected,)
    assert kwargs == {}


def test_close(get_logger_mock):
    """
    Given we have an existing report
    When we call close
    Then an error message is generated
    """
    expected = "Closing report: Test"
    mock_log = get_logger_mock()
    report = GenericReporter.new('Test', 'Test description', {})
    report.close()
    assert mock_log.error.called
    args, kwargs = mock_log.error.call_args
    assert args == (expected,)
    assert kwargs == {}


def test_no_update_after_close(get_logger_mock):
    """
    Given we have an existing report
    When we call close and then try to call update
    Then an error message is not  generated
    """
    mock_log = get_logger_mock()
    report = GenericReporter.get('Test', {})
    report.close()
    report.update(description='New description')
    assert mock_log.error.call_count == 1
