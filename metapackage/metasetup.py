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

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

sys.path.append(os.path.join(PROJECT_DIR, 'src'))
from oscar import get_version  # noqa isort:skip

OSCAR_VERSION = get_version().replace(' ', '-')
install_requires = [
    'oscar==%s' % OSCAR_VERSION,
    'django>=1.11,<2.2',
    # PIL is required for image fields, Pillow is the "friendly" PIL fork
    'pillow>=4.0',
    # We use the ModelFormSetView from django-extra-views for the basket page
    'django-extra-views>=0.11,<0.12',
    # Search support
    'django-haystack>=2.5.0,<3.0.0',
    # Treebeard is used for categories
    'django-treebeard>=4.3.0',
    # Sorl is used as the default thumbnailer
    'sorl-thumbnail>=12.4.1,<12.5',
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

with open(os.path.join(PROJECT_DIR, 'README.rst')) as fh:
    long_description = re.sub(
        '^.. start-no-pypi.*^.. end-no-pypi', '', fh.read(), flags=re.M | re.S)

setup(
    name='django-oscar',
    version=OSCAR_VERSION,
    url='https://github.com/django-oscar/django-oscar',
    author="David Winterbottom",
    author_email="david.winterbottom@gmail.com",
    description="A domain-driven e-commerce framework for Django",
    long_description=long_description,
    keywords="E-commerce, Django, domain-driven",
    license='BSD',
    platforms=['linux'],
    package_dir=None,
    packages=[],
    py_modules=[],
    include_package_data=False,
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Application Frameworks']
)
