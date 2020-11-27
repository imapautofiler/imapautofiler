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

from imapautofiler.client import IMAPClient
from imapautofiler.config import get_config, tobool


CONFIG = """\
server:
    hostname: example.com
    port: 1234
    username: my-user@example.com
    password: super-secret
    ca_file: path/to/ca_file.pem
    check_hostname: yes
"""


class BaseConfigTest(unittest.TestCase):
    def setUp(self):
        m = self._get_mock_open(CONFIG)
        with mock.patch('imapautofiler.config.open', m):
            self.cfg = get_config('dummy')

    def _get_mock_open(self, data):
        return mock.mock_open(read_data=data)


class TestConfig(BaseConfigTest):
    def test_get_config_empty(self):
        m = self._get_mock_open('')
        with mock.patch('imapautofiler.config.open', m):
            self.assertEqual(get_config('dummy'), None)
            m.assert_called_once_with('dummy', 'r', encoding='utf-8')

    def test_config_server(self):
        self.assertTrue(isinstance(self.cfg, dict))
        self.assertTrue('server' in self.cfg)
        self.assertTrue(isinstance(self.cfg['server'], dict))
        self.assertEqual(self.cfg['server']['hostname'], 'example.com')
        self.assertEqual(self.cfg['server']['port'], 1234)
        self.assertEqual(self.cfg['server']['username'], 'my-user@example.com')
        self.assertEqual(self.cfg['server']['password'], 'super-secret')
        self.assertEqual(self.cfg['server']['ca_file'], 'path/to/ca_file.pem')
        self.assertTrue(self.cfg['server']['check_hostname'])

    def test_check_hostname(self):
        for val in ('y', 'yes', 't', 'true', 'on', 'enabled', '1'):
            with self.subTest(val=val):
                m = self._get_mock_open('server:\n check_hostname: %s' % val)
                with mock.patch('imapautofiler.config.open', m):
                    cfg = get_config('dummy')
                    self.assertTrue(tobool(cfg['server']['check_hostname']))

            with self.subTest(val='"%s"' % val):
                m = self._get_mock_open('server:\n check_hostname: "%s"' % val)
                with mock.patch('imapautofiler.config.open', m):
                    cfg = get_config('dummy')
                    self.assertTrue(tobool(cfg['server']['check_hostname']))

    def test_tobool(self):
        for val in (True, 1, '1', 'y', 'Y', 'yes', 'YES', 't', 'T', 'true',
                    'TRUE', 'on', 'ON', 'enabled', 'Enabled'):
            with self.subTest(val=val):
                self.assertTrue(tobool(val))

        for val in (False, 0, 'enable', 'disabled', 'off', 'no', 'one',
                    'false', 'f', 'FALSE', 'NO', 'never', ''):
            with self.subTest(val=val):
                self.assertFalse(tobool(val))


class TestServerConfig(BaseConfigTest):
    def test_imapclient_config(self):
        context = mock.MagicMock()
        with mock.patch('imapclient.create_default_context',
                        return_value=context):
            with mock.patch('imapclient.IMAPClient') as clientclass:
                conn = IMAPClient(self.cfg)
                clientclass.assert_called_once_with(
                    'example.com',
                    use_uid=True,
                    ssl=True,
                    port=1234,
                    ssl_context=context)
                conn._conn.login.assert_called_once_with('my-user@example.com',
                                                         'super-secret')
                self.assertEqual(context.cafile, 'path/to/ca_file.pem')
                self.assertTrue(context.check_hostname)
