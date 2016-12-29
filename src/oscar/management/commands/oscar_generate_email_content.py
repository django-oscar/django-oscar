from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import get_class, get_model

Order = get_model('order', 'Order')
CommunicationEventType = get_model('customer', 'CommunicationEventType')
Dispatcher = get_class('customer.utils', 'Dispatcher')


class Command(BaseCommand):
    args = '<communication_event_type> <order number>'
    help = 'For testing the content of order emails'

    def add_arguments(self, parser):
        parser.add_argument('<communication_event_type>')
        parser.add_argument('<order number>')

    def handle(self, *args, **options):
        try:
            order = Order.objects.get(number=options['<order number>'])
        except Order.DoesNotExist:
            raise CommandError(
                "No order found with number %s" % options['<order number>'])

        ctx = {
            'order': order,
            'lines': order.lines.all(),
        }
        messages = CommunicationEventType.objects.get_and_render(
            options['<communication_event_type>'], ctx)
        print("Subject: %s\nBody:\n\n%s\nBody HTML:\n\n%s" % (
            messages['subject'], messages['body'], messages['html']))
