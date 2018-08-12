FROM centos/python-36-centos7:latest
USER root
RUN  yum install -y git

# Add The App
RUN mkdir /app
ADD . /app

WORKDIR /app
# Install Depenencies
RUN pip3 install pip --upgrade
RUN pip3 install -r requirements.txt

# Create the directory for the repo so that it stores the mounts file
RUN mkdir -p /config/nfs_mounts

CMD ["ssh-keyscan -t rsa $REPO_URI >> /root/.ssh/known_hosts", "&",  "git", "clone", "$REPO_SSH_URI", "/config/nfs_mounts"]
#Start the app on build
CMD [ "python3", "main.py" ]
EXPOSE 5000           
