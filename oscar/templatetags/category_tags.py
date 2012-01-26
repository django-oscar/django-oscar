from django import template
from django.db.models import get_model

register = template.Library()
Category = get_model('catalogue','category')

@register.tag(name="category_tree")
def do_category_list(parse, token):
    tokens = token.split_contents()
    error_msg = "%r tag uses the following syntax: {%% category_tree [depth=n] as categories %%}" % tokens[0]
    depth_var = '1'

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
    
    return CategoryTreeNode(depth_var, as_var)


class CategoryTreeNode(template.Node):
    def __init__(self, depth_var, as_var):
        self.depth_var = template.Variable(depth_var)
        self.as_var = as_var
        
    def _build_tree(self, root, parent, data, depth):
        for category in data[depth]:
            if not parent or category.is_child_of(parent):
                node = (category, [])
                if depth < len(data) - 1:
                    self._build_tree(node[1], category, data, depth+1)
                root.append(node)
        return root
        
    def render(self, context):
        depth = int(self.depth_var.resolve(context))
        categories = Category.objects.filter(depth__lte=depth)
        
        category_buckets = [[] for i in range(depth)]
        
        for c in categories:
            category_buckets[c.depth - 1].append(c)
        category_subtree = []
        
        self._build_tree(category_subtree, None, category_buckets, 0)
        
        context[self.as_var] = category_subtree
        return ''
