#!/usr/bin/env python
import sys
import os
from optparse import OptionParser

import tests.config


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
    (options, args) = parser.parse_args()
    create_migration(args[0], **options)
