
class ProgressChecker(object):
    """
    Class for testing whether the appropriate steps of the checkout
    have been completed.
    """
    
    # List of URL names that have to be completed (in this order)
    urls_for_steps = ['oscar-checkout-delivery-address',
                      'oscar-checkout-delivery-method',
                      'oscar-checkout-payment',
                      'oscar-checkout-preview']
    
    def are_previous_steps_complete(self, request, url_name):
        """
        Checks whether the previous checkout steps have been completed.
        
        This uses the URL-name and the class-level list of required
        steps.
        """
        complete_steps = request.session.get('checkout_complete_steps', [])
        try:
            current_step_index = self.urls_for_steps.index(url_name)
            last_completed_step_index = len(complete_steps) - 1
            return current_step_index <= last_completed_step_index + 1 
        except ValueError:
            # Can't find current step index - must be manipulation
            return False
        except IndexError:
            # No complete steps - only allowed to be on first page
            return current_step_index == 0
        
    def step_complete(self, request):
        """
        Record a checkout step as complete.
        """
        match = resolve(request.path)
        url_name = match.url_name
        complete_steps = request.session.get('checkout_complete_steps', [])
        if not url_name in complete_steps:
            # Only add name if this is the first time the step 
            # has been completed. 
            complete_steps.append(url_name)
            request.session['checkout_complete_steps'] = complete_steps
            
    def all_steps_complete(self):
        """
        Order has been submitted - clear the completed steps from 
        the session.
        """
        request.session['checkout_complete_steps'] = []