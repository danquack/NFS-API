FROM centos/python-36-centos7:latest
USER root
RUN  yum install -y git

ENV GIT_SSH_COMMAND="ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

# Add The App
RUN mkdir /app
ADD . /app

WORKDIR /app
# Install Depenencies
RUN pip3 install pip --upgrade
RUN pip3 install -r requirements.txt

# Create the directory for the repo so that it stores the mounts file
RUN mkdir -p /config

#Start the app on build
CMD ["bash", "start.sh"]

EXPOSE 5000