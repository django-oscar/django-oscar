# pylint: disable=redefined-outer-name,unused-argument
import datetime

import pytest
from django.utils import timezone

from oscar.apps.dashboard.reviews import views
from oscar.core.loading import get_model
from oscar.test.factories.catalogue import ProductReviewFactory
from oscar.test.factories.customer import UserFactory

now = timezone.now()


ProductReview = get_model("reviews", "ProductReview")

keywords = ["aaaaa", "bbbbb", "ccccc", "ddddd"]


@pytest.fixture
def reviews():
    for i in range(10):
        keyword = keywords[i % len(keywords)]
        date_created = now - datetime.timedelta(days=i)
        user = UserFactory(first_name=keyword)
        review = ProductReviewFactory(
            score=i % 5,
            title="review title product %d %s" % (i, keyword),
            body="review body product %d %s" % (i, keyword),
            status=i % 3,
            user=user,
        )
        review.date_created = date_created
        review.save()
    return ProductReview.objects.all()


@pytest.fixture
def reviewlistview(rf, reviews):
    view = views.ReviewListView()
    view.request = rf.get("/")
    return view


@pytest.mark.django_db
class TestReviewListView(object):
    def test_get(self, rf):
        request = rf.get("/")
        view = views.ReviewListView.as_view()
        response = view(request)
        assert response.status_code == 200

        request = rf.get(
            "/", data=dict(keyword="test", status="", date_from="", date_to="", name="")
        )
        response = view(request)
        assert response.status_code == 200

        request = rf.get(
            "/", data=dict(keyword="", status="0", date_from="", date_to="", name="")
        )
        response = view(request)
        assert response.status_code == 200

        request = rf.get(
            "/",
            data=dict(
                keyword="test", status="", date_from="2017-01-01", date_to="", name=""
            ),
        )
        response = view(request)
        assert response.status_code == 200

        request = rf.get(
            "/",
            data=dict(
                keyword="test", status="", date_from="", date_to="2017-01-01", name=""
            ),
        )
        response = view(request)
        assert response.status_code == 200

        request = rf.get(
            "/",
            data=dict(
                keyword="test",
                status="",
                date_from="2017-01-01",
                date_to="2017-12-31",
                name="",
            ),
        )
        response = view(request)
        assert response.status_code == 200

        request = rf.get(
            "/", data=dict(keyword="", status="", date_from="", date_to="", name="test")
        )
        response = view(request)
        assert response.status_code == 200

    def test_add_filter_status(self, rf, reviews):
        request = rf.get("/", data=dict(status=ProductReview.FOR_MODERATION))
        view = views.ReviewListView.as_view()
        response = view(request)
        view = response.context_data["view"]
        qs = view.get_queryset()
        assert qs.count() == 4

        request = rf.get("/", data=dict(status=ProductReview.APPROVED))
        view = views.ReviewListView.as_view()
        response = view(request)
        view = response.context_data["view"]
        qs = view.get_queryset()
        assert qs.count() == 3

        request = rf.get("/", data=dict(status=ProductReview.REJECTED))
        view = views.ReviewListView.as_view()
        response = view(request)
        view = response.context_data["view"]
        qs = view.get_queryset()
        assert qs.count() == 3

    def test_add_filter_keyword(self, rf, reviews):
        expect = {
            "aaaaa": 3,
            "bbbbb": 3,
            "ccccc": 2,
            "ddddd": 2,
        }

        for keyword in expect:
            request = rf.get("/", data=dict(keyword=keyword))
            view = views.ReviewListView.as_view()
            response = view(request)
            view = response.context_data["view"]
            qs = view.get_queryset()
            assert qs.count() == expect[keyword]
            assert "with keyword matching" in view.desc_ctx["kw_filter"]
            assert keyword in view.desc_ctx["kw_filter"]

    def test_add_filter_name(self, rf, reviews):
        expect = {
            "aaaaa": 3,
            "bbbbb": 3,
            "ccccc": 2,
            "ddddd": 2,
        }

        for keyword in expect:
            name = "%s winterbottom" % keyword
            request = rf.get("/", data=dict(name=name))
            view = views.ReviewListView.as_view()
            response = view(request)
            view = response.context_data["view"]
            qs = view.get_queryset()
            assert qs.count() == expect[keyword]
            assert "with customer name matching" in view.desc_ctx["name_filter"]
            assert keyword in view.desc_ctx["name_filter"]

    def test_get_date_from_to_queryset(self, reviewlistview):
        view = reviewlistview

        date_from = now - datetime.timedelta(days=6)
        date_to = now - datetime.timedelta(days=2)

        qs = view.get_queryset()
        assert qs.count() == 10

        qs = view.get_date_from_to_queryset(None, None)
        assert qs.count() == 10
        assert view.desc_ctx["date_filter"] == ""

        qs = view.get_date_from_to_queryset(date_from, None, qs)
        assert qs.count() == 7
        assert view.desc_ctx["date_filter"].startswith(" created after")

        qs = view.get_date_from_to_queryset(None, date_to, qs)
        assert qs.count() == 5
        assert view.desc_ctx["date_filter"].startswith(" created before")

        qs = view.get_date_from_to_queryset(date_from, date_to, qs)
        assert qs.count() == 5
        assert view.desc_ctx["date_filter"].startswith(" created between")
