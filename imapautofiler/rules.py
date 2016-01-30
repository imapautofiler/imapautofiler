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
import logging
import re


def factory(rule_data, cfg):
    """Create a rule processor.

    Using the rule type, instantiate a rule processor that can check
    the rule against a message.

    """
    if 'or' in rule_data:
        return Or(rule_data, cfg)
    if 'headers' in rule_data:
        return Headers(rule_data, cfg)
    if 'recipient' in rule_data:
        return Recipient(rule_data, cfg)
    raise ValueError('Unknown rule type {!r}'.format(rule_data))


class Rule(metaclass=abc.ABCMeta):
    "Base class"

    _log = logging.getLogger(__name__)

    def __init__(self, rule_data, cfg):
        self._log.debug('new %r', rule_data)
        self._data = rule_data
        self._cfg = cfg

    @abc.abstractmethod
    def check(self):
        raise NotImplementedError()

    def get_action(self):
        return self._data.get('action', {})


class Or(Rule):
    "True if any one of the sub-rules is true."

    _log = logging.getLogger('Or')

    def __init__(self, rule_data, cfg):
        super().__init__(rule_data, cfg)
        self._sub_rules = [
            factory(r, cfg)
            for r in rule_data['or'].get('rules', [])
        ]

    def check(self, message):
        if not self._sub_rules:
            self._log.debug('no sub-rules')
            return False
        return any(r.check(message) for r in self._sub_rules)


class Recipient(Or):
    "True if any recipient sub-rule matches."

    _log = logging.getLogger('Recipient')

    def __init__(self, rule_data, cfg):
        rules = []
        for header in ['to', 'cc']:
            header_data = {}
            header_data.update(rule_data['recipient'])
            header_data['name'] = header
            rules.append({'headers': [header_data]})
        rule_data['or'] = {
            'rules': rules,
        }
        super().__init__(rule_data, cfg)


class Headers(Rule):
    "True if all of the headers match."

    _log = logging.getLogger('Headers')

    def __init__(self, rule_data, cfg):
        super().__init__(rule_data, cfg)
        self._matchers = []
        for header in rule_data.get('headers', []):
            if 'substring' in header:
                self._matchers.append(HeaderSubString(header, cfg))
            elif 'regex' in header:
                self._matchers.append(HeaderRegex(header, cfg))
            else:
                raise ValueError('unknown header matcher {!r}'.format(header))

    def check(self, message):
        if not self._matchers:
            self._log.debug('no sub-rules')
            return False
        return all(m.check(message) for m in self._matchers)


class HeaderSubString(Rule):

    _log = logging.getLogger('HeaderSubString')

    def __init__(self, rule_data, cfg):
        super().__init__(rule_data, cfg)
        self._header_name = rule_data['name']
        self._substring = rule_data['substring'].lower()

    def check(self, message):
        header_value = message.get(self._header_name, '').lower()
        self._log.debug('%r in %r', self._substring, header_value)
        return (self._substring in header_value)


class HeaderRegex(Rule):

    _log = logging.getLogger('HeaderRegex')

    def __init__(self, rule_data, cfg):
        super().__init__(rule_data, cfg)
        self._header_name = rule_data['name']
        self._regex = re.compile(rule_data['regex'].lower())

    def check(self, message):
        header_value = message.get(self._header_name, '').lower()
        self._log.debug('%r in %r', self._regex.pattern, header_value)
        return bool(self._regex.search(header_value))
