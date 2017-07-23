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

import email.utils
import mailbox
import os.path
import textwrap
import testtools

import fixtures

from imapautofiler import client


class MaildirFixture(fixtures.Fixture):

    def __init__(self, root, name):
        self._root = root
        self._path = os.path.join(root, name)
        self.name = name
        self.make_message(subject='init maildir')

    def make_message(
            self,
            subject='subject',
            from_addr='from@example.com',
            to_addr='to@example.com'):
        mbox = mailbox.Maildir(self._path)
        mbox.lock()
        try:
            msg = mailbox.MaildirMessage()
            msg.set_unixfrom('author Sat Jul 23 15:35:34 2017')
            msg['From'] = from_addr
            msg['To'] = to_addr
            msg['Subject'] = subject
            msg['Date'] = email.utils.formatdate()
            msg.set_payload(textwrap.dedent('''
            This is the body.
            There are 2 lines.
            '''))
            mbox.add(msg)
            mbox.flush()
        finally:
            mbox.unlock()
        return msg


class MaildirTest(testtools.TestCase):

    def setUp(self):
        super().setUp()
        self.tmpdir = self.useFixture(fixtures.TempDir()).path
        self.src_mbox = self.useFixture(
            MaildirFixture(self.tmpdir, 'source-mailbox')
        )
        # self.msg = self.src_mbox.make_message()
        self.dest_mbox = self.useFixture(
            MaildirFixture(self.tmpdir, 'destination-mailbox')
        )
        self.client = client.MaildirClient({'maildir': self.tmpdir})

    def test_list_mailboxes(self):
        expected = set(['destination-mailbox', 'source-mailbox'])
        actual = set(self.client.list_mailboxes())
        self.assertEqual(expected, actual)

    def test_mailbox_iterate(self):
        self.src_mbox.make_message(subject='added by test')
        expected = set(['init maildir', 'added by test'])
        actual = set(
            msg['subject']
            for msg_id, msg in self.client.mailbox_iterate(self.src_mbox.name)
        )
        self.assertEqual(expected, actual)

    def test_copy_message(self):
        self.src_mbox.make_message(subject='added by test')
        messages = list(self.client.mailbox_iterate(self.src_mbox.name))
        for msg_id, msg in messages:
            if msg['subject'] != 'added by test':
                continue
            self.client.copy_message(
                self.src_mbox.name,
                self.dest_mbox.name,
                msg_id,
                msg,
            )
        expected = set(['init maildir', 'added by test'])
        actual = set(
            msg['subject']
            for msg_id, msg in self.client.mailbox_iterate(self.dest_mbox.name)
        )
        self.assertEqual(expected, actual)

    def test_move_message(self):
        self.src_mbox.make_message(subject='added by test')
        messages = list(self.client.mailbox_iterate(self.src_mbox.name))
        for msg_id, msg in messages:
            if msg['subject'] != 'added by test':
                continue
            self.client.move_message(
                self.src_mbox.name,
                self.dest_mbox.name,
                msg_id,
                msg,
            )
        expected = set(['init maildir', 'added by test'])
        actual = set(
            msg['subject']
            for msg_id, msg in self.client.mailbox_iterate(self.dest_mbox.name)
        )
        self.assertEqual(expected, actual)
        # No longer appears in source maildir
        expected = set(['init maildir'])
        actual = set(
            msg['subject']
            for msg_id, msg in self.client.mailbox_iterate(self.src_mbox.name)
        )
        self.assertEqual(expected, actual)
