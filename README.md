# syncthing

This ansible role handles the installation and configuration of [syncthing](https://syncthing.net/).

## Introduction

I wanted a role to install and configure syncthing for me and did not find an existing one that satisfied me. I had a few mandatory features in mind:
- the ability to configure a servers parameters in only one place to avoid repetition
- having a fact that retrieves the ID of a device
- the validation of host_vars which virtually no role in the wild ever does
- the ability to manage an additional inventory file for devices which ansible cannot manage (like my phone)

## Dependencies

This role relies on `doas` being installed and configured so that your ansible user can run the syncthing cli as the syncthing user.

Here is an example of a `doas.conf` that works for the ansible user:
```yaml
permit  nopass  ansible  as  syncthing
```

## Role variables

There is a single variable to specify in the `host_vars` of your hosts: `syncthing`. This is a dict that can contain the following keys:
- address: optional string to specify how to connect to the server, must match the format `tcp://<hostname>` or `tcp://<ip>`. Default value is *dynamic* which means a passive host.
- shared: a mandatory dict describing the directories this host shares, which can contain the following keys:
  - name: a mandatory string to name the share in the configuration. It must match on all devices that share this folder.
  - path: the path of the folder on the device. This can differ on each device sharing this data.
  - peers: a list a strings. Each item should be either the `ansible_hostname` of another device, or a hostname from the `syncthing_data.yaml` file

Configuring a host through its `host_vars` looks like this:
```yaml
syncthing:
  address: tcp://lore.adyxax.org
  shared:
    - name: org-mode
      path: /var/syncthing/org-mode
      peers:
        - hero
        - light
        - lumapps
        - Pixel 3a
```

## The optional syncthing_data.yaml file

To be found by the `action_plugins`, this file should be in the same folder as your playbook. It shares the same format as the `host_vars` but with additional keys for the hostname and its ID.

The data file for non ansible devices looks like this:
```yaml
- name: Pixel 3a
  id: ABCDEFG-HIJKLMN-OPQRSTU-VWXYZ01-2345678-90ABCDE-FGHIJKL-MNOPQRS
  shared:
    - name: Music
      path: /storage/emulated/0/Music
      peers:
        - phoenix
    - name: Photos
      path: /storage/emulated/0/DCIM/Camera
      peers:
        - phoenix
    - name: org-mode
      path: /storage/emulated/0/Org
      peers:
        - lore.adyxax.org
```

## Example playbook

```yaml
- hosts: all
  roles:
    -  {  role:  syncthing, tags: [ 'syncthing' ], when: "syncthing is defined" }
```
