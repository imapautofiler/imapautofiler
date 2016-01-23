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
import sys

from imapautofiler import config
import imapclient

LOG = logging.getLogger(__name__)


def process_rules(cfg, debug):
    conn = imapclient.IMAPClient(
        cfg['server']['hostname'],
        use_uid=True,
        ssl=True,
    )
    conn.login(cfg['server']['username'], cfg['server']['password'])
    try:

        for mailbox in cfg['mailboxes']:
            mailbox_name = mailbox['name']
            conn.select_folder(mailbox_name)

            msg_ids = conn.search(['ALL'])

            for msg_id in msg_ids:
                # Get the body of the message and create a Message
                # object, one line at a time (skipping the first line
                # that includes the server response).
                email_parser = email.parser.BytesFeedParser()
                response = conn.fetch([msg_id], ['BODY.PEEK[HEADER]'])
                email_parser.feed(response[msg_id][b'BODY[HEADER]'])
                message = email_parser.close()
                if debug:
                    print(message.as_string().rstrip())
                else:
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
                        action = rule['action']['name']
                        if action == 'move':
                            LOG.info('moving %s (%s) to %s',
                                     msg_id, message['subject'],
                                     rule['dest-mailbox'])
                            dest_mailbox = rule['action']['dest-mailbox']
                            response = conn.copy(
                                [msg_id],
                                dest_mailbox,
                            )
                            response = conn.add_flags(
                                [msg_id],
                                [imapclient.DELETED],
                            )
                        elif action == 'delete':
                            LOG.info('deleting %s (%s)',
                                     msg_id, message['subject'])
                            response = conn.add_flags(
                                [msg_id],
                                [imapclient.DELETED],
                            )
                        # At this point we've processed the message
                        # based on one rule, so there is no need to
                        # look at the other rules.
                        break
                    else:
                        LOG.debug('no rules match')

                # break

            # Remove messages that we just moved.
            response = conn.expunge()
    finally:
        try:
            conn.close()
        except:
            pass
        conn.logout()
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
    args = parser.parse_args()

    if args.debug:
        imaplib.Debug = 4

    if args.verbose or args.debug:
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
        process_rules(cfg, args.debug)
    except Exception as err:
        if args.debug:
            raise
        parser.error(err)
    return 0


if __name__ == '__main__':
    sys.exit(main())
