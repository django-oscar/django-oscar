from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractEmail(models.Model):
    
    user = models.ForeignKey('auth.User', related_name='emails')
    subject = models.TextField(_('Subject'), max_length=255)
    body_text = models.TextField()
    body_html = models.TextField(blank=True, null=True)
    date_sent = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return u"Email to %s with subject '%s'" % (self.user.username, self.subject)