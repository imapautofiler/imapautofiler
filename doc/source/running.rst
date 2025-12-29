=========
 Running
=========

Run ``imapautofiler`` on the command line.

.. code-block:: text

   $ imapautofiler -h
   usage: imapautofiler [-h] [-v] [--debug] [-c CONFIG_FILE] [--list-mailboxes]
                        [-n] [-i] [-q] [--no-interactive]
   
   options:
     -h, --help            show this help message and exit
     -v, --verbose         report more details about what is happening
     --debug               turn on imaplib debugging output
     -c, --config-file CONFIG_FILE
     --list-mailboxes      instead of processing rules, print a list of mailboxes
     -n, --dry-run         process the rules without taking any action
     -i, --interactive     enable rich interactive progress displays
     -q, --quiet           show only warning and error messages, disable interactive mode
     --no-interactive      disable interactive progress displays

When run with no arguments, it reads the default configuration file
and processes the rules.

.. code-block:: text

   $ imapautofiler
   Password for my-user@example.com
   Trash: 13767 (Re: spam message from disqus comment) to INBOX.Trash
   Move: 13771 (Re: [Openstack-operators] [deployment] [oslo] [ansible] [tripleo] [kolla] [helm] Configuration management with etcd / confd) to INBOX.OpenStack.Misc Lists
   imapautofiler: encountered 10 messages, processed 2

Interactive Progress Display
============================

imapautofiler includes rich interactive progress displays that show real-time 
processing status when run in a capable terminal. The interactive mode is automatically 
detected and enabled by default, but can be controlled with command-line options.

.. code-block:: text

   $ imapautofiler --interactive
   ┌────────────────────────── imapautofiler ──────────────────────────┐
   │ ┌─────────────────────── Progress ──────────────────────┐        │
   │ │ ⠙ Mailbox 1/3: INBOX                     ███████████   │        │
   │ │ ⠙ 📁 Messages in INBOX                   ████████████  │        │
   │ └────────────────────────────────────────────────────────┘        │
   │ ┌──────────────────────── Statistics ───────────────────┐        │
   │ │ Metric      Count    Progress                          │        │
   │ │ Mailboxes      1     1/3                              │        │
   │ │ Messages     847                                       │        │
   │ │ Seen         150                                       │        │
   │ │ Processed     12                                       │        │
   │ │ Moved          8                                       │        │
   │ │ Deleted        4                                       │        │
   │ └────────────────────────────────────────────────────────┘        │
   │ ┌─────────────── Current: INBOX ────────────────┐                │
   │ │ 📧 Important meeting tomorrow                  │                │
   │ │ 👤 From: boss@company.com                     │                │
   │ │ 📮 To: user@company.com                       │                │
   │ └────────────────────────────────────────────────┘                │
   └────────────────────────────────────────────────────────────────────┘

The interactive display includes:

* **Progress bars** showing overall mailbox progress and current message processing
* **Live statistics** including total messages, seen, processed, and action counts
* **Current message details** with subject, sender, and recipient information
* **Automatic ETAs** and elapsed time tracking
* **Graceful interrupt handling** with Ctrl+C showing progress summary

Command Line Options
====================

``-i, --interactive``
  Force enable rich interactive progress displays, even in environments where 
  auto-detection might disable them.

``-q, --quiet``
  Show only warning and error messages, disabling interactive mode. Useful for
  scripts or when you want minimal output with only important messages.

``--no-interactive``  
  Explicitly disable interactive progress displays and use simple text output.
  Useful for scripts, CI environments, or when redirecting output.

``-n, --dry-run``
  Process rules and show what actions would be taken without actually moving, 
  deleting, or flagging any messages. Excellent for testing rule configurations.

Auto-Detection
==============

Interactive mode is automatically enabled when:

* Rich library is available
* Running in a TTY (not redirected)
* Not in a CI environment (GitHub Actions, GitLab CI, etc.)
* Terminal supports color and cursor positioning
* Not using verbose (``-v``) or debug (``--debug``) modes

Interrupt Handling
==================

When using interactive mode, you can safely interrupt processing with Ctrl+C.
The application will:

* Complete processing of the current message
* Show a progress summary with timing information  
* Display helpful tips for resuming where you left off
* Safely clean up and restore terminal state

.. code-block:: text

   Processing Interrupted ⚠️

   Progress Summary
   Runtime:     2.3m
   Mailboxes:   2/5
   Messages:    1247
   Seen:        856
   Processed:   45
   Moved:       32
   Deleted:     13
   
   💡 Run again to continue processing remaining mailboxes


Different IMAP servers may use different naming conventions for
mailbox hierarchies. Use the ``--list-mailboxes`` option to the
command line program to print a list of all of the mailboxes known to
the account.

.. code-block:: text

   $ imapautofiler --list-mailboxes
   Password for my-user@example.com:
   INBOX
   INBOX.Archive
   INBOX.Conferences.PyCon-Organizers
   INBOX.ML.TIP
   INBOX.ML.python-announce-list
   INBOX.OpenStack.Dev List
   INBOX.PSF
   INBOX.Personal
   INBOX.PyATL
   INBOX.Sent Items
   INBOX.Sent Messages
   INBOX.Trash
   INBOX.Work
