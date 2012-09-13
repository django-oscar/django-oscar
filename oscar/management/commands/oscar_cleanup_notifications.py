import logging

from optparse import make_option
from datetime import datetime, timedelta

from django.db.models import get_model
from django.core.management.base import BaseCommand

ProductNotification = get_model('notification', 'productnotification')

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to remove all notifications derived from
    ``Notification`` that are in status ``UNCONFIRMED`` and
    have been created before a threshold date and time. The threshold
    can be specified as options ``days`` and ``hours`` and is
    calculated relative to the current date and time.
    """
    help = "Check unconfirmed notifications and clean them up"
    option_list = BaseCommand.option_list + (
        make_option('--days',
            dest='days',
            default=0,
            help='cleanup notifications older then DAYS from now.'),
        make_option('--hours',
            dest='hours',
            default=0,
            help='cleanup notifications older then HOURS from now.'),
        )

    def handle(self, *args, **options):
        """
        Generate a threshold date from the input options or 24 hours
        if no options specified. All notifications that have the
        status ``UNCONFIRMED`` and have been created before the
        threshold date will be removed assuming that the emails
        are wrong or the customer changed their mind.
        """
        delta = timedelta(days=int(options['days']),
                          hours=int(options['hours']))

        if not delta:
            delta = timedelta(hours=24)

        threshold_date = datetime.now() - delta

        logger.info('cleaning up unconfirmed notifications older than %s',
                    threshold_date.strftime("%Y-%m-%d %H:%M"))

        ProductNotification.objects.filter(
            status=ProductNotification.UNCONFIRMED,
            date_created__lt=threshold_date
        ).delete()
