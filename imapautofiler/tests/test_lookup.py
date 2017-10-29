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

from imapautofiler import lookup


class TestLookupTable(unittest.TestCase):

    def test_create(self):
        class A:
            NAME = 'a'

        class B(A):
            NAME = 'b'

        class C(B):
            NAME = 'c'

        expected = {
            'a': A,
            'b': B,
            'c': C,
        }
        actual = lookup.make_lookup_table(A, 'NAME')
        self.assertEqual(expected, actual)
