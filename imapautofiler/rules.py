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

import abc
import email.message
import logging
import re
import typing
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from imapautofiler import i18n, lookup


class Rule(metaclass=abc.ABCMeta):
    "Base class"

    _log: logging.Logger = logging.getLogger(__name__)

    NAME: str | None = None

    def __init__(
        self, rule_data: dict[str, typing.Any], cfg: dict[str, typing.Any]
    ) -> None:
        """Initialize the rule.

        :param rule_data: data describing the rule
        :type rule_data: dict
        :param cfg: full configuration data
        :type cfg: dict

        """
        self._log.debug("rule %r", rule_data)
        self._data = rule_data
        self._cfg = cfg

    @abc.abstractmethod
    def check(self, message: email.message.Message) -> bool:
        """Test the rule on the message.

        :param conn: connection to IMAP server
        :type conn: imapclient.IMAPClient
        :param message: the message object to process
        :type message: email.message.Message

        """
        raise NotImplementedError()

    def get_action(self) -> dict[str, typing.Any]:
        return self._data.get("action", {})


class Or(Rule):
    """True if any one of the sub-rules is true.

    The rule data must contain a ``rules`` list with other rules
    specifications.

    Actions on the sub-rules are ignored.

    """

    NAME = "or"
    _log: logging.Logger = logging.getLogger(NAME)

    def __init__(
        self, rule_data: dict[str, typing.Any], cfg: dict[str, typing.Any]
    ) -> None:
        super().__init__(rule_data, cfg)
        self._sub_rules: list[Rule] = [
            factory(rule_data=r, cfg=cfg) for r in rule_data["or"].get("rules", [])
        ]

    def check(self, message: email.message.Message) -> bool:
        if not self._sub_rules:
            self._log.debug("no sub-rules")
            return False
        return any(r.check(message) for r in self._sub_rules)


class And(Rule):
    """True if all of the sub-rules are true.

    The rule data must contain a ``rules`` list with other rules
    specifications.

    Actions on the sub-rules are ignored.

    """

    NAME = "and"
    _log: logging.Logger = logging.getLogger(NAME)

    def __init__(
        self, rule_data: dict[str, typing.Any], cfg: dict[str, typing.Any]
    ) -> None:
        super().__init__(rule_data, cfg)
        self._sub_rules: list[Rule] = [
            factory(r, cfg) for r in rule_data["and"].get("rules", [])
        ]

    def check(self, message: email.message.Message) -> bool:
        if not self._sub_rules:
            self._log.debug("no sub-rules")
            return False
        return all(r.check(message) for r in self._sub_rules)


class Recipient(Or):
    """True if any recipient sub-rule matches.

    The rule data must contain a ``recipient`` mapping containing
    either a ``substring`` key mapped to a simple string or a
    ``regex`` key mapped to a regular expression.

    """

    NAME = "recipient"
    _log: logging.Logger = logging.getLogger(NAME)

    def __init__(
        self, rule_data: dict[str, typing.Any], cfg: dict[str, typing.Any]
    ) -> None:
        rules: list[dict[str, typing.Any]] = []
        for header in ["to", "cc"]:
            header_data: dict[str, typing.Any] = {}
            header_data.update(rule_data["recipient"])
            header_data["name"] = header
            rules.append({"headers": [header_data]})
        rule_data["or"] = {
            "rules": rules,
        }
        super().__init__(rule_data, cfg)


class Headers(Rule):
    """True if all of the headers match.

    The rule data must contain a ``headers`` list of mappings
    containing a ``name`` for the header itself and either a
    ``substring`` key mapped to a simple string or a ``regex`` key
    mapped to a regular expression to be matched against the value of
    the header.

    """

    NAME = "headers"
    _log: logging.Logger = logging.getLogger(NAME)

    def __init__(
        self, rule_data: dict[str, typing.Any], cfg: dict[str, typing.Any]
    ) -> None:
        super().__init__(rule_data, cfg)
        self._matchers: list[Rule] = []
        for header in rule_data.get("headers", []):
            if "substring" in header:
                self._matchers.append(HeaderSubString(header, cfg))
            elif "regex" in header:
                self._matchers.append(HeaderRegex(header, cfg))
            elif "value" in header:
                self._matchers.append(HeaderExactValue(header, cfg))
            else:
                raise ValueError("unknown header matcher {!r}".format(header))

    def check(self, message: email.message.Message) -> bool:
        if not self._matchers:
            self._log.debug("no sub-rules")
            return False
        return all(m.check(message) for m in self._matchers)


