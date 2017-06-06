=========
 Running
=========

Run ``imapautofiler`` on the command line.

.. code-block:: text

   $ imapautofiler -h
   usage: imapautofiler [-h] [-v] [--debug] [-c CONFIG_FILE] [--list-mailboxes]
   
   optional arguments:
     -h, --help            show this help message and exit
     -v, --verbose         report more details about what is happening
     --debug               turn on imaplib debugging output
     -c CONFIG_FILE, --config-file CONFIG_FILE
     --list-mailboxes      instead of processing rules, print a list of mailboxes

When run with no arguments, it reads the default configuration file
and processes the rules.

.. code-block:: text

   $ imapautofiler
   Password for my-user@example.com
   Trash: 13767 (Re: spam message from disqus comment) to INBOX.Trash
   Move: 13771 (Re: [Openstack-operators] [deployment] [oslo] [ansible] [tripleo] [kolla] [helm] Configuration management with etcd / confd) to INBOX.OpenStack.Misc Lists
   imapautofiler: encountered 10 messages, processed 2


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
