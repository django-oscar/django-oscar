from django.core.cache import cache
from django.db import transaction, IntegrityError

from sorl.thumbnail.conf import settings
from sorl.thumbnail.kvstores.cached_db_kvstore import KVStore
from sorl.thumbnail.models import KVStore as KVStoreModel


class ConcurrentKVStore(KVStore):

    @transaction.commit_on_success
    def _set_raw(self, key, value):
        try:
            kv = KVStoreModel.objects.create(key=key)
        except IntegrityError:
            transaction.commit()
            kv = KVStoreModel.objects.get(key=key)
        kv.value = value
        kv.save()
        cache.set(key, value, settings.THUMBNAIL_CACHE_TIMEOUT)