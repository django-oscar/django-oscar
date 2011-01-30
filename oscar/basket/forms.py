from django import forms


class FormFactory(object):
    
    def create(self, item, values=None):
        """
        For dynamically creating add-to-basket forms for a given product
        """
        self.values = values
        if item.is_group:
            return self._create_group_product_form(item)
        return self._create_product_form(item)

    def _create_group_product_form(self, item):
        pass
    
    def _create_product_form(self, item):
        # See http://www.b-list.org/weblog/2008/nov/09/dynamic-forms/ for 
        # advice on how this works.
        self.fields = {'action': forms.CharField(widget=forms.HiddenInput(), initial='add'),
                       'product_id': forms.IntegerField(widget=forms.HiddenInput(), min_value=1),
                       'quantity': forms.IntegerField(min_value=1)}
        if not self.values:
            self.values = {'action': 'add', 
                           'product_id': item.id, 
                           'quantity': 1}
            
        for option in item.options.all():
            self._add_option_field(item, option)
            
        form_class = type('AddToBasketForm', (forms.BaseForm,), {'base_fields': self.fields})
        return form_class(self.values)
    
    def _add_option_field(self, item, option):
        """
        Creates the appropriate form field for the product option.
        
        This is designed to be overridden so that specific widgets can be used for 
        certain types of options.
        """
        self.fields[option.code] = forms.CharField()
    

    
