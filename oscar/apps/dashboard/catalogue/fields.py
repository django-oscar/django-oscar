from django import forms
from django.template import Context, Template

class ProductImageMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    Field that renders a ProductImage as a thumbnail and text instead of
    just as text.
    """

    # Using the low-level Template API instead of storing it in a separate file
    # A user might want to override this, so perhaps it should be a 'partial' template
    _template = Template("""
    {% load thumbnail %}
    
    {% thumbnail image.original "50x50" crop="center" as thumb %}
    <img src="{{ thumb.url }}" alt="{{ image }}" /> {{ image.original }}
    {% endthumbnail %}
    """)


    def __init__(self, *args, **kwargs):
        if 'widget' not in kwargs:
            kwargs['widget'] = forms.CheckboxSelectMultiple()

        if 'required' not in kwargs:
            kwargs['required'] = False

        super(ProductImageMultipleChoiceField, self).__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return self._template.render(Context({
            'image': obj
        }))