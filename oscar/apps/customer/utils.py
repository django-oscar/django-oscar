from django.core.mail import EmailMessage, EmailMultiAlternatives

from oscar.core.loading import import_module
import_module('order.models', ['CommunicationEvent',], locals())
import_module('customer.models', ['Email'], locals())


class Dispatcher(object):

    def __init__(self, logger):
        self.logger = logger
    
    def dispatch_order_messages(self, order, messages, event_type):
        self.dispatch_messages(order.user, messages)
        # Create order comms event for audit
        CommunicationEvent._default_manager.create(order=order, type=event_type)
    
    def dispatch_messages(self, user, messages):
        """
        Send messages
        """
        if messages['subject'] and messages['body']:
            self.send_email_messages(user, messages)
        if messages['sms']:
            self.send_text_message(user, messages['sms'])
                                   
    def send_email_messages(self, user, messages):
        if not user.email:
            self.logger.warning("Unable to send email messages as user #%d has no email address", user.id)
            return
        
        # Determine whether we are sending a HTML version too
        if messages['html']:
            email = EmailMultiAlternatives(messages['subject'],
                                           messages['body'],
                                           to=[user.email])
            email.attach_alternative(messages['html'], "text/html")
        else:
            email = EmailMessage(messages['subject'],
                                 messages['body'],
                                 to=[user.email])
        self.logger.info("Sending email to %s" % user.email)
        email.send()    
        
        # Is user is signed in, record the event for audit
        if user.is_authenticated():
            Email._default_manager.create(user=user, 
                                          subject=email.subject,
                                          body_text=email.body,
                                          body_html=messages['html'])
        
    def send_text_message(self, user, event_type):
        raise NotImplementedError
        