from django.core.mail import EmailMessage

from oscar.core.loading import import_module
import_module('order.models', ['CommunicationEvent', 'Email'], locals())


class Dispatcher(object):

    def __init__(self, logger):
        self.logger = logger
    
    def dispatch_order_message(self, user, order, event_type):
        """
        Sends an order-related message.
        
        - order : the order instance
        - event_type : a customer.EventType instance
        """
        if event_type.has_email_templates():
            self.logger.info("Order #%s: sending %s emails" % (order.number, event_type))
            self.send_order_email(user, order, event_type)
        if event_type.has_sms_template():
            self.logger.info("Order #%s: sending %s SMS" % (order.number, event_type))
            self.send_order_sms(user, order, event_type)
        
        # Record communication event against the order    
        CommunicationEvent._default_manager.create(order=order, type=event_type)
        
    def send_order_email(self, user, order, event_type):
        
        if not event_type.has_email_templates():    
            self.logger.warning(" - Unable to send email as event type has no email templates")
            return    
        if not user.email:
            self.logger.warning(" - Unable to send email as user has no email address")
            return    
        email = self.get_email_message(user.email, order, event_type)
        email.send()
        
        # Is user is signed in, record the event for audit
        if user.is_authenticated():
            Email._default_manager.create(user=user, 
                                          subject=email.subject,
                                          body_text=email.body)
        
    def get_email_message(self, to_address, order, event_type):
        return EmailMessage(event_type.get_email_subject_for_order(order),
                            event_type.get_email_body_for_order(order), 
                            to=[to_address])
        
    def send_order_sms(self, user, order, event_type):
        raise NotImplementedError
        