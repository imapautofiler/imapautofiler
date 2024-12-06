============
 Installing
============

Install ``imapautofiler`` with pip_ under Python 3.5 or greater.

.. code-block:: text

   $ pip install imapautofiler

System Package Dependencies
===========================

``imapautofiler`` uses some libraries for which system packages may
need to be installed.

Debian
------

Before installing ``imapautofiler``, install the other required packages

.. code-block:: shell

   $ sudo apt-get install build-essential python3-dev \
     libffi-dev libssl-dev libdbus-1-dev libdbus-glib-1-dev \
     gnome-keyring

If you are using a virtualenv, you may also need to install
``dbus-python``.

.. code-block:: shell

   $ pip install dbus-python

.. _pip: https://pypi.python.org/pypi/pip

============
 Docker
============

The docker image allow to run the script with the config as mount volume.

.. code-block:: shell
    $ git clone https://github.com/imapautofiler/imapautofiler
    $ docker build -t local-imapautofiler ./imapautofiler
    $ docker run -it  -v "./imap-config:/app/config.d" --rm local-imapautofiler

There are environements variables to change the parameters of imapautofiler :
* ``DEBUG=true`` to pass the parameter --debug
* ``VERBOSE=true`` to pass the parameter --verbose
* ``LISTMAILBOXES=true`` to pass the parameter --list-mailboxes
* ``DRYRUN=true`` to pass the parameter --dry-run

