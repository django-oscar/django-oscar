import datetime
from xml.dom.minidom import Document, parseString
import httplib
import urllib

from django.conf import settings
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.core.mail import mail_admins

from oscar.core.loading import import_module
import_module('payment.datacash.models', ['OrderTransaction'], locals())
import_module('payment.exceptions', ['TransactionDeclined', 'GatewayError', 
                                     'InvalidGatewayRequestError'], locals())

# Status codes
ACCEPTED, DECLINED, INVALID_CREDENTIALS = '1', '7', '10'


class Gateway(object):

    def __init__(self, client, password, host, cv2avs=False):
        self._client = client
        self._password = password
        self._host = host
        
        # Fraud settings
        self._cv2avs = cv2avs

    def do_request(self, request_xml):
        # Need to fill in HTTP request here
        conn = httplib.HTTPSConnection(self._host, 443, timeout=30)
        headers = {"Content-type": "application/xml",
                   "Accept": ""}
        conn.request("POST", "/Transaction", request_xml, headers)
        response = conn.getresponse()
        response_xml = response.read()
        if response.status != httplib.OK:
            raise GatewayError("Unable to communicate with payment gateway (code: %s, response: %s)" % (response.status, response_xml))
        conn.close()
        
        # Save response XML
        self._last_response_xml = response_xml
        return response_xml

    def _build_request_xml(self, method_name, **kwargs):
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
                
            if self._cv2avs:
                self._add_cv2avs_elements(doc, card, kwargs) 
        
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
        
        # Save XML for later retrieval
        self._last_request_xml = doc.toxml()
        
        return self.do_request(doc.toxml())

    def _add_cv2avs_elements(self, doc, card, kwargs):
        cv2avs = self._create_element(doc, card, 'Cv2Avs')
        if 'ccv' in kwargs:
            self._create_element(doc, cv2avs, 'cv2', kwargs['ccv'])

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
        try:
            ele = doc.getElementsByTagName(tag)[0]
        except IndexError:
            return None
        return ele.firstChild.data

    def _build_response_dict(self, response_xml, extra_elements=None):
        doc = parseString(response_xml)
        response = {'status': int(self._get_element_text(doc, 'status')),
                    'datacash_reference': self._get_element_text(doc, 'datacash_reference'),
                    'merchant_reference': self._get_element_text(doc, 'merchantreference'),
                    'reason': self._get_element_text(doc, 'reason')}
        if extra_elements:
            for tag, key in extra_elements.items():
                response[key] = self._get_element_text(doc, tag)
        return response

    # API

    def auth(self, **kwargs):
        """
        Performs an 'auth' request, which is to debit the money immediately
        as a one-off transaction.
        
        Note that currency should be ISO 4217 Alphabetic format.
        """ 
        self._check_kwargs(kwargs, ['amount', 'currency', 'card_number', 'expiry_date', 'merchant_reference'])
        response_xml = self._build_request_xml('auth', **kwargs)
        return self._build_response_dict(response_xml, {'authcode': 'auth_code'})
        
    def pre(self, **kwargs):
        """
        Performs an 'pre' request, which is to ring-fence the requested money
        so it can be fulfilled at a later time.
        """ 
        self._check_kwargs(kwargs, ['amount', 'currency', 'card_number', 'expiry_date', 'merchant_reference'])
        response_xml = self._build_request_xml('pre', **kwargs)
        return self._build_response_dict(response_xml, {'authcode': 'auth_code'})

    def refund(self, **kwargs):
        self._check_kwargs(kwargs, ['amount', 'currency', 'card_number', 'expiry_date', 'merchant_reference'])
        response_xml = self._build_request_xml('refund', **kwargs)
        return self._build_response_dict(response_xml, {'authcode': 'auth_code'})
        
    def erp(self, **kwargs):
        self._check_kwargs(kwargs, ['amount', 'currency', 'card_number', 'expiry_date', 'merchant_reference'])
        response_xml = self._build_request_xml('erp', **kwargs)
        return self._build_response_dict(response_xml, {'authcode': 'auth_code'})
        
    # "Historic" transaction types    
        
    def cancel(self, txn_reference): 
        response_xml = self._build_request_xml('cancel', txn_reference=txn_reference)
        return self._build_response_dict(response_xml)
    
    def fulfil(self, **kwargs):
        self._check_kwargs(kwargs, ['amount', 'currency', 'txn_reference', 'auth_code'])
        response_xml = self._build_request_xml('fulfil', **kwargs)
        return self._build_response_dict(response_xml)
    
    def txn_refund(self, **kwargs):
        self._check_kwargs(kwargs, ['amount', 'currency', 'txn_reference'])
        response_xml = self._build_request_xml('txn_refund', **kwargs)
        return self._build_response_dict(response_xml)
    
    def last_request_xml(self):
        return self._last_request_xml
    
    def last_response_xml(self):
        return self._last_response_xml
    
    def _check_kwargs(self, kwargs, required_keys):
        for key in required_keys:
            if key not in kwargs:
                raise RuntimeError('You must provide a "%s" argument' % key)


class Facade(object):
    """
    Responsible for dealing with oscar objects
    """
    
    def __init__(self):
        self.gateway = Gateway(settings.DATACASH_CLIENT, settings.DATACASH_PASSWORD, settings.DATACASH_HOST)
    
    def debit(self, order_number, amount, bankcard, basket, billing_address=None):
        with transaction.commit_on_success():
            response = self.gateway.auth(card_number=bankcard.card_number,
                                         expiry_date=bankcard.expiry_date,
                                         amount=amount,
                                         currency='GBP',
                                         merchant_reference=self.generate_merchant_reference(order_number),
                                         ccv=bankcard.ccv)
            
            # Create transaction model irrespective of whether transaction was successful or not
            txn = OrderTransaction.objects.create(order_number=order_number,
                                                  basket=basket,
                                                  method='auth',
                                                  datacash_ref=response['datacash_reference'],
                                                  merchant_ref=response['merchant_reference'],
                                                  amount=amount,
                                                  auth_code=response['auth_code'],
                                                  status=int(response['status']),
                                                  reason=response['reason'],
                                                  request_xml=self.gateway.last_request_xml(),
                                                  response_xml=self.gateway.last_response_xml())
        
        # Test if response is successful
        if response['status'] == INVALID_CREDENTIALS:
            # This needs to notify the administrators straight away
            import pprint
            msg = "Order #%s:\n%s" % (order_number, pprint.pprint(response))
            mail_admins("Datacash credentials are not valid", msg)
            raise InvalidGatewayRequestError("Unable to communicate with payment gateway, please try again later")
        
        if response['status'] == DECLINED:
            raise TransactionDeclined("Your bank declined this transaction, please check your details and try again")
        
        return response['datacash_reference']
        
    def generate_merchant_reference(self, order_number):
        return '%s_%s' % (order_number, datetime.datetime.now().microsecond)
        
        

