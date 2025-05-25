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

 Docker
============

The docker image allow to run the script with the config as mount volume.

There are environements variables to change the parameters of imapautofiler :
* ``DEBUG=true`` to pass the parameter --debug
* ``VERBOSE=true`` to pass the parameter --verbose
* ``LISTMAILBOXES=true`` to pass the parameter --list-mailboxes
* ``DRYRUN=true`` to pass the parameter --dry-run

The script running imapautofiler will take a folder as config directory.
Imapautofiler will be run for all config file present into that folder.
The folder read by the script is : ``/app/config.d/``, you can mount it
from the host machine with ``-v "./my-config-folder:/app/config.d/"``.

Since the Dockerfile is inside the ``contrib/`` folder, you need the specify
the file path.
Here is an example how to build and run the image in dry-run mode:

.. code-block:: shell
    $ git clone https://github.com/imapautofiler/imapautofiler
    $ docker build -t local-imapautofiler -f ./imapautofiler/contrib/Dockerfile ./imapautofiler
    $ docker run -it -e "DRYRUN=true" -v "./imap-config:/app/config.d" --rm local-imapautofiler
