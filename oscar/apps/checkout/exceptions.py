class FailedPreCondition(Exception):

    def __init__(self, url, message=None, messages=None):
        self.url = url
        if message:
            self.messages = [message]
        elif messages:
            self.messages = messages
        else:
            self.messages = []
