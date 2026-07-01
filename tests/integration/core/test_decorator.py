import warnings

from django.contrib.auth.models import AnonymousUser, Permission
from django.test import TestCase

from oscar.core.decorators import deprecated
from oscar.test import factories
from oscar.views.decorators import check_permissions


class TestPermissionsDecorator(TestCase):
    def test_empty_permissions_passes(self):
        user = factories.UserFactory.build()
        self.assertTrue(check_permissions(user, []))

    def test_properties_are_checked(self):
        staff_user = factories.UserFactory.build(is_staff=True)
        non_staff_user = factories.UserFactory.build(is_staff=False)
        self.assertTrue(check_permissions(staff_user, ["is_staff"]))
        self.assertFalse(check_permissions(non_staff_user, ["is_staff"]))

    def test_methods_are_checked(self):
        anonymous_user = AnonymousUser()
        known_user = factories.UserFactory.build()
        self.assertTrue(check_permissions(anonymous_user, ["is_anonymous"]))
        self.assertFalse(check_permissions(known_user, ["is_anonymous"]))

    def test_permissions_are_checked(self):
        user_with_perm = factories.UserFactory()
        user_without_perm = factories.UserFactory()
        perm = Permission.objects.get(
            content_type__app_label="address", codename="add_country"
        )
        user_with_perm.user_permissions.add(perm)
        self.assertTrue(check_permissions(user_with_perm, ["address.add_country"]))
        self.assertFalse(check_permissions(user_without_perm, ["address.add_country"]))


class TestDeprecatedDecorator(TestCase):
    def test_decorate_function(self):
        @deprecated
        def func():
            return True

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.assertTrue(func())
            assert len(caught) == 1
            assert issubclass(caught[0].category, DeprecationWarning)

    def test_decorate_class(self):
        class Cls(object):
            val = False

            def __init__(self):
                self.val = True

        Deprecated = deprecated(Cls)  # noqa

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            obj = Deprecated()
            self.assertTrue(obj.val)
            assert len(caught) == 1
            assert issubclass(caught[0].category, DeprecationWarning)

    def test_subclass_decorated(self):
        class Cls(object):
            val = False

            def __init__(self):
                self.val = True

        Deprecated = deprecated(Cls)  # noqa

        class SubCls(Deprecated):
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            obj = SubCls()
            self.assertTrue(obj.val)
            assert len(caught) == 1
            assert issubclass(caught[0].category, DeprecationWarning)
