#!/usr/bin/python

"""
repacked - dead simple package creation
"""

from __future__ import print_function
from pkg_resources import resource_string
from yapsy.PluginManager import PluginManager

__author__ = "Jonathan Prior"
__copyright__ = "Copyright 2011, 736 Computing Services Limited"
__license__ = "LGPL"
__version__ = "101"
__maintainer__ = "Jonathan Prior"
__email__ = "jjprior@736cs.com"

import optparse
import yaml
import os
import sys
import tempfile
import distutils.dir_util
import shutil
import logging

plugin_dir = os.path.join(os.path.dirname(__file__),'../../repacked/plugins')
pkg_plugins = {}

pluginMgr = PluginManager(plugin_info_ext="plugin")
pluginMgr.setPluginPlaces([plugin_dir])
pluginMgr.locatePlugins()
pluginMgr.loadPlugins()

for pluginInfo in pluginMgr.getAllPlugins():
   pluginMgr.activatePluginByName(pluginInfo.name)

def parse_spec(filename):
    """
    Loads the YAML file into a Python object for parsing
    and returns it
    """

    fp = open(filename, 'r')
    spec = yaml.safe_load("\n".join(fp.readlines()))

    return spec

def build_packages(spec, output):
    """
    Loops through package specs and call the package
    builders one by one
    """

    packages = spec['packages']
    tempdirs = []

    # Eventually replace this with a plugin system
    # with scripts to create build trees for different
    # packages
    for package in packages:
        try:
            builder = pkg_plugins[package['package']]
        except KeyError:
            builder = None
            print("Module {0} isn't installed. Ignoring this package and continuing.".format(package['package']))
        
        if builder:
            directory = builder.plugin_object.tree(spec, package, output)
            builder.plugin_object.build(directory, builder.plugin_object.filenamegen(package))
            tempdirs.append(directory)
        
    return tempdirs

def clean_up(dirs):
    """
    Delete the temporary build trees to save space
    """
    for fldr in dirs:
        shutil.rmtree(fldr, ignore_errors=True)

def main():
    """
    Set up the application
    """

    parser = optparse.OptionParser(description="Creates deb and RPM packages from files defined in a package specification.",
                                   prog="packager", version=__version__, usage="%prog [path to package specification]")
    parser.add_option('--outputdir', '-o', default='.', help="packages will be placed in the specified directory")
    parser.add_option('--no-clean', action="store_true", help="Don't remove temporary files used to build packages")
    options, arguments = parser.parse_args()

    # Parse the specification
    spec = parse_spec(arguments[0])

    # Import the plugins
    print("Enumerating plugins...")

    for plugin in pluginMgr.getAllPlugins():
        print("Found plugin {name}".format(name=plugin.name))
        pkg_plugins[plugin.name] = plugin
    
    # Create build trees based on the spec
    print("Building packages...")
    tempdirs = build_packages(spec, options.outputdir)

    # Clean up old build trees
    if not options.no_clean:
        print("Cleaning up...")
        clean_up(tempdirs)

if __name__ == "__main__":
    main()