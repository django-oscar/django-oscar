from datetime import timedelta, timezone as datetime_timezone

from django.urls import reverse
from django.utils import timezone

from oscar.core.compat import get_user_model
from oscar.core.loading import get_model
from oscar.test.factories import ProductReviewFactory, UserFactory
from oscar.test.testcases import WebTestCase

ProductReview = get_model("reviews", "productreview")
User = get_user_model()


class ReviewsDashboardTests(WebTestCase):
    is_staff = True

    def test_reviews_dashboard_is_accessible_to_staff(self):
        url = reverse("dashboard:reviews-list")
        response = self.get(url)
        self.assertIsOk(response)

    def test_bulk_editing_review_status(self):
        user1 = UserFactory()
        user2 = UserFactory()

        ProductReviewFactory(pk=1, user=user1, status=0)
        ProductReviewFactory(pk=2, user=user2, status=0)
        ProductReviewFactory(pk=3, user=user2, status=0)

        assert ProductReview.objects.count() == 3

        list_page = self.get(reverse("dashboard:reviews-list"))
        form = list_page.forms[1]
        form["selected_review"] = [3, 2]
        form.submit("update")

        self.assertEqual(ProductReview.objects.get(pk=1).status, 0)
        self.assertEqual(ProductReview.objects.get(pk=2).status, 1)
        self.assertEqual(ProductReview.objects.get(pk=3).status, 1)

    def test_filter_reviews_by_name(self):
        user1 = UserFactory(first_name="Peter", last_name="Griffin")
        user2 = UserFactory(first_name="Lois", last_name="Griffin")

        ProductReviewFactory(user=user1, status=0)
        ProductReviewFactory(user=user2, status=0)
        ProductReviewFactory(user=user2, status=0)

        url = reverse("dashboard:reviews-list") + "?name=peter"
        response = self.get(url)

        self.assertEqual(len(response.context["review_list"]), 1)
        self.assertEqual(response.context["review_list"][0].user, user1)

        url = reverse("dashboard:reviews-list") + "?name=lois+griffin"
        response = self.get(url)

        self.assertEqual(len(response.context["review_list"]), 2)
        for review in response.context["review_list"]:
            self.assertEqual(review.user, user2)

    def test_filter_reviews_by_keyword(self):
        url = reverse("dashboard:reviews-list")

        user1 = UserFactory()
        user2 = UserFactory()

        review1 = ProductReviewFactory(user=user1, title="Sexy Review")
        review2 = ProductReviewFactory(user=user2, title="Anry Review", body="argh")
        ProductReviewFactory(user=user2, title="Lovely Thing")

        response = self.get(url, params={"keyword": "argh"})
        self.assertEqual(len(response.context["review_list"]), 1)
        self.assertEqual(response.context["review_list"][0], review2)

        response = self.get(url, params={"keyword": "review"})
        assert list(response.context["review_list"]) == [review2, review1]

    def test_filter_reviews_by_date(self):
        def n_days_ago(days):
            """
            The tests below pass timestamps as GET parameters, but the
            ProductReviewSearchForm doesn't recognize the timezone notation.
            """
            return timezone.make_naive(
                now - timedelta(days=days), timezone=datetime_timezone.utc
            )

        now = timezone.now()
        review1 = ProductReviewFactory()
        review2 = ProductReviewFactory()
        review2.date_created = now - timedelta(days=2)
        review2.save()
        review3 = ProductReviewFactory()
        review3.date_created = now - timedelta(days=10)
        review3.save()

        url = reverse("dashboard:reviews-list")
        response = self.get(url, params={"date_from": n_days_ago(5)})
        assert list(response.context["review_list"]) == [review1, review2]

        response = self.get(url, params={"date_to": n_days_ago(5)})
        assert list(response.context["review_list"]) == [review3]

        response = self.get(
            url,
            params={
                "date_from": n_days_ago(12),
                "date_to": n_days_ago(9),
            },
        )
        assert list(response.context["review_list"]) == [review3]

    def test_filter_reviews_by_status(self):
        url = reverse("dashboard:reviews-list")

        user1 = UserFactory()
        user2 = UserFactory()

        review1 = ProductReviewFactory(user=user1, status=1)
        review2 = ProductReviewFactory(user=user2, status=0)
        review3 = ProductReviewFactory(user=user2, status=2)

        response = self.get(url, params={"status": 0})
        self.assertEqual(len(response.context["review_list"]), 1)
        self.assertEqual(response.context["review_list"][0], review2)

        response = self.get(url, params={"status": 1})
        self.assertEqual(len(response.context["review_list"]), 1)
        self.assertEqual(response.context["review_list"][0], review1)

        response = self.get(url, params={"status": 2})
        self.assertEqual(len(response.context["review_list"]), 1)
        self.assertEqual(response.context["review_list"][0], review3)

        response = self.get(url, params={"status": 3})
        reviews = response.context["review_list"]
        self.assertTrue(review1 in reviews)
