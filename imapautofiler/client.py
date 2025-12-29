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
import email.message
import email.parser
import logging
import mailbox
import os
import ssl
import typing
from typing import Iterator, Generator, Sized

import imapclient

from . import secrets
from .config import tobool

LOG = logging.getLogger("imapautofiler.client")


class MailboxIterator(abc.ABC, Sized):
    """Abstract base class for mailbox message iterators.

    Implements Python's iterator protocol and provides message count.
    """

    def __init__(self, mailbox_name: str) -> None:
        self.mailbox_name = mailbox_name
        self._iterator: Iterator[tuple[str, email.message.Message]] | None = None

    @abc.abstractmethod
    def __len__(self) -> int:
        """Return the number of messages in the mailbox."""

    @abc.abstractmethod
    def _create_iterator(self) -> Iterator[tuple[str, email.message.Message]]:
        """Create a fresh iterator over mailbox messages."""

    def __iter__(self) -> Iterator[tuple[str, email.message.Message]]:
        """Return iterator over (message_id, message) tuples."""
        self._iterator = self._create_iterator()
        return self._iterator

    def __next__(self) -> tuple[str, email.message.Message]:
        """Get next message from iterator."""
        if self._iterator is None:
            raise StopIteration
        return next(self._iterator)


def open_connection(cfg: dict[str, typing.Any]) -> "Client":
    "Open a connection to the mail server."
    if "server" in cfg:
        return IMAPClient(cfg)
    if "maildir" in cfg:
        return MaildirClient(cfg)
    raise ValueError("Could not find connection information in config")


class Client(metaclass=abc.ABCMeta):
    def __init__(self, cfg: dict[str, typing.Any]) -> None:
        self._cfg: dict[str, typing.Any] = cfg

    @abc.abstractmethod
    def list_mailboxes(self) -> Iterator[str]:
        "Return a list of mailbox names."

    @abc.abstractmethod
    def mailbox_iterate(
        self, mailbox_name: str
    ) -> Iterator[tuple[str, email.message.Message]]:
        """Iterate over messages from the mailbox.

        Produces tuples of (message_id, message).
        """

    @abc.abstractmethod
    def get_mailbox_iterator(self, mailbox_name: str) -> MailboxIterator:
        """Return an iterator for the specified mailbox."""

    @abc.abstractmethod
    def set_flagged(
        self,
        src_mailbox: str,
        message_id: str,
        message: email.message.Message,
        is_flagged: bool,
    ) -> None:
        """Manage the "flagged" flag for the message.

        If is_flagged is True, ensure the message is
        flagged. Otherwise, ensure it is not.
        """

    @abc.abstractmethod
    def set_read(
        self,
        src_mailbox: str,
        message_id: str,
        message: email.message.Message,
        is_read: bool,
    ) -> None:
        """Manage the "read" flag for the message.

        If is_read is True, ensure the message is
        read. Otherwise, ensure it is not.
        """

    @abc.abstractmethod
    def copy_message(
        self,
        src_mailbox: str,
        dest_mailbox: str,
        message_id: str,
        message: email.message.Message,
    ) -> None:
        """Create a copy of the message in the destination mailbox."""

    def move_message(
        self,
        src_mailbox: str,
        dest_mailbox: str,
        message_id: str,
        message: email.message.Message,
    ) -> None:
        """Move the message from the source to the destination mailbox."""
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
    def delete_message(
        self,
        src_mailbox: str,
        message_id: str,
        message: email.message.Message,
    ) -> None:
        """Remove the message."""

    @abc.abstractmethod
    def expunge(self) -> None:
        "Flush any pending changes."

    @abc.abstractmethod
    def close(self) -> None:
        "Close the connection, flushing any pending changes."


class IMAPMailboxIterator(MailboxIterator):
    """Iterator for IMAP mailbox messages with lazy loading."""

    def __init__(self, conn: "imapclient.IMAPClient", mailbox_name: str) -> None:
        super().__init__(mailbox_name)
        self._conn = conn
        self._msg_ids: list[str] | None = None

    def _ensure_msg_ids(self) -> list[str]:
        """Ensure message IDs are loaded and return them."""
        if self._msg_ids is None:
            self._conn.select_folder(self.mailbox_name)
            search_result = self._conn.search(["ALL"])
            self._msg_ids = search_result if isinstance(search_result, list) else []
        return self._msg_ids

    def __len__(self) -> int:
        """Return the number of messages in the mailbox."""
        return len(self._ensure_msg_ids())

    def _create_iterator(self) -> Iterator[tuple[str, email.message.Message]]:
        """Create a fresh iterator that lazily loads messages."""
        msg_ids = self._ensure_msg_ids()

        for msg_id in msg_ids:
            email_parser = email.parser.BytesFeedParser()
            response = self._conn.fetch([msg_id], ["BODY.PEEK[HEADER]"])
            email_parser.feed(response[msg_id][b"BODY[HEADER]"])
            message = email_parser.close()
            yield (msg_id, message)


