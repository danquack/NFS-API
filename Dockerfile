FROM python-36-centos7:latest
RUN yum install -y git

# Add The App
RUN mkdir /app
ADD . /app

# Install Depenencies
RUN pip3 install -r app/requirements.txt

# TODO: Configure SSH

# Clone The Repo that stores the mounts file
RUN mkdir -p /config/nfs_mounts
RUN git clone <mounts.yml repo> /config/nfs_mounts

#Start the app on build
CMD [ "python3", "/app/main.py" ]
EXPOSE 5000
