from decimal import Decimal as D
from unittest.mock import patch

from django.urls import reverse

from oscar.apps.basket.models import Basket
from oscar.apps.order.models import Order
from oscar.apps.partner import strategy
from oscar.core.compat import get_user_model
from oscar.test.factories import create_order, create_product
from oscar.test.testcases import WebTestCase

User = get_user_model()


class TestASignedInUser(WebTestCase):
    email = "customer@example.com"
    password = "cheeseshop"

    def setUp(self):
        self.user = User.objects.create_user("_", self.email, self.password)
        self.order = create_order(user=self.user)

    def test_can_view_their_profile(self):
        response = self.app.get(reverse("customer:profile-view"), user=self.user)
        self.assertEqual(200, response.status_code)
        self.assertTrue(self.email in response.content.decode("utf8"))

    def test_can_delete_their_profile(self):
        user_id = self.user.id
        order_id = self.order.id

        profile = self.app.get(reverse("customer:profile-view"), user=self.user)
        delete_confirm = profile.click(linkid="delete_profile")
        form = delete_confirm.forms["delete_profile_form"]
        form["password"] = self.password
        form.submit()

        # Ensure user is deleted
        users = User.objects.filter(id=user_id)
        self.assertEqual(0, len(users))

        # Ensure order isn't deleted
        users = User.objects.filter(id=user_id)
        orders = Order.objects.filter(id=order_id)
        self.assertEqual(1, len(orders))

    def test_can_update_their_name(self):
        profile_form_page = self.app.get(
            reverse("customer:profile-update"), user=self.user
        )
        self.assertEqual(200, profile_form_page.status_code)
        form = profile_form_page.forms["profile_form"]
        form["first_name"] = "Barry"
        form["last_name"] = "Chuckle"
        response = form.submit()
        self.assertRedirects(response, reverse("customer:profile-view"))

    def test_can_update_their_email_address_and_name(self):
        profile_form_page = self.app.get(
            reverse("customer:profile-update"), user=self.user
        )
        self.assertEqual(200, profile_form_page.status_code)
        form = profile_form_page.forms["profile_form"]
        form["email"] = "new@example.com"
        form["first_name"] = "Barry"
        form["last_name"] = "Chuckle"
        response = form.submit()
        self.assertRedirects(response, reverse("customer:profile-view"))

        user = User.objects.get(id=self.user.id)
        self.assertEqual("new@example.com", user.email)
        self.assertEqual("Barry", user.first_name)
        self.assertEqual("Chuckle", user.last_name)

    def test_cant_update_their_email_address_if_it_already_exists(self):
        # create a user to "block" new@example.com
        User.objects.create_user(
            username="testuser", email="new@example.com", password="somerandompassword"
        )
        self.assertEqual(User.objects.count(), 2)

        for email in ["new@example.com", "New@Example.com"]:
            profile_form_page = self.app.get(
                reverse("customer:profile-update"), user=self.user
            )
            form = profile_form_page.forms["profile_form"]
            form["email"] = email
            form["first_name"] = "Barry"
            form["last_name"] = "Chuckle"
            response = form.submit()

            # assert that the original user's email address is unchanged
            user = User.objects.get(id=self.user.id)
            self.assertEqual(self.email, user.email)
            self.assertEqual(
                User.objects.filter(email__iexact="new@example.com").count(), 1
            )
            self.assertContains(
                response, "A user with this email address already exists"
            )

    def test_can_change_their_password(self):
        new_password = "bubblesgopop"
        password_form_page = self.app.get(
            reverse("customer:change-password"), user=self.user
        )
        self.assertEqual(200, password_form_page.status_code)
        form = password_form_page.forms["change_password_form"]
        form["old_password"] = self.password
        form["new_password1"] = form["new_password2"] = new_password
        response = form.submit()
        self.assertRedirects(response, reverse("customer:profile-view"))
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertTrue(updated_user.check_password(new_password))

    def test_can_reorder_a_previous_order(self):
        order_history_page = self.app.get(
            reverse("customer:order", args=[self.order.number]), user=self.user
        )
        form = order_history_page.forms["order_form_%d" % self.order.id]
        form.submit()

        basket = Basket.open.get(owner=self.user)
        basket.strategy = strategy.Default()
        self.assertEqual(1, basket.all_lines().count())

    def test_can_reorder_a_previous_order_line(self):
        order_history_page = self.app.get(
            reverse("customer:order", kwargs={"order_number": self.order.number}),
            user=self.user,
        )
        line = self.order.lines.all()[0]
        form = order_history_page.forms["line_form_%d" % line.id]
        form.submit()

        basket = Basket.open.get(owner=self.user)
        basket.strategy = strategy.Default()
        self.assertEqual(1, basket.all_lines().count())

    def test_cannot_reorder_an_out_of_stock_product(self):
        line = self.order.lines.all()[0]
        line.stockrecord.num_in_stock = 0
        line.stockrecord.save()

        order_history_page = self.app.get(
            reverse("customer:order", args=[self.order.number]), user=self.user
        )
        form = order_history_page.forms["order_form_%d" % self.order.id]
        form.submit()

        basket = Basket.open.get(owner=self.user)
        self.assertEqual(0, basket.all_lines().count())


class TestReorderingOrderLines(WebTestCase):
    @patch("django.conf.settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD", 1)
    def test_cannot_reorder_when_basket_maximum_exceeded(self):
        order = create_order(user=self.user)
        line = order.lines.all()[0]

        product = create_product(price=D("12.00"))
        product_page = self.get(line.product.get_absolute_url())
        product_page.forms["add_to_basket_form"].submit()

        basket = Basket.objects.all()[0]
        basket.strategy = strategy.Default()
        self.assertEqual(len(basket.all_lines()), 1)

        # Try to reorder the whole order
        order_page = self.get(reverse("customer:order", args=(order.number,)))
        order_page.forms["order_form_%s" % order.id].submit()

        self.assertEqual(len(basket.all_lines()), 1)
        self.assertNotEqual(line.product.pk, product.pk)

    @patch("django.conf.settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD", 1)
    def test_cannot_reorder_line_when_basket_maximum_exceeded(self):
        order = create_order(user=self.user)
        line = order.lines.all()[0]

        product = create_product(price=D("12.00"))
        product_page = self.get(line.product.get_absolute_url())
        product_page.forms["add_to_basket_form"].submit()

        basket = Basket.objects.all()[0]
        basket.strategy = strategy.Default()
        self.assertEqual(len(basket.all_lines()), 1)

        # Try to reorder a line
        order_page = self.get(reverse("customer:order", args=(order.number,)))
        order_page.forms["line_form_%s" % line.id].submit()

        self.assertEqual(len(basket.all_lines()), 1)
        self.assertNotEqual(line.product.pk, product.pk)
