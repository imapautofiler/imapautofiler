=============
 Configuring
=============

The application is configured through a YAML file. The default file,
``~/.imapautofiler.yml``, is read if no other file is specified on the
command line.

Server Connection
=================

Each configuration file can hold one server specification.

.. code-block:: yaml

  server:
    hostname: example.com
    username: my-user@example.com

imapautofiler also supports using the keyring_ module to store and retrieve a
password from your system keyring:

.. _keyring: https://pypi.python.org/pypi/keyring

.. code-block:: yaml

  server:
    hostname: example.com
    username: my-user@example.com
    use_keyring: true

In this scenario, you will be asked for the password on first run. The password
will be stored in your operating system's secure keyring and reused when running
the app.

If you do not want to use the keyring, the connection section can optionally
include a password.

.. code-block:: yaml

  server:
    hostname: example.com
    username: my-user@example.com
    password: super-secret

.. warning::

  Because the password is kept in clear text, this mode of operation
  is only recommended when the configuration file is kept secure by
  other means.

If the password is not provided in the configuration file and ``use_keyring`` is
not true, ``imapautofiler`` will prompt for a value when it tries to connect to
the server.

Maildir Location
================

As an alternative to a server specification, the configuration file
can refer to a local directory containing one or more Maildir
folders. This is especially useful when combining imapautofiler with
offlineimap_.

.. code-block:: yaml

   maildir: ~/Mail

.. note::

   The directory specified should not itself be a Maildir. It must be
   a regular directory with nested Maildir folders.

.. _offlineimap: http://www.offlineimap.org

.. _trash-mailbox:

Trash Mailbox
=============

The ``trash`` action, for discarding messages without deleting them
immediately, requires a configuration setting to know the name of the
trash mailbox. There is no default value.

.. code-block:: yaml

  trash-mailbox: INBOX.Trash

Mailboxes
=========

The mailboxes that imapautofiler should process are listed under ``mailboxes``.
Each mailbox has a name and a list of rules.

.. code-block:: yaml

  mailboxes:
  - name: INBOX
    rules: ...
  - name: Sent
    rules: ...

Rules
=====

The rules are organized by mailbox, and then listed in order. The
first rule that matches a message triggers the associated action, and
then processing for that message stops.

Header Rules
------------

A ``header`` rule can match either a complete header value, a
substring, or a regular expression against the contents of a specified
message header. If a header does not exist, the content is treated as
an empty string. The header text and pattern are both converted to
lowercase before the comparison is performed.

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

This example rule matches messages for which the "Message-Id" header
is exactly ``<4FF56508-357B-4E73-82DE-458D3EEB2753@example.com>``.

.. code-block:: yaml

   - headers:
       - name: to
         value: "<4FF56508-357B-4E73-82DE-458D3EEB2753@example.com>"
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

For more complicated formulations, the ``and`` rule allows combining
other rules so that they all must match the message before the action
is taken.

For example, this rule matches any message sent to the PyATL meetup
mailing list address with a subject including the text ``"meeting
update"``.

.. code-block:: yaml

   - and:
       rules:
         - headers:
             - name: "to"
               substring: "pyatl-list@meetup.com"
         - headers:
             - name: "subject"
               substring: "meeting update"
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

The example below moves any message sent to the PyATL meetup group
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

Sort Action
-----------

The ``sort`` action uses data in a message header to determine the
destination mailbox for the message. This action can be used to
automatically file messages from mailing lists or other common sources
if the corresponding mailbox hierarchy is established. A ``sort``
action is equivalent to ``move`` except that the destination is
determined dynamically.

The action settings may contain a ``header`` entry to specify the name
of the mail header to examine to find the destination. The default is
to use the ``to`` header.

The action data may contain a ``dest-mailbox-regex`` entry for parsing
the header value to obtain the destination mailbox name. If the regex
has one match group, that substring will be used. If the regex has
more than one match group, the ``dest-mailbox-regex-group`` option
must specify which group to use (0-based numerical index). The default
pattern is ``([\w-+]+)@`` to match the first part of an email address.

The action data must contain a ``dest-mailbox-base`` entry with the
base name of the destination mailbox. The actual mailbox name will be
constructed by appending the value extracted via
``dest-mailbox-regex`` to the ``dest-mailbox-base`` value. The
``dest-mailbox-base`` value should contain the mailbox separator
character (usually ``.``) if the desired mailbox is a sub-folder of
the name given.

The example below sorts messages associated with two mailing lists
into separate mailboxes under a parent mailbox ``INBOX.ML``. It uses
the default regular expression to extract the prefix of the ``to``
header for each message. Messages to the
``python-committers@python.org`` mailing list are sorted into
``INBOX.ML.python-committers`` and messages to the
``sphinx-dev@googlegroups.com`` list are sorted into
``INBOX.ML.sphinx-dev``.

.. code-block:: yaml

   - or:
       rules:
         - recipient:
             substring: python-committers@python.org
         - recipient:
             substring: sphinx-dev@googlegroups.com
     action:
       name: sort
       dest-mailbox-base: "INBOX.ML."

Sort Mailing List Action
------------------------

The ``sort-mailing-list`` action works like ``sort`` configured to
read the ``list-id`` header and extract the portion of the ID between
``<`` and ``>``. if they are present. If there are no angle brackets
in the ID, the entire value is used. As with ``sort`` the
``dest-mailbox-regex`` can be specified in the rule to change this
behavior.

The example below sorts messages to any mailing list into separate
folders under ``INBOX.ML``.

.. code-block:: yaml

   - is-mailing-list: {}
     action:
       name: sort-mailing-list
       dest-mailbox-base: "INBOX.ML."

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

Complete example configuration file
===================================

Here's an example of a configuration file with all the possible parts.

.. code-block:: yaml

    server:
      hostname: imap.gmail.com
      username: user@example.com
      password: xxxxxxxxxxxxxx

    trash-mailbox: "[Gmail]/Trash"

    mailboxes:
    - name: INBOX
      rules:
      - headers:
        - name: "from"
          substring: user1@example.com
        action:
          name: "move"
          dest-mailbox: "User1 correspondence"
      - headers:
        - name: recipient
          substring: dev-team
        - name: subject
          substring: "[Django] ERROR"
        action:
          name: "move"
          dest-mailbox: "Django Errors"
