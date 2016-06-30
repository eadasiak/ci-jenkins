FROM java:8u45-jdk

ENV DOCKER_VERSION 1.9.1
ENV JENKINS_SWARM_VERSION 2.1
ENV HOME /usr/share/jenkins

# install Docker first
RUN apt-get update && \
  apt-get install -y -q apt-transport-https ca-certificates
RUN apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D && \
  mkdir -p /etc/apt/sources.list.d && \
  echo deb https://apt.dockerproject.org/repo ubuntu-trusty main > /etc/apt/sources.list.d/docker.list && \
  apt-get update && \
  apt-get install -y -q docker-engine=$DOCKER_VERSION-0~trusty net-tools && \
  rm -rf /var/lib/apt/lists/*

# install the Jenkins Swarm Agent
RUN curl --create-dirs -sSLo /usr/share/jenkins/swarm-client-$JENKINS_SWARM_VERSION-jar-with-dependencies.jar http://maven.jenkins-ci.org/content/repositories/releases/org/jenkins-ci/plugins/swarm-client/$JENKINS_SWARM_VERSION/swarm-client-$JENKINS_SWARM_VERSION-jar-with-dependencies.jar && \
  chmod 755 /usr/share/jenkins

COPY jenkins-slave.sh /usr/local/bin/jenkins-slave.sh

ENTRYPOINT ["/usr/local/bin/jenkins-slave.sh"]
