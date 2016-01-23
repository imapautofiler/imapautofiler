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

import logging

import imapclient


def factory(action_data):
    "Create an Action instance."
    name = action_data.get('name')
    if name == 'move':
        return Move(action_data)
    if name == 'delete':
        return Delete(action_data)
    raise ValueError('unrecognized rule action {!r}'.format(action_data))


class Action:
    "Base class"

    _log = logging.getLogger(__name__)

    def __init__(self, action_data):
        self._data = action_data
        self._log.debug('new: %r', action_data)

    def invoke(self, conn, message_id, message):
        raise NotImplementedError()


class Move(Action):

    _log = logging.getLogger('Move')

    def __init__(self, action_data):
        super().__init__(action_data)
        self._dest_mailbox = self._data.get('dest-mailbox')

    def invoke(self, conn, message_id, message):
        self._log.info(
            '%s (%s) to %s',
            message_id, message['subject'],
            self._dest_mailbox)
        conn.copy([message_id], self._dest_mailbox)
        conn.add_flags([message_id], [imapclient.DELETED])


class Delete(Action):

    _log = logging.getLogger('Delete')

    def invoke(self, conn, message_id, message):
        self._log.info('%s (%s)', message_id, message['subject'])
        conn.add_flags([message_id], [imapclient.DELETED])
