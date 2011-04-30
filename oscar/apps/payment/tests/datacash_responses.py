import mock
from decimal import Decimal as D
from xml.dom.minidom import parseString

from django.test import TestCase

from oscar.apps.payment.datacash.utils import Gateway


class AuthResponseHandlingTests(TestCase):
    
    def setUp(self):
        self.gateway = Gateway(client="DUMMY", password="123456")
        self.gateway.do_request = mock.Mock()
        
    def test_success_response(self):
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
        self.gateway.do_request.return_value = response_xml
        response = self.gateway.auth(card_number='1000010000000007', 
                                     expiry_date='01/12',
                                     merchant_reference='123123',
                                     currency='GBP',
                                     amount=D('12.99'))
        self.assertEquals('1', response['status'])
        self.assertEquals('3000000088888888', response['datacash_reference'])
        self.assertEquals('1000001', response['merchant_reference'])
        
    
 