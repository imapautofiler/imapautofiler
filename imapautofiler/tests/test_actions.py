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

import unittest
import unittest.mock as mock

import imapclient

from imapautofiler import actions
from imapautofiler.tests import base


class TestFactory(unittest.TestCase):

    def test_unknown(self):
        self.assertRaises(ValueError, actions.factory, {}, {})

    @mock.patch.object(actions, 'Move')
    def test_move(self, move):
        actions.factory({'name': 'move'}, {})
        move.assert_called_with({'name': 'move'}, {})

    @mock.patch.object(actions, 'Delete')
    def test_delete(self, delete):
        actions.factory({'name': 'delete'}, {})
        delete.assert_called_with({'name': 'delete'}, {})

    @mock.patch.object(actions, 'Trash')
    def test_trash(self, trash):
        actions.factory({'name': 'trash'}, {})
        trash.assert_called_with({'name': 'trash'}, {})


class TestMove(base.TestCase):

    def test_create(self):
        m = actions.Move(
            {'name': 'move', 'dest-mailbox': 'msg-goes-here'},
            {},
        )
        self.assertEqual('msg-goes-here', m._dest_mailbox)

    def test_invoke(self):
        m = actions.Move(
            {'name': 'move', 'dest-mailbox': 'msg-goes-here'},
            {},
        )
        conn = mock.Mock()
        m.invoke(conn, 'id-here', self.msg)
        conn.copy.assert_called_once_with(['id-here'], 'msg-goes-here')


class TestTrash(base.TestCase):

    def test_create(self):
        m = actions.Trash(
            {'name': 'trash'},
            {'trash-mailbox': 'to-the-trash'},
        )
        self.assertEqual('to-the-trash', m._dest_mailbox)

    def test_create_with_dest(self):
        m = actions.Trash(
            {'name': 'trash', 'dest-mailbox': 'local-override'},
            {'trash-mailbox': 'to-the-trash'},
        )
        self.assertEqual('local-override', m._dest_mailbox)

    def test_invoke(self):
        m = actions.Trash(
            {'name': 'trash'},
            {'trash-mailbox': 'to-the-trash'},
        )
        conn = mock.Mock()
        m.invoke(conn, 'id-here', self.msg)
        conn.copy.assert_called_once_with(['id-here'], 'to-the-trash')


class TestDelete(base.TestCase):

    def test_invoke(self):
        m = actions.Delete(
            {'name': 'delete'},
            {},
        )
        conn = mock.Mock()
        m.invoke(conn, 'id-here', self.msg)
        conn.add_flags.assert_called_once_with(
            ['id-here'], [imapclient.DELETED])
