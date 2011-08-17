from django.db import models
from django.template.loader import get_template
from django.template import Template, Context

class CommunicationTypeManager(models.Manager):
    def get_and_render(self, code, context):
        subject_template = None
        body_template = None
        html_template = None
        sms_template = None
        
        try:
            commtype = self.get(code=code)
            if commtype.email_subject_template:
                subject_template = Template(commtype.email_subject_template)
            if commtype.email_body_template:
                body_template =  Template(commtype.email_body_template)
            if commtype.email_body_html_template:
                html_template = Template(commtype.email_body_html_template)
            if commtype.sms_template:
                sms_template = Template(commtype.sms_template)
        except self.model.DoesNotExist:
            # We didn't find a CommunicationType for the code, so we use the template loader instead
            code = code.lower()

            subject_template = get_template('customer/emails/commtype_%s_subject.txt' % code)
            body_template = get_template('customer/emails/commtype_%s_body.txt' % code)
            html_template = get_template('customer/emails/commtype_%s_body.html' % code)
            sms_template = get_template('customer/emails/commtype_%s_sms.txt' % code)

        result = {
            'subject': None,
            'body': None,
            'html': None,
            'sms': None,
        }
        
        if subject_template:
            result['subject'] = subject_template.render(Context(context))
        if body_template:
            result['body'] = body_template.render(Context(context))
        if html_template:
            result['html'] = html_template.render(Context(context))
        if sms_template:
            result['sms'] = sms_template.render(Context(context))
            
        return result
