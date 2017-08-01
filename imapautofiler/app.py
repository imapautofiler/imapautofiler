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

"""
"""

import argparse
import imaplib
import logging
import sys

from imapautofiler import actions
from imapautofiler import client
from imapautofiler import config
from imapautofiler import rules

LOG = logging.getLogger('imapautofiler')


def list_mailboxes(cfg, debug, conn):
    """Print a list of the mailboxes.

    :param cfg: full configuration
    :type cfg: dict
    :param debug: flag to control debug output
    :type debug: bool
    :param conn: IMAP server onnection
    :type conn: imapautofiler.client.Client

    Used by the ``--list-mailboxes`` switch.

    """
    for f in conn.list_mailboxes():
        print(f)


def process_rules(cfg, debug, conn):
    """Run the rules from the configuration file.

    :param cfg: full configuration
    :type cfg: dict
    :param debug: flag to control debug output
    :type debug: bool
    :param conn: IMAP server onnection
    :type conn: imapautofiler.client.Client

    """
    num_messages = 0
    num_processed = 0
    num_errors = 0

    for mailbox in cfg['mailboxes']:
        mailbox_name = mailbox['name']

        mailbox_rules = [
            rules.factory(r, cfg)
            for r in mailbox['rules']
        ]

        for (msg_id, message) in conn.mailbox_iterate(mailbox_name):
            num_messages += 1
            if debug:
                print(message.as_string().rstrip())
            else:
                LOG.debug('message %s: %s', msg_id, message['subject'])

            for rule in mailbox_rules:
                if rule.check(message):
                    action = actions.factory(rule.get_action(), cfg)
                    try:
                        action.invoke(conn, mailbox_name, msg_id, message)
                    except Exception as err:
                        LOG.error('failed to %s "%s": %s',
                                  action.__class__.__name__.lower(),
                                  message['subject'], err)
                        num_errors += 1
                    else:
                        num_processed += 1
                    # At this point we've processed the message
                    # based on one rule, so there is no need to
                    # look at the other rules.
                    break
                else:
                    LOG.debug('no rules match')

            # break

        # Remove messages that we just moved.
        conn.expunge()
    LOG.info('encountered %s messages, processed %s',
             num_messages, num_processed)
    if num_errors:
        LOG.info('encountered %d errors', num_errors)
    return


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help='report more details about what is happening',
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help='turn on imaplib debugging output',
    )
    parser.add_argument(
        '-c', '--config-file',
        default='~/.imapautofiler.yml',
    )
    parser.add_argument(
        '--list-mailboxes',
        default=False,
        action='store_true',
        help='instead of processing rules, print a list of mailboxes',
    )
    args = parser.parse_args()

    if args.debug:
        imaplib.Debug = 4

    if args.verbose or args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(name)s: %(message)s',
    )
    logging.debug('starting')

    try:
        cfg = config.get_config(args.config_file)
        conn = client.open_connection(cfg)
        try:
            if args.list_mailboxes:
                list_mailboxes(cfg, args.debug, conn)
            else:
                process_rules(cfg, args.debug, conn)
        finally:
            conn.close()
    except Exception as err:
        if args.debug:
            raise
        parser.error(err)
    return 0


if __name__ == '__main__':
    sys.exit(main())
