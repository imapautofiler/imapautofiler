#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import abc
import logging
import re

from imapautofiler import i18n
from imapautofiler import lookup


class Action(metaclass=abc.ABCMeta):
    "Base class"

    _log = logging.getLogger(__name__)
    NAME = None

    def __init__(self, action_data, cfg):
        """Initialize the action.

        :param action_data: data describing the action
        :type action_data: dict
        :param cfg: full configuration data
        :type cfg: dict

        """
        self._data = action_data
        self._cfg = cfg
        self._log.debug('new: %r', action_data)

    @abc.abstractmethod
    def report(self, conn, mailbox_name, message_id, message):
        "Log a message explaining what action will be taken."

    @abc.abstractmethod
    def invoke(self, conn, mailbox_name, message_id, message):
        """Run the action on the message.

        :param conn: connection to mail server
        :type conn: imapautofiler.client.Client
        :param mailbox_name: name of the mailbox holding the message
        :type mailbox_name: str
        :param message_id: ID of the message to process
        :type message_id: str
        :param message: the message object to process
        :type message: email.message.Message

        """
        raise NotImplementedError()


class Move(Action):
    """Move the message to a different folder.

    The action is indicated with the name ``move``.

    The action data must contain a ``dest-mailbox`` entry with the
    name of the destination mailbox.

    """

    NAME = 'move' 
    _log = logging.getLogger(NAME)

    def __init__(self, action_data, cfg):
        super().__init__(action_data, cfg)
        self._dest_mailbox = self._data.get('dest-mailbox')

    def report(self, conn, src_mailbox, message_id, message):
        self._log.info(
            '%s (%s) to %s',
            message_id, i18n.get_header_value(message, 'subject'),
            self._dest_mailbox)

    def invoke(self, conn, src_mailbox, message_id, message):
        conn.move_message(
            src_mailbox,
            self._dest_mailbox,
            message_id,
            message,
        )


class Sort(Action):
    r"""Move the message based on parsing a destination from a header.

    The action is indicated with the name ``sort``.

    The action may contain a ``header`` entry to specify the name of
    the mail header to examine to find the destination. The default is
    to use the ``to`` header.

    The action data may contain a ``dest-mailbox-regex`` entry for
    parsing the header value to obtain the destination mailbox
    name. If the regex has one match group, that substring will be
    used. If the regex has more than one match group, the
    ``dest-mailbox-regex-group`` option must specify which group to
    use (0-based numerical index). The default pattern is
    ``([\w-+]+)@`` to match the first part of an email address.

    The action data must contain a ``dest-mailbox-base`` entry with
    the base name of the destination mailbox. The actual mailbox name
    will be constructed by appending the value extracted via
    ``dest-mailbox-regex`` to the ``dest-mailbox-base`` value. The
    ``dest-mailbox-base`` value should contain the mailbox separator
    character (usually ``.``) if the desired mailbox is a sub-folder
    of the name given.

    """

    # TODO(dhellmann): Extend this class to support named groups in
    # the regex.

    NAME = 'sort'
    _log = logging.getLogger(NAME)
    _default_header = 'to'
    _default_regex = r'([\w+-]+)@'

    def __init__(self, action_data, cfg):
        super().__init__(action_data, cfg)
        self._header = self._data.get('header', self._default_header)
        self._dest_mailbox_base = self._data.get('dest-mailbox-base')
        if not self._dest_mailbox_base:
            raise ValueError(
                'No dest-mailbox-base given for action {}'.format(
                    action_data)
            )
        self._dest_mailbox_regex = re.compile(self._data.get(
            'dest-mailbox-regex', self._default_regex))
        if not self._dest_mailbox_regex.groups:
            raise ValueError(
                'Regex {!r} has no group to select the mailbox '
                'name portion.'.format(self._dest_mailbox_regex.pattern)
            )
        if self._dest_mailbox_regex.groups > 1:
            if 'dest-mailbox-regex-group' not in action_data:
                raise ValueError(
                    'Regex {!r} has multiple groups and the '
                    'action data does not specify the '
                    'dest-mailbox-regex-group to use.'.format(
                        self._dest_mailbox_regex.pattern)
                )
        self._dest_mailbox_regex_group = action_data.get(
            'dest-mailbox-regex-group', 0)

    def _get_dest_mailbox(self, message_id, message):
        header_value = i18n.get_header_value(message, self._header)
        match = self._dest_mailbox_regex.search(header_value)
        if not match:
            raise ValueError(
                'Could not determine destination mailbox from '
                '{!r} header {!r} with regex {!r}'.format(
                    self._header, header_value, self._dest_mailbox_regex)
            )
        self._log.debug(
            '%s %r header %r matched regex %r with %r',
            message_id, self._header, header_value,
            self._dest_mailbox_regex.pattern,
            match.groups(),
        )
        self._log.debug(
            '%s using group %s',
            message_id,
            self._dest_mailbox_regex_group,
        )
        return '{}{}'.format(
            self._dest_mailbox_base,
            match.groups()[self._dest_mailbox_regex_group],
        )

    def report(self, conn, src_mailbox, message_id, message):
        dest_mailbox = self._get_dest_mailbox(message_id, message)
        self._log.info(
            '%s (%s) to %s',
            message_id, i18n.get_header_value(message, 'subject'),
            dest_mailbox)

    def invoke(self, conn, src_mailbox, message_id, message):
        dest_mailbox = self._get_dest_mailbox(message_id, message)
        conn.move_message(
            src_mailbox,
            dest_mailbox,
            message_id,
            message,
        )


