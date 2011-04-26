from setuptools import setup

setup(name='django-oscar',
      version='0.1.0',
      url='https://github.com/tangentlabs/django-oscar',
      description="Domain-driven ecommerce for Django",
      author="David Winterbottom",
      author_email="david.winterbottom@tangentlabs.co.uk",
      package_dir={'': '.'},
      install_requires=['Django==1.3',
          'PIL>=1.1.7',
          'django-haystack==1.2.0-beta'],
      dependency_links = [
          'https://github.com/toastdriven/django-haystack/tarball/master#egg=django-haystack-1.2.0-beta'
          ]
      )