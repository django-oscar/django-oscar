# -*- coding: utf-8 -*-
import json

from setuptools import find_packages, setup

install_requires: list = ["django-oscar", " django-oscar-elasticsearch", "whitenoise", "sorl-thumbnail", "setuptools>60"]


PACKAGE_CLASSIFIERS = [
    "License :: OSI Approved :: BSD License",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "Private :: Do Not Upload",
]

setup(
    name="oscarsandbox",
    version="0.0.1",
    url="https://latest.oscarcommerce.com",
    author="Anima Colenses",
    description="Oscar sandbox project",
    package_dir={
        "oscarsandbox": ".",
    },
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=install_requires,
    entry_points={"console_scripts": ["manage.py=oscarsandbox.manage:main"]},
    classifiers=PACKAGE_CLASSIFIERS,
)
