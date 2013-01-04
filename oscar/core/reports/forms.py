from django import forms

class DefaultForm(forms.Form):
    """
    As the report generator view is a FormView we give it a Empty form as
    the default form.
    If needed the Report form can be overriden to provide data validation
    before the form to be run.
    """

