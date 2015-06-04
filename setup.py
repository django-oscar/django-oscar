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

PROJECT_DIR = os.path.dirname(__file__)
PY3 = sys.version_info >= (3, 0)

sys.path.append(os.path.join(PROJECT_DIR, 'src'))
from oscar import get_version

setup(name='django-oscar',
      version=get_version().replace(' ', '-'),
      url='https://github.com/django-oscar/django-oscar',
      author="David Winterbottom",
      author_email="david.winterbottom@gmail.com",
      description="A domain-driven e-commerce framework for Django",
      long_description=open(os.path.join(PROJECT_DIR, 'README.rst')).read(),
      keywords="E-commerce, Django, domain-driven",
      license='BSD',
      platforms=['linux'],
      package_dir={'': 'src'},
      packages=find_packages('src'),
      include_package_data=True,
      install_requires=[
          'django>=1.7.8,<1.9',
          # PIL is required for image fields, Pillow is the "friendly" PIL fork
          'pillow>=1.7.8,<=2.7',
          # We use the ModelFormSetView from django-extra-views for the basket
          # page. 0.6.5 pins version of six, which causes issues:
          # https://github.com/AndrewIngram/django-extra-views/pull/85
          'django-extra-views>=0.2,<0.6.5',
          # Search support
          'django-haystack>=2.3.1,<2.4.0',
          # Treebeard is used for categories
          'django-treebeard>=3.0',
          # Sorl is used as the default thumbnailer
          'sorl-thumbnail>=11.12.1b,<=12.2',
          # Babel is used for currency formatting
          'Babel>=1.0,<1.4',
          # Oscar's default templates use compressor (but you can override
          # this)
          'django-compressor>=1.4',
          # For converting non-ASCII to ASCII when creating slugs
          'Unidecode>=0.04.12,<0.05',
          # For manipulating search URLs
          'purl>=0.7',
          # For phone number field
          'phonenumbers>=6.3.0,<7.0.0',
          # Used for oscar.test.contextmanagers.mock_signal_receiver
          'mock>=1.0.1,<1.1',
          # Used for oscar.test.newfactories
          'factory-boy>=2.4.1,<2.5',
          # Used for automatically building larger HTML tables
          'django-tables2>=1.0.4,<1.1',
          # Used for manipulating form field attributes in templates (eg: add
          # a css class)
          'django-widget-tweaks>=1.3,<1.4',
      ],
      dependency_links=[],
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Web Environment',
          'Framework :: Django',
          'Framework :: Django :: 1.7',
          'Framework :: Django :: 1.8',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: Unix',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Topic :: Software Development :: Libraries :: Application Frameworks']
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
    print(("\n%s\n%s\n%s" % (line, msg, line)))
