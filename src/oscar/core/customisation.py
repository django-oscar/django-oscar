import logging
import os
import shutil
from os.path import dirname, exists, join

from django.apps import apps

from oscar.core.application import OscarConfig


def create_local_app_folder(local_app_path):
    if exists(local_app_path):
        raise ValueError("There is already a '%s' folder! Aborting!" % local_app_path)
    for folder in subfolders(local_app_path):
        if not exists(folder):
            os.mkdir(folder)
            init_path = join(folder, "__init__.py")
            if not exists(init_path):
                create_file(init_path)


def subfolders(path):
    """
    Decompose a path string into a list of subfolders

    Eg Convert 'apps/dashboard/ranges' into
       ['apps', 'apps/dashboard', 'apps/dashboard/ranges']
    """
    folders = []
    while path not in ("/", ""):
        folders.append(path)
        path = dirname(path)
    folders.reverse()
    return folders


def inherit_app_config(local_app_folder_path, local_app_name, app_config):
    create_file(
        join(local_app_folder_path, "__init__.py"),
        "default_app_config = '{app_name}.apps.{app_config_class_name}'\n".format(
            app_name=local_app_name, app_config_class_name=app_config.__class__.__name__
        ),
    )
    create_file(
        join(local_app_folder_path, "apps.py"),
        "import {app_config_class_module} as apps\n\n\n"
        "class {app_config_class_name}(apps.{app_config_class_name}):\n"
        "    name = '{app_name}'\n".format(
            app_config_class_module=app_config.__module__,
            app_config_class_name=app_config.__class__.__name__,
            app_name=local_app_name,
        ),
    )


def fork_app(label, local_folder_path, local_app_subpackage=None, logger=None):
    """
    Create a custom version of one of Oscar's apps.

    The first argument is the app label of the Oscar app to fork.

    The second argument is a folder path, for where to copy the forked app.

    The third optional argument is the subpackage (inside the local folder path
    package) for the new app.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Check label is valid
    try:
        app_config = apps.get_app_config(label)
    except LookupError:
        raise ValueError("There is no app with the label '{}'".format(label))
    else:
        if not isinstance(app_config, OscarConfig):
            raise ValueError("There is no Oscar app with the label '{}'".format(label))

    # Remove trailing slash from folder path
    local_folder_path = local_folder_path.rstrip("/")

    # Check if local_folder_path is current folder
    if local_folder_path == ".":
        local_folder_path = ""

    local_apps_package = local_folder_path.lstrip("/").replace("/", ".")
    if local_app_subpackage is None:
        local_app_subpackage = app_config.name.replace("oscar.apps.", "")
        # In case this is a fork of a fork
        local_app_subpackage = local_app_subpackage.replace(local_apps_package, "")

    # Create folder
    local_app_subfolder_path = local_app_subpackage.replace(
        ".", "/"
    )  # eg 'dashboard/ranges'
    local_app_folder_path = join(local_folder_path, local_app_subfolder_path)
    logger.info("Creating package %s", local_app_folder_path)
    create_local_app_folder(local_app_folder_path)

    # Create minimum app files
    app_folder_path = app_config.path

    if exists(join(app_folder_path, "admin.py")):
        logger.info("Creating admin.py")
        create_file(
            join(local_app_folder_path, "admin.py"),
            "from {app_name}.admin import *  \n".format(app_name=app_config.name),
        )

    logger.info("Creating app config")
    local_app_name = (
        local_apps_package + ("." if local_apps_package else "") + local_app_subpackage
    )
    inherit_app_config(local_app_folder_path, local_app_name, app_config)

    # Only create models.py and migrations if they exist in the Oscar app
    models_file_path = join(app_folder_path, "models.py")
    if exists(models_file_path):
        logger.info("Creating models.py")
        create_file(
            join(local_app_folder_path, "models.py"),
            "from {app_name}.models import * \n".format(app_name=app_config.name),
        )

        migrations_subfolder_path = "migrations"
        migrations_folder_path = join(app_folder_path, migrations_subfolder_path)
        if exists(migrations_folder_path):
            logger.info("Creating %s folder", migrations_subfolder_path)
            local_migrations_folder_path = join(
                local_app_folder_path, migrations_subfolder_path
            )
            shutil.copytree(migrations_folder_path, local_migrations_folder_path)

    # Final step needs to be done by hand
    app_config_class_path = "{class_module}.{class_name}".format(
        class_module=app_config.__module__, class_name=app_config.__class__.__name__
    )
    local_app_config_class_path = "{local_app_name}.apps.{class_name}".format(
        local_app_name=local_app_name, class_name=app_config.__class__.__name__
    )
    msg = "Replace the entry '{}' with '{}' in INSTALLED_APPS".format(
        app_config_class_path, local_app_config_class_path
    )
    logger.info(msg)


def create_file(filepath, content=""):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
