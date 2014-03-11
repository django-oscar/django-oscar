from django.core.cache import cache

from sorl.thumbnail.conf import settings
from sorl.thumbnail.kvstores.cached_db_kvstore import KVStore
from sorl.thumbnail.models import KVStore as KVStoreModel


class ConcurrentKVStore(KVStore):
    """
    Custom KV store for Sorl to avoid integrity errors when settings new
    values.
    """

    def _set_raw(self, key, value):
        KVStoreModel.objects.get_or_create(
            key=key, defaults={'value': value})
        cache.set(key, value, settings.THUMBNAIL_CACHE_TIMEOUT)
