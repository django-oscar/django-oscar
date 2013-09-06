# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.db.models import get_model
from oscar.test.factories import create_product
from oscar.test.testcases import ClientTestCase

WishList = get_model('wishlists', 'WishList')


class TestWishlists(ClientTestCase):

    def setUp(self):
        super(TestWishlists, self).setUp()
        self.product = create_product()

    def test_add_to_wishlist_button_is_displayed(self):
        resp = self.client.get(self.product.get_absolute_url())
        self.assertContains(resp, reverse('customer:wishlists-create',
                                          args=[self.product.pk]))

    def test_add_a_product_to_wishlist(self):
        resp = self.client.get(reverse('customer:wishlists-create',
                                       args=[self.product.pk]))
        self.assertIsOk(resp)
        self.assertEqual(WishList.objects.count(), 0)
        self.assertEqual(self.product.wishlists_lines.count(), 0)
        # not done here, need to submit the wishlist
        # and verify it can be deleted
        data = {'name': 'Shopping list for Santa Claus'}
        resp = self.client.post(reverse('customer:wishlists-create',
                                        args=[self.product.pk]), data)
        self.assertIsRedirect(resp)
        self.assertEqual(WishList.objects.count(), 1)
        self.assertEqual(self.product.wishlists_lines.count(), 1)
        wishlist = WishList.objects.all()[0]
        resp = self.client.post(reverse('customer:wishlists-delete',
                                        args=[wishlist.key, ]))
        self.assertIsRedirect(resp)
        self.assertEqual(WishList.objects.count(), 0)
        self.assertEqual(self.product.wishlists_lines.count(), 0)








