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
          'django>=1.4.2,<1.7',
          # PIL is required for image fields, Pillow is the "friendly" PIL fork
          'pillow>=1.7.8,<2.3',
          # Oscar ships with migrations
          'South>=0.7.6,<0.9',
          # We use the ModelFormSetView from django-extra-views for the basket
          # page
          'django-extra-views>=0.2,<0.7',
          'django-haystack>=2.0.0',
          # Treebeard is used for categories
          'django-treebeard==2.0b2',
          # Sorl is used as the default thumbnailer
          'sorl-thumbnail==11.12',
          # Babel is used for currency formatting
          'Babel>=1.0',
          # Oscar's default templates use compressor (but you can override
          # this)
          'django-compressor>=1.2',
          # For converting non-ASCII to ASCII when creating slugs
          'Unidecode>=0.04.12,<0.05',
          # For manipulating search URLs
          'purl>=0.7',
          # For phone number field
          'phonenumbers==5.9.2'
      ],
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
    docs_url = 'http://django-oscar.readthedocs.org/en/latest/internals/contributing/index.html'
    mailing_list = 'django-oscar@googlegroups.com'
    mailing_list_url = 'https://groups.google.com/forum/?fromgroups#!forum/django-oscar'
    twitter_url = 'https://twitter.com/django_oscar'
    msg = (
        "You're installing Oscar in 'develop' mode so I presume you're thinking\n"
        "of contributing:\n\n"
        "(a) That's brilliant - thank you for your time\n"
        "(b) If you have any questions, please use the mailing list:\n    %s\n"
        "    %s\n"
        "(c) There are more detailed contributing guidelines that you should "
        "have a look at:\n    %s\n"
        "(d) Consider following @django_oscar on Twitter to stay up-to-date\n"
        "    %s\n\nHappy hacking!") % (mailing_list, mailing_list_url,
                                       docs_url, twitter_url)
    line = '=' * 82
    print "\n%s\n%s\n%s" % (line, msg, line)
