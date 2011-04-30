import mock
from decimal import Decimal as D
from xml.dom.minidom import parseString

from django.test import TestCase

from oscar.apps.payment.datacash.utils import Gateway


class AuthTransactionTests(TestCase):
    
    def setUp(self):
        self.gateway = Gateway(client="DUMMY", password="123456")
        self.transport = mock.Mock()
        self.gateway.do_request = self.transport
    
    def assertXmlTagValue(self, tag_name, value):
        request_xml = self.transport.call_args[0][0]
        doc = parseString(request_xml)
        try:
            tag = doc.getElementsByTagName(tag_name)[0]
            self.assertEquals(value, tag.firstChild.data)
        except IndexError:
            self.fail("Tag '%s' not found\n%s" % (tag_name, request_xml))
            
    def assertXmlTagAttributeValue(self, tag_name, attribute, value):
        request_xml = self.transport.call_args[0][0]
        doc = parseString(request_xml)
        try:
            tag = doc.getElementsByTagName(tag_name)[0]
            self.assertEquals(value, tag.attributes[attribute].value)
        except IndexError:
            self.fail("Tag '%s' not found\n%s" % (tagName, request_xml))
    
    def make_auth_request(self):
        self.gateway.auth(card_number='1000010000000007', 
                          start_date='01/10',
                          expiry_date='01/12',
                          issue_number='03',
                          merchant_reference='123123',
                          currency='GBP',
                          amount=D('12.99'))
    
    def test_auth_includes_credentials(self):
        self.make_auth_request()
        self.assertTrue(self.transport.called)
        self.assertXmlTagValue('client', 'DUMMY')
        self.assertXmlTagValue('password', '123456')
        
    def test_auth_includes_card_details(self):   
        self.make_auth_request()
        self.assertXmlTagValue('pan', '1000010000000007')
        self.assertXmlTagValue('startdate', '01/10')
        self.assertXmlTagValue('expirydate', '01/12')
        
    def test_auth_includes_merchant_reference(self):   
        self.make_auth_request()
        self.assertXmlTagValue('merchantreference', '123123')
        
    def test_auth_includes_amount_and_currency(self):   
        self.make_auth_request()
        self.assertXmlTagValue('amount', '12.99')
        self.assertXmlTagAttributeValue('amount', 'currency', 'GBP')
        
    def test_auth_includes_method(self):
        self.make_auth_request()    
        self.assertXmlTagValue('method', 'auth')
    

class HistoricTransactionTests(TestCase):
    
    def setUp(self):
        self.gateway = Gateway(client="DUMMY", password="123456")

    def test_cancel(self):
        self.gateway.auth
        
    def test_fulfil(self):
        pass
    
    def test_txn_refund(self):
        pass