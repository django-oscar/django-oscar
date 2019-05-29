#!/usr/bin/env python
"""
Installation script:

To release a new version to PyPi:
- Ensure the version is correctly set in oscar.__init__.py
- Run: make release
"""
import os
import re
import sys

from setuptools import find_packages, setup

PROJECT_DIR = os.path.dirname(__file__)

sys.path.append(os.path.join(PROJECT_DIR, 'src'))
from oscar import get_version  # noqa isort:skip

install_requires = [
    'django>=1.11,<2.3',
    # PIL is required for image fields, Pillow is the "friendly" PIL fork
    'pillow>=4.0',
    # We use the ModelFormSetView from django-extra-views for the basket page
    'django-extra-views>=0.11,<0.12',
    # Search support
    'django-haystack>=2.5.0,<3.0.0',
    # Treebeard is used for categories
    'django-treebeard>=4.3.0',
    # Babel is used for currency formatting
    'Babel>=1.0,<3.0',
    # For manipulating search URLs
    'purl>=0.7',
    # For phone number field
    'phonenumbers',
    'django-phonenumber-field>=2.0,<2.1',
    # Used for oscar.test.newfactories
    'factory-boy>=2.4.1,<3.0',
    # Used for automatically building larger HTML tables
    'django-tables2>=1.19,<2.0',
    # Used for manipulating form field attributes in templates (eg: add
    # a css class)
    'django-widget-tweaks>=1.4.1',
]

sorl_thumbnail_version = 'sorl-thumbnail>=12.4.1,<12.5'
easy_thumbnails_version = 'easy-thumbnails==2.5'

docs_requires = [
    'Sphinx==2.0.1',
    'sphinxcontrib-napoleon==0.7',
    'sphinx_rtd_theme==0.4.3',
    'sphinx-issues==1.2.0',
    sorl_thumbnail_version,
    easy_thumbnails_version,
]

test_requires = [
    'WebTest>=2.0,<2.1',
    'coverage>=4.5,<4.6',
    'django-webtest==1.9.4',
    'py>=1.4.31',
    'psycopg2>=2.7,<2.8',
    'pytest>=4.0,<4.5',
    'pytest-cov==2.6.1',
    'pytest-django==3.4.8',
    'pytest-xdist>=1.25,<1.28',
    'tox>=3.0,<3.9',
    sorl_thumbnail_version,
    easy_thumbnails_version,
]

with open(os.path.join(PROJECT_DIR, 'README.rst')) as fh:
    long_description = re.sub(
        '^.. start-no-pypi.*^.. end-no-pypi', '', fh.read(), flags=re.M | re.S)

setup(
    name='django-oscar',
    version=get_version(),
    url='https://github.com/django-oscar/django-oscar',
    author="David Winterbottom",
    author_email="david.winterbottom@gmail.com",
    description="A domain-driven e-commerce framework for Django",
    long_description=long_description,
    keywords="E-commerce, Django, domain-driven",
    license='BSD',
    platforms=['linux'],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'docs': docs_requires,
        'test': test_requires,
        'sorl-thumbnail': [sorl_thumbnail_version],
        'easy-thumbnails': [easy_thumbnails_version],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Application Frameworks']
)

# Show contributing instructions if being installed in 'develop' mode
if len(sys.argv) > 1 and sys.argv[1] == 'develop':
    docs_url = 'https://django-oscar.readthedocs.io/en/latest/internals/contributing/index.html'
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
