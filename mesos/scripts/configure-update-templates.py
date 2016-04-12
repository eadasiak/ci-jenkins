#!/usr/bin/env python2

"""
Update the update-templates job so that it has a on-push hook
"""
import os
import os.path as path
from copy import copy
from xml.etree import ElementTree as ET


def fixtures_path():
    """
    Returns the jenkins conf absolute path
    """
    return path.abspath(
        path.join(path.dirname(path.realpath(__file__)),
                  "..",
                  "conf",
                  "jenkins",
                  "update-templates.xml"))


class XMLFile:
    def __init__(self, path):
        self.path = copy(path)
        self.tree = ET.parse(self.path)

    def inject(self, root = ".", injections = {}):
        baseTree = self.tree.getroot().find(root)
        for (node, val) in injections.iteritems():
            relative_node = "./%s" % node
            childTree = baseTree.find(relative_node)
            if childTree is None:
                ET.SubElement(baseTree, node).text = val
                continue
            childTree.text = val
        self.tree.write(self.path)


def inject_scm(xmlfile, sshurl, rsa_id):
    gitscm_root = "scm/userRemoteConfigs/hudson.plugins.git.UserRemoteConfig"
    injections = {
        "url": sshurl,
        "credentialsId": rsa_id
    }
    xmlfile.inject(root=gitscm_root, injections=injections)


def merge_config(orig_path, injection_path):
    tree = ET.parse(orig_path)
    root = tree.getroot()
    inject_tree = ET.parse(injection_path)
    for node in inject_tree.findall("./"):
        root.append(node)
    tree.write(orig_path)


def configure_xml(opts):
    config_path = path.join(opts.workspace,
                            "jobs",
                            "update-templates",
                            "config.xml")
    merge_config(config_path, fixtures_path())
    jobconfig = XMLFile(config_path)
    inject_scm(jobconfig, opts.sshurl, opts.rsaid)


def main(argv=None):
    """
    Setup CLI
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("sshurl",
                        help="SSH URL of repo that we want push notifications from.")
    parser.add_argument("rsaid",
                        help="Jenkins ID of RSA SSH key credential.")
    parser.add_argument("--workspace",
                        default=os.getcwd(),
                        help="Where the Jenkins configuration is located. "
                             "Defaults to cwd (%s)" % os.getcwd())
    options = parser.parse_args(argv)
    return configure_xml(options)


if __name__ == '__main__':
    import sys
    sys.path.insert(0, ".")
    sys.exit(main())
