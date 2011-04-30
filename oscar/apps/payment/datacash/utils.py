import datetime
from xml.dom.minidom import Document, parseString

from django.conf import settings


class Gateway(object):

    def __init__(self, client, password):
        self._client = client
        self._password = password

    def do_request(self, request_xml):
        # Need to fillin HTTP request here
        pass

    def _initial_transaction(self, method_name, **kwargs):
        """
        Builds the XML for a 'initial' transaction
        """
        doc = Document()
        req = self._create_element(doc, doc, 'Request')
        
        # Authentication
        auth = self._create_element(doc, req, 'Authentication')
        self._create_element(doc, auth, 'client', self._client)
        self._create_element(doc, auth, 'password', self._password)
            
        # Transaction    
        txn = self._create_element(doc, req, 'Transaction') 
        
        # CardTxn
        if 'card_number' in kwargs:
            card_txn = self._create_element(doc, txn, 'CardTxn')
            self._create_element(doc, card_txn, 'method', method_name)
            
            card = self._create_element(doc, card_txn, 'Card')
            self._create_element(doc, card, 'pan', kwargs['card_number'])
            self._create_element(doc, card, 'expirydate', kwargs['expiry_date'])
            
            if 'start_date' in kwargs:
                self._create_element(doc, card, 'startdate', kwargs['start_date'])
            
            if 'issue_number' in kwargs:
                self._create_element(doc, card, 'issuenumber', kwargs['issue_number'])
          
            if 'auth_code' in kwargs:
                self._create_element(doc, card, 'authcode', kwargs['auth_code'])
        
        # HistoricTxn
        if 'txn_reference' in kwargs:
            historic_txn = self._create_element(doc, txn, 'HistoricTxn')
            self._create_element(doc, historic_txn, 'reference', kwargs['txn_reference'])
            self._create_element(doc, historic_txn, 'method', method_name)
            if 'auth_code' in kwargs:
                self._create_element(doc, historic_txn, 'authcode', kwargs['auth_code'])
        
        # TxnDetails
        if 'amount' in kwargs:
            txn_details = self._create_element(doc, txn, 'TxnDetails')
            if 'merchant_reference' in kwargs:
                self._create_element(doc, txn_details, 'merchantreference', kwargs['merchant_reference'])
            self._create_element(doc, txn_details, 'amount', str(kwargs['amount']), {'currency': kwargs['currency']})
        
        return self.do_request(doc.toxml())

    def _create_element(self, doc, parent, tag, value=None, attributes=None):
        """
        Creates an XML element
        """
        ele = doc.createElement(tag)
        parent.appendChild(ele)
        if value:
            text = doc.createTextNode(value)
            ele.appendChild(text)
        if attributes:
            [ele.setAttribute(k, v) for k,v in attributes.items()]
        return ele
    
    def _get_element_text(self, doc, tag):
        ele = doc.getElementsByTagName(tag)[0]
        return ele.firstChild.data

    def auth(self, **kwargs):
        """
        Performs an 'auth' request, which is to debit the money immediately
        as a one-off transaction.
        
        Note that currency should be ISO 4217 Alphabetic format.
        """ 
        response_xml = self._initial_transaction('auth', **kwargs)
        doc = parseString(response_xml)
        response = {'status': self._get_element_text(doc, 'status'),
                    'datacash_reference': self._get_element_text(doc, 'datacash_reference'),
                    'merchant_reference': self._get_element_text(doc, 'merchantreference')}
        return response
        
        
    def pre(self, **kwargs):
        """
        Performs an 'pre' request, which is to ring-fence the requested money
        so it can be fulfilled at a later time.
        """ 
        return self._initial_transaction('pre', **kwargs)

    def refund(self, **kwargs):
        return self._initial_transaction('refund', **kwargs)
        
    def erp(self, **kwargs):
        return self._initial_transaction('erp', **kwargs)
        
    # "Historic" transaction types    
        
    def cancel(self, txn_reference): 
        return self._initial_transaction('cancel', txn_reference=txn_reference)
    
    def fulfil(self, **kwargs):
        return self._initial_transaction('fulfil', **kwargs) 
    
    def txn_refund(self, **kwargs):
        return self._initial_transaction('txn_refund', **kwargs) 


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
        
        

