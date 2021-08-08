from oscar.core import application


class TestConfig(application.OscarConfig):
    name = 'tests._site.apps.myapp'

    namespace = 'testapp'
    default_permissions = 'is_superuser'
    permissions_map = {
        'index': 'is_staff',
    }
