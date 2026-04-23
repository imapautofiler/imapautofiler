===============
 imapautofiler
===============

imapautofiler is a tool for managing messages on an IMAP server based
on rules for matching properties such as the recipient or header
content.

Features
========

* **Interactive Terminal Interface** - Rich progress bars with real-time statistics
* **Graceful Interrupt Handling** - Safe Ctrl+C with progress summaries
* **Comprehensive Metrics** - Track messages seen, processed, moved, deleted, and errors
* **Smart Rule Processing** - Apply complex filters based on headers, sender, recipient, etc.
* **Multiple Backend Support** - Works with both IMAP servers and Maildir storage

Quick Start
===========

Install and run with interactive progress display:

.. code-block:: shell

   $ pip install imapautofiler
   $ imapautofiler --interactive

The tool will automatically detect your terminal capabilities and show a rich
interface with progress bars, live statistics, and current message information.

Links
=====

* Github: https://github.com/imapautofiler/imapautofiler
* Documentation: http://imapautofiler.readthedocs.io/
