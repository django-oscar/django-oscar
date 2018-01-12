import pytest
from django.utils import timezone

from oscar.apps.dashboard.reviews import views


now = timezone.now()


@pytest.fixture
def reviewlistview(rf):
    view = views.ReviewListView()
    view.request = rf.get('/')
    return view


@pytest.mark.django_db
class TestReviewListView(object):

    def test_get(self, rf):
        request = rf.get('/')
        view = views.ReviewListView.as_view()
        response = view(request)
        assert response.status_code == 200

        request = rf.get('/', data=dict(keyword='test', status='', date_from='', date_to='', name=''))
        response = view(request)
        assert response.status_code == 200

        request = rf.get('/', data=dict(keyword='', status='0', date_from='', date_to='', name=''))
        response = view(request)
        assert response.status_code == 200

        request = rf.get('/', data=dict(
            keyword='test', status='', date_from='2017-01-01', date_to='', name=''))
        response = view(request)
        assert response.status_code == 200

        request = rf.get('/', data=dict(
            keyword='test', status='', date_from='', date_to='2017-01-01', name=''))
        response = view(request)
        assert response.status_code == 200

        request = rf.get('/', data=dict(
            keyword='test', status='', date_from='2017-01-01', date_to='2017-12-31', name=''))
        response = view(request)
        assert response.status_code == 200

        request = rf.get('/', data=dict(
            keyword='', status='', date_from='', date_to='', name='test'))
        response = view(request)
        assert response.status_code == 200

    def test_get_date_from_to_queryset(self, reviewlistview):
        view = reviewlistview

        qs = view.get_queryset()
        assert qs.count() == 0

        qs = view.get_date_from_to_queryset(None, None)
        assert qs.count() == 0
        assert view.desc_ctx['date_filter'] == ''

        qs = view.get_date_from_to_queryset(now, None, qs)
        assert qs.count() == 0
        assert view.desc_ctx['date_filter'].startswith(' created after')

        qs = view.get_date_from_to_queryset(None, now, qs)
        assert qs.count() == 0
        assert view.desc_ctx['date_filter'].startswith(' created before')

        qs = view.get_date_from_to_queryset(now, now, qs)
        assert qs.count() == 0
        assert view.desc_ctx['date_filter'].startswith(' created between')
