from django.apps import AppConfig



class PartnerConfig(AppConfig):
    app_label = 'partner'
    name = 'oscar.apps.partner'

    def ready(self):
        from oscar.apps.partner import receivers

        receivers.register()

        return super(PartnerConfig, self).ready()
