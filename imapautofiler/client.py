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

"""Mail client API."""

import abc
import contextlib
import email.parser
import logging
import mailbox
import os
import ssl

import imapclient

from . import secrets
from .config import tobool

LOG = logging.getLogger("imapautofiler.client")


def open_connection(cfg):
    "Open a connection to the mail server."
    if "server" in cfg:
        return IMAPClient(cfg)
    if "maildir" in cfg:
        return MaildirClient(cfg)
    raise ValueError("Could not find connection information in config")


class Client(metaclass=abc.ABCMeta):
    def __init__(self, cfg):
        self._cfg = cfg

    @abc.abstractmethod
    def list_mailboxes(self):
        "Return a list of mailbox names."

    @abc.abstractmethod
    def mailbox_iterate(self, mailbox_name):
        """Iterate over messages from the mailbox.

        Produces tuples of (message_id, message).
        """

    @abc.abstractmethod
    def set_flagged(self, src_mailbox, message_id, message, is_flagged):
        """Manage the "flagged" flag for the message.

        If is_flagged is True, ensure the message is
        flagged. Otherwise, ensure it is not.

        :param src_mailbox: name of the source mailbox
        :type src_mailbox: str
        :param message_id: ID of the message to copy
        :type message_id: str
        :param is_flagged: whether to flag the message
        :type flags: bool

        """

    @abc.abstractmethod
    def set_read(self, src_mailbox, message_id, message, is_read):
        """Manage the "read" flag for the message.

        If is_read is True, ensure the message is
        read. Otherwise, ensure it is not.

        :param src_mailbox: name of the source mailbox
        :type src_mailbox: str
        :param message_id: ID of the message to copy
        :type message_id: str
        :param is_read: whether the message should be marked read
        :type flags: bool

        """

    @abc.abstractmethod
    def copy_message(self, src_mailbox, dest_mailbox, message_id, message):
        """Create a copy of the message in the destination mailbox.

        :param src_mailbox: name of the source mailbox
        :type src_mailbox: str
        :param dest_mailbox: name of the destination mailbox
        :type dest_mailbox: src
        :param message_id: ID of the message to copy
        :type message_id: str
        :param message: message instance
        :type message: email.message.Message

        """

    def move_message(self, src_mailbox, dest_mailbox, message_id, message):
        """Move the message from the source to the destination mailbox.

        :param src_mailbox: name of the source mailbox
        :type src_mailbox: str
        :param dest_mailbox: name of the destination mailbox
        :type dest_mailbox: src
        :param message_id: ID of the message to copy
        :type message_id: str
        :param message: message instance
        :type message: email.message.Message

        """
        self.copy_message(
            src_mailbox,
            dest_mailbox,
            message_id,
            message,
        )
        self.delete_message(
            src_mailbox,
            message_id,
            message,
        )

    @abc.abstractmethod
    def delete_message(self, src_mailbox, message_id, message):
        """Remove the message.

        :param src_mailbox: name of the source mailbox
        :type src_mailbox: str
        :param message_id: ID of the message to copy
        :type message_id: str
        :param message: message instance
        :type message: email.message.Message

        """

    @abc.abstractmethod
    def expunge(self):
        "Flush any pending changes."

    @abc.abstractmethod
    def close(self):
        "Close the connection, flushing any pending changes."


