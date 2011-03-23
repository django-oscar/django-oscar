from setuptools import setup

setup(name='django-oscar',
      version='0.1.0',
      url='https://github.com/codeinthehole/django-oscar',
      description="A flexible ecommerce application for Django",
      author="David Winterbottom",
      author_email="david.winterbottom@tangentlabs.co.uk",
      package_dir={'': '.'},
      install_requires=['Django=1.3',
                'MySQL-python==1.2.3',
                'PIL==1.1.7']    
      )