import io
import os
import pathlib
import tempfile
import shutil

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

import oscar
from tests import _site


class OscarForkStaticsTestCase(TestCase):
    def setUp(self):
        # Create dummy Oscar static-files directory (this exists in released
        # Oscar packages)
        self.oscar_static_dir_path = pathlib.Path(
            os.path.dirname(oscar.__file__), "static"
        )
        self.oscar_static_dir_path.mkdir(exist_ok=True)
        self.oscar_static_file_path = pathlib.Path(
            self.oscar_static_dir_path, "name.css"
        )
        self.oscar_static_file_path.touch(exist_ok=False)

        # Change to the project's base directory (where the static-files
        # directory should be copied to)
        self.project_base_dir_path = pathlib.Path(os.path.dirname(_site.__file__))
        os.chdir(self.project_base_dir_path)

    def tearDown(self):
        # Delete dummy Oscar static-files directory
        self.oscar_static_file_path.unlink()
        try:
            self.oscar_static_dir_path.rmdir()
        except OSError:
            pass

    def test_command_with_already_existing_directory(self):
        project_static_dir_path = pathlib.Path(self.project_base_dir_path, "static")

        project_static_dir_path.mkdir()
        with self.assertRaises(CommandError) as e:
            call_command("oscar_fork_statics")
        self.assertEqual(
            e.exception.args[0],
            "The folder %s already exists - aborting!" % project_static_dir_path,
        )

        shutil.rmtree(project_static_dir_path, ignore_errors=True)

    def test_command_with_default_target_path(self):
        project_static_dir_path = pathlib.Path(self.project_base_dir_path, "static")
        project_static_file_path = pathlib.Path(project_static_dir_path, "name.css")

        out = io.StringIO()
        call_command("oscar_fork_statics", stdout=out)
        self.assertTrue(project_static_file_path.exists())
        messages = out.getvalue().split("\n")
        self.assertEqual(
            messages[0], "Copying Oscar's static files to %s" % project_static_dir_path
        )
        self.assertEqual(
            messages[1],
            "You need to add %s to STATICFILES_DIRS in order for your local overrides to be "
            "picked up" % project_static_dir_path,
        )

        shutil.rmtree(project_static_dir_path)

    def test_command_with_relative_target_path(self):
        project_static_dir_path = pathlib.Path(
            self.project_base_dir_path, "relative/dir"
        )
        project_static_file_path = pathlib.Path(project_static_dir_path, "name.css")

        out = io.StringIO()
        call_command("oscar_fork_statics", target_path="relative/dir", stdout=out)
        self.assertTrue(project_static_file_path.exists())
        messages = out.getvalue().split("\n")
        self.assertEqual(
            messages[0], "Copying Oscar's static files to %s" % project_static_dir_path
        )
        self.assertEqual(
            messages[1],
            "You need to add %s to STATICFILES_DIRS in order for your local overrides to be "
            "picked up" % project_static_dir_path,
        )

        shutil.rmtree(project_static_dir_path)
        project_static_dir_path.parent.rmdir()

    def test_command_with_absolute_target_path(self):
        project_static_dir_path = pathlib.Path(tempfile.mkdtemp(), "static")
        project_static_file_path = pathlib.Path(project_static_dir_path, "name.css")

        out = io.StringIO()
        call_command(
            "oscar_fork_statics", target_path=str(project_static_dir_path), stdout=out
        )
        self.assertTrue(project_static_file_path.exists())
        messages = out.getvalue().split("\n")
        self.assertEqual(
            messages[0], "Copying Oscar's static files to %s" % project_static_dir_path
        )
        self.assertEqual(
            messages[1],
            "You need to add %s to STATICFILES_DIRS in order for your local overrides to be "
            "picked up" % project_static_dir_path,
        )

        shutil.rmtree(project_static_dir_path)
        project_static_dir_path.parent.rmdir()