class IMAPClient(Client):
    def __init__(self, cfg: dict[str, typing.Any]) -> None:
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

        use_ssl: bool = True
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
        password: str | typing.Any | None = secrets.get_password(cfg)
        self._conn.login(username, password)
        self._mbox_names: set[str] | None = None

    def list_mailboxes(self) -> Iterator[str]:
        "Return a list of folder names."
        return (f[-1] for f in self._conn.list_folders())

    def mailbox_iterate(
        self, mailbox_name: str
    ) -> Iterator[tuple[str, email.message.Message]]:
        """Iterate over messages from the mailbox.

        DEPRECATED: Use get_mailbox_iterator() instead.
        """
        import warnings

        warnings.warn(
            "mailbox_iterate is deprecated, use get_mailbox_iterator instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return iter(self.get_mailbox_iterator(mailbox_name))

    def get_mailbox_iterator(self, mailbox_name: str) -> MailboxIterator:
        """Return an iterator for the specified mailbox."""
        return IMAPMailboxIterator(self._conn, mailbox_name)

    def _ensure_mailbox(self, name: str) -> None:
        if self._mbox_names is None:
            self._mbox_names = set(self.list_mailboxes())
        if name not in self._mbox_names:
            LOG.debug("creating mailbox %s", name)
            self._conn.create_folder(name)
            self._mbox_names.add(name)

    def set_flagged(
        self,
        src_mailbox: str,
        message_id: str,
        message: email.message.Message,
        is_flagged: bool,
    ) -> None:
        if is_flagged:
            self._conn.add_flags([message_id], [imapclient.FLAGGED])
        else:
            self._conn.remove_flags([message_id], [imapclient.FLAGGED])

    def set_read(
        self,
        src_mailbox: str,
        message_id: str,
        message: email.message.Message,
        is_read: bool,
    ) -> None:
        if is_read:
            self._conn.add_flags([message_id], [imapclient.SEEN])
        else:
            self._conn.remove_flags([message_id], [imapclient.SEEN])

    def copy_message(
        self,
        src_mailbox: str,
        dest_mailbox: str,
        message_id: str,
        message: email.message.Message,
    ) -> None:
        self._ensure_mailbox(dest_mailbox)
        self._conn.copy([message_id], dest_mailbox)

    def delete_message(
        self,
        src_mailbox: str,
        message_id: str,
        message: email.message.Message,
    ) -> None:
        self._conn.add_flags([message_id], [imapclient.DELETED])

    def expunge(self) -> None:
        self._conn.expunge()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass
        self._conn.logout()


class MaildirMailboxIterator(MailboxIterator):
    """Iterator for Maildir mailbox messages with eager loading."""

    def __init__(
        self,
        locked_maildir_fn: typing.Callable[
            [], contextlib.AbstractContextManager[mailbox.Maildir]
        ],
        mailbox_name: str,
    ) -> None:
        super().__init__(mailbox_name)
        self._locked_maildir_fn = locked_maildir_fn
        self._results: list[tuple[str, email.message.Message]] | None = None

    def _ensure_results(self) -> list[tuple[str, email.message.Message]]:
        """Ensure messages are loaded and return them."""
        if self._results is None:
            with self._locked_maildir_fn() as box:
                self._results = list(box.iteritems())
        return self._results

    def __len__(self) -> int:
        """Return the number of messages in the mailbox."""
        return len(self._ensure_results())

    def _create_iterator(self) -> Iterator[tuple[str, email.message.Message]]:
        """Create a fresh iterator over pre-loaded messages."""
        return iter(self._ensure_results())


class MaildirClient(Client):
    def __init__(self, cfg: dict[str, typing.Any]) -> None:
        super().__init__(cfg)
        self._root = os.path.expanduser(cfg["maildir"])
        LOG.debug("maildir: %s", self._root)
        self._mbox_names = None

    @contextlib.contextmanager
    def _locked(self, mailbox_name: str) -> Generator[mailbox.Maildir, None, None]:
        path = os.path.join(self._root, mailbox_name)
        LOG.debug("locking %s", path)
        box = mailbox.Maildir(path, create=True)
        box.lock()
        try:
            yield box
        finally:
            box.flush()
            box.close()

    def list_mailboxes(self) -> Iterator[str]:
        # NOTE: We don't use Maildir to open root because it is a
        # parent directory but not a maildir.
        return iter(sorted(os.listdir(self._root)))

    def mailbox_iterate(
        self, mailbox_name: str
    ) -> Iterator[tuple[str, email.message.Message]]:
        """Iterate over messages from the mailbox.

        DEPRECATED: Use get_mailbox_iterator() instead.
        """
        import warnings

        warnings.warn(
            "mailbox_iterate is deprecated, use get_mailbox_iterator instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return iter(self.get_mailbox_iterator(mailbox_name))

    def get_mailbox_iterator(self, mailbox_name: str) -> MailboxIterator:
        """Return an iterator for the specified mailbox."""
        return MaildirMailboxIterator(lambda: self._locked(mailbox_name), mailbox_name)

    def set_flagged(
        self,
        src_mailbox: str,
        message_id: str,
        message: email.message.Message,
        is_flagged: bool,
    ) -> None:
        with self._locked(src_mailbox) as box:
            message = box[message_id]
            if is_flagged:
                message.add_flag("F")
            else:
                message.remove_flag("F")
            box[message_id] = message

    def set_read(
        self,
        src_mailbox: str,
        message_id: str,
        message: email.message.Message,
        is_read: bool,
    ) -> None:
        with self._locked(src_mailbox) as box:
            message = box[message_id]
            if is_read:
                message.add_flag("R")
            else:
                message.remove_flag("R")
            box[message_id] = message

    def copy_message(
        self,
        src_mailbox: str,
        dest_mailbox: str,
        message_id: str,
        message: email.message.Message,
    ) -> None:
        with self._locked(dest_mailbox) as box:
            box.add(message)

    def delete_message(
        self,
        src_mailbox: str,
        message_id: str,
        message: email.message.Message,
    ) -> None:
        with self._locked(src_mailbox) as box:
            box.remove(message_id)

    def expunge(self) -> None:
        pass

    def close(self) -> None:
        pass
