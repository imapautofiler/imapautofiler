import logging
import getpass
import typing
from typing import Iterator

import keyring

LOG = logging.getLogger("imapautofiler.client")


class FixedPasswordSecret:
    def __init__(self, password: str) -> None:
        self.password = password

    def get_password(self) -> str:
        return self.password


class KeyringPasswordSecret:
    def __init__(self, hostname: str, username: str) -> None:
        self.hostname = hostname
        self.username = username

    def get_password(self) -> str | None:
        password = keyring.get_password(self.hostname, self.username)
        if not password:
            LOG.debug("No keyring password; getting one interactively")
            password = getpass.getpass(
                "Password for {} (will be stored in the system keyring):".format(
                    self.username
                )
            )
            keyring.set_password(self.hostname, self.username, password)

        return keyring.get_password(self.hostname, self.username)


class AskPassword:
    def __init__(self, hostname: str, username: str) -> None:
        self.hostname = hostname
        self.username = username

    def get_password(self) -> str:
        return getpass.getpass("Password for {}:".format(self.username))


def configure_providers(
    cfg: dict[str, typing.Any],
) -> Iterator[FixedPasswordSecret | KeyringPasswordSecret | AskPassword]:
    # First, we'll try for the in-config one. It's not recommended, but someone
    # may have set it.
    try:
        provider = FixedPasswordSecret(cfg["server"]["password"])
        LOG.debug("Password provider in config as cleartext")
    except KeyError:
        pass
    else:
        yield provider

    # Second, we will try for a keyring password if configured
    try:
        use_keyring = cfg["server"]["use_keyring"]
    except KeyError:
        use_keyring = False

    if use_keyring:
        LOG.debug("Password configured from keyring")
        yield KeyringPasswordSecret(
            hostname=cfg["server"]["hostname"],
            username=cfg["server"]["username"],
        )

    else:
        yield AskPassword(
            hostname=cfg["server"]["hostname"],
            username=cfg["server"]["username"],
        )


def get_password(cfg: dict[str, typing.Any]) -> str | None:
    for provider in configure_providers(cfg):
        password = provider.get_password()
        if password:
            return password
    return None
