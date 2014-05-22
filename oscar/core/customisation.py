from __future__ import absolute_import
import os
import shutil
import logging
import textwrap

import oscar


def fork_app(app_label, folder_path, logger=None):
    """
    Create a custom version of one of Oscar's apps
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Check app_label is valid
    app_labels = [x.split('.').pop() for x in oscar.OSCAR_CORE_APPS if
                  x.startswith('oscar')]
    if app_label not in app_labels:
        raise ValueError("There is no Oscar app with label '%s'" % app_label)

    # Check folder exists
    if not os.path.exists(folder_path):
        raise ValueError(
            "The folder '%s' does not exist. Please create it then run this "
            "command again")

    # Create folder
    app_folder_path = os.path.join(folder_path, app_label)
    if os.path.exists(app_folder_path):
        raise ValueError(
            "There is already a '%s' folder! Aborting!" % app_folder_path)
    logger.info("Creating folder %s" % app_folder_path)
    os.mkdir(app_folder_path)

    # Create minimum app files
    logger.info("Creating __init__.py and models.py modules")
    create_file(os.path.join(app_folder_path, '__init__.py'))
    create_file(
        os.path.join(app_folder_path, 'models.py'),
        "from oscar.apps.%s.models import *" % app_label)

    # Migrations
    source = os.path.join(
        oscar.__path__[0], 'apps', app_label, 'migrations')
    destination = os.path.join(app_folder_path, 'migrations')
    logger.info("Copying migrations from %s to %s", source, destination)
    shutil.copytree(source, destination)

    # Final step needs to be done by hand
    app_package = app_folder_path.replace('/', '.')
    msg = (
        "The final step is to add '%s' to INSTALLED_APPS "
        "(replacing the equivalent Oscar app). This can be "
        "acheived using Oscar's get_core_apps function - eg:"
    ) % app_package
    snippet = (
        "  # settings.py\n"
        "  ...\n"
        "  INSTALLED_APPS = [\n"
        "      'django.contrib.auth',\n"
        "      ...\n"
        "  ]\n"
        "  from oscar import get_core_apps\n"
        "  INSTALLED_APPS = INSTALLED_APPS + get_core_apps(\n"
        "      ['%s'])"
    ) % app_package
    record = "\n%s\n\n%s" % (
        "\n".join(textwrap.wrap(msg)), snippet)
    logger.info(record)


def create_file(filepath, content=''):
    with open(filepath, 'w') as f:
        f.write(content)
