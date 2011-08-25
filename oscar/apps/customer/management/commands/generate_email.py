import logging
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
        logger = self._get_logger()
        if len(args) != 2:
            raise CommandError("Please select a event type and order number")
        
        try:
            order = Order.objects.get(number=args[1])
        except Order.DoesNotExist:
            raise CommandError("No order found with number %s" % args[1])
        
        try:
            event_type = CommunicationEventType.objects.get(code=args[0])
        except CommunicationEventType.DoesNotExist:
            raise CommandError("No event type found with code %s" % args[0])
        
        messages = event_type.get_messages({'order': order})
        dispatcher = Dispatcher(logger)
        user = User(username='dummy', email='user@example.com')
        email = dispatcher.send_email_messages(user, messages)
        
        print "Subject: %s\nBody:\n\n%s"% (email.subject, email.body)
        
    def _get_logger(self):
        logger = logging.getLogger(__name__)
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)
        return logger
        
        
 
        
        
        
            