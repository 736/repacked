from __future__ import print_function
from pkg_resources import resource_string
from yapsy.IPlugin import IPlugin
from mako.template import Template

import os
import distutils.dir_util
import shutil
import tempfile
import re
import sys

tmpl_dir = os.path.join(os.path.dirname(__file__),'../../repacked/templates')

class DebianPackager(IPlugin):
    def __init__(self):
        self.spec = {}
        self.package = {}
        self.output_dir = ""
    
    def checkarch(self, architecture):
        if architecture == "32-bit":
            architecture = "i386"
        elif architecture == "64-bit":
            architecture = "amd64"
            
        return architecture

    def filenamegen(self, package):
        """
        Generates a nice simple filename for a package
        based on its package info
        """

        spec = self.spec

        filename = "{name}_{version}_{architecture}.deb".format(
            name=spec['name'],
            version=spec['version'],
            architecture=self.checkarch(package['architecture']),
        )

        return filename
    
    def tree(self, spec, package, output):
        """
        Builds a debian package tree
        """
        
        self.spec = spec
        self.package = package
        self.output = output
        
        ## Create directories

        # Create the temporary folder
        tmpdir = tempfile.mkdtemp()
        
        # Create the directory holding control files
        os.mkdir(os.path.join(tmpdir, "DEBIAN"))

        # Copy across the contents of the file tree
        distutils.dir_util.copy_tree(spec['packagetree'], tmpdir)

        print("Debian package tree created in {0}".format(tmpdir))

        ## Create control file

        cf = open(os.path.join(tmpdir, "DEBIAN", "control"), "w")
        
        cf_template = Template(filename=os.path.join(tmpl_dir, "debcontrol.tmpl"))
        
        cf_final = cf_template.render(
            package_name=spec['name'],
            version=spec['version'],
            architecture=self.checkarch(package['architecture']),
            maintainer=spec['maintainer'],
            size=os.path.getsize(tmpdir),
            summary=spec['summary'],
            description="\n .\n ".join(re.split(r"\n\s\s*", spec['description'].strip())),
            dependencies=package.get('requires'),
            predepends=package.get('predepends'),
            replaces=package.get('replaces'),
            provides=package.get('provides'),
            conflicts=package.get('conflicts'),
        )

        cf.write(cf_final)
        cf.close()
        
        ## Check for lintian overrides and add them to the build tree
        overrides = package.get('lintian-overrides')
        
        if overrides:
            lint_tmpl = "{package}: {override}\n"
            lintfile = ""
            
            overrides = overrides.split(",")
            
            for o in overrides:
                override = o.strip()
                lintfile += lint_tmpl.format(package=spec['name'], override=override)
            
            try:
                os.makedirs(os.path.join(tmpdir, "usr/share/lintian/overrides"))
                do_overrides = True
            except:
                # Directory exists, skip it
                do_overrides = False
            
            if do_overrides:
                lf = open(os.path.join(tmpdir, "usr/share/lintian/overrides", spec['name']))
                lf.write(lintfile)
                lf.close()
                
        ## Copy over installation scripts
        
        try:
            scripts = spec['scripts']
        except:
            # No installation scripts
            scripts = None
        
        if scripts:
            for app in scripts.iteritems():
                script = app[0]
                filename = app[1]
                
                if os.path.isfile(filename):
                    shutil.copy(filename, os.path.join(tmpdir, "DEBIAN"))
                    os.chmod(os.path.join(tmpdir, "DEBIAN", script), 0755)
                else:
                    print("Installation script {0} not found.".format(script))
        
        return tmpdir

    def build(self, directory, filename):
        """
        Builds a deb package from the directory tree
        """

        filename = os.path.join(self.output_dir, filename)
        os.system("fakeroot dpkg-deb --build {0} {1}".format(directory, filename))
