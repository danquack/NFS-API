#!/bin/bash
git clone $REPO_SSH_URI $GIT_DIRECTORY
cd $GIT_DIRECTORY
git fetch --all && git checkout "${BRANCH:-master}"
git config --global user.name "NFS API"
git config --global user.email "nfsapi@yourdomain.com"
cd /app
gunicorn --workers 4 --bind 0.0.0.0:5000 --log-level=info main:app