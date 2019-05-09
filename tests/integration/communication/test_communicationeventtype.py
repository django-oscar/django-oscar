from django.test import TestCase

from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

User = get_user_model()

CommunicationEventType = get_model('communication', 'CommunicationEventType')


class CommunicationTypeTest(TestCase):
    keys = ('body', 'html', 'sms', 'subject')

    def test_no_templates_returns_empty_string(self):
        et = CommunicationEventType()
        messages = et.get_messages()
        for key in self.keys:
            assert messages[key] == ''

    def test_field_template_render(self):
        et = CommunicationEventType(email_subject_template='Hello {{ name }}')
        ctx = {'name': 'world'}
        messages = et.get_messages(ctx)
        assert 'Hello world' == messages['subject']

    def test_new_line_in_subject_is_removed(self):
        subjects = [
            ('Subject with a newline\r\n', 'Subject with a newline'),
            ('New line is in \n the middle', 'New line is in  the middle'),
            ('\rStart with the new line', 'Start with the new line'),
        ]

        for original, modified in subjects:
            et = CommunicationEventType(email_subject_template=original)
            messages = et.get_messages()
            assert modified == messages['subject']
