import logging
import yaml
import uuid
from os.path import join
import git


class ExistsException(Exception):
    pass

class Mounts:
    nfs_repo_files = '/config/nfs_mounts/files/'
    def __init__(self, app):
        self.app = app
        self.git = git.cmd.Git(self.nfs_repo_files)
        self.git.pull()
        file_path = join(self.nfs_repo_files, 'mounts.yml')
        with open(file_path) as yaml_file:
            self.nfs_info = yaml.safe_load(yaml_file.read())

    def commit(self, hostname, option):
        self.app.logger.info(f"successfully {option} for {hostname}")
        self.update_current()
        file_path = join(self.nfs_repo_files, 'mounts.yml')
        self.git.add(file_path)
        try:
            self.git.commit('-m', f"'updated - {option} for {hostname}'")
            self.git.push()
        except Exception as e:
            if 'nothing to commit' in str(e):
                raise Exception('No changes made')
            else:
                raise e


    def check_exists(self, mount_type, name, mount):
        for temp_mount in self.nfs_info[mount_type][name]:
            unmatched_item = set(temp_mount.items()) ^ set(mount.items())
            ## If the only difference is uuid
            if len(unmatched_item) is 1 and 'uuid' in dict(unmatched_item).keys():
                return True
        return False

    def update_current(self):
        file_path = join(self.nfs_repo_files, 'test.yml')
        with open(file_path,'w') as yaml_file:
            to_write = yaml.dump(self.nfs_info, default_flow_style=False)
            yaml_file.write(to_write)

    def add_nas_share(self, local_path, share_path, options, owner, group, host=None, hostgroup=None):
        if not host and not hostgroup:
            raise Exception('Missing host and hostgroup')
        else:
            host_type = 'hosts' if host else 'hostgroups'
            name = host if host else hostgroup
            if name.lower() not in self.nfs_info[host_type].keys():
                self.app.logger.info(f"{name}: has no mounts...appnding")
                self.nfs_info[host_type].update( {name: [] })

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
                self.nfs_info[host_type][name].append(mount)
                self.commit(name, 'add')
                return self.nfs_info[host_type][name]
            else:
                raise ExistsException('mount point already exists')
    def update_nas_share(self, uuid_num, replacement_dict, host=None, hostgroup=None):
        if not host and not hostgroup:
            raise Exception('Missing host and hostgroup')
        else:
            host_type = 'hosts' if host else 'hostgroups'
            name = host if host else hostgroup

            changed = False
            for idx, val in enumerate(self.nfs_info[host_type][name]):
                if uuid_num == val['uuid']:
                    self.nfs_info[host_type][name][idx].update(replacement_dict)
                    self.app.logger.info(f"{name}: updating {uuid_num}")
                    changed = True
            if not changed:
                raise IndexError('no index matching that uuid found')
            self.commit(name, 'added')
            return self.nfs_info[host_type][name]

    def delete_host_name(self, name, host_type):
        del self.nfs_info[host_type][name]
        if host_type == 'hostgroups':
            self.commit(name, 'deleted hostgroup')
        else:
            self.commit(name, 'deleted host')
    def delete_host_mount(self, name, host_type, uuid_num):
        self.nfs_info[host_type][name] = [x for x in self.nfs_info[host_type][name] if x['uuid'] != uuid_num]
        self.commit(name, 'deleted mount')
        return self.nfs_info[host_type][name]

