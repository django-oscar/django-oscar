import copy
import re

from django.forms import Widget
from django.urls import reverse


class RelatedFieldWidgetWrapper(Widget):
    """
    This class is a wrapper to a given widget to add the add icon for the
    Oscar dashboard.
    """
    template_name = 'oscar/dashboard/widgets/related_widget_wrapper.html'

    IS_POPUP_VALUE = '1'
    IS_POPUP_VAR = '_popup'
    TO_FIELD_VAR = '_to_field'

    def __init__(self, widget, rel):
        self.needs_multipart_form = widget.needs_multipart_form
        self.attrs = widget.attrs
        self.choices = widget.choices
        self.widget = widget
        self.rel = rel

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        obj.widget = copy.deepcopy(self.widget, memo)
        obj.attrs = self.widget.attrs
        memo[id(self)] = obj
        return obj

    @property
    def is_hidden(self):
        return self.widget.is_hidden

    @property
    def media(self):
        return self.widget.media

    def get_related_url(self, info, action, *args):
        app_label = info[0]
        model_object_name = info[1]
        # Convert the model's object name into lowercase, with dashes between
        # the camel-cased words
        model_object_name = '-'.join(re.sub('([a-z])([A-Z])', r'\1 \2', model_object_name).lower().split())
        # Does not specify current app
        return reverse("dashboard:%s-%s-%s" % (app_label, model_object_name, action), args=args)

    def get_context(self, name, value, attrs):
        rel_opts = self.rel.model._meta
        info = (rel_opts.app_label, rel_opts.object_name)
        self.widget.choices = self.choices
        url_params = '&'.join("%s=%s" % param for param in [
            (RelatedFieldWidgetWrapper.TO_FIELD_VAR, self.rel.get_related_field().name),
            (RelatedFieldWidgetWrapper.IS_POPUP_VAR, RelatedFieldWidgetWrapper.IS_POPUP_VALUE),
        ])
        context = {
            'rendered_widget': self.widget.render(name, value, attrs),
            'name': name,
            'url_params': url_params,
            'model': rel_opts.verbose_name,
        }
        change_related_template_url = self.get_related_url(info, 'update', '__fk__')
        context.update(
            change_related_template_url=change_related_template_url,
        )
        add_related_url = self.get_related_url(info, 'create')
        context.update(
            add_related_url=add_related_url,
        )
        delete_related_template_url = self.get_related_url(info, 'delete', '__fk__')
        context.update(
            delete_related_template_url=delete_related_template_url,
        )
        return context

    def value_from_datadict(self, data, files, name):
        return self.widget.value_from_datadict(data, files, name)

    def value_omitted_from_data(self, data, files, name):
        return self.widget.value_omitted_from_data(data, files, name)

    def id_for_label(self, id_):
        return self.widget.id_for_label(id_)
