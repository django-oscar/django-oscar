from oscar.core.application import Application


class TestApplication(Application):

    name = 'testapp'
    default_permissions = 'is_superuser'
    permissions_map = {
        'index': 'is_staff',
    }


application = TestApplication()
