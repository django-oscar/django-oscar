class Bankcard(object):
    """
    Simple data container for bankcard data
    """
    
    def __init__(self, card_number, expiry_date, name=None, cvv=None, start_date=None, issue_number=None):
        self.card_number = card_number
        self.card_holder_name = name
        self.expiry_date = expiry_date
        self.start_date = start_date
        self.issue_number = issue_number
        self.cvv = cvv

    @property
    def ccv(self):
        # There are lots of acronyms for this -
        # see http://en.wikipedia.org/wiki/Card_Code_Verification
        return self.cvv