from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    post_count = models.IntegerField(default=0)

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(default='pending', max_length=10)
    like_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, related_name='posts')
