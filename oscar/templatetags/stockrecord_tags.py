from django import template


register = template.Library()


@register.tag(name="session_strategy")
def do_stockrecord(parse, token):
    """
    Template tag for fetching the appropriate stockrecord for a
    product and returning it to the context
    """
    tokens = token.split_contents()
    if len(tokens) < 3 or tokens[3] != 'as':
        raise template.TemplateSyntaxError(
            "%(tag)r tag uses the following syntax: "
            "{%% %(tag)r request product as "
            "record %%}" % {'tag': tokens[0]})

    request_var, product_var, name_var = tokens[1], tokens[2], tokens[4]
    return StrategyNode(
        request_var, product_var, name_var)


class StrategyNode(template.Node):
    def __init__(self, request_var, product_var, name_var):
        self.request_var = template.Variable(request_var)
        self.product_var = template.Variable(product_var)
        self.name_var = name_var

    def render(self, context):
        try:
            request = self.request_var.resolve(context)
            product = self.product_var.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        context[self.name_var] = request.strategy.fetch(product)
        return ''
