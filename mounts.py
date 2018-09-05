"""
:contributors
- Daniel Quackenbush
"""
import logging
import uuid
from os.path import join
from os import environ
import yaml
from git import Git


class ExistsException(Exception):
    """
    An Already Exist Exception.
    Extends exception but allows for catching
    """
    pass


class Mounts:
    """
    The Mounts class is the class that does all the ETL from git to updating the file
    ** This is the magic sauce behind the api
    """
    def __init__(self, app):
        """
        Initilize mounts class by loading yaml into a variable
        :input app - flask app
        """
        self.app = app
        self.git = Git(environ['GIT_DIRECTORY'])
        self.git.pull()
        self.nfs_file = join(environ['GIT_DIRECTORY'], 'data/common.yaml')
        with open(self.nfs_file) as yaml_file:
            self.nfs_info = yaml.safe_load(yaml_file.read())
            if not self.nfs_info:
                raise Exception('error loading mounts file')

    def commit(self, hostname, option):
        """
        Commits the codes and pushes back to git
        :input hostname - name changed
        :input option - option changed
        """
        self.app.logger.info(f"successfully {option} for {hostname}")
        self.update_current()
        try:
            self.git.add(self.nfs_file)
            self.git.commit('-m', f"'updated - {option} for {hostname}'")
            self.git.push()
        except Exception as exc:
            if 'nothing to commit' in str(exc):
                raise Exception('No changes made')
            else:
                raise exc

    def check_exists(self, host_type, name, mount) -> bool:
        """
        Check if the mount exists
        :input host_type - hosts/hostgroups
        :input name - name of the host or hostgroup
        :input mount - the mount option
        :return boolean if exists
        """
        try:
            for temp_mount in self.nfs_info[f"nfs_mounts::{host_type}"][name]:
                unmatched_item = set(temp_mount.items()) ^ set(mount.items())
                if unmatched_item and dict(
                        unmatched_item) and 'uuid' in dict(unmatched_item).keys():
                    return True
        except Exception as exc:
            self.app.logger.warning(exc)

        return False

    def update_current(self):
        """
        Writes to file
        """
        with open(self.nfs_file, 'w') as yaml_file:
            to_write = yaml.dump(self.nfs_info, default_flow_style=False)
            yaml_file.write(to_write)

    def add_nas_share(
            self,
            local_path,
            share_path,
            options,
            owner,
            group,
            host=None,
            hostgroup=None):
        """
        Add a new NAS Share to a host/hostgroup
        """
        if not host and not hostgroup:
            raise Exception('Missing host and hostgroup')
        else:
            host_type = 'hosts' if host else 'hostgroups'
            name = host if host else hostgroup
            if not self.nfs_info[f"nfs_mounts::{host_type}"]:
                self.nfs_info[f"nfs_mounts::{host_type}"] = {}

            if name.lower(
            ) not in self.nfs_info[f"nfs_mounts::{host_type}"].keys():
                self.app.logger.info(f"{name}: has no mounts...appending")
                self.nfs_info[f"nfs_mounts::{host_type}"].update({name: []})

            self.app.logger.info(
                self.nfs_info[f"nfs_mounts::{host_type}"].keys())
            mount = {
                'uuid': str(uuid.uuid4()),
                'local_path': local_path,
                'share_path': share_path,
                'options': options,
                'owner': owner,
                'group': group
            }
            if not self.check_exists(host_type, name, mount):
                self.app.logger.info(f"{name}: adding {mount}")
                self.nfs_info[f"nfs_mounts::{host_type}"][name].append(mount)
                self.commit(name, 'add')
                return self.nfs_info[f"nfs_mounts::{host_type}"][name]
            else:
                raise ExistsException('mount point already exists')

    def update_nas_share(
            self,
            uuid_num,
            replacement_dict,
            host=None,
            hostgroup=None):
        """
        Modify an existing new NAS Share to a host/hostgroup
        """
        if not host and not hostgroup:
            raise Exception('Missing host and hostgroup')
        else:
            host_type = 'hosts' if host else 'hostgroups'
            name = host if host else hostgroup

            changed = False
            for idx, val in enumerate(
                    self.nfs_info[f"nfs_mounts::{host_type}"][name]):
                if uuid_num == val['uuid']:
                    self.nfs_info[f"nfs_mounts::{host_type}"][name][idx].update(
                        replacement_dict)
                    self.app.logger.info(f"{name}: updating {uuid_num}")
                    changed = True
            if not changed:
                raise IndexError('no index matching that uuid found')
            self.commit(name, 'added')
            return self.nfs_info[f"nfs_mounts::{host_type}"][name]

    def delete_host_name(self, name, host_type):
        """
        Remove a host/hostgroup
        """
        del self.nfs_info[f"nfs_mounts::{host_type}"][name]
        if host_type == 'hostgroups':
            self.commit(name, 'deleted hostgroup')
        else:
            self.commit(name, 'deleted host')

    def delete_host_mount(self, name, host_type, uuid_num):
        """
        Remove an existing new NAS mount from a host/hostgroup
        """
        self.nfs_info[f"nfs_mounts::{host_type}"][name] = [
            x for x in self.nfs_info[f"nfs_mounts::{host_type}"][name] if x['uuid'] != uuid_num]
        self.commit(name, 'deleted mount')
        return self.nfs_info[f"nfs_mounts::{host_type}"][name]
