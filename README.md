[![Build Status](https://travis-ci.org/danquack/NFS-API.svg?branch=master)](https://travis-ci.org/danquack/NFS-API)

The NFS API was designed to manage a mounts.yml file within nfs_mounts mounts puppet repo. This Python3 application is dockerized and posts to bitbucket using ssh keys embeded into the container.

# Structure:
```
main.py - flask application that defines the endpoints
mounts.py - the behind the scenes worker to read and update the mounts file
requirements.txt - pip3 install -r requirements.txt - will install the necesary packages needed to run the app
```

# Install Instructions
1. Clone Project
2. Modify git user profile configuration in dockerfile
2. Run `docker build -t nfs_api:latest .`
3. Run
```
docker run \
-e REPO_URI=<full ssh git (ex. git@github.com:someuser/NFS-MOUNTS.git)> \
-v /path/to/ssh/on/host:/root/.ssh \
-e GIT_DIRECTORY=/path/to/store/repo
-p 5000:5000 \
nfs_api:latest
```
4. Interact with the api on your servers ip address on port 80.

# Context
### API
<table>
    <tr>
        <th>HTTP method</th>
        <th>URI path</th>
        <th>Description</th>
    </tr>
    <tr>
        <td>GET</td>
        <td>/</td>
        <td>Returns health status to show node is active</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/mounts</td>
        <td>Retrieves all mounts</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/mounts/hosts, /mounts/hostgroups</td>
        <td>Retrieves just [hostname/hostgroup] mount.</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/mounts/[hosts/hostgroups]/[servername/hostgroupname]</td>
        <td>Retrieves servers/hostgroups mounts</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/mounts/[hosts/hostgroups]/[servername/hostgroupname]/uuid</td>
        <td> Retrieves invidiual mount point for given UUID</td>
    </tr>
    <tr>
        <td>POST/PUT</td>
        <td>/mounts/[hosts/hostgroups]</td>
        <td>Create new NAS Point for a particular host or hostgroup</td>
    </tr>
    <tr>
        <td>PATCH</td>
        <td>/mounts/[hosts/hostgroups]/[servername/hostgroupname]/uuid</td>
        <td>Modifies a NAS Point for a particular host or hostgroup</td>
    </tr>
    <tr>
        <td>DELETE</td>
        <td>/mounts/[hosts/hostgroups]/[servername/hostgroupname]</td>
        <td>Removes the management for a particular host or hostgroup</td>
    </tr>
    <tr>
        <td>DELETE</td>
        <td>/mounts/[hosts/hostgroups]/[servername/hostgroupname]/uuid</td>
        <td>Removes the management of a NAS Point for a particular host or hostgroup</td>
    </tr>
</table>

### YAML File:
The structure of the yaml defines an array of mount objects, located in the external REPO_SSH_URI (NFS-Mounts under a files directory), is as follows
```
Hosts:
   Hostname.company.com:
    -	uuid
        share_path
        local_path
        options
        owner
        group
   Hostname2.company.com:
    -	...
Hostgroups:
    Group1:
    -	uuid
        share_path
        local_path
        options
        owner
        group
    -	...
     Group2
    ...
```
