from django.test import TestCase
from django.db.models import get_model
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from django_dynamic_fixture import get

from oscar.test import ClientTestCase

ProductReview = get_model('reviews', 'productreview')


class ReviewsDashboardTests(ClientTestCase):
    is_staff = True

    def test_reviews_dashboard_is_accessible_to_staff(self):
        url = reverse('dashboard:reviews-list')
        response = self.client.get(url)
        self.assertIsOk(response)

    def test_bulk_editing_review_status(self):
        url = reverse('dashboard:reviews-list')

        user1 = get(User)
        user2 = get(User)

        review1 = get(ProductReview, user=user1, status=0)
        review2 = get(ProductReview, user=user2, status=0)
        review3 = get(ProductReview, user=user2, status=0)

        assert(ProductReview.objects.count() == 3)

        post_params = {
            'status': 1,
            'selected_review': [3, 2],
            'action': ['update_selected_review_status'],
        }
        response = self.client.post(url, post_params)

        self.assertEquals(ProductReview.objects.get(pk=1).status, 0)
        self.assertEquals(ProductReview.objects.get(pk=2).status, 1)
        self.assertEquals(ProductReview.objects.get(pk=3).status, 1)