class IMAPClient(Client):
    def __init__(self, cfg):
        super().__init__(cfg)

        # Use default client behavior if ca_file not provided.
        if "ca_file" in cfg["server"]:
            context = ssl.create_default_context(
                cafile=cfg["server"]["ca_file"],
            )
        else:
            context = ssl.create_default_context()

        if "check_hostname" in cfg["server"]:
            context.verify_mode = ssl.CERT_REQUIRED
            context.check_hostname = tobool(cfg["server"]["check_hostname"])

        use_ssl = True
        if "ssl" in cfg["server"]:
            use_ssl = tobool(cfg["server"]["ssl"])

        self._conn = imapclient.IMAPClient(
            cfg["server"]["hostname"],
            use_uid=True,
            ssl=use_ssl,
            port=cfg["server"].get("port"),
            ssl_context=context,
        )
        username = cfg["server"]["username"]
        password = secrets.get_password(cfg)
        self._conn.login(username, password)
        self._mbox_names = None
        self.search = cfg['server'].get('search', 'ALL')

    def list_mailboxes(self):
        "Return a list of folder names."
        return (f[-1] for f in self._conn.list_folders())

    def mailbox_iterate(self, mailbox_name):
        self._conn.select_folder(mailbox_name)
        msg_ids = self._conn.search(self.search)
        for msg_id in msg_ids:
            email_parser = email.parser.BytesFeedParser()
            response = self._conn.fetch([msg_id], ["BODY.PEEK[HEADER]"])
            email_parser.feed(response[msg_id][b"BODY[HEADER]"])
            message = email_parser.close()
            yield (msg_id, message)

    def _ensure_mailbox(self, name):
        if self._mbox_names is None:
            self._mbox_names = set(self.list_mailboxes())
        if name not in self._mbox_names:
            LOG.debug("creating mailbox %s", name)
            self._conn.create_folder(name)
            self._mbox_names.add(name)

    def set_flagged(self, src_mailbox, message_id, message, is_flagged):
        if is_flagged:
            self._conn.add_flags([message_id], [imapclient.FLAGGED])
        else:
            self._conn.remove_flags([message_id], [imapclient.FLAGGED])

    def set_read(self, src_mailbox, message_id, message, is_read):
        if is_read:
            self._conn.add_flags([message_id], [imapclient.SEEN])
        else:
            self._conn.remove_flags([message_id], [imapclient.SEEN])

    def copy_message(self, src_mailbox, dest_mailbox, message_id, message):
        self._ensure_mailbox(dest_mailbox)
        self._conn.copy([message_id], dest_mailbox)

    def delete_message(self, src_mailbox, message_id, message):
        self._conn.add_flags([message_id], [imapclient.DELETED])

    def expunge(self):
        self._conn.expunge()

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass
        self._conn.logout()


class MaildirClient(Client):
    def __init__(self, cfg):
        super().__init__(cfg)
        self._root = os.path.expanduser(cfg["maildir"])
        LOG.debug("maildir: %s", self._root)
        self._mbox_names = None
        if 'search' in cfg['server']:
            LOG.warning('Config "search" not used with a Maildir')
            LOG.warning('All mails into the configured mailboxes will be parsed')

    @contextlib.contextmanager
    def _locked(self, mailbox_name):
        path = os.path.join(self._root, mailbox_name)
        LOG.debug("locking %s", path)
        box = mailbox.Maildir(path, create=True)
        box.lock()
        try:
            yield box
        finally:
            box.flush()
            box.close()

    def list_mailboxes(self):
        # NOTE: We don't use Maildir to open root because it is a
        # parent directory but not a maildir.
        return sorted(os.listdir(self._root))

    def mailbox_iterate(self, mailbox_name):
        with self._locked(mailbox_name) as box:
            results = list(box.iteritems())
        return results

    def set_flagged(self, src_mailbox, message_id, message, is_flagged):
        with self._locked(src_mailbox) as box:
            message = box[message_id]
            if is_flagged:
                message.add_flag("F")
            else:
                message.remove_flag("F")
            box[message_id] = message

    def set_read(self, src_mailbox, message_id, message, is_flagged):
        with self._locked(src_mailbox) as box:
            message = box[message_id]
            if is_flagged:
                message.add_flag("R")
            else:
                message.remove_flag("R")
            box[message_id] = message

    def copy_message(self, src_mailbox, dest_mailbox, message_id, message):
        with self._locked(dest_mailbox) as box:
            box.add(message)

    def delete_message(self, src_mailbox, message_id, message):
        with self._locked(src_mailbox) as box:
            box.remove(message_id)

    def expunge(self):
        pass

    def close(self):
        pass
