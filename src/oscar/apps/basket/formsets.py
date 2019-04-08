from django.forms.models import BaseModelFormSet, modelformset_factory
from django.utils.functional import cached_property

from oscar.core.loading import get_classes, get_model

Line = get_model('basket', 'line')
BasketLineForm, SavedLineForm = get_classes('basket.forms', ['BasketLineForm', 'SavedLineForm'])


class BaseBasketLineFormSet(BaseModelFormSet):

    def __init__(self, strategy, *args, **kwargs):
        self.strategy = strategy
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        return super()._construct_form(
            i, strategy=self.strategy, **kwargs)

    def _should_delete_form(self, form):
        """
        Quantity of zero is treated as if the user checked the DELETE checkbox,
        which results in the basket line being deleted
        """
        if super()._should_delete_form(form):
            return True

        # If related form instance already removed, let's remove this form
        # as well.
        if not form.instance.id:
            return True
        if self.can_delete and 'quantity' in form.cleaned_data:
            return form.cleaned_data['quantity'] == 0

    @cached_property
    def forms_with_instances(self):
        return [f for f in self.forms if f.instance.id]

    def __iter__(self):
        """
        Skip forms with removed lines when iterating through the formset.
        """
        return iter(self.forms_with_instances)


BasketLineFormSet = modelformset_factory(
    Line, form=BasketLineForm, formset=BaseBasketLineFormSet, extra=0,
    can_delete=True)


class BaseSavedLineFormSet(BaseModelFormSet):

    def __init__(self, strategy, basket, *args, **kwargs):
        self.strategy = strategy
        self.basket = basket
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        return super()._construct_form(
            i, strategy=self.strategy, basket=self.basket, **kwargs)


SavedLineFormSet = modelformset_factory(Line, form=SavedLineForm,
                                        formset=BaseSavedLineFormSet, extra=0,
                                        can_delete=True)
