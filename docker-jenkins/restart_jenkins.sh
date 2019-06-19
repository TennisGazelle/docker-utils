#/bin/bash
# you might need to run this as admin
if [ ! -d "/opt/docker/jenkins/jenkins_home" ]; then
    mkdir -p /opt/docker/jenkins/jenkins_home
fi

if [ ! -w "/opt/docker/jenkins/jenkins_home" ]; then
    chmod 777 /opt/docker/jenkins/jenkins_home
fi

docker stop jenkins;
docker rm jenkins;
docker run --name jenkins -i -d -p 8787:8080 -p 50000:50000 -v /opt/docker/jenkins/jenkins_home:/var/jenkins_home:rw local_jenkins