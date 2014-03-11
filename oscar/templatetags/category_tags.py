from django import template
from oscar.core.loading import get_model

register = template.Library()
Category = get_model('catalogue', 'category')

# Since the category_tree template tag can be used multiple times in the same
# set of templates, we use a cache to avoid creating the node multile times.
NODE_CACHE = {}


@register.tag(name="category_tree")  # noqa (too complex (14))
def do_category_list(parse, token):
    tokens = token.split_contents()
    error_msg = ("%r tag uses the following syntax: {%% category_tree "
                 "[depth=n] [parent=<parent_category>] as categories %%}"
                 % tokens[0])
    # dict allows to assign values in `assign_vars` function closure
    var = {
        'depth': '0',
        'parent': '',
        'as': ''
    }

    def assign_vars(p_name, p_var):
        try:
            var[p_name] = p_var
        except KeyError:
            raise template.TemplateSyntaxError(error_msg)

    if len(tokens) == 5:
        if tokens[3] != 'as':
            raise template.TemplateSyntaxError(error_msg)
        p_name_was = None
        for i in range(1, 3):
            p_name, p_var = tokens[i].split('=')
            if p_name_was is not None and p_name == p_name_was:
                # raise error if same arg is given twice
                # for example {% category_tree depth=1 depth=2 as smth %}
                raise template.TemplateSyntaxError(error_msg)
            assign_vars(p_name, p_var)
            p_name_was = p_name
        var['as'] = tokens[-1]
    elif len(tokens) == 4:
        if tokens[2] != 'as':
            raise template.TemplateSyntaxError(error_msg)
        p_name, p_var = tokens[1].split('=')
        assign_vars(p_name, p_var)
        var['as'] = tokens[-1]
    elif len(tokens) == 3:
        if tokens[1] != 'as':
            raise template.TemplateSyntaxError(error_msg)
        var['as'] = tokens[-1]
    else:
        raise template.TemplateSyntaxError(error_msg)

    if var['parent']:
        # no cache if parent, because currently unique parent.id is unknown
        return CategoryTreeNode(var['depth'], var['parent'], var['as'])
    # Use a per-process cache of the CategoryTreeNode instance
    key = "".join(var.values())
    if key in NODE_CACHE:
        return NODE_CACHE[key]

    NODE_CACHE[key] = CategoryTreeNode(var['depth'], var['parent'], var['as'])
    return NODE_CACHE[key]


class CategoryTreeNode(template.Node):
    def __init__(self, depth_var, parent_var, as_var):
        self.depth_var = template.Variable(depth_var)
        if parent_var:
            self.parent_var = template.Variable(parent_var)
        else:
            self.parent_var = None
        self.as_var = as_var

    def get_annotated_list(self, max_depth=None, parent=None):
        """
        Gets an annotated list from a tree branch.

        Borrows heavily from treebeard's get_annotated_list
        """
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
            depth = node.get_depth()
            if start_depth is None:
                start_depth = depth
            if max_depth is not None and depth > max_depth:
                continue

            # Update previous node's info
            info['has_children'] = prev_depth is None or depth > prev_depth
            if prev_depth is not None and depth < prev_depth:
                info['num_to_close'] = list(range(0, prev_depth - depth))

            info = {'num_to_close': [],
                    'level': depth - start_depth}
            annotated_categories.append((node, info,))
            prev_depth = depth

        if prev_depth is not None:
            # close last leaf
            info['num_to_close'] = list(range(0, prev_depth - start_depth))
            info['has_children'] = prev_depth > prev_depth

        return annotated_categories

    def render(self, context):
        depth = int(self.depth_var.resolve(context))
        if self.parent_var:
            parent = self.parent_var.resolve(context)
        else:
            parent = None
        annotated_list = self.get_annotated_list(
            max_depth=depth or None, parent=parent)
        context[self.as_var] = annotated_list
        return ''
