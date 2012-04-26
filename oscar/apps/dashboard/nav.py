from django.core.urlresolvers import reverse

_nodes = []


class Node(object):

    def __init__(self, label, url_name=None, url_args=None, url_kwargs=None, access_fn=None):
        self.label = label
        self.url_name = url_name
        self.url_args = url_args
        self.url_kwargs = url_kwargs
        self.access_fn = access_fn
        self.children = []

    @property
    def is_heading(self):
        return self.url_name is None

    @property
    def url(self):
        return reverse(self.url_name, args=self.url_args, kwargs=self.url_kwargs)

    def add_child(self, node):
        self.children.append(node)

    def is_visible(self, user):
        if not self.access_fn:
            return True
        return self.access_fn(user)

    def filter(self, user):
        if not self.is_visible(user):
            return None
        node = Node(self.label, self.url_name, self.access_fn)
        for child in self.children:
            if child.is_visible(node):
                node.add_child(child)
        return node

    def has_children(self):
        return len(self.children) > 0

def register(node, display_order=5):
    # We use tuples so we can sort later on.  The lower the display order, the
    # closer to the left the node appears.
    _nodes.append((display_order, node))

def flush():
    _nodes = []

def get_nodes(user):
    nodes = []
    for _, node in sorted(_nodes):
        filtered_node = node.filter(user)
        if filtered_node:
            nodes.append(node)
    return nodes


