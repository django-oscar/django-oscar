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
          'django>=1.4,<1.5',
          # PIL is required for image fields, Pillow is the "friendly" PIL fork
          'pillow>=>=1.7.8,<2.3',
          'South>=0.7.6,<0.8',
          'django-extra-views>=0.2,<0.6',
          'django-haystack==2.0.0',
          'django-treebeard==1.61',
          'sorl-thumbnail==11.12',
          'python-memcached==1.48',
          'django-sorting==0.1',
          'Babel==0.9.6',
          ],
      dependency_links=['https://github.com/toastdriven/django-haystack/tarball/0e95d8696f8ba770f9c60152136aba32f5591fd6#egg=django-haystack-2.0.0-beta'],
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: Unix',
                   'Programming Language :: Python']
      )
