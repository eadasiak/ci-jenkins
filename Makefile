default: dev

dev:
	docker run --net=host --rm -ti \
	-v $${HOME}/.ssh:/mnt/.ssh:ro  \
	-v $$(pwd):/var/jenkins_home   \
	-e RUNNING_HOST=127.0.0.1      \
	-e RUNNING_USER=$$(whoami)     \
	-e DEVELOPMENT="true"          \
	-u root                        \
	-p 8080:8080                   \
	adobeplatform/ci-jenkins

dev-mesos:
	docker run --net=host --rm -ti                    \
	-v $${HOME}/.ssh:/mnt/.ssh:ro                     \
	-e DEVELOPMENT="true"                             \
	-e JENKINS_FRAMEWORK_NAME=jenkins                 \
	-e JENKINS_MESOS_MASTER=zk://zookeeper:2181/mesos \
	-e JENKINS_HOST=$$(hostname -i)                   \
	-e JENKINS_CONTEXT=""                             \
	-u root                                           \
	adobeplaform/ci-jenkins:mesos

provisioner:
	docker run --net=host --rm -ti \
	-v $${HOME}/.ssh:/mnt/.ssh:ro  \
	-v $$(pwd):/var/jenkins_home   \
	-e RUNNING_HOST=127.0.0.1      \
	-e RUNNING_USER=$$(whoami)     \
	-e TEMPLATE_GIT_URL            \
	-e TEMPLATE_LIB_GIT_URL        \
	-e PROVISIONER=true            \
	-u root                        \
	-p 8080:8080                   \
	adobeplatform/ci-jenkins

reader:
	docker run --net=host --rm -ti \
	-v $${HOME}/.ssh:/mnt/.ssh:ro  \
	-v $$(pwd):/var/jenkins_home   \
	-e RUNNING_HOST=127.0.0.1      \
	-e RUNNING_USER=$$(whoami)     \
	-e TEMPLATE_GIT_URL            \
	-e TEMPLATE_LIB_GIT_URL        \
	-u root                        \
	-p 8080:8080                   \
	adobeplatform/ci-jenkins

# obviously, you're going to need to clone this repo first
# 		git clone git@github.com:adobe-platform/ci-jenkins <YOUR JENKINS HOME>
# TODO: probably should just be a placeholder for a chef cookbook
cent:
	sudo wget -O /etc/yum.repos.d/jenkins.repo http://pkg.jenkins-ci.org/redhat/jenkins.repo
	sudo rpm --import https://jenkins-ci.org/redhat/jenkins-ci.org.key
	yum install -y java jenkins libffi-devel openssl-devel
	which python || yum install -y python
	which pip || rpm -iUvh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-5.noarch.rpm && yum -y install python-pip
	cd /opt && git clone https://github.com/behance/chamberlain && \
	    cd chamberlain && make && cd -
	sed -i.bak s/JENKINS_USER=\"jenkins\"/JENKINS_USER=\"root\"/g /etc/sysconfig/jenkins
	# a hack because our internal infra doesn't allow writing to /tmp for some reason
	sed -i 's/^JENKINS_JAVA_OPTIONS=.*/JENKINS_JAVA_OPTIONS=\"-Djava.awt.headless=true -Djava.io.tmpdir=$$JENKINS_HOME\/tmp\"/' /etc/sysconfig/jenkins
	mkdir /var/lib/jenkins/tmp

clean:
	git add .
	git reset --hard
	git clean -ffdx jobs
	rm -rf templates credentials* secret*
