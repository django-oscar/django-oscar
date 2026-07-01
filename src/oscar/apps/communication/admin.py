from django.contrib import admin

from oscar.core.loading import get_model

Email = get_model("communication", "Email")
Notification = get_model("communication", "Notification")
CommunicationEventType = get_model("communication", "CommunicationEventType")


class EmailAdmin(admin.ModelAdmin):
    list_display = ("subject", "email", "user", "date_sent")
    search_fields = ("subject", "user__username", "user__email", "email", "body_text")
    autocomplete_fields = ("user",)


admin.site.register(Email, EmailAdmin)
admin.site.register(Notification)
admin.site.register(CommunicationEventType)
