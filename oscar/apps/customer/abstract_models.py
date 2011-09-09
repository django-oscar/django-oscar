from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context, TemplateDoesNotExist
from django.template.loader import get_template

from oscar.apps.customer.managers import CommunicationTypeManager


class AbstractEmail(models.Model):
    """
    This is a record of all emails sent to a customer.
    Normally, we only record order-related emails.
    """
    user = models.ForeignKey('auth.User', related_name='emails')
    subject = models.TextField(_('Subject'), max_length=255)
    body_text = models.TextField()
    body_html = models.TextField(blank=True, null=True)
    date_sent = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u"Email to %s with subject '%s'" % (self.user.username, self.subject)


class AbstractCommunicationEventType(models.Model):
    
    # Code used for looking up this event programmatically.
    # eg. PASSWORD_RESET
    code = models.SlugField(max_length=128)
    
    # Name is the friendly description of an event for use in the admin
    name = models.CharField(max_length=255)
    
    # We allow communication types to be categorised
    ORDER_RELATED = 'Order related'
    USER_RELATED = 'User related'
    category = models.CharField(max_length=255, default=ORDER_RELATED)
    
    # Template content for emails
    email_subject_template = models.CharField(max_length=255, blank=True)
    email_body_template = models.TextField(blank=True, null=True)
    email_body_html_template = models.TextField(blank=True, null=True, help_text="HTML template")
    
    # Template content for SMS messages
    sms_template = models.CharField(max_length=170, blank=True, help_text="SMS template")
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    objects = CommunicationTypeManager()
    
    # File templates
    email_subject_template_file = 'customer/emails/commtype_%s_subject.txt'
    email_body_template_file = 'customer/emails/commtype_%s_body.txt'
    email_body_html_template_file = 'customer/emails/commtype_%s_body.html'
    sms_template_file = 'customer/sms/commtype_%s_body.txt'
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Communication event types")

    def get_messages(self, ctx=None):
        """
        Return a dict of templates with the context merged in

        We look first at the field templates but fail over to 
        a set of file templates.  
        """
        if ctx is None:
            ctx = {}
        code = self.code.lower()
        # Build a dict of message name to Template instance
        templates = {'subject': 'email_subject_template',
                     'body': 'email_body_template',
                     'html': 'email_body_html_template',
                     'sms': 'sms_template'}
        for name, attr_name in templates.items():
            field = getattr(self, attr_name, None)
            if field:
                templates[name] = Template(field)
            else:
                template_name = getattr(self, "%s_file" % attr_name) % code
                try:
                    templates[name] = get_template(template_name)
                except TemplateDoesNotExist:
                    templates[name] = None
        
        messages = {}
        for name, template in templates.items():
            messages[name] = template.render(Context(ctx)) if template else ''

        # Ensure the email subject doesn't contain any newlines
        messages['subject'] = messages['subject'].replace("\n", "")

        return messages
        
    def __unicode__(self):
        return self.name   
    
    def is_order_related(self):
        return self.category == self.ORDER_RELATED
    
    def is_user_related(self):
        return self.category == self.USER_RELATED 
    