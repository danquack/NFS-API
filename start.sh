#!/bin/bash
git clone $REPO_SSH_URI /config/nfs_mounts
gunicorn --workers 4 --bind 0.0.0.0:80 --log-level=info main:app