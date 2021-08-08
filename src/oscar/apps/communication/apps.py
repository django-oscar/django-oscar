from django.utils.translation import gettext_lazy as _

from oscar.core import application


class CommunicationConfig(application.OscarConfig):
    label = 'communication'
    name = 'oscar.apps.communication'
    verbose_name = _('Communication')
