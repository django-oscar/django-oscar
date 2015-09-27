from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import get_class, get_model

Order = get_model('order', 'Order')
CommunicationEventType = get_model('customer', 'CommunicationEventType')
Dispatcher = get_class('customer.utils', 'Dispatcher')


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

        ctx = {
            'order': order,
            'lines': order.lines.all(),
        }
        messages = CommunicationEventType.objects.get_and_render(
            args[0], ctx)
        print("Subject: %s\nBody:\n\n%s\nBody HTML:\n\n%s" % (
            messages['subject'], messages['body'], messages['html']))
