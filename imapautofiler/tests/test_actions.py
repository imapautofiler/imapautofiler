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

from imapautofiler import actions
from imapautofiler.tests import base
from imapautofiler.tests.base import pytest_generate_tests  # noqa


class TestRegisteredFactories(object):
    _names = [
        "move",
        "sort",
        "sort-mailing-list",
        "trash",
        "delete",
        "flag",
        "unflag",
    ]
    scenarios = [(name, {"name": name}) for name in _names]

    def test_known(self, name):
        assert name in actions._lookup_table


class TestFactory(unittest.TestCase):
    def test_unnamed(self):
        self.assertRaises(ValueError, actions.factory, {}, {})

    def test_unknown(self):
        self.assertRaises(ValueError, actions.factory, {"name": "unknown-action"}, {})

    def test_lookup(self):
        with mock.patch.object(actions, "_lookup_table", {}) as lt:
            lt["move"] = mock.Mock()
            actions.factory({"name": "move"}, {})
            lt["move"].assert_called_with({"name": "move"}, {})


class TestMove(base.TestCase):
    def test_static_mailbox_name(self):
        m = actions.Move(
            {"name": "move", "dest-mailbox": "msg-goes-here"},
            {},
        )
        self.assertEqual(
            "msg-goes-here",
            m._get_dest_mailbox("id-here", self.without_offset_msg),
        )

    def test_parameterized_mailbox_name(self):
        m = actions.Move(
            {"name": "move", "dest-mailbox": "archive.{{ date.year }}"},
            {},
        )
        dest_mailbox = m._get_dest_mailbox(
            message_id="id-here",
            message=self.without_offset_msg,
        )
        self.assertEqual(
            "archive.2000",
            dest_mailbox,
        )

    def test_invoke(self):
        m = actions.Move(
            {"name": "move", "dest-mailbox": "msg-goes-here"},
            {},
        )
        conn = mock.Mock()
        m.invoke(
            conn,
            mailbox_name="src-mailbox",
            message_id="id-here",
            message=self.msg,
        )
        conn.move_message.assert_called_once_with(
            src_mailbox="src-mailbox",
            dest_mailbox="msg-goes-here",
            message_id="id-here",
            message=self.msg,
        )


class TestSort(base.TestCase):
    def test_create(self):
        m = actions.Sort(
            {"name": "sort", "dest-mailbox-base": "lists-go-under-here."},
            {},
        )
        self.assertEqual("lists-go-under-here.", m._dest_mailbox_base)
        self.assertEqual(m._default_regex, m._dest_mailbox_regex.pattern)

    def test_create_missing_base(self):
        self.assertRaises(
            ValueError,
            actions.Sort,
            {"name": "sort"},
            {},
        )

    def test_create_with_regex(self):
        m = actions.Sort(
            {
                "name": "sort",
                "dest-mailbox-base": "lists-go-under-here.",
                "dest-mailbox-regex": ":(.*):",
            },
            {},
        )
        self.assertEqual("lists-go-under-here.", m._dest_mailbox_base)
        self.assertEqual(":(.*):", m._dest_mailbox_regex.pattern)

    def test_create_bad_regex(self):
        self.assertRaises(
            ValueError,
            actions.Sort,
            {
                "name": "sort",
                "dest-mailbox-base": "lists-go-under-here.",
                "dest-mailbox-regex": ":.*:",
            },
            {},
        )

    def test_create_with_multi_group_regex(self):
        m = actions.Sort(
            {
                "name": "sort",
                "dest-mailbox-base": "lists-go-under-here.",
                "dest-mailbox-regex": ":(.*):(.*):",
                "dest-mailbox-regex-group": 1,
            },
            {},
        )
        self.assertEqual(1, m._dest_mailbox_regex_group)

    def test_get_dest_mailbox_default(self):
        m = actions.Sort(
            {"name": "sort", "dest-mailbox-base": "lists-go-under-here."},
            {},
        )
        dest = m._get_dest_mailbox("id-here", self.msg)
        self.assertEqual(
            "lists-go-under-here.recipient1",
            dest,
        )

    def test_get_dest_mailbox_i18n(self):
        m = actions.Sort(
            {"name": "sort", "dest-mailbox-base": "lists-go-under-here."},
            {},
        )
        dest = m._get_dest_mailbox("id-here", self.i18n_msg)
        self.assertEqual(
            "lists-go-under-here.recipient3",
            dest,
        )

    def test_get_dest_mailbox_regex(self):
        m = actions.Sort(
            {
                "name": "sort",
                "dest-mailbox-base": "lists-go-under-here.",
                "dest-mailbox-regex": r"(.*)",
            },
            {},
        )
        dest = m._get_dest_mailbox("id-here", self.msg)
        self.assertEqual(
            "lists-go-under-here.recipient1@example.com",
            dest,
        )

    def test_get_dest_mailbox_template(self):
        m = actions.Sort(
            {
                "name": "sort",
                "dest-mailbox-base": "lists-go-under-here.{{ date.year }}.",
                "dest-mailbox-regex": r"(.*)",
            },
            {},
        )
        dest = m._get_dest_mailbox(
            message_id="id-here",
            message=self.without_offset_msg,
        )
        self.assertEqual(
            "lists-go-under-here.2000.recipient1@example.com",
            dest,
        )

    def test_invoke(self):
        m = actions.Sort(
            {"name": "sort", "dest-mailbox-base": "lists-go-under-here."},
            {},
        )
        conn = mock.Mock()
        m.invoke(
            conn,
            mailbox_name="src-mailbox",
            message_id="id-here",
            message=self.msg,
        )
        conn.move_message.assert_called_once_with(
            src_mailbox="src-mailbox",
            dest_mailbox="lists-go-under-here.recipient1",
            message_id="id-here",
            message=self.msg,
        )


