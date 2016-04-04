#!/usr/bin/env python2

"""
Add/Update configurations for Github Plugins (GithubPlugin & GHPRBuilder)
"""
import os
import os.path as path
from copy import copy
from xml.etree import ElementTree as ET

GHPR_FILE = "org.jenkinsci.plugins.ghprb.GhprbTrigger.xml"
GHPR_XML_PATH = "githubAuth/org.jenkinsci.plugins.ghprb.GhprbGitHubAuth"
GHPR_URL_KEY = "serverAPIUrl"

SCM_FILE = "github-plugin-configuration.xml"
SCM_XML_PATH = "configs/github-server-config"
SCM_URL_KEY = "apiUrl"


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


def plugin_params(name):
    if name == "ghpr":
        return (GHPR_FILE, GHPR_XML_PATH, GHPR_URL_KEY)
    elif name == "github":
        return (SCM_FILE, SCM_XML_PATH, SCM_URL_KEY)
    raise "Unknown plugin: %s" % name


def configure_xml(opts):
    (file, xml_path, url_key) = plugin_params(opts.plugin)
    config_path = path.join(opts.workspace, file)
    injections = {
        url_key: opts.apiurl,
        "credentialsId": opts.sysid
    }
    XMLFile(config_path).inject(root=xml_path, injections=injections)
    

def main(argv=None):
    """
    Setup CLI
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("plugin",
                        help="{github, ghpr} - former is for PUSH triggers, latter is for PRs")
    parser.add_argument("sysid",
                        help="System ID of OAuth token credential.")
    parser.add_argument("apiurl",
                        default="https://api.github.com",
                        help="Github API URL")
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
