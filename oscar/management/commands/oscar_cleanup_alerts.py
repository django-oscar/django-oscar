from optparse import make_option
from datetime import timedelta

from django.utils.timezone import now
from django.core.management.base import BaseCommand

from oscar.management import base
from oscar.core.loading import get_model

ProductAlert = get_model('customer', 'ProductAlert')



class Command(base.OscarBaseCommand):
    help = "Remove stale, unconfirmed alerts"

    option_list = BaseCommand.option_list + (
        make_option('--days', dest='days', default=0,
                    help='Remove alerts older then DAYS.'),
        make_option('--hours', dest='hours', default=0,
                    help='Remove alerts older then HOURS.'),
    )

    def handle(self, *args, **options):
        # Generate a threshold date from the input options or 24 hours
        # if no options specified. All alerts that have the
        # status ``UNCONFIRMED`` and have been created before the
        # threshold date will be removed.
        delta = timedelta(days=int(options['days']),
                          hours=int(options['hours']))
        if not delta:
            delta = timedelta(hours=24)

        threshold_date = now() - delta

        logger = self.logger(__name__)
        logger.info('Deleting unconfirmed alerts older than %s',
                    threshold_date.strftime("%Y-%m-%d %H:%M"))

        qs = ProductAlert.objects.filter(
            status=ProductAlert.UNCONFIRMED,
            date_created__lt=threshold_date
        )
        logger.info("Found %d stale alerts to delete", qs.count())
        qs.delete()
