from . import strategy


class StrategyMiddleware(object):
    """
    Responsible for assigning the appropriate stockrecord
    strategy instance to the request
    """

    def process_request(self, request):
        # Default to picking the first available stockrecord
        request.strategy = strategy.FirstStockrecord(request)
