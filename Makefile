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
	yum install -y jenkins libffi-devel openssl-devel
	which python || yum install -y python
	which pip || yum install -y python-pip
	cd /opt && git clone https://github.com/behance/chamberlain && \
	    cd chamberlain && make && cd -
	sed -i.bak s/JENKINS_USER=\"jenkins\"/JENKINS_USER=\"root\"/g /etc/sysconfig/jenkins

clean:
	git add .
	git reset --hard
	git clean -ffdx jobs
	rm -rf templates credentials* secret*
