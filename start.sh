#!/bin/bash
git clone $REPO_SSH_URI $GIT_DIRECTORY
gunicorn --workers 4 --bind 0.0.0.0:5000 --log-level=info main:app