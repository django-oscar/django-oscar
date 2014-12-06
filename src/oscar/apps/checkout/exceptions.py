class FailedPreCondition(Exception):

    def __init__(self, url, message=None, messages=None):
        self.url = url
        if message:
            self.messages = [message]
        elif messages:
            self.messages = messages
        else:
            self.messages = []


class PassedSkipCondition(Exception):
    """
    To be raised when a skip condition has been passed and the current view
    should be skipped. The passed URL dictates where to.
    """
    def __init__(self, url):
        self.url = url
