#!/bin/bash
git clone $REPO_SSH_URI /config/nfs_mounts
gunicorn -w 4 main:app -b 0.0.0.0:80