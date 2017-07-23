#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import os.path

import yaml

LOG = logging.getLogger(__name__)


def get_config(filename):
    """Return the configuration data.

    :param filename: name of configuration file to read
    :type filename: str

    Read ``filename`` and parse it as a YAML file, then return the
    results.

    """
    filename = os.path.expanduser(filename)
    LOG.debug('loading config from %s', filename)
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.load(f)
