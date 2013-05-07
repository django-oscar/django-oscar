#!/usr/bin/env python
"""
Convenience script to create migrations
"""
from optparse import OptionParser

from tests.config import configure
configure()


def create_migration(app_label, **kwargs):
    from south.management.commands.schemamigration import Command
    com = Command()
    com.handle(app=app_label, **kwargs)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-i', '--initial', dest='initial',
                      action='store_true', default=False)
    parser.add_option('-a', '--auto', dest='auto',
                      action='store_true', default=False)
    parser.add_option('-e', '--empty', dest='empty',
                      action='store_true', default=False)
    parser.add_option('-n', '--name', dest='name', default='')
    (options, args) = parser.parse_args()
    create_migration(args[0], initial=options.initial,
                     auto=options.auto, empty=options.empty,
                     name=options.name)
