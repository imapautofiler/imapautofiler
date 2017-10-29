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

import email.parser
import logging
from email.header import Header
from email.message import Message

import fixtures
import testtools


def construct_message(headers):
    msg = Message()
    encoding = 'utf-8'

    for header, value in headers.items():
        msg[header] = Header(value, encoding)

    return msg.as_string()


MESSAGE = {
    'From': 'Sender Name <sender@example.com>',
    'Content-Type':
        'multipart/alternative; '
        'boundary="Apple-Mail=_F10D7C06-52F7-4F60-BEC9-4D5F29A9BFE1"',
    'Message-Id': '<4FF56508-357B-4E73-82DE-458D3EEB2753@example.com>',
    'Mime-Version': '1.0 (Mac OS X Mail 9.2 \(3112\))',
    'X-Smtp-Server': 'AE35BF63-D70A-4AB0-9FAA-3F18EB9802A9',
    'Subject': 'Re: reply to previous message',
    'Date': 'Sat, 23 Jan 2016 16:19:10 -0500',
    'X-Universally-Unique-Identifier': 'CC844EE1-C406-4ABA-9DA5-685759BBC15A',
    'References': '<33509d2c-e2a7-48c0-8bf3-73b4ba352b2f@example.com>',
    'To': 'recipient1@example.com',
    'CC': 'recipient2@example.com',
    'In-Reply-To': '<33509d2c-e2a7-48c0-8bf3-73b4ba352b2f@example.com>'

}

I18N_MESSAGE = MESSAGE.copy()
I18N_MESSAGE.update({
    'From': 'Иванов Иван <sender@example.com>',
    'To': 'Иванов Иван <recipient3@example.com>',
    'Subject': 'Re: ответ на предыдущее сообщение',
})


class TestCase(testtools.TestCase):
    _msg = None

    def setUp(self):
        super().setUp()
        # Capture logging
        self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))
        # Capturing printing
        stdout = self.useFixture(fixtures.StringStream('stdout')).stream
        self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))

    @property
    def msg(self):
        if self._msg is None:
            self._msg = email.parser.Parser().parsestr(
                construct_message(MESSAGE)
            )
        return self._msg

    @property
    def i18n_msg(self):
        if self._msg is None:
            self._msg = email.parser.Parser().parsestr(
                construct_message(I18N_MESSAGE)
            )
        return self._msg
