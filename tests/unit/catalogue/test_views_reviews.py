from django.test.testcases import TestCase
from django.urls import reverse

from oscar.apps.catalogue.reviews.models import ProductReview, Vote
from oscar.test.factories import UserFactory, create_product


class TestAddVoteView(TestCase):
    def setUp(self):
        self.client.force_login(UserFactory())

    def test_voting_on_product_review_returns_404_on_non_public_product(self):
        product = create_product(is_public=False)
        review = ProductReview.objects.create(
            product=product,
            **{
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            }
        )
        path = reverse(
            "catalogue:reviews-vote",
            kwargs={
                "product_slug": product.slug,
                "product_pk": product.pk,
                "pk": review.pk,
            },
        )

        response = self.client.post(path, data={"delta": Vote.UP})

        self.assertEqual(response.status_code, 404)

    def test_voting_on_product_review_redirect_on_public_product(self):
        product = create_product(is_public=True)
        review = ProductReview.objects.create(
            product=product,
            **{
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            }
        )
        path = reverse(
            "catalogue:reviews-vote",
            kwargs={
                "product_slug": product.slug,
                "product_pk": product.pk,
                "pk": review.pk,
            },
        )

        response = self.client.post(path, data={"delta": Vote.UP})

        self.assertRedirects(response, product.get_absolute_url())

    def test_creating_product_review_returns_404_on_non_public_product(self):
        product = create_product(is_public=False)
        path = reverse(
            "catalogue:reviews-add",
            kwargs={"product_slug": product.slug, "product_pk": product.pk},
        )

        response = self.client.post(
            path,
            data={
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_creating_product_review_redirect_on_public_product(self):
        product = create_product(is_public=True)
        path = reverse(
            "catalogue:reviews-add",
            kwargs={"product_slug": product.slug, "product_pk": product.pk},
        )

        response = self.client.post(
            path,
            data={
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            },
        )

        self.assertRedirects(response, product.get_absolute_url())


class TestProductReviewList(TestCase):
    def setUp(self):
        self.client.force_login(UserFactory())

    def test_listing_product_reviews_returns_404_on_non_public_product(self):
        product = create_product(is_public=False)
        path = reverse(
            "catalogue:reviews-list",
            kwargs={"product_slug": product.slug, "product_pk": product.pk},
        )

        response = self.client.get(path)

        self.assertEqual(response.status_code, 404)

    def test_listing_product_reviews_returns_200_on_public_product(self):
        product = create_product(is_public=True)
        path = reverse(
            "catalogue:reviews-list",
            kwargs={"product_slug": product.slug, "product_pk": product.pk},
        )

        response = self.client.get(path)

        self.assertEqual(response.status_code, 200)


class TestProductReviewDetail(TestCase):
    def setUp(self):
        self.client.force_login(UserFactory())

    def test_retrieving_product_review_returns_404_on_non_public_product(self):
        product = create_product(is_public=False)
        review = ProductReview.objects.create(
            product=product,
            **{
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            }
        )
        path = reverse(
            "catalogue:reviews-detail",
            kwargs={
                "product_slug": product.slug,
                "product_pk": product.pk,
                "pk": review.pk,
            },
        )

        response = self.client.get(path)

        self.assertEqual(response.status_code, 404)

    def test_retrieving_product_review_returns_200_on_public_product(self):
        product = create_product(is_public=True)
        review = ProductReview.objects.create(
            product=product,
            **{
                "title": "Awesome!",
                "score": 5,
                "body": "Wonderful product",
            }
        )
        path = reverse(
            "catalogue:reviews-detail",
            kwargs={
                "product_slug": product.slug,
                "product_pk": product.pk,
                "pk": review.pk,
            },
        )

        response = self.client.get(path)

        self.assertEqual(response.status_code, 200)
