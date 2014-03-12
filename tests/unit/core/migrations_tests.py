# -*- coding: utf-8 -*-

import os

from django.test import TestCase

import oscar.apps


class TestMigrations(TestCase):

    def check_for_auth_model(self, filepath):
        with open(filepath) as f:
            s = f.read()
            return 'auth.User' in s or 'auth.user' in s

    def test_dont_contain_hardcoded_user_model(self):
        root_path = os.path.dirname(oscar.apps.__file__)
        matches = []
        for dir, __, migrations in os.walk(root_path):
            if dir.endswith('migrations'):
                paths = [os.path.join(dir, migration) for migration in migrations
                         if migration.endswith('.py')]
                matches += filter(self.check_for_auth_model, paths)

        if matches:
            pretty_matches = '\n'.join(
                [match.replace(root_path, '') for match in matches])
            self.fail('References to hardcoded User model found in the '
                      'following migration(s):\n' + pretty_matches)
