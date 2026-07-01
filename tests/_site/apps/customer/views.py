from oscar.apps.customer.views import AccountSummaryView as OscarAccountSummaryView


class AccountSummaryView(OscarAccountSummaryView):
    # just here to test import in loading_tests:ClassLoadingWithLocalOverrideTests
    pass
