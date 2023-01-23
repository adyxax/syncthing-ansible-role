from ansible.plugins.action import ActionBase
import re
import yaml
from yaml.loader import SafeLoader

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()
        result = super(ActionModule, self).run(tmp, task_vars)
        result['changed'] = False
        result['failed'] = False

        error_msgs = []

        ### Compiling host configuration ######################################
        config = {}
        if 'syncthing' in task_vars:
            config = {
                'config_path': "",
                'folders_to_create': [],
                'packages': [],
                'service': "syncthing",
                'user_group': "syncthing",
            }
            if task_vars['ansible_distribution'] == 'FreeBSD':
                config['config_dir'] = "/usr/local/etc/syncthing/"
                config['data_dir'] = "/var/syncthing"
                config['packages'] = ["syncthing"]
            elif task_vars['ansible_distribution'] == 'Gentoo':
                config['config_dir'] = "/var/lib/syncthing/.config/syncthing/"
                config['data_dir'] = "/var/lib/syncthing"
                config['packages'] = ["net-p2p/syncthing"]
            else:
                error_msgs.append(f"syncthing role does not support {task_vars['ansible_distribution']} hosts yet")

        ### Results compilation ##############################################
        if error_msgs != []:
            result['msg'] = ' ; '.join(error_msgs)
            result['failed'] = True

        result['ansible_facts'] = {
                'syncthing_pre': config,
        }

        return result
