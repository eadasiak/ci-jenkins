#!/usr/bin/env python2
"""
Reconfigures a Jenkins master running in Docker at container runtime.
"""

from __future__ import print_function
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


def is_firstrun(jenkins_home_dir):
    """A small helper utility to determine if this is the first run of this
    bootstrap script. Checks to see if the 'jenkins_home_dir' directory
    is empty, or if it contains existing data.

    :param jenkins_home_dir: the path to $JENKINS_HOME on disk
    :return: boolean; True if $JENKINS_HOME isn't populated, false otherwise
    """
    if os.path.isfile(os.path.join(jenkins_home_dir, 'clouds.xml')):
        return False
    return True

def is_marathon():
    """Checks a set of environment variables to determine if the Jenkins instance
    is being launched via Marathon (and thus should load the Jenkins Mesos framework),
    or if it is running as a standalone.  This combination of environment variables is
    automatically assigned via Marathon.
    """

    if os.getenv('HOST') == None and os.getenv('PORT0') == None and os.getenv('PORT1') == None:
        return False
    else:
        return True

def populate_jenkins_config_xml(config_xml, master, name, host, port):
    """Modifies a Jenkins master's 'config.xml' at runtime. Essentially, this
    replaces certain configuration options of the Mesos plugin, such as the
    framework name and the Jenkins URL that agents use to connect back to the
    master.

    :param config_xml: the path to Jenkins' 'config.xml' file
    :param name: the name of the framework, e.g. 'jenkins'
    :param host: the Mesos agent the task is running on
    :param port: the Mesos port the task is running on
    """
    tree = ET.parse(config_xml)
    root = tree.getroot()
    mesos = root.find('./clouds/org.jenkinsci.plugins.mesos.MesosCloud')

    mesos_master = mesos.find('./master')
    mesos_master.text = master

    mesos_frameworkName = mesos.find('./frameworkName')
    mesos_frameworkName.text = name

    mesos_jenkinsURL = mesos.find('./jenkinsURL')
    mesos_jenkinsURL.text = ''.join(['http://', host, ':', port])

    slave_agentPort = root.find('./slaveAgentPort')
    slave_agentPort.text = "0"

    tree.write(config_xml)

def remove_jenkins_cloud_config_xml(config_xml):
    """Modifies a Jenkins master's config.xml at runtime.  It removes the tree
    under the 'clouds' section so that Jenkins can operate as a standalone instance.
    """
    tree = ET.parse(config_xml)
    root = tree.getroot()

    mesos = root.find('./clouds')
    for cloud in mesos:
        mesos.remove(cloud)

    tree.write(config_xml)

def add_jenkins_cloud_config_xml(config_xml, cloud_xml):
    """Modifies a Jenkins master's config.xml at runtime to merge the Mesos cloud_xml
    configuration into the base config.xml.
    """
    tree = ET.parse(config_xml)
    root = tree.getroot()

    clouds_tree = ET.parse(cloud_xml)
    clouds_root = clouds_tree.getroot()

    cloud_config = root.find('./clouds')
    cloud_config.append(clouds_root)

    tree.write(config_xml)


def populate_jenkins_location_config(location_xml, host, port):
    """Modifies a Jenkins master's location config at runtime. Essentially,
    this replaces the value of 'jenkinsUrl' with a newly constructed URL
    based on the host and port that the Marathon app instance is running on.

    :param location_xml: the path to Jenkins'
        'jenkins.model.JenkinsLocationConfiguration.xml' file
    :param host: the Mesos agent the task is running on
    :param port: the Mesos port the task is running on
    """
    tree = ET.parse(location_xml)
    root = tree.getroot()
    jenkinsUrl = root.find('jenkinsUrl')
    jenkinsUrl.text = ''.join(['http://', host, ':', port])
    tree.write(location_xml)


def remove_jenkins_location_config(location_xml):
    """Removes the location config for a standalone instance
    """
    os.remove(location_xml)


def populate_nginx_config(config_file, nginx_port, jenkins_port, context):
    """Modifies an nginx config, replacing the "magic" strings
    '_XNGINX_PORT', '_XJENKINS_PORT' and '_XJENKINS_CONTEXT' with the real
    value provided.

    :param config_file: the path to an 'nginx.conf'
    :param nginx_port: the Mesos port the task is running on
    :param jenkins_port: the Mesos port the task is running on
    :param context: the application's context, e.g. '/service/jenkins'
    """
    original = None
    with open(config_file, 'r') as f:
        original = f.readlines()

    with open(config_file, 'w') as f:
        for line in original:
            if re.match(r'.*_XNGINX_PORT.*', line):
                f.write(re.sub('_XNGINX_PORT', nginx_port, line))
            elif re.match(r'.*_XJENKINS_PORT.*', line):
                f.write(re.sub('_XJENKINS_PORT', jenkins_port, line))
            elif re.match(r'.*_XJENKINS_CONTEXT.*', line):
                f.write(re.sub('_XJENKINS_CONTEXT', context, line))
            else:
                f.write(line)


