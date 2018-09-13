from django.conf.urls import url

from oscar.core.application import DashboardApplication
from oscar.core.loading import get_class


class SystemApplication(DashboardApplication):
    name = None
    default_permissions = ['is_staff']
    
    update_view = get_class('dashboard.system.views', 'ConfigUpdateView')

    def get_urls(self):
        urls = [
            url(r'^$', self.update_view.as_view(), name='system-config'),
        ]
        return self.post_process_urls(urls)


application = SystemApplication()
