from oscar.app import Shop

from apps.checkout.app import application as checkout_app


class Application(Shop):
    # Use local checkout app so we can mess with the view classes
    checkout_app = checkout_app


application = Application()
