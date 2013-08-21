from oscar.core.loading import get_class

Selector = get_class('partner.strategy', 'Selector')

selector = Selector()


class StrategyMiddleware(object):
    """
    Responsible for assigning the appropriate stockrecord
    strategy instance to the request
    """

    def process_request(self, request):
        strategy = selector.strategy(
            request=request, user=request.user)
        request.strategy = strategy
