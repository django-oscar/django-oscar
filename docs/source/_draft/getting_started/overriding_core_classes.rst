Customising core classes
========================

As much as possible, Oscar's core functionality is implemented in classes that are dynamically loaded
based on the values in ``settings.py``.  This means that any class can be extended and overridden
in your project to customise its behaviour.

To customise a single class, the process is as follows:

1.  Create a new app within your project with the same name as the app you are customising from oscar.  
    For example, if you want to change something from ``oscar.checkout.forms``, then create an app
    ``myshop.checkout`` and add a module ``forms.py``.  

2.  In this new module, create a new version of the class you want to customise.  This is usually done
    by importing the core class with a new name and then extended/overriding its functionality::

        from oscar.checkout.forms import ShippingAddressForm as CoreShippingAddressForm
        
        class ShippingAddressForm(CoreShippingAddressForm):
            
            # Customisation here
            pass

3.  Add your new app to ``settings.py``, replacing its counterpart from Oscar's core.