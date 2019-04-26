#! /usr/bin/env python
""" Tests for the TrelloCard reporter """

from unittest.mock import call, create_autospec, patch

import pytest

from trollo import Boards, Cards, Checklists, TrelloApi

from atkinson.errors.reporters.trello import TrelloCard, get_columns


@pytest.fixture()
def get_api():
    """ Trello Card api mock fixture """
    patcher = patch('atkinson.errors.reporters.trello.get_trello_api')
    func = patcher.start()
    api_mock = create_autospec(TrelloApi)
    api_mock.cards = create_autospec(Cards)
    api_mock.checklists = create_autospec(Checklists)
    api_mock.boards = create_autospec(Boards)
    func.return_value = api_mock
    yield func
    patcher.stop()


@pytest.fixture()
def get_columns_mock():
    """ Trello board column mock """
    patcher = patch('atkinson.errors.reporters.trello.get_columns')
    column = patcher.start()
    column.return_value = ('123', '987')
    yield column
    patcher.stop()


@pytest.fixture()
def good_config():
    """ A good configuration """
    return {'board_id': 'abc123', 'new_column': 'a', 'close_column': 'b'}


def get_instance(api):
    """ Generate a TrelloCard instance """
    return TrelloCard('card_id', api, '123', '987')


def test_columns_good_config(get_api):
    """
    Given we have a proper config and a trello api handle
    When we call get_columns
    Then we get a tuple of trello column ids back
    """
    api = get_api()
    api.boards.get_list.return_value = [{'name': 'a', 'id': '123'},
                                        {'name': 'b', 'id': '456'}]
    conf = {'board_id': 'abc123', 'new_column': 'a', 'close_column': 'b'}
    expected = ('123', '456')
    actual = get_columns(api.boards, conf)
    assert actual == expected
    assert api.boards.get_list.called


@pytest.mark.parametrize('conf', [{},
                                  {'board_id': 'abc123'},
                                  {'board_id': 'abc123', 'new_column': 'a'},
                                  {'board_id': 'abc123', 'close_column': 'b'},
                                  {'new_column': 'a', 'close_column': 'b'}])
def test_columns_bad_config(conf, get_api):
    """
    Given we have a bad config and a trello api handle
    When we call get_columns
    Then a KeyError exception is raised and the api is not called
    """
    with pytest.raises(KeyError):
        api = get_api()
        get_columns(api, conf)


def test_new(get_api, get_columns_mock, good_config):
    """
    Given we have a TrelloCard instance
    When we call new
    Then we get a TrelloCard object back
    """
    api_mock = get_api()
    api_mock.cards.new.return_value = {'id': '12345'}
    card = TrelloCard.new('Test', 'Running a Test', good_config)
    assert api_mock.cards.new.called
    assert get_columns_mock.called
    assert isinstance(card, TrelloCard)
    assert card.report_id == '12345'


def test_get(get_api, get_columns_mock, good_config):
    """
    Given we have a report_id and a configuration
    When we call TrelloCard.get
    Then we get a TrelloCard object back
    """
    api_mock = get_api()
    api_mock.cards.get.return_value = {'idChecklists': ['12345'], 'id': '1234'}

    api_mock.checklists.get.return_value = {'checkItems': [{'name': 'a',
                                                            'id': '789'}],
                                            'name': 'TestList',
                                            'id': 'checklist_id'}

    card = TrelloCard.get('1234', good_config)
    assert api_mock.cards.get.called
    assert api_mock.checklists.get.called
    assert get_columns_mock.called
    assert isinstance(card, TrelloCard)
    assert card.report_id == '1234'


def test_update_decription(get_api, get_columns_mock):
    """
    Given we have a TrelloCard instance
    When we call update
    And the description kwarg is available
    Then the card_api update_desc method gets called
    """
    api_mock = get_api()
    api_mock.cards.get.return_value = {'idChecklists': ['12345']}
    api_mock.cards.update_desc.return_value = True

    api_mock.checklists.get.return_value = {'checkItems': [{'name': 'a',
                                                            'id': '1234'}],
                                            'name': 'TestList',
                                            'id': 'checklist_id'}

    card = get_instance(api_mock)
    card.update(description='New description')
    assert api_mock.cards.update_desc.called
    args, kwargs = api_mock.cards.update_desc.call_args
    assert args == ('card_id', 'New description')
    assert kwargs == {}


