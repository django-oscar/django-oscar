from django import template

from oscar.core.loading import get_model

register = template.Library()
Category = get_model('catalogue', 'category')


@register.simple_tag(name="category_tree")
def get_annotated_list(depth=None, parent=None):
    """
    Gets an annotated list from a tree branch.

    Borrows heavily from treebeard's get_annotated_list
    """
    # 'depth' is the backwards-compatible name for the template tag,
    # 'max_depth' is the better variable name.
    max_depth = depth

    annotated_categories = []

    start_depth, prev_depth = (None, None)
    if parent:
        categories = parent.get_descendants()
        if max_depth is not None:
            max_depth += parent.get_depth()
    else:
        categories = Category.get_tree()

    info = {}
    for node in categories:
        node_depth = node.get_depth()
        if start_depth is None:
            start_depth = node_depth
        if max_depth is not None and node_depth > max_depth:
            continue

        # Update previous node's info
        info['has_children'] = prev_depth is None or node_depth > prev_depth
        if prev_depth is not None and node_depth < prev_depth:
            info['num_to_close'] = list(range(0, prev_depth - node_depth))

        info = {'num_to_close': [],
                'level': node_depth - start_depth}
        annotated_categories.append((node, info,))
        prev_depth = node_depth

    if prev_depth is not None:
        # close last leaf
        info['num_to_close'] = list(range(0, prev_depth - start_depth))
        info['has_children'] = prev_depth > prev_depth

    return annotated_categories
