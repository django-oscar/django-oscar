# -*- coding: utf-8 -*-
import os
import re

from django.test import TestCase

import oscar.apps


class TestMigrations(TestCase):

    def setUp(self):
        self.root_path = os.path.dirname(oscar.apps.__file__)
        self.migration_filenames = []
        for path, __, migrations in os.walk(self.root_path):
            if path.endswith('migrations'):
                paths = [
                    os.path.join(path, migration) for migration in migrations
                    if migration.endswith('.py') and migration != '__init__.py']
                self.migration_filenames += paths

    def test_dont_contain_hardcoded_user_model(self):
        def check_for_auth_model(filepath):
            with open(filepath) as f:
                s = f.read()
                return 'auth.User' in s or 'auth.user' in s

        matches = list(filter(check_for_auth_model, self.migration_filenames))

        if matches:
            pretty_matches = '\n'.join(
                [match.replace(self.root_path, '') for match in matches])
            self.fail('References to hardcoded User model found in the '
                      'following migration(s):\n' + pretty_matches)

    def test_no_duplicate_migration_numbers(self):
        # pull app name and migration number
        regexp = re.compile(r'^.+oscar/apps/([\w/]+)/migrations/(\d{4}).+$')
        keys = []
        for migration in self.migration_filenames:
            match = regexp.match(migration)
            keys.append(match.group(1) + match.group(2))
        self.assertEqual(len(keys), len(set(keys)))
