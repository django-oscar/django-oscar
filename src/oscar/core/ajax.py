from django.contrib import messages


class FlashMessages(object):
    """
    Intermediate container for flash messages.

    This is useful as, at the time of creating the message, we don't know
    whether the response is an AJAX response or not.
    """

    def __init__(self):
        self.msgs = {}

    def add_message(self, level, message):
        self.msgs.setdefault(level, []).append(message)

    def add_messages(self, level, messages):
        for msg in messages:
            self.add_message(level, msg)

    def info(self, message):
        self.add_message(messages.INFO, message)

    def warning(self, message):
        self.add_message(messages.WARNING, message)

    def error(self, message):
        self.add_message(messages.ERROR, message)

    def success(self, message):
        self.add_message(messages.SUCCESS, message)

    def as_dict(self):
        payload = {}
        for level, msgs in self.msgs.items():
            tag = messages.DEFAULT_TAGS.get(level, 'info')
            payload[tag] = [str(msg) for msg in msgs]
        return payload

    def apply_to_request(self, request):
        for level, msgs in self.msgs.items():
            for msg in msgs:
                messages.add_message(request, level, msg)
