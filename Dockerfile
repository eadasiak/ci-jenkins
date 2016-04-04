FROM jenkins:1.642.2

USER root

RUN apt-get update && apt-get install -y build-essential python-pip lsb-release
RUN git clone https://github.com/behance/chamberlain /opt/chamberlain \
    && cd /opt/chamberlain && make && cd -

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv E56151BF && \
    echo "deb http://repos.mesosphere.io/$(lsb_release -is | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) main"|tee /etc/apt/sources.list.d/mesosphere.list && \
    apt-get update && \
    apt-get install -y mesos

USER jenkins
ADD . /var/jenkins_home
