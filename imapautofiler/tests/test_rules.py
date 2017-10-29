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

from imapautofiler import rules
from imapautofiler.tests import base


class TestFactory(unittest.TestCase):

    def test_unnamed(self):
        self.assertRaises(ValueError, rules.factory, {}, {})

    def test_unknown(self):
        self.assertRaises(ValueError, rules.factory,
                          {'unknown-rule': {}}, {})

    def test_lookup(self):
        with mock.patch.object(rules, '_lookup_table', {}) as lt:
            lt['or'] = mock.Mock()
            rules.factory({'or': {}}, {})
            lt['or'].assert_called_with({'or': {}}, {})

    def test_known(self):
        expected = [
            'or',
            'and',
            'recipient',
            'headers',
            'header-exists',
            'is-mailing-list',
        ]
        expected.sort()
        self.assertEqual(
            expected,
            list(sorted(rules._lookup_table.keys())),
        )


class TestOr(base.TestCase):

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


class TestAnd(base.TestCase):

    def test_create_recursive(self):
        rule_def = {
            'and': {
                'rules': [
                    {'headers': [
                        {'name': 'to',
                         'substring': 'recipient1@example.com'}]},
                    {'headers': [
                        {'name': 'cc',
                         'substring': 'recipient2@example.com'}]}
                ],
            },
        }
        r = rules.And(rule_def, {})
        self.assertIsInstance(r._sub_rules[0], rules.Headers)
        self.assertIsInstance(r._sub_rules[1], rules.Headers)
        self.assertEqual(len(r._sub_rules), 2)

    def test_check_fail_one_1(self):
        rule_def = {'and': {'rules': []}}
        r = rules.And(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = True
        r._sub_rules.append(r1)
        r2 = mock.Mock()
        r2.check.return_value = False
        r._sub_rules.append(r2)
        self.assertFalse(r.check(self.msg))

    def test_check_fail_one_2(self):
        rule_def = {'and': {'rules': []}}
        r = rules.And(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = False
        r._sub_rules.append(r1)
        r2 = mock.Mock()
        r2.check.return_value = True
        r._sub_rules.append(r2)
        self.assertFalse(r.check(self.msg))

    def test_check_short_circuit(self):
        rule_def = {'and': {'rules': []}}
        r = rules.And(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = False
        r._sub_rules.append(r1)
        r2 = mock.Mock()
        r2.check.side_effect = AssertionError('r2 should not be called')
        r._sub_rules.append(r2)
        self.assertFalse(r.check(self.msg))

    def test_check_pass_second(self):
        rule_def = {'and': {'rules': []}}
        r = rules.And(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = True
        r._sub_rules.append(r1)
        r2 = mock.Mock()
        r2.check.return_value = True
        r._sub_rules.append(r2)
        self.assertTrue(r.check(self.msg))

    def test_check_no_match(self):
        rule_def = {'and': {'rules': []}}
        r = rules.And(rule_def, {})
        r1 = mock.Mock()
        r1.check.return_value = False
        r._sub_rules.append(r1)
        r2 = mock.Mock()
        r2.check.return_value = False
        r._sub_rules.append(r2)
        self.assertFalse(r.check(self.msg))

    def test_check_no_subrules(self):
        rule_def = {'and': {'rules': []}}
        r = rules.And(rule_def, {})
        self.assertFalse(r.check(self.msg))


class TestHeaderExactValue(base.TestCase):
    def test_match(self):
        rule_def = {
            'name': 'to',
            'value': 'recipient1@example.com',
        }
        r = rules.HeaderExactValue(rule_def, {})
        self.assertTrue(r.check(self.msg))

    def test_no_match(self):
        rule_def = {
            'name': 'to',
            'value': 'not_the_recipient1@example.com',
        }
        r = rules.HeaderExactValue(rule_def, {})
        self.assertFalse(r.check(self.msg))

    def test_no_such_header(self):
        rule_def = {
            'name': 'this_header_not_present',
            'value': 'recipient1@example.com',
        }
        r = rules.HeaderExactValue(rule_def, {})
        self.assertFalse(r.check(self.msg))

    def test_i18n_match(self):
        rule_def = {
            'name': 'subject',
            'value': 'Re: ответ на предыдущее сообщение',
        }
        r = rules.HeaderExactValue(rule_def, {})
        self.assertTrue(r.check(self.i18n_msg))

    def test_i18n_no_match(self):
        rule_def = {
            'name': 'subject',
            'value': 'Re: что-то другое',
        }
        r = rules.HeaderExactValue(rule_def, {})
        self.assertFalse(r.check(self.i18n_msg))

    def test_i18n_no_such_header(self):
        rule_def = {
            'name': 'this_header_not_present',
            'value': 'такого заголовка нет',
        }
        r = rules.HeaderExactValue(rule_def, {})
        self.assertFalse(r.check(self.i18n_msg))


class TestHeaderSubString(base.TestCase):

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

    def test_i18n_match(self):
        rule_def = {
            'name': 'subject',
            'substring': 'предыдущее',
        }
        r = rules.HeaderSubString(rule_def, {})
        self.assertTrue(r.check(self.i18n_msg))

    def test_i18n_no_match(self):
        rule_def = {
            'name': 'subject',
            'substring': 'что-то другое',
        }
        r = rules.HeaderSubString(rule_def, {})
        self.assertFalse(r.check(self.i18n_msg))

    def test_i18n_no_such_header(self):
        rule_def = {
            'name': 'this_header_not_present',
            'substring': 'такого заголовка нет',
        }
        r = rules.HeaderSubString(rule_def, {})
        self.assertFalse(r.check(self.i18n_msg))


class TestHeaderRegex(base.TestCase):

    def test_match(self):
        rule_def = {
            'name': 'to',
            'regex': 'recipient.*@example.com',
        }
        r = rules.HeaderRegex(rule_def, {})
        self.assertTrue(r.check(self.msg))

    def test_no_match(self):
        rule_def = {
            'name': 'to',
            'regex': 'not_the_recipient.*@example.com',
        }
        r = rules.HeaderRegex(rule_def, {})
        self.assertFalse(r.check(self.msg))

    def test_no_such_header(self):
        rule_def = {
            'name': 'this_header_not_present',
            'regex': 'not_the_recipient.*@example.com',
        }
        r = rules.HeaderRegex(rule_def, {})
        self.assertFalse(r.check(self.msg))

    def test_i18n_match(self):
        rule_def = {
            'name': 'subject',
            'regex': 'предыдущее',
        }
        r = rules.HeaderRegex(rule_def, {})
        self.assertTrue(r.check(self.i18n_msg))

    def test_i18n_no_match(self):
        rule_def = {
            'name': 'subject',
            'regex': 'что-то другое',
        }
        r = rules.HeaderRegex(rule_def, {})
        self.assertFalse(r.check(self.i18n_msg))

    def test_i18n_no_such_header(self):
        rule_def = {
            'name': 'this_header_not_present',
            'regex': 'такого заголовка нет',
        }
        r = rules.HeaderRegex(rule_def, {})
        self.assertFalse(r.check(self.i18n_msg))


class TestHeaderExists(base.TestCase):

    def test_exists(self):
        rule_def = {
            'name': 'references',
        }
        r = rules.HeaderExists(rule_def, {})
        self.assertTrue(r.check(self.msg))

    def test_exists_no_case(self):
        rule_def = {
            'name': 'REFERENCES',
        }
        r = rules.HeaderExists(rule_def, {})
        self.assertTrue(r.check(self.msg))

    def test_no_exists(self):
        rule_def = {
            'name': 'no-such-header',
        }
        r = rules.HeaderExists(rule_def, {})
        self.assertFalse(r.check(self.msg))


class TestIsMailingList(base.TestCase):

    def test_yes(self):
        rule_def = {}
        r = rules.IsMailingList(rule_def, {})
        self.msg['list-id'] = '<sphinx-dev.googlegroups.com>'
        self.assertTrue(r.check(self.msg))

    def test_no(self):
        rule_def = {}
        r = rules.IsMailingList(rule_def, {})
        self.assertFalse(r.check(self.msg))


class TestHeaders(base.TestCase):

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


class TestRecipient(base.TestCase):

    def test_create_recursive(self):
        rule_def = {
            'recipient': {'substring': 'recipient1@example.com'},
        }
        r = rules.Recipient(rule_def, {})
        self.assertEquals(
            {
                'recipient': {'substring': 'recipient1@example.com'},
                'or': {
                    'rules': [
                        {
                            'headers': [{
                                'name': 'to',
                                'substring': 'recipient1@example.com',
                            }],
                        },
                        {
                            'headers': [{
                                'name': 'cc',
                                'substring': 'recipient1@example.com',
                            }],
                        },
                    ],
                },
            },
            r._data,
        )
