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
import email.parser
import imaplib
import logging
import pprint
import re
import sys

from imapautofiler import config

LOG = logging.getLogger(__name__)


def open_connection(hostname, username, password):
    # Connect to the server
    LOG.info('connecting to %s@%s', username, hostname)
    connection = imaplib.IMAP4_SSL(hostname)
    connection.login(username, password)
    connection.enable('UTF8=ACCEPT')
    return connection


list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')


def parse_list_response(line):
    flags, delimiter, mailbox_name = list_response_pattern.match(line).groups()
    mailbox_name = mailbox_name.strip('"')
    return (flags, delimiter, mailbox_name)


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
    args = parser.parse_args()

    if args.debug:
        imaplib.Debug = 4

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(message)s',
    )
    logging.debug('starting')

    try:
        cfg = config.get_config(args.config_file)
    except Exception as err:
        parser.error(err)

    conn = open_connection(
        hostname=cfg['server']['hostname'],
        username=cfg['server']['username'],
        password=cfg['server']['password'],
    )
    try:
        for mailbox in cfg['mailboxes']:
            mailbox_name = mailbox['name']
            conn.select(
                mailbox='"{}"'.format(mailbox_name).encode('utf-8'),
            )

            typ, [msg_ids] = conn.search(None, b'ALL')
            msg_ids = msg_ids.decode('utf-8').split(' ')
            for msg_id in msg_ids:
                # Get the body of the message and create a Message object.
                email_parser = email.parser.BytesFeedParser()
                typ, msg_data = conn.fetch(msg_id, '(BODY.PEEK[HEADER] FLAGS)')
                for block in msg_data[0][1:]:
                    email_parser.feed(block)
                message = email_parser.close()
                LOG.debug('message %s: %s', msg_id, message['subject'])

                for rule in mailbox['rules']:
                    match = True
                    for header in rule['headers']:
                        LOG.debug('checking header %r', header['name'])
                        header_value = message[header['name']] or ''
                        if 'substring' in header:
                            # simple substring rule
                            LOG.debug('message[%s] = %r',
                                      header['name'], header_value)
                            LOG.debug('looking for substring %r',
                                      header['substring'])
                            if header['substring'] not in header_value:
                                # this header doesn't match, so the
                                # rule fails, so move to the next rule
                                match = False
                                break
                    if match:
                        LOG.info('moving %s (%s) to %s',
                                 msg_id, message['subject'],
                                 rule['dest-mailbox'])
                    else:
                        LOG.debug('no rules match')
    finally:
#        conn.close()
        conn.logout()
    return 0


if __name__ == '__main__':
    sys.exit(main())
