=========
 History
=========

Unreleased
==========

- Add protection for ``time-limit`` and ``sort-by-year`` in case the
  ``Date`` header cannot be parsed.
- Improve progress logging by reporting when each mailbox starts and
  showing the source mailbox along with other details for each action
  being taken.
- Correct a problem with the handlig of unparsable dates in `SortByDate` so that
  messages without a `Date` header or with a `Date` header that cannot be parsed
  are sorted into a special mailbox called `unparsable-date`.
- Convert packaging from setuptools to hatch and hatchling.
- Add type hints and mypy checking to linter.
- Change minimum python version to 3.13.

1.14.0
======

- Add :ref:`sort-by-year-action`.
- Add Python 3.12 to set matrix.

1.13.0
======

- stop using reno for release notes
- add python 3.11 support
- modernize packaging
- add testtools dependency to for tests
- set language to english for sphinx 5.0

1.12.0
======

* mergify: initial configuration rules
* client: update ssl handling for newer python 3 and imapclient
* requirements: update imapclient dependency to >=2.2.0 for python 3.10
* packaging: add python 3.10 support to trove classifiers
* tox: use current python version only for default environments
* github: add python 3.10 to CI configuration
* stop building universal wheels

1.11.0
======

.. _imapautofiler_1.11.0_New Features:

New Features
------------

.. releasenotes/notes/skip-ssl-34b2690375ef6260.yaml @ b'f51a4f8814083468a18d6596d7a2a1f6b9a0cf60'

- A configuration option has been added to disable the use of
  SSL/TLS for servers that do not support it. The default is to
  always use SSL/TLS. See :ref:`config-server-connection` for details.
  Contributed by `Samuele Zanon <https://github.com/webs86>`__.


.. _imapautofiler_1.11.0_Upgrade Notes:

Upgrade Notes
-------------

.. releasenotes/notes/drop-python-3.6-77bb3180351cd195.yaml @ b'63df44c4b68c5a05d1f7ad845f1905ce2bc887c5'

- This release drops support for python 3.6 and 3.7.

Changes
-------

* add a release note for the new option to disable ssl connections
* ignore files created by release notes build
* expand test coverage of rules module
* show coverage report for test modules
* Add configuration to enable/disable ssl
* drop support for python 3.6 and 3.7

1.10.0
======

.. _imapautofiler_1.10.0_New Features:

New Features
------------

.. releasenotes/notes/check-hostname-a2610e244ce7f6e2.yaml @ b'e88f5ebe96b1751c47abbfa159a631fdbc991307'

- Add ``check_hostname`` configuration option to allow connection to
  sites where the hostname does not match the value in the SSL/TLS
  certificate. See :ref:`config-server-connection` for details.

.. releasenotes/notes/flag-and-unflag-c3964dee9b68fb83.yaml @ b'effd877ac5b24a862c5e88c95dbb6573a2d32aad'

- Add `flag` and `unflag` actions. See :ref:`config-flag-action` for details.

.. releasenotes/notes/mark-read-and-unread-ed5ad2793142eeae.yaml @ b'6858ee54b2dfe82c1a5b569423c3bc02de244543'

- Add `mark_read` and `mark_unread` actions. See :ref:`config-mark-read-action` for details.

Changes
-------

* add release note for read/unread actions
* add release note for flag actions
* add mark\_read/mark\_unread actions
* when --debug is set stop when we see an exception
* fix mailbox client implementation of flagging
* clean up flag/unflag logging
* simplify flag and add unflag action
* Add unit tests for 'flag' action
* Add documentation for 'flag' action
* Implement 'flag' action
* add release note for check\_hostname

1.9.0
=====

.. _imapautofiler_1.9.0_New Features:

New Features
------------

.. releasenotes/notes/add-reno-65a040ebe662341a.yaml @ b'051298d0d40e0c9ec260030244a5534277a51eee'

- Start using `reno <https://docs.openstack.org/reno/latest/>`_ for
  managing release notes.

Changes
-------

