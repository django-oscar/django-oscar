from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from os.path import exists

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--flush',
            action='store_true',
            dest='flush',
            default=False,
            help='Flush tables before importing'),
        make_option('--csv-type',
            type='string',
            dest='csv_type',
            nargs=1,
            default='simple',
            help='CSV content type'),
        make_option('--file',
            type='string',
            dest='filename',
            nargs=1,
            default=False,
            help='path/to/file'),
        )


    def handle(self, *args, **options):
        self.flush = options.get('flush')
        self.csv_type = options.get('csv_type')
        self.file = options.get('filename')
        if not exists(self.file):
            self.stderr.write("File does not exists!\n")
        
    def flush(self):
        self.stdout.write("Flushing")
        
    def csv_type(self):
        #self.stdout.write(args)