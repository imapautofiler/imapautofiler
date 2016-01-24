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
import unittest
import unittest.mock as mock

from imapautofiler import rules
from imapautofiler.tests import base

MESSAGE = """
From: Sender Name <sender@example.com>
Content-Type: multipart/alternative;
    boundary="Apple-Mail=_F10D7C06-52F7-4F60-BEC9-4D5F29A9BFE1"
Message-Id: <4FF56508-357B-4E73-82DE-458D3EEB2753@example.com>
Mime-Version: 1.0 (Mac OS X Mail 9.2 \(3112\))
X-Smtp-Server: AE35BF63-D70A-4AB0-9FAA-3F18EB9802A9
Subject: Re: reply to previous message
Date: Sat, 23 Jan 2016 16:19:10 -0500
X-Universally-Unique-Identifier: CC844EE1-C406-4ABA-9DA5-685759BBC15A
References: <33509d2c-e2a7-48c0-8bf3-73b4ba352b2f@example.com>
To: recipient1@example.com
CC: recipient2@example.com
In-Reply-To: <33509d2c-e2a7-48c0-8bf3-73b4ba352b2f@example.com>
""".lstrip()


class TestFactory(unittest.TestCase):

    def test_unknown(self):
        self.assertRaises(ValueError, rules.factory, {}, {})

    @mock.patch.object(rules, 'Or')
    def test_or(self, or_):
        rules.factory({'or': {}}, {})
        or_.assert_called_with({'or': {}}, {})

    @mock.patch.object(rules, 'Headers')
    def test_headers(self, headers):
        rules.factory({'headers': {}}, {})
        headers.assert_called_with({'headers': {}}, {})


class TestOr(base.TestCase):

    def setUp(self):
        super().setUp()
        self.msg = email.parser.Parser().parsestr(MESSAGE)

    def test_create_recursive(self):
        rule_def = {
            'or': {
                'rules': [
                    {'headers': [
                        {'name': 'to',
                         'substring': 'recipient1@example.com'}]},
                    {'headers': [
                        {'name': 'cc',
                         'substring': 'recipient1@example.com'}]}
                ],
            },
        }
        r = rules.Or(rule_def, {})
        self.assertIsInstance(r._sub_rules[0], rules.Headers)
        self.assertIsInstance(r._sub_rules[1], rules.Headers)
        self.assertEqual(len(r._sub_rules), 2)

    def test_check_pass_first(self):
        rule_def = {'or': {'rules': []}}
        r = rules.Or(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = True
        r._sub_rules.append(r1)
        r2 = mock.Mock()
        r2.check.return_value = False
        r._sub_rules.append(r2)
        self.assertTrue(r.check(self.msg))

    def test_check_short_circuit(self):
        rule_def = {'or': {'rules': []}}
        r = rules.Or(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = True
        r._sub_rules.append(r1)
        r2 = mock.Mock()
        r2.check.side_effect = AssertionError('r2 should not be called')
        r._sub_rules.append(r2)
        self.assertTrue(r.check(self.msg))

    def test_check_pass_second(self):
        rule_def = {'or': {'rules': []}}
        r = rules.Or(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = False
        r._sub_rules.append(r1)
        r2 = mock.Mock()
        r2.check.return_value = True
        r._sub_rules.append(r2)
        self.assertTrue(r.check(self.msg))

    def test_check_no_match(self):
        rule_def = {'or': {'rules': []}}
        r = rules.Or(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = False
        r._sub_rules.append(r1)
        r2 = mock.Mock()
        r2.check.return_value = False
        r._sub_rules.append(r2)
        self.assertFalse(r.check(self.msg))

    def test_check_no_subrules(self):
        rule_def = {'or': {'rules': []}}
        r = rules.Or(rule_def, {})
        self.assertFalse(r.check(self.msg))


class TestHeaderSubString(base.TestCase):

    def setUp(self):
        super().setUp()
        self.msg = email.parser.Parser().parsestr(MESSAGE)

    def test_match(self):
        rule_def = {
            'name': 'to',
            'substring': 'recipient1@example.com',
        }
        r = rules.HeaderSubString(rule_def, {})
        self.assertTrue(r.check(self.msg))

    def test_no_match(self):
        rule_def = {
            'name': 'to',
            'substring': 'not_the_recipient1@example.com',
        }
        r = rules.HeaderSubString(rule_def, {})
        self.assertFalse(r.check(self.msg))

    def test_no_such_header(self):
        rule_def = {
            'name': 'this_header_not_present',
            'substring': 'recipient1@example.com',
        }
        r = rules.HeaderSubString(rule_def, {})
        self.assertFalse(r.check(self.msg))


class TestHeaders(base.TestCase):

    def setUp(self):
        super().setUp()
        self.msg = email.parser.Parser().parsestr(MESSAGE)

    def test_create_recursive(self):
        rule_def = {
            'headers': [
                {'name': 'to',
                 'substring': 'recipient1@example.com'},
                {'name': 'cc',
                 'substring': 'recipient1@example.com'},
            ],
        }
        r = rules.Headers(rule_def, {})
        self.assertIsInstance(r._matchers[0], rules.HeaderSubString)
        self.assertIsInstance(r._matchers[1], rules.HeaderSubString)
        self.assertEqual(len(r._matchers), 2)

    def test_check_no_short_circuit(self):
        rule_def = {'or': {'rules': []}}
        r = rules.Headers(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = True
        r._matchers.append(r1)
        r2 = mock.Mock()
        r2.check.return_value = True
        r._matchers.append(r2)
        self.assertTrue(r.check(self.msg))
        r1.check.assert_called_once_with(self.msg)
        r2.check.assert_called_once_with(self.msg)

    def test_fail_one(self):
        rule_def = {'or': {'rules': []}}
        r = rules.Headers(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = False
        r._matchers.append(r1)
        r2 = mock.Mock()
        r2.check.return_value = True
        r._matchers.append(r2)
        self.assertFalse(r.check(self.msg))

    def test_check_no_match(self):
        rule_def = {'or': {'rules': []}}
        r = rules.Headers(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = False
        r._matchers.append(r1)
        r2 = mock.Mock()
        r2.check.return_value = False
        r._matchers.append(r2)
        self.assertFalse(r.check(self.msg))

    def test_check_no_matchers(self):
        rule_def = {'or': {'rules': []}}
        r = rules.Headers(rule_def, {})
        self.assertFalse(r.check(self.msg))
