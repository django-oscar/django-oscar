from django.test import TestCase
from django.urls import reverse
from .models import Blog

class BlogModelTests(TestCase):
    def test_blog_creation(self):
        # Create a Blog instance to test the Blog model
        blog = Blog.objects.create(
            title='Test Blog Title',
            content='Just a test content',
            author='Test Author'
        )
        
        self.assertEqual(str(blog), 'Test Blog Title')

class BlogViewsTests(TestCase):
    def setUp(self):
        # Setup runs before every test method
        self.blog = Blog.objects.create(
            title='Another Test Blog Title',
            content='Just a test content',
            author='Test Author'
        )

    def test_blog_list_view(self):
        # Test the Blog list view
        response = self.client.get(reverse('blog-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Another Test Blog Title')

    def test_blog_detail_view(self):
        # Test the Blog detail view
        response = self.client.get(reverse('blog-detail', kwargs={'pk': self.blog.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Another Test Blog Title')