def test_update_checklist_complete_url_match(get_api):
    """
    Given we have a TrelloCard instance
    When we call update
    And the checklist kwarg is available with only one checklist item left
    And the url matches
    Then the missing checklist item is marked complete.
    """
    api_mock = get_api
    api_mock.cards.get.return_value = {'idChecklists': ['checklist_id'],
                                       'id': 'card_id'}
    api_mock.cards.check_checkItem.return_value = True
    api_mock.cards.move_checkItem.return_value = True

    checklist_ret = {'checkItems': [{'name': '[a](https://failing/a1)',
                                     'id': '1234',
                                     'state': 'incomplete'},
                                    {'name': '[b](https://failing/b1)',
                                     'id': '5678',
                                     'state': 'incomplete'}],
                     'name': 'TestList', 'id': 'checklist_id'}
    api_mock.checklists.get.return_value = checklist_ret

    card = get_instance(api_mock)
    card.update(checklist={'TestList': [{'name': 'a',
                                         'link': 'https://failing/a1'}]})
    assert api_mock.cards.get.called
    assert api_mock.checklists.get.called
    assert api_mock.cards.check_checkItem.called
    # Verify that only one checklist item was updated
    args, kwargs = api_mock.cards.check_checkItem.call_args
    assert args == ('card_id', '5678')
    assert kwargs == {}
    # Verify that 'a' was moved to the bottom of the list
    assert api_mock.cards.move_checkItem.called
    args2, kwargs2 = api_mock.cards.move_checkItem.call_args
    assert args2 == ('card_id', '5678', 'bottom')
    assert kwargs2 == {}


def test_update_checklist_url_no_match(get_api):
    """
    Given we have a TrelloCard instance
    When we call update
    And the checklist kwarg is available with only one checklist item left
    And the url does not match
    Then the missing checklist item is marked complete.
    """
    api_mock = get_api
    api_mock.cards.get.return_value = {'idChecklists': ['checklist_id'],
                                       'id': 'card_id'}
    api_mock.cards.rename_checkItem.return_value = True

    checklist_ret = {'checkItems': [{'name': '[a](https://failing/a1)',
                                     'id': '1234',
                                     'state': 'incomplete'}],
                     'name': 'TestList', 'id': 'checklist_id'}
    api_mock.checklists.get.return_value = checklist_ret

    card = get_instance(api_mock)
    card.update(checklist={'TestList': [{'name': 'a',
                                         'link': 'https://failing/a2'}]})
    assert api_mock.cards.get.called
    assert api_mock.checklists.get.called
    assert not api_mock.checklists.new_checkItem.called
    assert not api_mock.cards.uncheck_checkItem.called
    assert api_mock.cards.rename_checkItem.called
    args, kwargs = api_mock.cards.rename_checkItem.call_args
    assert args == ('card_id', '1234', '[a](https://failing/a2)')
    assert kwargs == {}


def test_update_checklist_no_url(get_api):
    """
    Given we have a TrelloCard instance
    When we call update
    And the checklist item's url is missing
    And the checklist kwarg is available with only one checklist item left
    Then the missing checklist item is marked complete.
    """
    api_mock = get_api
    api_mock.cards.get.return_value = {'idChecklists': ['checklist_id'],
                                       'id': 'card_id'}
    api_mock.cards.rename_checkItem.return_value = True

    checklist_ret = {'checkItems': [{'name': '[a]()',
                                     'id': '1234',
                                     'state': 'incomplete'}],
                     'name': 'TestList', 'id': 'checklist_id'}
    api_mock.checklists.get.return_value = checklist_ret

    card = get_instance(api_mock)
    card.update(checklist={'TestList': [{'name': 'a',
                                         'link': 'https://failing/a2'}]})
    assert api_mock.cards.get.called
    assert api_mock.checklists.get.called
    assert not api_mock.checklists.new_checkItem.called
    assert not api_mock.cards.uncheck_checkItem.called
    assert api_mock.cards.rename_checkItem.called
    args, kwargs = api_mock.cards.rename_checkItem.call_args
    assert args == ('card_id', '1234', '[a](https://failing/a2)')
    assert kwargs == {}


