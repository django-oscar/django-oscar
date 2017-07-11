from django.forms.models import BaseModelFormSet, modelformset_factory

from oscar.core.loading import get_classes, get_model

Line = get_model('basket', 'line')
BasketLineForm, SavedLineForm = get_classes('basket.forms', ['BasketLineForm', 'SavedLineForm'])


class BaseBasketLineFormSet(BaseModelFormSet):

    def __init__(self, strategy, *args, **kwargs):
        self.strategy = strategy
        super(BaseBasketLineFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        return super(BaseBasketLineFormSet, self)._construct_form(
            i, strategy=self.strategy, **kwargs)

    def _should_delete_form(self, form):
        """
        Quantity of zero is treated as if the user checked the DELETE checkbox,
        which results in the basket line being deleted
        """
        if super(BaseBasketLineFormSet, self)._should_delete_form(form):
            return True
        if self.can_delete and 'quantity' in form.cleaned_data:
            return form.cleaned_data['quantity'] == 0


BasketLineFormSet = modelformset_factory(
    Line, form=BasketLineForm, formset=BaseBasketLineFormSet, extra=0,
    can_delete=True)


class BaseSavedLineFormSet(BaseModelFormSet):

    def __init__(self, strategy, basket, *args, **kwargs):
        self.strategy = strategy
        self.basket = basket
        super(BaseSavedLineFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        return super(BaseSavedLineFormSet, self)._construct_form(
            i, strategy=self.strategy, basket=self.basket, **kwargs)


SavedLineFormSet = modelformset_factory(Line, form=SavedLineForm,
                                        formset=BaseSavedLineFormSet, extra=0,
                                        can_delete=True)
