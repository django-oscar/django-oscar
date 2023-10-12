from django.contrib import admin

from oscar.core.loading import get_model

Email = get_model("communication", "Email")
Notification = get_model("communication", "Notification")
CommunicationEventType = get_model("communication", "CommunicationEventType")

admin.site.register(Email)
admin.site.register(Notification)
admin.site.register(CommunicationEventType)
