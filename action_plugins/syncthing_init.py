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

        ### Syncthing variables for non ansible hosts #########################
        peers = {}
        with open('syncthing_data.yaml') as f:
            data = yaml.load(f, Loader=SafeLoader)
            for peer in data:
                peers[peer['name']] = peer
                if not 'address' in peer.keys():
                    peer['address'] = 'dynamic'

        ### Syncthing host vars ###############################################
        for hostname, hostvars in task_vars['hostvars'].items() :
            if 'syncthing' in hostvars.keys():
                syncthing = hostvars['syncthing']
                peer = {
                    'address': 'dynamic',
                    'id': '0000000-0000000-0000000-0000000-0000000-0000000-0000000-0000000',
                    'shared': [],
                }
                if 'address' in syncthing.keys():
                    peer['address'] = syncthing['address']
                for shared in syncthing['shared']:
                    peer['shared'].append({ 'name': shared['name'], 'path': shared['path'], 'peers': shared['peers']})
                if 'syncthing' in hostvars['ansible_local']:
                    peer['id'] = hostvars['ansible_local']['syncthing']['id']
                peers[hostname] = peer

        ### Compiling host configuration ######################################
        config = {}
        if task_vars['ansible_host'] in peers.keys():
            myself = peers[task_vars['ansible_host']]
            config = {
                'config_path': "",
                'folders_to_create': [],
                'packages': [],
                'peers': {},
                'service': "syncthing",
                'shared': myself['shared'],
                'user_group': "syncthing",
            }
            if task_vars['ansible_distribution'] == 'FreeBSD':
                config['config_path'] = "/usr/local/etc/syncthing/config.xml"
                config['folders_to_create'] = ["/usr/local/etc/syncthing/", "/var/syncthing"]
                config['packages'] = ["p5-libwww", "syncthing"]
            elif task_vars['ansible_distribution'] == 'Gentoo':
                config['config_path'] = "/var/lib/syncthing/.config/syncthing/config.xml"
                config['folders_to_create'] = ["/var/lib/syncthing/.config/syncthing"]
                config['packages'] = ["net-p2p/syncthing"]
            else:
                error_msgs.append(f"syncthing role does not support {task_vars['ansible_distribution']} hosts yet")
            for shared in myself['shared']:
                for peer in shared['peers']:
                    if not peer in config['peers'].keys():
                        config['peers'][peer] = { 'id': peers[peer]['id'], 'address': peers[peer]['address'] }

        ### Results compilation ##############################################
        if error_msgs != []:
            result['msg'] = ' ; '.join(error_msgs)
            result['failed'] = True

        result['ansible_facts'] = {
                'syncthing_config': config,
        }

        return result
