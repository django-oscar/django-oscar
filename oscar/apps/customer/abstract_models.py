from django.db import models
from django.utils.translation import ugettext_lazy as _


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
    
    # Template content for emails
    email_subject_template = models.CharField(max_length=255, blank=True)
    email_body_template = models.TextField(blank=True, null=True)
    email_body_html_template = models.TextField(blank=True, null=True)
    
    # Template content for SMS messages
    sms_template = models.CharField(max_length=170, blank=True)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Communication event types")
        
    def __unicode__(self):
        return self.name    
    
    def has_email_templates(self):
        return self.email_subject_template and self.email_body_template
    
    def get_email_subject_for_order(self, order, **kwargs):
        return self._merge_template_with_context(self.email_subject_template, order, **kwargs)
    
    def get_email_body_for_order(self, order, **kwargs):
        return self._merge_template_with_context(self.email_body_template, order, **kwargs)
    
    def _merge_template_with_context(self, template, order, **kwargs):
        ctx = {'order': order}
        ctx.update(**kwargs)
        return Template(template).render(Context(ctx))
    