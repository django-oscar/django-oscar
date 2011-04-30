import datetime
from xml.dom.minidom import Document

from django.conf import settings


class Gateway(object):

    def __init__(self, client, password):
        self._client = client
        self._password = password

    def do_request(self, request_xml):
        pass

    def create_xml_doc(self):
        
        
        return doc

    def auth(self, card_number, expiry_date, amount, currency, merchant_reference, start_date=None):
        doc = Document()
        req = doc.createElement('Request')
        doc.appendChild(req)
        
        auth = doc.createElement('Authentication')
        req.appendChild(auth)
        
        client = doc.createElement('client')
        auth.appendChild(client)
        client_text = doc.createTextNode(self._client)
        client.appendChild(client_text)
        
        pw = doc.createElement('password')
        auth.appendChild(pw)
        pw_text = doc.createTextNode(self._password)
        pw.appendChild(pw_text)
            
        txn = doc.createElement('Transaction')
        req.appendChild(txn)
        card_txn = doc.createElement('CardTxn')
        txn.appendChild(card_txn)
        card = doc.createElement('Card')
        card_txn.appendChild(card)
        
        pan = doc.createElement('pan')
        card.appendChild(pan)
        pan_text = doc.createTextNode(card_number)
        pan.appendChild(pan_text)
        
        expiry = doc.createElement('expirydate')
        card.appendChild(expiry)
        expiry_text = doc.createTextNode(expiry_date)
        expiry.appendChild(expiry_text)
        
        if start_date:
            start = doc.createElement('startdate')
            card.appendChild(start)
            start_text = doc.createTextNode(start_date)
            start.appendChild(start_text)
        
        txn_details = doc.createElement('TxnDetails')
        txn.appendChild(txn_details)
        
        merchant = doc.createElement('merchantreference')
        txn_details.appendChild(merchant)
        merchant_text = doc.createTextNode(merchant_reference)
        merchant.appendChild(merchant_text)
        
        amount_ele = doc.createElement('amount')
        txn_details.appendChild(amount_ele)
        amount_text = doc.createTextNode(str(amount))
        amount_ele.appendChild(amount_text)
        amount_ele.setAttribute('currency', currency)
        
        method = doc.createElement('method')
        card_txn.appendChild(method)
        method_text = doc.createTextNode('auth')
        method.appendChild(method_text)
        
        self.do_request(doc.toxml())

    def pre(self, request):
        pass

    def refund(self, request):
        pass


class Adapter(object):
    """
    Responsible for dealing with oscar objects
    """
    
    def __init__(self):
        self.gateway = Gateway(settings.OSCAR_DATACASH_CLIENT, settings.OSCAR_DATACASH_PASSWORD)
    
    def auth(self, order_number, amount, bankcard, billing_address):
        response = self.gateway.auth(pan=bankcard.pan,
                                     expiry_date=bankcard.expiry_date,
                                     merchant_reference=self.generate_merchant_reference(order_number))
        
    def generate_merchant_reference(self, order_number):
        return '%s_%s' % (order_number, datetime.datetime.now().microsecond)
        
        

