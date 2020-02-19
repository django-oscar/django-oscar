from django.contrib import admin

from oscar.core.loading import get_model

CommunicationEventType = get_model('communication', 'CommunicationEventType')
Email = get_model('communication', 'Email')


admin.site.register(Email)
admin.site.register(CommunicationEventType)
