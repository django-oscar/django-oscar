from setuptools import setup

from oscar import get_version

version = get_version()

setup(name='django-oscar',
      version=version.replace(' ', '-'),
      url='https://github.com/tangentlabs/django-oscar',
      author="Tangent Labs",
      author_email="david.winterbottom@tangentlabs.co.uk",
      description="A domain-driven ecommerce framework for Django 1.3",
      long_description=open('README.rst').read(),
      license='LICENSE',
      package_dir={'': '.'},
      install_requires=['Django>=1.3',
          'PIL>=1.1.7',
          'django-haystack>=1.2.0',
          'django-treebeard>=1.6.1'
          'sorl-thumbnail>=11.05.1'],
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: Unix',
                   'Programming Language :: Python']
      )
