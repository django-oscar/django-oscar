from django.template import Library, Node, Variable, Template, Context
from django.db.models import get_model
from django.template.loader import get_template
     
register = Library()
     
class MerchandisingBlockNode(Node):
    def __init__(self, linked_block):
        self.linked_block = Variable(linked_block)
    
    def render(self, context):
        linked_block = self.linked_block.resolve(context)
        template = get_template(linked_block.block.template_file)
        context = Context({'block': linked_block.block})
        return template.render(context)
 
def get_block_html(parser, token):
    tag_name, linked_block = token.split_contents()
    return MerchandisingBlockNode(linked_block)

register.tag('render_merchandising_block', get_block_html)