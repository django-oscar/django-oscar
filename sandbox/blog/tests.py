from django.test import TestCase
from .models import Post, Category
from .helpers import get_blog_posts, get_post_by_id, insert_post, update_post, get_categories, get_category_by_id, insert_category, update_category, delete_category

# Create your tests here.

class PostViewsTests(TestCase):
    def setUp(self):
        self.post = Post.objects.create(title='Test Title', content='Test Content')
    
    def test_post_list_view(self):
        posts = get_blog_posts()
        self.assertEqual(len(posts), 1)
        # Add more assertions for posts here
        post = posts[0]
        self.assertEqual(post.title, 'Test Title')
        self.assertEqual(post.content, 'Test Content')
    
    def test_post_detail_view(self):
        post = get_post_by_id(self.post.id)
        self.assertEqual(post.title, 'Test Title')
        self.assertEqual(post.content, 'Test Content')
        
class PostInsertUpdateTests(TestCase):
    def setUp(self):
        self.post = Post.objects.create(title='Test Title', content='Test Content')
    
    def test_insert_post(self):
        post_data = {
            'title': 'New Test Title', 
            'content': 'New Test Content'
        }
        insert_post(post_data)
        posts = get_blog_posts()
        self.assertEqual(len(posts), 2)
        # Add more assertions for posts here
        post = posts[0]
        self.assertEqual(post.title, 'New Test Title')
        self.assertEqual(post.content, 'New Test Content')
        
    def test_update_post(self):
        updated_data = {
            'title': 'Updated Test Title', 
            'content': 'Updated Test Content'
        }
        update_post(self.post.id, updated_data)
        post = get_post_by_id(self.post.id)
        self.assertEqual(post.title, 'Updated Test Title')
        self.assertEqual(post.content, 'Updated Test Content')



# Create Test Cases for Category

class CategoryViewsTests(TestCase):
    
    def setUp(self):
        self.category = Category.objects.create(name='TestCategory')
    

    def test_get_categories(self):
        categories = get_categories()
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0].name, 'TestCategory')

    
    def test_get_category_by_id(self):
        category = get_category_by_id(self.category.id)
        self.assertEqual(category.name, 'TestCategory')        
        


class CategoryInsertUpdateDeleteTests(TestCase):
    
    def setUp(self):
        self.category = Category.objects.create(name='TestCategory')

    def test_insert_category(self):
        new_category = insert_category('NewCategory')
        self.assertEqual(new_category.name, 'NewCategory') 
    
    def test_update_category(self):
        updated_category = update_category(self.category.id, 'UpdatedCategory')
        self.assertEqual(updated_category.name, 'UpdatedCategory')

    def test_delete_category(self):
        delete_category(self.category.id)
        with self.assertRaises(Category.DoesNotExist):
            Category.objects.get(pk=self.category.id)
