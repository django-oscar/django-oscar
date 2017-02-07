from django.test import TestCase

from oscar.core.compat import get_user_model
from oscar.apps.customer.models import CommunicationEventType


User = get_user_model()


class CommunicationTypeTest(TestCase):
    keys = ('body', 'html', 'sms', 'subject')

    def test_no_templates_returns_empty_string(self):
        et = CommunicationEventType()
        messages = et.get_messages()
        for key in self.keys:
            self.assertEqual('', messages[key])

    def test_field_template_render(self):
        et = CommunicationEventType(email_subject_template='Hello {{ name }}')
        ctx = {'name': 'world'}
        messages = et.get_messages(ctx)
        self.assertEqual('Hello world', messages['subject'])

    def test_new_line_in_subject_is_removed(self):
        subjects = [
            ('Subject with a newline\r\n', 'Subject with a newline'),
            ('New line is in \n the middle', 'New line is in  the middle'),
            ('\rStart with the new line', 'Start with the new line'),
        ]

        for original, modified in subjects:
            et = CommunicationEventType(email_subject_template=original)
            messages = et.get_messages()
            self.assertEqual(modified, messages['subject'])
