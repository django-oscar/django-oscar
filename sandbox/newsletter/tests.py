from django.test import TestCase
from .models import Subscriber
from .helpers import get_subscriber, create_subscriber, unsubscribe

class SubscriberTests(TestCase):
    def setUp(self):
        Subscriber.objects.create(email="test@test.com")

    def test_get_subscriber(self):
        subscribers = get_subscriber()
        self.assertEqual(len(subscribers), 1)

    def test_create_subscriber(self):
        create_subscriber("test2@test.com")
        subscribers = get_subscriber()
        self.assertEqual(len(subscribers), 2)
        self.assertIn("test2@test.com", [subscriber.email for subscriber in subscribers])
        self.assertTrue(subscribers[1].is_subscribed)

def test_unsubscribe(self):
        unsubscribe("test@test.com")
        subscribers = get_subscriber()
        self.assertEqual(len(subscribers), 0)
        self.assertNotIn("test@test.com", [subscriber.email for subscriber in subscribers])
        subscriber = Subscriber.objects.filter(email="test@test.com").first()
        self.assertFalse(subscriber.is_subscribed)