=============
 Configuring
=============

The application is configured through a YAML file. The default file,
``~/.imapautofiler.yml``, is read if no other file is specified on the
command line.

Server Connection
=================

Each configuration file can hold one server specification.

::

  server:
    hostname: example.com
    username: my-user@example.com

The connection section can optionally include a password.

::

  server:
    hostname: example.com
    username: my-user@example.com
    password: super-secret

.. warning::

  Because the password is kept in clear text, this mode of operation
  is only recommended when the configuration file is kept secure by
  other means.

If the password is not provided in the configuration file,
``imapautofiler`` will prompt for a value when it tries to connect to
the server.

.. _trash-mailbox:

Trash Mailbox
=============

The ``trash`` action, for discarding messages without deleting them
immediately, requires a configuration setting to know the name of the
trash mailbox. There is no default value.

::

  trash-mailbox: INBOX.Trash

Rules
=====

The rules are organized by mailbox, and then listed in order. The
first rule that matches a message triggers the associated action, and
then processing for that message stops.

Header Rules
------------

A ``header`` rule can match either a substring or regular expression
against the contents of a specified message header. If a header does
not exist, the content is treated as an empty string. The header text
and pattern are both converted to lowercase before the comparison is
performed.

This example rule matches messages with the string "[pyatl]" in the
subject line.

.. code-block:: yaml

   - headers:
       - name: "subject"
         substring: "[pyatl]"
     action:
       name: "move"
       dest-mailbox: "INBOX.PyATL"

This example rule matches messages for which the "to" header matches
the regular expression ``notify-.*@disqus.net``.

.. code-block:: yaml

   - headers:
       - name: to
         regex: "notify-.*@disqus.net"
     action:
       name: trash

Combination Rules
-----------------

It is frequently useful to be able to apply the same action to
messages with different characteristics. For example, if a mailing
list ID appears in the subject line or in the ``list-id`` header. The
``or`` rule allows nested rules. If any one matches, the combined rule
matches and the associated action is triggered.

For example, this rule matches any message where the PyATL meetup
mailing list address is in the ``to`` or ``cc`` headers.

.. code-block:: yaml

   - or:
       rules:
         - headers:
             - name: "to"
               substring: "pyatl-list@meetup.com"
         - headers:
             - name: "cc"
               substring: "pyatl-list@meetup.com"
     action:
       name: "move"
       dest-mailbox: "INBOX.PyATL"

Recipient Rules
---------------

The example presented for ``or`` rules is a common enough case that it
is supported directly using the ``recipient`` rule. If any header
listing a recipient of the message matches the substring or regular
expression, the action is triggered.

This example is equivalent to the example for ``or``.

.. code-block:: yaml

   - recipient:
       substring: "pyatl-list@meetup.com"
     action:
       name: "move"
       dest-mailbox: "INBOX.PyATL"

Actions
=======

Each rule is associated with an *action* to be triggered when the rule
matches a message.

Move Action
-----------

The ``move`` action copies the message to a new mailbox and then
deletes the version in the source mailbox. This action can be used to
automatically file messages.

The example below move any message sent to the PyATL meetup group
mailing list into the mailbox ``INBOX.PyATL``.

.. code-block:: yaml

   - recipient:
       substring: "pyatl-list@meetup.com"
     action:
       name: "move"
       dest-mailbox: "INBOX.PyATL"

Different IMAP servers may use different naming conventions for
mailbox hierarchies. Use the ``--list-mailboxes`` option to the
command line program to print a list of all of the mailboxes known to
the account.

Trash Action
------------

Moving messages to the "trash can" is a less immediate way of deleting
them. Messages in the trash can can typically be recovered until they
expire, or until the trash is emptied explicitly.

Using this action requires setting the global ``trash-mailbox`` option
(see :ref:`trash-mailbox`). If the action is triggered and the option
is not set, the action reports an error and processing stops.

This example moves messages for which the "to" header matches the
regular expression ``notify-.*@disqus.net`` to the trash mailbox.

.. code-block:: yaml

   - headers:
       - name: to
         regex: "notify-.*@disqus.net"
     action:
       name: trash

Delete Action
-------------

The ``delete`` action is more immediately destructive. Messages are
permanently removed from the mailbox as soon as the mailbox is closed.

This example deletes messages for which the "to" header matches the
regular expression ``notify-.*@disqus.net``.

.. code-block:: yaml

   - headers:
       - name: to
         regex: "notify-.*@disqus.net"
     action:
       name: delete
