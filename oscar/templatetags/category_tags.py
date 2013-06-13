from django import template
from django.db.models import get_model

register = template.Library()
Category = get_model('catalogue', 'category')

# Since the category_tree template tag can be used multiple times in the same
# set of templates, we use a cache to avoid creating the node multile times.
NODE_CACHE = {}


@register.tag(name="category_tree")
def do_category_list(parse, token):
    tokens = token.split_contents()
    error_msg = ("%r tag uses the following syntax: {%% category_tree "
                 "[depth=n] as categories %%}" % tokens[0])
    depth_var = '0'

    if len(tokens) == 4:
        if tokens[2] != 'as':
            raise template.TemplateSyntaxError(error_msg)
        depth_var = tokens[1].split('=')[1]
        as_var = tokens[3]
    elif len(tokens) == 3:
        if tokens[1] != 'as':
            raise template.TemplateSyntaxError(error_msg)
        as_var = tokens[2]
    else:
        raise template.TemplateSyntaxError(error_msg)

    # Use a per-process cache of the CategoryTreeNode instance
    key = depth_var + as_var
    if key in NODE_CACHE:
        return NODE_CACHE[key]

    NODE_CACHE[key] = CategoryTreeNode(depth_var, as_var)
    return NODE_CACHE[key]


class CategoryTreeNode(template.Node):
    def __init__(self, depth_var, as_var):
        self.depth_var = template.Variable(depth_var)
        self.as_var = as_var

    def get_annotated_list(self, max_depth=None):
        """
        Gets an annotated list from a tree branch.

        Borrows heavily from treebeard's get_annotated_list
        """
        result, info = [], {}
        start_depth, prev_depth = (None, None)

        for node in Category.get_tree():
            depth = node.get_depth()
            if start_depth is None:
                start_depth = depth

            if max_depth is not None and depth > max_depth:
                continue

            # annotate previous node's info
            info['has_children'] = depth > prev_depth
            if depth < prev_depth:
                info['num_to_close'] = range(0, prev_depth - depth)

            info = {'open': depth > prev_depth,  # is going down a level
                    'num_to_close': [],                 # is going up len(close) levels
                    'level': depth - start_depth}

            result.append((node, info,))
            prev_depth = depth

        if prev_depth is not None:
            # close last leaf
            info['num_to_close'] = range(0, prev_depth - start_depth)
            info['has_children'] = prev_depth > prev_depth
        return result

    def render(self, context):
        depth = int(self.depth_var.resolve(context))
        annotated_list = self.get_annotated_list(max_depth=depth or None)
        context[self.as_var] = annotated_list
        return ''
