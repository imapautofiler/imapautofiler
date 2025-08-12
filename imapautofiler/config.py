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
import typing

import yaml

LOG: logging.Logger = logging.getLogger(__name__)


def get_config(filename: str) -> dict[str, typing.Any] | None:
    """Return the configuration data.

    :param filename: name of configuration file to read
    :type filename: str

    Read ``filename`` and parse it as a YAML file, then return the
    results.

    """
    full_filename: str = os.path.expanduser(filename)
    LOG.debug("loading config from %s", full_filename)
    with open(full_filename, mode="r", encoding="utf-8") as f:
        # TODO(dhellmann): Add type checking to the YAML parser.
        return yaml.safe_load(stream=f)


def tobool(value: str | bool) -> bool:
    """Convert config option value to boolean."""
    if isinstance(value, bool):
        return value

    return str(value).lower() in ("y", "yes", "t", "true", "on", "enabled", "1")
