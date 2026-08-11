#!/usr/bin/env python
import os
import sys
import subprocess

from setuptools.command import build as build_module
from setuptools import setup, find_packages

PROJECT_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(PROJECT_DIR, "src"))

from oscar import get_version  # noqa isort:skip


install_requires = [
    'django==5.1.3',
    # PIL is required for image fields, Pillow is the "friendly" PIL fork
    'pillow>=6.0',
    # We use the ModelFormSetView from django-extra-views for the basket page
    'django-extra-views>=0.13,<0.15',
    # Search support
    'django-haystack>=3.0b1',
    # Treebeard is used for categories
    'django-treebeard>=4.3.0',
    # Babel is used for currency formatting
    'Babel>=1.0,<3.0',
    # For manipulating search URLs
    'purl>=0.7',
    # For phone number field
    'phonenumbers',
    'django-phonenumber-field>=4.0.0,<7.0.0',
    # Used for oscar.test.factories
    'factory-boy>=3.0,<3.3',
    # Used for automatically building larger HTML tables
    'django-tables2>=2.3,<2.4',
    # Used for manipulating form field attributes in templates (eg: add
    # a css class)
    'django-widget-tweaks>=1.4.1',
]

sorl_thumbnail_version = 'sorl-thumbnail>=12.6,<12.7'
easy_thumbnails_version = 'easy-thumbnails>=2.7,<2.8'

docs_requires = [
    'Sphinx>=4.2,<4.3',
    'sphinxcontrib-napoleon==0.7',
    'sphinxcontrib-spelling==7.2.1',
    'sphinx_rtd_theme==1.0.0',
    'sphinx-issues==1.2.0',
    sorl_thumbnail_version,
    easy_thumbnails_version,
]


class BuildNPM(build_module.build):
    def run(self):
        subprocess.check_call(["npm", "install"])
        subprocess.check_call(["npm", "run", "build"])
        super().run()


setup(
    cmdclass={"build": BuildNPM},
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    version=get_version(),
)
