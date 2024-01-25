from .models import Subscriber

def get_subscriber(limit: int = 10, offset: int = 0) -> list[Subscriber]:
    """
    Retrieve a list of subscribers from the database.

    Args:
        limit: The maximum number of subscribers to retrieve.
        offset: The number of subscribers to skip before starting to retrieve.

    Returns:
        list[Subscriber]: A list of Subscriber objects.
    """
    subscribers = Subscriber.objects.filter(is_subscribed=True).order_by('-created_at')[offset:offset+limit]
    
    return subscribers

def create_subscriber(email: str) -> Subscriber:
    """
    Create a new subscriber with the given email.

    Args:
        email: The email address of the subscriber.

    Returns:
        Subscriber: The newly created Subscriber object.
    """
    subscriber = Subscriber.objects.create(email=email)
    
    return subscriber

def unsubscribe(email: str) -> None:
    """
    Unsubscribe a subscriber with the given email.

    Args:
        email: The email address of the subscriber to unsubscribe.

    Returns:
        None
    """
    Subscriber.objects.filter(email=email).update(is_subscribed=False)



def delete_subscriber(email: str) -> None:
    """
    Delete a subscriber with the given email.

    Args:
        email: The email address of the subscriber to delete.

    Returns:
        None
    """
    Subscriber.objects.filter(email=email).delete()
