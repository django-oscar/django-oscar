#!/usr/bin/env python
"""
Installation script:

To release a new version to PyPi:
- Ensure the version is correctly set in oscar.__init__.py
- Run: make release
"""
import os
import re
import subprocess
import sys

from setuptools.command import build as build_module
from setuptools import setup, find_packages

PROJECT_DIR = os.path.dirname(__file__)

sys.path.append(os.path.join(PROJECT_DIR, "src"))
from oscar import get_version  # noqa isort:skip


class BuildNPM(build_module.build):
    def run(self):
        subprocess.check_call(["npm", "install"])
        subprocess.check_call(["npm", "run", "build"])
        super().run()


install_requires = [
    "setuptools>=62.4.0",
    "django>=3.2,<5.2",
    # PIL is required for image fields, Pillow is the "friendly" PIL fork
    "pillow>=6.0",
    # We use the ModelFormSetView from django-extra-views for the basket page
    "django-extra-views>=0.13,<0.15",
    # Search support
    "django-haystack>=3.0b1",
    # Treebeard is used for categories
    "django-treebeard>=4.3.0",
    # Babel is used for currency formatting
    "Babel>=1.0,<3.0",
    # For manipulating search URLs
    "purl>=0.7",
    # For phone number field
    "phonenumbers",
    "django-phonenumber-field>=4.0.0,<9.0.0",
    # Used for oscar.test.factories
    "factory-boy>=3.3.1,<4.0.0",
    # Used for automatically building larger HTML tables
    "django-tables2>=2.3,<2.8",
    # Used for manipulating form field attributes in templates (eg: add
    # a css class)
    "django-widget-tweaks>=1.4.1",
]

sorl_thumbnail_version = "sorl-thumbnail>=12.10.0,<13.0.0"
easy_thumbnails_version = "easy-thumbnails>=2.9,<2.10"

docs_requires = [
    "Sphinx>=5.0",
    "sphinxcontrib-spelling==7.5.1",
    "sphinx_rtd_theme==1.0.0",
    "sphinx-issues==3.0.1",
    sorl_thumbnail_version,
    easy_thumbnails_version,
]

test_requires = [
    "Whoosh>=2.7,<2.8",
    "WebTest>=3.0.0,<4.0.0",
    "coverage>=7.6.1,<8.0.0",
    "django-webtest>=1.9,<1.10",
    "psycopg2-binary>=2.8,<2.10",
    "pytest-django>=4.9.0,<5.0",
    "pytest-xdist>=3.6.1,<4.0.0",
    "tox>=4.18.0,<5.0.0",
    "freezegun>=1.5.1,<2.0.0",
    "pytz",
    "vdt.versionplugin.wheel",
    sorl_thumbnail_version,
    easy_thumbnails_version,
]

with open(os.path.join(PROJECT_DIR, "README.rst"), encoding="utf-8") as fh:
    long_description = re.sub(
        "^.. start-no-pypi.*^.. end-no-pypi", "", fh.read(), flags=re.M | re.S
    )

setup(
    name="django-oscar",
    version=get_version(),
    url="https://github.com/django-oscar/django-oscar",
    author="David Winterbottom",
    author_email="david.winterbottom@gmail.com",
    description="A domain-driven e-commerce framework for Django",
    long_description=long_description,
    keywords="E-commerce, Django, domain-driven",
    license="BSD",
    platforms=["linux"],
    include_package_data=True,
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require={
        "docs": docs_requires,
        "test": test_requires,
        "sorl-thumbnail": [sorl_thumbnail_version],
        "easy-thumbnails": [easy_thumbnails_version],
    },
    cmdclass={"build": BuildNPM},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
)

# Show contributing instructions if being installed in 'develop' mode
if len(sys.argv) > 1 and sys.argv[1] == "develop":
    docs_url = "https://django-oscar.readthedocs.io/en/latest/internals/contributing/index.html"
    mailing_list = "django-oscar@googlegroups.com"
    mailing_list_url = "https://groups.google.com/forum/?fromgroups#!forum/django-oscar"
    twitter_url = "https://twitter.com/django_oscar"
    msg = (
        "You're installing Oscar in 'develop' mode so I presume you're thinking\n"
        "of contributing:\n\n"
        "(a) That's brilliant - thank you for your time\n"
        "(b) If you have any questions, please use the mailing list:\n    %s\n"
        "    %s\n"
        "(c) There are more detailed contributing guidelines that you should "
        "have a look at:\n    %s\n"
        "(d) Consider following @django_oscar on Twitter to stay up-to-date\n"
        "    %s\n\nHappy hacking!"
    ) % (mailing_list, mailing_list_url, docs_url, twitter_url)
    line = "=" * 82
    print(("\n%s\n%s\n%s" % (line, msg, line)))
