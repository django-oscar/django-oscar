import mock
from decimal import Decimal as D
from xml.dom.minidom import parseString

from django.test import TestCase

from oscar.apps.payment.datacash.utils import Gateway


class TransactionMixin(object):
    
    def init_gateway(self, **kwargs):
        self.gateway = Gateway(client="DUMMY", password="123456", host="dummyhost.com", **kwargs)
        self.transport = mock.Mock()
        self.gateway.do_request = self.transport
        
        # Set a default success response
        response_xml = """<?xml version="1.0" encoding="UTF-8" ?>
<Response>
    <CardTxn>
        <authcode>060642</authcode>
        <card_scheme>Switch</card_scheme>
        <country>United Kingdom</country>
        <issuer>HSBC</issuer>
    </CardTxn>
    <datacash_reference>3000000088888888</datacash_reference>
    <merchantreference>1000001</merchantreference>
    <mode>LIVE</mode>
    <reason>ACCEPTED</reason>
    <status>1</status>
    <time>1071567305</time>
</Response>"""
        self.transport.return_value = response_xml
    
    def assertXmlTagValue(self, tag_name, value):
        request_xml = self.transport.call_args[0][0]
        doc = parseString(request_xml)
        try:
            tag = doc.getElementsByTagName(tag_name)[0]
            self.assertEquals(value, tag.firstChild.data)
        except IndexError:
            self.fail("Tag '%s' not found\n%s" % (tag_name, request_xml))
    
    def make_request(self, **kwargs):
        """
        Needs to be implemented by subclass.
        """
        pass
            
    def assertXmlTagAttributeValue(self, tag_name, attribute, value):
        request_xml = self.transport.call_args[0][0]
        doc = parseString(request_xml)
        try:
            tag = doc.getElementsByTagName(tag_name)[0]
            self.assertEquals(value, tag.attributes[attribute].value)
        except IndexError:
            self.fail("Tag '%s' not found\n%s" % (tag_name, request_xml))
    
    def test_request_includes_credentials(self):
        self.make_request()
        self.assertTrue(self.transport.called)
        self.assertXmlTagValue('client', 'DUMMY')
        self.assertXmlTagValue('password', '123456')


class InitialTransactionMixin(TransactionMixin):
    
    def test_request_includes_merchant_reference(self):   
        self.make_request()
        self.assertXmlTagValue('merchantreference', '123123')
        
    def test_request_includes_amount_and_currency(self):   
        self.make_request()
        self.assertXmlTagValue('amount', '12.99')
        self.assertXmlTagAttributeValue('amount', 'currency', 'GBP')
        
    def test_request_can_include_authcode(self):
        self.make_request(auth_code='334455')    
        self.assertXmlTagValue('authcode', '334455')
    
    def test_request_includes_card_details(self):   
        self.make_request(start_date='01/10')
        self.assertXmlTagValue('pan', '1000010000000007')
        self.assertXmlTagValue('startdate', '01/10')
        self.assertXmlTagValue('expirydate', '01/12')
        
    def test_request_can_include_issue_number(self):
        self.make_request(issue_number='03')    
        self.assertXmlTagValue('issuenumber', '03')    


class AuthTransactionTests(TestCase, InitialTransactionMixin):
    
    def setUp(self):
        self.init_gateway()
    
    def make_request(self, **kwargs):
        self.gateway.auth(card_number='1000010000000007', 
                          expiry_date='01/12',
                          merchant_reference='123123',
                          currency='GBP',
                          amount=D('12.99'),
                          **kwargs)
        
    def test_request_includes_method(self):
        self.make_request()    
        self.assertXmlTagValue('method', 'auth')
    
    
class PreTransactionTests(TestCase, InitialTransactionMixin):
    
    def setUp(self):
        self.init_gateway()
    
    def make_request(self, **kwargs):
        self.gateway.pre(card_number='1000010000000007', 
                         expiry_date='01/12',
                         merchant_reference='123123',
                         currency='GBP',
                         amount=D('12.99'),
                         **kwargs)    
        
    def test_request_includes_method(self):
        self.make_request()    
        self.assertXmlTagValue('method', 'pre')
        
        
class RefundTransactionTests(TestCase, InitialTransactionMixin):
    
    def setUp(self):
        self.init_gateway()
    
    def make_request(self, **kwargs):
        self.gateway.refund(card_number='1000010000000007', 
                            expiry_date='01/12',
                            merchant_reference='123123',
                            currency='GBP',
                            amount=D('12.99'),
                            **kwargs)    
        
    def test_request_includes_method(self):
        self.make_request()    
        self.assertXmlTagValue('method', 'refund')
    
    
class ErpTransactionTests(TestCase, InitialTransactionMixin):
    
    def setUp(self):
        self.init_gateway()
    
    def make_request(self, **kwargs):
        self.gateway.erp(card_number='1000010000000007', 
                         expiry_date='01/12',
                         merchant_reference='123123',
                         currency='GBP',
                         amount=D('12.99'),
                         **kwargs)    
        
    def test_request_includes_method(self):
        self.make_request()    
        self.assertXmlTagValue('method', 'erp')    
    
    
class CancelTransactionTests(TestCase, TransactionMixin):
    
    def setUp(self):
        self.init_gateway()
    
    def make_request(self, **kwargs):
        self.gateway.cancel(txn_reference='12312333444')
        
    def test_request_includes_method(self):
        self.make_request()    
        self.assertXmlTagValue('method', 'cancel') 
        
    def test_request_includes_reference(self):
        self.make_request()    
        self.assertXmlTagValue('reference', '12312333444') 
        
        
class FulfilTransactionTests(TestCase, TransactionMixin):
    
    def setUp(self):
        self.init_gateway()
    
    def make_request(self, **kwargs):
        self.gateway.fulfil(currency='GBP',
                            amount=D('12.99'),
                            txn_reference='12312333444',
                            auth_code='123444')
        
    def test_request_includes_method(self):
        self.make_request()    
        self.assertXmlTagValue('method', 'fulfil')   
        
    def test_request_includes_reference(self):
        self.make_request()    
        self.assertXmlTagValue('reference', '12312333444') 
        
    def test_request_includes_authcode(self):
        self.make_request()    
        self.assertXmlTagValue('authcode', '123444') 
        
        
class TxnRefundTransactionTests(TestCase, TransactionMixin):
    
    def setUp(self):
        self.init_gateway()
    
    def make_request(self, **kwargs):
        self.gateway.txn_refund(currency='GBP',
                                amount=D('12.99'),
                                txn_reference='12312333444')
        
    def test_request_includes_method(self):
        self.make_request()    
        self.assertXmlTagValue('method', 'txn_refund')   
        
    def test_request_includes_reference(self):
        self.make_request()    
        self.assertXmlTagValue('reference', '12312333444') 
        
        
class Av2CVsTests(TestCase, TransactionMixin):
    
    def setUp(self):
        self.init_gateway(cv2avs=True)
    
    def make_request(self, **kwargs):
        self.gateway.auth(card_number='1000010000000007', 
                          expiry_date='01/12',
                          merchant_reference='123123',
                          currency='GBP',
                          amount=D('12.99'),
                          ccv='234')
        
    def test_ccv_element_in_request(self):
        self.make_request()
        self.assertXmlTagValue('cv2', '234') 
    