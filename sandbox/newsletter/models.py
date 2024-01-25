from django.db import models

# Create your models here.
class Subscriber(models.Model):
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    is_subscribed = models.BooleanField(default=True)

    def __str__(self):
        return self.email
