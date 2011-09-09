import logging

from django.core.mail import EmailMessage, EmailMultiAlternatives

from oscar.core.loading import import_module
import_module('order.models', ['CommunicationEvent',], locals())
import_module('customer.models', ['Email'], locals())


class Dispatcher(object):

    def __init__(self, logger=None):
        if not logger:
            logger = logging.getLogger(__name__)
        self.logger = logger


    def dispatch_direct_messages(self, recipient, messages):
        """
        Dispatch one-off messages to explicitly specified recipient(s)
        """
        if messages['subject'] and messages['body']:
            self.send_email_messages(recipient, messages)
    
    
    def dispatch_order_messages(self, order, messages, event_type):
        """
        Dispatch order-related messages to the customer
        """
        self.dispatch_messages(order.user, messages)
            
        # Create order comms event for audit
        if event_type:
            CommunicationEvent._default_manager.create(order=order, type=event_type)
    
    
    def dispatch_messages(self, user, messages):
        """
        Send messages
        """
        if messages['subject'] and messages['body']:
            self.send_user_email_messages(user, messages)
        if messages['sms']:
            self.send_text_message(user, messages['sms'])
            
    
    def send_user_email_messages(self, user, messages):
        """
        Sends message to the registered user / customer and collects data in database
        """
        if not user.email:
            self.logger.warning("Unable to send email messages as user #%d has no email address", user.id)
            return
        
        email = self.send_email_messages(user.email, messages)
        
        # Is user is signed in, record the event for audit
        if user.is_authenticated():
            Email._default_manager.create(user=user, 
                                          subject=email.subject,
                                          body_text=email.body,
                                          body_html=messages['html'])
                                   
    
    def send_email_messages(self, recipient, messages):
        """
        Plain email sending to the specified recipient
        """
        # Determine whether we are sending a HTML version too
        if messages['html']:
            email = EmailMultiAlternatives(messages['subject'],
                                           messages['body'],
                                           to=[recipient])
            email.attach_alternative(messages['html'], "text/html")
        else:
            email = EmailMessage(messages['subject'],
                                 messages['body'],
                                 to=[recipient])
        self.logger.info("Sending email to %s" % recipient)
        email.send()
        
        return email
    
        
    def send_text_message(self, user, event_type):
        raise NotImplementedError

