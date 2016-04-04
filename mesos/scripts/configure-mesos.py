#!/usr/bin/env python

"""
Reconfigures a Jenkins master with mesos & credential data
"""

import os
import os.path as path
import xml.etree.ElementTree as ET


def fixtures_path():
    """
    Returns the jenkins conf absolute path
    """
    return path.abspath(path.join(path.dirname(path.realpath(__file__)), "..", "conf", "jenkins"))


def populate_jenkins_config_xml(config_xml, master, name, sysid):
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

    slave_agentPort = root.find('./slaveAgentPort')
    slave_agentPort.text = "0"

    credentials_id = root.find('./credentialsId')
    if credentials_id is None:
        ET.SubElement(mesos, 'credentialsId').text = sysid
    else:
        credentials_id.text = sysid

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


def configure(opts):
    """
    Either add or remove the clouds config from the config.xml
    """
    config_path = path.join(opts.workspace, 'config.xml')
    cloud_fixture_path = path.join(fixtures_path(), 'clouds.xml')
    try:
        if opts.mesos_master is not None:
            sysid = "" if opts.sysid is None else opts.sysid
            add_jenkins_cloud_config_xml(config_path, cloud_fixture_path)
            populate_jenkins_config_xml(config_path,
                                        opts.mesos_master,
                                        opts.framework_name,
                                        sysid)
        else:
            remove_jenkins_cloud_config_xml(config_path)
        return 0
    except:
        return 1


def main(argv=None):
    """
    Setup CLI
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace",
                        default=os.getcwd(),
                        help="Where the Jenkins configuration is located. "
                             "Defaults to cwd (%s)" % os.getcwd())
    parser.add_argument("--framework-name",
                        default="ci-jenkins",
                        help="Name of Jenkins provided to mesos.")
    parser.add_argument("--mesos-master",
                        help="Mesos master URL.")
    parser.add_argument("--sysid",
                        help="Credential ID of mesos framework username & password.")
    options = parser.parse_args(argv)
    return configure(options)


if __name__ == '__main__':
    import sys
    sys.path.insert(0, ".")
    sys.exit(main())
