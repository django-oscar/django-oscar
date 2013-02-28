#!/usr/bin/env python
"""
Installation script:

To release a new version to PyPi:
- Ensure the version is correctly set in oscar.__init__.py
- Run: python setup.py sdist upload
"""

from setuptools import setup, find_packages
import os
import sys

from oscar import get_version

PROJECT_DIR = os.path.dirname(__file__)

# Change to the current directory to solve an issue installing Oscar on the
# Vagrant machine.
if PROJECT_DIR:
    os.chdir(PROJECT_DIR)

setup(name='django-oscar',
      version=get_version().replace(' ', '-'),
      url='https://github.com/tangentlabs/django-oscar',
      author="David Winterbottom",
      author_email="david.winterbottom@tangentlabs.co.uk",
      description="A domain-driven e-commerce framework for Django",
      long_description=open(os.path.join(PROJECT_DIR, 'README.rst')).read(),
      keywords="E-commerce, Django, domain-driven",
      license='BSD',
      platforms=['linux'],
      packages=find_packages(exclude=["sandbox*", "tests*"]),
      include_package_data=True,
      install_requires=[
          'django>=1.4,<1.5',
          'PIL==1.1.7',
          'South>=0.7.6,<0.8',
          'django-extra-views>=0.2,<0.6',
          'django-haystack==2.0.0-beta',
          'django-treebeard>=1.61,<1.62',
          'sorl-thumbnail==11.12',
          'python-memcached>=1.48,<1.49',
          'Babel>=0.9,<0.10',
          'django-compressor>=1.2,<1.3',
          'virtual-node>=0.0.1',
          'virtual-less>=0.0.1-1.3.3'],
      dependency_links=['https://github.com/toastdriven/django-haystack/tarball/0e95d8696f8ba770f9c60152136aba32f5591fd6#egg=django-haystack-2.0.0-beta'],
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Django',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: Unix',
          'Programming Language :: Python',
          'Topic :: Other/Nonlisted Topic']
      )

# Show contributing instructions if being installed in 'develop' mode
if len(sys.argv) > 1 and sys.argv[1] == 'develop':
    url = 'http://django-oscar.readthedocs.org/en/latest/contributing.html'
    msg = (
        "You're installing Oscar in 'develop' mode so I presume you're thinking\n"
        "of contributing:\n\n"
        "(a) That's brilliant - thank you for your time\n"
        "(b) If you have any questions, please use the mailing list:\n    django-oscar@googlegroups.com\n"
        "(c) There are more detailed contributing guidelines that you should "
        "have a look at:\n    %s\n\nHappy hacking!") % url
    line = '=' * 82
    print "\n%s\n%s\n%s" % (line, msg, line)
