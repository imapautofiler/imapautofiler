#!/usr/bin/env python3
#
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

import argparse
import os

from imapautofiler.tests import test_maildir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'maildir_root',
        help='local directory for the Maildir folders',
    )
    args = parser.parse_args()

    if not os.path.exists(args.maildir_root):
        os.makedirs(args.maildir_root)

    src = test_maildir.MaildirFixture(
        args.maildir_root,
        'source-maildir',
    )
    src.make_message(
        subject='test subject',
        to_addr='pyatl-list@meetup.com',
    )

    test_maildir.MaildirFixture(
        args.maildir_root,
        'destination-maildir',
    )


if __name__ == '__main__':
    main()
