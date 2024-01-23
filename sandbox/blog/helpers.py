from blog.models import Post, Category
from typing import List, Union

def get_blog_posts(limit: int = 10, offset: int = 0) -> list[Post]:
    """
    Get a list of blog posts sorted by creation date in descending order.
    
    Parameters:
        limit (int): The maximum number of posts to return. Defaults to 10.
        offset (int): The starting index for the slice of posts to return. Defaults to 0.
        
    Returns:
        list[Post]: A list of Post objects.
    """
    posts = Post.objects.all().order_by('-created_at')[offset:offset+limit]
    return posts


def get_post_by_id(post_id: int) -> Post:
    """
    Get a post by its id.
    
    Args:
        post_id (int): The ID of the post to retrieve.
        
    Returns:
        Post: The post with the given ID, or None if no such post exists.
    """
    try:
        return Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return None


def insert_post(post_data: dict) -> Post:
    """
    Insert a new post into the database.
    
    Parameters:
        post_data (dict): A dictionary containing the data for the new post.
    
    Returns:
        Post: The newly created post object.
    """
    return Post.objects.create(**post_data)


def update_post(post_id: int, post_data: dict) -> None:
    """
    Update an existing post in the database.
    
    Parameters:
        post_id (int): The id of the post to be updated.
        post_data (dict): A dictionary containing the new data for the post.
    """
    Post.objects.filter(pk=post_id).update(**post_data)


def delete_post(post_id: int) -> None:
    """
    Delete a post from the database.
    
    Parameters:
        post_id (int): The id of the post to be deleted.
    """
    Post.objects.filter(pk=post_id).delete()


# Helper functions for Category
def get_categories() -> List[Category]:
    """
    This function retrieves all categories from the database.
    
    Returns:
        list: A list of all Category objects in the database.
    """
    return list(Category.objects.all())

def get_category_by_id(category_id: int) -> Union[Category, None]:
    """
    This function retrieves a category from the database by its id.
    
    Parameters:
        category_id (int): The id of the category to be retrieved.
        
    Returns:
        Category: A Category object with the given id, or None if no such category exists.
    """
    try:
        return Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        return None

def insert_category(name: str) -> Category:
    """
    This function inserts a new category into the database.
    
    Parameters:
        name (str): The name of the new category.
        
    Returns:
        Category: The newly created Category object.
    """
    return Category.objects.create(name=name)

def update_category(category_id: int, name: str) -> Union[Category, None]:
    """
    This function updates a category in the database.
    
    Parameters:
        category_id (int): The id of the category to be updated.
        name (str): The new name for the category.
        
    Returns:
        Category: The updated Category object, or None if no such category exists.
    """
    try:
        category = Category.objects.get(pk=category_id)
        category.name = name
        category.save()
        return category
    except Category.DoesNotExist:
        return None

def delete_category(category_id: int) -> bool:
    """
    This function deletes a category from the database by its id.
    
    Parameters:
        category_id (int): The id of the category to be deleted.
        
    Returns:
        bool: True if the category was successfully deleted, False otherwise.
    """
    try:
        Category.objects.get(pk=category_id).delete()
        return True
    except Category.DoesNotExist:
        return False
