from decimal import Decimal as D
from xml.dom.minidom import parseString
import datetime

from django.test import TestCase
from django.conf import settings

from oscar.apps.payment.datacash.models import OrderTransaction
from oscar.apps.payment.datacash.utils import Gateway, Facade
from oscar.apps.payment.utils import Bankcard


class OrderTransactionTests(TestCase):
    
    def test_cc_numbers_are_not_saved(self):
        
        request_xml = """<?xml version="1.0" encoding="UTF-8" ?>
<Request>
    <Authentication>
        <client>99000001</client>
        <password>boomboom</password>
    </Authentication>
    <Transaction>
    <CardTxn>
        <Card>
            <pan>1000011100000004</pan>
            <expirydate>04/06</expirydate>
            <startdate>01/04</startdate>
        </Card>
        <method>auth</method>
    </CardTxn>
    <TxnDetails>
        <merchantreference>1000001</merchantreference>
        <amount currency="GBP">95.99</amount>
    </TxnDetails>
    </Transaction>
</Request>"""

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
        
        txn = OrderTransaction.objects.create(order_number='1000',
                                              method='auth',
                                              datacash_ref='3000000088888888',
                                              merchant_ref='1000001',
                                              amount=D('95.99'),
                                              status=1,
                                              reason='ACCEPTED',
                                              request_xml=request_xml,
                                              response_xml=response_xml)
        doc = parseString(txn.request_xml)
        element = doc.getElementsByTagName('pan')[0]
        self.assertEqual('XXXXXXXXXXXX0004', element.firstChild.data)
        
        
class IntegrationTests(TestCase):
    
    def _test_for_smoke(self):
        gateway = Gateway(settings.DATACASH_CLIENT, 
                          settings.DATACASH_PASSWORD,
                          host=settings.DATACASH_HOST)
        response = gateway.auth(card_number='1000011000000005',
                                expiry_date='01/13',
                                amount=D('50.00'),
                                currency='GBP',
                                merchant_reference='123456_%s' % datetime.datetime.now().microsecond)
        print response
        
    def _test_adapter(self):
        bankcard = Bankcard(card_number='1000011000000005', expiry_date='01/13')
    
        dc_facade = Facade()
        reference = dc_facade.debit('102910', D('23.00'), bankcard)
        print reference
        
        OrderTransaction.objects.get(order_number='102910')
        
    