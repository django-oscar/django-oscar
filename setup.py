#!/usr/bin/env python
"""
Installation script:

To release a new version to PyPi:
- Ensure the version is correctly set in oscar.__init__.py
- Run: python setup.py sdist upload
"""

from setuptools import setup, find_packages

from oscar import get_version


setup(name='django-oscar',
      version=get_version().replace(' ', '-'),
      url='https://github.com/tangentlabs/django-oscar',
      author="David Winterbottom",
      author_email="david.winterbottom@tangentlabs.co.uk",
      description="A domain-driven e-commerce framework for Django 1.3+",
      long_description=open('README.rst').read(),
      keywords="E-commerce, Django, domain-driven",
      license='BSD',
      platforms=['linux'],
      packages=find_packages(exclude=["sandbox*", "tests*"]),
      include_package_data=True,
      install_requires=[
          'django>=1.4',
          'PIL==1.1.7',
          'South==0.7.3',
          'django-extra-views==0.2.0',
          'django-haystack==2.0.0-beta',
          'django-treebeard==1.61',
          'sorl-thumbnail==11.12',
          'python-memcached==1.48',
          'django-sorting==0.1',
          ],
      dependency_links=['http://github.com/toastdriven/django-haystack/tarball/master#egg=django-haystack-2.0.0-beta'],
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: Unix',
                   'Programming Language :: Python']
      )
