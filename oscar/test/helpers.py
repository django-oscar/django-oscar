import twill
from StringIO import StringIO

from django.test import TestCase
from django.core.servers.basehttp import AdminMediaHandler
from django.core.handlers.wsgi import WSGIHandler
from django.core.urlresolvers import reverse

from oscar.apps.catalogue.models import ProductClass, Product
from oscar.apps.partner.models import Partner, StockRecord

def create_product(price=None, title="Dummy title", product_class="Dummy item class", 
                   partner="Dummy partner", upc="dummy_101", num_in_stock=10):
    """
    Helper method for creating products that are used in tests.
    """
    ic,_ = ProductClass._default_manager.get_or_create(name=product_class)
    item = Product._default_manager.create(title=title, product_class=ic, upc=upc)
    if price:
        partner,_ = Partner._default_manager.get_or_create(name=partner)
        sr = StockRecord._default_manager.create(product=item, partner=partner, 
                                                 price_excl_tax=price, num_in_stock=num_in_stock)
    return item


class TwillTestCase(TestCase):
    """
    Simple wrapper around Twill to make writing TestCases easier.

    Commands availabel through self.command are:
    - go        -> visit a URL
    - back      -> back to previous URL
    - reload    -> reload URL
    - follow    -> follow a given link
    - code      -> assert the HTTP response code
    - find      -> assert page contains some string
    - notfind   -> assert page does not contain
    - title     -> assert page title
    """

    HOST = '127.0.0.1'
    PORT = 8080

    def setUp(self):
        app = AdminMediaHandler(WSGIHandler())
        twill.add_wsgi_intercept(self.HOST, self.PORT, lambda: app)
        twill.set_output(StringIO())
        self.command = twill.commands

    def tearDown(self):
        twill.remove_wsgi_intercept(self.HOST, self.PORT)

    def reverse(self, url_name, *args, **kwargs):
        """
        Custom 'reverse' function that includes the protocol and host
        """
        return 'http://%s:%d%s' % (self.HOST, self.PORT, reverse(url_name, *args, **kwargs))

    def visit(self, url_name, *args,**kwargs):
        self.command.go(self.reverse(url_name, *args, **kwargs))

    def assertResponseCodeIs(self, code):
        self.command.code(code)

    def assertPageContains(self, regexp):
        self.command.find(regexp)

    def assertPageDoesNotContain(self, regexp):
        self.command.notfind(regexp)

    def assertPageTitleMatches(self, regexp):
        self.command.title(regexp)

