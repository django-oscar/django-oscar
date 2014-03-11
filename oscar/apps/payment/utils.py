import warnings

from . import models


def Bankcard(card_number, expiry_date, name=None,
             cvv=None, start_date=None, issue_number=None):
    # This odd looking thing is to handle backwards compatibility with Oscar
    # 0.5 where the Bankcard class wasn't a model and lived in this utils
    # module.  As of 0.6, the Bankcard class is a model.
    #
    # We pretend to be a class here (hence the capitalisation), remap the
    # constructor args and return an instance of the new class.
    warnings.warn("The Bankcard class has moved to oscar.apps.payment.models",
                  DeprecationWarning)
    kwargs = {
        'number': card_number,
        'expiry_date': expiry_date,
        'name': name,
        'ccv': cvv,
        'start_date': start_date,
        'issue_number': issue_number
    }
    return models.Bankcard(**kwargs)
