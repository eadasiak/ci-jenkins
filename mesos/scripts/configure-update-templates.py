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


def add_scm(xmlfile, sshurl, rsa_id):
    tree = ET.parse(xmlfile)
    scmroot = tree.getroot().find("scm/userRemoteConfigs")
    scm = ET.SubElement(scmroot, "hudson.plugins.git.UserRemoteConfig")
    scm_url = ET.SubElement(scm, "url")
    scm_url.text = sshurl
    scm_cred_id = ET.SubElement(scm, "credentialsId")
    scm_cred_id.text = rsa_id
    tree.write(xmlfile)


def merge_config(orig_path, injection_path):
    tree = ET.parse(orig_path)
    root = tree.getroot()
    inject_tree = ET.parse(injection_path)
    for node in inject_tree.findall("./"):
        root.append(node)
    tree.write(orig_path)


def clean_config(job_cfg_path, fixtures_path):
    """
    Just remove top level nodes that are common between fixtures
    and target
    """
    tree = ET.parse(job_cfg_path)
    root = tree.getroot()
    inject_tree = ET.parse(fixtures_path)
    for node in inject_tree.getroot():
        srcnode = root.find("./%s" % node.tag)
        if srcnode is not None:
            root.remove(srcnode)
    tree.write(job_cfg_path)


def configure_xml(opts):
    config_path = path.join(opts.workspace,
                            "jobs",
                            "update-templates",
                            "config.xml")
    clean_config(config_path, fixtures_path())
    merge_config(config_path, fixtures_path())
    for template_repo in opts.sshurls:
        add_scm(config_path, template_repo, opts.rsaid)


def main(argv=None):
    """
    Setup CLI
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("rsaid",
                        help="Jenkins ID of RSA SSH key credential.")
    parser.add_argument("sshurls",
                        nargs="*",
                        default=[],
                        help="list of SSH URLs of repos that can be read by rsaid.")
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
