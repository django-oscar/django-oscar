import mock
from decimal import Decimal as D
from xml.dom.minidom import parseString

from django.test import TestCase

from oscar.apps.payment.datacash.utils import Gateway


class AuthResponseHandlingTests(TestCase):
    
    success_response_xml = """<?xml version="1.0" encoding="UTF-8" ?>
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
    
    def setUp(self):
        self.gateway = Gateway(client="DUMMY", password="123456", host="dummyhost.com",)
        self.gateway.do_request = mock.Mock()
    
    def test_success_auth_response(self):
        self.gateway.do_request.return_value = self.success_response_xml
        response = self.gateway.auth(card_number='1000010000000007', 
                                     expiry_date='01/12',
                                     merchant_reference='1000001',
                                     currency='GBP',
                                     amount=D('12.99'))
        self.assertEquals(1, response['status'])
        self.assertEquals('3000000088888888', response['datacash_reference'])
        self.assertEquals('1000001', response['merchant_reference'])
        self.assertEquals('060642', response['auth_code'])
        self.assertEquals('ACCEPTED', response['reason'])
        
    def test_success_pre_response(self):
        self.gateway.do_request.return_value = self.success_response_xml
        response = self.gateway.pre(card_number='1000010000000007', 
                                     expiry_date='01/12',
                                     merchant_reference='1000001',
                                     currency='GBP',
                                     amount=D('12.99'))
        self.assertEquals(1, response['status'])
        self.assertEquals('3000000088888888', response['datacash_reference'])
        self.assertEquals('1000001', response['merchant_reference'])
        self.assertEquals('060642', response['auth_code'])
        self.assertEquals('ACCEPTED', response['reason'])
        
    def test_declined_auth_response(self):
        response_xml = """<?xml version="1.0" encoding="UTF-8" ?>
<Response>
    <CardTxn>
        <authcode>DECLINED</authcode>
        <card_scheme>Mastercard</card_scheme>
        <country>United Kingdom</country>
    </CardTxn>
    <datacash_reference>4400200045583767</datacash_reference>
    <merchantreference>AA004630</merchantreference>
    <mode>TEST</mode>
    <reason>DECLINED</reason>
    <status>7</status>
    <time>1169223906</time>
</Response>"""
        self.gateway.do_request.return_value = response_xml
        response = self.gateway.auth(card_number='1000010000000007', 
                                     expiry_date='01/12',
                                     merchant_reference='1000001',
                                     currency='GBP',
                                     amount=D('12.99'))
        self.assertEquals(7, response['status'])
        self.assertEquals('4400200045583767', response['datacash_reference'])
        self.assertEquals('AA004630', response['merchant_reference'])
        self.assertEquals('DECLINED', response['auth_code'])
        self.assertEquals('DECLINED', response['reason'])

    def test_successful_cancel_response(self):
        response_xml = """<?xml version="1.0" encoding="UTF-8" ?>
<Response>
    <datacash_reference>4900200000000001</datacash_reference>
    <merchantreference>4900200000000001</merchantreference>
    <mode>TEST</mode>
    <reason>CANCELLED OK</reason>
    <status>1</status>
    <time>1151567456</time>
</Response>"""
        self.gateway.do_request.return_value = response_xml
        response = self.gateway.cancel(txn_reference='4900200000000001')
        self.assertEquals(1, response['status'])
        self.assertEquals('4900200000000001', response['datacash_reference'])
        self.assertEquals('4900200000000001', response['merchant_reference'])
        self.assertEquals('CANCELLED OK', response['reason'])
        
    def test_successful_fulfil_response(self):
        response_xml = """<?xml version="1.0" encoding="UTF-8" ?>
<Response>
    <datacash_reference>3900200000000001</datacash_reference>
    <merchantreference>3900200000000001</merchantreference>
    <mode>LIVE</mode>
    <reason>FULFILLED OK</reason>
    <status>1</status>
    <time>1071567356</time>
</Response>
"""
        self.gateway.do_request.return_value = response_xml
        response = self.gateway.fulfil(txn_reference='3900200000000001', 
                                     merchant_reference='1000001',
                                     currency='GBP',
                                     amount=D('12.99'),
                                     auth_code='asdf')
        self.assertEquals(1, response['status'])
        self.assertEquals('3900200000000001', response['datacash_reference'])
        self.assertEquals('3900200000000001', response['merchant_reference'])
        self.assertEquals('FULFILLED OK', response['reason'])



        
    
 