from django import template
from django.db.models import get_model

ProductNotification = get_model('notification', 'productnotification')

register = template.Library()


class RenderNotificationDescriptionNode(template.Node):
    """
    A node rendering the description of a ``Notification`` instance as 
    provided by the template context. The description is rendered using
    a template specific to the notification type and provides a context
    variable ``notify_item`` in the template context as provided by the
    notification instance.
    """

    def __init__(self, notification_variable):
        self.notification_variable = template.Variable(notification_variable)

    def render(self, context):
        """
        Render the template for the notification instance in *context*. The
        name of the template is generated based on the model name of the 
        notification and is expected to be found in 'notification/partials',
        e.g. for ``ProductNotification`` the template 
        'notification/partials/productnotification_description.html' will be
        used. In the context for this template, the notification item is 
        provided in the ``notify_item`` variable.
        """
        try:
            notification = self.notification_variable.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        name = notification.__class__.__name__.lower()
        tmpl = template.loader.get_template(
            'notification/partials/%s_description.html' % name
        )
        return tmpl.render(
            template.Context({'notify_item': notification.get_notification_item()},
            autoescape=context.autoescape)
        )


@register.tag
def generate_notification_description(parser, token):
    """
    Generate description for a ``Notification`` based on the class
    of the notification. A single argument is expected for this
    tag containing the ``Notification`` instance available in the
    template. The description for the notification is rendered
    in a templated that is based on the type of notification. The
    template name is based on the model name and is expected to
    be found in 'notification/partials' in the template folder.
    """
    try:
        tag_name, notification_variable = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires notification instance as "
            "argument" % token.contents.split()[0]
        )
    return RenderNotificationDescriptionNode(notification_variable)


@register.assignment_tag
def has_product_notification(user, product):
    """
    Check if the user has already signed up to receive a notification
    for this product. Anonymous users are ignored. If a registered
    user has signed up for a notification the tag returns ``True``.
    It returns ``False`` in all other cases.
    """
    if not user.is_authenticated():
        return False

    return ProductNotification.objects.filter(user=user,
                                              product=product).count() > 0