* add github action for publishing releases
* use default python for pep8 tox target
* remove travis config
* add github workflows for unit tests
* add github workflows for check jobs
* update list of default tox environments
* add pkglint tox target for verifying packaging
* move test commands out of travis.sh to tox.ini
* Add unit tests for config
* Add 'check\_hostname' server option
* use the correct default ssl context
* document debian dependencies
* update documentation for templating destination folders
* add templating to the sort action
* remove verbose flag from pytest call
* ensure that if a destination mailbox does not exist we create it
* add jinja2 templates to move action
* add python 3.8 to test matrix
* add separate doc requirement file for rtd build
* add contributing instructions for using reno
* add secrets module to API docs
* configure git depth for travis-ci
* add change history
* fix contributing docs
* move CONTRIBUTING.rst to CONTRIBUTING.md
* remove import to fix pep8 error

1.8.1
=====

* Fix comparison with TZ aware datetime in TimeLimit rule
* update URLs for new location in github org

1.8.0
=====

* add xenial dist for py 3.7 on travis
* have travis script show what is installed
* set minimums for test packages
* use yaml safe loader
* use assertEqual instead of assertEquals
* drop direct use of testtools
* fix warning for strings with unusual escapes
* update trove classifiers
* drop python 3.5 and add 3.7
* perform substring matches without regard to case

1.7.0
=====

* decode message subjects before logging
* switch rule loggers to use NAME
* add --dry-run option
* remove debug print statement
* switch action log messages to use action name directly
* add python 3.6 to the default environment list for tox
* fix factory tests so they don't break when new items are registered

1.6.0
=====

* use a separate attribute for i18n test message in test base class
* ignore .eggs directory
* uninstall nose and mock in travis but leave pytest
* ignore tests in coverage output
* switch from testrepository to pytest
* TimeLimit Rule
* case fix for IMAP and fix lint issues
* Allow more imap configuration via autofiler config

1.5.0
=====

* fix indentation of trash-mailbox setting in example
* link to the keyring documentation
* Add support for using the keyring module to store the IMAP password
* restore the api documentation

1.4.1
=====

* add home-page and description to setup.cfg

1.4.0
=====

* do not check in automatically generated documentation files
* document sort and sort-mailing-list actions
* make header exact match rule to work like other header rules
* add i18n support to sort actions
* extend i18n tests to substring and regex matching rules
* revert logging in header check method
* add internationalized header support
* add a name to the and rule for the lookup table
* implement "and" rule
* automate building the lookup tables for factories

1.3.0
=====

* fix pep8 error
* do not assume a mailbox separator in sort action
* make sort-mailing-list more a general sort action
* add sort-mailing-list action
* add a rule for checking if a message is from a mailing list
* add a rule for checking if a header exists
* Add documentation of mailbox list and example configuration
* do not die if there is an error handling one message
* be explicit about the code block type in config docs

1.2.1
=====

* use universal wheels

1.2.0
=====

* check in the docs generated by pbr
* add tool for creating dummy maildir dataset for testing
* add support for local maildir folders
* create a wrapper class for the server connection
* add/update docstrings for classes
* add basic contributor docs for rules and actions
* move flake8 dependency to extras so it is installed by travis
* have pbr and sphinx automatically generate API docs for classes
* wrap travis with script to support more complex build configurations
* configure travis to test doc build
* add tox environment to test sphinx build
* ignore .coverage output files
* configure travis-ci
* fix docstring for get\_message

1.1.1
=====

* add contributing instructions
* add the documentation link to the readme
* use the default docs theme
* add documentation

1.1.0
=====

* prompt the user for a password if none is given

1.0.0
=====

* add 'recipient' rules to cut down on repetition
* report on how many messages were processed at the end of the run
* add regex support for header matching
* add tests for actions
* make Action an abstract base class
* move test message to property of base class
* add tests for Headers
* add tests for HeaderSubString
* use Or directly in tests
* simplify rules tests to decouple Or from HeaderSubstring
* show missing coverage lines in report output
* make Rule an abstract base class
* expand Or rule tests
* add test coverage report
* start writing unit tests
* protect against missing header
* add --list-mailboxes and 'trash' action
* abstract out the actions
* start refactoring rules into classes
* support multiple types of actions
* switch to imapclient library, which uses uids
* semi-working version, gets confused after an expunge
* clean up some of the local debug messages
* separate imap debug from local verbose output
* simple rule application
* fix typo in packaging file
* initial structural commit
