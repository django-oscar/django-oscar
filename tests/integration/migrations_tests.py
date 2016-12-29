"""This module was taken from Wagtail, see:

https://github.com/torchbox/wagtail/blob/d82e38e11e9f6c27b6ad6dfc6467e2754b5ab228/wagtail/wagtailcore/tests/test_migrations.py


"""
from __future__ import absolute_import

from django.apps import apps
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.questioner import MigrationQuestioner
from django.db.migrations.state import ProjectState
from django.test import TransactionTestCase
from django.utils.six import iteritems


class TestForMigrations(TransactionTestCase):
    def test__migrations(self):
        app_labels = set(app.label for app in apps.get_app_configs()
                         if app.name.startswith('oscar.'))
        for app_label in app_labels:
            apps.get_app_config(app_label.split('.')[-1])
        loader = MigrationLoader(None, ignore_no_migrations=True)

        conflicts = dict(
            (app_label, conflict)
            for app_label, conflict in iteritems(loader.detect_conflicts())
            if app_label in app_labels
        )

        if conflicts:
            name_str = "; ".join("%s in %s" % (", ".join(names), app)
                                 for app, names in conflicts.items())
            self.fail("Conflicting migrations detected (%s)." % name_str)

        autodetector = MigrationAutodetector(
            loader.project_state(),
            ProjectState.from_apps(apps),
            MigrationQuestioner(specified_apps=app_labels, dry_run=True),
        )

        changes = autodetector.changes(
            graph=loader.graph,
            trim_to_apps=app_labels or None,
            convert_apps=app_labels or None,
        )

        if changes:
            migrations = '\n'.join((
                '  {migration}\n{changes}'.format(
                    migration=migration,
                    changes='\n'.join('    {0}'.format(operation.describe())
                                      for operation in migration.operations))
                for (_, migrations) in changes.items()
                for migration in migrations))

            self.fail('Model changes with no migrations detected:\n%s' % migrations)
