from django.test import TestCase
from ..models import Comment, Post, Category
from ..helpers import get_comments, get_comment_by_id, insert_comment, update_comment, delete_comment


class CommentViewsTests(TestCase):
    
    def setUp(self):
        self.category = Category.objects.create(name='TestCategory')
        self.post = Post.objects.create(title='TestPost', content='TestContent', category=self.category)
        self.comment = Comment.objects.create(content='TestComment', post=self.post, user=self.user)

    def test_get_comments(self):
        comments = get_comments(self.post.id)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].content, 'TestComment')

    def test_get_comment_by_id(self):
        comment = get_comment_by_id(self.comment.id)
        self.assertEqual(comment.content, 'TestComment')


class CommentInsertUpdateTests(TestCase):
    
    def setUp(self):
        self.category = Category.objects.create(name='TestCategory')
        self.post = Post.objects.create(title='TestPost', content='TestContent', category=self.category)
        self.comment = Comment.objects.create(content='TestComment', post=self.post, user_id=1)

    def test_insert_comment(self):
        new_comment = insert_comment(self.post.id, 1, 'NewComment')
        self.assertEqual(new_comment.name, 'NewComment') 
    
    def test_update_comment(self):
        updated_comment = update_comment(self.comment.id, 'UpdatedComment')
        self.assertEqual(updated_comment.name, 'UpdatedComment')


class CommentDeleteTests(TestCase):
    
    def setUp(self):
        self.category = Category.objects.create(name='TestCategory')
        self.post = Post.objects.create(title='TestPost', content='TestContent', category=self.category)
        self.comment = Comment.objects.create(content='TestComment', post=self.post, user_id=1)

    
    def test_delete_comment(self):
        delete_comment(self.comment.id)
        with self.assertRaises(Comment.DoesNotExist):
            Comment.objects.get(pk=self.comment.id)