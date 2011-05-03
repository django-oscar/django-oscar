

class Bankcard(object):
    
    def __init__(self, card_number, expiry_date, name=None, ccv=None, start_date=None, issue_number=None):
        self.card_number = card_number
        self.card_holder_name = name
        self.expiry_date = expiry_date
        self.start_date = start_date
        self.issue_number = issue_number
        self.ccv = ccv