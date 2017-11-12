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

from imapautofiler import secrets


class TestFixedPassword(unittest.TestCase):

    def test_get_password(self):
        self.assertEqual(
            mock.sentinel.Password,
            secrets.FixedPasswordSecret(mock.sentinel.Password).get_password()
        )


class TestInteractivePassword(unittest.TestCase):

    def test_returns_getpass(self):
        with mock.patch('getpass.getpass') as getpass:
            self.assertEqual(
                getpass.return_value,
                secrets.AskPassword(None, None).get_password()
            )


class TestKeyringPassword(unittest.TestCase):

    def setUp(self):
        self.fixture = secrets.KeyringPasswordSecret('hostname', 'username')
        patcher = mock.patch('getpass.getpass')
        self.getpass = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('keyring.get_password')
        self.get_password = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('keyring.set_password')
        self.set_password = patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_password_in_keychain(self):
        self.get_password.return_value = mock.sentinel.Password

        self.assertEqual(
            mock.sentinel.Password,
            self.fixture.get_password()
        )

    def test_get_password_missing_sets_password(self):
        self.get_password.side_effect = [None, mock.sentinel.Password]
        self.assertEqual(
            mock.sentinel.Password,
            self.fixture.get_password()
        )

        self.set_password.assert_called_once_with(
            'hostname', 'username', self.getpass.return_value
        )


class TestGetSecretFromConfig(unittest.TestCase):

    def configured(self, **server_args):
        server_args.setdefault('hostname', 'hostname')
        server_args.setdefault('username', 'username')
        return list(secrets.configure_providers({'server': server_args}))

    def test_configure_providers_has_fixed_when_config_has_password(self):
        self.assertIsInstance(
            self.configured(password='a password')[0],
            secrets.FixedPasswordSecret
        )

    def test_configure_providers_includes_keyring_with_keyring_enabled(self):
        ps = self.configured(use_keyring=True)
        self.assertTrue(
            any(isinstance(p, secrets.KeyringPasswordSecret) for p in ps)
        )

    def test_configure_providers_excludes_getpass_with_keyring_enabled(self):
        providers = self.configured(use_keyring=True)
        self.assertFalse(
            any(isinstance(p, secrets.AskPassword) for p in providers)
        )
