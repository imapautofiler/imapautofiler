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


def _all_subclasses(cls):
    direct = cls.__subclasses__()
    yield from direct
    for d in direct:
        yield from _all_subclasses(d)


def make_lookup_table(cls, attr_name):
    table = {
        getattr(subcls, attr_name, None): subcls
        for subcls in _all_subclasses(cls)
        if getattr(subcls, attr_name, None)
    }
    if getattr(cls, attr_name, None):
        table[getattr(cls, attr_name)] = cls
    return table
