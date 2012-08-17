from django.db.models import get_model

Category = get_model('catalogue', 'category')


def create_from_sequence(bits):
    """
    Create categories from an iterable
    """
    if len(bits) == 1:
        # Get or create root node
        try:
            root = Category.objects.get(depth=1, name=bits[0])
        except Category.DoesNotExist:
            root = Category.add_root(name=bits[0])
        return [root]
    else:
        parents = create_from_sequence(bits[:-1])
        try:
            child = parents[-1].get_children().get(name=bits[-1])
        except Category.DoesNotExist:
            child = parents[-1].add_child(name=bits[-1])
        parents.append(child)
        return parents


def create_from_breadcrumbs(breadcrumb_str, separator='>'):
    """
    Create categories from a breadcrumb string
    """
    category_names = [x.strip() for x in breadcrumb_str.split(separator)]
    categories = create_from_sequence(category_names)
    return categories[-1]
