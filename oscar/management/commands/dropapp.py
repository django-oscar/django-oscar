from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands.sqlclear import Command as SqlClearCommand

class Command(BaseCommand):
    args = '<app_name app_name ...>'
    help = 'Drops the db tables for the given apps'

    def handle(self, *args, **kwargs):
        com = SqlClearCommand()
        self.stdout.write("SET FOREIGN_KEY_CHECKS=0;\n")
        for app_name in args:
            self.stdout.write(com.handle(app_name))