class SortMailingList(Sort):
    r"""Move the message based on the mailing list id.

    The action is indicated with the name ``sort-mailing-list``.

    This action is equivalent to the ``sort`` action with header set
    to ``list-id`` and ``dest-mailbox-regex`` set to
    ``<?([^.]+)\..*>?``.

    """

    NAME = 'sort-mailing-list'
    _log = logging.getLogger(NAME)
    _default_header = 'list-id'
    _default_regex = r'<?([^.]+)\..*>?'


class Trash(Move):
    """Move the message to the trashcan.

    The action is indicated with the name ``trash``.

    The action expects the global configuration setting
    ``trash-mailbox``.

    """

    NAME = 'trash'
    _log = logging.getLogger(NAME)

    def __init__(self, action_data, cfg):
        super().__init__(action_data, cfg)
        if self._dest_mailbox is None:
            self._dest_mailbox = cfg.get('trash-mailbox')
        if self._dest_mailbox is None:
            raise ValueError('no "trash-mailbox" set in config')


class Delete(Action):
    """Delete the message immediately.

    The action is indicated with the name ``delete``.

    """

    NAME = 'delete'
    _log = logging.getLogger(NAME)

    def report(self, conn, mailbox_name, message_id, message):
        self._log.info('%s (%s)', message_id,
                       i18n.get_header_value(message, 'subject'))

    def invoke(self, conn, mailbox_name, message_id, message):
        conn.delete_message(
            mailbox_name,
            message_id,
            message,
        )


class Mark_as(Action):
    """
    Add flag to message
    """

    NAME = 'mark-as'
    _log = logging.getLogger(NAME)

    def __init__(self, action_data, cfg, flag):
        super().__init__(action_data, cfg)
        self.flag = flag

    def report(self, conn, mailbox_name, message_id, message):
        self._log.info()


    def invoke(self, conn, mailbox_name, message_id, message):
        conn.store(message_id,'+FLAG', '\\{}'.format(self.flag))

class Un_mark(Action):
    """
    Remove flag from message
    """

    NAME = 'un-mark'
    _log = logging.getLogger(NAME)

    def __init__(self, action_data, cfg, flag):
        super().__init__(action_data, cfg)
        self.flag = flag

    def report(self, conn, mailbox_name, message_id, message):
        self._log.info()


    def invoke(self, conn, mailbox_name, message_id, message):
        conn.store(message_id,'-FLAG', '\\{}'.format(self.flag))

_lookup_table = lookup.make_lookup_table(Action, 'NAME')


def factory(action_data, cfg):
    """Create an Action instance.

    :param action_data: portion of configuration describing the action
    :type action_data: dict
    :param cfg: full configuration data
    :type cfg: dict

    Using the action type, instantiate an action object that can
    process a message.

    """
    name = action_data.get('name')
    if name in _lookup_table:
        return _lookup_table[name](action_data, cfg)
    raise ValueError('unrecognized rule action {!r}'.format(action_data))