class TestSortMailingList(base.TestCase):
    def test_create(self):
        m = actions.SortMailingList(
            {"name": "sort-mailing-list", "dest-mailbox-base": "lists-go-under-here."},
            {},
        )
        self.assertEqual("lists-go-under-here.", m._dest_mailbox_base)
        self.assertEqual(m._default_regex, m._dest_mailbox_regex.pattern)

    def test_create_missing_base(self):
        self.assertRaises(
            ValueError,
            actions.SortMailingList,
            {"name": "sort-mailing-list"},
            {},
        )

    def test_create_with_regex(self):
        m = actions.SortMailingList(
            {
                "name": "sort-mailing-list",
                "dest-mailbox-base": "lists-go-under-here.",
                "dest-mailbox-regex": ":(.*):",
            },
            {},
        )
        self.assertEqual("lists-go-under-here.", m._dest_mailbox_base)
        self.assertEqual(":(.*):", m._dest_mailbox_regex.pattern)

    def test_create_bad_regex(self):
        self.assertRaises(
            ValueError,
            actions.SortMailingList,
            {
                "name": "sort-mailing-list",
                "dest-mailbox-base": "lists-go-under-here.",
                "dest-mailbox-regex": ":.*:",
            },
            {},
        )

    def test_create_with_multi_group_regex(self):
        m = actions.SortMailingList(
            {
                "name": "sort-mailing-list",
                "dest-mailbox-base": "lists-go-under-here.",
                "dest-mailbox-regex": ":(.*):(.*):",
                "dest-mailbox-regex-group": 2,
            },
            {},
        )
        self.assertEqual(2, m._dest_mailbox_regex_group)

    def test_get_dest_mailbox_default(self):
        m = actions.SortMailingList(
            {"name": "sort-mailing-list", "dest-mailbox-base": "lists-go-under-here."},
            {},
        )
        self.msg["list-id"] = "<sphinx-dev.googlegroups.com>"
        dest = m._get_dest_mailbox("id-here", self.msg)
        self.assertEqual(
            "lists-go-under-here.sphinx-dev",
            dest,
        )

    def test_get_dest_mailbox_regex(self):
        m = actions.SortMailingList(
            {
                "name": "sort-mailing-list",
                "dest-mailbox-base": "lists-go-under-here.",
                "dest-mailbox-regex": r"<(.*)>",
            },
            {},
        )
        self.msg["list-id"] = "<sphinx-dev.googlegroups.com>"
        dest = m._get_dest_mailbox("id-here", self.msg)
        self.assertEqual(
            "lists-go-under-here.sphinx-dev.googlegroups.com",
            dest,
        )

    def test_invoke(self):
        m = actions.SortMailingList(
            {
                "name": "sort-mailing-list",
                "dest-mailbox-base": "lists-go-under-here.",
                "dest-mailbox-regex": r"<(.*)>",
            },
            {},
        )
        self.msg["list-id"] = "<sphinx-dev.googlegroups.com>"
        conn = mock.Mock()
        m.invoke(
            conn, mailbox_name="src-mailbox", message_id="id-here", message=self.msg
        )
        conn.move_message.assert_called_once_with(
            src_mailbox="src-mailbox",
            dest_mailbox="lists-go-under-here.sphinx-dev.googlegroups.com",
            message_id="id-here",
            message=self.msg,
        )


