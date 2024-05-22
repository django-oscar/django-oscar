import pytest

from oscar.views import handler403, handler404, handler500


@pytest.mark.django_db
def test_handler403_response_status(rf):
    request = rf.get("/")
    response = handler403(request, exception=None)
    assert response.status_code == 403


@pytest.mark.django_db
def test_handler404_response_status(rf):
    request = rf.get("/")
    response = handler404(request, exception=None)
    assert response.status_code == 404


@pytest.mark.django_db
def test_handler500_response_status(rf):
    request = rf.get("/")
    response = handler500(request)
    assert response.status_code == 500
