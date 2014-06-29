from django.apps import AppConfig

from oscar.apps.partner import receivers


class PartnerConfig(AppConfig):
    app_label = 'partner'
    name = 'oscar.apps.partner'

    def ready(self):
        receivers.register()

        return super(PartnerConfig, self).ready()