def test_update_checklist_incomplete(get_api):
    """
    Given we have a TrelloCard instance
    When we call update
    And the checklist kwarg is available with two items listed
    Then the added checklist item is marked incomplete.
    """
    api_mock = get_api
    api_mock.cards.get.return_value = {'idChecklists': ['checklist_id'],
                                       'id': 'card_id'}
    api_mock.cards.uncheck_checkItem.return_value = True
    api_mock.cards.check_checkItem.return_value = True
    api_mock.cards.move_checkItem.return_value = True

    checklist_ret = {'checkItems': [{'name': 'a',
                                     'id': '1234',
                                     'state': 'complete'},
                                    {'name': 'b',
                                     'id': '5678',
                                     'state': 'incomplete'}],
                     'name': 'TestList', 'id': 'checklist_id'}
    api_mock.checklists.get.return_value = checklist_ret

    card = get_instance(api_mock)
    card.update(checklist={'TestList': [{'name': 'a', 'link': 'url/a'},
                                        {'name': 'b', 'link': 'url/b'}]})
    assert api_mock.checklists.get.called
    assert api_mock.cards.uncheck_checkItem.called
    # Check to see if 'a' was unchecked
    args, kwargs = api_mock.cards.uncheck_checkItem.call_args
    assert args == ('card_id', '1234')
    assert kwargs == {}
    # Check to makes sure nothing else was marked complete.
    assert not api_mock.cards.check_checkItem.called
    # Check to make sure 'a' was moved to the top of the list
    assert api_mock.cards.move_checkItem.called
    args2, kwargs2 = api_mock.cards.move_checkItem.call_args
    assert args2 == ('card_id', '1234', 'top')
    assert kwargs2 == {}


def test_update_new_checklist(get_api):
    """
    Given we have a TrelloCard instance
    When we call update
    And we don't have an existing checklist
    Then a checklist and all of the items are added.
    """
    api_mock = get_api
    api_mock.cards.get.side_effect = [{'idChecklists': [], 'id': 'card_id'},
                                      {'idChecklists': ['checklist_id'],
                                       'id': 'card_id'},
                                      {'idChecklists': ['checklist_id'],
                                       'id': 'card_id'}]
    api_mock.cards.new_checklist.return_value = {'id': 'checklist_id'}

    checklist_ret = [{'name': 'TestList', 'id': 'checklist_id',
                      'checkItems': []},
                     {'checkItems': [{'name': '[a](url/a)',
                                      'id': '1234',
                                      'state': 'incomplete'},
                                     {'name': '[b](url/b)',
                                      'id': '5678',
                                      'state': 'incomplete'}],
                      'name': 'TestList', 'id': 'checklist_id'}]
    api_mock.checklists.get.side_effect = checklist_ret
    api_mock.checklists.new_checkItem.return_value = True

    card = get_instance(api_mock)
    card.update(checklist={'TestList': [{'name': 'a', 'link': 'url/a'},
                                        {'name': 'b', 'link': 'url/b'}]})

    api_mock.cards.new_checklist.assert_called_once()
    assert api_mock.checklists.get.call_count == 2
    assert api_mock.checklists.new_checkItem.call_count == 2
    call_list = api_mock.checklists.new_checkItem.call_args_list
    assert [call('checklist_id', '[a](url/a)'),
            call('checklist_id', '[b](url/b)')] == call_list


def test_close_empty(get_api):
    """
    Given we have a TrelloCard instance
    When we call close
    And the card does not have a checklist
    Then none of the checklist api calls are made.
    """
    api_mock = get_api
    api_mock.cards.get.return_value = {'idList': '123', 'id': 'card_id'}
    api_mock.cards.update_idList.return_value = True
    api_mock.cards.update_pos.return_value = True

    api_mock.checklists.get.return_value = {}

    card = get_instance(api_mock)
    card.close()
    assert not api_mock.cards.check_checkItem.called
    assert api_mock.cards.update_idList.called
    assert api_mock.cards.update_pos.called


def test_close_complete_items(get_api):
    """
    Given we have a TrelloCard instance
    When we call close
    And the card has a checklist
    Then the check_checkItem api is called for each item.
    """
    api_mock = get_api
    api_mock.cards.get.return_value = {'idList': '123', 'id': 'card_id',
                                       'idChecklists': ['checklist_id']}
    api_mock.cards.check_checkItem.return_value = True

    checklist_ret = {'checkItems': [{'name': 'a',
                                     'id': '1234',
                                     'state': 'incomplete'},
                                    {'name': 'b',
                                     'id': '5678',
                                     'state': 'incomplete'}],
                     'name': 'TestList', 'id': 'checklist_id'}
    api_mock.checklists.get.return_value = checklist_ret
    api_mock.cards.update_pos.return_value = True

    card = get_instance(api_mock)
    card.close()
    assert api_mock.cards.check_checkItem.called
    call_list = api_mock.cards.check_checkItem.call_args_list
    assert call_list == [call('card_id', '1234'), call('card_id', '5678')]
    assert api_mock.cards.update_idList.called
    assert api_mock.cards.update_pos.called
