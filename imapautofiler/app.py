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

""" """

import argparse
import imaplib
import logging
import sys

from imapautofiler import actions, client, config, rules, ui, i18n

LOG = logging.getLogger("imapautofiler")


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


def process_rules(cfg, debug, conn, dry_run=False, progress_tracker=None):
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

    # Start overall progress tracking
    progress_tracker.start_overall(len(cfg["mailboxes"]))

    for mailbox in cfg["mailboxes"]:
        mailbox_name = mailbox["name"]
        LOG.info("starting mailbox %r", mailbox_name)

        mailbox_rules = [rules.factory(r, cfg) for r in mailbox["rules"]]

        mailbox_iter = conn.get_mailbox_iterator(mailbox_name)

        # Start mailbox-specific progress tracking
        progress_tracker.start_mailbox(mailbox_name, len(mailbox_iter))

        for msg_id, message in mailbox_iter:
            num_messages += 1
            subject = i18n.get_header_value(message, "subject") or "No Subject"
            from_addr = i18n.get_header_value(message, "from") or ""
            to_addr = i18n.get_header_value(message, "to") or ""

            if debug:
                print(message.as_string().rstrip())
            else:
                LOG.debug("message %s: %s", msg_id, subject)

            # Update progress tracker with current message
            progress_tracker.update_message(advance=0, subject=subject, from_addr=from_addr, to_addr=to_addr)

            action_taken = False
            for rule in mailbox_rules:
                if rule.check(message):
                    action = actions.factory(rule.get_action(), cfg)
                    try:
                        action.report(conn, mailbox_name, msg_id, message)
                        if not dry_run:
                            action.invoke(conn, mailbox_name, msg_id, message)

                        # Determine action type for statistics
                        action_type = "move"  # Default
                        if hasattr(action, "NAME") and action.NAME:
                            action_name = str(action.NAME).lower()
                            if "delete" in action_name:
                                action_type = "delete"
                            elif "flag" in action_name:
                                action_type = "flag"

                        # Update progress with action taken
                        progress_tracker.update_message(advance=1, action=action_type)
                        action_taken = True

                    except Exception as err:
                        LOG.error(
                            'failed to %s "%s": %s',
                            action.NAME,
                            subject,
                            err,
                        )
                        num_errors += 1
                        progress_tracker.update_message(advance=1, action="error")
                        if debug:
                            raise
                    else:
                        num_processed += 1
                    # At this point we've processed the message
                    # based on one rule, so there is no need to
                    # look at the other rules.
                    break
            else:
                LOG.debug("no rules match")

            # If no action was taken, still update progress to advance the counter
            if not action_taken:
                progress_tracker.update_message(advance=1)

            # break

        # Remove messages that we just moved.
        conn.expunge()
        LOG.info("completed mailbox %r", mailbox_name)

        # Finish mailbox progress tracking
        progress_tracker.finish_mailbox()
    LOG.info("encountered %s messages, processed %s", num_messages, num_processed)
    if num_errors:
        LOG.info("encountered %d errors", num_errors)
    return


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="report more details about what is happening",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="turn on imaplib debugging output",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        default="~/.imapautofiler.yml",
    )
    parser.add_argument(
        "--list-mailboxes",
        default=False,
        action="store_true",
        help="instead of processing rules, print a list of mailboxes",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        default=False,
        action="store_true",
        help="process the rules without taking any action",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        default=False,
        action="store_true",
        help="enable rich interactive progress displays",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        default=False,
        action="store_true",
        help="suppress logs, show only progress",
    )
    parser.add_argument(
        "--no-interactive",
        default=False,
        action="store_true",
        help="disable interactive progress displays",
    )
    args = parser.parse_args()

    if args.debug:
        imaplib.Debug = 4  # type: ignore[attr-defined]

    # Determine if we should show interactive progress using enhanced auto-detection
    show_progress = ui.should_use_progress(
        interactive_requested=args.interactive,
        no_interactive_requested=args.no_interactive,
        verbose=args.verbose,
        debug=args.debug
    )

    # Handle quiet mode and logging configuration
    # When showing interactive progress, suppress info logs to avoid interfering
    # But --no-interactive should preserve normal log level
    if args.quiet or (
        show_progress and not args.verbose and not args.debug and not args.no_interactive
    ):
        log_level = logging.WARNING  # Suppress info logs when showing progress
    elif args.verbose or args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(name)s: %(message)s",
    )
    logging.debug("starting")

    try:
        cfg = config.get_config(args.config_file)
        if cfg is None:
            parser.error(f"Could not load configuration from {args.config_file}")
        conn = client.open_connection(cfg)
        try:
            if args.list_mailboxes:
                list_mailboxes(cfg, args.debug, conn)
            else:
                # Create appropriate progress tracker
                if show_progress:
                    # Use interactive widgets by default when showing progress
                    use_interactive = args.interactive or (
                        show_progress and ui.RICH_AVAILABLE
                    )
                    progress_tracker = ui.ProgressTracker(
                        interactive=use_interactive, quiet=args.quiet
                    )

                    # When using interactive progress, redirect warnings to rich console
                    if use_interactive and not args.verbose and not args.debug:
                        # Add the rich warning handler
                        rich_handler = ui.RichWarningHandler(progress_tracker)
                        rich_handler.setFormatter(logging.Formatter("%(message)s"))
                        logging.getLogger().addHandler(rich_handler)
                else:
                    progress_tracker = ui.NullProgressTracker()

                with progress_tracker:
                    process_rules(cfg, args.debug, conn, args.dry_run, progress_tracker)
        finally:
            conn.close()
    except Exception as err:
        if args.debug:
            raise
        parser.error(str(err))
    return 0


if __name__ == "__main__":
    sys.exit(main())
