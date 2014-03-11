class FailedPreCondition(Exception):

    def __init__(self, url, message):
        self.url = url
        self.message = message
