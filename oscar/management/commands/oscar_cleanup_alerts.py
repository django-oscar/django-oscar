import logging
from optparse import make_option
from datetime import timedelta

from django.db.models import get_model
from django.utils.timezone import now
from django.core.management.base import BaseCommand

ProductAlert = get_model('customer', 'ProductAlert')

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to remove all stale unconfirmed alerts
    """
    help = "Check unconfirmed alerts and clean them up"

    option_list = BaseCommand.option_list + (
        make_option('--days', dest='days', default=0,
                    help='cleanup alerts older then DAYS from now.'),
        make_option('--hours', dest='hours', default=0,
                    help='cleanup alerts older then HOURS from now.'),
    )

    def handle(self, *args, **options):
        """
        Generate a threshold date from the input options or 24 hours
        if no options specified. All alerts that have the
        status ``UNCONFIRMED`` and have been created before the
        threshold date will be removed assuming that the emails
        are wrong or the customer changed their mind.
        """
        delta = timedelta(days=int(options['days']),
                          hours=int(options['hours']))
        if not delta:
            delta = timedelta(hours=24)

        threshold_date = now() - delta

        logger.info('Deleting unconfirmed alerts older than %s',
                    threshold_date.strftime("%Y-%m-%d %H:%M"))

        qs = ProductAlert.objects.filter(
            status=ProductAlert.UNCONFIRMED,
            date_created__lt=threshold_date
        )
        logger.info("Found %d stale alerts to delete", qs.count())
        qs.delete()