class TestSortByYear(base.TestCase):
    def test_create(self):
        m = actions.SortByYear(
            {"name": "sort-by-year", "dest-mailbox-base": "archive-under-here/"},
            {},
        )
        self.assertEqual("archive-under-here/", m._dest_mailbox_base)
        self.assertEqual(m._default_regex, m._dest_mailbox_regex.pattern)

    def test_invoke(self):
        m = actions.SortByYear(
            {
                "name": "sort-by-year",
                "dest-mailbox-base": "archive-under-here/",
            },
            {},
        )
        del self.msg["date"]
        self.msg["date"] = "Thu, 28 Dec 2023 13:47:53 -0600"
        conn = mock.Mock()
        m.invoke(
            conn, mailbox_name="src-mailbox", message_id="id-here", message=self.msg
        )
        conn.move_message.assert_called_once_with(
            src_mailbox="src-mailbox",
            dest_mailbox="archive-under-here/2023",
            message_id="id-here",
            message=self.msg,
        )

    def test_invalid_date(self):
        m = actions.SortByYear(
            {
                "name": "sort-by-year",
                "dest-mailbox-base": "archive-under-here/",
            },
            {},
        )
        del self.msg["date"]
        self.msg["date"] = "there is no date in this string"
        conn = mock.Mock()
        m.invoke(
            conn,
            mailbox_name="src-mailbox",
            message_id="id-here",
            message=self.msg,
        )
        conn.move_message.assert_called_once_with(
            src_mailbox="src-mailbox",
            dest_mailbox="archive-under-here/unparsable-date",
            message_id="id-here",
            message=self.msg,
        )

    def test_no_date_header(self):
        m = actions.SortByYear(
            {
                "name": "sort-by-year",
                "dest-mailbox-base": "archive-under-here/",
            },
            {},
        )
        del self.msg["date"]
        conn = mock.Mock()
        m.invoke(
            conn,
            mailbox_name="src-mailbox",
            message_id="id-here",
            message=self.msg,
        )
        conn.move_message.assert_called_once_with(
            src_mailbox="src-mailbox",
            dest_mailbox="archive-under-here/unparsable-date",
            message_id="id-here",
            message=self.msg,
        )

    def test_empty_date_header(self):
        m = actions.SortByYear(
            {
                "name": "sort-by-year",
                "dest-mailbox-base": "archive-under-here/",
            },
            {},
        )
        del self.msg["date"]
        self.msg["date"] = ""
        conn = mock.Mock()
        m.invoke(
            conn,
            mailbox_name="src-mailbox",
            message_id="id-here",
            message=self.msg,
        )
        conn.move_message.assert_called_once_with(
            src_mailbox="src-mailbox",
            dest_mailbox="archive-under-here/unparsable-date",
            message_id="id-here",
            message=self.msg,
        )


class TestTrash(base.TestCase):
    def test_create(self):
        m = actions.Trash(
            {"name": "trash"},
            {"trash-mailbox": "to-the-trash"},
        )
        self.assertEqual("to-the-trash", m._dest_mailbox)

    def test_create_with_dest(self):
        m = actions.Trash(
            {"name": "trash", "dest-mailbox": "local-override"},
            {"trash-mailbox": "to-the-trash"},
        )
        self.assertEqual("local-override", m._dest_mailbox)

    def test_invoke(self):
        m = actions.Trash(
            {"name": "trash"},
            {"trash-mailbox": "to-the-trash"},
        )
        conn = mock.Mock()
        m.invoke(
            conn,
            mailbox_name="src-mailbox",
            message_id="id-here",
            message=self.msg,
        )
        conn.move_message.assert_called_once_with(
            src_mailbox="src-mailbox",
            dest_mailbox="to-the-trash",
            message_id="id-here",
            message=self.msg,
        )


class TestDelete(base.TestCase):
    def test_invoke(self):
        m = actions.Delete(
            {"name": "delete"},
            {},
        )
        conn = mock.Mock()
        m.invoke(conn, "src-mailbox", "id-here", self.msg)
        conn.delete_message.assert_called_once_with("src-mailbox", "id-here", self.msg)


class TestFlag(base.TestCase):
    def test_flag(self):
        m = actions.Flag(
            {"name": "flag"},
            {},
        )
        conn = mock.Mock()
        m.invoke(conn, "src-mailbox", "id-here", self.msg)
        conn.set_flagged.assert_called_once_with(
            "src-mailbox", "id-here", self.msg, True
        )

    def test_unflag(self):
        m = actions.Unflag(
            {"name": "unflag"},
            {},
        )
        conn = mock.Mock()
        m.invoke(conn, "src-mailbox", "id-here", self.msg)
        conn.set_flagged.assert_called_once_with(
            "src-mailbox", "id-here", self.msg, False
        )


class TestMarkRead(base.TestCase):
    def test_mark_read(self):
        m = actions.MarkRead(
            {"name": "mark_read"},
            {},
        )
        conn = mock.Mock()
        m.invoke(conn, "src-mailbox", "id-here", self.msg)
        conn.set_read.assert_called_once_with("src-mailbox", "id-here", self.msg, True)

    def test_mark_unread(self):
        m = actions.MarkUnread(
            {"name": "mark_unread"},
            {},
        )
        conn = mock.Mock()
        m.invoke(conn, "src-mailbox", "id-here", self.msg)
        conn.set_read.assert_called_once_with("src-mailbox", "id-here", self.msg, False)
