from datetime import datetime, timedelta

from oscar.core.loading import get_model
from django.core.urlresolvers import reverse
from oscar.core.compat import get_user_model
from django_dynamic_fixture import get

from oscar.test.testcases import WebTestCase


ProductReview = get_model('reviews', 'productreview')
User = get_user_model()


class ReviewsDashboardTests(WebTestCase):
    is_staff = True

    def test_reviews_dashboard_is_accessible_to_staff(self):
        url = reverse('dashboard:reviews-list')
        response = self.client.get(url)
        self.assertIsOk(response)

    def test_bulk_editing_review_status(self):
        url = reverse('dashboard:reviews-list')

        user1 = get(User)
        user2 = get(User)

        get(ProductReview, user=user1, status=0)
        get(ProductReview, user=user2, status=0)
        get(ProductReview, user=user2, status=0)

        assert(ProductReview.objects.count() == 3)

        post_params = {
            'status': 1,
            'selected_review': [3, 2],
            'action': ['update_selected_review_status'],
        }
        self.client.post(url, post_params)

        self.assertEqual(ProductReview.objects.get(pk=1).status, 0)
        self.assertEqual(ProductReview.objects.get(pk=2).status, 1)
        self.assertEqual(ProductReview.objects.get(pk=3).status, 1)

    def test_filter_reviews_by_name(self):
        url = reverse('dashboard:reviews-list')

        user1 = get(User, first_name='Peter', last_name='Griffin')
        user2 = get(User, first_name='Lois', last_name='Griffin')

        get(ProductReview, user=user1, status=0)
        get(ProductReview, user=user2, status=0)
        get(ProductReview, user=user2, status=0)

        response = self.client.get(url, {'name': 'peter'})

        self.assertEqual(len(response.context['review_list']), 1)
        self.assertEqual(response.context['review_list'][0].user, user1)

        response = self.client.get(url, {'name': 'lois griffin'})

        self.assertEqual(len(response.context['review_list']), 2)
        for review in response.context['review_list']:
            self.assertEqual(review.user, user2)

    def test_filter_reviews_by_keyword(self):
        url = reverse('dashboard:reviews-list')

        user1 = get(User)
        user2 = get(User)

        review1 = get(ProductReview, user=user1, title='Sexy Review')
        review2 = get(ProductReview, user=user2, title='Anry Review',
                      body='argh')
        get(ProductReview, user=user2, title='Lovely Thing')

        response = self.client.get(url, {'keyword': 'argh'})
        self.assertEqual(len(response.context['review_list']), 1)
        self.assertEqual(response.context['review_list'][0], review2)

        response = self.client.get(url, {'keyword': 'review'})
        self.assertQuerysetContains(response.context['review_list'],
                                    [review1, review2])

    def assertQuerysetContains(self, qs, items):
        qs_ids = [obj.id for obj in qs]
        item_ids = [item.id for item in items]
        self.assertEqual(len(qs_ids), len(item_ids))
        for i, j in zip(qs_ids, item_ids):
            self.assertEqual(i, j)

    def test_filter_reviews_by_date(self):
        now = datetime.now()
        review1 = get(ProductReview)
        review2 = get(ProductReview)
        review2.date_created = now - timedelta(days=2)
        review2.save()
        review3 = get(ProductReview)
        review3.date_created = now - timedelta(days=10)
        review3.save()

        url = reverse('dashboard:reviews-list')
        response = self.client.get(url, {'date_from': now - timedelta(days=5)})
        self.assertQuerysetContains(response.context['review_list'],
                                    [review1, review2])

        response = self.client.get(url, {'date_to': now - timedelta(days=5)})
        self.assertQuerysetContains(response.context['review_list'],
                                    [review3])

        response = self.client.get(url, {
            'date_from': now - timedelta(days=12),
            'date_to': now - timedelta(days=9)
        })
        self.assertQuerysetContains(response.context['review_list'],
                                    [review3])

    def test_filter_reviews_by_status(self):
        url = reverse('dashboard:reviews-list')

        user1 = get(User)
        user2 = get(User)

        review1 = get(ProductReview, user=user1, status=1)
        review2 = get(ProductReview, user=user2, status=0)
        review3 = get(ProductReview, user=user2, status=2)

        response = self.client.get(url, {'status': 0})
        self.assertEqual(len(response.context['review_list']), 1)
        self.assertEqual(response.context['review_list'][0], review2)

        response = self.client.get(url, {'status': 1})
        self.assertEqual(len(response.context['review_list']), 1)
        self.assertEqual(response.context['review_list'][0], review1)

        response = self.client.get(url, {'status': 2})
        self.assertEqual(len(response.context['review_list']), 1)
        self.assertEqual(response.context['review_list'][0], review3)

        response = self.client.get(url, {'status': 3})
        reviews = response.context['review_list']
        self.assertTrue(review1 in reviews)
