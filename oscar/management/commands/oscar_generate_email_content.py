import sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from oscar.core.loading import import_module
import_module('order.models', ['Order'], locals())
import_module('customer.models', ['CommunicationEventType'], locals())
import_module('customer.utils', ['Dispatcher'], locals())


class Command(BaseCommand):
    args = '<communication_event_type> <order number>'
    help = 'For testing the content of order emails'
    
    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("Please select a event type and order number")
        
        try:
            order = Order.objects.get(number=args[1])
        except Order.DoesNotExist:
            raise CommandError("No order found with number %s" % args[1])
        
        messages = CommunicationEventType.objects.get_and_render(args[0], {'order': order})
        print "Subject: %s\nBody:\n\n%s"% (messsages['subject'], email['body'])