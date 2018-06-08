from elasticsearch_dsl import TermsFacet


class AutoRangeFacet(TermsFacet):
    """
    Custom facet class used for our `auto_range` facet type. The results returned are the same as those for a TermsFacet
    agg but processed and displayed like a range facet.
    """

    RESULT_SIZE = 1000000

    def __init__(self, group_count, **kwargs):
        self.group_count = group_count
        kwargs['size'] = self.RESULT_SIZE
        super().__init__(**kwargs)
