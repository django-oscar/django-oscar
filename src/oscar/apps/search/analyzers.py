from elasticsearch_dsl import analyzer, token_filter, tokenizer

from .models import Synonym

synonyms_filter = token_filter(
    'synonyms',
    type='synonym',
    synonyms=[o.synonyms for o in Synonym.objects.all()] or ['']
)
ngram_filter = token_filter(
    'ngram',
    min_gram=2,
    max_gram=15,
    type='nGram'
)
edgengram_filter = token_filter(
    'edgengram',
    min_gram=3,
    max_gram=15,
    side='front',
    type='edgeNGram'
)

ngram_tokenizer = tokenizer(
    'ngram_tokenizer',
    min_gram=2,
    max_gram=15,
    type='nGram'
)
edgengram_tokenizer = tokenizer(
    'edgengram_tokenizer',
    min_gram=3,
    max_gram=15,
    side='front',
    type='edgeNGram'
)


ngram_analyzer = analyzer(
    'ngram_analyzer',
    tokenizer='standard',
    filter=['lowercase', ngram_filter, synonyms_filter]
)

edgengram_analyzer = analyzer(
    'edgengram_analyzer',
    tokenizer='standard',
    filter=["lowercase", edgengram_filter, synonyms_filter]
)
