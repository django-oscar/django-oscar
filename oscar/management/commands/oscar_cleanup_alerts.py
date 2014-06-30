from optparse import make_option
from datetime import timedelta

from django.utils.timezone import now

from oscar.management import base
from oscar.core.loading import get_model
from oscar.apps.customer.alerts import utils

ProductAlert = get_model('customer', 'ProductAlert')


class Command(base.OscarBaseCommand):
    help = "Remove stale, unconfirmed alerts"
    option_list = base.OscarBaseCommand.option_list + (
        make_option('--days', dest='days', default=0,
                    help='Remove alerts older then DAYS.'),
        make_option('--hours', dest='hours', default=0,
                    help='Remove alerts older then HOURS.'),
    )
    logger_name = 'oscar.alerts'

    def run(self, *args, **options):
        # Generate a threshold date from the input options or 24 hours
        # if no options specified. All alerts that have the
        # status ``UNCONFIRMED`` and have been created before the
        # threshold date will be removed.
        delta = timedelta(days=int(options['days']),
                          hours=int(options['hours']))
        if not delta:
            delta = timedelta(hours=24)
        threshold_date = now() - delta
        utils.delete_unconfirmed_alerts(threshold_date, self.logger)
