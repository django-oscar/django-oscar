from django import template

from oscar.core.loading import get_model

register = template.Library()
Category = get_model('catalogue', 'category')


@register.assignment_tag(name="category_tree")
def get_annotated_list(depth=None, parent=None):
    """
    Gets an annotated list from a tree branch.

    Borrows heavily from treebeard's get_annotated_list
    """
    # 'depth' is the backwards-compatible name for the template tag,
    # 'max_depth' is the better variable name.
    max_depth = depth

    annotated_categories = []

    start_depth, prev_node = (None, None)
    if parent:
        categories = parent.get_descendants()
        if max_depth is not None:
            max_depth += parent.depth
    else:
        categories = Category.get_tree()

    info = {}
    for node in categories:
        node_depth = node.depth
        # Sets initial depth; is only executed once.
        if start_depth is None:
            start_depth = node_depth
        # Skip any nodes that are deeper than max_depth
        if max_depth is not None and node_depth > max_depth:
            continue

        # Update previous node's info.
        if prev_node is not None:
            # New node is one level deeper than the previous one.
            if node_depth > prev_node.depth:
                # That means, this node is a child of the previous one.
                info['has_children'] = True
                info['num_to_close'] = []
                node._slugs = prev_node._slugs + [node.slug]
            # New node is on same level
            elif node_depth == prev_node.depth:
                # That means the previous node didn't have children.
                info['has_children'] = False
                info['num_to_close'] = []
                node._slugs = prev_node._slugs[:-1] + [node.slug]
            # The new node is above the previous one.
            elif node_depth < prev_node.depth:
                # That means the previous node didn't have children.
                info['has_children'] = False
                info['num_to_close'] = list(range(0, prev_node.depth - node_depth))
                # By clever tracking, we could try to populate node._slugs here,
                # but it would make a complicated template tag even more complicated.

        # Write current node's info.
        info = {
            'num_to_close': [],
            'level': node_depth - start_depth,
            # Most of the time, this should use the already populated
            # node._slugs and not incur a database query.
            'url': node.get_absolute_url()
        }
        annotated_categories.append((node, info,))
        prev_node = node

    if prev_node is not None:
        # Close the last leaf.
        info['num_to_close'] = list(range(0, prev_node.depth - start_depth))
        info['has_children'] = False

    return annotated_categories
