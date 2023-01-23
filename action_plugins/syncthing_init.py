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
                    'id': '',
                    'shared': [],
                }
                if 'address' in syncthing.keys():
                    peer['address'] = syncthing['address']
                for shared in syncthing['shared']:
                    peer['shared'].append({ 'name': shared['name'], 'path': shared['path'], 'peers': shared['peers']})
                if 'ansible_local' in hostvars and 'syncthing' in hostvars['ansible_local']:
                    peer['id'] = hostvars['ansible_local']['syncthing']['id']
                peers[hostname] = peer

        ### Compiling host configuration ######################################
        config = {}
        if task_vars['ansible_host'] in peers.keys():
            myself = peers[task_vars['ansible_host']]
            config = {
                'peers': {},
                'shared': myself['shared'],
            }
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
