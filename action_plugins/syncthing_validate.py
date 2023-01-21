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

        ### syncthing_data.yaml file validation ###############################
        peers = {}
        with open('syncthing_data.yaml') as f:
            data = yaml.load(f, Loader=SafeLoader)
            if not isinstance(data, list):
                error_msgs.append(f"The syncthing_data.yaml file must contain a list")
            else:
                for peer in data:
                    if not isinstance(peer, dict):
                        error_msgs.append(f"syncthing_data.yaml must contain a list of dicts")
                    else:
                        for key in peer.keys():
                            if not key in ['address', 'id', 'name', 'shared']:
                                error_msgs.append(f"Invalid key {key} in dict for syncthing_data.yaml entry")
                        if 'address' in peer.keys():
                            if not isinstance(peer['address'], str):
                                error_msgs.append(f"Invalid address in syncthing_data.yaml, must be of type string")
                            elif re.match('^tcp://', peer['address']) == None:
                                error_msgs.append(f"Invalid address in syncthing_data.yaml, must be of format tcp://<hostname or ip address>/")
                        if 'id' in peer.keys():
                            if not isinstance(peer['id'], str):
                                error_msgs.append(f"Invalid id in syncthing_data.yaml, must be of type string")
                            elif re.match('^(?:[A-Z0-9]{7}-){7}[A-Z0-9]{7}$', peer['id']) == None:
                                error_msgs.append(f"Invalid id in syncthing_data.yaml, must be of valid")
                        if 'name' in peer.keys():
                            if not isinstance(peer['name'], str):
                                error_msgs.append(f"Invalid name in syncthing_data.yaml, must be of type string")
                            elif not re.match('^[A-Za-z0-9\.]+$', peer['name']) == None:
                                error_msgs.append(f"Invalid name in syncthing_data.yaml, must be name a valid hostname")
                        if 'shared' in peer.keys():
                            # TODO validate shared and populate peers
                            pass

        ### host_vars validations #############################################
        for hostname, hostvars in task_vars['hostvars'].items() :
            if 'syncthing' in hostvars.keys():
                if not isinstance(task_vars['syncthing'], dict):
                    error_msgs.append(f"The syncthing variable must be of type dict for host {hostname}")
                else:
                    syncthing = hostvars['syncthing']
                    for key in syncthing.keys():
                        if not key in ['address', 'shared']:
                            error_msgs.append(f"Invalid key {key} in the syncthing dict for host {hostname}")
                    peer = {
                        'address': 'dynamic',
                        'shared': [],
                    }
                    if 'address' in syncthing.keys():
                        if not isinstance(syncthing['address'], str):
                            error_msgs.append(f"Invalid address for host {hostname}: must be of type string")
                        elif re.match('^tcp://', syncthing['address']) == None:
                            error_msgs.append(f"Invalid address for host {hostname}: must be of format tcp://<hostname or ip address>/")
                        else:
                            peer['address'] = syncthing['address']
                    if 'shared' not in syncthing.keys():
                        error_msgs.append(f"Invalid syncthing entry for host {hostname}: no shared key in dict")
                    elif not isinstance(syncthing['shared'], list):
                        error_msgs.append(f"Invalid shared syncthing entry for host {hostname}: must be of type list")
                    elif len(syncthing['shared']) == 0:
                        error_msgs.append(f"Invalid shared syncthing entry for host {hostname}: must be a non empty list")
                    else:
                        for shared in syncthing['shared']:
                            if not isinstance(shared, dict):
                                error_msgs.append(f"Invalid shared syncthing entry for host {hostname}: shared needs to be a dict")
                            else:
                                for key in shared.keys():
                                    if not key in ['name', 'path', 'peers']:
                                        error_msgs.append(f"Invalid key {key} in the shared syncthing array for host {hostname}")
                                if 'name' not in shared.keys():
                                    error_msgs.append(f"Invalid shared syncthing entry for host {hostname}: no name key in dict")
                                elif not isinstance(shared['name'], str):
                                    error_msgs.append(f"Invalid shared name for host {hostname}: must be of type string")
                                #elif not shared['name'] in task_vars['hostvars']:
                                #    error_msgs.append(f"Invalid shared name for host {hostname}: must be an ansible host, or defined in syncthing_data.yaml")
                                # TODO keep validating each key

        ### Results compilation ##############################################
        if error_msgs != []:
            result['msg'] = ' ; '.join(error_msgs)
            result['failed'] = True

        return result