def populate_known_hosts(hosts, dest_file):
    """Gather SSH public key from one or more hosts and write out the
    known_hosts file.

    :param hosts: a string of hosts separated by whitespace
    :param dest_file: absolute path to the SSH known hosts file
    """
    dest_dir = os.path.dirname(dest_file)

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    command = ['ssh-keyscan'] + hosts.split()
    subprocess.call(
        command, stdout=open(dest_file, 'w'), stderr=open(os.devnull, 'w'))


def main():

    # Bootstrapping steps for Mesos-enabled Jenkins in Marathon
    try:
        jenkins_staging_dir = os.environ['JENKINS_STAGING']
        jenkins_home_dir = os.environ['JENKINS_HOME']
        ssh_known_hosts = os.environ['SSH_KNOWN_HOSTS']
        jenkins_framework_name = os.environ['JENKINS_FRAMEWORK_NAME']
        jenkins_app_context = os.environ['JENKINS_CONTEXT']
        mesos_master = os.environ['JENKINS_MESOS_MASTER']


    except KeyError:
        # Since each of the environment variables above are set in the marathon
        # app definition, the user should never get to this point.
        print("ERROR: missing one or more required environment variables.")
        return 1

    marathon_host = os.getenv('HOST') or os.getenv('JENKINS_HOST')
    marathon_nginx_port = os.getenv('PORT0') or os.getenv('NGINX_PORT')
    marathon_jenkins_port = os.getenv('PORT1') or os.getenv('JENKINS_PORT')

    # If this is the first run of the script, make changes to the staging
    # directory first, so we can then use these files to populate the host
    # volume. If data exists in that directory (e.g. Marathon has restarted
    # a Jenkins master task), then we'll make changes in-place to the existing
    # data without overwriting anything the user already has.
    firstrun = is_firstrun(jenkins_home_dir)
    jenkins_data_dir = jenkins_staging_dir if firstrun else jenkins_home_dir

    add_jenkins_cloud_config_xml(
        os.path.join(jenkins_data_dir, 'config.xml'),
        os.path.join(jenkins_data_dir, 'clouds.xml'))


    # If running under Marathon, utilize the nginx proxy port to communicate back to Jenkins
    # Otherwise, bypass and directly connect to the Jenkins port
    if is_marathon():

        populate_jenkins_config_xml(
            os.path.join(jenkins_data_dir, 'config.xml'),
            mesos_master,
            jenkins_framework_name,
            marathon_host,
            marathon_nginx_port)

        populate_jenkins_location_config(os.path.join(
            jenkins_data_dir, 'jenkins.model.JenkinsLocationConfiguration.xml'),
            marathon_host, marathon_nginx_port)
    else:

        populate_jenkins_config_xml(
            os.path.join(jenkins_data_dir, 'config.xml'),
            mesos_master,
            jenkins_framework_name,
            marathon_host,
            marathon_jenkins_port)

        populate_jenkins_location_config(os.path.join(
            jenkins_data_dir, 'jenkins.model.JenkinsLocationConfiguration.xml'),
            marathon_host, marathon_jenkins_port)


    populate_known_hosts(ssh_known_hosts, '/etc/ssh/ssh_known_hosts')


    # os.rename() doesn't work here because the destination directory is
    # actually a mount point to the volume on the host. shutil.move() here
    # also doesn't work because of some weird recursion problem.
    #
    # TODO(roger): figure out how to implement this in Python.
    #
    if firstrun:
        subprocess.call("/bin/mv {src}/* {dst}/.".format(
            src=jenkins_staging_dir, dst=jenkins_home_dir), shell=True)


    # nginx changes here are really "run once". The context should never
    # change as long as a Jenkins instance is alive, since the rewrite will
    # be based on the app ID in Marathon, as will the volume on disk.
    populate_nginx_config(
        '/etc/nginx/nginx.conf',
        marathon_nginx_port,
        marathon_jenkins_port,
        jenkins_app_context)


if __name__ == '__main__':
    sys.exit(main())