class _HeaderMatcher(Rule, metaclass=abc.ABCMeta):
    _log: logging.Logger = logging.getLogger("header")
    NAME: str | None = None  # matchers cannot be used directly

    def __init__(
        self, rule_data: dict[str, typing.Any], cfg: dict[str, typing.Any]
    ) -> None:
        super().__init__(rule_data, cfg)
        self._header_name = rule_data["name"]
        self._value = rule_data.get("value", "").lower()

    @abc.abstractmethod
    def _check_rule(self, header_value: str) -> bool:
        "run the rule-specific matching check"

    def check(self, message: email.message.Message) -> bool:
        header_value = i18n.get_header_value(message, self._header_name)
        return self._check_rule(header_value)


class HeaderExactValue(_HeaderMatcher):
    _log: logging.Logger = logging.getLogger("header-exact-value")

    def __init__(
        self, rule_data: dict[str, typing.Any], cfg: dict[str, typing.Any]
    ) -> None:
        super().__init__(rule_data, cfg)
        self._header_name = rule_data["name"]
        self._value = rule_data.get("value", "").lower()

    def _check_rule(self, header_value):
        self._log.debug("%r == %r", self._value, header_value)
        return self._value == header_value.lower()


class HeaderSubString(_HeaderMatcher):
    "Implements substring matching for headers."

    _log = logging.getLogger("header-substring")

    def __init__(self, rule_data, cfg):
        super().__init__(rule_data, cfg)
        self._value = rule_data.get("substring", "").lower()

    def _check_rule(self, header_value):
        self._log.debug("%r in %r", self._value, header_value)
        return self._value in header_value.lower()


class HeaderRegex(_HeaderMatcher):
    "Implements regular expression matching for headers."

    _log = logging.getLogger("header-regex")

    def __init__(self, rule_data, cfg):
        super().__init__(rule_data, cfg)
        self._value = rule_data.get("regex", "")
        self._regex = re.compile(self._value)

    def _check_rule(self, header_value):
        self._log.debug("%r matches %r", self._regex, header_value)
        return bool(self._regex.search(header_value))


class HeaderExists(Rule):
    "Looks for a message to have a given header."

    NAME = "header-exists"
    _log = logging.getLogger(NAME)

    def __init__(self, rule_data, cfg):
        super().__init__(rule_data, cfg)
        self._header_name = rule_data["name"]

    def check(self, message):
        self._log.debug("%r exists", self._header_name)
        return self._header_name in message


class IsMailingList(HeaderExists):
    "Looks for a message to have a given header."

    NAME = "is-mailing-list"
    _log = logging.getLogger(NAME)

    def __init__(self, rule_data, cfg):
        if "name" not in rule_data:
            rule_data["name"] = "list-id"
        super().__init__(rule_data, cfg)


class TimeLimit(Rule):
    """True if message is older than the specified 'age' measured
    in number of days."""

    NAME = "time-limit"
    _log = logging.getLogger(NAME)

    def __init__(
        self,
        rule_data,
        cfg,
    ):
        super().__init__(rule_data, cfg)
        self._age = rule_data["time-limit"]["age"]

    def check(self, message):
        header_value = i18n.get_header_value(message, "date")
        try:
            date = parsedate_to_datetime(header_value)
        except (TypeError, ValueError) as err:
            self._log.error(
                "Failed to check date for %r: %s",
                i18n.get_header_value(message, "subject"),
                err,
            )
            return False

        # RFC2822 dates ending with '-0000' create timezone naive datetimes
        # so we need to manually set their timezone so we can compare them
        # with TZ aware datetimes.
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        if self._age:
            time_limit = datetime.now(timezone.utc) - timedelta(days=self._age)
            if date <= time_limit:
                return True
            else:
                return 0


_lookup_table = lookup.make_lookup_table(Rule, "NAME")


def factory(rule_data, cfg):
    """Create a rule processor.

    :param rule_data: portion of configuration describing the rule
    :type rule_data: dict
    :param cfg: full configuration data
    :type cfg: dict

    Using the rule type, instantiate a rule processor that can check
    the rule against a message.

    """
    for key in rule_data:
        if key == "action":
            continue
        if key in _lookup_table:
            return _lookup_table[key](rule_data, cfg)
    raise ValueError("Unknown rule type {!r}".format(rule_data))
