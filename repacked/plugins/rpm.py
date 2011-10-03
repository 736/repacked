from __future__ import print_function
from pkg_resources import resource_string
from yapsy.IPlugin import IPlugin
from mako.template import Template
from mako import exceptions

import os
import distutils.dir_util
import shutil
import tempfile
import re
import sys

tmpl_dir = os.path.join(os.path.dirname(__file__),'../../repacked/templates')

class PRMPackager(IPlugin):
    def __init__(self):
        self.spec = {}
        self.package = {}
        self.output_dir = ""
        self.tmpdir = ""
    
    def checkarch(self, architecture):
        if architecture == "32-bit":
            architecture = "i386"
        elif architecture == "64-bit":
            architecture = "x86_64"
            
        return architecture

    def filenamegen(self, package):
        """
        Generates a nice simple filename for a package
        based on its package info
        """
        
        spec = self.spec

        filename = "{name}_{version}_{architecture}.rpm".format(
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
        self.output_dir = output

        ## Create directories

        # Create the temporary folder
        self.tmpdir = tmpdir = tempfile.mkdtemp()
        
        # Create the directory holding the program files
        program_files = os.path.join(tmpdir, "BUILD")
        os.mkdir(program_files)

        # Copy across the contents of the file tree
        distutils.dir_util.copy_tree(spec['packagetree'], program_files)

        print("RPM package tree created in {0}".format(tmpdir))

        ## Create RPM spec file

        cf = open(os.path.join(tmpdir, "rpm.spec"), "w")
        
        cf_template = Template(filename=os.path.join(tmpl_dir, "rpmspec.tmpl"))
        
        # Create file list
        filelist = []
        for root, subfolders, files in os.walk(program_files):
            for folder in subfolders:
                filelist.append('%dir "{0}"'.format(os.path.join(root, folder).replace(program_files, "")))
            for file in files:
                filelist.append('"{0}"'.format(os.path.join(root, file).replace(program_files, "")))
        
        # Collect the install scripts
        try:
            scripts = spec['scripts']
        except:
            # No installation scripts
            scripts = None
        
        scriptdata = {}

        if scripts:
            for app in scripts.iteritems():
                script = app[0]
                filename = app[1]
                
                if os.path.isfile(filename):
                    with open(filename, "r") as f:
                        scriptdata[script] = f.readlines()

                        if scriptdata[script][0].startswith("#!"):
                            del scriptdata[script][0]
                        
                        scriptdata[script] = "".join(scriptdata[script])
                else:
                    print("Installation script {0} not found.".format(script))
        
        # Render the spec file from template
        cf_final = cf_template.render(
            package_name=spec['name'],
            version=spec['version'],
            maintainer=spec['maintainer'],
            summary=spec['summary'],
            description=spec['description'],
            dependencies=package.get('requires'),
            architecture=self.checkarch(package['architecture']),
            file_list=filelist,
            license="N/A",
            output_dir=os.path.abspath(self.output_dir),
            build_dir=tmpdir,

            # Install scripts
            prein=scriptdata.get('preinst'),
            postin=scriptdata.get('postinst'),
            preun=scriptdata.get('prerm'),
            postun=scriptdata.get('postrm'),
        )
        
        cf.write(cf_final)
        cf.close()
        
        return tmpdir

    def build(self, directory, filename):
        """
        Builds a RPM package from the directory tree
        """

        directory = os.path.join(directory, "BUILD")

        os.system("fakeroot rpmbuild -bb --buildroot={buildroot} --target={architecture} {specfile}".format(
            architecture=self.checkarch(self.package['architecture']),
            buildroot=directory,
            specfile=os.path.abspath(os.path.join(self.tmpdir, "rpm.spec"))
        ))