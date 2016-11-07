from __future__ import absolute_import

import logging
import os
import shutil
import textwrap
from os.path import exists, join

import oscar


def create_local_app_folder(local_app_path):
    if exists(local_app_path):
        raise ValueError(
            "There is already a '%s' folder! Aborting!" % local_app_path)
    for folder in subfolders(local_app_path):
        if not exists(folder):
            os.mkdir(folder)
            init_path = join(folder, '__init__.py')
            if not exists(init_path):
                create_file(init_path)


def subfolders(path):
    """
    Decompose a path string into a list of subfolders

    Eg Convert 'apps/dashboard/ranges' into
       ['apps', 'apps/dashboard', 'apps/dashboard/ranges']
    """
    folders = []
    while path not in ('/', ''):
        folders.append(path)
        path = os.path.dirname(path)
    folders.reverse()
    return folders


def inherit_app_config(local_app_path, app_package, app_label):
    if 'dashboard' in app_label and app_label != 'dashboard':
        config_name = '%sDashboardConfig' % app_label.split('.').pop().title()
    elif app_label == 'catalogue.reviews':
        # This embedded app needs special handling
        config_name = 'CatalogueReviewsConfig'
    else:
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


def fork_app(label, folder_path, logger=None):
    """
    Create a custom version of one of Oscar's apps

    The first argument isn't strictly an app label as we allow things like
    'catalogue' or 'dashboard.ranges'.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Check label is valid
    valid_labels = [x.replace('oscar.apps.', '') for x in oscar.OSCAR_CORE_APPS
                    if x.startswith('oscar')]
    if label not in valid_labels:
        raise ValueError("There is no Oscar app that matches '%s'" % label)

    # Check folder_path is current catalog
    if folder_path == '.':
        folder_path = ''

    # Create folder
    label_folder = label.replace('.', '/')  # eg 'dashboard/ranges'
    local_app_path = join(folder_path, label_folder)
    logger.info("Creating package %s" % local_app_path)
    create_local_app_folder(local_app_path)

    # Create minimum app files
    app_package = local_app_path.replace('/', '.')

    oscar_app_path = join(oscar.__path__[0], 'apps', label_folder)
    if exists(os.path.join(oscar_app_path, 'admin.py')):
        logger.info("Creating admin.py")
        create_file(join(local_app_path, 'admin.py'),
                    "from oscar.apps.%s.admin import *  # noqa\n" % label)

    logger.info("Creating app config")
    inherit_app_config(local_app_path, app_package, label)

    # Only create models.py and migrations if it exists in the Oscar app
    oscar_models_path = join(oscar_app_path, 'models.py')
    if exists(oscar_models_path):
        logger.info("Creating models.py")
        create_file(
            join(local_app_path, 'models.py'),
            "from oscar.apps.%s.models import *  # noqa\n" % label)

        migrations_path = 'migrations'
        source = join(oscar_app_path, migrations_path)
        if exists(source):
            logger.info("Creating %s folder", migrations_path)
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
