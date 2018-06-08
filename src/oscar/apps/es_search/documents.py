from django.conf import settings
from django_elasticsearch_dsl import Index
from django_elasticsearch_dsl.documents import DocType, DocTypeMeta


class SearchDocTypeMeta(DocTypeMeta):

    def __new__(cls, name, bases, attrs):
        super_new = super(DocTypeMeta, cls).__new__

        # skip the logic in this function if the class is not a child of SearchDocument
        parents = [b for b in bases if isinstance(b, SearchDocTypeMeta)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        # Every document will leave in it's own index. Since this could potentially cause conflicts between documents
        # from different projects that are hosted the same elasticsearch cluster, we add a prefix to the index name
        # so that all documents/indices belonging to one project will have this prefix.
        if 'Meta' in attrs:
            meta = attrs['Meta']

            prefix = settings.OSCAR_SEARCH['INDEX_PREFIX']

            # if index is not defined in meta, use the Model's name.
            index_name = getattr(meta, 'index', meta.model.__name__.lower())

            meta.index = '{}--{}'.format(prefix, index_name)
            attrs['Meta'] = meta

        cls = super().__new__(cls, name, bases, attrs)
        cls.index = cls._doc_type.index
        cls.doc_type = cls._doc_type.name

        return cls


class SearchDocument(DocType, metaclass=SearchDocTypeMeta):

    analyzers = []
    index_config = {}

    @classmethod
    def define_analyzers(cls, index):
        for analyzer in cls.analyzers:
            index.analyzer(analyzer)

    @classmethod
    def build_index(cls):
        index = Index(cls.index)
        index.delete(ignore=404)

        cls.define_analyzers(index)

        index.settings(**cls.index_config)
        index.create()

    class Meta:
        model = None
        index = ''
