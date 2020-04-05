==============
 Contributing
==============

The Basics
==========

The source code and bug tracker for imapautofiler are `hosted on
github <https://github.com/imapautofiler/imapautofiler>`__.

The source code is released under the Apache 2.0 license. All patches
should use the same license.

When reporting a bug, please specify the version of imapautofiler you
are using.


Message handling rules
======================

imapautofiler operation is driven by *rules* and *actions* defined in
the :doc:`configuration file <configuring>`.

Each rule is evaluated by a class derived from
:class:`~imapautofiler.rules.Rule` and implemented in
``imapautofiler/rules.py``.

A rule must implement the ``check()`` method to support the interface
defined by the abstract base class. The method receives an
`email.message.Message
<https://docs.python.org/3.5/library/email.message.html>`__ instance
containing the message being processed. ``check()`` must return
``True`` if the rule should be applied to the message, or ``False`` if
it should not.

Each new rule must be handled in the
:func:`~imapautofiler.rules.factory` function so that when the name of
the rule is encountered the correct rule class is instantiated and
returned.

Message handling actions
========================

Each action triggered by a rule is evaluated by a class derived from
:class:`~imapautofiler.actions.Action` and implemented in
``imapautofiler/actions.py``.

An action must implement the ``invoke()`` method to support the
interface defined by the abstract base class. The method receives an
``IMAPClient`` instance (from the `imapclient`_ package) connected to
the IMAP server being scanned, a string message ID, and an
`email.message.Message
<https://docs.python.org/3.5/library/email.message.html>`__ instance
containing the message being processed. ``invoke()`` must perform the
relevant operation on the message.

Each new action must be handled in the
:func:`~imapautofiler.actions.factory` function so that when the name
of the action is encountered the correct action class is instantiated
and returned.

.. _imapclient: http://imapclient.readthedocs.io/en/stable/

API Documentation
=================

.. toctree::

   api/autoindex

Local Test Maildir
==================

Use ``tools/maildir_test_data.py`` to create a local test Maildir with
a few sample messages. The script requires several dependencies, so
for convenience there is a tox environment pre-configured to run it in
a virtualenv.

The script requires one argument to indicate the parent directory
where the Maildirs should be created.

.. code-block:: console

   $ tox -e testdata -- /tmp/testdata

Release Notes
=============

This project uses reno_ for managing release notes. Pull requests with
bug fixes and new features should include release notes and
documentation updates.

To create a new release note, use the `reno new` command. Use the
version of reno that will be used in the automated documentation build
by setting up the documentation build locally using `tox`.

.. code-block:: shell

   $ tox -e docs

Then, run the reno command from the virtualenv that tox creates,
passing a "slug" containing a summary of the fix or feature.

.. code-block:: shell

   $ ./.tox/docs/bin/reno new add-reno
   no configuration file in: ./releasenotes/config.yaml, ./reno.yaml
   Created new notes file in releasenotes/notes/add-reno-65a040ebe662341a.yaml

Finally, edit the file that was created. Fill in the "features" or
"fixes" section as appropriate, and remove the rest of the text in the
file.

To test the build, you will need to `git add` the new file, then run
tox again.

.. code-block:: shell

   $ git add releasenotes/notes/add-reno-65a040ebe662341a.yaml
   $ tox -e docs

The output will appear in the file `doc/build/html/history.html`.

.. note::

   Refer to the reno_ documentation for more details about adding,
   editing, and managing release notes.

.. _reno: https://docs.openstack.org/reno/latest/
