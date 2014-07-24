from __future__ import absolute_import
import os
from os.path import join, exists
import shutil
import logging
import textwrap

import oscar


def create_local_app_folder(local_app_path):
    if exists(local_app_path):
        raise ValueError(
            "There is already a '%s' folder! Aborting!" % local_app_path)
    os.mkdir(local_app_path)


def inherit_app_config(local_app_path, app_package, app_label):
    # This only works for non-dashboard apps; but then the fork_app command
    # doesn't support them anyway
    config_name = app_label.title() + 'Config'
    create_file(
        join(local_app_path, '__init__.py'),
        "default_app_config = '{app_package}.config.{config_name}'\n".format(
            app_package=app_package, config_name=config_name))
    create_file(
        join(local_app_path, 'config.py'),
        "from oscar.apps.{app_label} import config\n\n\n"
        "class {config_name}(config.{config_name}):\n"
        "    name = '{app_package}'\n".format(
            app_package=app_package,
            app_label=app_label,
            config_name=config_name))


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
    if not exists(folder_path):
        raise ValueError(
            "The folder '%s' does not exist. Please create it then run this "
            "command again" % folder_path)

    # Create folder
    local_app_path = join(folder_path, app_label)
    oscar_app_path = join(oscar.__path__[0], 'apps', app_label)
    logger.info("Creating folder %s" % local_app_path)
    create_local_app_folder(local_app_path)

    # Create minimum app files
    app_package = local_app_path.replace('/', '.')
    logger.info("Enabling Django admin integration")
    create_file(join(local_app_path, 'admin.py'),
                "from oscar.apps.%s.admin import *  # noqa\n" % app_label)
    logger.info("Inheriting app config")
    inherit_app_config(local_app_path, app_package, app_label)

    # Only create models.py and migrations if it exists in the Oscar app
    oscar_models_path = join(oscar_app_path, 'models.py')
    if exists(oscar_models_path):
        logger.info(
            "Creating models.py and copying South and native migrations")
        create_file(
            join(local_app_path, 'models.py'),
            "from oscar.apps.%s.models import *  # noqa\n" % app_label)

        for migrations_path in ['migrations', 'south_migrations']:
            source = join(oscar_app_path, migrations_path)
            destination = join(local_app_path, migrations_path)
            shutil.copytree(source, destination)

    # Final step needs to be done by hand
    msg = (
        "The final step is to add '%s' to INSTALLED_APPS "
        "(replacing the equivalent Oscar app). This can be "
        "achieved using Oscar's get_core_apps function - e.g.:"
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
