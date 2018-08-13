#!/bin/bash
ssh-keyscan $REPO_URI >> /root/.ssh/known_hosts
git clone $REPO_SSH_URI /config/nfs_mounts
python3 main.py