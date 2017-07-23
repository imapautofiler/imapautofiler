==============
 Contributing
==============

.. include:: ../../CONTRIBUTING.rst

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
