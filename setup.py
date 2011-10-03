try:
    from setuptools import setup, find_packages
except:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import sys, os

version = '100'

setup(name='repacked',
      version=version,
      description="repacked is a simple way to build multiple deb/RPM packages from a single directoryy",
      long_description=open("README").read(),
      classifiers=[
         'Development Status :: 3 - Alpha',
         'Environment :: Console',
         'Intended Audience :: Developers',
         'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
         'Programming Language :: Python',
         'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords='',
      author='Jonathan Prior',
      author_email='jjprior@736cs.com',
      url='https://github.com/736/repacked/',
      license='LGPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      scripts=["repacked/repacked.py"],
      package_data={'repacked': ['plugins/*.plugin', 'templates/*.tmpl']},
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'mako', 'yapsy'
      ],
)
