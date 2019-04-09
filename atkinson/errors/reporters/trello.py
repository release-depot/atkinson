#! /usr/bin/env python
""" Trello Card error reporter """

import re

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
    Get the trello column ids for a trello board given a api handle and the id
    of the board.

    :param api: A trollo Boards api handle.
    :param dict config: The configuration data (see note below for details).
    :return: A tuple of column trello ids

    .. note::
        Required configuration keys and values
            * board_id The trello board unique id
            * new_column The name(str) of the column where new cards are added
              This would be the same name as seen in the Trello webui
            * close_column The name(str) of the column where closed/inactive
              are moved.
              This would be the same name as seen in the Trello webui
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
                * new_column The name(str) of the column where new cards are added
                  This would be the same name as seen in the Trello webui
                * close_column The name(str) of the column where closed/inactive
                  are moved.
                  This would be the same name as seen in the Trello webui
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

        :param str report_id: The id of the report to construct
        :type report_id: Trello unique id
        :param dict config: Reporter configuration dictionary
        :return: A TrelloCard instance based on the report_id

        .. note::
            Required configuration keys and values
                * board_id The trello board unique id
                * new_column The name(str) of the column where new cards are added
                  This would be the same name as seen in the Trello webui
                * close_column The name(str) of the column where closed/inactive
                  are moved.
                  This would be the same name as seen in the Trello webui
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
                name, link = self._markdown_to_tuple(item['name'])
                check_data['items'][name] = item
                check_data['items'][name]['link'] = link
            self.__checklist_items[data['name']] = check_data

    def _markdown_to_tuple(self, markdown):
        """ Extract a tuple for a markdown formatted link """
        if markdown.find('[') != -1:
            match = re.search(r'\[(.+)\]\((.*)\)', markdown)
            if match:
                return (match.group(1), match.group(2))
        else:
            return (markdown, '')

    def _dict_to_markdown(self, data):
        """ Format a dict into a markdown link """
        return f"[{data['name']}]({data.get('link', '')})"

    def _add_checklist(self, checklist_name):
        """ Add a new checklist """
        self.__api.cards.new_checklist(self.__card_id, checklist_name)

    def _update_checklist(self, checklist_items):
        """ Check or uncheck checklist items """
        # Makes sure we have the latest data from the card.
        self._get_card_data()
        self._get_checklist_data()

        for checklist_name, list_items in checklist_items.items():
            current_list = self.__checklist_items.get(checklist_name)
            incoming = {x['name']: x['link'] for x in list_items}

            # Process the items items
            on_card = {x for x in current_list['items']}
            sorted_items = set(list(incoming))
            checked = {x for x in current_list['items']
                       if current_list['items'][x]['state'] == 'complete'}

            to_move_bottom = [current_list['items'][x]['id'] for x in checked]

            # items to add
            for item in sorted(sorted_items - on_card):
                data = self._dict_to_markdown({'name': item,
                                               'link': incoming[item]})
                self.__api.checklists.new_checkItem(current_list['id'],
                                                    data)

            # items to check
            for item in sorted((on_card - checked) - sorted_items):
                item_id = current_list['items'][item]['id']
                self.__api.cards.check_checkItem(self.__card_id, item_id)
                if item_id not in to_move_bottom:
                    to_move_bottom.append(item_id)

            # items to uncheck and/or update
            for item in sorted(checked & sorted_items):
                work_item = current_list['items'][item]
                self.__api.cards.uncheck_checkItem(self.__card_id,
                                                   work_item['id'])
                self.__api.cards.move_checkItem(self.__card_id,
                                                work_item['id'], 'top')
                to_move_bottom.remove(work_item['id'])

            # Check for naming updates
            for item in sorted(on_card & sorted_items):
                work_item = current_list['items'][item]
                if work_item['link'] != incoming[item]:
                    new_name = self._dict_to_markdown({'name': item,
                                                       'link': incoming[item]})
                    self.__api.cards.rename_checkItem(self.__card_id,
                                                      work_item['id'],
                                                      new_name)

            for item in to_move_bottom:
                self.__api.cards.move_checkItem(self.__card_id,
                                                item, 'bottom')

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
            for checklist_name in kwargs['checklist']:
                if checklist_name not in self.__checklist_items:
                    self._add_checklist(checklist_name)

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
