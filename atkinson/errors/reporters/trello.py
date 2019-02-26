#! /usr/bin/env python
""" Trello Card error reporter """

from trollo import TrelloApi

from atkinson.config.manager import ConfigManager
from atkinson.errors.reporters import BaseReport


def get_trello_api():
    """
    Construct an interface to trello using the trollo api
    """
    conf = ConfigManager('trello.yml').config
    return TrelloApi(conf['api_key'], conf['token'])


def get_columns(api, config):
    """
    Get the columns for a trello board given a api handle and the id
    of the board.

    :param api: A trollo Boards api handle.
    :param dict config: The trello unique id for the board to fetch the data.
    :return: A tuple of column trello ids
    """
    for key in ['board_id', 'new_column', 'close_column']:
        if key not in config:
            raise KeyError(f"A required key '{key}' is missing in the config")

    column_data = {x['name']: x['id']
                   for x in api.get_list(config['board_id'])}
    return (column_data[config['new_column']],
            column_data[config['close_column']])


class TrelloCard(BaseReport):
    """ Trello error card base class"""
    def __init__(self, card_id, api, new_column, close_column):
        """
        Class constructor

        :param str card_id: The trello unique id for the card to work on
        :param api: A trollo TrelloApi instance
        :param str new_column: The trello unique id for a column to place
                               new cards
        :param str close_column: The trello unique id for a column to place
                                 completed cards
        """
        self.__card_id = card_id
        self.__card_data = None
        self.__checklist_items = {}
        self.__new_column = new_column
        self.__close_column = close_column
        self.__api = api

        # seed data from trello
        self._get_card_data()
        self._get_checklist_data()

    @classmethod
    def new(cls, title, description, config):
        """
        Create a TrelloCard instance

        :param str title: A title for the trello card
        :param str description: A description for the trello card
        :param dict config: A configuration dictionary
        :returns: A TrelloCard instance

        .. note::
            Required configuration keys and values
                * board_id The trello board unique id
                * new_column The name of the column where new cards are added
                * close_column The name of the column where closed/inactive
                  are moved.
        """

        api = get_trello_api()
        # Get the trello ids for our columns in the config
        new_column, close_column = get_columns(api.boards, config)
        card_id = api.cards.new(title, new_column, description)['id']
        return cls(card_id, api, new_column, close_column)

    @classmethod
    def get(cls, report_id, config):
        """
        Get a report object based on the report id.

        :param report_id: The id of the report to construct
        :type report_id: Trello unique id
        :return: A TrelloCard instance based on the report_id
        """
        api = get_trello_api()
        # Get the trello ids for our columns in the config
        new_column, close_column = get_columns(api.boards, config)
        return cls(report_id, api, new_column, close_column)

    def _get_card_data(self):
        """ Fetch the cards data from Trello """
        self.__card_data = self.__api.cards.get(self.__card_id)

    def _get_checklist_data(self):
        """ Fetch the checklist data from Trello """
        for checklist in self.__card_data.get('idChecklists', []):
            data = self.__api.checklists.get(checklist)
            check_data = {'id': data['id'], 'items': {}}
            for item in data['checkItems']:
                check_data['items'][item['name']] = item
            self.__checklist_items[data['name']] = check_data

    def _update_checklist(self, checklist_items):
        """ Check or uncheck checklist items """
        for checklist_name, list_items in checklist_items.items():
            current_list = self.__checklist_items.get(checklist_name)

            # If we don't have a checklist by that name them create a new one.
            if current_list is None:
                self.__api.cards.new_checklist(self.__card_id, checklist_name)
                # refresh the card and checklist data
                self._get_card_data()
                self._get_checklist_data()
                current_list = self.__checklist_items.get(checklist_name)

            # Process the items items
            on_card = {x for x in current_list['items']}
            sorted_items = set(list_items)
            checked = {x for x in current_list['items']
                       if current_list['items'][x]['state'] == 'complete'}

            # items to add
            for item in sorted(sorted_items - on_card):
                self.__api.checklists.new_checkItem(current_list['id'],
                                                    item)

            # items to check
            for item in sorted((on_card - checked) - sorted_items):
                item_id = current_list['items'][item]['id']
                self.__api.cards.check_checkItem(self.__card_id, item_id)

            for item in sorted(checked & sorted_items):
                item_id = current_list['items'][item]['id']
                self.__api.cards.uncheck_checkItem(self.__card_id, item_id)

    @property
    def report_id(self):
        return self.__card_id

    def update(self, **kwargs):
        """ Update the current report

        :param kwargs: A dictionary of report items to update
        """
        if 'description' in kwargs:
            self.__api.cards.update_desc(self.__card_id, kwargs['description'])

        if 'checklist' in kwargs:
            self._update_checklist(kwargs['checklist'])

        # refresh card information.
        self._get_card_data()
        self._get_checklist_data()

    def close(self):
        """ Close report """
        current_column = self.__card_data['idList']
        clear_checklist = {x: {} for x in self.__checklist_items}

        self._update_checklist(clear_checklist)

        if current_column != self.__close_column:
            self.__api.cards.update_idList(self.__card_id,
                                           self.__close_column)
