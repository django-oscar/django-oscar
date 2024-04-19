from oscar.core.application import OscarConfig


class TestConfig(OscarConfig):
    name = "tests._site.apps.myapp"

    namespace = "testapp"
    default_permissions = "is_superuser"
    permissions_map = {
        "index": "is_staff",
    }
