from django.conf.urls import url

from oscar.core.application import Application
from oscar.core.loading import get_class


class ReviewsApplication(Application):
    name = None


application = ReviewsApplication()
