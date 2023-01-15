
# Copyright (C) 2020 Maciej Delmanowski <drybjed@gmail.com>
# Copyright (C) 2020 DebOps <https://debops.org/>
# SPDX-License-Identifier: GPL-3.0-or-later

from .constants import DEBOPS_PACKAGE_DATA
from .utils import unexpanduser
import os
import pkgutil
import jinja2
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class AnsibleConfig(object):

    def __init__(self, path, project_type=None):
        self.path = os.path.abspath(path)
        self.project_type = project_type

        self.config = configparser.ConfigParser()
        self._template_config(project_type=self.project_type)

    def _template_config(self, project_type=None):
        template_vars = {}
        template_vars['collections'] = [
                '/usr/share/ansible/collections',
                unexpanduser(os.path.join(DEBOPS_PACKAGE_DATA, 'ansible',
                                          'collections')),
                '~/.ansible/collections',
                'ansible/collections'
        ]

        template_vars['roles'] = [
                '/etc/ansible/roles',
                '/usr/share/ansible/roles',
                '~/.ansible/roles',
                'ansible/playbooks/roles',
        ]

        if project_type == 'legacy':
            template_vars['plugin_types'] = ['modules', 'action', 'callback',
                                             'connection', 'filter', 'lookup',
                                             'vars']

        if template_vars.get('plugin_types'):
            template_vars['plugins'] = {}
            for plugin in template_vars['plugin_types']:
                template_vars['plugins'][plugin] = [
                    '/usr/share/ansible/plugins/' + plugin,
                    '~/.ansible/plugins/' + plugin,
                    unexpanduser(os.path.join(DEBOPS_PACKAGE_DATA, 'ansible',
                                              'collections',
                                              'ansible_collections', 'debops',
                                              'debops', 'plugins', plugin)),
                    'ansible/plugins/' + plugin
                ]

        template = jinja2.Template(
                pkgutil.get_data('debops',
                                 os.path.join('_data',
                                              'templates',
                                              'projectdir',
                                              'legacy',
                                              'ansible.cfg.j2'))
                .decode('utf-8'), trim_blocks=True)
        self.config.read_string(template.render(template_vars))

    def get_option(self, option, section='defaults'):
        return self.config.get(section, option)

    def merge_config(self, config_data):
        for section, pairs in config_data.items():
            if not self.config.has_section(section) and pairs:
                self.config.add_section(section)
            for option, value in pairs.items():
                self.config.set(section, option, str(value))

    def load_config(self):
        if (os.path.exists(self.path) and os.path.isfile(self.path)):
            self.config.read(self.path)

    def write_config(self):
        header = """# Ansible configuration file generated by DebOps

                 # You can modify it, but direct changes will be lost when
                 # contents are refreshed. Store permanent changes in the
                 # DebOps configuration.
                 """
        with open(self.path, 'w') as configfile:
            for line in header.split('\n'):
                print(line.lstrip(), file=configfile)
            self.config.write(configfile)
